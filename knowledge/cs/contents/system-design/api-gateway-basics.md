# API Gateway 기초 (API Gateway Basics)

> 한 줄 요약: API Gateway는 여러 백엔드 서비스 앞에서 "공통 입구" 역할을 하며, 인증 확인, 라우팅, 속도 제한처럼 모든 요청에 반복되는 처리를 한곳에 모은다.

**난이도: 🟢 Beginner**

관련 문서:

- [로드 밸런서 기초](./load-balancer-basics.md)
- [Rate Limiting 기초](./rate-limiting-basics.md)
- [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md)
- [프록시와 리버스 프록시 기초](../network/proxy-reverse-proxy-basics.md)
- [HTTP 요청-응답 헤더 기초](../network/http-request-response-headers-basics.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: api gateway basics, api gateway 뭐예요, api gateway 처음, api gateway 왜 써요, reverse proxy vs api gateway, load balancer vs api gateway, gateway routing basics, gateway auth basics, gateway rate limiting basics, 클라이언트 요청 어디로 가요, 인증을 어디서 하나요, 여러 서비스 앞단, what is api gateway, beginner gateway primer

## 먼저 잡는 멘탈 모델

API Gateway는 "서비스 여러 개 앞에 두는 건물 로비"처럼 보면 된다.

- 클라이언트는 로비 하나만 찾는다.
- 로비는 신분 확인을 하고, 어느 방으로 보낼지 정한다.
- 각 방(백엔드 서비스)은 자기 일에 더 집중한다.

이 비유가 좋은 이유는 **Gateway의 핵심이 비즈니스 처리보다 공통 입구 관리**라는 점을 먼저 보여주기 때문이다. 다만 실제 Gateway는 단순 전달자만은 아니고, 인증 실패 응답이나 rate limit 차단처럼 요청을 아예 끝낼 수도 있다.

## 30초 비교표: 뭐가 다른가

| 대상 | 주 질문 | 주 역할 |
|---|---|---|
| Load Balancer | "같은 서비스를 여러 대에 어떻게 나눌까?" | 같은 종류 서버들 사이에 트래픽 분산 |
| Reverse Proxy | "서버 앞에서 요청을 대신 받을까?" | 서버 보호, TLS 종료, 전달 |
| API Gateway | "여러 서비스를 한 입구로 묶고 공통 정책을 어디서 처리할까?" | 인증, 라우팅, rate limit, 공통 로깅 |

초보자가 처음 헷갈리는 포인트는 "API Gateway도 reverse proxy 역할을 할 수 있지만, 보통은 거기서 한 단계 더 나아가 서비스별 정책과 공통 입구 책임까지 맡는다"는 점이다.

## 1분 예시: 주문 API 호출 한 번 따라가기

모바일 앱이 `GET /api/orders/recent`를 호출한다고 하자.

1. 요청이 API Gateway에 먼저 도착한다.
2. Gateway가 `Authorization` 헤더를 확인한다.
3. 사용자별 초당 호출 수가 너무 많지 않은지 본다.
4. 경로 규칙에 따라 주문 서비스로 요청을 보낸다.
5. 응답 상태 코드와 지연 시간을 공통 로그에 남긴다.

이때 주문 서비스는 "주문 조회" 자체에 집중하고, "토큰 형식 확인"이나 "공통 접근 로그 형식"은 Gateway가 먼저 맡을 수 있다.

## 처음 헷갈리는 질문 먼저 자르기

| 지금 나온 질문 | 먼저 잡을 답 |
|---|---|
| "로드 밸런서랑 같은 거예요?" | 아니다. 로드 밸런서는 보통 같은 서비스 여러 대에 나누는 쪽이고, Gateway는 여러 서비스 앞 입구를 관리한다. |
| "Gateway가 인증을 다 하면 서비스는 인증을 몰라도 되나요?" | 보통 1차 확인은 Gateway가 돕지만, 서비스도 자신이 믿는 사용자 정보 범위는 검증해야 한다. |
| "Gateway에 주문 할인 규칙도 넣어도 되나요?" | 보통 아니다. 그런 도메인 판단은 주문 서비스 책임이다. |
| "서비스가 하나뿐인데도 꼭 필요해요?" | 꼭 그렇진 않다. 서비스가 단순하면 reverse proxy나 앱 내부 처리만으로도 충분할 수 있다. |

## 흔한 오해와 함정

- "Gateway를 넣으면 MSA가 완성된다"는 오해가 많다. Gateway는 입구를 정리할 뿐이고, 서비스 경계 설계나 데이터 일관성 문제를 대신 해결하지는 않는다.
- "인증을 Gateway에 뒀으니 내부 서비스는 무조건 안전하다"도 위험하다. 헤더 위조 방지, 서비스 간 신뢰 범위, 내부 호출 정책은 따로 봐야 한다.
- "Gateway는 무조건 있어야 한다"도 아니다. 작은 서비스에서는 hop 하나가 늘고 운영 대상만 늘 수 있다.
- "Gateway는 비즈니스 로직을 모으는 곳"으로 커지기 시작하면 변경 병목이 생긴다. 공통 정책과 도메인 규칙을 분리해야 한다.

## 다음 문서 고르기

| 지금 더 궁금한 것 | 다음 문서 | 이유 |
|---|---|---|
| "로드 밸런서랑 책임이 아직 섞여요" | [로드 밸런서 기초](./load-balancer-basics.md) | 같은 서비스 분산과 여러 서비스 입구 관리를 분리할 수 있다. |
| "프록시, 리버스 프록시, Gateway 용어가 헷갈려요" | [프록시와 리버스 프록시 기초](../network/proxy-reverse-proxy-basics.md) | 네트워크 앞단의 공통 큰 그림을 먼저 잡을 수 있다. |
| "속도 제한을 왜 걸고 어디서 세나요?" | [Rate Limiting 기초](./rate-limiting-basics.md) | Gateway에서 자주 같이 붙는 정책을 따로 이해할 수 있다. |
| "세션/토큰이랑 Gateway 관계가 헷갈려요" | [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md) | 인증 상태를 어디에 둘지 큰 그림을 먼저 정리할 수 있다. |

## 한 줄 정리

API Gateway는 여러 백엔드 서비스 앞에서 **공통 입구와 공통 정책을 맡는 계층**이고, 로드 밸런서나 reverse proxy와 겹치는 부분이 있어도 핵심 질문은 "여러 서비스 앞단의 인증·라우팅·제한을 어디서 통합할까"에 있다.
