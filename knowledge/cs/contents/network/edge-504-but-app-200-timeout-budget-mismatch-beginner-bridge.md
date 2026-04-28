# Edge는 `504`인데 App은 `200`? Timeout Budget Mismatch Beginner Bridge

> 한 줄 요약: 브라우저는 edge gateway의 `504`를 봤는데 app 로그에는 `200`이 남는 장면은, 서로 다른 홉이 서로 다른 timeout 시계로 요청을 끝냈을 때 가장 흔하게 생긴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md)
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: edge 504 app 200, gateway timeout app 200, timeout budget mismatch, 브라우저 504인데 서버 로그 200, app은 성공했는데 왜 504, why edge 504 app 200, what is gateway timeout, 처음 보는 504, hop by hop timeout basics, browser waiting 504, proxy timeout budget beginner, timeout mismatch 왜 생겨요

## 핵심 개념

이 장면은 보통 "둘 중 하나가 거짓말한다"가 아니다.  
**브라우저가 본 종료 지점과 app이 본 종료 지점이 다르다**가 더 정확하다.

- 브라우저는 보통 edge gateway나 proxy가 최종으로 돌려준 상태 코드를 본다
- app 로그는 app이 자기 작업을 끝냈을 때의 결과를 남긴다
- edge timeout이 app 처리 시간보다 더 짧으면 브라우저는 `504`, app은 나중에 `200`을 남길 수 있다

초급자용 한 문장으로 줄이면 이렇다.

`504`는 "사용자가 기다리던 창구가 먼저 문을 닫았다"이고, app의 `200`은 "안쪽 창구는 뒤늦게 일을 끝냈다"이다.

## 한눈에 보기

| 눈에 보이는 현상 | 초급자 첫 해석 | 실제로 자주 있는 뜻 | 바로 다음 확인 |
|---|---|---|---|
| 브라우저 `504`, app 로그 없음 | app이 아예 못 받았을 수 있다 | edge나 proxy가 upstream 연결 전/초기에 포기했을 수 있다 | edge/proxy 로그와 upstream connect 흔적 |
| 브라우저 `504`, app 로그 `200` | 둘 중 하나가 틀렸다 | timeout budget mismatch로 종료 시점이 갈렸다 | edge timeout 값, app 처리 완료 시각 |
| 브라우저 `200`, app 로그 `200` | 같은 시계를 봤다 | end-to-end 예산 안에서 모두 끝났다 | 추가 확인 필요 없음 |

짧은 판단식:

```text
브라우저는 edge가 마지막에 한 말을 본다.
app 로그는 app이 자기 일을 끝낸 시점을 남긴다.
둘 사이 timeout budget이 다르면 edge 504 + app 200이 함께 나올 수 있다.
```

## 브라우저 타임라인 한 장으로 보기

브라우저 Network 탭에서 beginner가 먼저 상상해야 할 타임라인은 아래 하나면 충분하다.

```text
t=0ms    브라우저 -> edge 로 요청 시작
t=40ms   edge -> app 으로 전달
t=950ms  edge timeout 도달
t=951ms  브라우저는 504를 받음
t=1180ms app 작업 완료, app 로그에 200 기록
```

이 타임라인의 핵심은 `951ms`와 `1180ms`를 같은 사건으로 읽지 않는 것이다.

- 브라우저 사용자는 `951ms`에 이미 끝난 요청을 본다
- app은 `1180ms`에야 자기 일을 끝냈다고 기록한다
- 그래서 "브라우저 504"와 "서버 로그 200"이 동시에 참이 될 수 있다

DevTools에서는 보통 이렇게 읽으면 된다.

- `Status`가 `504`인지 먼저 본다
- waterfall에서 `waiting`이 길었는지 본다
- app 로그 timestamp가 edge timeout보다 뒤인지 비교한다

즉 browser timeline 질문은 "`왜 504가 떴지?`"보다 먼저  
"`사용자에게 응답이 끊긴 시점`과 `app이 끝난 시점`이 갈렸나?"로 두는 편이 안전하다.

## 홉별 mental model

이 패턴은 hop-by-hop으로 보면 훨씬 덜 헷갈린다.

| 홉 | 무엇을 기다리나 | 자기 timeout이 끝나면 | beginner 메모 |
|---|---|---|---|
| 브라우저 | edge의 최종 응답 | 사용자는 그 상태 코드로 끝난다 | 사용자는 app 내부 사정을 직접 못 본다 |
| edge / gateway | upstream app의 응답 | `504` 같은 gateway 응답을 직접 만들 수 있다 | 브라우저가 실제로 보는 주체인 경우가 많다 |
| app | DB, 외부 API, 내부 로직 | 자기 일은 계속 끝낼 수 있다 | 이미 사용자는 떠났는데도 `200`을 남길 수 있다 |

초급자용 비유:

- 브라우저 = 가게 앞 손님
- edge = 계산대 직원
- app = 주방

계산대 직원이 "30초 넘었으니 주문 취소"라고 말하면 손님은 끝이다.  
하지만 주방은 그 사실을 바로 모르고 요리를 완성할 수 있다. 그 장면이 바로 `edge 504 but app 200`이다.

## 흔한 오해와 함정

- `504`를 보면 app이 직접 `504`를 반환했다고 생각한다. 보통은 edge/gateway가 대신 말한 경우가 더 흔하다.
- app 로그에 `200`이 있으니 사용자도 `200`을 받았다고 단정한다. 사용자에게 실제로 간 응답은 edge에서 이미 끊겼을 수 있다.
- "그럼 app은 문제없다"라고 넘어간다. app이 cancellation을 모르고 오래 일하면 자원 낭비와 retry 증폭이 생긴다.
- `waiting`이 길면 무조건 DB만 느리다고 생각한다. 실제로는 queue wait, proxy timeout, per-hop budget reset일 수도 있다.
- 브라우저 시계와 app 시계를 비교하지 않는다. timestamp를 나란히 놓지 않으면 이 패턴을 거의 항상 놓친다.

## 실무에서 쓰는 모습

예를 들어 edge timeout이 `1.0s`, app 처리 시간은 `1.2s`인 요청을 생각해 보자.

| 시점 | 브라우저/edge 쪽에서 보이는 것 | app 쪽에서 보이는 것 |
|---|---|---|
| `0ms` | 요청 시작 | 요청 수신 |
| `1000ms` | edge가 기다림 종료, `504` 반환 | 아직 처리 중 |
| `1200ms` | 사용자는 이미 실패 화면 | 컨트롤러/서비스 로직 완료, `200` 로그 |

이때 learner가 가장 안전하게 내릴 첫 결론은 이것이다.

1. app이 아예 요청을 못 받은 건 아니다.
2. edge와 app의 timeout budget이 어긋났을 가능성이 크다.
3. 다음 액션은 "누가 마지막 응답을 만들었는가"와 "각 홉 timeout 값이 얼마였는가"를 붙여 보는 것이다.

특히 gateway, reverse proxy, service mesh가 중간에 있으면 아래처럼 숫자가 흔히 갈린다.

- browser patience: 2.5초
- edge gateway timeout: 1.0초
- app 내부 외부 API timeout: 2.0초
- DB query 완료: 1.2초

이 구성에서는 app 입장에서는 성공 가능한 요청이지만, 사용자 입장에서는 이미 실패다.

## 더 깊이 가려면

- `504`를 `500`/`502`와 먼저 가르려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- DevTools `waiting`과 timeline 읽는 법을 먼저 익히려면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- hop별 남은 시간을 어떻게 깎아 내려보내는지 보려면 [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- `504`가 edge local reply인지 upstream 결과인지 더 엄밀하게 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- app 내부 요청 수명과 async/cancel 감각까지 잇고 싶다면 [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

## 한 줄 정리

`edge 504 but app 200`은 보통 모순이 아니라, 브라우저와 app이 서로 다른 홉의 timeout 시계로 같은 요청을 끝낸 결과다.
