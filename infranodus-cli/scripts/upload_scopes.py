#!/usr/bin/env python3
"""Upload infranodus/ scope files to InfraNodus as saved graphs.

Stdlib-only. Handles the two API failure modes deterministically:
  - 413 Payload Too Large: chunks every scope file to <= CHUNK_BYTES before
    sending; if a chunk is still rejected, it is split in half and retried.
  - 429 Too Many Requests: paces calls (PACE_SECONDS apart) and, on a 429,
    sleeps BACKOFF_SECONDS and retries the same chunk (up to MAX_RETRIES).

Reads infranodus/manifest.json, uploads every scope whose graphName is null
(all scopes with --force), records graphName + url back into the manifest,
and saves the full graph JSON as infranodus/<scope>-graph.json.

Usage:
  python3 upload_scopes.py [project_dir] [--prefix NAME] [--force]

  --prefix   graph name prefix (default: <vault|repo>-<project dir slug>)
  --force    re-upload scopes that already have a graphName
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CHUNK_BYTES = 80_000      # safe payload size; API rejects ~100 KB+ with 413
PACE_SECONDS = 20         # gap between successful calls to stay under rate cap
BACKOFF_SECONDS = 300     # wait after a 429 before retrying the same chunk
MAX_RETRIES = 24          # per chunk, for 429s (24 * 5 min = 2 h worst case;
                          # observed lockouts can exceed 1 h on busy accounts)


RE_429 = re.compile(r"API request failed \(429\)|Too Many Requests", re.I)
RE_413 = re.compile(r"Payload Too Large|code:\s*413", re.I)


def call_mcporter(tool, args):
    """Return (status, out): status is 'ok', '429', '413', or 'error'."""
    proc = subprocess.run(
        ["mcporter", "call", f"infranodus.{tool}", "--args", json.dumps(args)],
        capture_output=True, text=True,
    )
    out = proc.stdout + proc.stderr
    if RE_429.search(out):
        return "429", out
    if RE_413.search(out):
        return "413", out
    if proc.returncode != 0 or '"error"' in out[:2000].lower():
        return "error", out
    return "ok", out


def strip_frontmatter(path):
    raw = path.read_text(encoding="utf-8")
    return re.sub(r"^---.*?---\s*", "", raw, flags=re.S)


def chunk_text(text, limit=CHUNK_BYTES):
    """Split text into chunks of <= limit bytes on line boundaries."""
    chunks, cur, size = [], [], 0
    for ln in text.splitlines(keepends=True):
        b = len(ln.encode("utf-8"))
        if size + b > limit and cur:
            chunks.append("".join(cur))
            cur, size = [], 0
        cur.append(ln)
        size += b
    if cur:
        chunks.append("".join(cur))
    return chunks


def upload_chunk(graph_name, chunk):
    """Upload one chunk, handling 429 (backoff) and 413 (bisect). Returns
    the last successful response text, or raises RuntimeError."""
    for attempt in range(1, MAX_RETRIES + 1):
        status, out = call_mcporter("create_knowledge_graph",
                                    {"graphName": graph_name, "text": chunk})
        if status == "ok":
            return out
        if status == "429":
            print(f"    429 rate-limited (attempt {attempt}/{MAX_RETRIES}), "
                  f"waiting {BACKOFF_SECONDS}s", flush=True)
            time.sleep(BACKOFF_SECONDS)
            continue
        if status == "413":
            if len(chunk.encode("utf-8")) < 2_000:
                raise RuntimeError(f"413 on a tiny chunk, giving up: {out[:300]}")
            print("    413 payload too large, bisecting chunk", flush=True)
            halves = chunk_text(chunk, len(chunk.encode("utf-8")) // 2)
            last = None
            for h in halves:
                last = upload_chunk(graph_name, h)
                time.sleep(PACE_SECONDS)
            return last
        raise RuntimeError(f"upload failed: {out[:500]}")
    raise RuntimeError(f"gave up after {MAX_RETRIES} rate-limit retries")


def extract_url(response_text):
    m = re.search(r"https://infranodus\.com/[^\s\"'\\]+", response_text)
    return m.group(0) if m else None


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    argv = [a for a in argv if a != "--force"]
    prefix = None
    if "--prefix" in argv:
        i = argv.index("--prefix")
        prefix = argv[i + 1]
        del argv[i:i + 2]
    root = Path(argv[0] if argv else ".").resolve()

    manifest_path = root / "infranodus" / "manifest.json"
    if not manifest_path.exists():
        sys.exit("no infranodus/manifest.json — run repo2statements.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scopes = manifest.get("scopes", {})

    if prefix is None:
        project = re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-")
        kind = "vault" if any(k.startswith("vault-") for k in scopes) else "repo"
        prefix = f"{kind}-{project}"

    for fname, meta in scopes.items():
        if meta.get("graphName") and not force:
            print(f"skip {fname} (already uploaded: {meta['graphName']})")
            continue
        scope = re.sub(r"^(repo|vault)-|-ontology\.md$", "", fname)
        graph_name = f"{prefix}-{scope}"
        path = root / meta["file"]
        text = strip_frontmatter(path)
        chunks = chunk_text(text)
        print(f"{fname} -> {graph_name} ({len(chunks)} chunk(s))", flush=True)

        last = None
        for i, chunk in enumerate(chunks):
            print(f"  chunk {i + 1}/{len(chunks)}", flush=True)
            last = upload_chunk(graph_name, chunk)
            time.sleep(PACE_SECONDS)

        meta["graphName"] = graph_name
        meta["url"] = extract_url(last) or f"https://infranodus.com/paranyushkin/{graph_name}"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        status, out = call_mcporter("analyze_existing_graph_by_name",
                                    {"graphName": graph_name, "includeGraph": True})
        if status == "ok":
            (root / "infranodus" / f"{scope}-graph.json").write_text(out, encoding="utf-8")
            print(f"  saved infranodus/{scope}-graph.json", flush=True)
        else:
            print(f"  WARNING: could not fetch graph JSON: {out[:200]}", flush=True)
        time.sleep(PACE_SECONDS)

    print("all scopes uploaded; manifest updated")


if __name__ == "__main__":
    main()
