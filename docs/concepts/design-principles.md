# Design Discrimination Principles — the coach's evaluation knowledge (v1)

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

- **Change, not direction**: A good mission captures whose what becomes different. "We provide ~" is a
  feature statement, not a mission. Discriminate: "On the morning this is achieved, who in the world is doing
  what differently?"
- **A sustainable problem**: A mission built on a problem that ends once solved is a project, not a company.
  Discriminate: "Ten years from now, is this problem still being born anew?"
- **Is the reason it has to be you inside it?**: A sentence anyone could use is a slogan, not a mission.
  Discriminate: "If a competitor hung this exact sentence and it wouldn't feel odd — redo it."
- **Did it descend to a felt state?** (back-extracted): The strongest missions write the change not as an
  abstract noun (accessibility·creativity) but as one person's felt experience — "How did we ever live
  without Coupang?" is the specimen. Discriminate: "Is this mission a third-person noun, or one person's felt
  state?"

**Example pair**: Strong — Toss "not difficult, inconvenient, distant finance, but finance that is easy and
common-sense for everyone" (before→after is inside the sentence). Weak — "anyone finishes transfers·investing·
payments in one app with a few taps" (a feature statement posing as a mission, a completed form that ends once
done) · "make the world better for everyone" (a slogan anyone could hang, no change).

## Core value — discrimination criteria

- **A value with no price is decoration** (validated, benchmark turn ⑨): Filter out any value that doesn't
  name what you lose by keeping it. Discriminate: "When did keeping this cost you something recently?"
- **Are the domains split apart?** (validated, turn 19): A mature value system is spread across different
  domains — customer treatment·quality·speed·money vs principle·way of working. If they're all in the customer
  family, it's still the mission's echo. Discriminate: "Is there a moment where these values collide with each
  other?" (a good system holds internal tension)
- **Is it an action statement?**: A noun like "honesty" is a word, not a value. The mature values in the
  answer keys are all action-directives ("Wow the customer", "don't block first"). Discriminate: "Can a new
  hire read this sentence alone and act differently tomorrow?"
- **Is there an opposing-pair tension?** (back-extracted): A mature system goes beyond domain spread and names
  pairs that pull against each other — Baemin hangs "be fast" and "good enough is not good enough" as an
  intended tension. Discriminate: "Are there two values that are flatly opposite? If not, you've still only
  seen one face."

**Example pair**: Strong — Coupang "Customer Wow" (price = margin), Shopify "software should never make people
feel stupid" (price = ship date), Duolingo "take the long view" (price = immediate revenue), Netflix "dream
team" (price = job security). Weak — "Honesty: always be honest" (no price·a noun) · "Innovation: innovate
ceaselessly" (nothing given up·an unmeasurable decorative word).

## Service map — discrimination criteria

- **Unit of exchange** (validated, turn ⑩): One service = one surface where value is given and received.
  Standing up an internal process (matching·settlement·safety) as a service makes it an org chart, not a map.
  Discriminate: "Do different parties stand on the two sides of this surface?"
- **As wide as the mission's reach**: A real product stands on 3–6 exchange surfaces. If the map is a single
  surface, discriminate: "What exchange the mission reaches is not yet on the map?"
- **A strangers' transaction needs a trust-manufacturing surface** (back-extracted): Products where two
  strangers transact (Airbnb·Karrot·Uber·Baemin·YouTube) without exception stand up a separate exchange
  surface that 'manufactures trust' (verification·guarantee·dispute resolution ↔ reporting·reviews).
  Discriminate: "Do two strangers transact? Then is a trust-manufacturing surface on the map?"

**Specimen of a wrong decomposition**: "search→cart→checkout→picking→delivery" as 5 services — all of it is
the internal process of one exchange surface (shopper↔company). Picking·dispatch have no counterparty: it's
an org chart, not a map.

## Feature — discrimination criteria

- **Is it described as a person's action?** (altitude guard): If save·fetch·render show up, it has fallen to
  implementation. Discriminate: "Is the subject of this sentence a person?"
- **Does the happy path run all the way through?**: Before branches·exceptions, start-to-end must be walkable
  in one line.
- **Promotion signal**: When one feature starts to hold multiple parties' exchange, it's a service candidate.

## How the coach uses this (wiring instructions)

When it meets weak content, **throw the discriminating question as-is** — evaluation takes the form of a
question, not a declaration ("that's weak"). If it doesn't pass, don't rush to register — refine it once more
(the challenge axis counts this moment).

## Follow-ups (queue)

1. ~~back-extraction~~ ✅ (2026-07-03 night, agent — reflected example pairs·3 new patterns: felt-state
   missions · opposing-pair tension · trust-manufacturing surface).
2. Wiring: expose as a coach skill or MCP resource + a one-line usage instruction (offset within budget).
3. Measure before/after via the benchmark's challenge axis.
