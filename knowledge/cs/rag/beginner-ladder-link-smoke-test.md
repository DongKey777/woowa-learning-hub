# Beginner Ladder Link Smoke Test

> 한 줄 요약: 루트 `README`, `JUNIOR-BACKEND-ROADMAP`, 우테코 primer가 같은 beginner-safe ladder를 가리키는지 정적으로 확인하는 경량 QA check다.

> retrieval-anchor-keywords: beginner ladder link smoke test, beginner safe next step lint, woowacourse ladder drift check, root readme roadmap primer link parity, safe-next-step link drift, beginner ladder smoke test, woowacourse backend beginner ladder lint, beginner bridge qa, primer roadmap root alignment

## 왜 필요한가

초심자 문서에서는 첫 링크 한 번이 다음 학습 동선을 거의 결정한다.
루트 `README`, 로드맵, 우테코 primer가 서로 다른 다음 문서를 가리키기 시작하면, beginner 입장에서는 "같은 사다리"처럼 보여도 실제로는 다른 길을 타게 된다.

이 smoke test는 그 드리프트를 아주 작게 막는 용도다.
핵심은 "deep dive가 많으냐"가 아니라, **primer -> safe next step -> 다음 navigator** 순서가 세 문서에서 계속 같은지 확인하는 데 있다.

## 점검 범위

| 문서 | 확인하는 것 |
|---|---|
| `knowledge/cs/README.md` | `Woowacourse Backend Beginner Ladder` 섹션의 starter/follow-up 링크와 roadmap/primer handoff |
| `knowledge/cs/JUNIOR-BACKEND-ROADMAP.md` | `우테코 백엔드 안전 사다리 동기화` 섹션의 primer/follow-up 링크 |
| `knowledge/cs/contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md` | 루트/로드맵 reverse-link와 primer ladder 링크 |

## 실행

```bash
python3 knowledge/cs/rag/check_beginner_ladder_links.py
```

성공하면 root README, 로드맵, primer의 beginner-safe next-step 링크가 서로 어긋나지 않았다는 뜻이다.

## 실패를 어떻게 읽을까

- `missing link`: 문서에서 아예 빠진 handoff다.
- `target file missing`: 링크는 남아 있지만 실제 문서가 없거나 path가 바뀌었다.
- `anchor missing`: `README.md#...` 같은 reverse-link가 stale slug를 가리킨다.

초심자용 사다리에서는 이 세 가지가 모두 "첫 다음 한 걸음이 흔들린다"는 같은 문제로 이어진다.

## 같이 보면 좋은 문서

- [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)
- [Role-Cue Consistency Lint](./role-cue-consistency-lint.md)
- [Auth Ladder Alias Drift Lint](./auth-ladder-alias-drift-lint.md)
