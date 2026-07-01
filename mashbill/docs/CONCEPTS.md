# Novel Concepts → 정본은 root

> **개념 정본은 root** (`D-2026-06-28-B`). kind·캔버스의 *의미*는 두 제품(오픈 엔진·상용
> 앱)이 공유하는 모델이라 root `docs/`가 단일 출처다. 이 파일은 더 이상 본문을 들지 않는다.

| 무엇 | 정본 위치 |
|---|---|
| kind별 *의미* (service/feature/actor/entity/… + Symbol 패턴 + 설계 원칙) | [`docs/concepts/kinds.md`](../../../docs/concepts/kinds.md) |
| 캔버스 5종의 *의미* (각자 강제하는 질문) | [`docs/concepts/canvases.md`](../../../docs/concepts/canvases.md) |
| AI 코치 모델 | [`docs/concepts/ai-collaboration.md`](../../../docs/concepts/ai-collaboration.md) |

엔진 코드-near 쪽:

- **kind별 와이어 필드(JSON 스키마)** = root [`docs/specs/kinds-fields.md`](../../../docs/specs/kinds-fields.md)
  (설계 계약) + 코드 SSOT `viewer/src/domain/{Kind}.ts` + `test_schema_parity.py`(드리프트 가드).
- **캔버스별 *동작* 스펙**(렌더·드릴·인스펙터·레이아웃) = [`SPEC.md`](./SPEC.md).
- **바운디드 컨텍스트 / 코드 거처** = [`DOMAIN.md`](./DOMAIN.md).

> 옛 본문(706줄, v0.12 시점 + 마라톤 전 일부 잔존)은 root concepts 가 흡수했다. 그 안의 폐기분
> (삭제된 `IDENTITY.md` 참조 · `actor_ref` `gives`/`receives` 모델)은 root 최신 모델이 *폐기*로
> 정합했으니, 정의가 갈리면 root를 따른다.
