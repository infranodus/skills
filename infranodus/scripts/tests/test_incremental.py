"""Incremental update flow, end to end, without a server.

Builds a throwaway git repo in a temp dir, runs repo2statements.py through
build / --detect / --update, then drives upload_scopes.py against a fake
MCP client that records every call_tool and answers with plausible
responses — asserting the delete_statements / create_knowledge_graph order
for a delta and for --force. Stdlib only:

    python3 -m unittest infranodus/scripts/tests/test_incremental.py
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True)


def make_repo(root: Path):
    (root / "docs").mkdir()
    (root / "src").mkdir()
    (root / "README.md").write_text(
        "# Tiny project\n\nThis project demonstrates the incremental "
        "update flow for the InfraNodus skill.\n\nIt has a docs folder, a "
        "source folder, and a short git history.\n")
    (root / "docs" / "api.md").write_text(
        "# API guide\n\nThe API exposes a single endpoint that returns the "
        "knowledge graph for a project.\n\nAuthentication uses a bearer "
        "token passed in the Authorization header of each request.\n")
    (root / "docs" / "setup.md").write_text(
        "# Setup\n\nInstall the dependencies with pip and run the server "
        "with the start command.\n\nThe server reads its configuration "
        "from environment variables only.\n")
    (root / "src" / "app.py").write_text(
        '"""Application entry point: wires the HTTP server to the graph '
        'builder and serves the API."""\n\n\ndef main():\n    # WHY: the '
        'server must start even when the graph is empty, so the health '
        'check works\n    pass\n')
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@t.t")
    git(root, "config", "user.name", "t")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "initial import", "-m",
        "Adds the docs folder, the app entry point, and a README "
        "explaining the purpose of the project.")
    with (root / "README.md").open("a") as f:
        f.write("extra line\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "expand readme", "-m",
        "The README now mentions the git history so the history scope "
        "has something to mine.")


def run_r2s(r2s, root, *flags):
    """Run repo2statements.main() in-process; returns (code, stdout)."""
    out, err = io.StringIO(), io.StringIO()
    argv = sys.argv
    sys.argv = ["repo2statements.py", str(root), "--no-gh", *flags]
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = r2s.main()
    finally:
        sys.argv = argv
    return code, out.getvalue(), err.getvalue()


def manifest(root):
    return json.loads((root / "infranodus" / "manifest.json").read_text())


class FakeSpec:
    transport = "http"

    def endpoint(self):
        return "https://fake.invalid/mcp"

    def describe(self):
        return "  server: fake"


class FakeClient:
    """Records every call_tool; answers like the server would."""

    def __init__(self):
        self.calls = []

    def connect(self):
        pass

    def close(self):
        pass

    def call_tool(self, name, arguments):
        self.calls.append((name, json.loads(json.dumps(arguments))))
        g = arguments.get("graphName", "")
        url = f"https://infranodus.com/acct/{g}"
        if name == "update_statements":
            return "ok", json.dumps({"updated": 3, "changes": [],
                                     "unchanged": 0, "unmatched": 0,
                                     "rejected": 0, "graphName": g,
                                     "graphUrl": url})
        if name == "delete_statements":
            if arguments.get("deleteAll"):
                return "ok", json.dumps({"deleted": 7, "removedIds": [],
                                         "remaining": 0, "graphName": g,
                                         "graphUrl": url})
            return "ok", json.dumps({"deleted": 4, "removedIds": [1, 2, 3, 4],
                                     "remaining": 2, "graphName": g,
                                     "graphUrl": url})
        if name == "create_knowledge_graph":
            return "ok", json.dumps({"graphUrl": url,
                                     "mainTopicalClusters": ["api", "docs"],
                                     "contentGaps": ["deployment"]})
        if name == "generate_contextual_hint":
            return "ok", json.dumps({"textOverview": "overview text"})
        if name == "optimize_text_structure":
            return "ok", json.dumps({"diversity_stats":
                                     {"diversity_score": "focused"},
                                     "suggestions": ["develop deployment"]})
        return "ok", "{}"


def run_uploader(up, root, *flags):
    client = FakeClient()
    up.connect_to_configured_server = lambda r: (client, FakeSpec())
    up.PACE_SECONDS = 0
    up.time.sleep = lambda s: None
    out, err = io.StringIO(), io.StringIO()
    argv = sys.argv
    sys.argv = ["upload_scopes.py", str(root), *flags]
    try:
        with redirect_stdout(out), redirect_stderr(err):
            up.main()
    finally:
        sys.argv = argv
    return client, out.getvalue() + err.getvalue()


class IncrementalFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "tinyrepo"
        self.root.mkdir()
        make_repo(self.root)
        self.r2s = load("repo2statements")
        self.up = load("upload_scopes")

    def tearDown(self):
        self.tmp.cleanup()

    def build_and_fake_upload(self):
        code, _, _ = run_r2s(self.r2s, self.root)
        self.assertEqual(code, 0)
        m = manifest(self.root)
        for k, v in m["scopes"].items():
            v["graphName"] = "repo-tinyrepo-" + self.r2s.scope_label(k)
            v["url"] = "https://infranodus.com/acct/" + v["graphName"]
        (self.root / "infranodus" / "manifest.json").write_text(
            json.dumps(m, indent=2))
        for p in (self.root / "infranodus").glob("*-ontology.md"):
            p.unlink()   # a real upload deletes the intermediates
        return m

    def mutate(self):
        with (self.root / "docs" / "api.md").open("a") as f:
            f.write("\nRate limits apply per account and are reported with "
                    "a 429 status code.\n")
        (self.root / "docs" / "new.md").write_text(
            "# Deployment notes\n\nDeploy with the container image; the "
            "graph builder runs as a sidecar next to the API server.\n")
        (self.root / "docs" / "setup.md").unlink()
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "docs: rate limits", "-m",
            "Documents the rate limit behaviour of the API and adds a "
            "deployment note about the sidecar layout.")

    def test_manifest_foundation_detect_update(self):
        code, _, _ = run_r2s(self.r2s, self.root)
        self.assertEqual(code, 0)
        m = manifest(self.root)
        docs = m["scopes"]["repo-docs-ontology.md"]
        self.assertEqual(set(docs["files"]),
                         {"README.md", "docs/api.md", "docs/setup.md"})
        self.assertEqual(docs["filters"], {"include": [], "terms": []})
        self.assertRegex(docs["builtAtCommit"], r"^[0-9a-f]{40}$")
        hist = m["scopes"]["repo-history-ontology.md"]
        self.assertEqual(hist["history"]["lastCommit"], docs["builtAtCommit"])
        self.assertNotIn("files", hist)

        code, out, err = run_r2s(self.r2s, self.root, "--detect")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertTrue(all(r["status"] == "clean" for r in report.values()))
        self.assertIn("docs: clean", err)

        self.build_and_fake_upload()
        self.mutate()
        code, out, err = run_r2s(self.r2s, self.root, "--detect")
        report = json.loads(out)
        self.assertEqual(report["repo-docs-ontology.md"],
                         {"status": "changed", "new": ["docs/new.md"],
                          "modified": ["docs/api.md"],
                          "deleted": ["docs/setup.md"], "renamed": []})
        self.assertEqual(report["repo-code-rationale-ontology.md"]["status"],
                         "clean")
        self.assertEqual(report["repo-history-ontology.md"]["newCommits"], 1)
        self.assertIn("docs: +1 new / 1 modified / 1 deleted / 0 renamed",
                      err)

        code, out, _ = run_r2s(self.r2s, self.root, "--update")
        self.assertEqual(code, 0)
        delta = self.root / "infranodus" / "repo-docs-delta-ontology.md"
        self.assertTrue(delta.exists())
        fm = self.up.parse_frontmatter(delta)
        self.assertIs(fm["delta"], True)
        self.assertEqual(fm["graphName"], "repo-tinyrepo-docs")
        self.assertEqual(fm["replaceCategories"],
                         ["docs/api.md", "docs/setup.md"])
        body = self.up.strip_frontmatter(delta)
        self.assertIn("## [[docs/api.md]]", body)
        self.assertIn("## [[docs/new.md]]", body)
        self.assertNotIn("README.md", body)
        m = manifest(self.root)
        docs = m["scopes"]["repo-docs-ontology.md"]
        self.assertEqual(set(docs["files"]),
                         {"README.md", "docs/api.md", "docs/new.md"})
        entry = m["scopes"]["repo-docs-delta-ontology.md"]
        self.assertEqual(entry["deltaOf"], "repo-docs-ontology.md")
        self.assertEqual(entry["policy"], "generated")
        self.assertTrue((self.root / "infranodus" /
                         "repo-history-delta-ontology.md").exists())

        # nothing left to update
        code, out, _ = run_r2s(self.r2s, self.root, "--update")
        self.assertIn("no changes", out)

    def test_delta_upload_deletes_categories_before_append(self):
        self.build_and_fake_upload()
        self.mutate()
        run_r2s(self.r2s, self.root, "--update")
        client, log = run_uploader(self.up, self.root)
        names = [n for n, _ in client.calls]
        self.assertIn("delete_statements", names)
        first_delete = names.index("delete_statements")
        first_create = names.index("create_knowledge_graph")
        self.assertLess(first_delete, first_create)
        deletes = [a for n, a in client.calls if n == "delete_statements"]
        self.assertEqual(len(deletes), 1)   # history delta has nothing to replace
        self.assertEqual(deletes[0], {"graphName": "repo-tinyrepo-docs",
                                      "categories": ["docs/api.md",
                                                     "docs/setup.md"],
                                      "confirm": True})
        creates = [a for n, a in client.calls if n == "create_knowledge_graph"]
        self.assertEqual({a["graphName"] for a in creates},
                         {"repo-tinyrepo-docs", "repo-tinyrepo-history"})
        self.assertFalse((self.root / "infranodus" /
                          "repo-docs-delta-ontology.md").exists())
        m = manifest(self.root)
        self.assertNotIn("repo-docs-delta-ontology.md", m["scopes"])
        docs = m["scopes"]["repo-docs-ontology.md"]
        self.assertEqual(docs["statements"], 6 - 4 + 4)
        self.assertEqual(docs["graphName"], "repo-tinyrepo-docs")
        self.assertIn("Delta build", (self.root / "infranodus" /
                                      "INFRANODUS_REPORT.md").read_text())
        self.assertIn("removed 4 statement(s)", log)

    def test_rename_is_relabelled_in_place(self):
        self.build_and_fake_upload()
        old_hash = manifest(self.root)["scopes"]["repo-docs-ontology.md"][
            "files"]["docs/setup.md"]
        git(self.root, "mv", "docs/setup.md", "docs/install.md")
        git(self.root, "commit", "-q", "-m", "docs: rename setup to install")

        code, out, err = run_r2s(self.r2s, self.root, "--detect")
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["repo-docs-ontology.md"],
                         {"status": "changed", "new": [], "modified": [],
                          "deleted": [],
                          "renamed": [{"from": "docs/setup.md",
                                       "to": "docs/install.md"}]})
        self.assertIn("docs: +0 new / 0 modified / 0 deleted / 1 renamed",
                      err)

        code, out, _ = run_r2s(self.r2s, self.root, "--update")
        self.assertEqual(code, 0)
        delta = self.root / "infranodus" / "repo-docs-delta-ontology.md"
        self.assertTrue(delta.exists())
        fm = self.up.parse_frontmatter(delta)
        self.assertEqual(fm["renameFrom"], ["docs/setup.md"])
        self.assertEqual(fm["renameTo"], ["docs/install.md"])
        self.assertEqual(fm["replaceCategories"], [])
        self.assertEqual(self.up.strip_frontmatter(delta).strip(), "")
        m = manifest(self.root)
        entry = m["scopes"]["repo-docs-delta-ontology.md"]
        self.assertEqual(entry["statements"], 0)
        self.assertEqual(entry["renameCategories"],
                         [{"from": "docs/setup.md", "to": "docs/install.md"}])
        docs = m["scopes"]["repo-docs-ontology.md"]
        self.assertEqual(docs["files"]["docs/install.md"], old_hash)
        self.assertNotIn("docs/setup.md", docs["files"])
        before = docs["statements"]

        client, log = run_uploader(self.up, self.root)
        docs_calls = [(n, a) for n, a in client.calls
                      if a.get("graphName") == "repo-tinyrepo-docs"]
        updates = [a for n, a in docs_calls if n == "update_statements"]
        self.assertEqual(updates, [{
            "graphName": "repo-tinyrepo-docs",
            "categories": ["docs/setup.md"],
            "set": {"removeCategories": ["docs/setup.md"],
                    "addCategories": ["docs/install.md"]},
            "confirm": True}])
        self.assertEqual([n for n, _ in client.calls
                          if n == "delete_statements"], [])
        self.assertNotIn("create_knowledge_graph",
                         [n for n, _ in docs_calls])
        self.assertIn("relabelled 3 statements docs/setup.md -> "
                      "docs/install.md", log)
        m = manifest(self.root)
        self.assertNotIn("repo-docs-delta-ontology.md", m["scopes"])
        docs = m["scopes"]["repo-docs-ontology.md"]
        self.assertEqual(docs["statements"], before)
        self.assertEqual(docs["files"]["docs/install.md"], old_hash)
        self.assertFalse(delta.exists())
        self.assertIn("renamed: docs/setup.md -> docs/install.md "
                      "(3 statements)",
                      (self.root / "infranodus" /
                       "INFRANODUS_REPORT.md").read_text())

    def test_moved_and_edited_file_is_delete_plus_add(self):
        self.build_and_fake_upload()
        git(self.root, "mv", "docs/setup.md", "docs/install.md")
        with (self.root / "docs" / "install.md").open("a") as f:
            f.write("\nThe install step also creates the local cache "
                    "directory next to the configuration.\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "docs: move and edit setup")
        _, out, err = run_r2s(self.r2s, self.root, "--detect")
        report = json.loads(out)
        self.assertEqual(report["repo-docs-ontology.md"],
                         {"status": "changed", "new": ["docs/install.md"],
                          "modified": [], "deleted": ["docs/setup.md"],
                          "renamed": []})
        self.assertIn("docs: +1 new / 0 modified / 1 deleted / 0 renamed",
                      err)
        run_r2s(self.r2s, self.root, "--update")
        delta = self.root / "infranodus" / "repo-docs-delta-ontology.md"
        fm = self.up.parse_frontmatter(delta)
        self.assertNotIn("renameFrom", fm)
        self.assertEqual(fm["replaceCategories"], ["docs/setup.md"])
        self.assertIn("## [[docs/install.md]]",
                      self.up.strip_frontmatter(delta))
        client, _ = run_uploader(self.up, self.root)
        names = [n for n, _ in client.calls]
        self.assertNotIn("update_statements", names)
        self.assertIn("delete_statements", names)

    def test_force_clears_graph_first(self):
        code, _, _ = run_r2s(self.r2s, self.root)
        m = manifest(self.root)
        slug = self.root.name
        for k, v in m["scopes"].items():
            v["graphName"] = f"repo-{slug}-" + self.r2s.scope_label(k)
        (self.root / "infranodus" / "manifest.json").write_text(
            json.dumps(m, indent=2))
        client, log = run_uploader(self.up, self.root, "--force")
        names = [n for n, _ in client.calls]
        self.assertEqual(names[0], "delete_statements")
        self.assertEqual(client.calls[0][1],
                         {"graphName": f"repo-{slug}-docs", "deleteAll": True,
                          "confirm": True})
        self.assertEqual(names[1], "create_knowledge_graph")
        self.assertEqual(client.calls[1][1]["graphName"], f"repo-{slug}-docs")
        # every uploaded scope was cleared exactly once, before its upload
        for g in (f"repo-{slug}-docs", f"repo-{slug}-code-rationale",
                  f"repo-{slug}-history"):
            idx = [i for i, (n, a) in enumerate(client.calls)
                   if n == "delete_statements" and a["graphName"] == g]
            self.assertEqual(len(idx), 1)
            first_up = next(i for i, (n, a) in enumerate(client.calls)
                            if n == "create_knowledge_graph"
                            and a["graphName"] == g)
            self.assertLess(idx[0], first_up)
        self.assertNotIn("delete the graph", log)

    def test_no_force_skips_uploaded_scopes_without_deleting(self):
        self.build_and_fake_upload()
        run_r2s(self.r2s, self.root)   # regenerate scope files
        client, log = run_uploader(self.up, self.root)
        self.assertEqual(client.calls, [])
        self.assertIn("already uploaded", log)


if __name__ == "__main__":
    unittest.main()
