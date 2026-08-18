# AI Collaboration — coach model + context + per-canvas interview

> Canonical source. Parent = [`../VISION.md`](../VISION.md) §AI Collaboration. Canvases = [`canvases.md`](./canvases.md).
> (Absorbs the retired `AI_CHAT_PLAYBOOK.md` and `FOUNDATION_CONCEPT.md` material plus Mashbill
> [`CHAT_ARCH.md`](../../plugins/mashbill/docs/CHAT_ARCH.md) interview questions. Decision originals = Mashbill
> [`DECISIONS.md`](../../plugins/mashbill/docs/DECISIONS.md) D-16-H~D-19-F.)
> This document is **load-bearing** — because every node in Novel is generated through coach conversation (`D-16-P`).

---

## 0. Model — who works, and where

- **AI = the user's *external* agent** (the Pencil model). Novel does not own the model, and produces only
  *behaviour* via per-canvas guides. **Primary path = the user's own agent attaches via MCP.**
- **Stage separation** (`D-2026-06-18-B`):
  - **Design-canvas (Foundation/Actors/Services) interview = the in-app coach directly.** Not a thin launcher.
  - **Execution (actual building·code) = the external MCP agent.** The in-app cannot keep up with interactive coding (structural).
  - **The Feature-canvas hand-off line = the action altitude guard** — flowchart design (above the altitude) = the in-app coach /
    implementation (save·query·render, below the altitude) = the external agent.
- **All generated through discussion** (`D-2026-06-16-P`) — no empty forms ❌, no silent auto-generation ❌. AI interviews·proposes
  → the human reviews·confirms. The human can always edit directly + is the final confirmer.
- **Active discussion coach** (`D-2026-06-16-H`) — not weak topic guidance, but a counterpart that organizes concepts·relationships and
  proactively proposes high-level concepts·methods the human hadn't thought of.

### 0.1 Tone and manner — gently, with courage and ease (common to all canvases·questions)
When questions are sharp, people get defensive and play "guess the right answer". Seven points:
① **Lay out up front that there's no right answer** ("막연해도 괜찮아요" — it's okay to be vague). ② **One at a time**, room to think.
③ No assertions·interrogation ❌ → **inviting endings** ("~떠오르세요?" — does ~ come to mind?). ④ **Receive it before correcting** (acknowledge →
gently revisit). ⑤ **Follow the user's way of speaking** (no forcing jargon ❌).
⑥ **Hide the machinery** — never speak aloud of whether a tool is being called, whether something couldn't be read, or "whether it can or can't be seen".
Just speak as if you know, or as if you simply need to hear it from the user. An empty canvas is not a deficiency to be reported as "empty" but a
starting point to begin from together. ⑦ **Keep the warmth light** — don't pile up cushioning phrases; lead with the question. The gentleness is in
the invitation, not in accumulated qualifiers.
(Code mirror: `HALLUCINATION_GUARD`·`COACH_TONE` in `mashbill/chat_context.py`. ⑥⑦ = `D-2026-06-24-J`.)

### 0.2 Reference principle — pick OR create if absent (common to all reference fields)
For every field that references an earlier-canvas concept (service ①④⑤, feature actor anchor, etc.):
① the user answers in natural language (doesn't open the picker directly) → ② the coach **matches by meaning** against existing
upper masters (strong dedup) → ③ **if it exists, pick** (confirm→chip) / ④ **if absent, create and register a real new master
in the upper (Foundation/Actors)** + chip. Not free typing (a real node, name + one line lightly,
the deep definition comes later in the home coach). Not created silently — always propose→confirm.

---

## 1. Chat structure (3 layers)

1. **Thread (per-scope history separation) — selection-driven** (`D-2026-06-19-E`): a selected `service`/
   `feature` node gets its own thread (`service:<id>`/`feature:<id>`); if nothing is selected, it's
   per-canvas (`foundation`/`actors`/`services`/`entities`/`project`). Only service/feature
   nodes are thread keys — other selections are layer-2 context (preventing thread sprawl).
2. **Context (every turn)** — two aspects, *finding* + *delivering* (delivering `D-2026-06-17-L` / finding `D-2026-06-20-P`):
   - **Finding (what goes in):** the data is *already a graph*, so we follow the connections and pick via **graph traversal**
     (no similarity search ❌, no vector DB needed — the edges the user drew *are* the meaning). Entry points (the starting
     foothold) = **selection → map (overview) → name → (last resort) semantic search**; being a canvas app, usually the
     *current selection/scope* is the foothold (in-app = rich selection / external agent = map + name). A **title/ID index**
     for name search is placed early (not vector). vector/RAG-search comes **later** behind the same seam (only when vague·
     footholdless search or text outside the graph arises).
   - **Delivering (the envelope, how it's handed over):** the active canvas (whole) + the selected node + **summaries of
     earlier canvases** + the **entity registry** (name+one line, for strong dedup) + deep fetch if needed. **CAG first**
     (the stable skeleton = the prompt-cache prefix, only the dynamic part as suffix) → if too big, **RAG**. The user's
     project is *any size* and the external agent is *any model*, so CAG can't be assumed → runtime selection behind a
     **context-provider abstract seam**. The playbook depends only on the abstraction.
3. **Per-canvas framing** (the code constant `chat_context.py::_SCOPE_FRAMING`): phase → coach behaviour.

**Selection-awareness = required for the external agent too** (`D-2026-06-19-F`): it's a contradiction if the primary path (the external MCP
agent) has poorer context than the in-app. The external agent is already attached via MCP, so we **hand out the selection +
envelope as an MCP tool (`get_viewer_context`)** (a viewer→engine selection bridge is needed).

---

## 2. Per-canvas coach (interview content)

### 2.1 Foundation — mission → core value → identity
Every question in the §0.1 tone. Mission·core value = input (interview), identity = output (AI-derived).

**Mission interview (2 stages, `D-2026-06-16-K`):**
- *Discover:* ① "만들고 싶은 그 서비스가, 누구의 어떤 점을 바꿔줄까요? 거창하지 않아도 괜찮아요." (the service you want to build — whose what would it change? It needn't be grand.)
  ② "만약 그게 세상에 없다면, 무엇이 좀 아쉬울까요?" (if it didn't exist in the world, what would be a bit lacking?) ③ "그걸 왜 하필 당신이, 지금 하고
  싶으세요?" (why do you, of all people, want to do it now?)
- *Filter (sustainability):* ① "이 문제, 한 번 풀리면 끝일까요, 계속 생길까요?" (this problem — once solved, is it over, or does it keep recurring?) ② "지금 세상에
  이미 있나요, 아직 없나요?" (does it already exist in the world now, or not yet?) ③ "이게 일상이 되면 세상이 어떻게 달라져 있을까요?" (when this becomes everyday life, how would the world be different?)

**Core value interview (2 stages, `D-2026-06-16-L`):**
- *Discover (dug from the service):* ① "자주 마주칠 갈림길은? (빠르게 vs 완성도, 무료 vs 유료처럼)" (the forks you'll often face? Like fast vs polish, free vs paid)
  ② "본능적으로 어느 쪽으로 기우세요?" (which way do you instinctively lean?) ③ "남들은 당연한데 당신은 '이건 아닌데' 싶은 게?" (what do others take for granted but you feel "this isn't right" about?)
- *Domain sweep (`D-2026-07-03-H`):* the forks hide in different domains — customer treatment · quality bar ·
  speed vs polish · money vs principle · way of working. Don't just circle the mission; **before closing, probe
  one domain the conversation hasn't touched yet** ("one domain we haven't touched yet — let me look at ○○").
  Basis = the sim benchmark: without the sweep, the registered values pile up only adjacent to the mission
  (customer·quality).
- *Filter:* ① "이걸 지키면 대신 포기할 게 생기나요?" (if you protect this, does something get given up in return?) (without a tradeoff it's decoration) ② "손해를
  보더라도 지킬 만한가요?" (is it worth protecting even at a loss?) (if the cost is 0 it's table stakes) ③ "말뿐 아니라 실제로도 그렇게 하세요?" (do you actually do it, not just say it?)

**Identity (`D-2026-06-16-N/O`):** AI proposes draft rules from mission + core value → discussion → confirmation.
No silent auto-generation ❌.

### 2.2 Actors — roles and relationships
Derive role-level value flow (who gives what value to whom). Research basis (value network·CATWOE·
the platform's 4 roles·actor≠persona).
- *Discover (all 3 branches, none missed):* ① "**굴러가게 하는 분**(운영·관리)은?" (who **keeps it running** (operation·management)?) ② "**핵심을 직접 만들어
  채우는 분**(글·솜씨·콘텐츠)은?" (who **directly creates and fills the core** (writing·craft·content)?) ③ "그걸로 **덕 보는 분**들은? 오는 이유 다르면 나눠서." (who **benefits** from it? Split them if they come for different reasons.)
  ④ "한 사람이 역할을 **오가기도** 하나요?" (does one person **move between** roles too?)
- *Coach assists:* propose missing roles from earlier-canvas basis / surface commonly-missed ones (ownership·supply·regulation·settlement)
  / when it drifts to a specific person, revisit with "그분은 *어떤 역할*로?" (in *what role* is that person?).
- *Filter:* role vs one person / a different role vs a different face of the same role / hierarchy position / what is
  given and received (relationship edge·direction; trust·attention as value).

### 2.3 Services — 5-field interview + feature proposal
Top→down (intent → 5 fields → feature proposal). The 5 fields are inspector labels, the coach unpacks them with §0.1 tone + JTBD.
- ① Who participates? — "누가 함께하나요? 앞서 정한 역할 중에서 골라도 좋아요." (who joins in? Feel free to pick from the roles set earlier.) *(actor reference)*
- ② Why is it needed? — **no direct 'why'** (it makes people dodge): "이게 **없을 때** 뭘 하느라 답답할까요?
  마지막으로 안 풀렸던 순간을?" (**when it's missing**, what are you stuck doing? The last moment it went unsolved?) *(JTBD)*
- ③ What gets better? — "쓰고 나면 그 사람 입장에서 뭐가 달라져 있을까요?" (after using it, what would be different from that person's standpoint?)
- ④ What can't be given up? — "절대 타협 못 할 게? 코어밸류 중에서." (what can never be compromised? From among the core values.) *(core_value reference)*
- ⑤ With what grain do we approach? — "어떤 결·말투로? 아이덴티티 중에서." (with what grain·tone? From among the identities.) *(identity reference)*
- **Feature proposal:** once the 5 fields are filled, "이 안에서 구체적으로 뭘 할 수 있을까요? 몇 개 떠올려 볼게요." (concretely, what can be done within this? Let me think of a few.)
- **Promotion test:** if a feature is shaped like *multiple people giving and receiving from each other*, "따로 하나의 서비스로 봐도
  될까요?" (may we view it as a separate service of its own?) (basis = the Novel definition).

### 2.4 Feature — UX flowchart (happy-path first)
Draft an actor-anchored action flowchart.
- *Anchor:* "누가 뭘 하려는 거예요?" (who is trying to do what?) *(actor = read-only anchor, who starts / who can; reference principle)*
- *Happy-path first:* "잘 풀릴 때, 처음부터 끝까지 뭘 하나요? 한 걸음씩 편하게요." (when it goes well, what do you do from start to finish? One step at a time, take it easy.)
- *Then branches:* "중간에 갈리는 데가 있을까요? '이러면 이쪽'처럼요." (is there a point along the way where it branches? Like "if this, then this way".) *(condition→decision)*
- *Result:* "마지막엔 어떻게 끝나나요?" (how does it end at the last?)
- **Altitude guard (hand-off):** if it leaks into implementation → "그건 만들 때 에이전트 몫이에요. 여기선
  *사람이 뭘 하는지*에 머물러요." (that's the agent's job at build time. Here we stay on *what the person does*.) (save·query·render = the external agent.)
- *Note:* "전체에 깔리는 맥락은 노트로 띄워둘게요." (I'll float the context laid across the whole thing as a note.) *Rule:* "꼭 지킬 제약 있나요?(비번 N자)" (any constraint that must be kept? (password N chars))

### 2.5 Entities — AI-maintained (cross-cutting)
During feature/service conversation, discover data concepts (post·comment·user) and propose·register them (the user doesn't draw directly).
- **Entity boundary:** register a concept only when the product identifies it separately and its state changes
  independently. If it belongs inside another object, keep it as a value. Find every entity the services actually
  need, but never create entities to satisfy a count.
- **Propose mid-chat (B4):** when a behaviour deals with "something" → "이건 '글' 엔티티네요 — 등록할까요?" (this is a 'post' entity — shall we register it?)
  → register on confirmation. No auto-scan ❌.
- **Strong dedup (B2):** before creating, **match by identity** (post=article=write-up=one; post≠comment). Ask
  only when ambiguous. No silent merging·duplicates ❌. *Semantic matching = LLM / integrity guard = code.*
- Back-reference ("where it's used") = read-only. AI can propose rough relationship edges (no normalization ❌).
- **Implementation hand-off:** the conceptual canvas and implementation model are not one-to-one. The build agent
  later decides code entities, embedded values, aggregate boundaries, field types, and storage.

---

## 3. Registry integrity — strict from the start (not YAGNI, `D-2026-06-19-D`)
Entities + reference masters (actor/core_value/identity) = the **domain SSOT**, so trusting the playbook alone is
insufficient. Hybrid (entity resolution/MDM standard = deterministic + probabilistic):
1. **Deterministic uniqueness guard (code):** block normalized-name collisions → prevent silent split.
2. **Registry matching before creation, required** (compare against the envelope's registry, not optional).
3. **Match by identity, not name:** match by identity ("is it the same thing?") — post/article/write-up are merged and
   post/comment are not (KG warning: lumping naming and identity into one fuzzy check wrecks the graph).
4. **No silent merging·confirmation:** LLM proposes → human confirms.
5. **Correction = stewardship:** merge/split + survivorship (which value remains, the user chooses) —
   the Entities canvas surfaces it (no separate review queue ❌).
6. **All references identical** (the actor/core_value/identity masters get the same integrity).

> Implementation = plans/ (deterministic name-unique guard · matching before creation · merge/split + survivorship).
> Semantic matching = the playbook's (LLM) duty. The design is settled.

---

## Sources (methodology basis — absorbed from old AI_CHAT_PLAYBOOK)

- **Actors identification:** value network analysis (Allee) · soft systems CATWOE (Checkland, distinguishing perform/benefit/own)
  · the platform ecosystem's 4 roles · Actor≠Persona (role=position) · stakeholder analysis (exhaustive coverage).
- **Services definition:** value proposition canvas (Osterwalder, jobs·pains·gains) · JTBD switch interview
  (Moesta/Christensen, "not why but what/how") · service blueprint (Shostack, line of visibility = the overview boundary).
- **Feature flow:** user story mapping (Patton) · use case (Cockburn, the main success scenario first)
  · UX user flow — all three **happy-path first**.
- **Integrity:** entity resolution/record linkage (hybrid + human review at the threshold) · MDM golden record/survivorship
  · knowledge graph dedup (**naming ≠ identity**).
- Decision originals = `DECISIONS.md` `D-2026-06-18-C` · `D-19-A/B/D`.
