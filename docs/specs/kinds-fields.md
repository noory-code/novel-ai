# Per-kind wire fields (schema design contract)

> **Canon (shared schema design contract, `D-2026-06-28-B`).** The *code* SSOT = `viewer/src/domain/{Kind}.ts`
> + `test_schema_parity.py` (on drift the code guard wins). kind *meaning* = [`../concepts/kinds.md`](../concepts/kinds.md),
> detailed behaviour/field usage = engine [`SPEC.md`](../../plugins/mashbill/docs/SPEC.md).
> (Retired kinds excluded, the actor_ref reform reflected.)

## BaseFields (common to all kinds, not repeated)
`id` · `label` · `x` · `y` · `width` · `height` · `color` · `shape` · `icon` ·
`collapsed` · `is_root` · `details_path` · `owner` · `version` · `publish_baseline`.
> Hierarchy is expressed not by a node `parent_id` but by the **directional edge's `relation`** (legacy `parent_id`
> removed, [`edges.md`](./edges.md)).

## Current palette (14 kinds)

### Foundation
| kind | typed fields | notes |
|---|---|---|
| `project` | (no content of its own) | anchor. label=`ProjectDoc.name` mirror, position=`ProjectDoc.anchors[canvas]` |
| `mission` | `body` | label = the one-sentence declaration. (old what_we_do/why/direction retired) |
| `core_value` | `body` | label = value name. body = meaning + tradeoff. (old definition·do/dont retired) |
| `identity` | `summary` + `description` | label = short directive. summary = one-line meaning. description = concrete behavior. Legacy `body` folds into `description`; `status`/`provenance` stay structural. |

### Actors
| kind | typed fields | notes |
|---|---|---|
| `actor` | `body` | **identity-only** (US-303: side field/editing/schema removal complete). inheritance fields=[body]. (old motivation/pain retired) |

### Services overview
| kind | typed fields | notes |
|---|---|---|
| `category` | `theme` (one line) | visual grouping (low-friction/dumb). minimal inspector. |
| `service` | **5 fields**: why is it needed (typed) · what improves (typed) + **3 reference kinds** who participates (actor) · what can't be conceded (core_value) · in what manner (identity) | old 9 fields (what/scope/trigger/how/outcome/do/dont/target_side/body) deleted. reference model (node vs array)=implementation choice (plans). |
| `feature` | `proposed` (one line "what can be done") | lean inspector (name + action summary). drill target. |

### Entities
| kind | typed fields | notes |
|---|---|---|
| `entity` | `label` (name) · one-line `"무엇을 담나"` (what does it hold) | rough relationship=edge, back-reference=derived (read-only). no type/FK. |

### Feature canvas
| kind | typed fields | notes |
|---|---|---|
| `step` | `order` · `outcome` · `polarity` (positive/negative/neutral) · `body` | label = user action. branch badge=outgoing edges ≥2 (derived). |
| `decision` | `body` | label = question. branch outcomes = outgoing edge labels (not a stored field). shape=◇ forced. |
| `rule` | `policy` · `enforcement` · `actor_permissions` (optional) · `body` | label = rule name. per-feature operating constraint (incl. permissions). |
| `note` | `body` | label + ambient memo. **edge-invariant (never any edge).** no reference·target. |
| `actor_ref` | `ref_actor_id` | **reform this session: read-only anchor.** US-303 also removed `side`. old `gives`/`receives`/`motivation`/`pain` **retired.** not publishable. |

> **actor_ref reform (this session):** on the Feature canvas, actor_ref = a read-only reference pointing at the
> `actor` master ("who starts/who can"). It no longer holds value-exchange data — role-level
> value is the Actors relationship edge, aggregate value is the service "what improves". The only
> standalone reference node to survive the marathon.

> **service reference modeling (undecided, implementation choice):** whether the 3 reference fields (actor/core_value/identity) sit as (A) separate
> `*_ref` nodes + edges, or (B) id arrays on the service, is a domain decision — pinned in `plans/`.
> Either way the user sees chips, not free typing.

## Retired kinds (history — code reconciliation in plans/)

| kind | old fields | reason retired |
|---|---|---|
| `mission_ref`·`value_ref`·`identity_ref` | `ref_*_id` · `notes_in_context` | moved to service inspector chips |
| `metric` | `target` · `measurement` · `body` | below action altitude/unneeded |
| `content` | `format` · `producer_actor_id` · `consumer_actor_id` · `body` | implementation deliverable (below altitude); project roles go to Entities |
| `group` | `member_ids` · `body` | the feature level replaces grouping; collapse=view |

> The code's 15/17 kind-count drift (`schema_export._ALL_KIND_CLASSES` 15 vs viewer 17) is
> reconciled in one pass at the implementation stage (add feature/note/entity, retire 6). `plans/`.
