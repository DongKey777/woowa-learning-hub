# Bulk Helper Ports vs Query Model Separation

> 한 줄 요약: `findByIds` helper port는 "하나의 command/use case가 판단 재료를 한 번에 모으는" 도구이고, dedicated query repository/read model은 "읽기 화면 자체가 별도 제품"이 되었을 때 꺼내는 더 안전한 다음 단계다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: bulk helper ports vs query model separation basics, bulk helper ports vs query model separation beginner, bulk helper ports vs query model separation intro, software engineering basics, beginner software engineering, 처음 배우는데 bulk helper ports vs query model separation, bulk helper ports vs query model separation 입문, bulk helper ports vs query model separation 기초, what is bulk helper ports vs query model separation, how to bulk helper ports vs query model separation
<details>
<summary>Table of Contents</summary>

- [왜 이 둘이 자주 헷갈리는가](#왜-이-둘이-자주-헷갈리는가)
- [먼저 떠올릴 그림](#먼저-떠올릴-그림)
- [`findByIds` helper port만으로 충분한 경우](#findbyids-helper-port만으로-충분한-경우)
- [Dedicated query repository/read model이 더 안전한 경우](#dedicated-query-repositoryread-model이-더-안전한-경우)
- [짧은 비교 표](#짧은-비교-표)
- [예시 1: 알림 발송 준비 데이터는 helper port로 끝낸다](#예시-1-알림-발송-준비-데이터는-helper-port로-끝낸다)
- [예시 2: 관리자 주문 목록은 query repository로 분리한다](#예시-2-관리자-주문-목록은-query-repository로-분리한다)
- [helper port에서 query model로 넘어가야 하는 냄새](#helper-port에서-query-model로-넘어가야-하는-냄새)
- [자주 하는 오해](#자주-하는-오해)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: Bulk Helper Ports vs Query Model Separation](./README.md#bulk-helper-ports-vs-query-model-separation)
> - [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
> - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
> - [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md)
> - [Query Model Separation for Read-Heavy APIs](./query-model-separation-read-heavy-apis.md)
> - [Helper Snapshot Bloat Vs Response DTO Separation](./helper-snapshot-bloat-vs-response-dto-separation.md)
> - [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
> - [JPA Lazy Loading and N+1 Boundary Smells](./jpa-lazy-loading-n-plus-one-boundary-smells.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
>
> retrieval-anchor-keywords:
> - bulk helper ports vs query model separation
> - findByIds helper port
> - helper port vs query repository
> - bulk helper port vs read model
> - support query vs dedicated query repository
> - query repository next step
> - cqrs lite beginner boundary
> - command support query
> - list search query repository
> - projection repository vs helper port
> - read model separation same database
> - helper snapshot smell
> - screen query hidden in helper port
> - pagination sort filter query repository
> - findByIds vs search condition
> - read side projection boundary
> - when to split query repository
> - beginner query model separation
> - helper snapshot vs response dto
> - command support data vs api response

## 왜 이 둘이 자주 헷갈리는가

둘 다 "읽기"를 다루기 때문에 이름만 보면 비슷해 보인다.

- `findByIds(List<UserId>)`도 조회다
- `OrderQueryRepository.findSummaries(...)`도 조회다

그래서 초심자는 종종 이렇게 생각한다.

- "조회가 복잡해졌으니 이제 CQRS-lite인가?"
- "bulk helper port를 만들었으니 이미 query model을 분리한 건가?"

하지만 둘이 해결하는 질문은 다르다.

- helper port는 **기존 command/use case가 판단할 재료를 빨리 모으는 문제**를 푼다
- query repository/read model은 **읽기 화면과 검색 자체를 별도 경로로 다루는 문제**를 푼다

즉 둘은 경쟁 관계라기보다, 서로 다른 시점의 안전한 선택지다.

## 먼저 떠올릴 그림

초심자 기준으로는 이 두 문장을 먼저 기억하면 된다.

- **이미 처리할 ID를 알고 있고, 판단에 필요한 보조 데이터만 모으는 것**이면 helper port
- **어떤 ID를 보여줄지부터 읽기 경로가 결정해야 하는 것**이면 query repository

짧은 예로 보면 차이가 더 선명하다.

```java
Map<UserId, ContactSnapshot> contacts = userContactQueryPort.findByIds(userIds);
Page<OrderSummaryView> page = orderQueryRepository.findSummaries(condition, pageable);
```

첫 줄은:

- 이미 `userIds`가 있다
- 목적은 command가 연락처를 참고해 판단하는 것이다

둘째 줄은:

- 어떤 주문을 보여줄지 `condition`과 `pageable`이 정한다
- 목적은 화면/검색 결과를 읽기 좋게 반환하는 것이다

즉 helper port는 보통 **lookup**, query repository는 보통 **search/list/detail** 쪽에 가깝다.

## `findByIds` helper port만으로 충분한 경우

아래 조건이면 dedicated query model까지 가지 않아도 되는 경우가 많다.

### 1. 읽기가 command를 돕는 역할이다

- 알림 발송 전에 사용자 연락처를 모은다
- 주문 취소 전에 결제 상태 snapshot을 읽는다
- 배송 재확인 전에 운송장 상태를 bulk 조회한다

핵심은 읽기가 **단독 제품이 아니라 기존 유스케이스의 입력 보강**이라는 점이다.

### 2. 입력이 이미 정해진 ID나 고정 lookup key다

- `findByIds(List<UserId>)`
- `fetchStatuses(List<TrackingNo>)`
- `loadSnapshots(List<OrderId>)`

이때 읽기 경로는 "무엇을 보여줄까"보다 "이미 정해진 대상에 대해 어떤 참고값이 필요할까"에 답한다.

### 3. 반환 타입이 lookup 성격을 가진다

안전한 helper port는 보통 이런 모양이다.

- `Map<Id, Snapshot>`
- `List<Snapshot>`이더라도 item lookup 중심
- 화면 전용 row나 page보다 command 보조 데이터에 가깝다

즉 반환 타입이 `DashboardRow`, `AdminCardView`, `SearchResultPage`보다 `ContactSnapshot`, `PaymentSnapshot` 쪽에 가까우면 helper port일 가능성이 높다.

### 4. 규칙, 실패, 재시도 단위는 여전히 command/item 쪽에 있다

- 누가 전송 가능한지는 application service가 판단한다
- 누가 취소 가능한지도 domain/application이 판단한다
- 실패를 다시 실행할 때도 item이나 command 단위로 설명한다

읽기 helper는 데이터를 모아 주기만 하고, 실제 결정은 여전히 안쪽에서 한다.

## Dedicated query repository/read model이 더 안전한 경우

반대로 아래 신호가 보이면 helper port를 조금씩 늘리기보다 dedicated query repository를 꺼내는 편이 안전하다.

### 1. 읽기 경로가 "어떤 ID를 보여줄지"부터 결정한다

- 관리자 목록에서 기간, 상태, 담당자 조건으로 검색한다
- 대시보드에서 통계와 요약 수치를 보여 준다
- 목록, 상세, 검색 결과가 서로 다른 projection을 요구한다

이때는 더 이상 "이미 정해진 ID의 lookup"이 아니다.
읽기 경로 자체가 독립된 책임이 되었다.

### 2. pagination, sorting, filtering, aggregation이 중요하다

`findByIds` helper port는 보통 정해진 집합 조회에 잘 맞는다.
하지만 아래 요구가 커지면 query repository 쪽이 자연스럽다.

- 페이지네이션
- 정렬
- 복합 검색 조건
- 집계 값, 합계, 카운트
- 목록/상세별 projection 최적화

이 요구는 command 보조 조회보다 **화면/조회 제품 설계**에 가깝다.

### 3. helper snapshot이 점점 화면 DTO처럼 비대해진다

처음엔 `ContactSnapshot` 하나로 충분했는데, 시간이 지나며 이런 식이 되면 위험 신호다.

- `teamName`
- `couponCount`
- `lastOrderAt`
- `badgeLabel`
- `highlightColor`

즉 command 판단용 snapshot이 아니라 화면용 projection이 helper port 안으로 숨어들기 시작한 것이다.

### 4. controller나 query service가 helper port 여러 개를 조립해 화면을 만든다

아래 구조가 반복되면 dedicated query repository를 검토할 시점이다.

- 먼저 ID 목록을 찾는다
- 여러 helper port로 `findByIds(...)`를 반복한다
- controller/service에서 join 비슷한 조립을 한다
- 최종적으로 목록 row나 카드 view를 만든다

이건 helper port가 나쁜 게 아니라, **읽기 전용 조립 책임이 이제 별도 경계가 필요하다**는 뜻이다.

### 5. 더 안전한 다음 단계는 보통 "같은 DB 위 query repository"다

초심자가 자주 오해하는 부분이 있다.

- dedicated query repository를 꺼낸다고 곧바로 이벤트 소싱을 하는 것은 아니다
- read model을 분리한다고 곧바로 다른 DB를 도입하는 것도 아니다

처음 안전한 다음 단계는 대개 이것이다.

1. 같은 애플리케이션 안에 `OrderQueryRepository`를 추가한다.
2. 목록/상세/search 전용 projection을 분리한다.
3. 정말로 scale, freshness, storage 분리가 필요할 때만 별도 read store를 고민한다.

## 짧은 비교 표

| 질문 | `findByIds` helper port | dedicated query repository/read model |
|---|---|---|
| 주로 누구를 돕나 | command/use case | 목록/상세/검색 API |
| 입력 모양 | 이미 아는 ID, 고정 lookup key | 검색 조건, 정렬, 페이지, 집계 기준 |
| 반환 모양 | `Map<Id, Snapshot>` 같은 보조 데이터 | `View`, `Page<View>`, projection |
| 규칙 판단은 어디 있나 | application/domain 쪽 | 읽기 경로는 보통 read-only |
| 잘 맞는 상황 | 조회 fan-out만 줄이고 싶다 | 읽기 경로 자체가 복잡하다 |
| 넘어가야 하는 신호 | snapshot이 화면 필드로 비대해진다 | 목록/상세/query 책임을 독립 관리한다 |

짧게 외우면 이렇다.

- **ID는 이미 있고 재료만 모으면 된다**면 helper port
- **무엇을 보여줄지부터 읽기가 결정한다**면 query repository

## 예시 1: 알림 발송 준비 데이터는 helper port로 끝낸다

휴면 해제 알림을 여러 사용자에게 보내야 한다고 하자.

- 발송 가능 여부 판단은 사용자별로 다르다
- 중복 발송 방지도 사용자별로 다르다
- 다만 연락처 조회를 한 명씩 하면 너무 느리다

이때는 helper port가 잘 맞는다.

```java
public interface UserContactQueryPort {
    Map<UserId, ContactSnapshot> findByIds(List<UserId> userIds);
}

@Service
public class SendDormantReminderService {
    private final UserContactQueryPort userContactQueryPort;
    private final ReminderPolicy reminderPolicy;
    private final NotificationGateway notificationGateway;

    public void send(List<UserId> userIds) {
        Map<UserId, ContactSnapshot> contacts = userContactQueryPort.findByIds(userIds);

        for (UserId userId : userIds) {
            ContactSnapshot contact = contacts.get(userId);
            if (reminderPolicy.canSend(userId, contact)) {
                notificationGateway.send(ReminderMessage.of(userId, contact));
            }
        }
    }
}
```

여기서 읽기의 역할은:

- command가 판단할 재료를 모은다
- 읽기 결과를 화면으로 직접 노출하지 않는다
- 실패/재시도 설명도 여전히 사용자 단위다

즉 query model separation까지 갈 이유가 아직 없다.

## 예시 2: 관리자 주문 목록은 query repository로 분리한다

이번에는 관리자 화면에서 주문 목록을 보여 준다고 하자.

- 기간, 상태, 고객명으로 검색한다
- 총액과 아이템 수를 함께 보여 준다
- 페이지네이션과 정렬이 필요하다
- 목록과 상세가 서로 다른 projection을 쓴다

이때는 helper port보다 query repository가 자연스럽다.

```java
public interface OrderQueryRepository {
    Page<OrderSummaryView> findSummaries(
            OrderSearchCondition condition,
            Pageable pageable
    );
}

public record OrderSummaryView(
        Long orderId,
        String customerName,
        String status,
        int itemCount,
        BigDecimal totalPrice
) {
}

@Service
@Transactional(readOnly = true)
public class OrderQueryService {
    private final OrderQueryRepository orderQueryRepository;

    public Page<OrderSummaryView> findSummaries(
            OrderSearchCondition condition,
            Pageable pageable
    ) {
        return orderQueryRepository.findSummaries(condition, pageable);
    }
}
```

이 구조가 더 안전한 이유는:

- 검색/정렬/페이지 책임이 읽기 경계에 모인다
- write aggregate를 화면 요구에 맞춰 늘리지 않아도 된다
- helper port 여러 개를 controller가 조립하는 우회를 막는다

## helper port에서 query model로 넘어가야 하는 냄새

아래 신호가 2~3개 이상 겹치면 dedicated query repository를 검토할 시점이다.

- helper port 이름이 `findDashboardRowsByIds`, `findCardsByIds`, `findSearchResultsByIds`처럼 이미 화면 언어를 말한다
- `Snapshot` 하나가 점점 커져서 사실상 목록 row DTO 역할을 한다
- controller/query service가 helper port 여러 개를 불러 직접 join한다
- 먼저 ID를 찾고, 다시 `findByIds`를 반복하는 우회 쿼리가 많다
- pagination/sort/filter를 helper port 바깥에서 임시로 구현한다
- 같은 읽기 projection을 여러 화면이 반복해서 원한다
- write repository보다 query helper가 더 자주 바뀐다

이 시점에는 `findByIds`를 더 늘리는 것보다, query repository와 projection을 한 번 세우는 편이 장기적으로 단순하다.

## 자주 하는 오해

### "`findByIds`가 보이면 이미 CQRS-lite 아닌가요?"

아니다.
helper port는 command를 돕는 조회일 수 있다.
핵심은 조회가 독립 read path인지, 기존 유스케이스 보조 수단인지를 구분하는 것이다.

### "query repository를 쓰려면 다른 DB가 꼭 있어야 하나요?"

아니다.
같은 DB, 같은 스키마 위에서도 query repository와 projection은 충분히 분리할 수 있다.

### "helper port는 projection을 쓰면 안 되나요?"

그렇지 않다.
helper port 내부 구현이 projection SQL을 쓰는 건 괜찮다.
중요한 것은 port 계약이 command 보조 조회인지, 화면 전용 읽기 계약인지다.

### "query repository가 생기면 write repository는 없어지나요?"

아니다.
write repository는 aggregate 저장/복원 책임을 유지하고, query repository는 읽기 책임을 맡는다.

## 기억할 기준

- **이미 정해진 ID를 빠르게 조회해 command 판단을 돕는 것**이면 `findByIds` helper port가 먼저다.
- **목록/상세/검색이 무엇을 보여줄지 스스로 결정하는 것**이면 dedicated query repository가 더 안전하다.
- helper snapshot이 화면 projection처럼 커지기 시작하면 "조금 더 참자"보다 "읽기 경계를 세우자"가 낫다.
- 초심자 기준의 안전한 다음 단계는 보통 `같은 DB 위 query repository`이고, 별도 read store는 그 다음 문제다.

## 한 줄 정리

`findByIds` helper port는 "하나의 command/use case가 판단 재료를 한 번에 모으는" 도구이고, dedicated query repository/read model은 "읽기 화면 자체가 별도 제품"이 되었을 때 꺼내는 더 안전한 다음 단계다.
