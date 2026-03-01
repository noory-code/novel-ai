# Changelog

## [1.3.0] - 2026-03-02

### Added
- `meta-skill` skill: create, review, or improve skill files in `.claude/skills/`; includes 4 type templates (unit-guide, unit-procedural, composite-guide, composite-procedural)
- `meta-rule` skill: create, review, or improve rule files in `.claude/rules/`
- `meta-command` skill: create, review, or improve slash command files in `.claude/commands/`
- `meta-subagent` skill: create, review, or improve agent definition files in `.claude/agents/`
- `docs/work-item-structure.md`: full hierarchy diagram (Identity → Action Item), folder layout, branch mapping, Human vs AI responsibility split

## [1.2.0] - 2026-03-02

### Added
- `writing-identity` skill: define service identity (Mission, Core Values, Vision, Goals rough list)

## [1.1.0] - 2026-03-02

### Added
- `docs/` folder with quick-start, architecture, and team-workflow guides
- README rewritten with Why Solera, Quick Start, comparison table, and team workflow section

### Changed
- plugin.json: version 1.1.0, expanded keywords

## [1.0.0] - 2026-03-01

### Added
- Initial release with 9 workflow skills
- Writing hierarchy: writing-phase, writing-goal, writing-epic, writing-story, writing-action-item
- Workflow management: workflow-manage, workflow-pr
- Context management: catalog-transition, handoff
- Stop hook: auto-runs handoff skill on session end
