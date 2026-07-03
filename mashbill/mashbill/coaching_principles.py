"""Design-quality discriminators the coach consults when judging content.

D-2026-07-03-O/P: the coach's evaluation knowledge is DISTILLED PRINCIPLES,
not RAG — and it rides here as an MCP tool payload, not in the per-turn
prompt (word budget). CANON lives in the workspace repo
(``noory-workspace/docs/concepts/design-principles.md``, Korean); this is the
runtime copy the engine ships — sync canon → here when the canon changes.
Korean on purpose: the coach quotes these discriminator questions verbatim.
"""

from __future__ import annotations

_MISSION = """미션 판별 기준 — 약하면 판별 질문을 그대로 던져라:
- 방향이 아니라 변화: "이게 이뤄진 아침, 세상 누가 뭘 다르게 하고 있나?" ("~을 제공한다"는
  기능 서술이지 미션이 아니다)
- 지속가능한 문제: "10년 뒤에도 이 문제는 새로 태어나나?" (한 번 풀리면 끝 = 프로젝트)
- 당신이어야 하는 이유: "경쟁사가 이 문장을 그대로 걸어도 어색하지 않다면 다시."
- 체감 상태로 내려갔나: "이 미션이 3인칭 명사인가, 한 사람의 체감 상태인가?"
  (최강 미션은 추상명사가 아니라 한 사람의 체감으로 쓴다 — "쿠팡 없이 어떻게 살았을까?")
강한 예: "어렵고 불편하고 먼 금융이 아닌, 누구에게나 쉽고 상식적인 금융"(before→after 내장).
약한 예: "몇 번의 탭으로 송금·투자·결제를 한 앱에서"(기능 서술) · "모두를 위해 세상을 더
좋게"(누구나 걸 수 있는 슬로건)."""

_VALUES = """핵심 가치 판별 기준:
- 대가 없는 가치는 장식: "이걸 지켜서 최근에 손해 본 순간은?"
- 영역이 갈라져 있나: 고객 대우·품질·속도·돈vs원칙·일하는 방식에 분산돼야 성숙한 체계.
  전부 고객 계열이면 아직 미션의 메아리.
- 행동 문장인가: "신입이 이 문장만 보고 내일 다르게 행동할 수 있나?" (명사 하나는 단어지
  가치가 아니다)
- 반대쌍 긴장이 있나: "대놓고 반대인 두 가치가 있나?" (성숙한 체계는 '빠르게'와 '적당히는
  적당하지 않다'처럼 서로 당기는 쌍을 의도적으로 건다)
강한 예: "고객 와우"(대가=마진) · "소프트웨어가 사람을 바보로 느끼게 해선 안 된다"(대가=
출시일) · "멀리 본다"(대가=즉시 매출) · "드림팀"(대가=고용안정).
약한 예: "정직 — 늘 정직하게"(대가 없음·명사) · "혁신 — 끊임없이"(포기하는 것 없음)."""

_SERVICES = """서비스 지도 판별 기준:
- 교환 단위: "이 면의 양쪽에 서로 다른 당사자가 서 있나?" (내부 공정 — 매칭·정산·피킹 —
  을 서비스로 세우면 지도가 아니라 조직도)
- 미션의 도달 범위만큼: 실제 제품은 3~6개 교환면. "미션이 닿는데 아직 지도에 없는 교환은?"
- 낯선 당사자 거래엔 신뢰 제조면: "모르는 둘이 거래하나? 그럼 신뢰를 만드는 면(검증·보증·
  분쟁해결↔신고·리뷰)이 지도에 있나?" (그런 제품은 예외 없이 이 면을 따로 세운다)
틀린 분해의 표본: "검색→장바구니→결제→피킹→배송"을 5개 서비스로 — 전부 한 교환면의 내부
공정. 피킹·배차엔 거래 상대가 없다."""

_FEATURES = """기능 판별 기준:
- 사람의 동작으로 서술되나: "이 문장의 주어가 사람인가?" (저장·조회·렌더링이 등장하면
  구현으로 추락한 것)
- 행복 경로가 끝까지: 분기·예외 전에 처음-끝이 한 줄로 걸어져야 한다.
- 승격 신호: 기능 하나가 여러 당사자의 교환을 품기 시작하면 서비스 후보."""

_AREAS: dict[str, str] = {
    "mission": _MISSION,
    "values": _VALUES,
    "services": _SERVICES,
    "features": _FEATURES,
}


def get_principles(area: str | None = None) -> str:
    """Return the discriminator principles for ``area``, or all areas joined.

    ``area``: mission | values | services | features | None (= everything).
    Raises ``ValueError`` on an unknown area so a typo can't silently return
    nothing.
    """
    if area is None:
        return "\n\n".join(_AREAS[k] for k in ("mission", "values", "services", "features"))
    if area not in _AREAS:
        raise ValueError(f"unknown area {area!r}; pick one of {sorted(_AREAS)} or omit")
    return _AREAS[area]
