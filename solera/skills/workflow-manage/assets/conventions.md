# Conventions

프로젝트 공통 규칙. 모든 스킬이 이 파일을 참조한다.

## 일감 계층

```
Identity > Initiative > Phase > Goal > Epic > Story > Action Item
           (연간)      (분기)  (목표) (작업) (일간) (커밋)
```

| 역할 | 계층 | 하는 일 |
|------|------|---------|
| **사람** | Identity~Phase | 전략 결정, 승인 |
| **AI** | Goal~Action Item | 분해, 문서 생성, 구현 |

## Git 브랜치

| 계층 | 브랜치명 | 분기 원점 |
|------|----------|----------|
| **Epic** | `epic-[name]` | 부모 브랜치 |
| **Story** | `epic-[name]/story-[ID]-[name]` | Epic 브랜치 |

> Action Item = 커밋만 (브랜치 없음)

## 폴더 구조

```
[project]/
├── progress.md
└── workspace/
    ├── identity/
    ├── initiative/[year]/
    ├── phase/[phase]/
    │   └── goals/[goal]/
    │       ├── _goal.md
    │       ├── artifacts/
    │       └── epics/
    └── catalog/
```

## 상태값

| 아이콘 | 상태 | 설명 |
|--------|------|------|
| ⏳ | 대기 | 작업 전 |
| 🔄 | 진행 | 작업 중 |
| ✅ | 완료 | 작업 완료 |
| ⏸️ | 보류 | 일시 중단 |
