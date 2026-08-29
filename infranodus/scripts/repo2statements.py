#!/usr/bin/env python3
"""repo2statements — deterministic rationale miner for InfraNodus.

Turns a repo's natural-language layer into InfraNodus statement files
(one statement per line, [[wikilinks]] preserved verbatim), written to
<path>/infranodus/ with `generated: true` frontmatter and registered in
<path>/infranodus/manifest.json.

v1 mines rationale/prose only — deep code-structure extraction
is deferred by design (see docs/todo-graph-repo.md in InfraNodus-Skills).

Sources (repo mode, default):
  - *.md / *.rst / *.txt docs         -> repo-docs-ontology.md
  - *.pdf text layer (see below)      -> repo-pdfs-ontology.md
  - docstrings + WHY:/NOTE:/TODO:/... -> repo-code-rationale-ontology.md
  - git commit bodies, gh PRs/issues  -> repo-history-ontology.md
Structure mode (--structure), a condensed structural map instead of the prose:
  - directory tree, file -> imports (local deps + packages),
    file -> exported symbols, first docstring line per file,
    package manifests -> dependencies    -> repo-structure-ontology.md
  The structure map is small enough to feed generate_ontology_graph (see
  upload_scopes.py --ontology) and is the architecture layer the
  rationale scopes lack. Runs alone; combine with a full run by
  running the script twice (scopes are independent files).
Digest mode (--digest), the LLM-written digest:
  The agent (not this script) reads the target and writes simple statements
  describing how things work — principles, rules, procedures, main ideas —
  in its own words, one per line with [[wikilinks]], grouped under
  `## [[Topic]]` headings, into infranodus/repo-digest-ontology.md
  (vault-digest-ontology.md in a vault). Run with --digest BEFORE
  writing to get the reading list (every file in the target, honouring
  --include / --term; docs, code, and main config files only, capped) and
  the format; run it AGAIN after writing to normalise the frontmatter and
  register the scope in the manifest (policy "authored": the uploader keeps
  the file). Exit code 2 on the first run means "now write the file". Feed the uploaded graph to
  optimize_knowledge_base (focus: codebase | vault | procedural).

Vault mode (--vault):
  - [[wikilink]] / [md](links) between pages -> vault-links-ontology.md

Stdlib only. No LLM. Same input -> same output (modulo git/gh history).

PDFs: extraction is DETERMINISTIC text-layer extraction (what the PDF
literally says), not summarization — summarizing a PDF corpus into a
knowledge base is the llm-wiki skill's job. The Python stays stdlib-only
by shelling out to the first installed converter (pdftotext from poppler,
mutool from mupdf, or markitdown); with none installed, PDFs are reported
as skipped with install guidance. Scanned PDFs without a text layer are
reported as non-minable (OCR is out of scope — route those to llm-wiki).
Extracted text is an in-memory intermediate: no converted files are ever
written into the project.

Usage:
  repo2statements.py [PATH] [--vault] [--max-commits N] [--max-prs N]
                     [--max-issues N] [--no-git] [--no-gh]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "dist", "build", "out", "vendor",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
    "coverage", "target", ".next", ".nuxt", ".obsidian", "infranodus",
    ".idea", ".vscode",
}
DOC_EXTS = {".md", ".mdx", ".markdown", ".rst", ".txt"}
CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cc", ".cs", ".go", ".rs", ".swift", ".kt", ".kts", ".php", ".rb",
    ".scala", ".sh", ".bash", ".zsh", ".lua", ".ex", ".exs", ".sql",
}
MAX_FILE_BYTES = 1_000_000
MAX_PDF_BYTES = 30_000_000   # PDFs are large containers for small text
MAX_STATEMENT_CHARS = 1000
MIN_DOCSTRING_CHARS = 40

# Never mine (or upload) likely-secret material. Matched against the file
# NAME, case-insensitive. Scope files feed a cloud service — err on the
# side of skipping.
SENSITIVE_NAME_RE = re.compile(
    r"^\.env(\..+)?$|^\.?(npmrc|netrc|pgpass|htpasswd)$"
    r"|^id_(rsa|dsa|ecdsa|ed25519)(\..*)?$"
    r"|\.(pem|key|p12|pfx|keystore|jks)$"
    r"|credential|secret|api[_-]?key",
    re.IGNORECASE,
)

TAG_RE = re.compile(
    r"(?:#|//|/\*+|\*|<!--|--|;)\s*(WHY|NOTE|TODO|HACK|FIXME)\b[:\s-]\s*(.+)",
    re.IGNORECASE,
)
PY_DOCSTRING_RE = re.compile(r'"""(.*?)"""|\'\'\'(.*?)\'\'\'', re.S)
C_DOCSTRING_RE = re.compile(r"/\*\*(.*?)\*/", re.S)
WIKILINK_RE = re.compile(r"(?<!\!)\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
MDLINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(\s*<?([^)\s>#?]+\.md)")
TRAILER_RE = re.compile(
    r"^(Co-Authored-By|Signed-off-by|Reviewed-by|Cc|Fixes|Closes|See-also):",
    re.IGNORECASE,
)

# Scan filters, set from CLI args in main(). Empty = no filtering.
INCLUDE_PREFIXES: list[str] = []   # only files under these relative paths
TERMS: list[str] = []              # only files whose content matches any term


def one_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:MAX_STATEMENT_CHARS]


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if SENSITIVE_NAME_RE.search(p.name):
            continue
        if INCLUDE_PREFIXES and not any(
            rel == pref or rel.startswith(pref.rstrip("/") + "/")
            for pref in INCLUDE_PREFIXES
        ):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        if TERMS:
            text = read_text(p).lower()
            if not any(t.lower() in text for t in TERMS):
                continue
        yield p


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# ---------------------------------------------------------------- docs pass

def paragraphs_from_markdown(src: str):
    """Yield prose paragraphs, skipping fenced code blocks; headings become
    their own short statements when they carry more than one word."""
    in_fence = False
    buf: list[str] = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("|"):  # table rows are layout, not prose
            continue
        if not stripped:
            if buf:
                yield " ".join(buf)
                buf = []
            continue
        if stripped.startswith("#"):
            if buf:
                yield " ".join(buf)
                buf = []
            heading = stripped.lstrip("#").strip()
            if len(heading.split()) > 1:
                yield heading
            continue
        buf.append(stripped)
    if buf:
        yield " ".join(buf)


def mine_docs(root: Path, stem_prefix: bool = False) -> list[str]:
    """stem_prefix=True (vault case) names sections after the Obsidian page
    ([[Page A]]) instead of the file path, so content statements share node
    names with in-text wikilinks and the vault link scan.

    Statements are grouped under `## [[<page>]]` headings — the parent-page
    contract of the MCP parentAndConcepts/obsidianStyle wikilinksMode: the
    heading sets the parent for the statements below it, keeping the parent
    OUT of the statement text (an inline [[page]] prefix would suppress all
    non-wikilink words of the statement during processing)."""
    statements = []
    for p in iter_files(root):
        if p.suffix.lower() not in DOC_EXTS:
            continue
        prefix = p.stem if stem_prefix else p.relative_to(root).as_posix()
        page_paras = []
        for para in paragraphs_from_markdown(read_text(p)):
            para = one_line(para)
            # A lone link or a one-word line is not a statement.
            if len(para) < 30 and not WIKILINK_RE.search(para):
                continue
            page_paras.append(para)
        if page_paras:
            statements.append(f"## [[{prefix}]]")
            statements.extend(page_paras)
            statements.append("")
    return statements


# ---------------------------------------------------------------- pdfs pass

def iter_pdfs(root: Path):
    """Same skip/sensitive/--include rules as iter_files, but with the PDF
    size cap and no --term pre-filter (terms match the EXTRACTED text —
    matching them against raw PDF bytes would be meaningless)."""
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() != ".pdf":
            continue
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if SENSITIVE_NAME_RE.search(p.name):
            continue
        if INCLUDE_PREFIXES and not any(
            rel == pref or rel.startswith(pref.rstrip("/") + "/")
            for pref in INCLUDE_PREFIXES
        ):
            continue
        try:
            if p.stat().st_size > MAX_PDF_BYTES:
                continue
        except OSError:
            continue
        yield p


def find_pdf_converter():
    """(name, extract_fn) of the first installed PDF->text converter, or
    None. All three are deterministic text-layer extractors — no OCR, no
    LLM. Tried in order of fidelity/ubiquity."""
    if shutil.which("pdftotext"):     # poppler
        return "pdftotext", lambda p: run(
            ["pdftotext", "-enc", "UTF-8", str(p), "-"], p.parent,
            timeout=120)
    if shutil.which("mutool"):        # mupdf
        return "mutool", lambda p: run(
            ["mutool", "draw", "-F", "text", "-o", "-", str(p)], p.parent,
            timeout=120)
    if shutil.which("markitdown"):
        return "markitdown", lambda p: run(
            ["markitdown", str(p)], p.parent, timeout=120)
    return None


NON_PROSE_LINE_RE = re.compile(r"^[\d\s.\-–—/|:()\[\]]+$")
PAGE_FOOTER_RE = re.compile(r"^page\s+\d+(\s*(of|/)\s*\d+)?$", re.I)


def pdf_paragraphs(raw: str):
    """Deterministic cleanup of converter output, yielding prose paragraphs.

    Rules (pure string operations, reproducible scan-to-scan):
    - re-join words hyphenated across line breaks;
    - drop running headers/footers: short lines whose exact text repeats
      across many pages;
    - drop lines that are only digits/punctuation (page numbers, rules);
    - split paragraphs on blank lines and form-feeds (page breaks);
    - drop paragraphs that are mostly non-letters (tables, figures, math
      debris) — the graph wants prose, not layout."""
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", raw)
    lines = text.replace("\f", "\n\n").splitlines()
    seen = Counter(l.strip() for l in lines if l.strip())

    def is_noise(s: str) -> bool:
        return (NON_PROSE_LINE_RE.match(s) is not None
                or PAGE_FOOTER_RE.match(s) is not None
                or (seen[s] >= 4 and len(s) < 80))

    buf: list[str] = []
    for line in lines:
        s = line.strip()
        if not s or is_noise(s):
            if buf:
                yield " ".join(buf)
                buf = []
            continue
        buf.append(s)
    if buf:
        yield " ".join(buf)


def letters_ratio(s: str) -> float:
    return sum(c.isalpha() or c.isspace() for c in s) / max(len(s), 1)


def mine_pdfs(root: Path, extract, vault: bool) -> tuple[list[str], list[str]]:
    """(statements, no_text_layer_files). Grouped under `## [[<path>]]`
    headings — same parent-page contract as mine_docs. Section names follow
    the docs pass: page stem in a vault, relative path otherwise."""
    statements: list[str] = []
    no_text: list[str] = []
    for p in iter_pdfs(root):
        rel = p.relative_to(root).as_posix()
        raw = extract(p)
        if TERMS and not any(t.lower() in raw.lower() for t in TERMS):
            continue
        paras = []
        for para in pdf_paragraphs(raw):
            para = one_line(para)
            if len(para) < 40 or letters_ratio(para) < 0.6:
                continue
            paras.append(para)
        if not paras:
            no_text.append(rel)
            continue
        statements.append(f"## [[{p.stem if vault else rel}]]")
        statements.extend(paras)
        statements.append("")
    return statements, no_text


def is_vault(root: Path) -> bool:
    """Obsidian vault, or md-dominated folder that should be treated as one."""
    if (root / ".obsidian").is_dir():
        return True
    md = code = 0
    for p in iter_files(root):
        suffix = p.suffix.lower()
        if suffix == ".md":
            md += 1
        elif suffix in CODE_EXTS:
            code += 1
    return md >= 5 and md > code * 2


# ------------------------------------------------------- code-rationale pass

def mine_code_rationale(root: Path) -> list[str]:
    """Grouped under `## [[<filepath>]]` headings — same parent-page contract
    as mine_docs, so file provenance never suppresses the prose."""
    statements = []
    for p in iter_files(root):
        if p.suffix.lower() not in CODE_EXTS:
            continue
        rel = p.relative_to(root).as_posix()
        src = read_text(p)
        if not src:
            continue

        file_statements = []
        docstrings = []
        if p.suffix == ".py":
            for m in PY_DOCSTRING_RE.finditer(src):
                docstrings.append(m.group(1) or m.group(2) or "")
        else:
            for m in C_DOCSTRING_RE.finditer(src):
                body = re.sub(r"^\s*\*\s?", "", m.group(1), flags=re.M)
                docstrings.append(body)
        for ds in docstrings:
            ds = one_line(ds)
            if len(ds) >= MIN_DOCSTRING_CHARS:
                file_statements.append(f"{ds} #docstring")

        for line in src.splitlines():
            m = TAG_RE.search(line)
            if not m:
                continue
            tag = m.group(1).lower()
            text = one_line(re.sub(r"(\*/|-->)\s*$", "", m.group(2)))
            if len(text) >= 15:
                file_statements.append(f"{text} #{tag}")

        if file_statements:
            statements.append(f"## [[{rel}]]")
            statements.extend(file_statements)
            statements.append("")
    return statements


# ------------------------------------------------------------- history pass

def run(cmd: list[str], cwd: Path, timeout: int = 60) -> str:
    try:
        res = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return res.stdout if res.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def mine_git(root: Path, max_commits: int,
             paths: list[str] | None = None) -> list[str]:
    cmd = ["git", "log", "--no-merges", f"-{max_commits}",
           "--format=%s%x1f%b%x1e"]
    if paths:
        cmd += ["--"] + paths
    raw = run(cmd, root)
    statements = []
    for record in raw.split("\x1e"):
        if "\x1f" not in record:
            continue
        subject, body = record.split("\x1f", 1)
        subject = one_line(subject)
        lines = [
            l for l in body.splitlines()
            if l.strip() and not TRAILER_RE.match(l.strip())
        ]
        body_text = one_line(" ".join(lines))
        if len(body_text) < 20:
            continue  # bare one-liner commits carry no rationale
        statements.append(f"{subject}: {body_text} #commit")
    return statements


def mine_gh(root: Path, kind: str, limit: int) -> list[str]:
    raw = run(
        ["gh", kind, "list", "--state", "all", "--limit", str(limit),
         "--json", "number,title,body"],
        root,
        timeout=120,
    )
    if not raw:
        return []
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return []
    tag = "#pr" if kind == "pr" else "#issue"
    label = "PR" if kind == "pr" else "Issue"
    statements = []
    for item in items:
        title = one_line(item.get("title") or "")
        body = item.get("body") or ""
        paras = [one_line(x) for x in re.split(r"\n\s*\n", body)]
        paras = [x for x in paras if len(x) >= 20 and not x.startswith("<!--")]
        if not paras and title:
            statements.append(f"{label} #{item['number']} {title} {tag}")
        for para in paras[:5]:
            statements.append(
                f"{label} #{item['number']} ({title}): {para} {tag}"
            )
    return statements


# --------------------------------------------------------------- vault pass

def mine_vault_links(root: Path) -> list[str]:
    pairs = set()
    for p in iter_files(root):
        if p.suffix.lower() != ".md":
            continue
        src_page = p.stem
        text = read_text(p)
        targets = set()
        for m in WIKILINK_RE.finditer(text):
            targets.add(m.group(1).strip())
        for m in MDLINK_RE.finditer(text):
            targets.add(Path(m.group(1)).stem)
        for tgt in targets:
            if tgt and tgt != src_page:
                pairs.add((src_page, tgt))
    return [f"[[{a}]] links to [[{b}]]" for a, b in sorted(pairs)]


# ------------------------------------------------------------------- output

def scope_wikilinks_mode(name: str) -> str:
    """Processing mode a scope file should be uploaded with (declared in its
    frontmatter so any later consumer knows without heuristics). Link scopes
    are pure [[A]] links to [[B]] statements -> wikilinksOnly; prose scopes
    (and the structure map, whose statements all carry [[wikilinks]] under
    ## [[dir/]] headings) use parentAndConcepts."""
    return ("wikilinksOnly" if name.startswith("vault-links")
            else "parentAndConcepts")


# ------------------------------------------------------------- digest pass

DIGEST_FORMAT = """\
Write infranodus/{fname} — a digest of how this project works, in your own
words, from the files listed above (read them; do not paraphrase file names).
One simple statement per line, grouped under `## [[Topic]]` headings (a
subsystem, workflow, framework, or theme), with [[wikilinks]] on the modules,
concepts, tools, and files a statement is about. Write these kinds of
statements: principles (why it is done this way), rules (what must / must
not happen), procedures (when X, do Y, then Z), hand-offs (where one part
passes control or data to another), main ideas, and gaps (what the content
leaves unexplained — you may mark those with #gap, nothing else). Do not tag
every line: tags become the most connected nodes of the graph and distort
the structural analysis this digest is for. Cover every area of the target;
skip files that add nothing. Between 100 and 300 lines — below 100 the
structural diagnosis is unreliable. Example:

## [[Adding a tool]]
Every tool is a schema in [[src/schemas]], a handler in [[src/tools]], and a registration in [[src/index.ts]].
Handlers return an error content block instead of throwing so the [[MCP client]] can show the message.
Nothing says how a tool should report partial progress to the [[MCP client]]. #gap

Then run this command again to register the file, and upload_scopes.py.
"""
DIGEST_LIST_CAP = 200
DIGEST_CONFIG_NAMES = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "Cargo.toml",
    "go.mod", "Gemfile", "composer.json", "Dockerfile", "Makefile",
    "docker-compose.yml", "docker-compose.yaml", "tsconfig.json",
}
DIGEST_SKIP_RE = re.compile(
    r"(\.lock$|-lock\.(json|yaml|yml)$|\.min\.(js|css)$|^LICENSE|^llms.*\.txt$)",
    re.I)
DIGEST_FNAME_RE = re.compile(r"^(repo|vault)-digest(-.+)?-ontology\.md$")


def digest_reading_list(root: Path) -> list[str]:
    """Files worth reading in the target (honours --include / --term):
    documents first, then code, then the recognised config files. Lock
    files, minified bundles, licences, binaries, and dotfiles are left
    out — the agent reads these and writes the digest."""
    docs, code, conf = [], [], []
    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        if DIGEST_SKIP_RE.search(p.name) or p.name.startswith("."):
            continue
        ext = p.suffix.lower()
        if ext in DOC_EXTS:
            docs.append(rel)
        elif ext in CODE_EXTS:
            code.append(rel)
        elif p.name in DIGEST_CONFIG_NAMES:
            conf.append(rel)
    return docs + code + conf


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)


def register_digest(out_dir: Path, fname: str, mode: str) -> int | None:
    """Normalise the agent-written digest's frontmatter (BOM stripped;
    generated/generator/mode/wikilinksMode/updated set by the script, any
    other keys the agent wrote kept) and return its statement count. None
    when the file does not exist."""
    path = out_dir / fname
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    extra: list[str] = []
    m = FRONTMATTER_RE.match(text)
    if m:
        ours = {"generated", "generator", "mode", "wikilinksMode", "updated"}
        extra = [line for line in m.group(1).splitlines()
                 if line.strip() and line.split(":", 1)[0].strip() not in ours]
        body = text[m.end():]
    else:
        body = text
    body = body.lstrip("\r\n")
    frontmatter = "\n".join(
        ["---", "generated: false", "generator: agent", f"mode: {mode}",
         "wikilinksMode: parentAndConcepts",
         f"updated: {date.today().isoformat()}", *extra, "---", ""])
    new_text = frontmatter + "\n" + body
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return count_statements(body.splitlines())


def retire_old_digest(out_dir: Path, fname: str) -> None:
    """Before registering an agent-written digest, drop manifest entries
    for the SAME principles scope left by the old regex extractor (source
    repo2statements — possibly under the repo- name in a vault). Their
    graphs contain mined sentences, and uploads append, so the user must
    delete those graphs on the server before the new digest goes up."""
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    scopes = manifest.get("scopes", {})
    suffix_part = DIGEST_FNAME_RE.match(fname).group(2) or ""
    stale = [k for k, v in scopes.items()
             if (mm := DIGEST_FNAME_RE.match(k))
             and (mm.group(2) or "") == suffix_part
             and v.get("source") == "repo2statements"]
    for k in stale:
        entry = scopes.pop(k)
        if entry.get("graphName"):
            print(f"NOTE: {k} was built by the old extractor and uploaded as "
                  f"{entry['graphName']}; delete that graph on the server "
                  f"before uploading (uploads append to an existing graph).")
        if k != fname and (out_dir / k).exists():
            (out_dir / k).unlink()
    if stale:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")


# ---------------------------------------------------------- structure pass

TS_IMPORT_RE = re.compile(
    r'^\s*(?:import|export)\s+(?:[^\'"\n]*?\s+from\s+)?[\'"]([^\'"\n]+)[\'"]',
    re.M)
REQUIRE_RE = re.compile(r'require\(\s*[\'"]([^\'"\n]+)[\'"]\s*\)')
TS_EXPORT_RE = re.compile(
    r'^\s*export\s+(?:default\s+)?(?:async\s+)?'
    r'(?:function|class|const|let|var|interface|type|enum)\s+'
    r'([A-Za-z_$][\w$]*)', re.M)
PY_IMPORT_RE = re.compile(r'^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))',
                          re.M)
PY_DEF_RE = re.compile(r'^(?:def|class)\s+([A-Za-z_]\w*)', re.M)
STRUCTURE_MAX_EXPORTS = 25
STRUCTURE_MAX_IMPORTS = 25
STRUCTURE_HEADLINE_CHARS = 160


def _resolve_local_import(from_file: Path, spec: str, root: Path,
                          known: set[str]) -> str | None:
    """Map a relative import specifier to a repo path when the target exists
    in the scan (index files and stripped .js -> .ts extensions included)."""
    if not spec.startswith("."):
        return None
    base = (from_file.parent / spec).resolve()
    candidates = [base]
    stem = re.sub(r"\.(js|mjs|cjs|jsx)$", "", str(base))
    for ext in (".ts", ".tsx", ".js", ".mjs", ".jsx", ".py"):
        candidates.append(Path(stem + ext))
        candidates.append(base / f"index{ext}")
    for c in candidates:
        try:
            rel = c.relative_to(root).as_posix()
        except ValueError:
            continue
        if rel in known:
            return rel
    return None


def _first_docstring_line(src: str, suffix: str) -> str:
    m = (PY_DOCSTRING_RE.search(src) if suffix == ".py"
         else C_DOCSTRING_RE.search(src))
    if not m:
        return ""
    body = m.group(1) or (m.group(2) if m.lastindex and m.lastindex >= 2 else "")
    body = re.sub(r"^\s*\*\s?", "", body or "", flags=re.M)
    first = one_line(body.strip().split("\n\n")[0])
    return first[:STRUCTURE_HEADLINE_CHARS]


def mine_structure(root: Path) -> list[str]:
    """Condensed structural map: one `## [[dir/]]` section per directory,
    then per file its imports (local paths resolved, packages by name),
    exported symbols, and the first docstring line. Every statement carries
    [[wikilinks]], so under parentAndConcepts only real entities become
    nodes. Deterministic; a few statements per file."""
    files = [p for p in iter_files(root) if p.suffix.lower() in CODE_EXTS]
    known = {p.relative_to(root).as_posix() for p in files}
    by_dir: dict[str, list[str]] = {}

    for p in files:
        rel = p.relative_to(root).as_posix()
        src = read_text(p)
        if not src:
            continue
        stmts: list[str] = []
        suffix = p.suffix.lower()

        imports: list[str] = []
        if suffix == ".py":
            for m in PY_IMPORT_RE.finditer(src):
                mod = m.group(1) or m.group(2) or ""
                if not mod:
                    continue
                if mod.startswith("."):
                    target = _resolve_local_import(
                        p, "./" + mod.lstrip(".").replace(".", "/"), root, known)
                    imports.append(target or mod)
                else:
                    local = (root / (mod.replace(".", "/") + ".py"))
                    imports.append(local.relative_to(root).as_posix()
                                   if local.exists() else mod.split(".")[0])
        else:
            specs = TS_IMPORT_RE.findall(src) + REQUIRE_RE.findall(src)
            for spec in specs:
                target = _resolve_local_import(p, spec, root, known)
                if target:
                    imports.append(target)
                elif not spec.startswith("."):
                    # package name (scoped packages keep their scope)
                    parts = spec.split("/")
                    imports.append("/".join(parts[:2]) if spec.startswith("@")
                                   else parts[0])
        seen: list[str] = []
        for imp in imports:
            if imp not in seen and imp != rel:
                seen.append(imp)
        for imp in seen[:STRUCTURE_MAX_IMPORTS]:
            stmts.append(f"[[{rel}]] imports [[{imp}]]")

        exports = (PY_DEF_RE.findall(src) if suffix == ".py"
                   else TS_EXPORT_RE.findall(src))
        uniq: list[str] = []
        for e in exports:
            if e not in uniq and not e.startswith("_"):
                uniq.append(e)
        if uniq:
            names = ", ".join(f"[[{e}]]" for e in uniq[:STRUCTURE_MAX_EXPORTS])
            stmts.append(f"[[{rel}]] exports {names}")

        headline = _first_docstring_line(src, suffix)
        if len(headline) >= 15:
            stmts.append(f"[[{rel}]]: {headline}")

        if not stmts:
            stmts.append(f"[[{rel}]] is a {suffix.lstrip('.')} file")
        d = p.parent.relative_to(root).as_posix()
        by_dir.setdefault(d if d != "." else "", []).extend(stmts)

    # package manifests -> external dependencies
    manifest_stmts: list[str] = []
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(read_text(pkg))
            for key in ("dependencies", "peerDependencies"):
                for dep in sorted((data.get(key) or {}).keys()):
                    manifest_stmts.append(f"[[package.json]] depends on [[{dep}]]")
            for script in sorted((data.get("scripts") or {}).keys()):
                manifest_stmts.append(
                    f"[[package.json]] defines script [[npm run {script}]]")
        except (json.JSONDecodeError, AttributeError):
            pass
    for req in ("requirements.txt", "pyproject.toml"):
        f = root / req
        if f.exists():
            for line in read_text(f).splitlines():
                m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*(?:[<>=!~\[]|$)", line)
                if m and not line.lstrip().startswith(("#", "[")):
                    manifest_stmts.append(f"[[{req}]] depends on [[{m.group(1)}]]")
    if manifest_stmts:
        by_dir.setdefault("", []).extend(manifest_stmts)

    statements: list[str] = []
    for d in sorted(by_dir):
        statements.append(f"## [[{d + '/' if d else '/'}]]")
        statements.extend(by_dir[d])
        statements.append("")
    return statements


HEADING_LINE_RE = re.compile(r"^\s*#{1,6}\s")


def count_statements(statements: list[str]) -> int:
    """Real statements only — `## [[page]]` heading lines and blank
    separators are structure, not statements ('#tag...' without a space
    after the hashes is a statement, not a heading)."""
    return sum(1 for s in statements
               if s.strip() and not HEADING_LINE_RE.match(s))


def write_scope(out_dir: Path, name: str, statements: list[str],
                mode: str, suffix: str = "") -> Path | None:
    if not statements:
        return None
    if suffix:
        name = name.replace("-ontology.md", f"-{suffix}-ontology.md")
    path = out_dir / name
    frontmatter = (
        "---\n"
        "generated: true\n"
        "generator: repo2statements\n"
        f"mode: {mode}\n"
        f"wikilinksMode: {scope_wikilinks_mode(name)}\n"
        f"updated: {date.today().isoformat()}\n"
        "---\n\n"
    )
    path.write_text(frontmatter + "\n".join(statements) + "\n",
                    encoding="utf-8")
    return path


def update_manifest(out_dir: Path, written: dict[str, int]) -> None:
    manifest_path = out_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    scopes = manifest.setdefault("scopes", {})
    for fname, count in written.items():
        entry = scopes.setdefault(fname, {})
        authored = bool(DIGEST_FNAME_RE.match(fname))
        entry.update({
            "file": f"infranodus/{fname}",
            "policy": "authored" if authored else "generated",
            "source": "agent" if authored else "repo2statements",
            "statements": count,
            "updated": date.today().isoformat(),
        })
        entry.setdefault("graphName", None)  # filled in after upload
        entry.setdefault("url", None)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--vault", action="store_true",
                    help="page-link scan for an Obsidian/md vault")
    ap.add_argument("--structure", action="store_true",
                    help="condensed structural map only (tree, imports, "
                         "exports, docstring headlines, manifests) -> "
                         "repo-structure-ontology.md; code repos only — a "
                         "vault's structure is its link map (--vault)")
    ap.add_argument("--digest", action="store_true",
                    help="LLM-written digest of how the project works: "
                         "first run prints the reading list and the format "
                         "for infranodus/repo-digest-ontology.md "
                         "(vault-… in a vault); once the agent has written "
                         "it, the same command registers it in the manifest")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--no-gh", action="store_true")
    ap.add_argument("--max-commits", type=int, default=200)
    ap.add_argument("--max-prs", type=int, default=50)
    ap.add_argument("--max-issues", type=int, default=50)
    ap.add_argument("--include", action="append", default=[],
                    metavar="RELPATH",
                    help="only scan these folders/files (relative to PATH; "
                         "repeatable)")
    ap.add_argument("--term", action="append", default=[], metavar="TERM",
                    help="only scan files whose content contains TERM "
                         "(case-insensitive; repeatable, any-of)")
    ap.add_argument("--suffix", default="", metavar="SLUG",
                    help="scope-filename suffix for filtered scans "
                         "(auto-derived from --include/--term if omitted)")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    out_dir = root / "infranodus"
    out_dir.mkdir(exist_ok=True)

    if sum(map(bool, (args.structure, args.principles, args.vault))) > 1:
        print("--structure, --digest and --vault are separate runs; "
              "run them one at a time (scopes share the manifest)",
              file=sys.stderr)
        return 1
    # Vault detection looks at the whole folder, not the filtered target:
    # `--include docs/` on a code repo must not turn it into a vault.
    vault = is_vault(root)

    global INCLUDE_PREFIXES, TERMS
    INCLUDE_PREFIXES = [x.strip("/").strip() for x in args.include if x.strip()]
    TERMS = [x for x in args.term if x.strip()]
    filtered = bool(INCLUDE_PREFIXES or TERMS)
    suffix = args.suffix
    if filtered and not suffix:
        raw = (INCLUDE_PREFIXES or TERMS)[0]
        suffix = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")[:30]

    written: dict[str, int] = {}

    def keep(name: str, statements: list[str], mode: str) -> None:
        path = write_scope(out_dir, name, statements, mode, suffix=suffix)
        if path:
            written[path.name] = count_statements(statements)

    if args.structure:
        if is_vault(root):
            print("--structure maps code (imports, exports, docstrings); a "
                  "vault's structure is its link map: use --vault",
                  file=sys.stderr)
            return 1
        keep("repo-structure-ontology.md", mine_structure(root), "repo")
    elif args.principles:
        # The agent writes this scope; the script only lists what to read
        # and registers the result. A vault gets the vault- prefix so the
        # graph is named vault-<p>-digest (Step 6 of the runbook).
        mode = "vault" if vault else "repo"
        fname = f"{mode}-digest-ontology.md"
        if suffix:
            fname = fname.replace("-ontology.md", f"-{suffix}-ontology.md")
        count = register_digest(out_dir, fname, mode)
        if count is None:
            files = digest_reading_list(root)
            if not files:
                print("digest: nothing to read in this target",
                      file=sys.stderr)
                return 1
            shown = files[:DIGEST_LIST_CAP]
            print(f"digest: {len(files)} file(s) to read"
                  + (f" (filtered: {suffix})" if suffix else "") + "\n")
            for rel in shown:
                print(f"  {rel}")
            if len(files) > len(shown):
                print(f"  … and {len(files) - len(shown)} more: narrow the "
                      "target with --include / --term (one digest per "
                      "target) and tell the user what was left out")
            print("\n" + DIGEST_FORMAT.format(fname=fname))
            return 2
        if count == 0:
            print(f"infranodus/{fname} has no statements (headings and "
                  "blank lines only) — not registered", file=sys.stderr)
            return 1
        retire_old_digest(out_dir, fname)
        written[fname] = count
        print(f"registered infranodus/{fname}: {count} statement(s) — "
              "edit it in place and run again to re-register, or delete it "
              "to get the reading list and rewrite it")
    elif args.vault:
        # explicit --vault: map the vault structure ONLY
        keep("vault-links-ontology.md", mine_vault_links(root), "vault")
    else:
        keep("repo-docs-ontology.md", mine_docs(root, stem_prefix=vault),
             "repo")

        pdfs = list(iter_pdfs(root))
        if pdfs:
            conv = find_pdf_converter()
            if conv is None:
                print(f"NOTE: {len(pdfs)} PDF(s) found but no converter "
                      "installed — skipped. Install poppler for "
                      "deterministic PDF mining (`brew install poppler` / "
                      "`apt install poppler-utils`), or use the llm-wiki "
                      "skill for LLM-authored summarization.")
            else:
                conv_name, extract = conv
                pdf_statements, no_text = mine_pdfs(root, extract, vault)
                if no_text:
                    shown = ", ".join(no_text[:5])
                    more = " …" if len(no_text) > 5 else ""
                    print(f"NOTE: {len(no_text)} PDF(s) with no extractable "
                          f"text layer (scanned images?) — OCR is out of "
                          f"scope here; the llm-wiki skill can handle "
                          f"those: {shown}{more}")
                keep("repo-pdfs-ontology.md", pdf_statements, "repo")

        if vault:
            # bare launch in a vault/md folder: content AND link structure
            keep("vault-links-ontology.md", mine_vault_links(root), "vault")

        keep("repo-code-rationale-ontology.md", mine_code_rationale(root),
             "repo")

        # History is not file-scoped, so a filtered scan skips it — except
        # a pure folder filter, which git can honor via pathspec.
        history: list[str] = []
        if not TERMS:
            if not args.no_git:
                if INCLUDE_PREFIXES:
                    history += mine_git(root, args.max_commits,
                                        paths=INCLUDE_PREFIXES)
                else:
                    history += mine_git(root, args.max_commits)
            if not args.no_gh and not INCLUDE_PREFIXES:
                history += mine_gh(root, "pr", args.max_prs)
                history += mine_gh(root, "issue", args.max_issues)
        keep("repo-history-ontology.md", history, "repo")

    if not written:
        print("no statements extracted (empty corpus?)")
        return 1

    update_manifest(out_dir, written)
    for fname, count in written.items():
        print(f"infranodus/{fname}: {count} statements")
    print("next: python3 upload_scopes.py <path>  (uploads each scope and "
          "records graphName + url in infranodus/manifest.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
