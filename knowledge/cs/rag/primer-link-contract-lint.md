# Primer Link Contract Lint

> 한 줄 요약: beginner primer와 browser/session bridge doc이 "어디로 돌아가야 하는지"와 "다음에 어디로 가야 하는지"를 같이 보여 주는지 확인하는 경량 QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Navigation Taxonomy](./navigation-taxonomy.md)
> - [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)
> - [Beginner Ladder Link Smoke Test](./beginner-ladder-link-smoke-test.md)
> - [Role-Cue Consistency Lint](./role-cue-consistency-lint.md)
>
> retrieval-anchor-keywords: primer link contract lint, beginner primer return path check, beginner primer next safe follow-up lint, beginner bridge link contract, browser session bridge lint, readme anchor return-path, safe next step lint, primer handoff qa, beginner primer link hygiene, primer return path and follow-up, bridge return path and follow-up, beginner entrypoint warning rule, 다음 읽기 섹션 lint, 다음에 이어서 읽기 cue, 다음 문서 라우팅 cue, safe next doc heading check, 안전한 handoff heading check

## 먼저 떠올릴 그림

beginner primer나 browser/session beginner bridge는 설명을 많이 붙이는 문서라기보다, 초심자가 길을 잃지 않게 잡아 주는 첫 계단에 가깝다.
그래서 링크 계약도 두 가지만 보면 된다.

| 질문 | beginner 기준에서 필요한 답 |
|---|---|
| 여기서 길을 잃으면 어디로 돌아가나? | 같은 category `README.md#...` anchor return-path |
| 여기까지 읽었으면 다음에 어디로 가나? | cue가 드러난 next safe follow-up link |

둘 중 하나가 빠지면 초심자 입장에서는 "문서는 읽었는데 다음 행동이 안 보이는 상태"가 된다.

## 무엇을 경고하나

이 lint는 `knowledge/cs/contents/**` 아래 beginner entrypoint 문서를 가볍게 훑어서 아래 둘을 본다.

1. 같은 category `README.md#...` anchor로 돌아가는 obvious return-path가 있는가
2. `다음 읽기`, `다음 문서 라우팅`, `safe next doc`, `안전한 handoff`, `detour에서 복귀하는 ... ladder`처럼 초심자 primer/bridge에서 실제로 많이 쓰는 섹션 제목 아래 local markdown follow-up이 보이는가

파일명이 `*primer*`, `*bridge*`, `*guide*`, `*shortcut*` 중 하나를 포함하고, 문서 앞부분에 `난이도: 🟢 Beginner` 같은 marker가 있으며, 내용이 browser/session/login/cookie/redirect 계열 beginner entrypoint일 때만 검사한다.

## 왜 기존 check와 분리했나

- [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)는 category 문서가 **돌아갈 path**를 잃었는지 본다.
- 이 lint는 beginner primer/bridge가 **돌아갈 path + 다음 한 걸음**을 동시에 보여 주는지 본다.
- [Beginner Ladder Link Smoke Test](./beginner-ladder-link-smoke-test.md)는 루트 README/로드맵/대표 primer 정합성을 본다.
- 이번 규칙은 개별 beginner entrypoint가 혼자 고립되지 않는지 보는 더 작은 문서 단위 경고다.

즉 범위는 작지만, 초심자 입장에서는 가장 먼저 체감되는 링크 품질을 직접 본다.

## 실행

보통은 touched path만 넘겨서 돌린다.

```bash
python docs/primer_link_contract_lint.py \
  knowledge/cs/contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md
```

category 단위로 볼 수도 있다.

```bash
python docs/primer_link_contract_lint.py knowledge/cs/contents/security
```

path를 주지 않으면 기본값으로 `knowledge/cs/contents` 전체를 스캔한다.

## 출력 읽는 법

```text
knowledge/cs/contents/example/example-primer.md
  warning: missing same-category README anchor return-path such as `./README.md#...`.
  warning: missing obvious next safe follow-up link under a `다음 읽기` / `다음 문서 라우팅` / `safe next doc` / `안전한 handoff` style section.
```

- 첫 warning은 "돌아갈 navigator가 안 보인다"는 뜻이다.
- 둘째 warning은 "다음 문서는 있을 수 있어도, beginner가 즉시 읽을 수 있는 safe next step cue가 안 보인다"는 뜻이다.

한쪽만 빠진 경우에는 그 warning만 나온다.

## 고치는 가장 작은 순서

1. `관련 문서`나 `다음 문서` 섹션에 같은 category `README.md#...` anchor return-path를 넣는다.
2. `다음 읽기`, `다음 문서 라우팅`, `safe next doc`, `안전한 handoff` 같은 섹션 제목 아래에 local markdown follow-up을 하나 둔다.
3. deep dive만 바로 던지기보다, 가능하면 `primer bridge`나 좁은 다음 단계부터 건다.
4. 수정 후 touched path만 다시 lint한다.

## 흔한 혼동

- 링크가 많으면 계약이 채워진 것이 아니다. 초심자에게는 "돌아가기 1개 + 다음 한 걸음 1개"가 더 중요하다.
- `README.md` 파일 링크만 있고 anchor가 없으면 category 안에서 어디로 복귀해야 하는지 흐릴 수 있다.
- 문서 서두의 `다음에 읽는 beginner bridge` 같은 설명 문장은 후속 섹션 제목이 아니다. 링크 cue는 초심자가 스캔 가능한 섹션 제목으로 드러나야 한다.
- browser/session bridge는 deep dive 링크를 많이 붙이는 것보다, `README ladder return-path + safe next doc` 두 축이 먼저 눈에 보여야 한다.

## 한 줄 정리

beginner primer와 browser/session bridge는 내용보다 먼저 동선이 보여야 하므로, `README anchor return-path + next safe follow-up`을 한 세트로 본다.
