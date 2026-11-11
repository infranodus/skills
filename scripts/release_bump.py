#!/usr/bin/env python3
"""Decide the next release and bump the plugins that changed since the last one.

Run from the repo root (the release workflow does, on every push to master):

    python3 scripts/release_bump.py [--level patch|minor|major] [--since <ref>] [--dry-run]

Rules:
- The last release is the newest `v*` tag. Nothing changed under a plugin
  folder since then means no release.
- The new version is the last release (or the highest plugin version, if one
  is ahead of it) bumped by --level.
- Every plugin with changed files gets the new version; so does the
  `infranodus-all` bundle when a skill it lists changed. A plugin's version is
  therefore the release it last changed in. Claude Code fetches an update
  only when this number goes up.
- A change in openai/infranodus/ counts as a change to `infranodus`: the
  ChatGPT / Codex package takes its version from that plugin.

Prints a summary, and writes `release`, `version`, `changed` and
`openai_upload` to $GITHUB_OUTPUT when it is set.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
OPENAI_PLUGIN = "infranodus"
OPENAI_LISTING = "openai/infranodus/"
VERSION_LINE = re.compile(r'^(\s*"version"\s*:\s*")(\d+\.\d+\.\d+)(")', re.M)


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def parse(version):
    return tuple(int(part) for part in version.split("."))


def bump(version, level):
    major, minor, patch = parse(version)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def read_version(manifest):
    return json.loads(manifest.read_text())["version"]


def write_version(manifest, version):
    # Edit the one line, so the file keeps its tabs and key order.
    text, count = VERSION_LINE.subn(rf"\g<1>{version}\g<3>", manifest.read_text(), count=1)
    if count != 1:
        sys.exit(f"error: no version line in {manifest}")
    manifest.write_text(text)


def last_release_tag():
    tags = git("tag", "--list", "v*", "--sort=-v:refname").splitlines()
    return tags[0] if tags else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", choices=["patch", "minor", "major"], default="patch")
    parser.add_argument("--since", help="compare against this ref instead of the newest v* tag")
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = parser.parse_args()

    tag = last_release_tag()
    since = args.since or tag
    if not since:
        sys.exit("error: no v* tag to compare against; pass --since")

    bundle = json.loads(BUNDLE_MANIFEST.read_text())
    bundled = {Path(entry).name for entry in bundle["skills"]}
    plugins = {
        manifest.parent.parent.name: manifest
        for manifest in sorted(ROOT.glob("*/.claude-plugin/plugin.json"))
    }

    changed_files = git("diff", "--name-only", f"{since}..HEAD").splitlines()
    changed = {
        folder
        for folder in plugins
        if any(path.startswith(folder + "/") for path in changed_files)
    }
    listing_changed = any(path.startswith(OPENAI_LISTING) for path in changed_files)
    if listing_changed:
        changed.add(OPENAI_PLUGIN)

    outputs = {"release": "false", "version": "", "changed": "", "openai_upload": "false"}
    if not changed:
        print(f"No plugin changed since {since}: no release.")
    else:
        versions = [read_version(manifest) for manifest in plugins.values()]
        versions.append(bundle["version"])
        if tag:
            versions.append(tag.lstrip("v"))
        new_version = bump(max(versions, key=parse), args.level)
        bump_bundle = bool(changed & bundled)

        print(f"Release v{new_version} ({args.level}; changes since {since})")
        for folder in sorted(changed):
            print(f"  {folder}: {read_version(plugins[folder])} -> {new_version}")
            if not args.dry_run:
                write_version(plugins[folder], new_version)
        if bump_bundle:
            print(f"  infranodus-all: {bundle['version']} -> {new_version}")
            if not args.dry_run:
                write_version(BUNDLE_MANIFEST, new_version)

        outputs = {
            "release": "true",
            "version": new_version,
            "changed": " ".join(sorted(changed)),
            "openai_upload": "true" if OPENAI_PLUGIN in changed else "false",
        }

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as handle:
            for key, value in outputs.items():
                handle.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
