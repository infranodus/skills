# Releasing

How a change in this repo reaches users: the Claude Code marketplace,
`npx skills`, release zips, and the ChatGPT / Codex plugin directory.

## Versions

Claude Code fetches a plugin update only when its `version` goes up.

- Bump the plugin whose files changed: `<skill-dir>/.claude-plugin/plugin.json`.
- **If you change `infranodus/`, also bump `infranodus-all`** (root
  `.claude-plugin/plugin.json`). The bundle ships the same skill folders, so
  without a bump its users keep the old copy. The same applies to any other
  skill the bundle lists.
- The ChatGPT package takes its version from
  `infranodus/.claude-plugin/plugin.json` (see `tests/build-openai.sh`).

## Release (Claude marketplace, npx skills, zips)

1. Merge the feature branches into `master` through PRs.
2. Bump versions as above.
3. Run the install and upgrade test against `master`:
   `tests/split-test.sh . master v1.7.3`
   (needs network; runs every `claude` call under a throwaway config).
4. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.
   `.github/workflows/release.yml` builds the Claude skill zips and attaches
   `infranodus-openai.zip` to the GitHub release.
5. Users update with `/plugin marketplace update infranodus-skills` and then
   the plugin update in Claude Code; `npx skills` users re-run their `add`.
   Nothing else is deployed: the marketplace reads this repo.

## ChatGPT / Codex plugin directory (`infranodus` only)

Manual: the directory does not read this repo.

- **Skill or listing change** (anything in `infranodus/` or
  `openai/infranodus/`): bump the `infranodus` version, run
  `tests/build-openai.sh --strict`, and upload `dist/infranodus-openai.zip`
  in the OpenAI dashboard. A re-upload with an unchanged version is rejected,
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
