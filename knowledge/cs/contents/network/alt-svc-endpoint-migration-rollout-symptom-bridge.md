# Alt-Svc Endpoint Migration Rollout Symptom Bridge

> 한 줄 요약: H3 `Alt-Svc` endpoint를 옮기는 rollout에서는 일부 브라우저가 예전 힌트를 잠깐 들고 있어서 `421 -> 재시도 성공`, `h3 -> h2` 같은 짧은 흔들림이 보일 수 있고, 이것은 대개 배포 직후의 정상적인 수렴 구간이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [421 Retry Path Mini Guide: Fresh H3 Connection vs H2 Fallback](./421-retry-path-mini-guide-fresh-h3-vs-h2-fallback.md)
- [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md)
- [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)
- [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)
- [HTTP Cache Reuse vs Connection Reuse vs Session Persistence Primer](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [Feature Flags, Rollout Dependency Management](../software-engineering/feature-flags-rollout-dependency-management.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: alt-svc endpoint migration, h3 endpoint moved symptoms, alt-svc rollout symptom bridge, h3 421 after endpoint move, same url 421 then 200, h3 to h2 temporary fallback, why protocol changed after rollout, 처음 보는 alt-svc rollout, stale client retry after deploy, browser cache vs alt-svc confusion, repeat visitor first request issue, what happens when alt-svc moves

## 핵심 개념

`Alt-Svc` endpoint migration은 "브라우저가 예전에 배운 H3 목적지"를 운영팀이 다른 edge나 다른 authority로 옮기는 상황이다.

초급자는 아래 한 줄로 먼저 기억하면 된다.

- 서버는 이미 새 endpoint를 쓰고 있어도
- 일부 브라우저는 잠깐 예전 `Alt-Svc` 메모를 먼저 믿는다
- 그래서 첫 시도만 `421`, timeout, 또는 `h3 -> h2` 전환이 보일 수 있다
- 그 뒤 새 힌트를 배우거나 fresh path로 재시도하면서 수렴한다

즉 rollout 직후의 짧은 흔들림은 "전부 장애"가 아니라 **클라이언트 메모와 서버 현실이 잠깐 어긋난 상태**일 수 있다.

## 먼저 끊어 읽을 3가지

이 문서를 처음 읽을 때는 아래 셋을 섞지 않으면 훨씬 쉽다.

| 헷갈리는 대상 | 이 문서에서 먼저 붙일 이름 |
|---|---|
| 예전 `Alt-Svc` endpoint를 계속 기억하는 현상 | stale client hint |
| 같은 URL이 `421` 뒤 다시 뜨는 현상 | 브라우저 recovery 재시도 |
| `h3 -> h2`가 잠깐 보이는 현상 | 임시 fallback 가능성 |

즉 "`배포 직후 일부 사용자 첫 요청만 흔들린다`"는 말은 종종 **client memory 차이**를 뜻한다.

## 한눈에 보기

| rollout 직후 보이는 장면 | 초급자 1차 해석 | 흔한 다음 모습 |
|---|---|---|
| 같은 URL이 `421` 뒤 바로 `200` | 예전 H3 endpoint를 먼저 썼다가 교정됨 | 새 `h3` connection 또는 `h2` fallback |
| 어제까지 `h3`였는데 오늘 첫 요청만 `h2` | stale hint 시도 뒤 보수적으로 내려감 | 다음 응답에서 새 `Alt-Svc`를 배우고 다시 `h3` 수렴 가능 |
| 일부 사용자만 증상을 말함 | warm `Alt-Svc`를 갖고 있던 repeat visitor 쪽 영향 | 신규 사용자나 clean client는 바로 새 경로로 갈 수 있음 |
| `Protocol`이 `h3 -> h3`인데 `Connection ID`가 바뀜 | H3 자체는 유지, 예전 connection/path만 버림 | fresh H3 retry |
| `Protocol`이 `h3 -> h2`로 바뀜 | H3 전체 제거가 아니라 임시 fallback일 수 있음 | 새 힌트 학습 뒤 다시 `h3` 가능 |

이 표의 핵심은 "`endpoint 이동` 직후엔 모든 사용자가 똑같이 실패하지 않는다"는 점이다.

## 상세 분해

### 1. 왜 일부 클라이언트만 먼저 흔들리나

브라우저마다 갖고 있는 정보가 다르기 때문이다.

- 신규 사용자: 예전 `Alt-Svc` 메모가 없어서 곧바로 새 현실을 배울 수 있다
- 반복 방문 사용자: 어제 배운 `Alt-Svc` endpoint를 아직 기억할 수 있다
- 이미 열려 있던 connection이 있는 사용자: 기존 H2/H3 재사용 상태까지 섞여 보일 수 있다

그래서 rollout 증상은 "전체 100% 실패"보다 **일부 repeat visitor의 첫 몇 요청만 흔들리는 형태**로 더 자주 나타난다.

### 2. transient retry는 왜 생기나

브라우저는 첫 시도가 틀렸다고 해서 바로 URL 자체를 버리지 않는다.

보통은 이렇게 움직인다.

1. 예전 `Alt-Svc` endpoint로 H3를 먼저 시도한다.
2. `421` 또는 연결 실패로 "방금 그 길은 아니다"를 배운다.
3. 새 H3 connection, 다른 endpoint, 또는 `h2` 기본 경로로 다시 간다.
4. 성공 응답을 받으면 새 힌트로 점점 수렴한다.

그래서 DevTools에는 같은 URL이 두 줄 보이거나, 첫 줄과 둘째 줄의 protocol이 다르게 보일 수 있다.

### 3. protocol shift는 어떤 뜻인가

`h3 -> h2`가 보였다고 항상 "HTTP/3 배포가 완전히 망했다"는 뜻은 아니다.

| 보이는 shift | 더 안전한 beginner 해석 |
|---|---|
| `h3 -> h3` + connection 변경 | endpoint는 여전히 H3로 쓸 만하고, 방금 그 path만 틀렸을 수 있다 |
| `h3 -> h2` | 브라우저가 이번 한 번은 H2를 더 안전한 복구 경로로 골랐을 수 있다 |
| 첫 요청부터 계속 `h2` | stale hint가 없거나, 새 힌트를 아직 배우지 않았거나, fallback 상태일 수 있다 |

여기서 중요한 점은 protocol shift가 **수렴 과정의 흔적**일 수 있다는 것이다.

## 흔한 오해와 함정

- "`421`이 보였으니 배포가 완전히 깨졌다"라고 단정하면 안 된다. 첫 실패 뒤 즉시 성공하는지 먼저 본다.
- "`h3 -> h2`가 보였으니 UDP 차단이다"라고 바로 단정하면 안 된다. endpoint migration 뒤 임시 fallback일 수도 있다.
- "사용자 몇 명만 느리다고 하니 서버 문제가 아니다"라고 넘기면 안 된다. warm `Alt-Svc`를 가진 클라이언트 집단만 흔들릴 수 있다.
- "`Alt-Svc`를 새 값으로 바꿨으니 즉시 전 세계가 동시에 수렴한다"라고 기대하면 안 된다. 각 브라우저의 cache 수명과 기존 connection 상태가 다르다.
- "브라우저에서 disable cache를 켰는데도 남았으니 cache 이슈가 아니다"라고 말하면 안 된다. DevTools의 일반 cache 토글은 Alt-Svc 힌트와 같은 층위가 아니다.

초급자용 안전 규칙:

- rollout 직후에는 `Status`, `Protocol`, `Connection ID`를 같이 본다
- 증상이 일부 사용자에게만 보이면 stale client hint 가능성을 먼저 남겨 둔다
- 같은 URL의 짧은 재시도 흔적은 중복 호출보다 브라우저 recovery일 수 있다

## 실무에서 쓰는 모습

가장 흔한 배포 장면을 짧게 그리면 아래와 같다.

```text
1. 어제: Alt-Svc: h3="edge-old.example.net:443"; ma=86400
2. 오늘 배포: edge-old 대신 edge-new가 새 H3 endpoint가 됨
3. repeat visitor A: 아직 edge-old 메모를 들고 첫 요청을 보냄
4. edge-old 또는 중간 edge가 421 또는 연결 실패로 교정
5. 브라우저가 edge-new 쪽 fresh path 또는 h2 기본 경로로 재시도
6. 응답에서 새 Alt-Svc를 배우며 이후 요청이 점점 안정화
```

주니어가 incident 메모에 남기기 좋은 요약은 이 정도면 충분하다.

| 관찰 | 메모 문장 예시 |
|---|---|
| `421 (h3)` 뒤 `200 (h3)` | "예전 Alt-Svc endpoint 재사용 후 fresh H3 connection으로 회복" |
| `421 (h3)` 뒤 `200 (h2)` | "예전 H3 path 교정 후 임시 H2 fallback으로 회복" |
| 일부 사용자 첫 요청만 느림 | "warm Alt-Svc client 집단에서 rollout 수렴 구간 의심" |

또 한 가지:

- 서버가 `Alt-Svc: clear` 또는 짧은 `ma` 전략을 같이 쓰면 수렴이 더 빨라질 수 있다
- 반대로 긴 `ma`를 유지한 채 endpoint를 옮기면 repeat visitor 쪽 transient symptom이 더 오래 남을 수 있다

## 더 깊이 가려면

- `Alt-Svc` 메모가 어떻게 warm/stale가 되는지부터 다시 보고 싶으면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- `421` 뒤 새 H3와 H2 fallback이 어떻게 갈리는지 더 짧게 보고 싶으면 [421 Retry Path Mini Guide: Fresh H3 Connection vs H2 Fallback](./421-retry-path-mini-guide-fresh-h3-vs-h2-fallback.md)
- stale hint recovery 장면 자체를 더 자세히 보고 싶으면 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- DNS `HTTPS` RR와 `Alt-Svc` 시간축이 어떻게 어긋나는지 보려면 [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md)
- QUIC의 진짜 connection migration과 이 문서의 "Alt-Svc endpoint migration"을 구분하려면 [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)
- browser cache 토글과 Alt-Svc/DNS cache가 왜 다른지 먼저 정리하려면 [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)

## 면접/시니어 질문 미리보기

| 질문 | 핵심 답변 |
|---|---|
| endpoint migration 때 왜 일부 사용자만 `421`을 보나요? | 예전 `Alt-Svc`를 기억한 repeat visitor와 그렇지 않은 사용자의 클라이언트 상태가 다르기 때문이다 |
| 왜 `h3 -> h2`가 잠깐 보일 수 있나요? | 브라우저가 stale path를 교정한 뒤 이번 한 번은 더 보수적인 복구 경로를 선택할 수 있기 때문이다 |
| rollout 안정화를 빠르게 보려면 무엇을 함께 보나요? | `Status`, `Protocol`, `Connection ID`, 그리고 새 응답의 `Alt-Svc` 재광고 여부를 같이 본다 |

## 한 줄 정리

H3 `Alt-Svc` endpoint를 옮기는 rollout에서는 일부 브라우저가 예전 힌트로 첫 시도를 잠깐 잘못할 수 있어서 `421 -> 재시도 성공`이나 `h3 -> h2` 같은 transient symptom이 보이지만, 새 힌트를 다시 배우면서 점점 정상 경로로 수렴한다.
