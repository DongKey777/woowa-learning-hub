# Read-After-Write Consistency Basics

> 한 줄 요약: read-after-write consistency는 "방금 쓴 값을 바로 다시 읽을 수 있는가"의 문제이며, replica lag, primary fallback, session stickiness, strong read consistency가 어떤 제품 흐름에 필요한지 설명하는 입문 문서다.

retrieval-anchor-keywords: read-after-write consistency basics, read-after-write 뭐예요, replica lag basics, primary fallback, session stickiness, recent-write pinning, strong read consistency basics, stale read after write, write then read stale, order status freshness, payment confirmation consistency, beginner consistency, 방금 쓴 값 안 보여요, how to read after write

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)

---

## 핵심 개념

사용자는 보통 `저장` 버튼을 누른 다음 바로 같은 데이터를 다시 본다.
이때 시스템이 "쓰기"는 primary에서 처리하고 "읽기"는 replica에서 처리하면, 방금 저장한 값이 다음 화면에서 안 보일 수 있다.

이 현상의 가장 흔한 원인은 **replica lag**다.

```text
POST /profile -> primary commit
              -> replicate
GET  /profile -> replica read

commit은 끝났지만 replica apply가 아직 안 끝났다면
사용자는 방금 바꾼 값을 못 본다
```

여기서 초보자가 먼저 구분해야 할 단어는 네 개다.

- replica lag: primary commit 후 replica가 변경을 따라오는 데 걸리는 시간
- primary fallback: 최신성이 중요한 읽기만 잠시 primary로 보내는 방식
- session stickiness: 최근 write를 한 사용자 세션의 읽기를 더 신선한 경로에 잠깐 붙이는 방식
- strong read consistency: 읽을 때마다 최신 commit 기준 상태를 보장하려는 정책

핵심은 이것이다.

- 모든 읽기에 strong consistency를 강요하면 비싸다
- 하지만 어떤 제품 흐름은 stale read를 허용하면 안 된다
- 그래서 보통은 **경로별로 consistency 강도를 나눠서** 설계한다

즉, read-after-write consistency는 "replica를 쓰느냐 말느냐"보다 **어떤 사용자 흐름을 stale로 두면 안 되는가**를 정하는 문제다.

---

## 깊이 들어가기: Replica Lag와 Primary Fallback

### 1. Replica lag는 작은 숫자여도 제품에서는 크게 보인다

DB 관점에서 lag가 수십 ms여도 사용자 관점에서는 충분히 눈에 띈다.

대표 증상:

- 닉네임을 바꿨는데 새로고침 직후 예전 닉네임이 보인다
- 방금 주문했는데 주문 상세에서 아직 `PENDING`처럼 보인다
- 권한을 해제했는데 관리자 화면에서 잠깐 예전 권한처럼 보인다

즉, "lag가 짧다"와 "문제가 작다"는 같은 말이 아니다.
특히 write 직후 redirect되는 화면은 lag를 아주 잘 드러낸다.

### 2. Primary fallback은 최신성이 필요한 구간만 보호하는 가장 단순한 방법이다

가장 쉬운 해법은 "모든 GET을 replica로 보내지 말고, 중요한 읽기만 primary로 보낸다"다.

예:

- 주문 생성 직후 `GET /orders/{id}`
- 결제 완료 직후 영수증/주문 확인 화면
- 비밀번호 변경 직후 세션/권한 상태 확인

이 전략의 장점:

- 구현이 단순하다
- stale read를 바로 줄일 수 있다

단점도 분명하다.

- primary read 부하가 늘어난다
- fallback 범위를 넓히면 replica를 둔 효과가 줄어든다

그래서 primary fallback은 보통 **짧은 시간, 좁은 경로, 높은 가치 화면**에만 적용한다.

### 3. 흔한 오해

`read replica가 있으니 모든 GET을 replica로 보내면 된다`

- 아니다. write 직후 확인 흐름은 product bug처럼 보일 수 있다.

`lag가 100ms면 사용자도 못 느낀다`

- 아니다. redirect 직후 확인 화면에서는 100ms도 꽤 자주 드러난다.

---

## 깊이 들어가기: Session Stickiness와 Strong Consistency 정책

### 4. Session stickiness는 load balancer의 sticky session과 다른 개념이다

`stickiness`라는 단어 때문에 둘을 자주 헷갈린다.
하지만 목적이 다르다.

| 개념 | 무엇을 같은 곳에 붙이나 | 주 목적 |
|---|---|---|
| Load balancer sticky session | 사용자 요청을 같은 app 인스턴스에 붙인다 | 인메모리 세션 유지 |
| Read-after-write session stickiness | 최근 write한 사용자의 읽기를 fresher path에 붙인다 | 방금 쓴 값을 다시 읽게 한다 |

read-after-write에서의 session stickiness는 보통 아래처럼 쓴다.

- 최근 3초 안에 write한 사용자만 primary read
- 주문 직후 한두 번의 확인 요청만 primary로 pinning

이 부분은 [Stateless Sessions Primer](./stateless-sessions-primer.md)와 함께 보면 용어 충돌이 덜하다.

### 5. Strong read consistency가 꼭 필요한 제품 흐름은 따로 있다

| 제품 흐름 | stale 허용 여부 | 흔한 선택 |
|---|---|---|
| 결제 직후 주문 상세 / 영수증 | 거의 불가 | primary fallback 또는 강한 read |
| 재고 예약 직후 구매 가능 여부 | 거의 불가 | source of truth read |
| 권한 변경 직후 접근 제어 | 거의 불가 | primary read, version check |
| 프로필 수정 직후 내 프로필 화면 | 짧게는 가능하지만 UX 나쁨 | recent-write stickiness |
| 검색 결과 / 피드 | 보통 가능 | replica/cache + stale budget |

### 6. 단계적 정책이 더 현실적이다

```pseudo
function read(key, session, endpoint):
  if endpoint.requiresStrongRead():
    return primary.read(key)

  if session.hasRecentWrite(key, within=3 seconds):
    return primary.read(key)

  return replica.read(key)
```

`strong consistency가 제일 안전하니 전체 경로에 적용하자` — 최신성은 좋아질 수 있지만 latency, availability, primary load 비용이 함께 오른다.

---

## 실전 시나리오

### 시나리오 1: 프로필 수정 후 내 프로필 화면

- 사용자는 프로필 저장 후 바로 자기 프로필을 다시 본다
- stale이 나와도 금전 사고는 아니지만 UX가 크게 깨진다

이때는 전체 strong read보다 **짧은 recent-write stickiness**가 잘 맞는다.

### 시나리오 2: 결제 완료 후 주문 확인 페이지

- 결제 직후 주문이 안 보이면 사용자는 다시 결제할 수 있다
- support 문의와 환불 이슈로 바로 이어질 수 있다

이 경로는 replica default보다 **primary fallback**이 더 안전하다.

### 시나리오 3: 권한 해제 직후 관리자 접근 체크

- stale read가 잠깐이라도 security gap이 될 수 있다

이 경우는 일반적인 "UX inconsistency"가 아니라 **보안 경계**이므로 강한 read path를 더 보수적으로 잡는 편이 맞다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 잘 맞는 경우 |
|---|---|---|---|
| Replica default | 빠르고 확장성이 좋다 | write 직후 stale 가능 | 검색, 목록, 피드, 통계 |
| Recent-write session stickiness | 필요한 세션만 보호할 수 있다 | 라우팅 상태 관리가 필요하다 | 저장 후 redirect되는 UX 흐름 |
| Endpoint-level primary fallback | 이해하기 쉽고 효과가 빠르다 | primary read 부하가 늘어난다 | 주문 확인, 결제 결과, 권한 확인 |
| Full strong reads everywhere | 개념적으로 단순하다 | latency, availability, cost 부담이 크다 | 금전/재고/보안처럼 제한된 핵심 경로 |

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> read-after-write consistency는 사용자가 방금 쓴 값을 바로 다시 읽을 수 있게 하는 문제입니다.  
> read replica를 쓰면 replica lag 때문에 이 보장이 깨질 수 있어서, 실무에서는 모든 읽기를 강하게 만들기보다 최신성이 중요한 흐름만 primary fallback이나 recent-write session stickiness로 보호합니다.  
> 특히 결제, 재고, 권한처럼 틀렸을 때 비용이 큰 경로는 strong read consistency가 더 중요하고, 검색이나 피드처럼 약간 stale해도 되는 경로는 replica나 cache를 유지하는 식으로 나눕니다.

## 꼬리질문

> Q: read-after-write consistency와 strong consistency는 같은 말인가요?  
> 의도: session-level 보장과 global 보장의 차이 이해 확인  
> 핵심: read-after-write는 주로 "내가 방금 쓴 값을 내가 다시 읽는가"에 가깝고, strong consistency는 더 넓은 읽기 보장이다.

> Q: session stickiness와 sticky session은 왜 다르죠?  
> 의도: routing affinity의 대상 구분 확인  
> 핵심: 전자는 DB freshness를 위한 recent-write pinning이고, 후자는 app 인스턴스 메모리 세션 유지를 위한 load balancer 정책이다.

> Q: 모든 write 뒤에 primary fallback을 두면 안전하지 않나요?  
> 의도: selective consistency 감각 확인  
> 핵심: 안전성은 높아지지만 primary 부하가 커져 read scaling 이점을 잃을 수 있다.

> Q: 어떤 제품 흐름부터 strong read를 검토해야 하나요?  
> 의도: 도메인별 위험도 분류 확인  
> 핵심: 금전, 재고, 권한, 중복 실행 위험처럼 stale이 실제 사고로 이어지는 흐름부터 본다.

## 한 줄 정리

Read-after-write consistency는 replica lag를 제품 버그처럼 보이지 않게 다루는 설계 문제이며, 보통은 모든 읽기를 강하게 만들기보다 primary fallback과 session stickiness를 필요한 흐름에만 선택적으로 적용한다.
