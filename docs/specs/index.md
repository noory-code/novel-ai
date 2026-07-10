# specs/ — canvas behavior + node schema + edges + storage + domain

> Canonical (SSOT). Parent = [`../VISION.md`](../VISION.md), concepts = [`../concepts/`](../concepts/).
> (The former Mashbill `SPEC.md` 1815 lines + `DOMAIN.md` + `node-format/` were consolidated,
> reconciled with the new concepts [marathon + this session]. Retired/superseded body text removed.)

This directory is the canonical source of *behavior* — what each canvas does, what fields a node
holds, how edges are governed, and how things are stored/published. *Meaning* lives in `concepts/`.

| File | What |
|---|---|
| [`canvas-behavior.md`](./canvas-behavior.md) | Per-canvas: anchor·render·drill·edge-permission·inspector·layout |
| [`kinds-fields.md`](./kinds-fields.md) | Per-kind wire fields (schema) — current palette |
| [`edges.md`](./edges.md) | Edge model: relation classification + payload + render |
| [`storage-publish.md`](./storage-publish.md) | `.noory/` layout · JSON-SSOT · versioning · publish |
| [`domain.md`](./domain.md) | 5 bounded contexts + dependency direction + Entity/VO |

## Pinned vs later expansion (honestly)

The *model* of the new concepts is pinned, but the *full behavior spec* of some canvases is not yet
written (the old SPEC also stated "Foundation/Actors only full-spec, the rest later expansion"):

- ✅ **Pinned:** Foundation·Actors behavior, 5-canvas model, kind palette, edge model, storage/publish, domain.
- 🚧 **Later expansion (model pinned only, full behavior spec unwritten):** Services overview full
  behavior, Feature canvas body (drill·layout re-description), Entities on-canvas interaction, anchor click→inspector (TBD).
- These 🚧 get finalized via TDD at the implementation stage (plans/). Here we mark the *model* and the *known unknowns*.

## Code-near goes in noory-ai (not duplicated here)

Pure code mechanisms are canonical in [`mashbill/docs/`](../../mashbill/docs/) — referenced only here:
- Auto-layout algorithm details (`AUTO_LAYOUT.md`), cursor SSOT (`CURSOR.md`), publish MD format
  (`PUBLISH.md`), code structure (`ARCHITECTURE.md`), i18n terms (`I18N_KO_GLOSSARY.md`).
- The *code* SSOT for the wire schema = `viewer/src/domain/{Kind}.ts` + `test_schema_parity.py`.
  This `kinds-fields.md` is its *design contract* (what field, and why) — on drift the code guard wins.
