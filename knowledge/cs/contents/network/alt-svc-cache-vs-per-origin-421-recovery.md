# Alt-Svc Cache vs Per-Origin 421 Recovery

> 한 줄 요약: `Alt-Svc` cache가 아직 warm해도 특정 origin의 H3 reuse만 `421`로 교정될 수 있으며, 브라우저는 그 origin에 대해 새 H3로 다시 시도할지, 더 보수적으로 H2로 돌아갈지를 따로 판단한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)
- [HTTP Cache Reuse vs Connection Reuse vs Session Persistence Primer](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [network 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: alt-svc cache vs 421 recovery, warm alt-svc but 421, per-origin 421 recovery, why 421 does not clear all alt-svc, alt-svc cache survives 421, h3 retry vs h2 fallback, 처음 보는 alt-svc cache, alt-svc dns cache confusion, cache reuse vs connection reuse, same origin 421 new h3, same origin 421 h2 fallback, what is per-origin 421

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [핵심 한 표: cache와 421 recovery는 무엇이 다른가](#핵심-한-표-cache와-421-recovery는-무엇이-다른가)
- [브라우저는 421 뒤에 무엇을 다시 판단하나](#브라우저는-421-뒤에-무엇을-다시-판단하나)
- [언제 새 H3로 다시 가고 언제 H2로 돌아가나](#언제-새-h3로-다시-가고-언제-h2로-돌아가나)
- [타임라인 예시 1: warm Alt-Svc, wrong shared H3, 새 H3 retry](#타임라인-예시-1-warm-alt-svc-wrong-shared-h3-새-h3-retry)
- [타임라인 예시 2: warm Alt-Svc, 421 뒤 H2 fallback](#타임라인-예시-2-warm-alt-svc-421-뒤-h2-fallback)
- [초급자가 자주 헷갈리는 포인트](#초급자가-자주-헷갈리는-포인트)
- [DevTools에서 먼저 볼 4가지](#devtools에서-먼저-볼-4가지)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

기존 primer를 읽고도 초급자는 아래 두 문장을 자주 한 문장으로 섞는다.

- "`Alt-Svc` cache가 아직 살아 있다"
- "방금 특정 origin이 `421`을 받았다"

하지만 이 둘은 같은 층위가 아니다.

- `Alt-Svc` cache는 "이 origin이 H3 후보를 배워 둔 상태인가"에 가깝다.
- `421` recovery는 "방금 사용한 그 connection/path가 이 origin에 맞았는가"를 교정한다.

그래서 `421` 하나를 봤다고 곧바로 "`Alt-Svc` 전체가 다 죽었다"라고 읽으면 과하다. 반대로 `Alt-Svc`가 warm하다고 해서 "`421` 뒤에도 무조건 같은 H3 길로 다시 간다"라고 읽어도 과하다.

이 문서는 그 중간 다리만 잡는다.

## 먼저 잡는 mental model

아주 짧게는 아래처럼 기억하면 된다.

- `Alt-Svc` cache: "이 origin은 H3 후보를 알고 있음"
- per-origin `421`: "하지만 방금 그 H3 connection/path는 이 origin에 맞지 않음"
- recovery: "그 origin만 새 길을 다시 고른다"

비유하면:

- 브라우저는 건물 안내 메모(`Alt-Svc`)를 아직 들고 있다.
- 그런데 `admin.example.com`만 특정 출입문에서 되돌려 보냈다(`421`).
- 그러면 브라우저는 건물 전체를 잊는 것이 아니라, **그 출입문으로 `admin`을 보내는 것만** 다시 생각한다.

핵심은 이것이다.

- `Alt-Svc` cache는 "후보를 기억하는 메모"
- `421`은 "이번 탑승 조합은 틀렸다"는 교정 신호

## 왜 자꾸 cache라는 단어에서 헷갈리나

초급자는 `cache`라는 단어가 세 군데에서 나와 자주 섞는다.

| 단어 | 실제로 저장하는 것 | 이 문서에서의 역할 |
|---|---|---|
| `Alt-Svc` cache | "이 origin에는 h3 후보가 있었다"는 힌트 | h3 후보를 기억하는 메모 |
| http cache | body, validator, `304` 관련 응답 재사용 | 이번 421 retry path의 중심이 아님 |
| session/cookie 상태 | 로그인 같은 사용자 상태 | connection 교정과 별개 층위 |

그래서 "`421`이 났다 = cache를 전부 지웠다"라고 읽으면 거의 항상 과하다.

## 핵심 한 표: cache와 421 recovery는 무엇이 다른가

| 질문 | `Alt-Svc` cache가 답하는 것 | per-origin `421`이 답하는 것 |
|---|---|---|
| 지금 무엇을 아는가 | 이 origin에 H3 후보가 있는가 | 방금 쓴 connection/path가 이 origin에 맞는가 |
| 범위 | 힌트를 배운 origin 중심 | 방금 실패한 origin + connection 문맥 중심 |
| 바로 내리면 안 되는 결론 | "warm이면 무조건 H3 성공" | "421이면 H3 전체 금지" |
| 브라우저가 다음에 하는 일 | 새 connection이 필요할 때 H3 후보를 검토 | 그 origin의 retry 경로를 더 좁게 다시 선택 |

초급자용 한 줄:

- cache는 "배운 것"
- `421`은 "방금 틀린 것"

## 브라우저는 421 뒤에 무엇을 다시 판단하나

`421` 뒤 브라우저가 다시 보는 질문은 보통 아래 둘이다.

1. 방금 실패한 것은 "`이 H3 전체`"인가, 아니면 "`이 shared H3 connection`"인가?
2. 같은 origin에 대해 **새 H3 connection**을 열어 볼 근거가 아직 남아 있는가?

그래서 `421` 뒤 행동은 항상 하나로 고정되지 않는다.

| `421` 뒤 재판단 항목 | beginner 해석 |
|---|---|
| 기존 shared H3 connection만 버리기 | 같은 H3라도 새 QUIC connection에서는 다시 될 수 있음 |
| 특정 alternative endpoint 신뢰 낮추기 | 다른 H3 endpoint나 기본 origin 경로를 볼 수 있음 |
| H3 후보 자체를 당장 보수적으로 취급 | 이번 recovery는 H2/H1.1로 갈 수 있음 |

브라우저별 세부 정책은 다를 수 있으므로, 초급자에게는 "`421` 뒤에는 그 origin의 경로 선택이 더 보수적으로 다시 평가된다" 정도로 잡는 것이 가장 안전하다.

## 언제 새 H3로 다시 가고 언제 H2로 돌아가나

가장 많이 궁금해하는 부분을 먼저 표로 자르면 아래와 같다.

| 관찰/상황 | 브라우저가 새 H3로 retry할 가능성이 큰 쪽 | 브라우저가 H2로 fallback할 가능성이 큰 쪽 |
|---|---|---|
| `Alt-Svc` 힌트는 여전히 plausible하고, 문제는 shared connection reuse로 보임 | 예 | 덜함 |
| 다른 authoritative H3 endpoint를 다시 고를 여지가 있음 | 예 | 덜함 |
| stale path를 버리고 fresh H3 connection만 열면 될 것 같음 | 예 | 덜함 |
| H3 path 자체 신뢰가 약해졌거나, QUIC path 문제/보수 정책이 겹침 | 덜함 | 예 |
| 새 H3를 다시 시도하는 것보다 기본 origin의 H2가 더 안전해 보임 | 덜함 | 예 |

초급자용 핵심 문장 두 개만 남기면 된다.

- `421`이 "wrong shared H3 connection" 교정에 가까우면 새 H3 retry가 가능하다.
- `421` 뒤 H3 path 자체가 덜 믿기거나 fallback 조건이 겹치면 H2로 돌아갈 수 있다.

즉 `421` 뒤 결과는 둘 다 가능하다.

- `421 -> 새 H3 -> 200`
- `421 -> H2 fallback -> 200`

## 타임라인 예시 1: warm Alt-Svc, wrong shared H3, 새 H3 retry

가장 단순한 per-origin recovery 예시는 이렇다.

```text
1. www.example.com 응답에서 Alt-Svc를 배워 H3 cache는 warm
2. 브라우저가 기존 shared H3 connection을 admin.example.com에도 재사용해 봄
3. edge/server가 admin에는 그 connection이 authoritative하지 않다고 보고 421 반환
4. 브라우저는 "admin을 이 shared connection에 싣는 것은 틀렸구나"를 학습
5. admin용 새 H3 connection 또는 더 맞는 H3 endpoint로 다시 감
6. 같은 URL이 h3에서 200으로 회복
```

이 장면의 포인트는 세 가지다.

- `Alt-Svc` cache는 여전히 warm일 수 있다.
- 틀린 것은 "`admin`을 기존 shared H3에 실은 것"일 수 있다.
- 그래서 recovery 결과도 다시 `h3`일 수 있다.

## 타임라인 예시 2: warm Alt-Svc, 421 뒤 H2 fallback

이번에는 recovery 결과가 H2인 장면이다.

```text
1. 브라우저는 예전에 배운 H3 alternative service를 아직 기억
2. 특정 origin 요청을 그 H3 path나 shared QUIC connection에 먼저 실음
3. 421이 돌아옴
4. 브라우저는 이번 origin에 대해서는 H3 재시도보다 기본 origin 경로가 더 안전하다고 판단
5. 새 TCP+TLS connection을 열고 h2로 다시 감
6. 같은 URL이 h2에서 200으로 회복
```

초급자는 여기서 "`421`이 나왔으니 Alt-Svc cache가 즉시 전역 삭제됐다"라고 이해할 필요는 없다.

더 안전한 해석은 이것이다.

- 그 origin의 다음 retry에서 H3보다 H2가 선택됐다.
- 이유는 wrong path 교정, 브라우저의 보수적 recovery, QUIC/H3 path 신뢰 저하가 함께 작용할 수 있다.

## 초급자가 자주 헷갈리는 포인트

| 헷갈리는 말 | 더 안전한 해석 |
|---|---|
| "`421`이면 Alt-Svc cache를 전부 비운다" | 보통은 그렇게 단순화하지 않는다. 먼저 특정 origin의 wrong connection/path 교정으로 본다. |
| "`Alt-Svc`가 warm하면 `421` 뒤에도 무조건 다시 H3다" | 아니다. 새 H3 retry도 가능하지만 H2 fallback도 가능하다. |
| "`421 -> h2`면 Alt-Svc가 원래 없었던 것이다" | 아니다. warm cache가 있어도 recovery 정책상 H2가 선택될 수 있다. |
| "한 origin이 `421`을 받았으니 같은 certificate의 다른 origin도 전부 실패한다" | 먼저 per-origin correction인지 본다. 다른 origin은 계속 정상일 수 있다. |
| "DevTools에서 disable cache를 켜면 Alt-Svc 문제도 같이 사라진다" | 아니다. http cache 토글과 Alt-Svc/connection 상태는 같은 스위치가 아니다. |

## DevTools에서 먼저 볼 4가지

| 무엇을 보나 | 왜 보나 |
|---|---|
| `Status` | 첫 줄이 `421`인지, 둘째 줄이 `200/403/404`인지 먼저 가른다 |
| `Protocol` | recovery 결과가 다시 `h3`인지 `h2`인지 본다 |
| `Connection ID` | 같은 H3 재사용 실패 뒤 새 connection으로 갈아탔는지 본다 |
| `Remote Address` | 다른 edge/endpoint로 바뀌었는지 본다 |

빠른 판독 예시는 아래처럼 잡으면 된다.

| 관찰 | 초급자 1차 해석 |
|---|---|
| `421 h3` 뒤 `200 h3`, `Connection ID` 변경 | wrong shared H3를 버리고 새 H3로 recovery했을 가능성 |
| `421 h3` 뒤 `200 h2` | per-origin recovery 뒤 더 보수적인 H2 fallback이 선택됐을 가능성 |
| `421 h3` 뒤 `403/404 h2/h3` | 첫 줄은 connection/path 교정, 둘째 줄은 그 다음 app 결과일 수 있음 |

## 다음에 이어서 볼 문서

- `Alt-Svc` 자체의 warm/stale/expiry 흐름부터 다시 보면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- `ma`, cache scope, `421`을 더 직접 비교하면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- stale hint에서 `421` 뒤 fresh path로 가는 장면을 더 길게 보면 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- same-URL `421` retry trace를 H2/H3 공통 그림으로 보면 [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- `421` 뒤 왜 `h2`가 되었는지 fallback 관점으로 더 보고 싶으면 [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)
- browser cache 토글과 Alt-Svc/DNS cache를 헷갈린다면 [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)

## 한 줄 정리

`Alt-Svc` cache가 warm하다는 것은 H3 후보를 아직 기억한다는 뜻이고, per-origin `421`은 방금 그 origin이 탄 connection/path가 틀렸다는 뜻이다. 그래서 브라우저는 `421` 뒤에 같은 origin을 새 H3로 다시 보낼 수도 있고, 더 보수적으로 H2로 fallback할 수도 있다.
