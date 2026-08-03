#!/usr/bin/env python3
"""Upload infranodus/ scope files to InfraNodus as saved graphs.

Stdlib-only. Talks to THE MCP SERVER THE USER CONFIGURED — an http entry is
reached at its own url, a stdio entry is launched as its own subprocess —
so the data flows disk -> that server without passing through an agent
context, and the server's wikilinksMode handling (parentAndConcepts heading
parsing, wikilinksOnly, ...) applies exactly as it does for native MCP tool
calls.

The endpoint is never guessed and credentials are never read out of config
files. See "MCP server resolution" below for the whole contract.

Handles the two API failure modes deterministically:
  - 413 Payload Too Large: chunks every scope file to <= CHUNK_BYTES before
    sending; if a chunk is still rejected, it is split in half and retried.
  - 429 Too Many Requests: paces calls (PACE_SECONDS apart) and, on a 429,
    sleeps BACKOFF_SECONDS and retries the same chunk (up to MAX_RETRIES).

Reads infranodus/manifest.json, uploads every scope whose graphName is null
(all such scopes with --force). Scopes whose manifest entry says
policy "curated" (llm-wiki ontologies etc.) are NEVER uploaded, named, or
metadata-rewritten here — they belong to their authoring skill, which ships
its own uploader. Per uploaded scope: records the routing metadata into
the manifest (graphName, url, purpose, topics, gaps — so the agent can pick
the right graph per question) plus its provenance (endpoint, transport,
account, verified — so a later session can tell WHERE the graph lives and
whether it is still readable), appends a dated build section to the
append-only infranodus/INFRANODUS_REPORT.md log, and deletes the scope
file — scope files are build intermediates (kept on failure/skip, with
--keep-scopes, or when not marked policy "generated"); the content's home
is the graphs.

NOTE: uploads to an existing graphName APPEND statements server-side. A
clean rebuild of an already-uploaded scope requires deleting the graph in
InfraNodus first, then re-running with --force (which warns about this).

The graphs live on the server and are queried there (via the MCP tools
analyze_existing_graph_by_name, retrieve_from_knowledge_base), so no local
graph copy is written by default; --save-graph exports one when an
offline/renderable copy is explicitly wanted.

Usage:
  python3 upload_scopes.py [project_dir] [--prefix NAME] [--force]
                           [--save-graph]
  python3 upload_scopes.py [project_dir] --register-project
  python3 upload_scopes.py --register-global

  --prefix           graph name prefix (default: <vault|repo>-<dir slug>)
  --force            re-upload scopes that already have a graphName
                     (APPENDS to the existing graph — see NOTE above)
  --save-graph       also fetch each uploaded graph and save it as
                     infranodus/<scope>-graph.json (opt-in)
  --keep-scopes      keep the scope .md files after a successful upload
                     (e.g. for Obsidian rendering)
  --register-project no upload: write the "## infranodus" always-on block
                     into <project_dir>/CLAUDE.md so the agent queries these
                     graphs for questions instead of grepping files.
                     Idempotent (marker-delimited, replaced in place).
                     Run once, after the scopes are uploaded.
  --register-global  no upload, no project needed: write the trigger block
                     into ~/.claude/CLAUDE.md so the skill is surfaced in
                     every session. Derives the skill path and slash command
                     from this file's own location. Run by install.sh.

Both registration modes preserve everything outside their markers; neither
rewrites a CLAUDE.md.

MCP server resolution (uploads only; queries use the session's own MCP
connection). The server comes from this agent's own configuration, in this
order — project scope wins, first match wins:

  <project_dir>/.mcp.json
  ~/.claude.json            (this project's section, then the global one)
  ~/.claude/settings.json

Nothing else is consulted: no other application's config is read, and no
endpoint default exists. If no infranodus server is configured the script
stops and explains how to add one.

Credentials are NEVER read out of a config file:
  - http server  -> INFRANODUS_API_KEY from the environment, and nothing
                    else (infranodus.com -> settings -> API access).
  - stdio server -> the entry's own env block is handed to the subprocess
                    untouched, so whatever key the user configured is passed
                    through without being inspected, logged, or re-aimed at
                    a different endpoint.

Exactly one server is tried. A failed connection is a hard stop — it never
falls through to another credential or another endpoint.

Preflight: `upload_scopes.py [project_dir] --check-auth`.
"""
import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from datetime import date
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CHUNK_BYTES = 80_000      # safe payload size; API rejects ~100 KB+ with 413
MAX_NODES = 500           # graph size cap per scope (server default 150 is
                          # too small for repo/vault corpora; API max 1000)
PACE_SECONDS = 20         # gap between successful calls to stay under rate cap
BACKOFF_SECONDS = 300     # wait after a 429 before retrying the same chunk
MAX_RETRIES = 24          # per chunk, for 429s (24 * 5 min = 2 h worst case;
                          # observed lockouts can exceed 1 h on busy accounts)
HTTP_TIMEOUT = 180        # seconds per request (graph computation is slow)

RE_429 = re.compile(r"API request failed \(429\)|Too Many Requests", re.I)
RE_413 = re.compile(r"Payload Too Large|code:\s*413", re.I)


# -------------------------------------------------- MCP server resolution

# WHY only these three: they are this agent's own MCP configuration. Reading
# another application's config (a different editor's mcp.json, a shell rc,
# ...) would mean uploading a user's content through a server and an account
# they did not choose for this project — which is exactly the failure this
# resolution order exists to prevent. Project scope wins over global.
def _config_sources(root):
    return [
        (root / ".mcp.json", "project"),
        (Path.home() / ".claude.json", None),   # both scopes, handled below
        (Path.home() / ".claude" / "settings.json", "global"),
    ]


class ServerSpec:
    """The InfraNodus MCP server the user configured, and how to reach it.

    Holds transport information only. For a stdio server `env` is carried
    verbatim so it can be handed to the subprocess — its values are never
    read, printed, or sent anywhere else."""

    def __init__(self, name, source, scope, transport,
                 url=None, command=None, args=None, env=None):
        self.name = name
        self.source = source        # config file this came from
        self.scope = scope          # 'project' | 'global'
        self.transport = transport  # 'http' | 'stdio'
        self.url = url
        self.command = command
        self.args = list(args or [])
        self.env = dict(env or {})

    def endpoint(self):
        if self.transport == "http":
            return self.url
        return " ".join([self.command, *self.args])

    def describe(self):
        return (f"  server:   {self.name} ({self.transport}, {self.scope})\n"
                f"  endpoint: {self.endpoint()}\n"
                f"  source:   {self.source}")


def _infranodus_entries(servers):
    if not isinstance(servers, dict):
        return []
    return [(name, entry) for name, entry in servers.items()
            if "infranodus" in name.lower() and isinstance(entry, dict)]


def _spec_from_entry(name, entry, source, scope):
    """Build a ServerSpec from an mcpServers entry — transport only."""
    url = entry.get("url") or entry.get("endpoint")
    etype = str(entry.get("type") or "").lower()
    if url and etype in ("", "http", "sse", "streamable-http", "streamablehttp"):
        return ServerSpec(name, source, scope, "http", url=url)
    if entry.get("command"):
        return ServerSpec(name, source, scope, "stdio",
                          command=entry["command"], args=entry.get("args"),
                          env=entry.get("env"))
    return None


def _load_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def resolve_mcp_server(root):
    """Return the ServerSpec of the InfraNodus MCP server configured for this
    project, or None if the user has not configured one."""
    candidates = []
    for path, scope in _config_sources(root):
        data = _load_json(path)
        if data is None:
            continue
        if scope is None:
            # ~/.claude.json: this project's own section outranks the global
            # server list, mirroring how the agent itself resolves servers.
            projects = data.get("projects")
            if isinstance(projects, dict):
                pcfg = projects.get(str(root))
                if isinstance(pcfg, dict):
                    for name, entry in _infranodus_entries(
                            pcfg.get("mcpServers")):
                        candidates.append((name, entry, str(path), "project"))
            for name, entry in _infranodus_entries(data.get("mcpServers")):
                candidates.append((name, entry, str(path), "global"))
        else:
            for name, entry in _infranodus_entries(data.get("mcpServers")):
                candidates.append((name, entry, str(path), scope))

    for name, entry, source, scope in candidates:
        spec = _spec_from_entry(name, entry, source, scope)
        if spec:
            return spec
    return None


NO_SERVER_HELP = """\
no InfraNodus MCP server is configured for this project.

Uploads go through the MCP server you set up — this script does not pick an
endpoint or look for a credential on its own. Add one, then re-run:

  hosted server
    export INFRANODUS_API_KEY=...   # infranodus.com -> settings -> API access
    claude mcp add --transport http infranodus https://mcp.infranodus.com \\
        --header "Authorization: Bearer $INFRANODUS_API_KEY"

  local / self-hosted server
    claude mcp add infranodus -- node /path/to/mcp-server-infranodus/dist/index.js

  or connect the InfraNodus connector in claude.ai. A cloud OAuth connector
  keeps its token remotely, so uploads additionally need INFRANODUS_API_KEY.

Looked in: {sources}"""


# ------------------------------------------------------------ MCP transport

def _classify_payload(payload):
    """JSON-RPC payload -> (status, text), status in ok/429/413/error.
    Shared by both transports so retry and bisect behave identically."""
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


class HttpMcpClient:
    """Minimal MCP streamable-HTTP client (JSON-RPC over POST).

    Flow: exchange the API key for a JWT at /oauth/token (the JWT carries a
    stable session id — raw-key auth gets a fresh session per request, which
    breaks the stateful transport), then initialize once and reuse the
    mcp-session-id header for every tools/call. Reconnects transparently on
    401 / stale-session errors (e.g. after a server restart rotates the JWT
    secret)."""

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
            # Not a raw API key? A discovered credential may already be an
            # access token (e.g. an OAuth bearer stored in a local MCP
            # config) — those authenticate directly, without the exchange.
            exchange_err = f"{e.code}: {e.read()[:200]}"
            self.token = self.api_key
        except urllib.error.URLError as e:
            raise RuntimeError(f"cannot reach {self.base_url}: {e}") from e

        try:
            resp, payload = self._rpc("initialize", {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "upload_scopes", "version": "2.0"},
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
        """The transport answers a POST either as plain JSON or as an SSE
        stream of `data:` lines; take the message answering our id."""
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
        """Return (status, text): status is 'ok', '429', '413', or 'error'."""
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
                # 401: token invalidated; 400/404: stale/lost session.
                if e.code in (400, 401, 404) and attempt == "first":
                    self.connect()
                    continue
                return "error", f"HTTP {e.code}: {text}"
            except (urllib.error.URLError, TimeoutError) as e:
                return "error", f"connection failed: {e}"

            return _classify_payload(payload)
        return "error", "reconnect loop exhausted"

    def close(self):
        pass


class StdioMcpClient:
    """MCP stdio transport: launches the user's configured server command and
    speaks newline-delimited JSON-RPC over its stdin/stdout.

    WHY this exists: a locally configured server (`command` + `args`) has no
    HTTP endpoint to post to, so the only way to honour it is to run it. The
    entry's env block is merged into the child environment untouched — the
    script never reads, prints, or re-targets whatever credential is in it.

    Responses are pumped off stdout by a reader thread so a wedged server
    times out instead of hanging the build; non-JSON lines (servers that log
    to stdout) are skipped rather than treated as protocol errors."""

    def __init__(self, spec):
        self.spec = spec
        self.proc = None
        self._rpc_id = 0
        self._lines = queue.Queue()

    def connect(self):
        env = dict(os.environ)
        env.update({str(k): str(v) for k, v in self.spec.env.items()})
        try:
            self.proc = subprocess.Popen(
                [self.spec.command, *self.spec.args],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env=env,
                text=True, encoding="utf-8", errors="replace", bufsize=1)
        except OSError as e:
            raise RuntimeError(
                f"cannot launch {self.spec.endpoint()}: {e}") from e

        def pump(stream, sink):
            for line in stream:
                sink.put(line)
            sink.put(None)

        threading.Thread(target=pump, args=(self.proc.stdout, self._lines),
                         daemon=True).start()

        payload = self._rpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "upload_scopes", "version": "2.0"},
        })
        if payload is None or "error" in payload:
            raise RuntimeError(f"initialize rejected by the server: {payload}")
        self._notify("notifications/initialized")

    def _send(self, msg):
        if self.proc is None or self.proc.poll() is not None:
            raise RuntimeError("the MCP server process is not running")
        try:
            self.proc.stdin.write(json.dumps(msg) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError) as e:
            raise RuntimeError(f"lost the MCP server process: {e}") from e

    def _rpc(self, method, params):
        self._rpc_id += 1
        msg = {"jsonrpc": "2.0", "id": self._rpc_id, "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)
        return self._await(self._rpc_id)

    def _notify(self, method):
        self._send({"jsonrpc": "2.0", "method": method})

    def _await(self, rpc_id):
        deadline = time.monotonic() + HTTP_TIMEOUT
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(
                    f"no reply within {HTTP_TIMEOUT}s from "
                    f"{self.spec.endpoint()}")
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError("the MCP server closed its output stream")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue          # server logging to stdout, not a response
            if isinstance(msg, dict) and msg.get("id") == rpc_id:
                return msg

    def call_tool(self, tool, arguments):
        try:
            payload = self._rpc("tools/call",
                                {"name": tool, "arguments": arguments})
        except RuntimeError as e:
            return "error", str(e)
        return _classify_payload(payload)

    def close(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
            except (OSError, ValueError):
                pass
            self.proc.terminate()


# ---------------------------------------------------------------- chunking

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


def upload_chunk(client, graph_name, chunk, wikilinks_mode="default"):
    """Upload one chunk, handling 429 (backoff) and 413 (bisect). Returns
    the last successful response text, or raises RuntimeError.
    wikilinksMode/maxNodes only take effect when the graph context is first
    created, so passing them on every chunk is safe and only the first
    matters."""
    args = {"graphName": graph_name, "text": chunk, "maxNodes": MAX_NODES}
    if wikilinks_mode != "default":
        args["wikilinksMode"] = wikilinks_mode
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
                raise RuntimeError(f"413 on a tiny chunk, giving up: {out[:300]}")
            print("    413 payload too large, bisecting chunk", flush=True)
            halves = chunk_text(chunk, len(chunk.encode("utf-8")) // 2)
            last = None
            for h in halves:
                last = upload_chunk(client, graph_name, h, wikilinks_mode)
                time.sleep(PACE_SECONDS)
            return last
        raise RuntimeError(f"upload failed: {out[:500]}")
    raise RuntimeError(f"gave up after {MAX_RETRIES} rate-limit retries")


def graph_location(response_text, graph_name):
    """Return (url, account) for an uploaded graph.

    The server answers with the graph's URL, whose path is
    /<account>/<graphName>/...; that account segment is the only record of
    WHICH account now holds the content. A graphName on its own cannot be
    resolved later — the same name means different graphs on different
    servers and accounts — so the account is recorded alongside it."""
    m = re.search(r"https?://[^\s\"'\\]+", response_text or "")
    if not m:
        return None, None
    url = m.group(0).rstrip(".,);")
    parts = [p for p in urllib.parse.urlparse(url).path.split("/") if p]
    if graph_name in parts:
        i = parts.index(graph_name)
        if i > 0:
            return url, parts[i - 1]
    return url, None


def scope_graph_name(prefix, fname):
    scope = re.sub(r"^(repo|vault)-|-ontology\.md$", "", fname)
    return scope, f"{prefix}-{scope}"


# --------------------------------------------- routing metadata + insight log

# What each graph is FOR — recorded in the manifest so the agent can route a
# question to the right graph without any local content files.
SCOPE_PURPOSES = {
    "docs": "documentation prose — what the project is, how things work, "
            "design decisions",
    "code-rationale": "docstrings and WHY/NOTE/TODO/HACK/FIXME comments — "
                      "why the code is the way it is",
    "pdfs": "text extracted from PDF documents (deterministic text-layer "
            "extraction — what the PDFs literally say, no summarization)",
    "history": "commit messages, PR descriptions, issue threads — what "
               "changed, when, and the discussion around it",
    "vault-links": "the vault's page-link structure — how notes reference "
                   "each other",
}


def scope_purpose(scope):
    """Longest-prefix match so filtered scopes (docs-auth) inherit their
    base purpose with the filter noted."""
    for base in sorted(SCOPE_PURPOSES, key=len, reverse=True):
        if scope == base:
            return SCOPE_PURPOSES[base]
        if scope.startswith(base + "-"):
            return (f"{SCOPE_PURPOSES[base]} (filtered scan: "
                    f"{scope[len(base) + 1:]})")
    return "project content"


def harvest_summary(response_text):
    """Pull routing metadata out of a create_knowledge_graph response (its
    text content is a JSON object with mainTopicalClusters / contentGaps /
    graphUrl). Returns {} when unparseable — metadata is best-effort."""
    try:
        data = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out = {}
    topics = data.get("mainTopicalClusters") or data.get("topicalClusters")
    if isinstance(topics, list) and topics:
        out["topics"] = [str(t) for t in topics[:10]]
    gaps = data.get("contentGaps")
    if isinstance(gaps, list) and gaps:
        out["gaps"] = [str(g) for g in gaps[:6]]
    if isinstance(data.get("graphUrl"), str):
        out["graphUrl"] = data["graphUrl"]
    return out


def fetch_hint(client, graph_name):
    """Best-effort structural hint for the build log: the graph's
    textOverview (main concepts, topics, gaps, gateways, diversity) from
    generate_contextual_hint. Returns None on any failure — the hint is
    log enrichment, never a build blocker."""
    status, out = client.call_tool("generate_contextual_hint",
                                   {"graphName": graph_name})
    if status != "ok":
        return None
    try:
        parsed = json.loads(out)
    except (json.JSONDecodeError, TypeError):
        return out or None
    if isinstance(parsed, dict):
        return parsed.get("textOverview") or None
    return parsed if isinstance(parsed, str) else (out or None)


def fetch_structure(client, graph_name):
    """Best-effort structure/development summary via optimize_text_structure
    (accepts graphName; optimize_reasoning is text-only): the diversity
    diagnosis (biased/focused/diversified/dispersed) plus AI suggestions for
    how the graph could be developed further. Returns None on any failure."""
    status, out = client.call_tool("optimize_text_structure",
                                   {"graphName": graph_name})
    if status != "ok":
        return None
    try:
        data = json.loads(out)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    res = {}
    ds = data.get("diversity_stats") or {}
    if ds.get("diversity_score"):
        res["diversity"] = str(ds["diversity_score"]) + (
            f", modularity {ds['modularity_score']}"
            if ds.get("modularity_score") else "")
    if isinstance(data.get("suggestions"), list) and data["suggestions"]:
        res["suggestions"] = [str(s) for s in data["suggestions"]]
    if isinstance(data.get("topicsToDevelop"), list):
        res["topicsToDevelop"] = [str(t) for t in data["topicsToDevelop"][:3]]
    return res or None


def condense(text, limit=400):
    return re.sub(r"\s+", " ", text).strip()[:limit]


REPORT_HEADER = """# InfraNodus log — {project}

Append-only. Builds append a dated section below; query sessions append
dated insights when something non-obvious is learned. Never rewrite or
delete existing entries — the history IS the value.
"""


def append_build_log(root, project, entries):
    """Append one dated build section to infranodus/INFRANODUS_REPORT.md."""
    if not entries:
        return
    path = root / "infranodus" / "INFRANODUS_REPORT.md"
    lines = [f"\n## Build {date.today().isoformat()}\n"]
    for e in entries:
        lines.append(f"### {e['graphName']}" +
                     (f" — {e['url']}" if e.get("url") else ""))
        lines.append(f"- purpose: {e['purpose']}")
        if e.get("endpoint"):
            loc = f"- server: {e.get('transport', '?')} {e['endpoint']}"
            if e.get("account"):
                loc += f" | account: {e['account']}"
            loc += (f" | read back {e['verified']}" if e.get("verified")
                    else " | NOT verified — upload accepted but not readable")
            lines.append(loc)
        if e.get("topics"):
            lines.append(f"- topics: {'; '.join(e['topics'])}")
        if e.get("gaps"):
            lines.append(f"- gaps: {'; '.join(e['gaps'])}")
        st = e.get("structure") or {}
        if st.get("diversity"):
            lines.append(f"- diversity: {st['diversity']}")
        if e.get("hint"):
            lines.append("")
            lines.append("<details><summary>structural hint "
                         "(generate_contextual_hint)</summary>")
            lines.append("")
            lines.append(e["hint"].strip())
            lines.append("")
            lines.append("</details>")
        if st.get("suggestions"):
            lines.append("")
            lines.append("<details><summary>development suggestions "
                         "(optimize_text_structure)</summary>")
            lines.append("")
            for s in st["suggestions"]:
                lines.append(s.strip())
                lines.append("")
            if st.get("topicsToDevelop"):
                lines.append("topics to develop: "
                             + " | ".join(st["topicsToDevelop"]))
                lines.append("")
            lines.append("</details>")
        lines.append("")
    body = "\n".join(lines)
    if path.exists():
        with path.open("a", encoding="utf-8") as f:
            f.write(body)
    else:
        path.write_text(REPORT_HEADER.format(project=project) + body,
                        encoding="utf-8")
    print(f"appended build section to {path.relative_to(root)}")


# ------------------------------------------------------------- registration

CLAUDE_MD_BEGIN = "<!-- infranodus:begin -->"
CLAUDE_MD_END = "<!-- infranodus:end -->"

# Static on purpose: everything graph-specific (names, purposes, topics)
# is read from manifest.json at query time, so re-scoping or renaming a
# graph never leaves this block stale.
CLAUDE_MD_BLOCK = f"""{CLAUDE_MD_BEGIN}
## infranodus

This project's content is indexed as InfraNodus knowledge graphs. The
content lives ONLY in the graphs — there are no local copies of it.
`infranodus/manifest.json` is the routing table: per graph it records
`graphName`, `purpose` (what the graph is for), `topics`, `gaps`,
`hint` (structural overview: main concepts, gateways, relations,
diversity), `diversity` (biased/focused/diversified/dispersed), and
`develop` (how the graph could be developed further). Use `purpose` +
`topics` to pick the graph; use `hint` when they don't disambiguate;
use `diversity` + `develop` for direction/improvement questions.
Each graph also records its provenance — `endpoint` and `transport` (the
MCP server it was uploaded through), `account` (who holds it), and
`verified` (when it was last read back successfully).

Rules:
- For questions about themes, concepts, rationale, or what is missing or
  under-developed, query the graphs BEFORE reading or grepping files.
  Route via the manifest: match the question against each graph's
  `purpose` and `topics`, then call
  `analyze_existing_graph_by_name` (structure: topics, clusters, gaps),
  `retrieve_from_knowledge_base` (content: GraphRAG over the statements),
  `generate_contextual_hint` (broad questions: lightweight structural
  overview of the graph — inject it as context before answering),
  `generate_content_gaps` (direction: what to develop next).
- When synthesizing across graphs or drafting recommendations, run
  `optimize_reasoning` on the draft reasoning: it diagnoses whether it is
  biased / focused / diversified / dispersed and suggests which
  under-represented topics or gaps to develop further.
- Read graph names from `infranodus/manifest.json` — do not guess them.
- If a graph query fails with "select an existing graph context", do NOT
  conclude the graph is missing. Compare the manifest's `endpoint` and
  `account` for that graph against the server this session is connected
  to (`list_graphs`): the same `graphName` is a different graph on a
  different server or account. Report the mismatch instead of retrying.
- `infranodus/INFRANODUS_REPORT.md` is an APPEND-ONLY log: dated build
  sections plus insights from past sessions. Consult it for prior
  findings. After answering, append a dated one-line insight ONLY when
  something non-obvious and reusable was learned (a confirmed gap, a
  correction, a dead end) — never rewrite or delete existing entries.
- These graphs cover meaning and discourse structure, NOT code structure.
  For files, symbols, and call paths use the code-graph tool if one is
  installed (e.g. graphify) — the two are complementary, not competing.
- After adding or substantially editing content, re-run `/infranodus` to
  refresh the affected scope (delete the old graph in InfraNodus first —
  uploads to an existing graphName append).
{CLAUDE_MD_END}
"""


SKILL_MD_BEGIN = "<!-- infranodus-skill:begin -->"
SKILL_MD_END = "<!-- infranodus-skill:end -->"


def _write_marker_block(path, block, begin, end):
    """Insert or replace a marker-delimited block in a markdown file.

    Never rewrites the file: content outside the markers is preserved
    byte-for-byte. Markers (rather than a substring check) are what let a
    re-run REPLACE a stale block instead of skipping it forever.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(block, encoding="utf-8")
        return "created"
    content = path.read_text(encoding="utf-8")
    if begin in content and end in content:
        start, stop = content.index(begin), content.index(end) + len(end)
        updated = content[:start] + block.rstrip("\n") + content[stop:]
        if updated == content:
            return "unchanged"
        path.write_text(updated, encoding="utf-8")
        return "updated"
    path.write_text(content.rstrip("\n") + "\n\n" + block, encoding="utf-8")
    return "appended"


def write_claude_md_block(root):
    """Insert/replace the per-project rules block in <root>/CLAUDE.md."""
    path = root / "CLAUDE.md"
    return _write_marker_block(path, CLAUDE_MD_BLOCK,
                               CLAUDE_MD_BEGIN, CLAUDE_MD_END), path


def register_global_skill():
    """Insert/replace the trigger block in ~/.claude/CLAUDE.md.

    Self-contained on purpose: it derives the skill path and the slash
    command from THIS file's own location, so it works from an installed
    copy with no source repo present, and can never disagree with where the
    skill actually lives. It touches one markdown file and nothing else.
    """
    skill_dir = Path(__file__).resolve().parents[1]
    home = Path.home()
    try:
        shown = "~/" + str(skill_dir.relative_to(home))
    except ValueError:
        shown = str(skill_dir)
    command = skill_dir.name
    block = f"""{SKILL_MD_BEGIN}
# infranodus
- **infranodus** (`{shown}/SKILL.md`) - any text, repo, or vault to a knowledge graph; topics, content gaps, GraphRAG retrieval. Trigger: `/{command}`
When the user types `/{command}`, use the installed infranodus skill before doing anything else.
When a project root has `infranodus/manifest.json`, answer questions about its themes, concepts, rationale, or gaps by querying those graphs first (see that project's CLAUDE.md for the rules).
{SKILL_MD_END}
"""
    path = home / ".claude" / "CLAUDE.md"
    return _write_marker_block(path, block, SKILL_MD_BEGIN, SKILL_MD_END), path


def scope_wikilinks_mode(fname, path=None):
    """Processing mode for a scope file. The generated files declare it in
    their frontmatter (`wikilinksMode: ...`) — that wins, so custom scope
    files work too. Fallback heuristic: link-structure scopes ->
    wikilinksOnly; prose scopes (docs, rationale, history) ->
    parentAndConcepts (the `## [[page]]` heading travels as a per-statement
    parent). Both keep [[name]]-style node naming, so scopes stay
    mergeable."""
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


# --------------------------------------------------------------------- main

def connect_to_configured_server(root):
    """Connect to the InfraNodus MCP server configured for this project.

    One server, one attempt, no fallback: trying a second credential after a
    rejection is how content ends up in an account the user never chose."""
    spec = resolve_mcp_server(root)
    if spec is None:
        sources = ", ".join(str(p) for p, _ in _config_sources(root))
        sys.exit(NO_SERVER_HELP.format(sources=sources))

    if spec.transport == "http":
        key = os.environ.get("INFRANODUS_API_KEY", "").strip()
        if not key:
            sys.exit(
                "the configured InfraNodus MCP server is remote but "
                "INFRANODUS_API_KEY is not set.\n"
                f"{spec.describe()}\n\n"
                "  export INFRANODUS_API_KEY=...   "
                "# infranodus.com -> settings -> API access\n\n"
                "Credentials are taken from the environment only — this "
                "script never reads a key out of an MCP config file.")
        client = HttpMcpClient(spec.url, key)
    else:
        client = StdioMcpClient(spec)

    try:
        client.connect()
    except RuntimeError as e:
        client.close()
        sys.exit("could not connect to the configured InfraNodus MCP "
                 f"server.\n{spec.describe()}\n  error:    {e}\n\n"
                 "Stopping. No other endpoint or credential will be tried — "
                 "fix this server's configuration and re-run.")
    return client, spec


def main():
    ap = argparse.ArgumentParser(
        description="Upload infranodus/ scope files to InfraNodus.")
    ap.add_argument("project_dir", nargs="?", default=".")
    ap.add_argument("--prefix", metavar="NAME",
                    help="graph name prefix (default: <vault|repo>-<dir slug>)")
    ap.add_argument("--force", action="store_true",
                    help="re-upload scopes that already have a graphName "
                         "(APPENDS to the existing graph)")
    ap.add_argument("--save-graph", action="store_true",
                    help="also save infranodus/<scope>-graph.json per scope")
    ap.add_argument("--keep-scopes", action="store_true",
                    help="keep the scope .md files after a successful upload "
                         "(default: they are build intermediates, deleted "
                         "once their statements live in the graph)")
    ap.add_argument("--register-project", action="store_true",
                    help="write the ## infranodus block into CLAUDE.md")
    ap.add_argument("--register-global", action="store_true",
                    help="write the skill trigger block into ~/.claude/CLAUDE.md")
    ap.add_argument("--check-auth", action="store_true",
                    help="no upload: resolve the configured MCP server and "
                         "verify the connection to it")
    args = ap.parse_args()

    root = Path(args.project_dir).resolve()

    if args.check_auth:
        client, spec = connect_to_configured_server(root)
        print("connected OK to the configured InfraNodus MCP server")
        print(spec.describe())
        client.close()
        return

    # Global registration is project-independent — handle it before the
    # manifest check so it works from any directory, graphs or not.
    if args.register_global:
        action, path = register_global_skill()
        print(f"CLAUDE.md {action}: {path}")
        return

    manifest_path = root / "infranodus" / "manifest.json"
    if not manifest_path.exists():
        sys.exit("no infranodus/manifest.json — run repo2statements.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scopes = manifest.get("scopes", {})

    if args.register_project:
        action, path = write_claude_md_block(root)
        print(f"CLAUDE.md {action}: {path}")
        if action in ("created", "appended", "updated"):
            print("  the agent will now query these graphs for questions "
                  "about themes, concepts, rationale, and gaps")
        return

    client, spec = connect_to_configured_server(root)
    print("uploading through the configured InfraNodus MCP server")
    print(spec.describe(), flush=True)

    prefix = args.prefix
    if prefix is None:
        project = re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-")
        kind = "vault" if any(k.startswith("vault-") for k in scopes) else "repo"
        prefix = f"{kind}-{project}"

    log_entries = []
    for fname, meta in scopes.items():
        # Curated scopes (llm-wiki ontologies etc. sharing this manifest)
        # are owned by their authoring skill: never claim them by uploading
        # under this run's prefix or rewriting their graphName/url — even
        # with --force. The delete guard below is the other half of this.
        if meta.get("policy") == "curated":
            print(f"skip {fname} (curated — owned by its authoring skill)")
            continue
        if meta.get("graphName") and not args.force:
            print(f"skip {fname} (already uploaded: {meta['graphName']})")
            continue
        if "file" not in meta:
            # External entries (e.g. graphs exported from the VSCode
            # extension) register a graph without a local scope file —
            # they are query-only here, never uploaded or deleted.
            print(f"skip {fname} (external entry, no scope file)")
            continue
        if meta.get("graphName") and args.force:
            print(f"WARNING: {fname} re-uploads to existing graph "
                  f"{meta['graphName']} — statements APPEND; for a clean "
                  f"rebuild delete the graph in InfraNodus first.")
        scope, graph_name = scope_graph_name(prefix, fname)
        path = root / meta["file"]
        if not path.exists():
            sys.exit(f"scope file missing: {meta['file']} — scope files are "
                     "build intermediates; re-run repo2statements.py first")
        text = strip_frontmatter(path)
        chunks = chunk_text(text)
        print(f"{fname} -> {graph_name} ({len(chunks)} chunk(s))", flush=True)

        mode = scope_wikilinks_mode(fname, path)
        last = None
        for i, chunk in enumerate(chunks):
            print(f"  chunk {i + 1}/{len(chunks)}", flush=True)
            last = upload_chunk(client, graph_name, chunk, mode)
            time.sleep(PACE_SECONDS)

        summary = harvest_summary(last or "")
        url, account = graph_location(
            summary.get("graphUrl") or last or "", graph_name)
        meta["graphName"] = graph_name
        meta["url"] = url
        # Provenance: a graphName is only resolvable together with the server
        # and account that hold it. Without these a later session cannot tell
        # "no such graph" from "not on the server you are talking to".
        meta["endpoint"] = spec.endpoint()
        meta["transport"] = spec.transport
        if account:
            meta["account"] = account
        meta["wikilinksMode"] = mode
        meta["purpose"] = scope_purpose(scope)
        if summary.get("topics"):
            meta["topics"] = summary["topics"]
        if summary.get("gaps"):
            meta["gaps"] = summary["gaps"]
        # First manifest write right away — the graph identity must survive
        # even if the enrichment calls below fail or get rate-limited.
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")

        # Enrichment (best-effort, one paced call each): the structural
        # overview and the structure/development diagnosis — summaries that
        # tell a future agent WHICH graph to query and HOW to develop it.
        time.sleep(PACE_SECONDS)
        hint = fetch_hint(client, graph_name)
        time.sleep(PACE_SECONDS)
        structure = fetch_structure(client, graph_name)
        if hint:
            meta["hint"] = hint.strip()
        if structure:
            if structure.get("diversity"):
                meta["diversity"] = structure["diversity"]
            if structure.get("suggestions"):
                meta["develop"] = [condense(s)
                                   for s in structure["suggestions"][:2]]
        if hint or structure:
            # Both enrichment calls READ the saved graph back, so either one
            # succeeding proves the graph is retrievable through this server
            # with this credential — not merely that the upload returned 200.
            meta["verified"] = date.today().isoformat()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                                     encoding="utf-8")
        else:
            print(f"  WARNING: {graph_name} uploaded but could not be read "
                  f"back from {spec.endpoint()} — not marking it verified",
                  file=sys.stderr, flush=True)
        log_entries.append({"graphName": graph_name, "url": meta["url"],
                            "purpose": meta["purpose"],
                            "endpoint": spec.endpoint(),
                            "transport": spec.transport,
                            "account": account,
                            "verified": meta.get("verified"),
                            "topics": summary.get("topics"),
                            "gaps": summary.get("gaps"),
                            "hint": hint, "structure": structure})

        # Only generated intermediates are deleted — curated scope files
        # (llm-wiki ontologies etc. sharing this manifest) are human-owned
        # and must survive every upload.
        if not args.keep_scopes and meta.get("policy") == "generated":
            path.unlink()
            print(f"  removed {meta['file']} (statements now live in "
                  f"{graph_name}; --keep-scopes retains them)", flush=True)

        if args.save_graph:
            status, out = client.call_tool("analyze_existing_graph_by_name",
                                           {"graphName": graph_name,
                                            "includeGraph": True,
                                            "addNodesAndEdges": True,
                                            "fullGraph": True})
            if status == "ok":
                (root / "infranodus" / f"{scope}-graph.json").write_text(
                    out, encoding="utf-8")
                print(f"  saved infranodus/{scope}-graph.json", flush=True)
            else:
                print(f"  WARNING: could not fetch graph JSON: {out[:200]}",
                      flush=True)
            time.sleep(PACE_SECONDS)

    append_build_log(root, root.name, log_entries)
    print("all scopes uploaded; manifest updated")
    if not (root / "CLAUDE.md").exists() or CLAUDE_MD_BEGIN not in (
            root / "CLAUDE.md").read_text(encoding="utf-8"):
        print("NEXT: run --register-project once to add the always-on block "
              "to CLAUDE.md — without it nothing routes questions to these "
              "graphs.", file=sys.stderr)


if __name__ == "__main__":
    main()
