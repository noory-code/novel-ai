---
name: solera-write-identity
description: Establish what your service stands for — write the Mission, Core Values, Vision, and a first cut of Goals.
metadata:
  version: "2.0.0"
  category: writing
  type: composite
  style: guide
  triggers: [define service identity, write mission statement, establish core values, set up identity, identity setup]
  uses: []
---

# Writing Identity

> Defines the service identity through Mission, Core Values, Vision, and a rough Goals list.
> Run this once before starting any Goal-level work.

## Prerequisites

- Service name and target user known (collected via conversation if not provided)

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **service_name** | N | Service name (collected via conversation if omitted) | task-app |
| **target_user** | N | Target user (collected via conversation if omitted) | freelancers |
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Mission | `{project_path}/identity/mission.md` |
| Create | Core Values | `{project_path}/identity/core-values.md` |
| Create | Vision | `{project_path}/identity/vision_1.md` |
| Create | Goals (rough) | `{project_path}/initiative/{year}/goals.md` |

## Procedure

1. **Discovery Interview**
   - [ ] If `team-process.md` exists at `{project_path}/workspace/team-process.md`, read it and skip questions already answered
   - [ ] If `service_name` is not provided, ask: "What is the name of your service?"
   - [ ] If `target_user` is not provided, ask: "Who are the primary users of this service?"
   - [ ] Gather persona details for each user type via the following questions.
     Ask all questions per persona; if the answer is vague, ask a follow-up to get specifics.

   **Per-persona interview (NN/G 6-field model):**
   ```
   "이 사용자의 역할/직군은 무엇인가요? (예: 바리스타, 프리랜서 개발자, 중소기업 대표)"
   "기술 수준은 어느 정도인가요? (초보 / 중급 / 전문가)"
     → 모호하면: "스마트폰 앱을 혼자 설치할 수 있는 수준인가요, 아니면 개발자 수준인가요?"
   "언제, 어디서, 왜 이 서비스를 쓰나요? (사용 맥락)"
     → 예: "출퇴근 중 모바일로, 빠르게 재고 확인하려고"
   "이 서비스로 궁극적으로 달성하려는 목표가 뭔가요?"
   "지금 겪고 있는 가장 큰 불편함이나 문제는 뭔가요?"
   "이 사람이 할 법한 말 한 문장을 만들어주세요. (대표 한마디)"
     → 예: "재고 파악하느라 매일 아침 30분을 낭비하고 있어요."
   ```

   - [ ] Repeat for each persona (2–4 recommended)
   - [ ] **Personas are additive** — when a new user type is discovered later, re-invoke `solera-write-identity` to add a persona without modifying existing ones

2. **Define Mission** — ref: [assets/mission.md](assets/mission.md)
   - [ ] Write a one-sentence mission statement: "For [who], through [how], we build [what]."
   - [ ] Define key terms used in the mission
   - [ ] Write the underlying philosophy (beliefs that support the mission)
   - [ ] Save to `{project_path}/identity/mission.md`

3. **Define Core Values** — ref: [assets/core-values.md](assets/core-values.md)
   - [ ] Define 3–5 core values
   - [ ] For each value, write a decision-making criterion: "When in doubt, ask: [question]"
   - [ ] Save to `{project_path}/identity/core-values.md`

4. **Define Vision** — ref: [assets/vision.md](assets/vision.md)
   - [ ] Describe a concrete future state the service aims to reach
   - [ ] Write measurable achievement conditions (checklist format)
   - [ ] Save to `{project_path}/identity/vision_1.md`

5. **Draft Goals list** — ref: [assets/goals.md](assets/goals.md)
   - [ ] List Goals that contribute to the Vision (rough — will be elaborated later)
   - [ ] Assign IDs: G1, G2, ...
   - [ ] Link each Goal to a core value
   - [ ] Mark each as Feature or Enabler
   - [ ] Save to `{project_path}/initiative/{year}/goals.md`

## Folder Structure

```
{project_path}/
├── identity/
│   ├── mission.md
│   ├── core-values.md
│   └── vision_1.md
└── initiative/{year}/
    └── goals.md
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| service_name 누락 | 파라미터가 제공되지 않음 | 사용자에게 "서비스 이름은 무엇입니까?" 질문 | 파라미터 수집 후 계속 진행 |
| target_user 누락 | 파라미터가 제공되지 않음 | 사용자에게 "주요 사용자는 누구입니까?" 질문 | 파라미터 수집 후 계속 진행 |
| project_path 없음 | 디렉토리가 존재하지 않음 | `mkdir -p {project_path}` 실행 | 디렉토리 생성 후 계속 진행 |
| 파일 쓰기 실패 | 권한 오류 또는 디스크 공간 부족 | 오류 메시지 출력, 사용자에게 권한 확인 요청 | 스킬 중단, 오류 상태 반환 |
| 템플릿 에셋 누락 | assets/ 디렉토리의 템플릿 파일 없음 | 기본 구조로 문서 생성 (템플릿 없이 진행) | 경고 메시지 출력, 작업 계속 진행 |

## Completion Checklist

- [ ] mission.md created — explains the "why"
- [ ] core-values.md created — 3–5 values with decision criteria
- [ ] vision_1.md created — concrete future state with measurable conditions
- [ ] goals.md created — Goal IDs assigned, linked to values, Feature/Enabler classified
- [ ] Ready to hand off to solera-write-phase or solera-write-goal
