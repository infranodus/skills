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
  the file). Exit code 2 on the first run means "now write the file". Feed
  the uploaded graph to optimize_knowledge_base (focus: codebase | vault |
  procedural).

Vault mode (--vault):
  - [[wikilink]] / [md](links) between pages -> vault-links-ontology.md

Change tracking (--detect / --update), for scopes that are already uploaded:
  Every generated scope entry in the manifest records the git commit it was
  built at (`builtAtCommit`), the --include/--term filters that defined it
  (`filters`), and a per-file index (`files`: heading prefix -> sha1 of the
  EXTRACTED text, so formatting-only edits do not register). The history
  scope records cursors instead (`history`: lastCommit / lastPr /
  lastIssue). The heading prefix (`## [[docs/api.md]]`) is what the MCP
  server stores as each statement's category under parentAndConcepts, so
  the index keys are exactly what `delete_statements({categories})` needs
  to remove one file's statements from the graph.
  --detect  re-walks each scope with its stored filters and prints, per
            scope, the new / modified / deleted files (JSON on stdout, a
            one-line summary per scope on stderr). No writes.
  --update  extracts the new and modified files (and history past the
            cursors) into infranodus/<scope>-delta-ontology.md, whose
            frontmatter names the target graph and the categories to
            replace; upload_scopes.py deletes those categories' statements
            and appends the delta to the same graph. Deleted files are
            listed for removal only. Link scopes (wikilinksOnly, no
            categories) are re-uploaded whole with `replaceAll: true`.
  A scope built before change tracking has no index: rebuild it once
  (plain run, then `upload_scopes.py --force`) to enable updates.

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
  repo2statements.py [PATH] --detect [--scope NAME] [--path RELPATH]
  repo2statements.py [PATH] --update [--scope NAME] [--path RELPATH]
"""
from __future__ import annotations

import argparse
import hashlib
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


# ------------------------------------------------------------------ sections

# A mined unit is a Section: (prefix, relpath, statements). `prefix` is the
# `## [[prefix]]` heading its statements are grouped under — the file's
# relative POSIX path in repo mode, the page stem in a vault, the directory
# (`src/`) in the structure map, the source page in the link scan. Under
# parentAndConcepts the MCP server stores that heading as a per-statement
# category, so the prefix is also the key `delete_statements({categories})`
# needs to remove exactly this file's statements later — the manifest's
# `files` index is keyed by it, verbatim.
Section = tuple


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def flatten_sections(sections: list[Section], headed: bool = True) -> list[str]:
    """Sections -> statement lines. Headed scopes get the `## [[prefix]]`
    heading + blank separator per section; link scopes are bare lines."""
    out: list[str] = []
    for prefix, _rel, stmts in sections:
        if not stmts:
            continue
        if headed:
            out.append(f"## [[{prefix}]]")
            out.extend(stmts)
            out.append("")
        else:
            out.extend(stmts)
    return out


def hash_sections(sections: list[Section]) -> dict[str, str]:
    """prefix -> sha1 of the extracted text (two files sharing a prefix —
    same page stem in two vault folders — hash together, as they share a
    category on the server)."""
    by_prefix: dict[str, list[str]] = {}
    for prefix, _rel, stmts in sections:
        if stmts:
            by_prefix.setdefault(prefix, []).extend(stmts)
    return {k: sha1_text("\n".join(v)) for k, v in by_prefix.items()}


def git_head(root: Path) -> str | None:
    out = run(["git", "rev-parse", "HEAD"], root).strip()
    return out or None


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


def mine_docs(root: Path, stem_prefix: bool = False) -> list[Section]:
    """stem_prefix=True (vault case) names sections after the Obsidian page
    ([[Page A]]) instead of the file path, so content statements share node
    names with in-text wikilinks and the vault link scan.

    Statements are grouped under `## [[<page>]]` headings — the parent-page
    contract of the MCP parentAndConcepts/obsidianStyle wikilinksMode: the
    heading sets the parent for the statements below it, keeping the parent
    OUT of the statement text (an inline [[page]] prefix would suppress all
    non-wikilink words of the statement during processing)."""
    sections: list[Section] = []
    for p in iter_files(root):
        if p.suffix.lower() not in DOC_EXTS:
            continue
        rel = p.relative_to(root).as_posix()
        prefix = p.stem if stem_prefix else rel
        page_paras = []
        for para in paragraphs_from_markdown(read_text(p)):
            para = one_line(para)
            # A lone link or a one-word line is not a statement.
            if len(para) < 30 and not WIKILINK_RE.search(para):
                continue
            page_paras.append(para)
        if page_paras:
            sections.append((prefix, rel, page_paras))
    return sections


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


def mine_pdfs(root: Path, extract, vault: bool) -> tuple[list[Section], list[str]]:
    """(sections, no_text_layer_files). Grouped under `## [[<path>]]`
    headings — same parent-page contract as mine_docs. Section names follow
    the docs pass: page stem in a vault, relative path otherwise."""
    sections: list[Section] = []
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
        sections.append((p.stem if vault else rel, rel, paras))
    return sections, no_text


def mine_pdf_sections(root: Path, vault: bool, quiet: bool = False) -> list[Section]:
    """The PDF pass as the build runs it: find the converter, extract, and
    (unless quiet) print the notes about missing converters and PDFs with no
    text layer. Empty when there are no PDFs or no converter."""
    pdfs = list(iter_pdfs(root))
    if not pdfs:
        return []
    conv = find_pdf_converter()
    if conv is None:
        if not quiet:
            print(f"NOTE: {len(pdfs)} PDF(s) found but no converter "
                  "installed — skipped. Install poppler for "
                  "deterministic PDF mining (`brew install poppler` / "
                  "`apt install poppler-utils`), or use the llm-wiki "
                  "skill for LLM-authored summarization.")
        return []
    _conv_name, extract = conv
    sections, no_text = mine_pdfs(root, extract, vault)
    if no_text and not quiet:
        shown = ", ".join(no_text[:5])
        more = " …" if len(no_text) > 5 else ""
        print(f"NOTE: {len(no_text)} PDF(s) with no extractable "
              f"text layer (scanned images?) — OCR is out of "
              f"scope here; the llm-wiki skill can handle "
              f"those: {shown}{more}")
    return sections


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

def mine_code_rationale(root: Path) -> list[Section]:
    """Grouped under `## [[<filepath>]]` headings — same parent-page contract
    as mine_docs, so file provenance never suppresses the prose."""
    sections: list[Section] = []
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
            sections.append((rel, rel, file_statements))
    return sections


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
             paths: list[str] | None = None,
             since: str | None = None) -> list[str]:
    """Commit statements, newest first. `since` (a commit hash) restricts
    the walk to `since..HEAD` — the history scope's update cursor."""
    cmd = ["git", "log", "--no-merges", f"-{max_commits}",
           "--format=%s%x1f%b%x1e"]
    if since:
        cmd.append(f"{since}..HEAD")
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


def gh_numbers(root: Path, kind: str, limit: int) -> list[int] | None:
    """Numbers of the newest `limit` PRs/issues, or None when gh is not
    installed / not authenticated (the caller cannot tell "none" from
    "unknown" otherwise)."""
    if not shutil.which("gh"):
        return None
    raw = run(["gh", kind, "list", "--state", "all", "--limit", str(limit),
               "--json", "number"], root, timeout=120)
    if not raw:
        return None
    try:
        return [int(i["number"]) for i in json.loads(raw) if "number" in i]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def mine_gh(root: Path, kind: str, limit: int,
            after: int | None = None) -> tuple[list[str], int | None]:
    """(statements, highest number seen). `after` skips items numbered at
    or below the history scope's cursor, so an update mines only what is
    new since the last build."""
    raw = run(
        ["gh", kind, "list", "--state", "all", "--limit", str(limit),
         "--json", "number,title,body"],
        root,
        timeout=120,
    )
    if not raw:
        return [], None
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return [], None
    tag = "#pr" if kind == "pr" else "#issue"
    label = "PR" if kind == "pr" else "Issue"
    statements = []
    highest: int | None = None
    for item in items:
        try:
            number = int(item["number"])
        except (KeyError, TypeError, ValueError):
            continue
        highest = number if highest is None else max(highest, number)
        if after is not None and number <= after:
            continue
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
    return statements, highest


def mine_history(root: Path, opts: dict, cursors: dict | None = None
                 ) -> tuple[list[str], dict]:
    """The history scope: commit bodies via git, PRs/issues via gh, past the
    given cursors when there are any. Returns (statements, new cursors).
    opts: max_commits, max_prs, max_issues, no_git, no_gh. A term filter
    disables history (it is not file-scoped); a folder filter is honoured
    by git's pathspec and disables the gh part."""
    cursors = dict(cursors or {})
    new = {"lastCommit": cursors.get("lastCommit"),
           "lastPr": cursors.get("lastPr"),
           "lastIssue": cursors.get("lastIssue")}
    statements: list[str] = []
    if TERMS:
        return statements, new
    if not opts.get("no_git"):
        head = git_head(root)
        since = cursors.get("lastCommit")
        if head and since != head:
            statements += mine_git(root, opts["max_commits"],
                                   paths=INCLUDE_PREFIXES or None,
                                   since=since)
        if head:
            new["lastCommit"] = head
    if not opts.get("no_gh") and not INCLUDE_PREFIXES:
        for kind, key, limit in (("pr", "lastPr", opts["max_prs"]),
                                 ("issue", "lastIssue", opts["max_issues"])):
            stmts, highest = mine_gh(root, kind, limit, after=cursors.get(key))
            statements += stmts
            if highest is not None:
                old = cursors.get(key)
                new[key] = highest if old is None else max(old, highest)
    return statements, new


def cursor_is_reachable(root: Path, commit: str) -> bool:
    res = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                         cwd=root, capture_output=True)
    return res.returncode == 0


def detect_history(root: Path, cursors: dict, opts: dict) -> dict:
    """Count commits / PRs / issues past the stored cursors without
    extracting anything. gh is consulted only when installed."""
    res: dict = {"newCommits": 0, "newPrs": 0, "newIssues": 0}
    if not opts.get("no_git") and cursors.get("lastCommit"):
        last = cursors["lastCommit"]
        if not cursor_is_reachable(root, last):
            return {"status": "unknown",
                    "reason": f"history cursor {last[:12]} is no longer on "
                              "this branch (rebase?); rebuild the history "
                              "scope with --force"}
        cmd = ["git", "rev-list", "--count", "--no-merges", f"{last}..HEAD"]
        if INCLUDE_PREFIXES:
            cmd += ["--"] + INCLUDE_PREFIXES
        out = run(cmd, root).strip()
        res["newCommits"] = int(out) if out.isdigit() else 0
    if not opts.get("no_gh") and not INCLUDE_PREFIXES:
        for kind, key, out_key, limit in (
                ("pr", "lastPr", "newPrs", opts["max_prs"]),
                ("issue", "lastIssue", "newIssues", opts["max_issues"])):
            numbers = gh_numbers(root, kind, limit)
            if numbers is None:
                continue
            last = cursors.get(key)
            res[out_key] = (len(numbers) if last is None
                            else sum(1 for n in numbers if n > last))
    res["status"] = ("changed" if any(res[k] for k in
                                      ("newCommits", "newPrs", "newIssues"))
                     else "clean")
    return res


# --------------------------------------------------------------- vault pass

def mine_vault_links(root: Path) -> list[Section]:
    """One section per source page: its `[[A]] links to [[B]]` lines. The
    scope is uploaded wikilinksOnly (no headings, no categories), so the
    per-page grouping only serves change detection."""
    seen: set[tuple[str, str]] = set()
    sections: list[Section] = []
    for p in iter_files(root):
        if p.suffix.lower() != ".md":
            continue
        src_page = p.stem
        rel = p.relative_to(root).as_posix()
        text = read_text(p)
        targets = set()
        for m in WIKILINK_RE.finditer(text):
            targets.add(m.group(1).strip())
        for m in MDLINK_RE.finditer(text):
            targets.add(Path(m.group(1)).stem)
        lines = []
        for tgt in sorted(targets):
            if tgt and tgt != src_page and (src_page, tgt) not in seen:
                seen.add((src_page, tgt))
                lines.append(f"[[{src_page}]] links to [[{tgt}]]")
        if lines:
            sections.append((src_page, rel, lines))
    return sections


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


LEGACY_PRINCIPLES_RE = re.compile(r"^(repo|vault)-principles(-.+)?-ontology\.md$")


def adopt_legacy_digest(out_dir: Path, fname: str) -> None:
    """The digest scope used to be called principles: if an agent-written
    principles file for the same target is on disk and no digest file is,
    rename it so the register step picks it up."""
    if (out_dir / fname).exists():
        return
    legacy = fname.replace("-digest", "-principles", 1)
    if (out_dir / legacy).exists():
        (out_dir / legacy).rename(out_dir / fname)
        print(f"NOTE: renamed infranodus/{legacy} -> {fname} (the scope is "
              "now called digest)")


def retire_old_digest(out_dir: Path, fname: str) -> list[str]:
    """Before registering an agent-written digest, drop stale manifest
    entries for the same target: the script-generated structure map that
    used to carry the digest name (source repo2statements), and any entry
    under the old principles name. Their graphs hold other content, so
    their graph names are returned: the new entry records them as
    `supersedes` and the uploader clears each one (delete_statements
    deleteAll) before the digest goes up."""
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    scopes = manifest.get("scopes", {})
    suffix_part = DIGEST_FNAME_RE.match(fname).group(2) or ""
    stale = []
    for k, v in scopes.items():
        m = DIGEST_FNAME_RE.match(k)
        if m and (m.group(2) or "") == suffix_part \
                and v.get("source") == "repo2statements":
            stale.append((k, "the script-generated structure map"))
            continue
        m = LEGACY_PRINCIPLES_RE.match(k)
        if m and (m.group(2) or "") == suffix_part:
            stale.append((k, "the earlier principles version of this mode"))
    superseded: list[str] = []
    for k, why in stale:
        entry = scopes.pop(k)
        if entry.get("graphName"):
            superseded.append(entry["graphName"])
            print(f"NOTE: {k} was {why} and is uploaded as "
                  f"{entry['graphName']}; the uploader will clear that "
                  f"graph before uploading the digest.")
        if k != fname and (out_dir / k).exists():
            (out_dir / k).unlink()
    if stale:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")
    return superseded


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


def mine_structure(root: Path) -> list[Section]:
    """Condensed structural map: one `## [[dir/]]` section per directory,
    then per file its imports (local paths resolved, packages by name),
    exported symbols, and the first docstring line. Every statement carries
    [[wikilinks]], so under parentAndConcepts only real entities become
    nodes. Deterministic; a few statements per file. Sections (and so the
    change index and the replace categories) are per directory."""
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

    return [(d + "/" if d else "/", d, by_dir[d]) for d in sorted(by_dir)]


HEADING_LINE_RE = re.compile(r"^\s*#{1,6}\s")
SECTION_HEADING_RE = re.compile(r"^##\s*\[\[(.+?)\]\]\s*$")


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


def update_manifest(out_dir: Path, written: dict[str, dict]) -> None:
    """written: scope filename -> the entry fields this build produced
    (statements, builtAtCommit, filters, files | history, supersedes).
    Existing routing/provenance fields (graphName, url, hint, ...) are
    kept: a rebuilt scope keeps its graph identity, and the uploader's
    --force clears that graph before re-uploading it."""
    manifest_path = out_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    scopes = manifest.setdefault("scopes", {})
    for fname, fields in written.items():
        entry = scopes.setdefault(fname, {})
        authored = bool(DIGEST_FNAME_RE.match(fname))
        entry.update({
            "file": f"infranodus/{fname}",
            "policy": "authored" if authored else "generated",
            "source": "agent" if authored else "repo2statements",
            "updated": date.today().isoformat(),
        })
        entry.update(fields)
        entry.setdefault("graphName", None)  # filled in after upload
        entry.setdefault("url", None)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                             encoding="utf-8")


# ------------------------------------------------------ change tracking

SCOPE_FNAME_RE = re.compile(
    r"^(?P<mode>repo|vault)-"
    r"(?P<kind>docs|pdfs|code-rationale|history|links|structure|digest)"
    r"(?:-(?P<suffix>.+?))?(?P<delta>-delta)?-ontology\.md$")


def scope_kind(fname: str) -> tuple[str | None, str | None, bool]:
    """(kind, mode, is_delta) for a scope filename; kind None when the
    name is not one of ours."""
    m = SCOPE_FNAME_RE.match(fname)
    if not m:
        return None, None, False
    return m.group("kind"), m.group("mode"), bool(m.group("delta"))


def scope_label(fname: str) -> str:
    """Short name for messages: repo-docs-auth-ontology.md -> docs-auth."""
    return re.sub(r"^(repo|vault)-|-ontology\.md$", "", fname)


def match_scope(fname: str, entry: dict, wanted: str) -> bool:
    return wanted in (fname, scope_label(fname), entry.get("graphName"))


def apply_filters(entry: dict) -> None:
    """Re-apply the --include / --term filters a scope was built with."""
    global INCLUDE_PREFIXES, TERMS
    f = entry.get("filters") or {}
    INCLUDE_PREFIXES = [x for x in (f.get("include") or []) if x]
    TERMS = [x for x in (f.get("terms") or []) if x]


def mine_scope(kind: str, root: Path, vault: bool, hist_opts: dict,
               cursors: dict | None = None, quiet: bool = False):
    """Re-run one scope's pass -> (sections, history_statements,
    new_cursors). File-based kinds fill sections; history the other two."""
    if kind == "docs":
        return mine_docs(root, stem_prefix=vault), [], None
    if kind == "pdfs":
        return mine_pdf_sections(root, vault, quiet=quiet), [], None
    if kind == "code-rationale":
        return mine_code_rationale(root), [], None
    if kind == "structure":
        return mine_structure(root), [], None
    if kind == "links":
        return mine_vault_links(root), [], None
    if kind == "history":
        stmts, cur = mine_history(root, hist_opts, cursors)
        return [], stmts, cur
    raise ValueError(f"unknown scope kind {kind}")


def under_path(rel_or_prefix: str, path: str | None) -> bool:
    if not path:
        return True
    p = path.strip("/")
    x = rel_or_prefix.strip("/")
    return bool(p) and (x == p or x.startswith(p + "/"))


def diff_index(stored: dict[str, str], sections: list[Section],
               path: str | None = None):
    """(new, modified, deleted, current_index) of prefixes against the
    stored index. --path narrows the lists to files under it: new/modified
    by their real path, deleted by their prefix (a deleted vault page is
    known only by its stem, so it matches only when --path names it)."""
    current = hash_sections(sections)
    rel_of: dict[str, str] = {}
    for prefix, rel, stmts in sections:
        if stmts:
            rel_of.setdefault(prefix, rel)
    new = [k for k in current if k not in stored]
    modified = [k for k in current if k in stored and stored[k] != current[k]]
    deleted = [k for k in stored if k not in current]
    if path:
        def keep(k: str) -> bool:
            return under_path(rel_of.get(k, k), path) or under_path(k, path)
        new = [k for k in new if keep(k)]
        modified = [k for k in modified if keep(k)]
        deleted = [k for k in deleted if under_path(k, path)]
    return sorted(new), sorted(modified), sorted(deleted), current


UNTRACKED_REASON = ("built before change tracking; rebuild once "
                    "(repo2statements.py with the same flags, then "
                    "upload_scopes.py --force) to enable updates")


def trackable(fname: str, entry: dict) -> tuple[str | None, dict | None]:
    """(kind, None) when the entry can be diffed, else (kind, report)
    explaining why not — pending delta, authored, untracked, foreign."""
    if entry.get("deltaOf"):
        return None, {"status": "pending",
                      "reason": f"delta of {entry['deltaOf']} awaiting upload "
                                f"({entry.get('statements', 0)} statements) "
                                "— run upload_scopes.py"}
    if entry.get("policy") == "authored":
        return None, {"status": "authored",
                      "reason": "agent-written scope: edit it in place and "
                                "re-upload with --force (the uploader clears "
                                "the graph first)"}
    if entry.get("policy") != "generated" or "file" not in entry:
        return None, None
    kind, _mode, is_delta = scope_kind(fname)
    if kind is None or is_delta or kind == "digest":
        return None, None
    if (kind == "history" and not entry.get("history")) or \
            (kind != "history" and "files" not in entry):
        return kind, {"status": "unknown", "reason": UNTRACKED_REASON}
    return kind, None


def detect_changes(root: Path, scopes: dict, hist_opts: dict, vault: bool,
                   only: str | None = None, path: str | None = None) -> dict:
    """--detect: per scope, what changed since it was built. No writes."""
    report: dict = {}
    for fname, entry in scopes.items():
        if only and not match_scope(fname, entry, only):
            continue
        kind, problem = trackable(fname, entry)
        if problem:
            report[fname] = problem
            continue
        if kind is None:
            continue
        apply_filters(entry)
        if kind == "history":
            report[fname] = detect_history(root, entry["history"], hist_opts)
            continue
        sections, _, _ = mine_scope(kind, root, vault, hist_opts, quiet=True)
        new, modified, deleted, _ = diff_index(entry["files"], sections, path)
        report[fname] = {
            "status": "changed" if (new or modified or deleted) else "clean",
            "new": new, "modified": modified, "deleted": deleted,
        }
    return report


def summarize(fname: str, r: dict) -> str:
    label = scope_label(fname)
    st = r.get("status")
    if st == "clean":
        return f"{label}: clean"
    if st == "changed" and "new" in r:
        return (f"{label}: +{len(r['new'])} new / {len(r['modified'])} "
                f"modified / {len(r['deleted'])} deleted")
    if st == "changed":
        parts = [f"{r['newCommits']} new commits" if r.get("newCommits") else "",
                 f"{r['newPrs']} new PRs" if r.get("newPrs") else "",
                 f"{r['newIssues']} new issues" if r.get("newIssues") else ""]
        return f"{label}: " + ", ".join(p for p in parts if p)
    return f"{label}: {st} — {r.get('reason', '')}"


def write_delta(out_dir: Path, name: str, statements: list[str], mode: str,
                graph_name: str, parent: str, replace_categories: list[str],
                replace_all: bool) -> Path:
    """A delta scope file: same frontmatter contract as a scope, plus the
    upload instructions — the graph to append to, the parent scope, and
    the categories whose statements the uploader deletes first
    (`replaceAll: true` for link scopes, which carry no categories)."""
    path = out_dir / name
    lines = ["---", "generated: true", "generator: repo2statements",
             f"mode: {mode}", f"wikilinksMode: {scope_wikilinks_mode(name)}",
             f"updated: {date.today().isoformat()}", "delta: true",
             f"graphName: {json.dumps(graph_name)}",
             f"deltaOf: {json.dumps(parent)}"]
    if replace_all:
        lines.append("replaceAll: true")
    if replace_categories:
        lines.append("replaceCategories:")
        lines += [f"  - {json.dumps(c)}" for c in replace_categories]
    else:
        lines.append("replaceCategories: []")
    lines += ["---", ""]
    path.write_text("\n".join(lines) + "\n" + "\n".join(statements) + "\n",
                    encoding="utf-8")
    return path


def read_delta(path: Path) -> tuple[list[Section], list[str]]:
    """(sections, loose statements) of a pending delta file, so a second
    --update before the upload merges into it instead of losing it."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    sections: list[Section] = []
    loose: list[str] = []
    cur: list[str] | None = None
    for line in body.splitlines():
        if not line.strip():
            continue
        h = SECTION_HEADING_RE.match(line)
        if h:
            cur = []
            sections.append((h.group(1), h.group(1), cur))
            continue
        (loose if cur is None else cur).append(line)
    return sections, loose


def update_scopes(root: Path, out_dir: Path, manifest: dict, hist_opts: dict,
                  vault: bool, only: str | None = None,
                  path: str | None = None) -> list[str]:
    """--update: write a delta file per changed scope and advance the
    manifest (index merged, deleted keys dropped, cursors moved). Returns
    the delta filenames written."""
    scopes = manifest.setdefault("scopes", {})
    today = date.today().isoformat()
    head = git_head(root)
    written: list[str] = []
    for fname, entry in list(scopes.items()):
        if only and not match_scope(fname, entry, only):
            continue
        kind, problem = trackable(fname, entry)
        if problem:
            if problem["status"] != "pending":
                print(f"{scope_label(fname)}: {problem['status']} — "
                      f"{problem['reason']}", file=sys.stderr)
            continue
        if kind is None:
            continue
        label = scope_label(fname)
        if not entry.get("graphName"):
            print(f"{label}: not uploaded yet — nothing to update; upload "
                  "it (upload_scopes.py) or run the build again",
                  file=sys.stderr)
            continue
        apply_filters(entry)
        _k, mode, _d = scope_kind(fname)
        delta_name = fname.replace("-ontology.md", "-delta-ontology.md")
        delta_path = out_dir / delta_name
        pending = scopes.get(delta_name) or {}
        pending_sections: list[Section] = []
        pending_loose: list[str] = []
        if pending and delta_path.exists():
            pending_sections, pending_loose = read_delta(delta_path)
        replace_cats = sorted(set(pending.get("replaceCategories") or []))
        replace_all = bool(pending.get("replaceAll"))

        if kind == "history":
            cur = entry["history"]
            last = cur.get("lastCommit")
            if last and not hist_opts.get("no_git") \
                    and not cursor_is_reachable(root, last):
                print(f"{label}: history cursor {last[:12]} is no longer on "
                      "this branch (rebase?) — rebuild the history scope "
                      "with --force", file=sys.stderr)
                continue
            new_stmts, cursors = mine_history(root, hist_opts, cur)
            if not new_stmts:
                print(f"{label}: no changes", file=sys.stderr)
                continue
            statements = pending_loose + new_stmts
            entry["history"] = cursors
            summary = f"{len(new_stmts)} new history statements"
        else:
            sections, _, _ = mine_scope(kind, root, vault, hist_opts,
                                        quiet=True)
            new, modified, deleted, current = diff_index(
                entry["files"], sections, path)
            if not (new or modified or deleted):
                print(f"{label}: no changes", file=sys.stderr)
                continue
            changed = set(new) | set(modified)
            if kind == "links":
                # wikilinksOnly: no categories to replace — the whole scope
                # goes up again after the graph is cleared.
                delta_sections = sections
                replace_all, replace_cats = True, []
            else:
                gone = changed | set(deleted)
                delta_sections = [s for s in pending_sections
                                  if s[0] not in gone]
                delta_sections += [s for s in sections if s[0] in changed]
                replace_cats = sorted(set(replace_cats) | set(modified)
                                      | set(deleted))
            statements = flatten_sections(delta_sections,
                                          headed=(kind != "links"))
            files = dict(entry["files"])
            for k in changed:
                files[k] = current[k]
            for k in deleted:
                files.pop(k, None)
            entry["files"] = files
            summary = (f"+{len(new)} new / {len(modified)} modified / "
                       f"{len(deleted)} deleted")

        write_delta(out_dir, delta_name, statements, mode or "repo",
                    entry["graphName"], fname, replace_cats, replace_all)
        entry["updated"] = today
        entry["builtAtCommit"] = head
        count = count_statements(statements)
        scopes[delta_name] = {
            "file": f"infranodus/{delta_name}",
            "policy": "generated",
            "source": "repo2statements",
            "statements": count,
            "updated": today,
            "deltaOf": fname,
            "replaceCategories": replace_cats,
            "replaceAll": replace_all,
            "graphName": None,
            "url": None,
        }
        written.append(delta_name)
        print(f"infranodus/{delta_name}: {count} statements ({summary}"
              + (f"; replaces {len(replace_cats)} file(s)" if replace_cats
                 else "; replaces the whole graph" if replace_all else "")
              + f") -> {entry['graphName']}")
    if written:
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return written


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
    ap.add_argument("--detect", action="store_true",
                    help="no extraction: compare each uploaded scope with "
                         "the working tree (its stored filters re-applied) "
                         "and print new / modified / deleted files as JSON "
                         "(stdout) plus a one-line summary per scope (stderr)")
    ap.add_argument("--update", action="store_true",
                    help="extract only what changed since the last build "
                         "into infranodus/<scope>-delta-ontology.md and "
                         "advance the manifest; upload_scopes.py then "
                         "replaces the changed files' statements in place")
    ap.add_argument("--scope", default=None, metavar="NAME",
                    help="with --detect/--update: only this scope (manifest "
                         "filename, short name such as docs or docs-auth, "
                         "or graphName)")
    ap.add_argument("--path", dest="only_path", default=None,
                    metavar="RELPATH",
                    help="with --detect/--update: only files under this "
                         "path (relative to PATH)")
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

    hist_opts = {"max_commits": args.max_commits, "max_prs": args.max_prs,
                 "max_issues": args.max_issues, "no_git": args.no_git,
                 "no_gh": args.no_gh}

    if args.detect or args.update:
        if args.detect and args.update:
            print("--detect and --update are separate runs", file=sys.stderr)
            return 1
        if args.include or args.term:
            print("NOTE: --include/--term are ignored with --detect/--update "
                  "— each scope re-applies the filters it was built with",
                  file=sys.stderr)
        manifest_path = out_dir / "manifest.json"
        if not manifest_path.exists():
            print("no infranodus/manifest.json — nothing to update; run a "
                  "build first", file=sys.stderr)
            return 1
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("infranodus/manifest.json is not valid JSON", file=sys.stderr)
            return 1
        scopes = manifest.get("scopes", {})
        vault = is_vault(root)   # whole folder, before any scope filter
        if args.detect:
            report = detect_changes(root, scopes, hist_opts, vault,
                                    only=args.scope, path=args.only_path)
            for fname, r in report.items():
                print(summarize(fname, r), file=sys.stderr)
            if not report:
                print("no trackable scopes in the manifest"
                      + (f" matching {args.scope}" if args.scope else ""),
                      file=sys.stderr)
            print(json.dumps(report, indent=2))
            return 0
        written_deltas = update_scopes(root, out_dir, manifest, hist_opts,
                                       vault, only=args.scope, path=args.only_path)
        if not written_deltas:
            print("no changes")
            return 0
        print("next: python3 upload_scopes.py <path>  (replaces the changed "
              "files' statements in the existing graphs)")
        return 0

    if sum(map(bool, (args.structure, args.digest, args.vault))) > 1:
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

    # Change-tracking foundation, recorded per scope so --detect/--update
    # can re-walk exactly this scope later.
    built_at = git_head(root)
    filters = {"include": list(INCLUDE_PREFIXES), "terms": list(TERMS)}
    written: dict[str, dict] = {}

    def keep(name: str, sections: list[Section], mode: str,
             headed: bool = True) -> None:
        statements = flatten_sections(sections, headed)
        path = write_scope(out_dir, name, statements, mode, suffix=suffix)
        if path:
            written[path.name] = {
                "statements": count_statements(statements),
                "builtAtCommit": built_at,
                "filters": filters,
                "files": hash_sections(sections),
            }

    if args.structure:
        sections = mine_structure(root)
        if not sections:
            print("--structure maps code (imports, exports, docstrings) and "
                  "found no code files here; a vault's structure is its "
                  "link map: use --vault", file=sys.stderr)
            return 1
        keep("repo-structure-ontology.md", sections, "repo")
    elif args.digest:
        # The agent writes this scope; the script only lists what to read
        # and registers the result. A vault gets the vault- prefix so the
        # graph is named vault-<p>-digest (Step 6 of the runbook).
        mode = "vault" if vault else "repo"
        fname = f"{mode}-digest-ontology.md"
        if suffix:
            fname = fname.replace("-ontology.md", f"-{suffix}-ontology.md")
        adopt_legacy_digest(out_dir, fname)
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
        superseded = retire_old_digest(out_dir, fname)
        written[fname] = {"statements": count, "builtAtCommit": built_at,
                          "filters": filters}
        if superseded:
            written[fname]["supersedes"] = superseded
        print(f"registered infranodus/{fname}: {count} statement(s) — "
              "edit it in place and run again to re-register, or delete it "
              "to get the reading list and rewrite it")
    elif args.vault:
        # explicit --vault: map the vault structure ONLY
        keep("vault-links-ontology.md", mine_vault_links(root), "vault",
             headed=False)
    else:
        keep("repo-docs-ontology.md", mine_docs(root, stem_prefix=vault),
             "repo")
        keep("repo-pdfs-ontology.md", mine_pdf_sections(root, vault), "repo")

        if vault:
            # bare launch in a vault/md folder: content AND link structure
            keep("vault-links-ontology.md", mine_vault_links(root), "vault",
                 headed=False)

        keep("repo-code-rationale-ontology.md", mine_code_rationale(root),
             "repo")

        # History is not file-scoped: a term filter skips it, a folder
        # filter is honoured via git's pathspec (see mine_history). The
        # scope records cursors instead of a file index.
        history, cursors = mine_history(root, hist_opts)
        path = write_scope(out_dir, "repo-history-ontology.md", history,
                           "repo", suffix=suffix)
        if path:
            written[path.name] = {
                "statements": count_statements(history),
                "builtAtCommit": built_at,
                "filters": filters,
                "history": cursors,
            }

    if not written:
        print("no statements extracted (empty corpus?)")
        return 1

    update_manifest(out_dir, written)
    for fname, fields in written.items():
        print(f"infranodus/{fname}: {fields['statements']} statements")
    print("next: python3 upload_scopes.py <path>  (uploads each scope and "
          "records graphName + url in infranodus/manifest.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
