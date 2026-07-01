# Novel — i18n Korean Glossary

> **Audience:** Claude (or any contributor) writing or reviewing
> Korean strings for the Novel viewer.
>
> **Purpose:** keep Korean translations natural, consistent, and
> aligned with the user-provided canonical vocabulary. Avoid the
> "AI-translated awkward Korean" failure mode that surfaces when a
> long hint sentence reads as direct English-to-Korean syntax.
>
> **Pairs with:**
> - [`../CLAUDE.md`](../CLAUDE.md) i18n anti-pattern row — the rule "Novel is a
>   global service, i18n is non-negotiable" (originally a user-direction memory note).
> - [`PRODUCT_SPEC.md`](../../../plot/docs/PRODUCT_SPEC.md) — the canonical vocabulary
>   for Novel kinds.

---

## 1. Canonical vocabulary

The Korean spelling for Novel's domain terms is fixed. Do not vary
spelling between locales, files, or commits.

| English | Korean | Notes |
|---|---|---|
| Foundation | **파운데이션** | NOT 토대 (corrected v0.14.8). |
| Mission | **미션** | |
| Core value | **코어밸류** | NOT 핵심 가치 — user product spec. |
| Identity | **아이덴티티** | NOT 정체성 — user product spec. |
| Actor | **액터** | NOT 행위자 (corrected v0.14.6). |
| Service | **서비스** | |
| Feature | **기능** | services-overview drill target (D-2026-06-17-D). |
| Category | **카테고리** | |
| Project | **프로젝트** | |
| Entity | **엔티티** | AI-maintained data object; 액터=누가 ↔ 엔티티=무엇 (D-2026-06-17-I). |
| Note | **노트** | edgeless canvas-global context node (D-2026-06-17-F). |
| Metric | **지표** | |
| Step | **단계** | |
| Rule | **규칙** | |
| Content | **콘텐츠** | NOT 컨텐츠. |
| ~~User journey~~ | ~~유저저니~~ | **RETIRED — service→service "유저저니" edges dropped (D-2026-06-17-C).** |
| Symbol | **심볼** | |
| Instance | **인스턴스** | |
| Snapshot | **스냅샷** | |
| User story | **유저스토리** | |
| Task | **태스크** | |
| MCP | **MCP** | leave as-is (proper noun / acronym). |
| Agent | **에이전트** | |
| Pain point | **페인포인트** | |
| Tab / Toggle | **탭 / 토글** | UI mechanics, transliterate. |

## 2. UI-context fragments

Short label / button text. Already settled.

| English | Korean |
|---|---|
| Undo / Redo | 되돌리기 / 다시 실행 |
| Delete | 삭제 |
| Rename | 이름 변경 |
| Close | 닫기 |
| Save | 저장 |
| Cancel | 취소 |
| Narrow / Widen | 좁게 / 넓게 |
| (unset) | (미지정) |
| (none) | (없음) |
| (none yet) | (아직 없음) |
| Mark session… | 세션 기록… |
| New project | 새 프로젝트 |
| Session tags | 세션 태그 |

## 3. Hint sentences — review process

Hint sentences (the small italic description after a field label,
e.g. "current-tense daily activity") are the most likely failure
mode. They MUST go through user review before commit.

**Process:**

1. Add the English source to `inspector.fieldHint.*` (or wherever
   the hint lives) in `en.json`.
2. Draft a Korean candidate in `ko.json`.
3. **Before committing**, surface the new Korean hints via
   `AskUserQuestion` (one question per commit, batch all new
   hints into multiSelect options or list them in the question
   text).
4. Apply user corrections, log them in this file's §4
   correction log, then commit.

**Don't:**

- Translate idioms literally. "current-tense daily activity" is
  not "현재형 일일 활동" — say "현재형으로 표현한 매일의 활동" or
  shorter.
- Use academic vocabulary (e.g. "측면", "양상") when a casual
  word ("속성", "종류") fits better.
- Skip review on a hint just because it's "obvious". If the
  user notices unnatural Korean, the cost of a correction commit
  exceeds the cost of one AskUserQuestion.

## 4. Correction log

Track corrections so the same mistake does not repeat across
commits.

| Date | English | Initial Korean | Corrected to | Source |
|---|---|---|---|---|
| 2026-05-11 | Foundation (tab) | 토대 | **파운데이션** | user direction during v0.14.7 |
| 2026-05-11 | Actors (tab) | 행위자 | **액터** | user product spec |
| 2026-05-12 | "one per aspect — Voice, Energy, Speech style, …" | 측면별로 하나씩 — 목소리, 에너지, 말투, … | **속성별로 하나씩 — 목소리, 에너지, 말투, …** | user pointed out 측면 is unnatural; user picked 속성. (측면→속성 rule still applies. ⚠ The identity "facet/aspect" framing this hint described is **superseded**: identity is now a **standing execution/expression action-rule list**, not per-aspect attributes — D-2026-06-16-N/O.) |
| 2026-05-12 | "이 측면이 어떻게 드러나는가" (Identity description hint) | 이 측면이 어떻게 드러나는가 | **이 속성이 어떻게 드러나는가** | follows the 측면→속성 rule above. ⚠ **STALE — the identity `description` field is removed** (inspector = name + action-rule list, D-2026-06-16-O); this hint string no longer exists. Kept for audit trail. |

## 5. When this file changes

- New canonical term (a Novel kind, surface, mechanic) → §1.
- New UI label translation → §2.
- A user-driven correction → §4 + the underlying §1 / §2 / locale
  file update. Add the correction date and source so future
  Claude sessions see the audit trail.
