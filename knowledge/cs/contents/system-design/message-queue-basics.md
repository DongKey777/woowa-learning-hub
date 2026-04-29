# 메시지 큐 기초 (Message Queue Basics)

> 한 줄 요약: 메시지 큐는 `지금 응답에 꼭 필요 없는 일`을 뒤로 넘겨 생산자와 소비자의 속도를 분리하는 비동기 handoff 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md)
- [System Design Foundations](./system-design-foundations.md)
- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- [Queue vs Cache vs DB Decision Drill](./queue-vs-cache-vs-db-decision-drill.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md)
- [커맨드 패턴 기초](../design-pattern/command-pattern-basics.md)
- [Command Pattern, Undo, Queue](../design-pattern/command-pattern-undo-queue.md)
- [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: message queue basics, what is message queue, beginner message queue, 메시지 큐 입문, message queue 뭐예요, 왜 메시지 큐를 써요, 언제 rest 대신 queue, producer consumer 기초, pub sub랑 queue 차이, 큐에 넣으면 끝인가요, 왜 바로 처리하지 않고 큐에 넣나요, queue vs bfs, queue vs command queue, queue가 왜 알고리즘이랑 시스템 설계 둘 다 나와요, 처음 메시지 큐 헷갈려요

---

## 처음 헷갈리는 `queue` 비교

처음에는 `queue`라는 단어보다 "어디에서 누구를 기다리게 하려는가"를 먼저 자르면 안전하다.

| 보이는 단어 | 초심자용 짧은 해석 | 먼저 볼 문서 | 아직 첫 클릭으로 올리지 않는 것 |
|---|---|---|---|
| `BFS`, `visited`, `최소 이동 횟수` | 탐색 순서를 queue에 담는 알고리즘 질문 | [알고리즘 README - BFS, Queue, Map 먼저 분리하기](../algorithm/README.md#bfs-queue-map-먼저-분리하기) | broker, consumer lag, DLQ |
| `undo`, `redo`, `작업 이력`, `명령 재실행` | 실행 요청을 객체로 쌓는 설계 질문 | [커맨드 패턴 기초](../design-pattern/command-pattern-basics.md) | topic 파티션, 재처리 인프라 |
| `왜 어떤 요청은 API로 끝내고 어떤 요청은 큐로 보내요?`, `처음 배우는데 queue를 언제 써요?` | direct API와 후처리 queue 경계를 고르는 시스템 질문 | [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md) | backlog tuning, watermark, replay repair |
| `producer`, `consumer`, `broker`, `후처리`, `비동기` | 서비스 사이 handoff를 분리하는 시스템 질문 | 이 문서 | cutover, backlog tuning, replay repair |

- mental model: 알고리즘 queue는 같은 프로세스 안에서 `탐색 순서`를 관리하고, Command queue는 같은 애플리케이션 안에서 `실행 요청`을 미루며, 메시지 큐는 서비스 사이 `전달 경계`를 분리한다.
- misconception guard: `큐에 넣었다`가 곧 `업무 완료`는 아니다. 보통은 전달을 시작했다는 뜻이고, 실제 완료는 consumer 성공까지 따로 확인해야 한다.
- safe next step: 아직 `왜 direct API 대신 queue를 두는지`를 한 문장으로 못 말하면 DLQ, replay, watermark 같은 운영 심화보다 `[커맨드 패턴 기초 -> Per-Key Queue vs Direct API Primer -> 이 문서]` 3칸까지만 읽고 멈춘다.

## 핵심 개념

메시지 큐는 "메시지를 임시로 담아두는 창고"다. 생산자(Producer)가 메시지를 큐에 넣으면, 소비자(Consumer)가 자신의 속도에 맞게 꺼내 처리한다.

입문자가 자주 헷갈리는 지점은 **왜 직접 API 호출(REST)이 아닌 큐를 써야 하는가**이다.

먼저 아래 두 문장을 분리해서 이해하면 훨씬 덜 헷갈린다.

- 응답 마감시간: 사용자가 지금 기다리는 결과를 돌려줘야 하는 시점
- 작업 완료시간: 이메일 발송, 알림 생성처럼 나중에 끝나도 되는 시점

직접 호출 방식의 문제:

- 소비자 서비스가 느리거나 다운되면 생산자 서비스도 블록된다.
- 갑자기 트래픽이 몰리면 소비자가 감당하지 못해 에러가 발생한다.
- 두 서비스의 배포 일정을 맞춰야 한다.

메시지 큐를 두면 생산자는 큐에 넣고 바로 다음 일로 넘어간다. 소비자는 자신의 속도로 처리한다.

처음에는 아래 두 상태를 꼭 분리해서 본다.

- `큐 적재 성공`: broker가 메시지를 받았다는 뜻
- `업무 처리 완료`: consumer가 실제 일을 끝냈다는 뜻

초보자가 `큐에 넣었는데 왜 메일이 아직 안 와요?`에서 막히는 이유는 보통 이 둘을 같은 완료로 보기 때문이다.

---

## 한눈에 보기

```text
생산자 A  ─┐
생산자 B  ─┼──> [메시지 큐] ──> 소비자 1
생산자 C  ─┘              └──> 소비자 2
```

핵심 개념 비교:

| 개념 | 설명 |
|---|---|
| Producer | 메시지를 큐에 넣는 쪽 |
| Consumer | 큐에서 메시지를 꺼내 처리하는 쪽 |
| Broker | 큐를 관리하는 서버 |
| Topic/Queue | 메시지가 쌓이는 논리적 공간 |

직접 호출과 큐를 초보자 기준으로 비교하면:

| 질문 | 동기 직접 호출 | 큐 기반 비동기 |
|---|---|---|
| 생산자가 소비자 응답을 기다리나 | 기다린다 | 보통 기다리지 않는다 |
| 소비자가 느릴 때 생산자 영향 | 바로 받는다 | 큐가 완충한다 |
| 사용자 응답은 빨라지나 | 소비자 지연 영향을 크게 받는다 | 후처리를 분리하면 보통 빨라진다 |
| 어디까지 완료로 볼지 판단 | 호출 성공 여부로 단순화되기 쉽다 | "큐 적재 성공"과 "업무 완료"를 분리해야 한다 |

`queue`가 보여도 "이걸 cache 대신 쓰는 건가?"가 바로 안 풀리면 [Queue vs Cache vs DB Decision Drill](./queue-vs-cache-vs-db-decision-drill.md)로 잠깐 돌아가 `정답 저장 / 빠른 재사용 / 나중 처리` 세 칸부터 다시 고정하는 편이 안전하다.

## 1분 예시: 주문 성공과 메일 발송은 완료 시점이 다르다

```text
Client -> Order API -> DB에 주문 저장 -> 201 Created
                        \
                         -> Queue(order.created) -> Mail Worker -> 메일 발송
```

이 흐름에서:

- 주문 성공은 보통 `DB 저장 + 응답 반환` 시점에 먼저 확정된다.
- 메일 발송은 queue 뒤에서 조금 늦게 끝나도 된다.

즉, queue의 핵심 가치는 "모든 걸 더 빨리 끝내는 것"보다 **사용자가 기다리는 경로와 나중에 끝나도 되는 경로를 분리하는 것**에 가깝다.

---

## 상세 분해

- **비동기 처리**: 생산자는 소비자의 응답을 기다리지 않는다. 주문 생성 API가 이메일 발송 서비스를 직접 호출하는 대신 큐에 이벤트를 넣으면, 이메일 서비스는 자신의 속도로 처리한다.
- **버퍼링**: 트래픽 피크에 메시지가 큐에 쌓이고, 소비자는 처리 가능한 속도로 꺼내간다. 소비자 서버가 다운돼도 메시지는 큐에 보존된다.
- **Pub/Sub 패턴**: 한 메시지를 여러 소비자가 동시에 받는 방식이다. 주문 완료 이벤트를 이메일 서비스, 재고 서비스, 포인트 서비스가 각자 수신한다.
- **Point-to-Point 패턴**: 메시지를 소비자 하나만 받는 방식이다. 작업 큐(Job Queue)에서 주로 쓴다.

---

## 흔한 오해와 함정

- **"메시지 큐를 쓰면 모든 통신이 비동기가 된다"**: 동기 응답이 반드시 필요한 흐름(결제 결과 즉시 반환 등)에는 맞지 않는다. 큐는 응답이 즉시 필요하지 않은 흐름에 적합하다.
- **"큐에 넣었으니 비즈니스도 끝났다"**: 보통 아니다. 큐 적재 성공은 전달 시작 신호이고, 실제 완료는 consumer 작업 성공까지 봐야 한다.
- **"메시지가 큐에 들어가면 무조건 처리된다"**: 보통 아니다. 실패한 메시지를 어떻게 재시도하고 어디까지 복구할지는 제품과 도구 설정에 따라 다르다. 이 문서에서는 `큐 적재 성공 != 업무 완료`까지만 먼저 잡고, 자세한 복구 흐름은 후속 문서로 넘긴다.
- **"큐를 쓰면 순서가 자동으로 보장된다"**: 보통 아니다. 순서는 큐 제품과 소비 방식에 따라 달라질 수 있으므로, 초보자는 먼저 `순서가 정말 중요한 작업인가`부터 구분하는 편이 안전하다.

처음에는 DLQ나 파티션 세부보다 아래 질문이 먼저다.

1. 사용자가 지금 결과를 알아야 하나?
2. 조금 늦어도 되지만 retry와 분리가 더 중요한가?
3. 같은 key의 작업을 한 줄로 처리해야 하나?

이 세 질문을 먼저 자르면 queue를 붙이는 이유가 훨씬 덜 추상적이다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 주문 처리에서 이메일 발송을 분리하는 것이다.

1. 사용자가 주문을 완료하면 주문 서비스가 `order.created` 이벤트를 큐에 넣는다.
2. 주문 API는 바로 `201 Created`를 반환하고, 이메일 발송을 기다리지 않는다.
3. 이메일 서비스가 큐에서 이벤트를 꺼내 발송을 처리한다.
4. 이메일 서버가 일시적으로 다운돼도 메시지는 큐에 보존되고, 복구 후 처리된다.
5. 같은 이벤트가 재전달될 수 있으므로 consumer는 `event_id` 기준 dedup을 둔다.

도구 이름은 RabbitMQ, Kafka처럼 여러 선택지가 있지만, 입문 단계에서는 제품별 옵션보다 `응답 경로와 후처리 경로를 분리한다`는 구조를 먼저 이해하면 충분하다.

처음 읽은 뒤 바로 다음 한 칸은 보통 아래 둘 중 하나다.

- `지금 direct API로 끝낼지 queue로 보낼지`가 남으면 [Per-Key Queue vs Direct API Primer](./per-key-queue-vs-direct-api-primer.md)
- `중복 처리와 retry가 왜 같이 나오는지`가 남으면 [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)

---

## 더 깊이 가려면

- 큐가 app/cache/db와 어떤 관계인지 먼저 보고 싶다면 [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- sync/async 경계와 eventual consistency를 주문 흐름으로 묶어 보고 싶다면 [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- retry owner와 폭증 방지 기준을 보고 싶다면 [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
- 멱등 키, dedup window, replay-safe 처리까지 설계하려면 [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md) — 메시징과 캐시, 관측성의 실무 연결 포인트
- [System Design Foundations](./system-design-foundations.md) — 큐가 전체 아키텍처에서 어떤 위치에 놓이는지

---

## 면접/시니어 질문 미리보기

> Q: 메시지 큐를 쓰면 어떤 이점이 있나요?
> 의도: 비동기 처리와 디커플링 개념 이해 확인
> 핵심: 생산자와 소비자를 분리해 독립 배포와 독립 확장이 가능하고, 트래픽 피크를 큐로 흡수해 소비자 과부하를 막는다.

> Q: Pub/Sub과 Point-to-Point 큐의 차이는 무엇인가요?
> 의도: 메시지 전달 패턴 구분 능력 확인
> 핵심: Pub/Sub은 하나의 메시지를 여러 소비자가 받고, Point-to-Point는 메시지를 소비자 하나만 가져간다.

> Q: 소비자가 메시지 처리에 실패하면 어떻게 보나요?
> 의도: `큐 적재`와 `업무 완료`를 분리하는지 확인
> 핵심: 실패 재시도와 격리 방식은 도구마다 다르지만, 중요한 것은 적재 성공만으로 비즈니스 완료를 선언하지 않는다는 점이다.

---

## 한 줄 정리

메시지 큐는 `지금 응답할 일`과 `나중에 처리할 일`을 분리해 생산자와 소비자의 속도를 떼어 놓는 handoff 레이어다.
