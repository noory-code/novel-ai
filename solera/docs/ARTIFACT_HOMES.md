# Artifact homes

Every output Solera's work produces has exactly **one** home (SSOT). Pick the
home by the *nature* of the output, not by which step created it. Solera itself
stores neither code nor design nor decisions — it stages process output and
points at the rest by id.

## The homes

| Output (nature) | Home | Notes |
|---|---|---|
| **Code** (source the agent writes) | the **repository** | Never staged in `.noory/solera/`. The misplacement guard warns if code lands in artifacts. |
| **Code-derived** (generated ERD, API docs — produced *from* code) | the repo's `docs/generated/` | Regenerable from source; lives next to the code it derives from. |
| **Conceptual design** (*what* to build and *why*) | **Novel** | Folded back via a retrospective or feedback note. When Novel is absent the note still records the intent for a human to place later. |
| **Technical design** (*how* it is built — architecture, schema, wiring) | the **repository** (code-near) | Lives next to the code it governs (e.g. `docs/`). Novel does not define the stack; this is not Novel's. |
| **Decisions** (the *choices* that govern the work — stack, architecture, conventions) | **proof** | An append-only decision log. Solera/mashbill point at decision ids by value; a decision-type leaf records here on acceptance. |
| **Process artifacts** (scratch output on the way: a draft, a screenshot, a dump) | `artifacts/{id}/` | Staging only. Tagged, not versioned (below). |

## Staging convention (`artifacts/{id}/`)

Process artifacts stage under the WorkItem that produced them and carry **tags**,
never version numbers (versioning is Novel's job, not the staging area's):

- `about` — the id(s) the artifact relates to (e.g. `feature/login`). Empty in
  standalone Solera, which has no published spec to point at.
- `from` — where the artifact came from (a tool name, a step). Optional.

Tags live in an optional manifest, `artifacts/{id}/MANIFEST.md`:

```yaml
---
artifacts:
  - file: erd.png
    about: [feature/login]
    from: dbml-export
  - file: draft-notes.md
    about: []
---
```

A `version:` field is rejected — staged artifacts are tagged, not versioned.

## The guard

`solera.artifacts.find_misplaced_artifacts(ws)` scans every WorkItem's
`artifacts/` and returns warnings (not errors) for output in the wrong home —
currently source code, which belongs in the repository. It advises; it does not
block.

## Large files

A large artifact is referenced by a link, not copied into staging. (The link
form is left open until a concrete need appears — see the redesign backlog.)
