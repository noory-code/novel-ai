---
kind: category
canvas: services
field_count: 2
status: draft   # draft → reviewing → done
---

# category — 카테고리

> 서비스 캔버스의 최상위 그룹핑 (인증/온보딩/프로필 …). 서비스를 담는
> 컨테이너. 정본: `viewer/src/domain/Category.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `theme` | 이 카테고리의 주제/성격 | 그룹의 정체성을 한 줄로 | ❓ label 과 뭐가 다른가? sim 에서 채워지나 |
| `body` | 자유 서술 | 산문 보강 | ❓ category 는 그냥 묶음인데 body 가 필요한가 |

## 2. 핵심 질문

- category 는 **순수 그룹핑 컨테이너**(서비스 N개를 담음). 컨테이너에
  `theme`+`body` 라는 내용 필드 2개가 정말 필요한가? — label 만으로 충분할
  수 있음. **2개 필드 다 의심 대상.**
- theme 이 살아남는다면 label 과의 역할 분담을 명문화해야 함
  (label=이름, theme=성격?).

## 3. 작업 정의

- [ ] sim 7개 category 의 theme/body 충전율 확인
- [ ] theme/body 제거 → category 를 필드 없는 순수 컨테이너로 둘지 결정

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 2: theme/body). |
