# Releasing

How a change in this repo reaches users: the Claude Code marketplace,
`npx skills`, release zips, the Claude directory, and the ChatGPT / Codex
plugin directory.

## Versions

Claude Code fetches a plugin update only when its `version` goes up. The
release workflow sets the versions, so a pull request does not bump them:

- Each plugin that changed since the last release gets the new release
  version (`<skill-dir>/.claude-plugin/plugin.json`). A plugin's version is
  the release it last changed in.
- `infranodus-all` (root `.claude-plugin/plugin.json`) gets it too when any
  skill it lists changed. The bundle ships the same skill folders, so without
  a bump its users would keep the old copy.
- A change in `openai/infranodus/` counts as a change to `infranodus`: the
  ChatGPT package takes its version from
  `infranodus/.claude-plugin/plugin.json` (see `tests/build-openai.sh`).

The rules live in `scripts/release_bump.py`. To see what the next merge would
release: `python3 scripts/release_bump.py --dry-run`.

## Release (Claude marketplace, npx skills, zips)

Merging a pull request into `master` releases it.
`.github/workflows/auto-release.yml` runs on every push to `master`:

1. Finds the plugins that changed since the newest `v*` tag. None changed
   (docs, tests, workflows only): no release.
2. Bumps them and, when needed, the bundle; checks the ChatGPT package with
   `tests/build-openai.sh --strict`.
3. Commits `Release vX.Y.Z` to `master`, tags it and pushes.
4. Calls `.github/workflows/release.yml`, which builds the Claude skill zips
   and attaches `infranodus-openai.zip` to the GitHub release.

Labels on the pull request change this:

| Label | Effect |
|---|---|
| `release:skip` | No release for this merge. Its changes go out with the next one |
| `release:minor` | Bump the minor version instead of the patch |
| `release:major` | Bump the major version |

Users update with `/plugin marketplace update infranodus-skills` and then
the plugin update in Claude Code; `npx skills` users re-run their `add`.
Nothing else is deployed: the marketplace reads this repo.

Not run by the workflow: the install and upgrade test,
`tests/split-test.sh . master v1.7.3`. It drives the `claude` CLI under a
throwaway config and needs network. Run it by hand before merging a change
to the manifests, the marketplace file or the install script.

A release by hand still works: bump, `git tag vX.Y.Z && git push origin
vX.Y.Z`, and `release.yml` runs on the tag.

## Claude directory (`infranodus` only)

Anthropic's directory (claude.ai/directory) reads this repo, at the plugin
path `claude-directory/infranodus`. It accepts programs and scripts only
from Verified organizations, so it does not get `infranodus/` (which ships
the Python extraction programs) but a script-free edition of the same skill:
Markdown, JSON and the icon only.

- `claude-directory/infranodus/` is build output and is committed. Never
  edit it: run `python3 scripts/build_claude_directory.py`.
- The build takes the shared sections of `infranodus/SKILL.md` as they are
  and the parts that differ (how the skill connects, the repo / vault
  workflow, the runbook, the README shown as the listing, the skill
  description) from `claude-directory/src/infranodus/`. The manifest and the
  icon are copied from `infranodus/.claude-plugin/`, so there is one version.
- A new `## ` section in `infranodus/SKILL.md` stops the build until
  `SECTIONS` in the script says whether to keep or replace it.
- The build fails on what the directory refuses or holds: a file that is not
  Markdown, text, JSON, YAML or an image, a `#!` first line, a reference to
  a bundled program, a credential read from the environment, frontmatter
  keys other than `name` and `description`.
- In a pull request that changes `infranodus/SKILL.md` or the sources, run
  the build and commit the result; `--check` fails when it is stale. The
  release workflow rebuilds it after the version bump and commits it with
  the release. Whether the directory then takes the new commit by itself
  is not confirmed: check the listing's version after a release and
  resubmit in the portal when it has not moved.
- Before a submission: `claude plugin validate claude-directory/infranodus
  --profile directory --strict`.

## ChatGPT / Codex plugin directory (`infranodus` only)

Manual: the directory does not read this repo.

- **Skill or listing change** (anything in `infranodus/` or
  `openai/infranodus/`): the release notes of the GitHub release say when
  this applies. Download `infranodus-openai.zip` from that release and
  upload it in the OpenAI dashboard. A re-upload with an unchanged version is rejected,
  and every upload is reviewed again.
- **MCP server change** (`mcp-server-infranodus`): no upload. After
  publication the directory rescans the live server; new tools come up for
  review.
- The plugin's MCP URL is fixed at `https://mcp.infranodus.com/openai`. Never
  deploy the MCP server from a branch without that endpoint.
- The listing and the skill description must not name other AI assistants,
  models or platforms; the build fails if they do. See `openai/README.md`.

Other skills are not set up for the directory. Each would need its own
`openai/<skill>/` folder, listing and review, and those that call InfraNodus
tools would bundle the MCP server.
