---
name: solera-import
user-invocable: true
description: Import a published mashbill service release (format F) into Solera and plan work items that realize its features.
metadata:
  version: "7.7.0"
  category: planning
  type: unit
  style: procedure
  triggers: [solera import, import a plot release, start from a published release, import vS]
  uses: [solera-plan, solera-run, solera-decide]
---

# solera-import

Start a Solera engagement from a published mashbill service release. mashbill freezes
a service (its 5-column definition + every feature's UX flow) into a
**format F** bundle on disk. Solera imports that bundle and you plan work items
that *realize* each feature — tying implementation directly to the design.

## When to use

After Novel has published a service release (`vS`) and you want to plan the
implementation work in Solera with explicit links back to the design.

## Procedure

### 1. Find the published release path

After Novel publishes, the release lands at:

```
<project-root>/.noory/plot/published/<service-slug>/vS<N>/
```

For example: `.noory/plot/published/auth/vS1/`.

### 2. Import the release

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  import .noory/plot/published/<service-slug>/vS<N>/ --label <label>
```

`--label` is a short local name for this import (e.g. `auth-v1`). It controls
where Solera writes the spec copy (`specs/<label>/`). Pick a name that makes the
version traceable.

### 3. Read what was imported

The imported release lands at `specs/<label>/`. Open
`specs/<label>/design/features/` to see which features it defines. Each
`features/<slug>.md` describes one feature's UX flow — the behaviour an
implementation must realise.

### 4. Plan with realizes links

Create a planning root for this engagement, then add leaves that realize format
F elements:

```bash
# root container for this release
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  plan "Implement <service> (<label>)" --level initiative

# one leaf per feature (or group of features in an epic)
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  add INIT-001 "Implement <feature>" --level action \
  --gate "pytest tests/test_<feature>.py" \
  --realizes feature/<slug>

# a leaf that realizes multiple elements
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  add INIT-001 "Wire <entity> model" --level action \
  --gate "pytest tests/test_<entity>.py" \
  --realizes entity/<slug>
```

`--realizes` is repeatable — use it multiple times on one item when the leaf
spans more than one format F element.

### 5. Execute

Hand off to **solera-run**. The `next` command prints each leaf's goal and gate.
The leaf's `realizes` links trace back to the design in `specs/<label>/`.

## Rules

- Import before planning. The import step validates the bundle; a broken bundle
  is caught here, not mid-execution.
- Use the feature slug from `specs/<label>/design/features/<slug>.md` as the
  `feature/<slug>` value in `--realizes`. Don't invent slugs — they must match
  the published spec.
- One label per release. If you import the same service twice (e.g. a patch),
  use a new label so both versions stay in `specs/`.
- When Novel publishes an updated vS, use **solera-repin** to surface which items
  have gone stale.
