# Service Contract Smell Cards

> 한 줄 요약: service 메서드 시그니처에 `ResponseEntity`, `Pageable`, `MultipartFile`, `OrderEntity` 같은 타입이 보이면 "유스케이스 계약" 대신 웹/프레임워크/영속 세부가 새고 있는지 먼저 의심하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Service 계층 기초](./service-layer-basics.md)
- [Entity Leakage Review Checklist](./entity-leakage-review-checklist.md)
- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- [software-engineering 카테고리 인덱스](./README.md)
- [spring request pipeline / bean container 입문](../spring/spring-request-pipeline-bean-container-foundations-primer.md)

retrieval-anchor-keywords: service contract smell, service contract basics, service signature smell, service method exposes framework type, responseentity in service, pageable in service, multipartfile in service, entity in service parameter, use case input output beginner, service boundary review, service contract primer, 처음 배우는데 service 계약 냄새, service가 jpa 타입을 안다, service가 spring 타입을 안다

## 핵심 개념

처음에는 어려운 용어보다 **"service는 유스케이스를 말해야 하고, controller/repository/adapter 세부를 그대로 말하면 경계가 흐려진다"**만 잡으면 된다.

service 메서드는 보통 아래 질문에 답해야 한다.

- 어떤 작업을 요청받았는가
- 작업 결과를 유스케이스 관점에서 무엇으로 돌려주는가

반대로 아래 질문에 답하기 시작하면 냄새가 난다.

- HTTP 응답 코드는 무엇인가
- Spring Data paging 객체를 그대로 어떻게 넘길까
- JPA entity를 그대로 수정할까
- 업로드 프레임워크 타입을 서비스가 직접 알아야 하나

짧게 외우면 이렇다.

- controller는 웹 입력/응답을 다룬다
- service는 작업 의도와 결과를 다룬다
- adapter/repository는 저장·프레임워크 세부를 다룬다

## 한눈에 보기

| 시그니처에서 보인 타입 | 보통 무슨 냄새인가 | 더 안전한 기본값 |
|---|---|---|
| `ResponseEntity<T>` | service가 HTTP 응답 책임까지 먹고 있다 | `Result DTO`, `void`, 상태 enum |
| `Pageable`, `Sort`, `Page<T>` | 유스케이스보다 Spring Data API가 앞에 나온다 | query DTO, page request value, query result |
| `MultipartFile` | 웹 업로드 어댑터 타입이 안쪽으로 들어왔다 | `UploadImageCommand`, 파일 내용/value object |
| `OrderEntity`, `MemberJpaEntity` | 저장 모델이 유스케이스 계약을 대신한다 | `OrderId`, command DTO, domain object |
| `HttpServletRequest`, `Authentication` | request/security 프레임워크 문맥이 안쪽으로 샌다 | 필요한 값만 추출한 command |

핵심 판단 기준은 타입 이름이 멋진가가 아니라, **그 타입이 어느 계층 질문에 답하는가**다.

## 냄새 카드 1: 웹 타입이 service에 보인다

아래 시그니처는 초심자 PR에서 자주 보이는 패턴이다.

```java
public ResponseEntity<OrderResponse> createOrder(CreateOrderRequest request) { ... }
public void uploadProfile(MultipartFile file) { ... }
```

이 경우 service가 벌써 두 가지를 같이 안다.

- 웹 요청/응답 포맷
- 유스케이스 실행

처음 대응은 작게 해도 된다.

- `CreateOrderRequest`는 controller에서 `CreateOrderCommand`로 바꾼다
- service는 `OrderResult`나 `OrderId`를 돌려준다
- `ResponseEntity`는 controller가 만든다
- `MultipartFile`은 controller/adapter에서 읽고 service에는 필요한 내용만 넘긴다

즉 service 메서드 이름은 `createOrder`, `uploadProfileImage`처럼 유스케이스를 말하고, 타입도 그 질문에 맞춰 좁히는 편이 낫다.

## 냄새 카드 2: persistence 타입이 service에 보인다

아래 시그니처도 경계가 자주 무너지는 지점이다.

```java
public OrderEntity approve(OrderEntity orderEntity) { ... }
public Page<OrderEntity> findAll(Pageable pageable) { ... }
```

이 시그니처는 service가 이미 저장 세부를 직접 안다.

- dirty checking이나 영속 상태를 은근히 전제한다
- 조회 기술 선택이 유스케이스 계약으로 굳는다
- 테스트에서도 `Pageable`, `OrderEntity`를 같이 세팅해야 해서 의미가 흐려진다

더 안전한 출발점은 아래 쪽이다.

```java
public ApproveOrderResult approve(ApproveOrderCommand command) { ... }
public OrderPageResult findOrders(FindOrdersQuery query) { ... }
```

여기서 paging이 필요 없다가 아니라, **paging 프레임워크 타입을 service 계약의 언어로 바로 쓰지 않는다**는 점이 핵심이다.

## 짧은 before / after 카드

| before | 왜 읽기 어려운가 | after |
|---|---|---|
| `cancel(ResponseEntity<OrderEntity> order)` | HTTP와 JPA가 한 메서드에 겹친다 | `cancel(CancelOrderCommand command)` |
| `search(Pageable pageable)` | Spring Data API가 유스케이스 이름을 덮는다 | `searchOrders(FindOrdersQuery query)` |
| `upload(MultipartFile file, Authentication auth)` | 웹/보안 문맥 없이는 재사용이 어렵다 | `uploadProfileImage(UploadProfileImageCommand command)` |
| `pay(OrderEntity order)` | 저장 모델이 작업 의도보다 먼저 보인다 | `pay(PayOrderCommand command)` |

초심자 기준에서는 after가 완벽하게 고급 설계여서 좋은 것이 아니다. **메서드 이름과 타입만 읽어도 "무슨 일을 하는지"가 먼저 보여서** 더 좋다.

## 자주 헷갈리는 지점

- "작은 프로젝트인데 service에 `Pageable` 정도는 괜찮지 않나요?"
  - 당장 동작은 하지만, service를 다른 진입점이나 테스트에서 읽을 때 Spring Data 의미를 같이 알아야 한다.
- "업로드는 결국 `MultipartFile`로 들어오는데 왜 바로 못 받나요?"
  - 들어오는 입구는 웹이지만, service는 "프로필 이미지를 바꾼다"는 작업을 재사용 가능하게 가져가는 쪽이 보통 더 안전하다.
- "service가 `Entity`를 받아야 수정이 쉬운 것 아닌가요?"
  - 수정 편의보다 계약 선명도가 먼저다. `orderId`, `command`, domain method가 보통 더 읽기 쉽다.
- "조회니까 `Page<OrderEntity>`를 그냥 반환해도 되지 않나요?"
  - 목록 컬럼, 조인, 직렬화 요구가 붙는 순간 읽기 모델이 금방 달라진다. query/result DTO가 흔들림을 줄인다.

## 실무에서 쓰는 모습

코드 리뷰에서는 긴 설명보다 아래 4문장 정도가 실제로 더 쓸모 있다.

- "`ResponseEntity`는 controller에서 만들고 service는 결과 DTO만 반환해 주세요."
- "`Pageable`을 그대로 받기보다 조회 의도를 담은 query 타입으로 좁혀 보세요."
- "`OrderEntity` 대신 `orderId`나 command를 받으면 JPA 세부 의존이 줄어듭니다."
- "`MultipartFile`은 웹 어댑터에서 읽고 service에는 필요한 값만 넘기는 편이 경계가 덜 섞입니다."

리뷰 순서도 단순하게 보면 된다.

1. service 메서드 파라미터를 본다
2. 반환 타입을 본다
3. Spring/JPA 타입이 이름에 보이는지 본다
4. 그 타입을 유스케이스 input/output 이름으로 바꿀 수 있는지 본다

## 더 깊이 가려면

- service 책임 기준을 먼저 다시 잡으려면: [Service 계층 기초](./service-layer-basics.md)
- `@Entity` 누수만 빠르게 체크하려면: [Entity Leakage Review Checklist](./entity-leakage-review-checklist.md)
- repository/service 경계에서 JPA 타입을 어떻게 끊는지 보려면: [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- request DTO, command, entity 흐름을 다시 보려면: [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)

## 면접/시니어 질문 미리보기

- "왜 service 계약에서 framework 타입을 줄이려고 하나요?"
  - 유스케이스 의미와 진입 기술 세부를 분리해 재사용성과 테스트 설명력을 높이기 위해서다.
- "항상 framework 타입을 완전히 숨겨야 하나요?"
  - 절대 규칙이라기보다 초심자 기본값이다. 경계가 흔들릴 때 먼저 줄이는 쪽이 안전하다.
- "paging이나 upload는 결국 framework 도움을 받는데 왜 감추나요?"
  - 감추는 목적은 기능 제거가 아니라, 그 세부가 service 계약 자체를 지배하지 않게 하려는 것이다.

## 한 줄 정리

service 메서드에서 `ResponseEntity`, `Pageable`, `MultipartFile`, `OrderEntity`가 먼저 보이면, 유스케이스 입력/출력 대신 웹·프레임워크·영속 세부가 계약을 덮고 있는지부터 의심하면 된다.
