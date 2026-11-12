#!/usr/bin/env python3
"""Build the Claude directory edition of the infranodus plugin.

    python3 scripts/build_claude_directory.py [--check]

Anthropic's directory (claude.ai/directory) accepts programs, scripts and
other code files only from Verified organizations. The full plugin in
infranodus/ ships Python extraction programs, so the directory gets its own
edition: the same skill with the script-driven parts replaced by
agent-driven ones, and nothing but Markdown, JSON and a PNG in the folder.

Output (committed, because the directory reads the repository):

    claude-directory/infranodus/        <- the plugin path to submit

Sources:

    infranodus/SKILL.md                         shared sections, verbatim
    infranodus/.claude-plugin/{plugin.json,icon.png}   manifest, version, icon
    claude-directory/src/infranodus/            the parts that differ
    LICENSE

--check builds into a temporary folder and fails when the committed output
differs from it (run in CI and before a release). Both modes fail when the
output breaks a directory rule this script knows about.
"""
import argparse
import filecmp
import json
import re
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FULL = ROOT / "infranodus"
SRC = ROOT / "claude-directory" / "src" / "infranodus"
OUT = ROOT / "claude-directory" / "infranodus"

# Every `## ` section of infranodus/SKILL.md, by the start of its heading:
# None keeps the section as it is, a file name takes that file from SRC
# instead. A section missing from this map stops the build, so a new section
# in the full skill is a decision here and never a silent copy.
SECTIONS = {
    "How this skill talks to InfraNodus": "connection.md",
    "Quick orientation": None,
    "Analyze and optimize memories": None,
    "Repo / Vault Graphs": "repo-vault.md",
    "Companion skills": None,
}

ALLOWED_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
}
ALLOWED_NAMES = {"LICENSE", "README", "NOTICE", ".gitignore"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
SYSTEM_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}
MAX_TEXT_BYTES = 256 * 1024
README_MIN_WORDS = 40

# Text that would bring back what the directory refused or held: a call to
# a bundled program, or a credential taken from the user's machine.
FORBIDDEN = [
    (re.compile(r"INFRANODUS_API_KEY"), "names the INFRANODUS_API_KEY variable"),
    (re.compile(r"\bscripts/"), "points at a scripts/ folder"),
    (re.compile(r"\b[\w-]+\.(py|sh|js|mjs|cjs|ts)\b"), "names a program file"),
    (re.compile(r"\bpython3?\b"), "runs python"),
    (re.compile(r"\$\{?[A-Z][A-Z0-9_]*(TOKEN|KEY|SECRET|PASSWORD)\b"),
     "reads a credential from the environment"),
]

# The directory's scan holds a skill whose instructions put a remote server
# address beside words for a credential, even in a sentence that forbids
# using one. The address and those words stay in the README, which is the
# listing and not instructions.
SKILL_FORBIDDEN = [
    (re.compile(r"mcp\.infranodus\.com"), "names the server address"),
    (re.compile(r"(?i)\bAPI key\b|\bcredentials?\b|\bpasswords?\b|\bsecret key\b"),
     "uses a word for a credential"),
    (re.compile(r"(?i)\b(sign-in|key|token)s?\b[^.\n]{0,60}\b(environment|machine|config files?)\b"),
     "puts a credential word beside the user's machine"),
]


def split_skill(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        sys.exit("error: infranodus/SKILL.md has no frontmatter")
    body = text[match.end():]
    parts = re.split(r"(?m)^(?=## )", body)
    return match.group(1), parts[0], parts[1:]


def frontmatter(source):
    name = re.search(r"(?m)^name:\s*(.+)$", source)
    if not name:
        sys.exit("error: infranodus/SKILL.md has no name")
    description = " ".join((SRC / "skill-description.txt").read_text(encoding="utf-8").split())
    lines = ["---", f"name: {name.group(1).strip()}", "description: >-"]
    lines += ["  " + line for line in textwrap.wrap(description, 76)]
    lines.append("---")
    return "\n".join(lines) + "\n"


def build_skill():
    source, preamble, sections = split_skill((FULL / "SKILL.md").read_text(encoding="utf-8"))
    seen = set()
    body = [preamble]
    for section in sections:
        heading = section.splitlines()[0][3:].strip()
        key = next((k for k in SECTIONS if heading.startswith(k)), None)
        if key is None:
            sys.exit(
                f'error: infranodus/SKILL.md has a section "{heading}" that '
                "scripts/build_claude_directory.py does not know. Add it to "
                "SECTIONS: keep it, or replace it with a file in "
                "claude-directory/src/infranodus/."
            )
        seen.add(key)
        override = SECTIONS[key]
        if override is None:
            body.append(section)
        else:
            body.append((SRC / override).read_text(encoding="utf-8").rstrip("\n") + "\n\n")
    missing = set(SECTIONS) - seen
    if missing:
        sys.exit(f"error: infranodus/SKILL.md no longer has: {', '.join(sorted(missing))}")
    return frontmatter(source) + "".join(body).rstrip("\n") + "\n"


def build(out):
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / "references").mkdir()

    (out / "SKILL.md").write_text(build_skill(), encoding="utf-8")
    shutil.copyfile(SRC / "repo-graph.md", out / "references" / "repo-graph.md")
    shutil.copyfile(SRC / "README.md", out / "README.md")
    shutil.copyfile(ROOT / "LICENSE", out / "LICENSE")
    # The manifest is the full plugin's, byte for byte: one name, one
    # version, one listing. The release workflow bumps it there.
    shutil.copyfile(FULL / ".claude-plugin" / "plugin.json", out / ".claude-plugin" / "plugin.json")
    shutil.copyfile(FULL / ".claude-plugin" / "icon.png", out / ".claude-plugin" / "icon.png")


def readme_words(text):
    prose = re.sub(r"```.*?```", " ", text, flags=re.S)
    return len(re.findall(r"\b\w+\b", prose))


def check_policy(out):
    """The directory rules for an organization that is not Verified, as far
    as they can be checked here. The portal runs more."""
    errors = []
    files = sorted(p for p in out.rglob("*") if p.is_file() or p.is_symlink())
    for path in files:
        rel = path.relative_to(out).as_posix()
        if path.is_symlink():
            errors.append(f"{rel}: symbolic link")
            continue
        if path.name in SYSTEM_FILES or "__MACOSX" in path.parts:
            errors.append(f"{rel}: system file")
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES and path.name not in ALLOWED_NAMES:
            errors.append(f"{rel}: file type outside Markdown, text, JSON, YAML and images")
            continue
        data = path.read_bytes()
        if data.startswith(b"#!"):
            errors.append(f"{rel}: starts with #!")
        if path.suffix.lower() in IMAGE_SUFFIXES:
            continue
        if len(data) > MAX_TEXT_BYTES:
            errors.append(f"{rel}: over 256 KiB")
        if b"\x00" in data:
            errors.append(f"{rel}: NUL byte")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: not UTF-8")
            continue
        if path.name == "LICENSE":
            continue
        for pattern, why in FORBIDDEN:
            hit = pattern.search(text)
            if hit:
                line = text.count("\n", 0, hit.start()) + 1
                errors.append(f"{rel}:{line}: {why} ({hit.group(0)})")
        if path.name != "README.md" and path.suffix.lower() == ".md":
            for pattern, why in SKILL_FORBIDDEN:
                hit = pattern.search(text)
                if hit:
                    line = text.count("\n", 0, hit.start()) + 1
                    errors.append(f"{rel}:{line}: {why} ({hit.group(0)})")

    for forbidden_dir in ("scripts", "bin", "hooks", "workflows"):
        if (out / forbidden_dir).exists():
            errors.append(f"{forbidden_dir}/: not accepted from an organization that is not Verified")
    if (out / ".mcp.json").exists():
        servers = json.loads((out / ".mcp.json").read_text(encoding="utf-8")).get("mcpServers", {})
        for name, server in servers.items():
            if "command" in server:
                errors.append(f".mcp.json: {name} is a local MCP server")

    manifest = json.loads((out / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    for key in ("hooks", "mcpServers", "lspServers", "userConfig", "commands", "agents"):
        if key in manifest:
            errors.append(f"plugin.json: {key} is set; this edition is one skill")

    skill = (out / "SKILL.md").read_text(encoding="utf-8")
    keys = re.findall(r"(?m)^([A-Za-z_-]+):", skill.split("---\n")[1])
    if keys != ["name", "description"]:
        errors.append(f"SKILL.md: frontmatter keys are {keys}, expected name and description only")
    description = " ".join((SRC / "skill-description.txt").read_text(encoding="utf-8").split())
    if len(description) > 1024:
        errors.append(f"SKILL.md: description is {len(description)} characters (max 1024)")
    for link in re.findall(r"\]\(((?!https?:)[^)#]+)", skill):
        if not (out / link).is_file():
            errors.append(f"SKILL.md: link to missing file {link}")

    words = readme_words((out / "README.md").read_text(encoding="utf-8"))
    if words < README_MIN_WORDS:
        errors.append(f"README.md: {words} words outside code blocks (min {README_MIN_WORDS})")
    return errors


def differences(expected, actual):
    """Paths that differ between two folders, both ways."""
    found = []

    def walk(comparison, prefix=""):
        found.extend(prefix + name for name in comparison.left_only + comparison.right_only)
        _, mismatch, errors = filecmp.cmpfiles(
            comparison.left, comparison.right, comparison.common_files, shallow=False
        )
        found.extend(prefix + name for name in mismatch + errors)
        for name, sub in comparison.subdirs.items():
            walk(sub, f"{prefix}{name}/")

    walk(filecmp.dircmp(expected, actual, ignore=[]))
    return sorted(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="write nothing; fail when the committed edition is stale")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "infranodus"
            build(fresh)
            errors = check_policy(fresh)
            stale = differences(fresh, OUT) if OUT.is_dir() else ["(the folder is missing)"]
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        if stale:
            print("error: claude-directory/infranodus/ is stale: " + ", ".join(stale)
                  + "\n       run python3 scripts/build_claude_directory.py and commit the result",
                  file=sys.stderr)
        if errors or stale:
            sys.exit(1)
        print("claude-directory/infranodus/ is current and meets the checks")
        return

    build(OUT)
    errors = check_policy(OUT)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        sys.exit(1)
    version = json.loads((OUT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    count = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"Built claude-directory/infranodus/ (version {version}, {count} files)")


if __name__ == "__main__":
    main()
