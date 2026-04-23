# Monotonic Reads and Session Guarantees Primer

> 한 줄 요약: read-after-write, monotonic reads, causal consistency, session guarantees는 모두 "같은 사용자 흐름의 시간선"을 다루지만 막아 주는 실패가 다르고, 그래서 라우팅 규칙도 다르게 잡아야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)

retrieval-anchor-keywords: monotonic reads and session guarantees primer, monotonic reads primer, monotonic reads 뭐예요, session guarantees primer, session guarantee 차이, read-after-write vs monotonic reads, causal consistency basics, session consistency routing, why data goes backward, saw newer then older, cause before effect routing, per-session consistency basics, beginner consistency guarantees, replica routing session guarantee

## 핵심 개념

초보자가 가장 헷갈리는 이유는 이 보장들이 모두 "값이 최신이어야 한다"처럼 들리기 때문이다.
하지만 실제로는 막는 실패가 서로 다르다.

- read-after-write: 내가 방금 저장한 값이 바로 안 보이는 문제
- monotonic reads: 한 번 본 최신값보다 나중 읽기가 더 오래된 값으로 뒤로 가는 문제
- causal consistency: 원인보다 결과를 먼저 보는 문제
- session guarantees: 위 보장들을 한 사용자 세션 단위로 묶어 설계하는 관점

즉, 네 단어는 모두 일관성 이야기이지만 같은 질문에 답하지 않는다.
system design에서는 "어느 요청에 어떤 보장을 붙일 것인가"를 먼저 정하고, 그다음에 primary fallback, session pinning, min-version token, causal token 같은 라우팅 수단을 고른다.

## 한눈에 보기

| 개념 | 먼저 묻는 질문 | 막는 실패 | 가장 단순한 라우팅 예시 |
|---|---|---|---|
| Read-after-write | `내가 방금 쓴 값이 보이나?` | 저장 직후 옛값 재등장 | 최근 write 뒤 3초 동안 primary read |
| Monotonic reads | `한 번 본 최신값보다 뒤로 가나?` | `PAID -> PENDING`처럼 값 역행 | 세션이 본 `min_version`보다 뒤처진 replica는 피함 |
| Causal consistency | `원인보다 결과를 먼저 보나?` | 댓글 알림은 왔는데 원글/댓글 조회는 404 | causal token이나 watermark를 만족하는 경로만 읽음 |
| Session guarantees | `이 사용자 흐름에 어떤 보장을 묶어야 하나?` | 화면마다 다른 시간선을 보는 문제 | read-after-write + monotonic reads를 세션 정책으로 묶음 |

헷갈리지 않게 한 줄로 줄이면 이렇다.

- read-after-write는 "내 write"를 기준으로 본다
- monotonic reads는 "내가 이미 본 최신선"을 기준으로 본다
- causal consistency는 "원인과 결과의 순서"를 기준으로 본다
- session guarantees는 위 보장 중 필요한 조합을 한 세션 정책으로 묶는다

## 상세 분해

### 1. Read-after-write는 가장 좁은 보장이다

프로필 저장 직후 내 프로필을 다시 보는 흐름을 생각하면 쉽다.

```text
POST /profile -> primary commit
GET  /me      -> replica read
```

이때 `GET /me`가 lagging replica로 가면 저장은 성공했는데 예전 닉네임이 보인다.
그래서 read-after-write는 보통 "최근 write가 있었던 그 사용자"만 잠깐 더 신선한 경로로 보낸다.

- recent-write flag를 세션에 1~3초 저장
- 해당 key나 endpoint만 primary fallback
- same leader / same region follow read가 가능하면 그 경로 유지

핵심은 "내가 방금 바꾼 값이 바로 안 보이는가"다.

### 2. Monotonic reads는 한 번 본 최신선 아래로 내려가지 않게 한다

이번에는 사용자가 주문 상세에서 이미 `PAID`를 본 뒤 목록으로 이동한다고 해 보자.

```text
GET /orders/123 -> version 12, status=PAID
GET /orders     -> version 10, status=PENDING
```

여기서는 내가 새로 write를 하지 않았어도 문제가 생긴다.
이미 본 최신선은 `version 12`인데 다음 읽기가 `version 10`으로 뒤로 갔기 때문이다.

그래서 monotonic reads는 보통 세션이 본 기준선을 기억한다.

- `session.min_version(order:123)=12`
- 다음 replica가 `12` 이상을 못 보여 주면 fallback
- 기준선 추적이 어렵다면 짧게 session pinning

핵심은 "내가 이미 본 미래보다 다시 과거로 가는가"다.

### 3. Causal consistency는 원인과 결과 순서를 본다

이번에는 댓글 작성 후 알림이 생기는 흐름을 보자.

```text
comment created -> notification emitted
notification opened -> comment thread read
```

알림에서는 "새 댓글이 달렸습니다"가 보이는데, 댓글 스레드에 들어가면 댓글이 없거나 원글이 아직 안 보이면 사용자는 더 크게 혼란을 느낀다.
이건 단순 stale read보다 "결과를 먼저 봤다"는 인과 순서 문제가 더 크다.

그래서 causal consistency는 보통 아래 같은 힌트를 읽기 경로에 실어 나른다.

- notification click에 causal token 포함
- 토큰이 요구하는 watermark를 만족하는 region/replica만 선택
- 못 맞추면 잠깐 대기하거나 primary/source-of-truth로 fallback

핵심은 "결과를 봤다면 그 결과의 원인도 함께 보여야 한다"다.

## 세션 보장을 묶는 법

실무에서 `session guarantee가 필요하다`고 말할 때는 보통 특정 기술 하나가 아니라 per-session 약속 묶음을 뜻한다.

- 저장 직후 확인 화면만 중요하면 read-after-write만으로도 충분할 수 있다
- 여러 화면을 오가며 상태가 뒤집히면 read-after-write에 monotonic reads를 추가한다
- 읽은 결과를 바탕으로 다음 쓰기나 승인 흐름이 이어지면 writes-follow-reads, monotonic writes까지 고려한다

즉 session guarantees는 "어떤 조합을 한 사용자 흐름에 줄 것인가"라는 설계 질문이고, monotonic reads는 그 안의 한 항목이다.
면접에서도 둘을 같은 말처럼 답하면 섞이기 쉽다.

## 흔한 오해와 함정

- `read-after-write만 있으면 monotonic reads도 자동으로 해결된다`는 오해가 많다. 내가 write하지 않은 데이터나 이전 화면에서 본 최신선은 여전히 뒤로 갈 수 있다.
- `sticky session을 켰으니 session guarantees가 생긴다`고 생각하기 쉽다. app 인스턴스 affinity와 DB/read-model freshness 보장은 다른 문제다.
- `causal consistency면 모든 읽기를 primary로 보내야 한다`는 뜻은 아니다. 필요한 dependency를 만족하는 경로만 고르면 된다.
- `session guarantees`와 `causal consistency`를 완전히 같은 말로 쓰면 안 된다. session guarantees는 보통 한 사용자 흐름의 약속 묶음이고, causal consistency는 원인과 결과의 순서를 더 넓게 보는 개념이다.
- cache가 앞에 있으면 보장이 자동으로 사라지지 않는다. cache hit accept rule, miss fallback rule, refill rule에도 같은 기준선을 적용해야 한다.

## 실무에서 쓰는 모습

많은 팀은 아래 정도의 간단한 routing ladder부터 시작한다.

```pseudo
function routeRead(request, session):
  if request.isAfterWriteSensitive():
    return primary

  if session.minVersion(request.key) > replica.visibleVersion(request.key):
    return primary

  if request.causalToken() > region.visibleWatermark():
    return source_of_truth

  return replica_or_cache
```

각 줄이 뜻하는 바는 단순하다.

| 사용자 흐름 | 필요한 보장 | 가장 쉬운 시작 규칙 |
|---|---|---|
| 저장 후 redirect 화면 | read-after-write | recent-write endpoint는 primary fallback |
| 상세에서 최신 상태를 본 뒤 목록/다음 단계 이동 | monotonic reads | 세션의 `min_version`보다 뒤처진 replica는 금지 |
| 알림/이벤트를 보고 원문으로 이동 | causal consistency | causal token이나 watermark를 만족하는 경로만 허용 |
| 여러 화면을 오가며 상태를 계속 확인 | session guarantees | 위 규칙 둘 이상을 세션 정책으로 묶음 |

cache가 앞에 있으면 `cache hit이면 끝`으로 두면 안 된다.
cache 값도 `min_version`이나 causal watermark를 못 맞추면 버리고 더 신선한 경로로 가야 한다.
이 mixed path 문제는 [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)에서 이어서 보면 된다.

## 더 깊이 가려면

- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)

## 면접/시니어 질문 미리보기

> Q: read-after-write와 monotonic reads의 차이는 뭔가요?
> 의도: "내 write" 기준과 "내가 본 최신선" 기준을 구분하는지 확인
> 핵심 답변: read-after-write는 저장 직후 최신성 보장이고, monotonic reads는 이미 본 최신값보다 뒤로 가지 않게 하는 보장이다.

> Q: session guarantees가 필요하다고 하면 보통 무엇을 뜻하나요?
> 의도: 묶음 개념을 이해하는지 확인
> 핵심 답변: 보통 read-after-write, monotonic reads, 필요하면 writes-follow-reads 같은 per-session 약속 조합을 뜻한다.

> Q: causal consistency는 언제 별도로 신경 써야 하나요?
> 의도: 원인-결과 흐름을 식별하는지 확인
> 핵심 답변: 알림->원문, 주문->결제, 승인->권한 반영처럼 결과를 봤다면 원인도 같이 보여야 하는 흐름에서 특히 중요하다.

## 한 줄 정리

read-after-write는 "방금 쓴 값", monotonic reads는 "이미 본 최신선", causal consistency는 "원인과 결과의 순서"를 지키는 보장이며, session guarantees는 그중 필요한 약속을 한 사용자 흐름에 묶어 주는 설계 이름이다.
