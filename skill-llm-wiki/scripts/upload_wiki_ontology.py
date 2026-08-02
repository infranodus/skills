#!/usr/bin/env python3
"""Upload curated llm-wiki ontologies from infranodus/ to InfraNodus.

Stdlib-only and self-contained: this script ships WITH the llm-wiki skill
so the skill works when installed alone (the infranodus skill's uploader is
its sibling for generated repo/vault scopes — same manifest, same server,
different ownership). Talks to the InfraNodus MCP server directly over
streamable HTTP (JSON-RPC POSTs, authenticated with INFRANODUS_API_KEY),
so ontology content never passes through an agent context, and handles the
API failure modes deterministically: chunks to <= CHUNK_BYTES (413), paces
calls and backs off on rate limits (429), bisects rejected chunks.

Ownership contract (mirrored by the infranodus skill's upload_scopes.py):
  - This script touches ONLY manifest scopes with policy "curated". It
    never uploads, names, or rewrites generated scopes.
  - Curated graphs are named "wiki-<project>-<scope>" — the wiki-* prefix
    namespace belongs to llm-wiki; repo-*/vault-* belong to the scanner.

Append-only aware: curated ontologies grow by appending relation lines.
The manifest records how much of each file has been uploaded
(uploadedLines + a checksum of that prefix). A re-run uploads only the new
tail lines (server-side uploads to an existing graphName APPEND — exactly
what we want here). If earlier lines were edited or removed (allowed as a
deliberate editorial decision), the checksum no longer matches: the script
refuses and asks for --rebuild, because appending would not reflect the
edit. A clean rebuild = delete the graph in InfraNodus first, then re-run
with --rebuild (re-uploads the whole file, resets the counters).

Usage:
  python3 upload_wiki_ontology.py [project_dir]
      upload every curated scope: full upload if it has no graphName yet,
      else append the new tail lines (no-op when nothing new)
  python3 upload_wiki_ontology.py [project_dir] --file infranodus/concepts-ontology.md
      register (if needed) and upload one ontology file
  python3 upload_wiki_ontology.py [project_dir] --rebuild
      re-upload whole files and reset counters — ONLY after deleting the
      remote graph(s) in InfraNodus, otherwise every statement duplicates
  python3 upload_wiki_ontology.py --check-auth

  --prefix NAME   graph name prefix (default: wiki-<dir slug>)

Credentials: INFRANODUS_API_KEY env var, else auto-reused from a local
'infranodus' MCP server entry (.mcp.json, ~/.claude.json, ...).
INFRANODUS_MCP_URL overrides the server (default https://mcp.infranodus.com).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import date
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MCP_URL = os.environ.get("INFRANODUS_MCP_URL", "https://mcp.infranodus.com")
CHUNK_BYTES = 80_000      # safe payload size; API rejects ~100 KB+ with 413
MAX_NODES = 500           # server default 150 is too small for full wikis
PACE_SECONDS = 20         # gap between successful calls to stay under rate cap
BACKOFF_SECONDS = 300     # wait after a 429 before retrying the same chunk
MAX_RETRIES = 24          # per chunk, for 429s
HTTP_TIMEOUT = 180        # seconds per request (graph computation is slow)

RE_429 = re.compile(r"API request failed \(429\)|Too Many Requests", re.I)
RE_413 = re.compile(r"Payload Too Large|code:\s*413", re.I)


# ------------------------------------------------------ credential discovery

MCP_CONFIG_PATHS = [
    Path.cwd() / ".mcp.json",
    Path.home() / ".claude.json",
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".cursor" / "mcp.json",
    Path.home() / ".codex" / "config.json",
]


def _expand_env(value):
    return re.sub(r"\$\{?(\w+)\}?",
                  lambda m: os.environ.get(m.group(1), ""), value)


def _find_infranodus_entries(node, out):
    if isinstance(node, dict):
        servers = node.get("mcpServers")
        if isinstance(servers, dict):
            for name, entry in servers.items():
                if "infranodus" in name.lower() and isinstance(entry, dict):
                    out.append(entry)
        for v in node.values():
            _find_infranodus_entries(v, out)
    elif isinstance(node, list):
        for v in node:
            _find_infranodus_entries(v, out)


def discover_credentials():
    """[(credential, source), ...]: env var first, then local MCP configs.
    Credentials are never printed — only their sources are."""
    found, seen = [], set()

    def add(cred, source):
        cred = cred.strip()
        if cred and "$" not in cred and cred not in seen:
            seen.add(cred)
            found.append((cred, source))

    add(os.environ.get("INFRANODUS_API_KEY", ""), "environment")
    for path in MCP_CONFIG_PATHS:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        entries = []
        _find_infranodus_entries(data, entries)
        for entry in entries:
            headers = {k.lower(): v for k, v in
                       (entry.get("headers") or {}).items()
                       if isinstance(v, str)}
            m = re.match(r"Bearer\s+(\S+)",
                         _expand_env(headers.get("authorization", "")))
            if m:
                add(m.group(1), str(path))
            add(_expand_env(
                str((entry.get("env") or {}).get("INFRANODUS_API_KEY", ""))),
                str(path))
    return found


# ------------------------------------------------------------ MCP transport

class McpClient:
    """Minimal MCP streamable-HTTP client (JSON-RPC over POST). Exchanges
    the API key for a JWT (stable session id), initializes once, reuses the
    mcp-session-id header, reconnects on 401/stale-session errors."""

    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.token = None
        self.session_id = None
        self._rpc_id = 0

    def _post(self, path, data, headers):
        req = urllib.request.Request(self.base_url + path, data=data,
                                     headers=headers, method="POST")
        return urllib.request.urlopen(req, timeout=HTTP_TIMEOUT)

    def connect(self):
        exchange_err = None
        body = urllib.parse.urlencode({"api_key": self.api_key}).encode()
        try:
            with self._post("/oauth/token", body, {
                "Content-Type": "application/x-www-form-urlencoded",
            }) as resp:
                self.token = json.loads(resp.read())["access_token"]
        except urllib.error.HTTPError as e:
            # The discovered credential may already be an access token.
            exchange_err = f"{e.code}: {e.read()[:200]}"
            self.token = self.api_key
        except urllib.error.URLError as e:
            raise RuntimeError(f"cannot reach {self.base_url}: {e}") from e

        try:
            resp, payload = self._rpc("initialize", {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "upload_wiki_ontology",
                               "version": "1.0"},
            }, expect_response=True)
        except urllib.error.HTTPError as e:
            msg = f"authentication failed ({e.code}): {e.read()[:200]}"
            if exchange_err:
                msg += f"; token exchange also failed ({exchange_err})"
            raise RuntimeError(msg) from e
        self.session_id = resp.headers.get("mcp-session-id")
        if not self.session_id:
            raise RuntimeError(f"no mcp-session-id in initialize response "
                               f"({payload})")
        self._notify("notifications/initialized")

    def _headers(self):
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
        }
        if self.session_id:
            h["mcp-session-id"] = self.session_id
        return h

    def _rpc(self, method, params, expect_response=True):
        self._rpc_id += 1
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if expect_response:
            msg["id"] = self._rpc_id
        resp = self._post("/mcp", json.dumps(msg).encode(), self._headers())
        with resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ctype = resp.headers.get("Content-Type", "")
        if not expect_response:
            return resp, None
        return resp, self._parse_payload(raw, ctype, self._rpc_id)

    def _notify(self, method):
        self._rpc(method, None, expect_response=False)

    @staticmethod
    def _parse_payload(raw, ctype, rpc_id):
        if "text/event-stream" not in ctype:
            return json.loads(raw) if raw.strip() else None
        answer = None
        for line in raw.splitlines():
            if not line.startswith("data:"):
                continue
            try:
                msg = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            if msg.get("id") == rpc_id or "result" in msg or "error" in msg:
                answer = msg
        return answer

    def call_tool(self, tool, arguments):
        """Return (status, text): 'ok', '429', '413', or 'error'."""
        for attempt in ("first", "reconnect"):
            try:
                _, payload = self._rpc("tools/call",
                                       {"name": tool, "arguments": arguments})
            except urllib.error.HTTPError as e:
                text = e.read().decode("utf-8", errors="replace")[:2000]
                if e.code == 429 or RE_429.search(text):
                    return "429", text
                if e.code == 413 or RE_413.search(text):
                    return "413", text
                if e.code in (400, 401, 404) and attempt == "first":
                    self.connect()
                    continue
                return "error", f"HTTP {e.code}: {text}"
            except (urllib.error.URLError, TimeoutError) as e:
                return "error", f"connection failed: {e}"

            if payload is None:
                return "error", "empty response from server"
            if "error" in payload:
                text = json.dumps(payload["error"])
                if RE_429.search(text):
                    return "429", text
                if RE_413.search(text):
                    return "413", text
                return "error", text
            result = payload.get("result", {})
            text = "".join(c.get("text", "")
                           for c in result.get("content", [])
                           if c.get("type") == "text")
            if result.get("isError"):
                if RE_429.search(text):
                    return "429", text
                if RE_413.search(text):
                    return "413", text
                return "error", text
            return "ok", text
        return "error", "reconnect loop exhausted"


def connect_with_discovered_credentials():
    creds = discover_credentials()
    if not creds:
        sys.exit("no InfraNodus credential found — set INFRANODUS_API_KEY "
                 "(infranodus.com -> settings -> API access):\n"
                 "  export INFRANODUS_API_KEY=your_key\n"
                 "(also checked local MCP configs for an 'infranodus' server "
                 "entry; a cloud OAuth connector holds its token remotely "
                 "and cannot be reused)")
    for cred, source in creds:
        client = McpClient(MCP_URL, cred)
        try:
            client.connect()
            return client, source
        except RuntimeError as e:
            print(f"credential from {source}: {e}", file=sys.stderr)
    sys.exit(f"none of the {len(creds)} discovered credential(s) "
             f"authenticated against {MCP_URL}")


# ---------------------------------------------------- content and chunking

def split_frontmatter(raw):
    """(frontmatter_or_empty, body)."""
    m = re.match(r"^(---.*?---\s*)", raw, flags=re.S)
    return (m.group(1), raw[m.end():]) if m else ("", raw)


def chunk_text(text, limit=CHUNK_BYTES):
    """Split into <= limit-byte chunks on line boundaries."""
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


def upload_chunk(client, graph_name, chunk, wikilinks_mode):
    """Upload one chunk, handling 429 (backoff) and 413 (bisect)."""
    args = {"graphName": graph_name, "text": chunk, "maxNodes": MAX_NODES,
            "wikilinksMode": wikilinks_mode}
    for attempt in range(1, MAX_RETRIES + 1):
        status, out = client.call_tool("create_knowledge_graph", args)
        if status == "ok":
            return out
        if status == "429":
            print(f"    429 rate-limited (attempt {attempt}/{MAX_RETRIES}), "
                  f"waiting {BACKOFF_SECONDS}s", flush=True)
            time.sleep(BACKOFF_SECONDS)
            continue
        if status == "413":
            if len(chunk.encode("utf-8")) < 2_000:
                raise RuntimeError(f"413 on a tiny chunk: {out[:300]}")
            print("    413 payload too large, bisecting chunk", flush=True)
            halves = chunk_text(chunk, len(chunk.encode("utf-8")) // 2)
            last = None
            for h in halves:
                last = upload_chunk(client, graph_name, h, wikilinks_mode)
                time.sleep(PACE_SECONDS)
            return last
        raise RuntimeError(f"upload failed: {out[:500]}")
    raise RuntimeError(f"gave up after {MAX_RETRIES} rate-limit retries")


def extract_url(response_text):
    m = re.search(r"https://infranodus\.com/[^\s\"'\\]+", response_text)
    return m.group(0) if m else None


def frontmatter_mode(frontmatter):
    m = re.search(r"^wikilinksMode:\s*(\S+)", frontmatter, re.M)
    return m.group(1) if m else "wikilinksOnly"


def prefix_sha(lines):
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------- main

def scope_graph_name(prefix, fname):
    scope = re.sub(r"-ontology\.md$|\.md$", "", fname)
    return f"{prefix}-{scope}"


def main():
    ap = argparse.ArgumentParser(
        description="Upload curated llm-wiki ontologies to InfraNodus.")
    ap.add_argument("project_dir", nargs="?", default=".")
    ap.add_argument("--file", metavar="PATH",
                    help="register (if needed) and upload one ontology file")
    ap.add_argument("--prefix", metavar="NAME",
                    help="graph name prefix (default: wiki-<dir slug>)")
    ap.add_argument("--rebuild", action="store_true",
                    help="re-upload whole files and reset the append "
                         "counters. Delete the remote graph(s) in "
                         "InfraNodus FIRST — uploads append, so a rebuild "
                         "without deleting duplicates every statement.")
    ap.add_argument("--check-auth", action="store_true",
                    help="no upload: verify a credential works")
    args = ap.parse_args()

    if args.check_auth:
        _, source = connect_with_discovered_credentials()
        print(f"authenticated OK against {MCP_URL} "
              f"(credential from {source})")
        return

    root = Path(args.project_dir).resolve()
    manifest_path = root / "infranodus" / "manifest.json"
    manifest = (json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest_path.exists() else {"scopes": {}})
    scopes = manifest.setdefault("scopes", {})

    if args.file:
        p = (root / args.file).resolve()
        if not p.exists():
            sys.exit(f"file not found: {args.file}")
        fname = p.name
        entry = scopes.setdefault(fname, {})
        entry.setdefault("file", str(p.relative_to(root)))
        entry.setdefault("policy", "curated")
        targets = {fname: entry}
    else:
        targets = {f: m for f, m in scopes.items()
                   if m.get("policy") == "curated" and "file" in m}

    if not targets:
        print("no curated scopes in the manifest — register ontologies "
              "with --file, or add entries with policy \"curated\"")
        return

    for fname, meta in targets.items():
        if meta.get("policy") != "curated":
            sys.exit(f"{fname}: policy is {meta.get('policy')!r} — this "
                     "uploader only touches curated scopes; generated "
                     "scopes belong to the infranodus skill's uploader")

    prefix = args.prefix
    if prefix is None:
        project = re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-")
        prefix = f"wiki-{project}"

    client, source = connect_with_discovered_credentials()
    if source != "environment":
        print(f"using credential from MCP config: {source}")

    for fname, meta in targets.items():
        path = root / meta["file"]
        if not path.exists():
            print(f"skip {fname} (file missing: {meta['file']})")
            continue
        frontmatter, body = split_frontmatter(
            path.read_text(encoding="utf-8"))
        lines = body.splitlines(keepends=True)
        mode = frontmatter_mode(frontmatter)
        graph_name = meta.get("graphName") or scope_graph_name(prefix, fname)

        if meta.get("graphName") and not args.rebuild:
            done = int(meta.get("uploadedLines") or 0)
            if done > len(lines):
                sys.exit(f"{fname}: file has fewer lines ({len(lines)}) "
                         f"than were uploaded ({done}) — earlier lines were "
                         "removed. Delete the graph in InfraNodus, then "
                         "re-run with --rebuild.")
            if meta.get("uploadedSha") and \
                    prefix_sha(lines[:done]) != meta["uploadedSha"]:
                sys.exit(f"{fname}: already-uploaded lines changed on disk "
                         "— appending would not reflect the edit. Delete "
                         "the graph in InfraNodus, then re-run with "
                         "--rebuild.")
            new_lines = lines[done:]
            if not new_lines:
                print(f"skip {fname} (no new lines since last upload)")
                continue
            text = "".join(new_lines)
            print(f"{fname} -> {graph_name} (+{len(new_lines)} new line(s))",
                  flush=True)
        else:
            text = body
            print(f"{fname} -> {graph_name} (full upload, "
                  f"{len(lines)} line(s))", flush=True)

        last = None
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            if len(chunks) > 1:
                print(f"  chunk {i + 1}/{len(chunks)}", flush=True)
            last = upload_chunk(client, graph_name, chunk, mode)
            time.sleep(PACE_SECONDS)

        meta["graphName"] = graph_name
        meta["url"] = extract_url(last or "") or meta.get("url")
        meta["wikilinksMode"] = mode
        meta["uploadedLines"] = len(lines)
        meta["uploadedSha"] = prefix_sha(lines)
        meta["updated"] = date.today().isoformat()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"  manifest updated ({fname}: {graph_name})", flush=True)

    print("done — curated scopes are in sync with their graphs")


if __name__ == "__main__":
    main()
