# `vipassana-llm` has moved to InfraNodus Skills Lab

This skill now lives in the InfraNodus Skills Lab repository:
**https://github.com/infranodus/skills-lab**, folder `skill-vipassana-meditation/`.

This folder intentionally holds no `SKILL.md` or plugin manifest, so no
installer picks it up from here.

Install it:

- Claude Code, same id as before (fetched from the Lab repo):
  `/plugin install vipassana-llm@infranodus-skills`
- `npx skills add infranodus/skills-lab --skill vipassana-llm -g`
- Claude web/desktop: download `vipassana-llm.zip` from the Lab repo's Releases page and upload it under Settings → Capabilities → Skills.
- Or add the Lab marketplace directly: `/plugin marketplace add infranodus/skills-lab`, then `/plugin install vipassana-llm@infranodus-skills-lab`.

The skill's history up to the move (v1.7.3) stays in this repository's git log.

