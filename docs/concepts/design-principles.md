# Design Discrimination Principles — the coach's evaluation knowledge (v2)

> **What**: A distillation of the criteria that *tell apart* good mission·value·feature design. This is the
> knowledge source for two of the coach's three roles — "evaluating" (challenging weak content) and
> "proposing higher-level concepts" (`D-2026-07-03-O` — not RAG, but distilled principles). The interview
> *procedure* is canon in [ai-collaboration.md](ai-collaboration.md) §2; this document holds only the criteria
> for judging the *quality* of the content.
>
> **Home·consumption**: Canon = here (root concepts). Coach wiring is a follow-up (a skill or MCP resource —
> read on demand, outside the ≤1300-word prompt budget). The benchmark's challenge axis measures the effect.
>
> **Sources**: rules validated by a 20-turn benchmark + the shared structure of the answer keys for 16 famous
> services + existing canon (PHILOSOPHY·VISION). Each principle is phrased as a "discriminating question" — so
> the coach can throw it as-is.

## Mission — discrimination criteria

- **Better, not merely different**: A good mission states what in people's lives or society needs to improve.
  "Things will change" has no direction. Discriminate: "Whose what needs to become better, and in what way?"
- **A continuing commitment, not a finish line**: The condition can keep arising even after one solution works.
  Discriminate: "After the first solution succeeds, what are you still committed to improving?"
- **The solution can change**: A mission commits to the improvement, not to today's product or method. Solutions
  are put into the world, tested, and refined. Discriminate: "If this solution is replaced, does the mission
  still tell you what to improve next?"
- **Concrete enough to choose**: A sentence anyone could use cannot guide a difficult choice. Discriminate:
  "When two solutions compete, does this sentence help you choose which one better serves the mission?"

**Example pair**: Strong — "People and AI never lose sight of the essence or where the current work fits into
the whole" (the better state is clear while the solution may change). Weak — "provide an AI canvas" (a current
solution, not the improvement) · "change the world" (no direction for what should become better).

## Core value — discrimination criteria

- **A real conflict, not a preference**: A core value earns its place when choices cannot all be kept.
  Discriminate: "What are the two choices, and when do they actually conflict?"
- **A one-word name, with the full choice in the body**: The name may be one word such as "Essence". Never
  reject a value merely because its label is a noun. The body must name the recurring conflict, what takes
  priority, and the cost accepted. Discriminate: "Can I see the conflict, the choice, and the cost without
  guessing?"
- **A value with no price is decoration** (validated, benchmark turn ⑨): Filter out any value that doesn't
  name what is given up by keeping it. Discriminate: "What do you accept losing when this value wins?"
- **Values can conflict with each other**: Two core values can point in different directions. Do not force an
  artificial pair or a target count; record only conflicts the person truly faces. Discriminate: "If two values
  apply here, what decides which one takes priority in this situation?"
- **Values buried in the telling** (2026-07-23, W-106): A founder needn't label something a "value"
  for it to be one — decision criteria, communication habits, and what they refuse to tolerate already
  carry candidate values in the sentences that describe them. Discriminate: "Did the coach catch the
  value implied by how the founder described a decision or a habit, and reflect it back explicitly —
  rather than wait for a named 'our value is …'?" (Missing the buried candidates leaves the value map
  half-drawn.)

**Example pair**: Strong — "Essence": when familiar or profitable additions conflict with the mission, the
mission wins; slower delivery is accepted. Weak — "Honesty: always be honest" (no conflict or cost) ·
"Innovation: keep innovating" (no choice it resolves).

## Identity — discrimination criteria

- **Standing behavior, not only a voice**: Identity sets the attitude and way the service behaves while it
  is designed, built, and shown to users. Discriminate: "Can we tell what the service will do differently
  because of this guideline?"
- **A short directive becomes concrete action**: A label such as "밝고 명쾌하게" is valid when its summary
  and description say how to act. A vague aspiration is not enough.
- **Derived from mission and core values**: Ask whether the guideline turns the intended change and choice
  criteria into everyday behavior rather than borrowing a generic brand voice.
- **Applied continuously**: Every proposal and reply should follow the current identities. If an identity
  conflicts with a core value, follow the core value.
- **No fixed facets or count**: Keep as many guidelines as the service needs. Do not require voice, energy,
  speech style, or any other predefined set.

**Example pair**: Strong — "밝고 명쾌하게 — explain difficult ideas in plain words and lead with the
conclusion" · "The coach drafts first and shows it" · "The coach says clearly when a proposal does not
fit." Weak — "Deliver a good experience" (no behavior) · "Friendly" (no action).

## Actors — discrimination criteria

> This section currently carries only the nesting discriminator (W-61). The remaining actor criteria
> (reciprocal give/receive · trust·safety·operations actors · role-not-demographics) still live in the
> runtime copy `coaching_principles._ACTORS` and are queued for canon sync (follow-up 4).

- **Nested, not a flat list** (2026-07-14): A mature actor map nests concrete roles under broader role
  families (배달·운영 family → 전속·긱 rider); a flat top level with no nesting is still immature. It is a
  grouping of exchange roles, not a corporate org chart. Discriminate: "Are concrete roles nested under
  role families, or is the top level a flat list?"

## Service map — discrimination criteria

- **One coherent human outcome** (D-2026-08-18-B): One service owns one result
  that one or more people seek. Discriminate: "If this service works, what is
  now true for the person that was not true before?"
- **Outcome, not channel or internal process**: A screen, channel, matching
  step, settlement step, or revenue line does not become a service by itself.
  Discriminate: "Does this candidate own a result, or only describe where or
  how part of another result happens?"
- **As wide as the mission's reach**: Cover every distinct outcome needed to
  realize the mission. Do not require a fixed count. Discriminate: "Which
  outcome promised by the mission is still missing?"
- **Use only real human actors**: A single person can be the only actor in a
  valid service. When several people take part, reference their existing human
  roles. Do not invent an AI, system, or organization actor to create an
  exchange. Discriminate: "Does every referenced actor represent a real human
  role in this product?"
- **Group only when grouping helps**: A category is optional. Use it only when
  several services share a useful theme or surface; do not wrap one service to
  complete a pattern.

**Specimen of a wrong decomposition**: "search→cart→checkout→picking→delivery" as 5 services — all of it is
the internal process of one shopping outcome. The steps belong as features or
feature-flow actions, not as five services.

**Specimen of a wrong collapse**: A product helps a person design a service and
also helps them run the resulting work, but the map calls both "project work."
The two results need separate services even if the same person uses both.

## Feature — discrimination criteria

- **Is it described as a person's action?** (altitude guard): If save·fetch·render show up, it has fallen to
  implementation. Discriminate: "Is the subject of this sentence a person?"
- **Does the happy path run all the way through?**: Before branches·exceptions, start-to-end must be walkable
  in one line.
- **Promotion signal**: When one feature starts to own a distinct human outcome,
  it is a service candidate.

## Entities — discrimination criteria

- **Cover every business line** (2026-07-22, W-97): The data nouns must span all of the service map's
  surfaces, not only the primary exchange loop. A delivery app that models 주문·가게·메뉴·배달·라이더 but
  omits the nouns of its secondary lines (shopping SKU · coupon·benefit · gift card · membership subscription
  · ad) has a half-drawn data map. Discriminate: "Does every service surface's core noun appear as an entity?"
- **An identity-bearing noun, not a field** (value-vs-entity): An entity is tracked by id and changes state
  independently. A noun that lives as one field of another thing is a value, not an entity (a delivery address
  is a field of 주문; a coupon carries its own lifecycle and state). A canvas node's technical id is not proof
  that the product identifies the concept separately. Discriminate: "Does the product track this separately with
  its own state, or is it a field of something else?"
- **Conceptual entity, not implementation model**: The Entities canvas says what the product identifies and tracks.
  It does not decide classes, tables, aggregate boundaries, or storage records, and the two models need not map
  one-to-one. Discriminate: "Are we defining what the product deals with, or how the build stores it?"
- **Service↔entity pairing (missing-noun signal)**: A service surface with no core noun in the entity set is a
  gap. Discriminate: "This surface exists — where is the noun it moves?"
- **Not a role noun**: Do not duplicate an actor (an exchange party) as an entity. 라이더 is an actor; 라이더 보수
  (rider settlement) is an entity. Discriminate: "Is this an exchange party (actor) or a thing the exchange
  produces (entity)?"

## How the coach uses this (wiring instructions)

When it meets weak content, **throw the discriminating question as-is** — evaluation takes the form of a
question, not a declaration ("that's weak"). If it doesn't pass, don't rush to register — refine it once more
(the challenge axis counts this moment).

## Follow-ups (queue)

1. ~~back-extraction~~ ✅ (2026-07-03 night, agent — reflected example pairs·3 new patterns: felt-state
   missions · opposing-pair tension · trust-manufacturing surface).
2. Wiring: expose as a coach skill or MCP resource + a one-line usage instruction (offset within budget).
3. Measure before/after via the benchmark's challenge axis.
4. Sync the remaining actor criteria (reciprocity · trust·safety·operations actors · role-not-demographics)
   from `coaching_principles._ACTORS` into the Actors section above.
