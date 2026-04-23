# Causal Consistency Notification Primer

> 한 줄 요약: 알림을 먼저 봤다면 그 알림이 가리키는 댓글, 주문, 승인 같은 source 데이터도 이어서 보여야 하고, 이 "결과를 봤으면 원인도 보여야 한다"는 문제가 causal consistency다.

**난이도: 🟢 Beginner**

관련 문서:

- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Notification 시스템 설계](./notification-system-design.md)
- [Mobile Push Notification Pipeline Design](./mobile-push-notification-pipeline-design.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)
- [system design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: causal consistency notification primer, notification to source flow, notification click source missing, notification click watermark check, tap notification but source missing, 알림 눌렀는데 본문 없음, effect before cause notification, cause before effect notification, causal consistency vs stale read, causal token notification, required watermark notification, comment notification source read, payment notification order detail, beginner causal consistency, what is causal consistency notification

---

## 핵심 개념

초보자가 이 주제를 stale read와 자주 헷갈리는 이유는 겉보기 증상이 비슷하기 때문이다.
둘 다 "기대한 데이터가 안 보인다"처럼 보인다.

하지만 질문이 다르다.

- 단순 stale read: "값이 조금 옛날인가?"
- causal consistency: "내가 이미 본 결과를 설명하는 원인도 같이 보이나?"

알림 흐름으로 보면 차이가 더 선명하다.

1. 사용자가 `새 댓글이 달렸습니다` 알림을 본다
2. 알림을 눌러 댓글 화면으로 들어간다
3. 댓글이 안 보인다

이건 단순히 "조금 stale하다"보다, **결과를 먼저 봤는데 원인이 안 보이는 상태**다.
그래서 causal consistency는 notification-to-source 흐름에서 특히 중요하다.

---

## 한눈에 보기

| 상황 | 사용자가 먼저 본 것 | 이어서 안 보이는 것 | 먼저 떠올릴 이름 | 가장 단순한 첫 대응 |
|---|---|---|---|---|
| 프로필 저장 후 내 프로필 확인 | 내가 방금 성공시킨 write | 새 닉네임 | read-after-write | recent-write flag, short primary fallback |
| 주문 상세에서 `PAID`를 본 뒤 목록 이동 | 내가 이미 본 최신 상태 | 더 최신인 줄 알았던 상태가 뒤로 감 | monotonic reads | `min_version` 이하 경로 차단 |
| `새 댓글`, `결제 완료`, `승인 완료` 알림을 누름 | 결과를 알려 주는 notification | 그 결과의 source 데이터 | causal consistency | notification payload의 causal token, watermark-aware routing |

짧게 줄이면 이렇다.

- read-after-write는 "내 write가 보이느냐"를 본다
- monotonic reads는 "내가 본 선보다 뒤로 가느냐"를 본다
- causal consistency는 "결과를 봤다면 그 원인도 이어서 보이느냐"를 본다

---

## 상세 분해

### 1. 알림은 보통 source의 "결과 신호"다

알림은 대개 source write가 끝난 뒤 만들어진다.
댓글 생성, 주문 상태 변경, 승인 완료 같은 source 이벤트가 먼저 있고, notification은 그 뒤에 나온다.

```text
source write -> event/outbox -> notification delivered
            -> replica/read model catch-up
```

문제는 notification delivery path와 source read path가 같지 않다는 점이다.
push 시스템은 빠르게 도착했는데, 댓글 화면이나 주문 상세 화면은 아직 lagging replica/read model을 읽을 수 있다.

### 2. 그래서 notification-to-source 흐름은 causal 질문이 된다

사용자는 알림을 보는 순간 이미 "어떤 일이 일어났다"는 결과를 받아들인다.
그 상태에서 source 화면에 들어갔는데 원인이 안 보이면, 사용자 입장에서는 시간보다 **의미 순서**가 깨진다.

대표 예시는 아래 셋이다.

- `새 댓글` 알림을 눌렀는데 댓글 본문이 없다
- `결제 완료` 알림을 눌렀는데 주문 상세는 아직 `PENDING`이다
- `승인 완료` 알림을 눌렀는데 권한 화면은 아직 바뀌지 않았다

이때의 핵심 질문은 "조금 기다리면 최신이 되나?"가 아니라, **알림이 가리키는 dependency를 이 읽기 경로가 만족하나?**다.

### 3. 단순 stale-read handling과 다른 이유

read-after-write 문제는 대개 사용자가 직접 write한 뒤 곧바로 읽는 흐름이다.
그래서 `recent_write=true`나 짧은 primary fallback으로 시작해도 된다.

하지만 notification-to-source 흐름에서는 사용자가 write하지 않았을 수 있다.
알림이 dependency를 대신 들고 와야 한다.

즉 차이는 아래와 같다.

- read-after-write: "내가 방금 쓴 값"
- causal notification flow: "내가 방금 본 결과가 의존하는 원인"

그래서 `500ms 뒤 재시도`는 현상을 가릴 수는 있어도, causal consistency를 보장했다고 말하기는 어렵다.

---

## 흔한 오해와 함정

- `알림 delivery를 조금 늦추면 causal 문제가 사라진다`는 오해가 많다. 경로별 지연이 계속 달라질 수 있어서 근본 해결이 아니다.
- `causal consistency면 모든 source read를 primary로 보내야 한다`는 뜻은 아니다. 필요한 token이나 watermark를 만족하는 경로만 고르면 된다.
- `monotonic reads와 causal consistency는 거의 같은 말이다`라고 섞어 쓰면 안 된다. 전자는 내가 본 시간선의 하한을 지키는 것이고, 후자는 결과와 원인의 dependency를 지키는 것이다.
- `알림 본문에 일부 내용을 넣었으니 source가 늦어도 괜찮다`고 생각하기 쉽다. 하지만 deep link 뒤 액션, 상세 조회, 후속 버튼은 결국 source-of-truth를 읽어야 한다.
- `retry 한 번 넣었으니 해결됐다`고 보면 안 된다. 사용자가 이미 결과를 본 뒤이므로, 운 좋게 맞는 경우와 보장된 경우를 구분해야 한다.

---

## 실무에서 쓰는 모습

beginner 단계에서는 "알림에 dependency 힌트를 싣고, source read가 그 힌트를 만족하는지 확인한다" 정도로 이해하면 충분하다.

| 단계 | 요청/데이터에 싣는 것 | 왜 필요한가 |
|---|---|---|
| source write 완료 | `entity_version`, `commit_lsn`, `watermark` | 어떤 원인이 이미 확정됐는지 표현 |
| notification 생성 | `causal_token`, `required_watermark`, `entity_id` | 알림이 어떤 source 상태를 전제로 하는지 표현 |
| notification open | deep link + token 전달 | 알림이 본 dependency를 source read path로 넘김 |
| source read | cache/replica가 token 충족 여부 확인 | 못 맞추면 fallback해서 effect-before-cause를 막음 |

아주 단순한 라우팅 예시는 아래처럼 생각할 수 있다.

```pseudo
function openFromNotification(key, causalToken):
  cached = cache.get(key)
  if cached != null and cached.watermark >= causalToken.requiredWatermark:
    return cached

  if replica.visibleWatermark(key) >= causalToken.requiredWatermark:
    return replica.read(key)

  return primary.read(key)
```

중요한 점은 notification service가 모든 replica가 따라올 때까지 delivery를 무조건 멈춰야 한다는 뜻이 아니라, **알림이 의존하는 기준선을 source read까지 함께 가져가야 한다**는 점이다.

---

## 더 깊이 가려면

- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Notification 시스템 설계](./notification-system-design.md)
- [Causal Consistency Intuition](../database/causal-consistency-intuition.md)

---

## 면접/시니어 질문 미리보기

> Q: notification-to-source 문제를 왜 read-after-write 하나로 설명하면 부족한가요?
> 의도: 직접 write한 사용자의 최신성 문제와 dependency visibility 문제를 구분하는지 확인
> 핵심: notification flow에서는 사용자가 write하지 않았어도 결과를 먼저 볼 수 있으므로, request가 causal dependency를 전달해야 한다.

> Q: 가장 단순한 시작 설계는 무엇인가요?
> 의도: over-engineering 없이도 causal contract를 잡는 법을 아는지 확인
> 핵심: notification payload에 token/watermark를 싣고, source read path에서 그 기준선을 만족하는 cache/replica만 허용한다.

> Q: `retry after 300ms`는 왜 보장이 아니죠?
> 의도: 확률적 완화와 계약 기반 consistency를 구분하는지 확인
> 핵심: 지연 편차가 계속 바뀌므로 재시도는 성공 확률을 높일 뿐, effect-before-cause를 막는 명시적 contract가 아니다.

---

## 한 줄 정리

notification-to-source 흐름에서 causal consistency는 "알림이라는 결과를 봤다면 그 결과의 원인 source도 이어서 읽혀야 한다"는 보장이고, 그래서 단순 stale-read handling과 구분해서 봐야 한다.
