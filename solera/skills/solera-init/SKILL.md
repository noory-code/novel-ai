---
name: solera-init
description: Set up Solera in a project — install rules and create the workspace folder structure.
metadata:
  version: "1.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [set up solera, initialize solera, install solera, solera init, solera 설치, solera 설정, solera 초기화]
  uses: []
---

# Solera Init

> Sets up Solera in the current project by installing rules and creating the workspace structure.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root (where `workspace/` will live) | . |

## Output

| Step | Output | Path |
|------|--------|------|
| Rules | Workflow rule | `.claude/rules/solera-workflow.md` |
| Folders | Workspace skeleton | `{project_path}/workspace/` |
| State | Progress file | `{project_path}/progress.md` |

## Procedure

### Step 1. Check existing setup

- [ ] Check if `.claude/rules/solera-workflow.md` already exists
  - If exists: ask user whether to overwrite or skip
- [ ] Check if `{project_path}/workspace/` already exists
  - If exists: skip folder creation, proceed to rule installation

### Step 2. Install rules

- [ ] Create `.claude/rules/` directory (if not exists)
- [ ] Write `.claude/rules/solera-workflow.md` — ref: [assets/solera-workflow.md](assets/solera-workflow.md)
  - Copy the asset content as-is (no variable substitution needed)

### Step 3. Create workspace structure

- [ ] Create folder structure:
  ```
  {project_path}/
  ├── progress.md
  └── workspace/
      ├── identity/
      ├── initiative/
      └── catalog/
          └── published/
  ```
- [ ] Write initial `progress.md`:
  ```markdown
  # Progress

  > Phase: (none)
  > Goal: (none)
  > Epic: (none)
  > Story: (none)
  > Action Item: (none)
  ```

### Step 4. Verify

- [ ] `.claude/rules/solera-workflow.md` exists and is non-empty
- [ ] `{project_path}/workspace/` directory exists
- [ ] `{project_path}/progress.md` exists

### Step 5. Team Kickoff Interview

Collect team process information through a conversational interview.
Ask questions in order; if answers are vague, ask follow-up questions to get specifics.
Save results to `{project_path}/workspace/team-process.md`.

**Interview questions:**

```
1. 서비스 기본
   - "어떤 서비스를 만드나요? 한 문장으로 설명해주세요."
   - "주요 사용자는 누구인가요?"
     → 모호하면: "어떤 상황에서 이 서비스를 쓰게 되나요? 직군이나 역할이 있나요?"

2. 개발 프로세스

   2-1. 단계 구성
        "기능 개발 시 어떤 단계를 거치나요? 팀에서 실제로 사용하는 단계를 나열해주세요."
        → 답이 모호하면 아래 목록을 제시하고 해당하는 것을 선택하게 함:
          [ ] 기획/요구사항 정의     — 무엇을 만들지 결정
          [ ] UX 설계 (와이어프레임) — 화면 흐름 설계 (UX와 UI를 구분하지 않는다면 하나로 합쳐도 됨)
          [ ] UI 디자인 (시각 디자인) — 실제 화면 디자인 (UX와 별도 단계로 진행하는 경우)
          [ ] 도메인/엔티티 설계     — 데이터 구조 설계
          [ ] API 설계               — 인터페이스 정의
          [ ] 백엔드 개발
          [ ] 프론트엔드 개발
          [ ] 테스트 (단위/통합/E2E)
          [ ] 코드 리뷰
          [ ] QA/검수
          [ ] 배포

        체크리스트 선택 완료 후:
        → 백엔드와 프론트엔드를 모두 선택한 경우: "백엔드와 프론트엔드 개발은 동시에 진행하나요, 아니면 순서가 있나요?"
        → UX 설계와 UI 디자인을 모두 선택한 경우: "두 단계를 별도 담당자가 진행하나요, 아니면 동일 담당자가 순서대로 진행하나요?"

   2-2. 단계별 심화 (선택된 단계에 대해서만 질문)

        기획/요구사항 단계가 있다면:
          "요구사항의 완료 기준은 무엇인가요?"
            → 예: "PRD 문서 작성 완료", "팀장 승인", "사용자 스토리 형식으로 작성"
          "요구사항 문서 형식이 있나요? (PRD / 사용자 스토리 / 없음)"

        UX 설계 단계가 있다면:
          "UX 설계 완료 기준은 무엇인가요?"
            → 예: "모든 핵심 플로우의 와이어프레임 완성", "사용자 테스트 1회 이상"
          "와이어프레임 툴은? (Figma / Balsamiq / 기타)"
          "UX 설계 결과물이 다음 단계의 게이트 조건인가요? (필수 / 선택)"

        UI 디자인 단계가 있다면:
          "디자인 완료 기준은 무엇인가요?"
            → 예: "디자이너 최종 확인", "Figma 링크 _epic.md에 첨부"
          "디자인 시스템이 있나요? (있음 / 없음 / 구축 중)"
          "개발 시작 전 디자인이 반드시 완료되어야 하나요?"
            → 필수면: "백엔드/프론트 모두인가요, 아니면 프론트엔드 개발 시작 전만인가요?"

        도메인/엔티티 설계 단계가 있다면:
          "엔티티 설계 완료 기준은 무엇인가요?"
            → 예: "ERD 작성 완료", "팀 리뷰 통과"
          "엔티티 설계는 누가 주도하나요? (백엔드 개발자 / 아키텍트 / 팀 전체)"
          "설계 결과물 형식은? (ERD 다이어그램 / 클래스 다이어그램 / 문서)"
          "엔티티 설계 완료가 백엔드 개발 시작 전 조건인가요, 전체 개발 시작 전 조건인가요?"

        API 설계 단계가 있다면:
          "API 설계 완료 기준은? (예: OpenAPI spec 작성, Postman collection 공유)"
          "API 설계는 프론트엔드와 백엔드 협의 후 확정인가요?"

        테스트 단계가 있다면:
          "테스트 커버리지 기준이 있나요? (예: 80% 이상 / 없음)"
          "어떤 테스트를 필수로 작성하나요? (단위 / 통합 / E2E / 없음)"
          "QA는 별도 담당자가 있나요, 아니면 개발자 자체 검수인가요?"

        코드 리뷰 단계가 있다면:
          "리뷰 기준이 있나요? (체크리스트 / 자유 형식)"
          "리뷰 통과 기준은? (승인 N명 / 특정 역할 필수)"
          → 수집한 승인 수를 pr_approvals로 재사용 (Section 4에서 중복 질문 안 함)

        인프라/배포 단계가 있다면:
          "CI/CD 파이프라인은 어떻게 구성되어 있나요? (GitHub Actions / Jenkins / 없음 / 기타)"
          "배포 환경이 여러 개인가요? (dev / staging / prod)"
          "배포 승인 절차가 있나요? (자동 배포 / 수동 승인 필요)"

   2-3. 게이트 조건 정리
        수집한 답변을 바탕으로 AI가 workflow_gates를 도출한 뒤 사용자에게 확인.

        도출 규칙:
        - done_when + gate=true 인 단계 → 해당 단계가 막는 Solera 스텝에 게이트 추가
        - 여러 gate=true 단계가 같은 Solera 스텝을 막으면:
          → 각 단계가 백엔드/프론트 중 어느 쪽 개발을 막는지 확인:
            "UI 디자인 완료 조건은 프론트엔드 개발 시작 전인가요, 전체 개발 시작 전인가요?"
          → 답변에 따라 단일 게이트 또는 분리 게이트로 작성

        확인 메시지 형식:
        "정리하면 이런 게이트가 있는 것 같은데요, 맞나요?
         - epic.use_case:  '{조건}'
         - epic.concept:   '{조건}'
         - story.execute:  '{조건}'
         - story.wrap_up:  '{조건}'
         확인 또는 수정해주세요."

        단계 체크리스트에서 처음 언급했으나 최종 선택에서 빠진 단계가 있다면:
        → "처음에 [단계명]도 언급하셨는데, 목록에서는 선택하지 않으셨어요.
           이 단계는 Solera 관리 밖인가요, 아니면 추가할까요?"

3. 기술 스택
   백엔드:
   - "백엔드 프레임워크는 무엇인가요?"
     → Spring Boot면: "버전은요? ORM은 JPA / MyBatis 중 어느 것인가요? 인증 방식은? (JWT / Session)"
     → Django면: "DRF를 쓰나요? 인증은 JWT / Session?"
     → NestJS면: "TypeORM / Prisma 중 어느 것인가요?"
   - "데이터베이스는 무엇인가요? (PostgreSQL / MySQL / MongoDB 등)"
   프론트엔드:
   - "프론트엔드 프레임워크는 무엇인가요?"
     → React / Next.js면: "상태관리 라이브러리는? (Redux / Zustand / Jotai / 없음)"
                          "스타일링은? (Tailwind CSS / CSS Modules / styled-components)"
     → Vue면: "Vuex / Pinia 중 어느 것인가요?"
   인프라:
   - "어떤 클라우드를 쓰나요? (AWS / GCP / Azure / 없음)"
     → 있다면: "컨테이너를 쓰나요? (Docker / Kubernetes / ECS)"
   - 배포 단계(2-2)에서 CI/CD를 이미 수집했으면 재사용, 아니면:
     "CI/CD 파이프라인은 어떻게 구성되어 있나요? (GitHub Actions / Jenkins / 없음)"

4. 협업 규칙
   - "커밋 메시지에 특별한 규칙이 있나요? (예: Jira 티켓 번호 필수)"
   - "스프린트 주기가 있나요? (1주 / 2주 / 없음)"
   - PR 승인 수: 코드 리뷰 단계(2-2)에서 이미 수집했으면 재사용, 수집하지 않았으면 여기서 질문:
     "PR 병합에 몇 명의 승인이 필요한가요?"

5. 추가 제약
   - "팀만의 특별한 규칙이나 주의사항이 있나요?"
```

**team-process.md template** — fill in collected answers, leave comments for unknowns:

```yaml
# team-process.md
# Generated by solera-init on {date}. Edit freely to update team conventions.
# Skills read this file at the start of Goal and Epic level work.

service:
  name: "{서비스명}"
  description: "{한 줄 설명}"
  target_users:
    - "{페르소나1 요약 — 역할, 사용 맥락}"
    # - "{페르소나2}"  ← 추가 페르소나는 solera-write-identity로

workflow_gates:
  # Solera skills check these gates before entering each step.
  # Format: "{work-item-level}.{step}: "{condition}"
  # Populated automatically from kickoff interview answers.
  #
  # Gate levels:
  #   epic.use_case  — Epic 시작 전 (요구사항/기획 완료 여부)
  #   epic.concept   — Epic의 Concept 단계 진입 전 (디자인 산출물 확정 여부, Epic 범위)
  #   story.execute  — Story 개발 시작 직전 (해당 Story 단위 체크, 엔티티/설계 완료 여부)
  #   story.wrap_up  — Story 완료 전 (테스트/리뷰 기준 충족 여부)
  epic.use_case:  ""   # e.g. "요구사항 문서(PRD) 팀장 승인 완료"
  epic.concept:   ""   # e.g. "이 Epic의 Figma 디자인 링크 _epic.md에 첨부 확인"
  story.execute:  ""   # e.g. "ERD 팀 리뷰 통과 후 백엔드 개발 시작"
  story.wrap_up:  ""   # e.g. "단위 테스트 작성 및 코드 리뷰 2명 승인"

process_stages:
  # Team's actual development stages in order (from kickoff interview).
  stages: []
  # e.g.:
  # - name: "UX 설계"
  #   tool: "Figma"
  #   done_when: "핵심 플로우 와이어프레임 완성"
  #   gate: true        ← required before next stage starts
  # - name: "엔티티 설계"
  #   owner: "백엔드 개발자"
  #   done_when: "ERD 팀 리뷰 통과"
  #   gate: true
  # - name: "개발"
  #   gate: false

tech_stack:
  backend:
    framework: ""        # e.g. "Spring Boot 3.3"
    orm: ""              # e.g. "JPA / Hibernate"
    auth: ""             # e.g. "JWT (Access 30m / Refresh 7d)"
    database: ""         # e.g. "PostgreSQL 16"
  frontend:
    framework: ""        # e.g. "Next.js 14 (App Router)"
    state: ""            # e.g. "Zustand"
    styling: ""          # e.g. "Tailwind CSS v3"
  infra:
    cloud: ""            # e.g. "AWS"
    container: ""        # e.g. "Docker + ECS Fargate"
    ci_cd: ""            # e.g. "GitHub Actions"

conventions:
  pr_approvals: 1
  commit_prefix: ""      # e.g. "[JIRA-{id}]" — prepended to every commit
  sprint_cycle: ""       # e.g. "2주"
  design_tool: ""        # e.g. "Figma"

custom_rules:
  # - "API 변경 시 OpenAPI spec 업데이트 Action Item 필수"
  # - "모든 PR에 테스트 커버리지 80% 이상 유지"
```

## Completion Checklist

- [ ] Rule file installed at `.claude/rules/solera-workflow.md`
- [ ] Workspace folder structure created
- [ ] `progress.md` initialized
- [ ] Kickoff interview completed
- [ ] `{project_path}/workspace/team-process.md` created
- [ ] User informed of next step: "Run `solera-write-identity` to define your service identity and personas"
