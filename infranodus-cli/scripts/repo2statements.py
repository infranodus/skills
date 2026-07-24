#!/usr/bin/env python3
"""repo2statements — deterministic rationale miner for InfraNodus.

Turns a repo's natural-language layer into InfraNodus statement files
(one statement per line, [[wikilinks]] preserved verbatim), written to
<path>/infranodus/ with `generated: true` frontmatter and registered in
<path>/infranodus/manifest.json.

v1 mines rationale/prose only — code-structure extraction (--structure)
is deferred by design (see docs/todo-graph-repo.md in InfraNodus-Skills).

Sources (repo mode, default):
  - *.md / *.rst / *.txt docs         -> repo-docs-ontology.md
  - docstrings + WHY:/NOTE:/TODO:/... -> repo-code-rationale-ontology.md
  - git commit bodies, gh PRs/issues  -> repo-history-ontology.md

Vault mode (--vault):
  - [[wikilink]] / [md](links) between pages -> vault-links-ontology.md

Stdlib only. No LLM. Same input -> same output (modulo git/gh history).

Usage:
  repo2statements.py [PATH] [--vault] [--max-commits N] [--max-prs N]
                     [--max-issues N] [--no-git] [--no-gh]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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
MAX_STATEMENT_CHARS = 1000
MIN_DOCSTRING_CHARS = 40

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


def one_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:MAX_STATEMENT_CHARS]


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
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


def mine_docs(root: Path) -> list[str]:
    statements = []
    for p in iter_files(root):
        if p.suffix.lower() not in DOC_EXTS:
            continue
        rel = p.relative_to(root).as_posix()
        for para in paragraphs_from_markdown(read_text(p)):
            para = one_line(para)
            # A lone link or a one-word line is not a statement.
            if len(para) < 30 and not WIKILINK_RE.search(para):
                continue
            statements.append(f"[[{rel}]]: {para}")
    return statements


# ------------------------------------------------------- code-rationale pass

def mine_code_rationale(root: Path) -> list[str]:
    statements = []
    for p in iter_files(root):
        if p.suffix.lower() not in CODE_EXTS:
            continue
        rel = p.relative_to(root).as_posix()
        src = read_text(p)
        if not src:
            continue

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
                statements.append(f"[[{rel}]]: {ds} #docstring")

        for line in src.splitlines():
            m = TAG_RE.search(line)
            if not m:
                continue
            tag = m.group(1).lower()
            text = one_line(re.sub(r"(\*/|-->)\s*$", "", m.group(2)))
            if len(text) >= 15:
                statements.append(f"[[{rel}]]: {text} #{tag}")
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


def mine_git(root: Path, max_commits: int) -> list[str]:
    raw = run(
        ["git", "log", "--no-merges", f"-{max_commits}",
         "--format=%s%x1f%b%x1e"],
        root,
    )
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

def write_scope(out_dir: Path, name: str, statements: list[str],
                mode: str) -> Path | None:
    if not statements:
        return None
    path = out_dir / name
    frontmatter = (
        "---\n"
        "generated: true\n"
        "generator: repo2statements\n"
        f"mode: {mode}\n"
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
        entry.update({
            "file": f"infranodus/{fname}",
            "policy": "generated",
            "source": "repo2statements",
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
                    help="DEFERRED: code-structure extraction (not in v1)")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--no-gh", action="store_true")
    ap.add_argument("--max-commits", type=int, default=200)
    ap.add_argument("--max-prs", type=int, default=50)
    ap.add_argument("--max-issues", type=int, default=50)
    args = ap.parse_args()

    if args.structure:
        print("--structure is deferred to a later version (v1 mines "
              "rationale only). See InfraNodus-Skills/docs/todo-graph-repo.md")
        return 2

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 1
    out_dir = root / "infranodus"
    out_dir.mkdir(exist_ok=True)

    written: dict[str, int] = {}

    if args.vault:
        links = mine_vault_links(root)
        if write_scope(out_dir, "vault-links-ontology.md", links, "vault"):
            written["vault-links-ontology.md"] = len(links)
    else:
        docs = mine_docs(root)
        if write_scope(out_dir, "repo-docs-ontology.md", docs, "repo"):
            written["repo-docs-ontology.md"] = len(docs)

        rationale = mine_code_rationale(root)
        if write_scope(out_dir, "repo-code-rationale-ontology.md",
                       rationale, "repo"):
            written["repo-code-rationale-ontology.md"] = len(rationale)

        history: list[str] = []
        if not args.no_git:
            history += mine_git(root, args.max_commits)
        if not args.no_gh:
            history += mine_gh(root, "pr", args.max_prs)
            history += mine_gh(root, "issue", args.max_issues)
        if write_scope(out_dir, "repo-history-ontology.md", history, "repo"):
            written["repo-history-ontology.md"] = len(history)

    if not written:
        print("no statements extracted (empty corpus?)")
        return 1

    update_manifest(out_dir, written)
    for fname, count in written.items():
        print(f"infranodus/{fname}: {count} statements")
    print("next: upload each scope via create_knowledge_graph, then record "
          "graphName + url in infranodus/manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
