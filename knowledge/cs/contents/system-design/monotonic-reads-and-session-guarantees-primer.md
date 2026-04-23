# Monotonic Reads and Session Guarantees Primer

> 한 줄 요약: read-after-write는 "내가 방금 쓴 값", monotonic reads는 "내가 이미 본 값", causal consistency는 "내가 먼저 본 결과의 원인"을 기준으로 하고, session guarantees는 이 보장들을 한 사용자 흐름에 맞게 묶는 설계 이름이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)

retrieval-anchor-keywords: monotonic reads and session guarantees primer, monotonic reads primer, monotonic reads 뭐예요, session guarantees primer, session guarantee 차이, session guarantees decision matrix, list detail monotonicity bridge, list detail mismatch, list detail search min-version floor, value regression across pages, read-after-write vs monotonic reads vs causal consistency, read-your-writes vs monotonic reads, session guarantees vs causal consistency, writes-follow-reads beginner, monotonic writes beginner, monotonic reads routing example, causal consistency routing example, recent write flag min version causal token, saw newer then older, cause before effect routing, per-session consistency basics, beginner consistency guarantees, session pinning vs monotonic reads, session policy bundle

---

## 핵심 개념

초보자가 가장 많이 헷갈리는 이유는 네 용어가 모두 "최신값을 보여 주는 이야기"처럼 들리기 때문이다.
하지만 실제로는 **무엇을 기준으로 시간을 맞출지**가 다르다.

- read-after-write: 내 **방금 전 write**
- monotonic reads: 내가 **이미 본 최신선**
- causal consistency: 내가 먼저 본 **결과의 원인**
- session guarantees: 위 보장 중 필요한 것을 **한 세션 정책으로 묶는 방식**

즉, 이 문서는 "어떤 보장이 더 강한가"보다 **어떤 사용자 흐름에 어떤 기준선을 들고 다녀야 하는가**를 구분하는 입문 문서다.

---

## 먼저 한 주문 흐름으로 구분하기

아래처럼 같은 사용자 흐름을 따라가면 차이가 빠르게 보인다.

| 사용자 행동 | 깨질 수 있는 것 | 필요한 보장 | 가장 쉬운 라우팅 시작점 |
|---|---|---|---|
| `POST /orders` 직후 `GET /orders/123` | 방금 만든 주문이 안 보임 | read-after-write | 최근 write 뒤 짧게 primary fallback |
| 상세에서 `PAID`를 본 뒤 목록 이동 | `PAID -> PENDING`처럼 값이 뒤로 감 | monotonic reads | 세션의 `min_version`보다 뒤처진 replica/cache 금지 |
| 결제 완료 알림을 눌러 주문 화면 진입 | 결과는 봤는데 원인 데이터가 아직 안 보임 | causal consistency | causal token이나 watermark를 만족하는 경로만 허용 |
| 주문 생성, 상세 확인, 목록 이동, 알림 확인을 한 세션에서 이어감 | 화면마다 서로 다른 시간선을 봄 | session guarantees | 위 규칙 둘 이상을 세션 정책으로 묶음 |

핵심은 이것이다.

- read-after-write는 "내 write가 보이느냐"를 묻는다
- monotonic reads는 "내가 본 값보다 뒤로 가느냐"를 묻는다
- causal consistency는 "결과를 봤다면 원인도 같이 보이느냐"를 묻는다
- session guarantees는 "이 흐름에 어떤 질문들을 같이 묶을까"를 묻는다

---

## 한눈에 비교

| 개념 | 기준선 | 막는 실패 | 요청에 싣는 가장 단순한 힌트 | 시작하기 쉬운 라우팅 예시 |
|---|---|---|---|---|
| Read-after-write | 내가 방금 성공시킨 write | 저장 직후 옛값 재등장 | `recent_write=true`, `recent_write_until` | 최근 1~3초는 primary 또는 same-leader follow read |
| Monotonic reads | 세션이 이미 본 최고 version | `PAID -> PENDING`처럼 값 역행 | `min_version(order:123)=12` | `version < 12`인 replica/cache는 버리고 fallback |
| Causal consistency | 이전에 본 결과가 요구하는 dependency | 알림은 왔는데 댓글/주문 원문은 없음 | `causal_token`, `required_watermark` | 토큰을 만족하는 region/replica만 읽고 아니면 대기/primary fallback |
| Session guarantees | 한 세션에 필요한 보장 조합 | 화면마다 다른 시간선, 흐름 단절 | `session_policy=checkout` + 위 힌트들 | recent-write, min-version, causal-token 규칙을 같이 적용 |

짧게 줄이면 이렇다.

- read-after-write는 "내 write" 기준
- monotonic reads는 "내가 본 최신선" 기준
- causal consistency는 "원인-결과 순서" 기준
- session guarantees는 "보장 조합" 기준

---

## 왜 read-after-write만으로는 충분하지 않을까

read-after-write는 가장 좁은 보장이다.
내가 방금 저장한 값만 신경 쓴다.

```text
POST /profile -> primary commit
GET  /me      -> replica read
```

여기서 `GET /me`가 lagging replica로 가면 저장 성공 직후 예전 닉네임이 보인다.
이 문제는 보통 아래처럼 풀기 시작한다.

- recent-write flag를 세션에 1~3초 저장
- 해당 entity나 redirect endpoint만 primary fallback
- 같은 leader나 같은 region follow read가 가능하면 그 경로 유지

하지만 read-after-write만으로는 아래 문제가 남는다.

```text
GET /orders/123 -> version 12, status=PAID
GET /orders     -> version 10, status=PENDING
```

여기서는 사용자가 새로 write를 하지 않았어도 값이 뒤집혀 보인다.
즉, **이미 본 최신선**을 지키려면 monotonic reads가 따로 필요하다.

---

## Monotonic reads는 "뒤로 가지 않기"에 집중한다

monotonic reads의 질문은 단순하다.

> 내가 이미 `version 12`를 봤는데, 왜 다음 화면에서 `version 10`을 보지?

이 보장은 "항상 최신"을 약속하는 게 아니다.
그 대신 **내가 이미 본 시간선보다 과거로 내려가지 않게** 한다.

가장 쉬운 설계는 세션이 본 기준선을 기억하는 것이다.

- `session.min_version(order:123)=12`
- cache hit이라도 `version < 12`면 버림
- replica가 `12` 이상을 못 보이면 primary fallback
- version 추적이 어렵다면 짧은 session pinning으로 단순화

간단한 라우팅 예시는 이 정도로 시작할 수 있다.

```pseudo
function routeOrderRead(key, session):
  cached = cache.get(key)
  if cached != null and cached.version >= session.minVersion(key):
    return cached

  if replica.visibleVersion(key) >= session.minVersion(key):
    return replica.read(key)

  return primary.read(key)
```

핵심은 "새 값을 보여 주느냐"보다 **뒤로 가느냐**다.

---

## Causal consistency는 "결과를 봤다면 원인도 보이게" 한다

이번에는 댓글 알림이나 결제 완료 알림을 생각하면 쉽다.

```text
comment created -> notification emitted
notification opened -> comment thread read
```

알림에서 "새 댓글이 달렸습니다"를 봤는데 댓글 화면에는 댓글이 없으면 사용자는 단순 stale보다 더 강한 혼란을 느낀다.
이건 "내가 방금 썼는가"보다 **결과를 먼저 봤다면 그 원인도 함께 보여야 한다**는 문제다.

그래서 causal consistency는 보통 읽기 경로에 dependency 힌트를 실어 나른다.

- notification click에 `causal_token` 포함
- 토큰이 요구하는 watermark를 만족하는 region/replica만 선택
- 못 맞추면 잠깐 기다리거나 source-of-truth로 fallback

간단한 라우팅 예시는 아래처럼 생각할 수 있다.

```pseudo
function routeNotificationFollowup(request):
  if request.causalToken() <= region.visibleWatermark():
    return local_replica.read(request.key)

  return primary_or_source_of_truth.read(request.key)
```

즉, causal consistency는 "원인보다 결과를 먼저 보면 안 된다"는 보장이다.

---

## Session guarantees는 별도 기술보다 "정책 묶음"에 가깝다

실무에서 `session guarantee가 필요하다`고 말할 때는 보통 특정 기술 하나를 뜻하지 않는다.
대개는 **한 사용자 흐름에 필요한 보장을 조합한 정책**을 뜻한다.

예를 들어 checkout 세션 정책은 이렇게 묶을 수 있다.

```text
session_policy = checkout

- 주문 생성 직후 상세 화면: read-after-write
- 상세 -> 목록 -> 영수증 이동: monotonic reads
- 결제 완료 알림 -> 주문 화면: causal consistency
```

이 정책을 코드로 보면 아래 같은 느낌이다.

```pseudo
function routeRead(request, session):
  if request.isAfterWriteSensitive() and session.hasRecentWrite(request.key):
    return primary.read(request.key)

  if session.minVersion(request.key) > replica.visibleVersion(request.key):
    return primary.read(request.key)

  if request.causalToken() > region.visibleWatermark():
    return primary.read(request.key)

  return replica_or_cache.read(request.key)
```

여기서 session guarantees는 새로운 한 줄 규칙이 아니라, 위 세 줄을 **어떤 흐름에 함께 적용할지 결정하는 레벨**이다.

더 깊게 가면 writes-follow-reads, monotonic writes까지 붙을 수 있지만, beginner 단계에서는 "read-after-write + monotonic reads + 필요 시 causal consistency를 묶는 이름" 정도로 잡아도 충분하다.

---

## 요청에 무엇을 들고 다니나

보장을 주려면 요청 경로가 기준선을 알아야 한다.
초보자는 보통 "개념 이름"만 외우고 끝내기 쉬운데, 실전에서는 아래 힌트가 더 중요하다.

| 질문 | 가장 쉬운 힌트 | 보통 저장하는 곳 |
|---|---|---|
| 방금 write했나? | `recent_write_until` | session store, cookie, request context |
| 이미 본 최소 version은? | `min_version(key)` | session store, response token, client memory |
| 어떤 원인이 먼저 반영돼야 하나? | `causal_token`, `required_watermark` | link, message metadata, request header |
| 이 흐름에 어떤 보장을 묶나? | `session_policy`, endpoint freshness class | session context, gateway rule, app config |

이 힌트가 없으면 cache, replica, primary 사이에서 올바른 source selection을 하기 어렵다.

---

## 흔한 오해와 혼동

- `read-after-write만 있으면 monotonic reads도 해결된다`는 오해가 많다. 내가 write하지 않은 데이터나 이미 본 최신선은 여전히 뒤로 갈 수 있다.
- `monotonic reads`는 "항상 최신을 보여 준다"는 뜻이 아니다. 세션 기준으로 뒤로 가지 않게만 막는다.
- `causal consistency`가 곧 "모든 읽기를 primary로"라는 뜻은 아니다. 필요한 dependency를 만족하는 경로만 고르면 된다.
- `session guarantees`와 `causal consistency`를 같은 말처럼 쓰면 안 된다. 전자는 보장 묶음이고, 후자는 그 안에 들어갈 수 있는 한 항목이다.
- `sticky session`을 켰다고 session guarantees가 생기지는 않는다. app 인스턴스 affinity와 DB/read-model freshness 보장은 다른 문제다.
- cache가 앞에 있어도 규칙은 같아야 한다. cache hit accept rule, miss fallback rule, refill rule에 `min_version`과 causal 힌트를 같이 적용해야 한다.

---

## 빠른 판단법

새 흐름을 볼 때는 아래 순서로 물으면 된다.

1. 사용자가 **방금 쓴 값**을 바로 확인하나?
   그러면 read-after-write부터 본다.
2. 사용자가 여러 화면을 오가며 **이미 본 값보다 뒤로 가면 안 되나?**
   그러면 monotonic reads가 필요하다.
3. 사용자가 알림, 이벤트, 승인처럼 **결과를 먼저 보고 원인을 따라가나?**
   그러면 causal consistency를 본다.
4. 한 세션에서 위 질문이 둘 이상 동시에 중요하나?
   그러면 session guarantees로 묶는다.

이 판단 순서가 잡히면 "보장 이름"보다 "라우팅 규칙"이 더 쉽게 보인다.

---

## 더 깊이 가려면

- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)

## 한 줄 정리

read-after-write는 "내가 방금 쓴 값", monotonic reads는 "내가 이미 본 최신선", causal consistency는 "내가 먼저 본 결과의 원인", session guarantees는 이 보장들을 한 사용자 흐름에 맞게 묶는 정책 이름이다.
