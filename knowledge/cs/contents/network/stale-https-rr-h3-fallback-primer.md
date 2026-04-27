# Stale HTTPS RR H3 Fallback Primer


> 한 줄 요약: Stale HTTPS RR H3 Fallback Primer는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
> DNS `HTTPS` RR/SVCB cache가 예전 H3 endpoint를 아직 가리키지만, 서버가 `421`을 줄 틈도 없이 QUIC/H3 시도 단계에서 조용히 실패하고 브라우저가 H2/H1.1이나 새 path로 회복하는 beginner primer

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 관련 문서:
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md)
> - [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)
> - [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)
> - [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
> - [HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나](./https-rr-resolver-drift-primer.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)

retrieval-anchor-keywords: stale https rr h3 fallback, stale svcb h3 fallback, cached https rr outdated h3 path, stale dns h3 hint no 421, stale https record fallback, stale svcb no 421, old h3 endpoint from dns cache, https rr cached edge moved, quic fail before 421, no 421 silent fallback, browser h3 fallback stale dns, first h3 attempt then h2 without 421, stale https rr beginner primer, stale svcb beginner, outdated h3 endpoint dns cache

<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [왜 `421` 없이도 회복되나](#왜-421-없이도-회복되나)
- [한 표로 먼저 구분하기](#한-표로-먼저-구분하기)
- [짧은 타임라인 예시](#짧은-타임라인-예시)
- [초급자용 관찰 포인트](#초급자용-관찰-포인트)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 primer가 필요한가

입문자는 아래 장면에서 자주 멈춘다.

- DNS `HTTPS` RR/SVCB를 보고 H3를 시도한 것 같은데 DevTools에는 `421`이 없다.
- 첫 시도는 `h3`가 안 보이거나 아주 짧게 실패하고, 최종 row는 `h2` 또는 `http/1.1`로 성공한다.
- "`예전 DNS 힌트가 틀렸으면 왜 `421`로 설명되지 않지?`"라는 질문이 남는다.

이 문서는 그 장면을 한 줄로 고정한다.

- 브라우저가 DNS cache의 예전 H3 힌트를 먼저 믿는다.
- 하지만 그 endpoint가 이미 낡아서 QUIC/H3 시도 단계에서 실패한다.
- HTTP 요청이 정상적으로 올라가기 전에 실패했으므로 `421`을 줄 기회가 없을 수 있다.
- 브라우저는 조용히 기본 경로나 다른 새 path로 내려가 최종 성공한다.

### Retrieval Anchors

- `stale HTTPS RR H3 fallback`
- `stale SVCB no 421`
- `cached HTTPS RR outdated H3 path`
- `QUIC fail before 421`
- `no 421 silent fallback`

---

## 먼저 잡는 mental model

초급자는 "`잘못된 길`"과 "`그 사실을 언제 알았는가`"를 분리하면 된다.

| 질문 | 이 문서의 짧은 답 |
|---|---|
| 무엇이 stale한가 | DNS `HTTPS` RR/SVCB에서 배운 H3 path가 stale할 수 있다 |
| 왜 `421`이 없나 | HTTP layer까지 못 올라가면 서버가 `421`을 보낼 기회가 없다 |
| 브라우저는 어떻게 회복하나 | H2/H1.1 fallback 또는 fresh DNS/path 재선택으로 회복할 수 있다 |

비유하면:

- 출발 전에 지도 앱이 "`저 고속도로 진입로로 가면 된다`"고 알려 줬다.
- 그런데 현장에 가 보니 그 진입로가 이미 막혔다.
- 톨게이트 직원에게 "`이 길이 아닙니다`"라는 말을 들은 것이 아니라, 진입 자체가 안 돼서 다른 길로 돌아간 셈이다.

핵심은 이것이다.

> stale HTTPS RR/SVCB는 "`출발 전 힌트`"가 낡은 문제이고, `421`은 "`HTTP 요청을 받은 뒤 이 connection/path는 아니다`"라고 말할 수 있을 때 보이는 신호다.

---

## 왜 `421` 없이도 회복되나

`421 Misdirected Request`는 서버가 HTTP 요청을 실제로 받아서 "`이 origin을 이 연결로 처리하면 안 된다`"라고 답할 수 있을 때 나온다.

하지만 stale DNS H3 hint는 더 앞단에서 실패할 수 있다.

| 실패 위치 | 초급자 해석 | `421` 가능성 |
|---|---|---|
| DNS cache에는 예전 H3 endpoint가 남아 있음 | 출발 전 힌트가 낡음 | 아직 없음 |
| QUIC 연결 시도 또는 TLS/ALPN 성립 전 실패 | H3 문 앞에서 막힘 | 거의 없음 |
| 브라우저가 H2/H1.1로 fallback | 다른 길로 자동 전환 | `421` 없이도 가능 |
| HTTP 요청이 잘못된 authoritative endpoint까지 실제 도달 | 서버가 "`이 길은 아님`"을 응답 가능 | 여기서는 `421` 가능 |

즉 `421`이 안 보인다고 stale hint 가능성이 사라지는 것은 아니다.

- `421`은 HTTP 응답이다.
- stale HTTPS RR/SVCB 문제는 그보다 앞선 discovery/connection 단계에서 조용히 소화될 수 있다.

---

## 한 표로 먼저 구분하기

| 장면 | 무엇이 stale하거나 틀렸나 | 흔한 첫 신호 | 회복 모양 |
|---|---|---|---|
| stale `Alt-Svc` path | 브라우저의 HTTP 응답 기반 H3 메모 | `421`가 보일 수 있음 | 새 connection 또는 기본 경로로 재시도 |
| stale HTTPS RR/SVCB path | DNS cache의 출발 전 H3 힌트 | `421` 없이 H3 시도 실패 또는 최종 `h2` | silent fallback 또는 fresh path 재선택 |
| 단순 UDP/QUIC 차단 | H3 path 자체보다 네트워크 정책 문제 | 여러 host에서 일관된 H3 실패 | 계속 `h2`로 내려감 |

초급자용 한 줄 요약:

- `421`이 보이면 "HTTP까지 갔다가 교정당했나?"를 본다.
- `421` 없이 조용히 `h2`가 되면 "stale DNS H3 hint나 QUIC path 실패가 앞단에서 끝났나?"를 먼저 본다.

---

## 짧은 타임라인 예시

```text
1. 오전: resolver/browser cache가 HTTPS RR로 edge-old의 H3 힌트를 기억
2. 오후: 운영 변경으로 실제 H3는 edge-new 또는 H2 기본 경로만 정상
3. 브라우저가 cached HTTPS RR을 믿고 edge-old로 QUIC/H3를 먼저 시도
4. 연결 또는 handshake 단계에서 실패해 HTTP 요청까지 못 감
5. 브라우저가 H2/H1.1 또는 새 path로 조용히 fallback
6. 최종 요청은 200으로 성공하지만 421 row는 남지 않을 수 있음
```

이 시나리오에서 초급자가 기억할 핵심은 두 가지다.

- stale hint는 있었지만 서버가 `421`을 보낼 위치까지 가지 못했을 수 있다.
- 최종 `200`만 보고 "`처음부터 문제 없었다`"고 읽으면 앞단 H3 실패를 놓칠 수 있다.

---

## 초급자용 관찰 포인트

| 지금 보이는 장면 | 먼저 적는 해석 | 바로 다음 문서 |
|---|---|---|
| `dig HTTPS`에는 H3 힌트가 보이는데 최종 `Protocol=h2` | DNS discovery는 있었지만 H3 사용은 실패했을 수 있다 | [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md) |
| browser는 `h3`를 안 쓰는데 `Alt-Svc`도 안 보인다 | DNS HTTPS RR/SVCB만으로 출발했는지 분리해서 본다 | [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md) |
| 새 사용자와 기존 사용자의 결과가 다르다 | 기존 cache의 stale HTTPS RR/SVCB 가능성을 본다 | [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md) |
| `421`이 있는 경우와 없는 경우가 섞여 헷갈린다 | `421`은 HTTP까지 간 경우, no-`421`는 앞단 실패일 수 있다 | [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md) |
| browser와 `dig`가 서로 다른 H3 힌트를 본다 | resolver path와 cache 시점을 분리한다 | [HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나](./https-rr-resolver-drift-primer.md) |

입문자가 가장 먼저 붙여야 할 라벨은 이것이다.

- `421`이 없다고 stale discovery hint를 배제하지 않는다.
- `h2` 최종 결과만 보고 app 문제로 바로 넘어가지 않는다.

---

## 자주 헷갈리는 포인트

- stale HTTPS RR/SVCB와 stale `Alt-Svc`는 같은 캐시가 아니다.
- `421`이 없다고 해서 "`잘못된 H3 path 시도`"가 없었다고 단정하면 안 된다.
- `dig HTTPS`에 H3 힌트가 있다고 해서 브라우저가 반드시 끝까지 H3로 간 것은 아니다.
- 최종 `200`은 "`복구 후 성공`"일 수 있다.
- 모든 no-`421` fallback이 stale DNS hint 때문인 것은 아니다.
  - UDP 차단, handshake 실패, resolver drift도 같이 후보에 둬야 한다.

---

## 다음에 이어서 볼 문서

- discovery와 reuse 질문을 더 크게 가르려면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- DNS TTL과 browser `Alt-Svc` 메모가 왜 서로 다른 시간축으로 움직이는지 보려면 [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md)
- `421`이 있는 stale path 복구와 비교하려면 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- 관찰 증거를 `dig`/DevTools/curl로 나눠 보는 법은 [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)

## 한 줄 정리

cached DNS `HTTPS` RR/SVCB가 예전 H3 path를 가리키면, 브라우저는 그 힌트를 먼저 시도했다가 HTTP `421`을 받을 단계 전에 조용히 실패하고 H2/H1.1이나 새 path로 회복할 수 있다. 그래서 "`421`이 없다"와 "`stale H3 discovery hint가 아니다`"는 같은 뜻이 아니다.
