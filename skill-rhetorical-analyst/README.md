# `rhetorical-analyst` has moved to InfraNodus Lab

This skill now lives in the InfraNodus Lab repository:
**https://github.com/infranodus/infranodus-lab** (placeholder name, TBD), folder `skill-rhetorical-analyst/`.

This folder intentionally holds no `SKILL.md` or plugin manifest, so no
installer picks it up from here.

Install it:

- Claude Code, same id as before (fetched from the Lab repo):
  `/plugin install rhetorical-analyst@infranodus-skills`
- `npx skills add infranodus/infranodus-lab --skill rhetorical-analyst -g`
- Claude web/desktop: download `rhetorical-analyst.zip` from the Lab repo's Releases page and upload it under Settings → Capabilities → Skills.

The skill's history up to the move (v1.7.3) stays in this repository's git log.
