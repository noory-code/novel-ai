# Self-Verification

> 스킬 정의 자동 검증 TC (Test Cases)

## TC001: 입력 섹션 존재
```yaml
type: section_exists
section: "## 입력"
```

## TC002: 산출물 섹션 존재
```yaml
type: section_exists
section: "## 산출물"
```

## TC003: 절차 섹션 존재
```yaml
type: section_exists
section: "## 절차"
```

## TC004: Completion Checklist 존재
```yaml
type: section_exists
section: "## Completion Checklist"
```

## TC005: metadata.triggers 2개 이상
```yaml
type: pattern_match
pattern: "triggers: \\[[^\\]]+,[^\\]]+\\]"
description: "triggers 배열에 최소 2개 이상의 키워드 필요"
```

## TC006: uses 필드 존재 (composite 타입)
```yaml
type: pattern_match
pattern: "uses: \\[.*\\]"
description: "composite 타입은 uses 필드 필수"
```

## TC007: AI-First 금지 표현 없음
```yaml
type: content_not_contains
forbidden_words: ["적절히", "필요시", "상황에 따라", "적절하게", "알아서", "경우에 따라"]
description: "AI-First 금지 표현 사용 불가"
```

## TC008: 절차 단계 존재
```yaml
type: content_contains
required_patterns: ["### Step 1", "### Step 2", "### Step 3", "### Step 4"]
description: "절차 섹션에 Step 1~4 존재"
```

## TC009: assets 파일 참조
```yaml
type: cross_reference
referenced_files: ["assets/handoff-template.md", "assets/self-verification.md"]
description: "참조된 assets 파일이 실제로 존재하는지 확인"
```
