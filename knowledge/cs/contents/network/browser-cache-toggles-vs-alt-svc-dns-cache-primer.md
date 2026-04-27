# Browser Cache Toggles vs Alt-Svc DNS Cache Primer


> 한 줄 요약: Browser Cache Toggles vs Alt-Svc DNS Cache Primer는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> DevTools `Disable cache`, 새 profile, 기존 connection 종료가 왜 서로 다른 H3 discovery 결과를 만드는지, "무슨 cache를 비웠는가"와 "새 connection이 정말 생겼는가" 관점으로 설명하는 beginner primer

> 관련 문서:
> - [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)
> - [Browser DevTools 새로고침 분기표: normal reload, hard reload, `Disable cache`](./browser-devtools-reload-hard-reload-disable-cache-primer.md)
> - [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
> - [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나](./https-rr-resolver-drift-primer.md)
> - [Browser NetLog H3 Appendix: Alt-Svc Cache와 HTTPS RR 흔적 확인](./browser-netlog-h3-alt-svc-https-rr-appendix.md)

retrieval-anchor-keywords: disable cache vs fresh profile, disable cache vs close connections, alt-svc cache primer, dns cache primer browser, h3 discovery different results, disable cache not alt-svc cache, disable cache not dns cache, close connections h3 discovery, fresh profile alt-svc clean test, fresh profile dns cache clean test, browser cache toggle h3, browser cache vs alt-svc vs dns cache, http cache vs alt-svc cache vs dns cache, why h3 appears only after closing connections, why fresh profile changes h3

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 멘탈 모델](#먼저-잡는-멘탈-모델)
- [세 가지 실험이 왜 다른가](#세-가지-실험이-왜-다른가)
- [한눈에 보는 비교표](#한눈에-보는-비교표)
- [같은 사이트가 다르게 보이는 대표 타임라인](#같은-사이트가-다르게-보이는-대표-타임라인)
- [초급자용 관찰 순서](#초급자용-관찰-순서)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)

</details>

## 먼저 잡는 멘탈 모델

H3 discovery 실험에서 브라우저가 기억할 수 있는 것은 보통 세 층이다.

| 층 | 무엇을 기억하나 | H3 관찰에 주는 영향 |
|---|---|---|
| HTTP response cache | HTML, JS, 이미지, `ETag`, `304` 같은 body 재사용 정보 | body를 다시 받는지에 영향 |
| discovery cache | `Alt-Svc` 메모, DNS HTTPS RR/SVCB 결과 같은 "다음 연결 힌트" | 새 connection에서 H3를 시도할지에 영향 |
| live connection | 이미 열려 있는 H2/H3 연결 자체 | 새 discovery보다 기존 길 재사용에 영향 |

핵심은 이것이다.

- DevTools `Disable cache`는 주로 첫 번째 층, 즉 **HTTP response cache 관찰**을 흔든다.
- 새 profile은 첫 번째와 두 번째 층을 함께 비우는 쪽에 가깝다.
- 기존 connection 종료는 세 번째 층을 끊어서 **브라우저가 새 connection 결정을 다시 하게** 만든다.

그래서 세 실험은 이름이 비슷해 보여도 "무엇을 초기화했는가"가 다르다.

## 세 가지 실험이 왜 다른가

### 1. DevTools `Disable cache`

이 체크박스는 보통 "응답 body 재사용을 덜 보게 만드는 실험 스위치"로 읽는 편이 안전하다.

- `from memory cache`, `from disk cache`, `304` 같은 관찰이 달라질 수 있다
- 하지만 이미 배운 `Alt-Svc` 메모나 DNS 쪽 힌트를 항상 함께 지워 주는 스위치는 아니다
- 이미 열린 H2 connection도 그대로 남아 있을 수 있다

초급자 결론:

- `Disable cache`만 켜고 "`왜 아직 h2지?`"라고 보면 질문이 섞였을 수 있다
- body cache는 우회했어도, discovery 메모와 live connection은 그대로일 수 있다

### 2. 새 profile

새 profile은 보통 가장 "cold start"에 가까운 출발점이다.

- HTTP response cache가 비어 있다
- 브라우저 안의 `Alt-Svc` 메모도 없는 상태에서 시작할 가능성이 높다
- 기존 browsing session의 host resolver 상태나 H3 학습 흔적도 줄어든다

그래서 새 profile에서는 자주 이런 흐름이 나온다.

1. 첫 요청은 `h2`
2. response에서 `Alt-Svc`를 배움
3. 다음 새 connection에서야 `h3`가 보일 수 있음

즉 새 profile은 "`브라우저가 H3를 언제 처음 배웠는가`"를 보기 좋다.

### 3. 기존 connection 종료

기존 connection을 닫는 실험은 cache를 지우는 실험이라기보다, **기존 길을 못 쓰게 해서 새 길 선택을 다시 보게 하는 실험**이다.

- warm `Alt-Svc` 메모가 이미 있다면, 기존 H2 connection을 닫은 뒤 새 connection에서 `h3`가 갑자기 보일 수 있다
- 반대로 기존 H3 connection을 닫았더니 새 경로에서 다시 `h2`가 나올 수도 있다
- 이 차이는 `Alt-Svc`/DNS 힌트 유무와 별개로 "브라우저가 새 연결을 만들 기회를 얻었는가"에 달려 있다

초급자 결론:

- "`닫고 다시 열었더니 h3가 됐다`"는 말은 종종 `Alt-Svc` 메모가 새로 생긴 것이 아니라, **기존 H2 reuse가 끊겨 새 선택이 일어난 것**에 가깝다

## 한눈에 보는 비교표

| 실험 | 주로 건드리는 것 | 그대로 남을 수 있는 것 | H3 discovery 관점의 흔한 결과 |
|---|---|---|---|
| DevTools `Disable cache` | HTTP response cache 관찰 | `Alt-Svc` 메모, DNS 힌트, 기존 connection | protocol은 그대로인데 body cache 흔적만 달라질 수 있음 |
| 새 profile | HTTP cache + `Alt-Svc` 메모 + 세션 상태 상당수 | 서버 설정, 네트워크 정책, 외부 DNS 현실 | 첫 요청 `h2`, 다음 새 connection `h3` 같은 cold-to-warm 흐름이 잘 보임 |
| 기존 connection 종료 | live connection reuse | 이미 배운 `Alt-Svc` 메모, DNS 힌트 | 기존 H2가 끊긴 뒤 새 connection에서 `h3`가 드러날 수 있음 |

짧게 줄이면:

| 질문 | 더 맞는 실험 |
|---|---|
| "이 body가 cache hit였나?" | `Disable cache` ON/OFF 비교 |
| "`Alt-Svc`를 처음 배우는 순간부터 보고 싶나?" | 새 profile |
| "기존 H2 재사용 때문에 H3가 안 보였나?" | 기존 connection 종료 |

## 같은 사이트가 다르게 보이는 대표 타임라인

예를 들어 `https://shop.example.com`이 첫 응답에서 아래 header를 준다고 하자.

```http
Alt-Svc: h3=":443"; ma=86400
```

브라우저에서 보일 수 있는 대표 흐름은 이렇다.

### 장면 A. 새 profile에서 시작

1. 첫 요청: `Protocol = h2`
2. response header: `Alt-Svc: h3=":443"; ma=86400`
3. 같은 H2 connection을 계속 재사용하는 동안은 여전히 `h2`
4. connection을 새로 만들 기회가 오면 그때 `h3`

이 장면의 포인트:

- 새 profile은 `Alt-Svc`를 **처음 배우는 순간**이 드러난다
- 첫 요청이 바로 `h3`가 아니어도 이상하지 않다

### 장면 B. 평소 쓰던 profile에서 `Disable cache`만 켬

1. 이미 이전 방문 덕분에 `Alt-Svc` 메모가 warm일 수 있다
2. 하지만 기존 H2 connection도 살아 있을 수 있다
3. `Disable cache`를 켜면 body cache 흔적은 줄어든다
4. 그래도 protocol은 계속 `h2`일 수 있다

이 장면의 포인트:

- "`Disable cache`를 켰는데 왜 H3가 안 보이지?"는 자연스러운 질문이지만,
- 실제로는 **protocol 선택보다 body cache만 건드렸기 때문**일 수 있다

### 장면 C. 같은 profile에서 connection까지 닫음

1. warm `Alt-Svc` 메모는 남아 있다
2. 기존 H2 connection은 더 이상 재사용할 수 없다
3. 브라우저가 새 connection을 만들며 H3를 다시 시도한다
4. 이제 `Protocol = h3`가 보일 수 있다

이 장면의 포인트:

- 결과가 바뀐 이유는 `Disable cache`가 아니라 **새 connection 강제**일 수 있다

## 초급자용 관찰 순서

H3 discovery 실험을 덜 헷갈리게 하려면 아래 순서가 안전하다.

1. 먼저 새 profile 또는 충분히 깨끗한 조건에서 첫 요청을 본다.
2. 첫 response에 `Alt-Svc`가 있는지 적는다.
3. 그다음 요청이 **기존 connection reuse**인지, **새 connection 생성**인지 나눠 본다.
4. `Disable cache`는 body cache 실험용으로만 따로 쓴다.
5. DNS HTTPS RR/SVCB도 의심되면 browser와 `dig` 결과가 같은 resolver를 보는지 바로 단정하지 않는다.

아주 짧은 판독 규칙:

- `Disable cache` 차이 = 먼저 HTTP cache 질문
- 새 profile 차이 = discovery warm-up 질문
- connection 종료 후 차이 = connection reuse 질문

## 자주 헷갈리는 포인트

### `Disable cache`가 `Alt-Svc` cache도 같이 지운다고 생각한다

보통 그렇게 단정하면 안 된다.

- `Disable cache`는 주로 HTTP response cache 관찰 스위치다
- `Alt-Svc` 메모나 DNS 힌트, live connection은 별도 층이다

### 새 profile과 connection 종료를 같은 실험으로 본다

둘은 다르다.

- 새 profile은 "아예 처음 배우는가"를 보기 좋다
- connection 종료는 "이미 배운 힌트를 새 연결에서 쓸 기회를 만들었는가"를 보기 좋다

### DNS cache와 `Alt-Svc` cache를 하나로 묶어 말한다

둘 다 discovery 입력이지만 출처가 다르다.

- `Alt-Svc`는 이전 HTTP response에서 배운다
- DNS HTTPS RR/SVCB는 DNS 단계에서 배운다
- 둘 중 무엇이 실제로 쓰였는지는 DevTools만으로 모호할 수 있다

### `h3`가 보였으니 실험 원인도 확정됐다고 말한다

`h3`는 결과다.

- warm `Alt-Svc` 때문일 수 있다
- DNS HTTPS RR 때문일 수 있다
- 기존 connection을 닫아 새 선택이 일어났기 때문일 수 있다

## 다음에 이어서 볼 문서

- HTTP body cache 실험을 따로 정리하려면 [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)
- `Alt-Svc` warm, expired, stale 흐름을 더 자세히 보려면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- DNS HTTPS RR와 `Alt-Svc`를 더 직접 비교하려면 [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)
- browser와 `dig` 결과가 왜 엇갈리는지 보려면 [HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나](./https-rr-resolver-drift-primer.md)
- DevTools만으로 모호할 때는 [Browser NetLog H3 Appendix: Alt-Svc Cache와 HTTPS RR 흔적 확인](./browser-netlog-h3-alt-svc-https-rr-appendix.md)

## 한 줄 정리

Browser Cache Toggles vs Alt-Svc DNS Cache Primer는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
