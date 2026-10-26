# `actionize` has moved to InfraNodus Lab

This skill now lives in the InfraNodus Lab repository:
**https://github.com/infranodus/infranodus-lab** (placeholder name, TBD), folder `skill-actionize/`.

This folder intentionally holds no `SKILL.md` or plugin manifest, so no
installer picks it up from here.

Install it:

- Claude Code, same id as before (fetched from the Lab repo):
  `/plugin install actionize@infranodus-skills`
- `npx skills add infranodus/infranodus-lab --skill actionize -g`
- Claude web/desktop: download `actionize.zip` from the Lab repo's Releases page and upload it under Settings → Capabilities → Skills.

The skill's history up to the move (v1.7.3) stays in this repository's git log.
