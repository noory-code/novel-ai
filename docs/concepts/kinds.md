# kind — the *meaning* of each node kind

> **Canon (shared concept, `D-2026-06-28-B`).** The single source of the kind meaning both products (open
> engine·commercial app) use. Parent = [`../VISION.md`](../VISION.md), canvases = [`canvases.md`](./canvases.md).
> This is what each kind *means*; the **full typed fields·schema** (JSON contract) are the SSOT in
> [`../specs/`](../specs/), the *behaviour* spec is the engine `SPEC.md` — not duplicated here.
> (The engine [`mashbill/docs/CONCEPTS.md`](../../plugins/mashbill/docs/CONCEPTS.md) points to this file.)

## Palette (current)

`project` · `mission` · `core_value` · `identity` · `actor` · `category` ·
`service` · `feature` · `entity` · `step` · `decision` · `rule` · `note` ·
`actor_ref`.

> **Retired** (marathon + this session): `mission_ref` · `value_ref` · `identity_ref`
> (→ service inspector chips) · `metric` · `content` · `group`. History = §retired kinds.
> The 15/17 count drift in the code will be reconciled in one pass at the implementation stage (plans/).

---

## Foundation kinds — identity, time-independent

> **The essence has no node.** Essence = the emergent whole of 3 kinds, the core is the mission. The anchor is name only.

### `project` — project anchor
- **Asks:** which project is this?
- Auto-seeded, exactly 1 per project, cannot be deleted. A circle at the center of every primary canvas.
- Label = mirror of `ProjectDoc.name` (edit in one place → propagates everywhere). Holds **name only** (not a content container).

### `mission` — the root of existence (input)
- **Asks:** what fundamental change does it bring to the world?
- Definition = the fundamental change it will bring to the world (MTP). Test = is it sustainable (a problem that keeps recurring + value that didn't exist before).
- Form = **one declaration sentence + body** (merges old label/statement·what_we_do/why/direction).
- Count 0..N.

### `core_value` — decision criterion (input)
- **Asks:** what do you protect when there's a conflict?
- Definition = the value that *wins* when decisions diverge (how you decide right now). Not future-oriented (that's identity).
- Form = **name (label) + body** (meaning + tradeoff). Old `definition`·do/dont retired.
- The name is load-bearing (referenced in decisions as "with 'tolerance and support'…"). Count 0..N (usually 3–7).

### `identity` — consistent execution·expression rule (output)
- **Asks:** how do we consistently execute·express?
- Definition = the accumulation of always-applied action rules ("this is how we do it"). *Not value-conflict judgment*
  (that's core_value). When they clash, core_value is higher.
- **Output kind** — AI derives a draft from mission + core value → refined·confirmed with the human (no silent auto-generation ❌).
- Form = **name + action rule list**. Old `description` retired. `status`/`provenance` are
  dropped because they're inert until the AI-derivation flow (plans).

---

## Actor kind

### `actor` — relational role of the value economy
- **Asks:** who participates?
- Definition = a *role/participant class* (not a person·persona). Defined by position·resources, no demographics.
  One person can hold·switch between multiple roles. Every actor both gives **and receives**.
- **People only.** External APIs·systems·bots·infrastructure are not actors (an infra layer, out of scope until mode 2).
- **Hierarchy (`parent_id` tree, is-a refinement):** user → hero/fan, operator → manager etc. Core.
- Form = **identity-only** (body). (US-303: `side` field removed from actor — editing and schema. Asymmetry expressed via actor_ref/edges)
- Count = one or more human roles. A single person can be the only actor; there
  is no operator/user pair minimum.
- **2 kinds of edges** (hierarchy / relationship value arrow) = [`canvases.md`](./canvases.md) Actors.

> **Changed this session:** per-service exchanges (gives/receives/motivation/pain) are no longer
> stored granularly. Role-level value = Actors relationship edge, aggregate value = the service's
> "what gets better". (Old CONCEPTS' actor_ref gives/receives retired — see `actor_ref` below.)

---

## Service kinds

### `category` — thematic grouping of services
- **Asks:** what kind of services does it group?
- An optional pure container (creates no value, mindless). Use it only when two
  or more services share a useful theme or surface. Only on the Services canvas.
- Field: `theme` (one-line common subject).

### `service` — one outcome and the capabilities that reach it
- **Asks:** what coherent outcome does this service help people reach, and who participates?
- Definition = one coherent outcome that one or more human actors seek, together
  with the capabilities that help them reach it. A multi-actor value exchange
  can happen inside a service, but is not required. A screen, channel, internal
  process, or revenue line is not a service by itself.
- **Selection = a 5-field inspector, no drill.** Behaviour is one layer down (each `feature` drills into the Feature canvas).
- **5-field question form** (each title is itself an interview question): ① who participates? (actor reference, plural) ② why is it
  needed? (typing) ③ what gets better? (typing) ④ what can't be given up? (core_value reference, plural)
  ⑤ with what grain do we approach? (identity reference, plural). The 3 reference fields = pick from Foundation/Actors
  (no free typing ❌). Old 9 fields (what/scope/trigger/how/outcome/do/dont/target_side/body) **deleted**.
- Minimum participants = **≥1 human actor reference**. Do not create an actor for AI, software, or infrastructure merely to fill this field.

### `feature` — the capability a service provides
- **Asks:** what can a person do to reach this service's outcome?
- Definition = a *capability* under the service (writing/editing/emoji reactions) = **a behaviour grouping under the service**.
  Writing/editing/deleting are not services but capabilities the service provides.
- **Does not own a separate outcome. Promotion rule:** when a proposed feature
  starts to own a distinct outcome → **promoted to a service** (the outcome test).
- **The only drill target** — click = the Feature canvas (UX flowchart) opens.
- Inspector = lean (name + behaviour summary; details settled at the implementation stage).
- Hierarchy: **service → feature**, optionally **category → service → feature**
  (overview) → behaviour/rule (Feature canvas).

---

## Feature-canvas kinds (inside the UX flowchart)

> Feature canvas = the **UX flowchart** you open by clicking a feature (action → branch → result), **action
> altitude only**. The implementation below that is the external agent's job. Actor-anchored·value-oriented. Allowed =
> `step`·`decision`·flow edge·`note`·`rule`·`actor_ref` only.

### `step` — action (order)
- **Asks:** in what order does it happen?
- An ordered sub-action that makes up the feature (a user action). Fields (meaning): order, acting actor (actor_ref),
  outcome, `polarity` (positive/negative/neutral — marks failure cases in red,
  modeling negatives beyond the happy path too).

### `decision` — branch point (◇)
- **Asks:** where does the flow branch?
- A branch between action `step`s (a diamond). A user choice (selecting a method) or a system judgment (validation
  success/failure). **A system judgment is a `decision`, not a `step`** (step = a user action, kept so).
- A branch = a **labeled flow edge** (success/failure), not a stored field — governed by edge definition.
- Form = question label + choice body. Shape = always a diamond (the shape is the meaning).

### `rule` — operating constraint (per-feature)
- **Asks:** what is enforced here? Who can do what?
- Definition = a concrete operating/feature constraint (password length·validation·limit·permission·SLA). **Not identity**
  (identity = brand voice, core_value = conflict tie-breaker, rule = operations). Per-feature, inside the feature.
- Includes: policy·constraint·SLA·**permissions** (a per-actor CRUD matrix `actor_permissions`).
- (Cross-cutting policy [spanning multiple features/services] is not yet modeled — YAGNI, revisit when concretely needed.)

### `note` — edge-less canvas-global context
- **Asks:** what context applies across this whole feature?
- Canvas-global ambient context ("mobile-first·body ≤ 500 chars"). A guide a human reads **+ context the AI always
  lays under** its work (injected into the per-canvas framing).
- **Edge invariant:** `note` **never has an edge** (being ambient, it's not a flow participant). Multiple OK.

### `actor_ref` — read-only actor anchor
- **Asks:** who is the subject of this flow? (who starts / who can)
- Definition = a **reference** pointing to the `actor` master. Placed on the Feature canvas to **mark the subject of the flow**.
- **This session's key change:** a **read-only anchor** — you do *not* edit role definitions·value exchange here. The old
  `gives`/`receives` (per-actor-per-feature value flow) is **retired**. Value lives in
  Actors (role-level relationship edge) + the service's 5 fields ("what gets better", aggregate). Editing the role itself =
  Actors, permissions = `rule.actor_permissions`.
- The **only standalone reference node** to survive after the marathon (foundation refs moved to chips).

---

## Entity kind

### `entity` — project-global data object
- **Asks:** what does the product deal with?
- Definition = the product's data object (post·comment·user), the project-level Entities canvas. Symmetric with Actors
  (who/what).
- **AI-maintained, the user does not draw it directly.** AI emerges·registers it as a byproduct of feature/service design → human confirms.
- **Altitude guard:** name + one-line "what it holds" + rough relationships only. **Not a physical ERD** (normalization·FK·
  cardinality·types = outside Novel). Putting them in turns it into a DB-modeling tool = an identity violation.
- **Strong dedup:** semantic matching by identity before creating (post=article=write-up → one; post≠comment). Ask
  only when ambiguous. No silent merging·duplicates ❌ (a first-class duty of the AI coach + code integrity guard, ai-collaboration).
- Inspector (lean): name + "what it holds" (rough fields, no types ❌) + where it's used (back-reference, read-only)
  + rough relationships. Feature behaviour **references** the entity ("publish → create post").

---

## Retired kinds (history)

| kind | Reason retired | Where to |
|---|---|---|
| `mission_ref`·`value_ref`·`identity_ref` | The service references via chips, the feature inherits → duplication | Service inspector chips (④⑤) |
| `metric` | Below the action altitude/unneeded | (Produced value is implied by result nodes·flow edges) |
| `content` | An implementation artifact = below the altitude = the external agent's job | (User output is implied in behaviour/edges) |
| `group` | The grouping role = replaced by the `feature` level | Collapsing = a view feature (not a node kind) |

---

## Edges — governed by definition, not authorship

- The meaning of an edge (`relation`: flow/injection/inheritance + payload: direction·label) is what matters, not
  *who drew it*. AI can also propose·draw edges (especially the AI-maintained Entities canvas).
  The human can edit·delete at any time. **Forbidden = a meaningless·silently-uneditable edge.**
- A canvas can be user-draw-only by its own spec (Foundation/Actors/Services currently) —
  a per-canvas choice, not a global law.

## Design principles (load-bearing)

1. **Each kind = a distinct unit of meaning.** Different concepts are not lumped into one kind.
2. **Templates rich, requirements minimal — but the floor is real.** Most fields optional, a few hard requirements
   form the quality floor (encoding *what* Novel is).
3. **AI-first, generated through discussion.** Every node is interview·proposal → human confirmation. No empty forms ❌·no silent
   auto-generation ❌. Typed fields = structured JSON the AI reads.
4. **Symbol/Component pattern.** There is an asymmetric **producer→consumer** flow between canvases — earlier
   canvases (Foundation/Actors) *define* masters (`mission`/`core_value`/`identity`/`actor`) and later canvases
   (Services·Feature) **reference** them ("the later canvas references the earlier"). Every instance of these four
   kinds is itself a Symbol (no per-node toggle). After the marathon the only standalone reference *node* is
   `actor_ref` (Foundation references moved to service-inspector chips).
