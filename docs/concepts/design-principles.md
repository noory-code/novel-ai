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

## Identity — discrimination criteria

- **Behavioral, not adjectival**: A pile of adjectives ("friendly, innovative, trustworthy") is not an
  identity — it's a word list. Discriminate: "In the same moment, does one scene come to mind where this
  voice speaks or acts differently from a competitor?"
- **Does it refuse something?**: A strong identity rules a tone or behavior out; it pays a price. If it
  chose warmth, it gave up some authority/formality. Discriminate: "Is there a 'we don't do it this way'
  the identity refuses? An identity that gives up nothing is decoration."
- **Grown from mission and values, not borrowed**: A strong identity is the felt surface of the mission +
  values, not a stock brand-voice template. Discriminate: "Erase the mission and values — does this voice
  survive, or is it a stock voice you could paste onto any service?"
- **A coherent persona, not scattered adjectives**: Identity is one character — how it speaks, what it
  assumes about the user. Discriminate: "Drawn as one person, does a single scene of how they talk and
  treat the user come into focus?"

**Example pair**: Strong — "Finance as common sense — plain, no jargon to intimidate" (refuses banking's
authority/formality) · "A mischievous but relentless coach — pokes guilt with humor" (refuses polite
distance) · "Restrained conviction — show more, explain less" (refuses spec-listing). Weak — "Friendly,
innovative, and trustworthy" (adjective pile, refuses nothing) · "Delivers the best user experience" (a
slogan anyone could hang) · "Professional and polished tone" (stock voice).

## Actors — discrimination criteria

> This section currently carries only the nesting discriminator (W-61). The remaining actor criteria
> (reciprocal give/receive · trust·safety·operations actors · role-not-demographics) still live in the
> runtime copy `coaching_principles._ACTORS` and are queued for canon sync (follow-up 4).

- **Nested, not a flat list** (2026-07-14): A mature actor map nests concrete roles under broader role
  families (배달·운영 family → 전속·긱 rider); a flat top level with no nesting is still immature. It is a
  grouping of exchange roles, not a corporate org chart. Discriminate: "Are concrete roles nested under
  role families, or is the top level a flat list?"

## Service map — discrimination criteria

- **Unit of exchange** (validated, turn ⑩): One service = one surface where value is given and received.
  Standing up an internal process (matching·settlement·safety) as a service makes it an org chart, not a map.
  Discriminate: "Do different parties stand on the two sides of this surface?"
- **As wide as the mission's reach**: A real product stands on 3–6 exchange surfaces. If the map is a single
  surface, discriminate: "What exchange the mission reaches is not yet on the map?"
- **Scan for distinct businesses (brands)** (2026-07-23, W-98): When one company runs several
  businesses with different party-pairs — food delivery (restaurant↔orderer), streaming
  (viewer↔content), payments (payer↔merchant) — each is usually its own exchange surface. Do not fold
  them into facets of the first business. Discriminate: "Of the distinct brands/businesses the founder
  mentioned, which are not yet on the map as their own surface?" (The same party-pair repeating across
  surfaces means one business was over-split; a mentioned different party-pair absent from the map means
  another business was dropped whole.)
- **A strangers' transaction needs a trust-manufacturing surface** (back-extracted): Products where two
  strangers transact (Airbnb·Karrot·Uber·Baemin·YouTube) without exception stand up a separate exchange
  surface that 'manufactures trust' (verification·guarantee·dispute resolution ↔ reporting·reviews).
  Discriminate: "Do two strangers transact? Then is a trust-manufacturing surface on the map?"

**Specimen of a wrong decomposition**: "search→cart→checkout→picking→delivery" as 5 services — all of it is
the internal process of one exchange surface (shopper↔company). Picking·dispatch have no counterparty: it's
an org chart, not a map.

**Specimen of a wrong collapse**: Modeling Coupang as only "buy·sell / delivery / seller-growth /
trust" — Coupang Eats (restaurant↔orderer), Play (viewer↔content), and Pay (payer↔merchant) have
different party-pairs and are distinct businesses collapsed into one commerce facet.

## Feature — discrimination criteria

- **Is it described as a person's action?** (altitude guard): If save·fetch·render show up, it has fallen to
  implementation. Discriminate: "Is the subject of this sentence a person?"
- **Does the happy path run all the way through?**: Before branches·exceptions, start-to-end must be walkable
  in one line.
- **Promotion signal**: When one feature starts to hold multiple parties' exchange, it's a service candidate.

## Entities — discrimination criteria

- **Cover every business line** (2026-07-22, W-97): The data nouns must span all of the service map's
  surfaces, not only the primary exchange loop. A delivery app that models 주문·가게·메뉴·배달·라이더 but
  omits the nouns of its secondary lines (shopping SKU · coupon·benefit · gift card · membership subscription
  · ad) has a half-drawn data map. Discriminate: "Does every service surface's core noun appear as an entity?"
- **An identity-bearing noun, not a field** (value-vs-entity): An entity is tracked by id and changes state
  independently. A noun that lives as one field of another thing is a value, not an entity (a delivery address
  is a field of 주문; a coupon carries its own lifecycle and state). Discriminate: "Is this tracked by id with
  its own state, or is it a field of something else?"
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
