# 421 Retry Path Mini Guide: Fresh H3 Connection vs H2 Fallback

> 한 줄 요약: H3 connection reuse 뒤 `421`이 나오면 브라우저는 "같은 H3라도 새 QUIC connection으로 다시 갈지", 아니면 "더 보수적으로 H2로 내려갈지"를 고르며, 초급자는 그 차이를 `same origin, new connection, same protocol?` 순서로 읽으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: 421 retry path mini guide, 421 fresh h3 vs h2 fallback, h3 reuse 421 retry path, same h3 new connection after 421, h2 fallback after h3 421, fresh quic connection retry, browser 421 retry path, 421 after h3 reuse beginner, wrong h3 reuse then h2, wrong h3 reuse then fresh h3, 421 retry decision beginner, same url 421 then h3, same url 421 then h2, h3 misdirected request retry path, h3 421 fallback primer

## 먼저 잡는 mental model

`421` 뒤 retry path는 "이번 URL이 맞냐"보다 "다음엔 어느 길로 다시 갈까"의 문제다.

- fresh H3 retry: 브라우저가 "`H3 자체`를 버린 건 아니다. 방금 그 QUIC connection만 틀렸다"라고 판단
- H2 fallback: 브라우저가 "이 origin에서는 지금 H3 path를 덜 믿고, 일단 더 보수적인 H2로 다시 가자"라고 판단

즉 초급자용 한 줄은 이렇다.

- `421`은 **wrong connection 교정 신호**
- 그다음 선택은 **fresh H3**일 수도 있고 **H2 fallback**일 수도 있다

## 둘 중 무엇이 더 잘 나오나

운영자가 외워야 하는 세부 정책보다, 초급자는 아래 감각만 먼저 잡으면 된다.

| 재시도 결과 | 더 그럴듯한 상황 | 초급자 해석 |
|---|---|---|
| 새 `h3` connection | 기존 shared QUIC connection만 틀렸고, H3 endpoint 자체는 아직 유효해 보임 | "길은 H3가 맞지만, 방금 탔던 차선이 틀렸다" |
| `h2` fallback | 그 origin에 대해 H3 path를 덜 믿게 됐거나, 브라우저가 더 보수적인 경로로 재선택 | "이번엔 H3보다 기본 경로/H2가 더 안전하다고 봤다" |

핵심은 "H3 reuse 실패"와 "H3 전체 실패"를 같은 뜻으로 읽지 않는 것이다.

- reuse만 틀렸으면 fresh H3가 나올 수 있다
- H3 path 신뢰가 약해지면 H2 fallback이 나올 수 있다

## 가장 짧은 판별 카드

같은 URL 두 줄이 보이면 이 순서로 읽는다.

1. 첫 줄이 `421`인가
2. 둘째 줄이 **새 connection**인가
3. 둘째 줄의 `Protocol`이 `h3`인가 `h2`인가

이 세 질문을 표로 줄이면:

| 보이는 장면 | 1차 해석 |
|---|---|
| `421 (h3)` -> `200 (h3)` + connection id 변경 | fresh H3 connection retry 쪽이 더 강함 |
| `421 (h3)` -> `200/403/404 (h2)` + connection id 변경 | H2 fallback 뒤 app 결과를 본 것에 가까움 |
| `421 (h3)`만 있고 후속 row가 안 보임 | retry path를 아직 못 잡은 상태다. DevTools 보존/NetLog/edge log를 더 본다 |

## fresh H3 connection이 더 그럴듯한 때

아래처럼 읽으면 beginner에게 과하지 않다.

- 첫 줄도 `h3`, 둘째 줄도 `h3`다
- 하지만 `Connection ID`가 바뀌었다
- `Remote Address`가 같아도 괜찮다. **같은 edge여도 새 QUIC connection**일 수 있다

짧은 예시:

| row | Status | Protocol | Connection ID | 읽는 법 |
|---|---:|---|---:|---|
| 1 | `421` | `h3` | `42` | shared QUIC connection reuse 거절 |
| 2 | `200` | `h3` | `57` | H3는 유지하되 새 connection으로 다시 감 |

이 장면은 보통 이렇게 설명하면 충분하다.

"브라우저가 H3 자체를 포기한 게 아니라, 그 origin을 기존 QUIC connection에 같이 싣는 판단만 접었다."

## H2 fallback이 더 그럴듯한 때

이번에는 둘째 줄 protocol이 바뀐다.

- 첫 줄은 `421` + `h3`
- 둘째 줄은 `h2`
- connection도 새로 열린다

짧은 예시:

| row | Status | Protocol | Connection ID | 읽는 법 |
|---|---:|---|---:|---|
| 1 | `421` | `h3` | `42` | H3 reuse 거절 |
| 2 | `200` | `h2` | `63` | 브라우저가 더 보수적으로 H2로 재선택 |

초급자용 한 줄은 이렇다.

"`421` 뒤 `h2`가 보이면, 브라우저가 그 origin에 대해 fresh H3보다 H2 path를 더 안전하게 본 것이다."

중요한 점:

- 이것만으로 항상 UDP 차단이라고 단정하면 안 된다
- 이 문서의 문맥에서는 **reuse 거절 뒤 retry path 선택**을 읽는 것이지, 모든 H3 실패 원인을 확정하는 것이 아니다

## 왜 fresh H3로 갈 때도 있고 H2로 갈 때도 있나

정밀한 브라우저 내부 정책을 외우기보다, 아래 두 문장으로 기억하면 충분하다.

- 브라우저가 "`이 origin의 H3 endpoint는 아직 쓸 만하다`"라고 보면 fresh H3 connection이 더 자연스럽다
- 브라우저가 "`이번에는 H3 path보다 기본 경로를 쓰는 편이 안전하다`"라고 보면 H2 fallback이 더 자연스럽다

초급자용 비교표:

| 질문 | fresh H3 retry 쪽 | H2 fallback 쪽 |
|---|---|---|
| 무엇을 버렸나 | 기존 QUIC connection reuse 판단 | 이번 origin에 대한 H3 path 신뢰 일부 |
| 무엇은 유지했나 | H3 자체 | URL과 origin은 유지 |
| 화면에서 가장 눈에 띄는 것 | protocol은 그대로 `h3`, connection만 바뀜 | protocol이 `h3 -> h2`로 바뀜 |

## 자주 하는 오해

- "`421` 뒤 다시 `h3`가 보였으니 같은 요청을 같은 connection으로 보낸 것"은 아니다. connection id가 바뀌면 fresh H3다.
- "`421` 뒤 `h2`가 보였으니 원인이 무조건 UDP 차단"은 아니다. 이 문서에서는 먼저 retry path 재선택으로 읽는다.
- "`421`이 떴으니 H3는 완전히 깨졌다"도 아니다. 같은 trace 안에서 새 H3 connection으로 바로 회복될 수 있다.

## 다음에 이어서 볼 문서

- `421` 자체의 큰 흐름부터 다시 보려면 [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- stale `Alt-Svc`나 stale authority 쪽이 더 궁금하면 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- 실제 DevTools 판독 순서를 더 보고 싶으면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- `h3 -> h2`가 정말 fallback인지, 애초에 H3 시도 근거가 있었는지 더 따지려면 [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)

## 한 줄 정리

H3 reuse 뒤 `421`이 나왔을 때는 "다음 줄이 새 `h3`인가, 아니면 `h2`인가"를 보면 fresh H3 connection retry와 H2 fallback을 초급자도 안전하게 구분할 수 있다.
