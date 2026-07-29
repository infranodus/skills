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

Transport: shells out to `mcporter`. When the calling agent has native
InfraNodus MCP tools in its session, it should NOT use the upload mode of
this script — use --emit-chunks to get the chunk files + graph names, call
create_knowledge_graph natively per chunk, then --record the results.

Usage:
  python3 upload_scopes.py [project_dir] [--prefix NAME] [--force]
  python3 upload_scopes.py [project_dir] --emit-chunks [--prefix NAME]
                                         [--chunk-bytes N]
  python3 upload_scopes.py [project_dir] --record SCOPE_FILE GRAPH_NAME [URL]

  --prefix       graph name prefix (default: <vault|repo>-<project dir slug>)
  --force        re-upload scopes that already have a graphName
  --emit-chunks  no upload: write ready-to-send chunks to
                 infranodus/.chunks/<graphName>/NNN.txt and print the plan
                 (for agents with native MCP tools). Chunks are
                 EMIT_CHUNK_BYTES each — smaller than upload mode's, so an
                 agent can Read one whole chunk per call and re-emit it
                 verbatim as the native tool's `text` argument.
  --chunk-bytes  override the emit-mode chunk size (e.g. 30000 if the
                 agent's Read still truncates)
  --record       no upload: write graphName (+ optional url) for one scope
                 into the manifest after a native-tool upload
"""
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

CHUNK_BYTES = 80_000      # safe payload size; API rejects ~100 KB+ with 413
EMIT_CHUNK_BYTES = 45_000 # --emit-chunks only: native-MCP uploads pass each
                          # chunk through the agent's context (full Read +
                          # verbatim re-emit), so chunks must fit ONE agent
                          # read (~25k tokens) with headroom, not just the
                          # API payload limit
MAX_NODES = 500           # graph size cap per scope (server default 150 is
                          # too small for repo/vault corpora; API max 1000)
PACE_SECONDS = 20         # gap between successful calls to stay under rate cap
BACKOFF_SECONDS = 300     # wait after a 429 before retrying the same chunk
MAX_RETRIES = 24          # per chunk, for 429s (24 * 5 min = 2 h worst case;
                          # observed lockouts can exceed 1 h on busy accounts)


RE_429 = re.compile(r"API request failed \(429\)|Too Many Requests", re.I)
RE_413 = re.compile(r"Payload Too Large|code:\s*413", re.I)


NO_MCPORTER_MSG = """\
mcporter is not installed — no upload transport available.

The extracted scope files in infranodus/ are intact; only the upload needs
a transport. In order of preference:
  1. If this agent session has native InfraNodus MCP tools, re-run with
     --emit-chunks and upload the chunks via create_knowledge_graph directly,
     then record results with --record.
  2. Install mcporter:  npm install -g mcporter
     then configure it (needs INFRANODUS_API_KEY from infranodus.com, or OAuth):
       mcporter config add infranodus --url https://mcp.infranodus.com/ \\
         --transport http --header "accept=application/json, text/event-stream" \\
         --header "Authorization=Bearer $INFRANODUS_API_KEY" --scope home
"""


def call_mcporter(tool, args):
    """Return (status, out): status is 'ok', '429', '413', or 'error'."""
    try:
        proc = subprocess.run(
            ["mcporter", "call", f"infranodus.{tool}", "--args",
             json.dumps(args)],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        sys.exit(NO_MCPORTER_MSG)
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


HEADING_LINE_RE = re.compile(r"^\s*#{1,6}\s")


def chunk_text(text, limit=CHUNK_BYTES):
    """Split text into chunks of <= limit bytes on line boundaries.

    Heading-aware: scope files carry the parent page as `## [[page]]`
    section headings (parentAndConcepts/obsidianStyle contract). When a
    chunk boundary falls mid-section, the active heading is re-emitted at
    the top of the next chunk so its statements keep their parent."""
    chunks, cur, size = [], [], 0
    current_heading = None
    carried_heading = None  # heading active when the current chunk started
    for ln in text.splitlines(keepends=True):
        b = len(ln.encode("utf-8"))
        if size + b > limit and cur:
            chunks.append("".join(cur))
            cur, size = [], 0
            carried_heading = current_heading
        if not cur and carried_heading and not HEADING_LINE_RE.match(ln):
            cur.append(carried_heading)
            size += len(carried_heading.encode("utf-8"))
        if HEADING_LINE_RE.match(ln):
            current_heading = ln if ln.endswith("\n") else ln + "\n"
        cur.append(ln)
        size += b
    if cur:
        chunks.append("".join(cur))
    return chunks


def upload_chunk(graph_name, chunk, wikilinks_mode="default"):
    """Upload one chunk, handling 429 (backoff) and 413 (bisect). Returns
    the last successful response text, or raises RuntimeError.
    wikilinksMode/maxNodes only take effect when the graph context is first
    created, so passing them on every chunk is safe and only the first
    matters."""
    args = {"graphName": graph_name, "text": chunk, "maxNodes": MAX_NODES}
    if wikilinks_mode != "default":
        args["wikilinksMode"] = wikilinks_mode
    for attempt in range(1, MAX_RETRIES + 1):
        status, out = call_mcporter("create_knowledge_graph", args)
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
                last = upload_chunk(graph_name, h, wikilinks_mode)
                time.sleep(PACE_SECONDS)
            return last
        raise RuntimeError(f"upload failed: {out[:500]}")
    raise RuntimeError(f"gave up after {MAX_RETRIES} rate-limit retries")


def extract_url(response_text):
    m = re.search(r"https://infranodus\.com/[^\s\"'\\]+", response_text)
    return m.group(0) if m else None


def scope_graph_name(prefix, fname):
    scope = re.sub(r"^(repo|vault)-|-ontology\.md$", "", fname)
    return scope, f"{prefix}-{scope}"


def scope_wikilinks_mode(fname, path=None):
    """Processing mode for a scope file. The generated files declare it in
    their frontmatter (`wikilinksMode: ...`) — that wins, so custom scope
    files work too. Fallback heuristic: link-structure scopes are pure
    [[A]] links to [[B]] statements -> wikilinksOnly (only the wikilinks
    become nodes; 'links'/'to' would otherwise form a fake hub); prose
    scopes (docs, rationale, history) -> parentAndConcepts (the
    `## [[page]]` heading / `[[Page]]: ` prefix travels as a per-statement
    parent category, so the page node attaches to its statements' concepts
    WITHOUT suppressing the prose). Both keep [[name]]-style node naming,
    so all scopes stay mergeable."""
    if path is not None:
        try:
            head = path.read_text(encoding="utf-8")[:500]
            m = re.search(r"^wikilinksMode:\s*(\S+)", head, re.M)
            if m:
                return m.group(1)
        except OSError:
            pass
    return ("wikilinksOnly" if fname.startswith("vault-links")
            else "parentAndConcepts")


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    emit_chunks = "--emit-chunks" in argv
    argv = [a for a in argv if a not in ("--force", "--emit-chunks")]
    record = None
    if "--record" in argv:
        i = argv.index("--record")
        record = argv[i + 1:i + 4]  # SCOPE_FILE GRAPH_NAME [URL]
        del argv[i:i + 4]
        if len(record) < 2:
            sys.exit("--record needs: SCOPE_FILE GRAPH_NAME [URL]")
    prefix = None
    if "--prefix" in argv:
        i = argv.index("--prefix")
        prefix = argv[i + 1]
        del argv[i:i + 2]
    emit_chunk_bytes = EMIT_CHUNK_BYTES
    if "--chunk-bytes" in argv:
        i = argv.index("--chunk-bytes")
        emit_chunk_bytes = int(argv[i + 1])
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

    if record:
        fname, graph_name = record[0], record[1]
        if fname not in scopes:
            sys.exit(f"unknown scope file: {fname} (manifest has: "
                     f"{', '.join(scopes)})")
        scopes[fname]["graphName"] = graph_name
        scopes[fname]["url"] = (record[2] if len(record) > 2 else
                                f"https://infranodus.com/user/{graph_name}")
        manifest_path.write_text(json.dumps(manifest, indent=2),
                                 encoding="utf-8")
        print(f"recorded {fname} -> {graph_name}")
        scope, _ = scope_graph_name(prefix, fname)
        graph_json = root / "infranodus" / f"{scope}-graph.json"
        if not graph_json.exists():
            print(f"  STILL MISSING: infranodus/{scope}-graph.json — --record "
                  f"only writes the manifest. Fetch the graph "
                  f"(analyze_existing_graph_by_name with includeGraph: true, "
                  f"maxNodes {MAX_NODES}) and Write the response there.",
                  file=sys.stderr)
        return

    if emit_chunks:
        chunks_root = root / "infranodus" / ".chunks"
        plan = []
        for fname, meta in scopes.items():
            if meta.get("graphName") and not force:
                continue
            scope, graph_name = scope_graph_name(prefix, fname)
            text = strip_frontmatter(root / meta["file"])
            out_dir = chunks_root / graph_name
            out_dir.mkdir(parents=True, exist_ok=True)
            files = []
            for i, chunk in enumerate(chunk_text(text, emit_chunk_bytes)):
                p = out_dir / f"{i:03d}.txt"
                p.write_text(chunk, encoding="utf-8")
                files.append(str(p.relative_to(root)))
            plan.append({"scopeFile": fname, "graphName": graph_name,
                         "wikilinksMode": scope_wikilinks_mode(
                             fname, root / meta["file"]),
                         "maxNodes": MAX_NODES, "chunks": files,
                         "graphJson": f"infranodus/{scope}-graph.json"})
        print(json.dumps(plan, indent=2))
        print("\nupload each chunk via the NATIVE create_knowledge_graph "
              "tool ({graphName, text: <chunk contents>, maxNodes, and the "
              "scope's wikilinksMode when not 'default'}), IN ORDER, same "
              "graphName per scope. Read each chunk file COMPLETELY and "
              "pass its exact contents as text — if a Read truncates, "
              "re-run --emit-chunks with a smaller --chunk-bytes instead "
              "of switching transport (never mcporter while native tools "
              "exist). Pace calls and back off on rate limits.\n\n"
              "THEN, per scope, BOTH of these — the scope is not done "
              "until both exist:\n"
              "  1. --record <scopeFile> <graphName> [url]  (manifest only; "
              "it does NOT fetch anything)\n"
              "  2. call analyze_existing_graph_by_name natively with "
              "{graphName, includeGraph: true, maxNodes} and Write the "
              "response verbatim to that scope's \"graphJson\" path above. "
              "Upload mode does this for you; the native path does not, so "
              "skipping it leaves the workflow's local graph JSON missing.\n\n"
              "Delete infranodus/.chunks/ once every scope has both.",
              file=sys.stderr)
        return

    if shutil.which("mcporter") is None:
        sys.exit(NO_MCPORTER_MSG)

    for fname, meta in scopes.items():
        if meta.get("graphName") and not force:
            print(f"skip {fname} (already uploaded: {meta['graphName']})")
            continue
        scope, graph_name = scope_graph_name(prefix, fname)
        path = root / meta["file"]
        text = strip_frontmatter(path)
        chunks = chunk_text(text)
        print(f"{fname} -> {graph_name} ({len(chunks)} chunk(s))", flush=True)

        mode = scope_wikilinks_mode(fname, path)
        last = None
        for i, chunk in enumerate(chunks):
            print(f"  chunk {i + 1}/{len(chunks)}", flush=True)
            last = upload_chunk(graph_name, chunk, mode)
            time.sleep(PACE_SECONDS)

        meta["graphName"] = graph_name
        meta["url"] = extract_url(last) or f"https://infranodus.com/paranyushkin/{graph_name}"
        meta["wikilinksMode"] = mode
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        status, out = call_mcporter("analyze_existing_graph_by_name",
                                    {"graphName": graph_name,
                                     "includeGraph": True,
                                     "maxNodes": MAX_NODES})
        if status == "ok":
            (root / "infranodus" / f"{scope}-graph.json").write_text(out, encoding="utf-8")
            print(f"  saved infranodus/{scope}-graph.json", flush=True)
        else:
            print(f"  WARNING: could not fetch graph JSON: {out[:200]}", flush=True)
        time.sleep(PACE_SECONDS)

    print("all scopes uploaded; manifest updated")


if __name__ == "__main__":
    main()
