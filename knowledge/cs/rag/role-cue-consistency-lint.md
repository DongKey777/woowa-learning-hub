# Role-Cue Consistency Lint

> 한 줄 요약: beginner/junior 독자를 위한 row가 `[primer] -> [primer bridge]` handoff를 잃고 바로 `[deep dive]`, `[playbook]`, `[recovery]`로 점프하는지 빠르게 잡는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Navigation Taxonomy](./navigation-taxonomy.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
> - [Query Playbook](./query-playbook.md)
> - [Auth Ladder Alias Drift Lint](./auth-ladder-alias-drift-lint.md)
>
> retrieval-anchor-keywords: role-cue consistency lint, beginner row lint, primer primer bridge handoff lint, beginner-safe handoff qa, primer bridge missing row, beginner route deep dive jump, role cue drift check, survey primer deep dive playbook recovery label check, starter row qa, safe next step lint, primer handoff consistency, beginner entrypoint safety, junior route handoff lint, first-step primer missing, second-step handoff missing, direct deep dive jump, role badge parity, primer bridge anchor cue

## 먼저 잡는 mental model

beginner row는 "문서를 많이 거는 곳"이 아니라 "다음 한 걸음을 안전하게 고르는 곳"이다.

| 역할 | beginner row에서 맡는 일 | 여기서 바로 끝내면 안 되는 것 |
|---|---|---|
| `survey` | 큰 그림과 학습 순서를 보여 준다 | symptom 해결 starter처럼 쓰지 않는다 |
| `primer` | 첫 진입 mental model을 만든다 | deep dive 대체물처럼 너무 많은 예외를 싣지 않는다 |
| `primer bridge` | primer 언어를 다음 symptom/deep-dive 언어로 번역한다 | first-step primer 없이 단독 starter가 되지 않는다 |
| `deep dive` | 경계, internals, trade-off를 판다 | beginner row의 첫 링크가 되지 않는다 |
| `playbook` | live debugging 순서를 준다 | 개념 축이 없는 beginner 첫 handoff가 되지 않는다 |
| `recovery` | outage/degradation 복구를 다룬다 | primer/bridge 없이 첫 안전 경로처럼 보이면 안 된다 |

핵심은 간단하다.

- beginner row 첫 링크는 보통 `[primer]`여야 한다.
- 두 번째 안전 handoff는 보통 `[primer bridge]`여야 한다.
- `[deep dive]`, `[playbook]`, `[recovery]`는 그다음 선택지여야 한다.

## 언제 돌리나

- `README`, topic map, bridge map, query playbook에서 beginner/junior shortcut row를 새로 추가했을 때
- beginner row의 링크 순서나 label badge를 손봤을 때
- primer 문서는 남아 있는데 row 문구에서 `[primer bridge]` cue가 사라졌을 때
- symptom-first row가 편하다는 이유로 spring/system-design deep dive를 첫 링크로 올렸을 때

## 무엇을 실패로 보나

| 실패 패턴 | 왜 beginner에게 위험한가 | 최소 수리 |
|---|---|---|
| beginner row에 `[primer]`가 없다 | 첫 문서가 catalog/deep dive로 바뀌어 cold-start가 깨진다 | 첫 링크를 `[primer]` entrypoint로 되돌린다 |
| `[primer]` 다음에 `[primer bridge]` 없이 바로 `[deep dive]`가 온다 | 용어 handoff 없이 internals로 떨어진다 | `[primer bridge]`를 중간 단계로 복구한다 |
| row 안에서 `survey`, `playbook`, `recovery`가 같은 수준으로 섞인다 | "큰 그림", "실전 대응", "복구"가 starter처럼 오인된다 | row 목적을 하나로 줄이고 later 문서에 cue를 다시 붙인다 |
| 링크는 있지만 badge가 없다 | reader와 retrieval이 역할 전환 시점을 놓친다 | 각 링크 앞에 `[primer]`, `[primer bridge]`, `[deep dive]`를 다시 적는다 |
| `primer bridge`가 사실상 deep dive 문서를 가리킨다 | handoff 문서가 아니라 난이도 점프가 된다 | handoff용 문서나 README subsection anchor를 먼저 둔다 |

## 빠른 체크리스트

beginner row 하나를 볼 때 아래 다섯 가지만 본다.

1. 이 row가 정말 beginner/junior starter인가.
2. 첫 링크가 `[primer]` 또는 동급 entrypoint인가.
3. 두 번째 링크가 `[primer bridge]` 또는 handoff anchor인가.
4. 세 번째부터만 `[deep dive]`, `[playbook]`, `[recovery]`, `[system design]`로 내려가는가.
5. row 문구와 `retrieval-anchor-keywords`에 `beginner route`, `first-step primer`, `primer bridge`, `safe next step` 같은 cue가 남아 있는가.

## 이 lint가 바로 flag해야 하는 row

아래 셋 중 하나라도 맞으면 "handoff 누락"으로 바로 잡는다.

| flag 조건 | beginner 관점에서 보이는 문제 | 바로 고칠 기본형 |
|---|---|---|
| 첫 starter link가 `[deep dive]`, `[playbook]`, `[recovery]`, `[system design]`다 | 첫 단추부터 난이도 점프가 난다 | 첫 링크를 `[primer]`로 내리고 later link만 남긴다 |
| `[primer]`는 있는데 다음 링크 badge가 없거나 bare link다 | primer 다음 handoff가 숨어서 reader가 다음 안전 경로를 못 고른다 | 두 번째 링크를 `[primer bridge]`로 명시한다 |
| row 문구는 beginner/junior인데 metadata anchor에는 `primer bridge`, `safe next step`, `first-step primer` cue가 없다 | retrieval이 row를 찾아도 handoff row로 분류하지 못한다 | row 문구와 `retrieval-anchor-keywords`에 beginner handoff alias를 같이 보강한다 |

짧게 말하면 beginner row는 "첫 링크가 무엇인가"만이 아니라 "두 번째 링크가 handoff로 읽히는가"까지 보여야 한다.

## 수동 lint 순서

먼저 beginner row 후보를 찾는다.

```bash
rg -n "beginner|junior|입문|첫 단계|first-step|safe next step|primer bridge" \
  knowledge/cs/rag \
  knowledge/cs/README.md \
  knowledge/cs/contents/*/README.md
```

그다음 row 안 role cue를 본다.

```bash
rg -n "\\[primer\\]|\\[primer bridge\\]|\\[deep dive\\]|\\[playbook\\]|\\[recovery\\]|\\[survey\\]" \
  knowledge/cs/rag \
  knowledge/cs/README.md \
  knowledge/cs/contents/*/README.md
```

둘을 같이 보면서 beginner row가 아래 순서를 지키는지 확인한다.

```text
[primer] -> [primer bridge] -> [deep dive] / [playbook] / [recovery]
```

role cue가 보이는데도 handoff가 흐리면 metadata cue까지 같이 확인한다.

```bash
rg -n "retrieval-anchor-keywords: .*?(beginner route|first-step primer|primer bridge|safe next step)" \
  knowledge/cs/rag \
  knowledge/cs/README.md \
  knowledge/cs/contents/*/README.md
```

찾은 row는 아래처럼 메모하면 된다.

```text
flag: beginner row missing clear handoff
- row: <file or section>
- missing: first-step primer | primer bridge cue | role badge parity
- repair: [primer] -> [primer bridge] -> [deep dive]
```

## Before / After 예시

```markdown
<!-- before -->
- `cookie 있는데 다시 로그인`이면 [deep dive] Spring Security `RequestCache` / `SavedRequest` Boundaries부터 본다.
```

```markdown
<!-- after -->
- `cookie 있는데 다시 로그인`이면
  [primer] Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문 ->
  [primer bridge] Browser `401` vs `302` Login Redirect Guide ->
  [deep dive] Spring Security `RequestCache` / `SavedRequest` Boundaries
```

```markdown
<!-- before -->
- `revoke lag`이면
  [primer] Role Change and Session Freshness Basics ->
  Claim Freshness After Permission Changes ->
  [deep dive] Revocation Propagation Lag
```

```markdown
<!-- after -->
- `revoke lag`이면
  [primer] Role Change and Session Freshness Basics ->
  [primer bridge] Claim Freshness After Permission Changes ->
  [deep dive] Revocation Propagation Lag
```

## 흔한 혼동

- `survey`는 큰 그림이다. beginner symptom row의 두 번째 링크 자리를 대신하지 않는다.
- `[primer bridge]`는 "짧은 deep dive"가 아니라 "다음 문서를 읽을 언어를 맞추는 handoff"다.
- `playbook`이나 `recovery`가 더 실용적으로 보여도, 기초 축이 없는 beginner row에서는 첫 링크가 되면 안 된다.
- 한 row 안에서 역할이 바뀌면 later link가 앞 badge를 상속한다고 가정하지 말고 cue를 다시 붙인다.

## 관련 문서에 어떻게 연결하나

- 역할 정의 자체가 흔들리면 [Navigation Taxonomy](./navigation-taxonomy.md)에서 role boundary를 먼저 맞춘다.
- auth/session beginner ladder alias가 같이 흔들리면 [Auth Ladder Alias Drift Lint](./auth-ladder-alias-drift-lint.md)를 이어서 본다.
- row label은 맞는데 검색어 회수가 약하면 [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)에서 `beginner route`, `first-step primer`, `primer bridge`, symptom alias를 함께 보강한다.
- beginner route가 README row와 bridge map에서 서로 다른 이름으로 갈라졌다면 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)과 [Query Playbook](./query-playbook.md)까지 같이 봐서 same ladder를 다시 맞춘다.

## 한 줄 정리

beginner row는 `[primer] -> [primer bridge]` handoff가 보여야 안전하고, 그 cue가 사라진 row는 deep-dive 품질 문제가 아니라 entrypoint 안전 문제로 먼저 잡아야 한다.
