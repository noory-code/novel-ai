# Template: Use Case

API/기능 사용 시나리오를 정의합니다.

## 템플릿

```markdown
# Use Case: [UC-ID] [제목]

> 마지막 업데이트: [YYYY-MM-DD]

## 개요

| 항목 | 내용 |
|------|------|
| **ID** | UC-[NNN] |
| **제목** | [Use Case 제목] |
| **Actor** | [사용자/시스템] |
| **Goal** | [달성하려는 목표] |

## 사전 조건 (Preconditions)

- [조건 1]
- [조건 2]

## 기본 흐름 (Basic Flow)

1. [Actor]가 [행동]
2. 시스템이 [응답]
3. [Actor]가 [행동]
4. 시스템이 [결과 반환]

## 대안 흐름 (Alternative Flow)

### [조건]인 경우

1. [대안 행동]
2. [대안 결과]

## 예외 흐름 (Exception Flow)

### [에러 조건]

1. 시스템이 [에러 메시지] 표시
2. [복구 방법]

## 사후 조건 (Postconditions)

- [결과 상태 1]
- [결과 상태 2]

## 필요 데이터

| 데이터 | Entity | 속성 |
|--------|--------|------|
| [데이터1] | [Entity명] | [속성 목록] |
| [데이터2] | [Entity명] | [속성 목록] |

## 관련 Journey

- [Journey명] Step [N]
```

## Use Case 목록 템플릿

```markdown
# Use Cases

> 마지막 업데이트: [YYYY-MM-DD]

## 목록

| ID | 제목 | Actor | 우선순위 | 상태 |
|----|------|-------|---------|------|
| UC-001 | [제목] | [Actor] | High | 정의됨 |
| UC-002 | [제목] | [Actor] | Medium | 정의됨 |

## Use Case 다이어그램

```mermaid
flowchart LR
    subgraph Actors
        A1[Actor1]
        A2[Actor2]
    end

    subgraph Use Cases
        UC1((UC-001<br/>제목))
        UC2((UC-002<br/>제목))
    end

    A1 --> UC1
    A1 --> UC2
    A2 --> UC2
```

## 상세

→ [UC-001.md](./UC-001.md)
→ [UC-002.md](./UC-002.md)
```

## 품질 기준

- [ ] Actor가 명확한가? (사람/시스템)
- [ ] Goal이 측정 가능한가?
- [ ] 사전 조건이 정의되어 있는가?
- [ ] 기본 흐름이 단계별로 정의되어 있는가?
- [ ] 예외 흐름이 정의되어 있는가?
- [ ] 필요 데이터가 Entity와 연결되어 있는가?

## 예시

### liquor-db - 주류 검색 Use Case

```markdown
# Use Case: UC-001 주류 검색

## 개요

| 항목 | 내용 |
|------|------|
| **ID** | UC-001 |
| **제목** | 주류 검색 |
| **Actor** | API 소비자 (서비스) |
| **Goal** | 조건에 맞는 주류 목록 조회 |

## 사전 조건

- API 인증 완료 (해당되는 경우)

## 기본 흐름

1. 소비자가 검색 조건(이름, 카테고리, 태그)과 함께 API 호출
2. 시스템이 조건에 맞는 주류 검색
3. 시스템이 주류 목록 반환 (페이징 적용)

## 대안 흐름

### 검색 결과가 없는 경우

1. 시스템이 빈 배열 반환
2. 메타 정보에 total: 0 포함

## 예외 흐름

### 잘못된 파라미터

1. 시스템이 400 Bad Request 반환
2. 에러 메시지에 잘못된 파라미터 명시

## 필요 데이터

| 데이터 | Entity | 속성 |
|--------|--------|------|
| 주류 정보 | Liquor | name, category, tags, abv |
| 브랜드 정보 | Brand | name |
```
