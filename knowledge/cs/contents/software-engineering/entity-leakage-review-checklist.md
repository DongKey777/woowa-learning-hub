# Entity Leakage Review Checklist

> 한 줄 요약: 초심자 코드 리뷰에서 `@Entity`가 API DTO, service 계약, 모듈 경계를 넘어다니는지 빠르게 찾으려면 "밖으로 나가는 타입 이름"부터 보는 짧은 체크리스트가 가장 효율적이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
- [Service Contract Smell Cards](./service-contract-smell-cards.md)
- [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- [Module API DTO Patterns](./module-api-dto-patterns.md) - 모듈 간 `Entity` 노출을 `Command/Query/Result DTO`로 바꾸는 첫 입문
- [software-engineering 카테고리 인덱스](./README.md)
- [spring bean / request pipeline 입문](../spring/spring-request-pipeline-bean-container-foundations-primer.md)

retrieval-anchor-keywords: entity leakage review checklist, jpa entity leakage checklist, 코드리뷰에서 entity 누수, 엔티티를 response dto로 반환, service 계약에 entity 전달, module api entity 노출, beginner code review entity leak, entity를 dto로 바로 반환, service가 entity를 받는 코드리뷰, cross module entity leak, jpa entity boundary review, entity leakage basics, 처음 배우는데 entity 누수, 모듈 간 entity 노출 왜 안 돼요, module dto review basics

## 핵심 개념

처음 리뷰할 때는 어려운 용어보다 **"`@Entity`가 저장 계층 밖으로 나가는가?"**만 먼저 보면 된다. 특히 코드리뷰에서 "엔티티를 response DTO로 그냥 반환했나?", "service 계약에 entity를 그냥 넣었나?", "모듈 API로 entity가 새었나?"를 바로 체크하면 된다.

- Controller 밖 응답 타입에 `Entity`가 보이면 API 누수 가능성이 크다.
- Service 메서드 파라미터/반환 타입에 `Entity`가 보이면 유스케이스 계약 누수 가능성이 크다.
- 다른 모듈 공개 API에 `Entity`가 보이면 경계 누수 가능성이 크다. 이 경우 첫 다음 문서는 [Module API DTO Patterns](./module-api-dto-patterns.md)다.

짧게 외우면 이렇다.

- Entity는 저장 모양 쪽에 가깝다.
- DTO/Command/View는 경계 계약 쪽에 가깝다.
- 코드 리뷰에서는 "지금 이 타입이 어느 질문에 답하는가?"를 묻는다.

## 한눈에 보기

| 리뷰 위치 | 바로 찾을 신호 | 왜 위험한가 | 첫 대응 |
|---|---|---|---|
| Controller 응답 | `OrderEntity`, `List<UserEntity>` 반환 | DB 컬럼/LAZY/연관관계가 API 계약으로 굳는다 | `Response DTO`로 바꾼다 |
| Service 시그니처 | `create(OrderEntity entity)` | 웹 입력, 유스케이스 의미, 저장 세부가 한 번에 섞인다 | `Command`나 domain type으로 좁힌다 |
| 모듈 공개 API | `paymentApi.pay(OrderEntity order)` | 다른 모듈이 내부 JPA 구조를 알아야 한다 | `Command/Result DTO`로 바꾼다 |
| 공용 util/helper | `Entity`를 여기저기 재조합 | 저장 모델이 사실상 전역 모델이 된다 | 변환 위치를 adapter/assembler 한 곳으로 모은다 |

리뷰 순서도 단순하게 잡으면 된다.

1. 반환 타입부터 본다.
2. 파라미터 타입을 본다.
3. `Entity`가 패키지 경계를 넘는지 본다.

## 짧은 체크리스트

코드 리뷰에서 아래 6문항만 체크해도 대부분의 beginner 누수를 빨리 잡을 수 있다.

| 질문 | `예`면 의심할 것 | 보통 더 안전한 기본값 |
|---|---|---|
| Controller가 `Entity`를 그대로 반환하는가? | API 응답이 DB 구조에 묶임 | `Response DTO` |
| Request DTO를 바로 `Entity`로 저장하는가? | 웹 입력 형식이 저장 규칙을 밀어버림 | `Request DTO -> Command/Domain -> Entity` |
| Service 메서드가 `Entity`를 파라미터/반환 타입으로 쓰는가? | 유스케이스 계약이 JPA 세부를 안다 | `Command`, domain object, `Result DTO` |
| 다른 모듈 public API가 `Entity`를 받거나 돌려주는가? | cross-module 결합이 커짐 | `Command DTO`, `Query/Result DTO` |
| 코드 리뷰 코멘트가 "`Entity` 필드 하나만 더 응답에 노출하자"로 끝나는가? | 임시 편의가 API 계약으로 굳음 | 응답 전용 DTO 추가 |
| `Entity`에 직렬화/화면용 어노테이션이 계속 붙는가? | 저장 모델이 표현 모델 역할까지 먹고 있음 | 표현 책임을 DTO로 분리 |

한 문장으로 줄이면: **Entity가 "저장"이 아니라 "전달 계약" 역할까지 하고 있으면 누수 신호다.**

특히 마지막에서 두 번째 질문이 `예`라면, 여기서 누수 신호만 확인한 뒤 바로 [Module API DTO Patterns](./module-api-dto-patterns.md)로 넘어가서 어떤 `Command/Query/Result DTO`로 끊을지 고르면 된다.

## 흔한 누수 패턴 3개

### 1. API DTO로 새는 경우

```java
@GetMapping("/orders/{id}")
public OrderEntity findById(@PathVariable Long id) {
    return orderRepository.findById(id).orElseThrow();
}
```

이 코드는 짧지만 리뷰에서는 바로 세 가지를 물으면 된다.

- 이 응답이 진짜로 모든 엔티티 필드를 공개해야 하나?
- `member`, `lines` 같은 연관관계가 직렬화 시점에 안전한가?
- DB 컬럼이 바뀌면 API도 같이 흔들리지 않는가?

초심자 리뷰 코멘트 예시는 이 정도면 충분하다.

`OrderEntity`를 바로 응답으로 내보내기보다 `OrderResponse`로 필요한 필드만 고르면 API 계약과 JPA 구조를 분리하기 쉽습니다.

### 2. Service 계약으로 새는 경우

```java
public void approve(OrderEntity orderEntity) {
    orderEntity.setStatus(APPROVED);
}
```

여기서 문제는 "setter를 썼다"보다 **Service 계약이 이미 저장 모델을 알고 있다**는 점이다.

- Service가 JPA 영속 상태를 전제로 동작하기 쉽다.
- 배치/메시지/테스트에서 같은 유스케이스를 재사용하기 어려워진다.
- 규칙 설명이 `approve(OrderEntity)`보다 `approve(OrderId)` 또는 `ApproveOrderCommand`일 때 더 선명하다.

### 3. 모듈 경계로 새는 경우

```java
public interface PaymentApi {
    PaymentResult pay(OrderEntity order);
}
```

같은 코드베이스라도 이 시그니처는 위험하다.

- `payment` 모듈이 `order`의 JPA 구조를 같이 알아야 한다.
- `OrderEntity` 필드 구조 변경이 다른 모듈 컴파일 에러로 번진다.
- 조회/저장 최적화 세부가 public contract처럼 굳는다.

이 경우 기본값은 `PayOrderCommand`, `OrderPaymentView`, `PaymentResult` 같은 경계 전용 타입이다.

## 자주 헷갈리는 지점

- "작은 프로젝트인데 그냥 `Entity` 써도 되지 않나요?"
  - 한두 화면에서는 돌아가도, 응답 필드 추가와 조회 최적화가 시작되면 가장 먼저 흔들린다.
- "Service가 `Entity`를 받으면 코드가 덜 복잡한데요?"
  - 파일 수는 줄어도 계약이 흐려진다. 초심자 코드 리뷰에서는 "덜 복잡해 보이는가"보다 "변경 이유가 분리되는가"가 더 중요하다.
- "도메인 객체도 Entity 아닌가요?"
  - 문맥에 따라 다르다. 여기 체크리스트에서 말하는 것은 보통 JPA `@Entity` 같은 저장 모델 누수다.
- "읽기 전용 조회니까 `Entity` 반환해도 괜찮지 않나요?"
  - 목록/상세 요구는 자주 바뀌므로 보통 query/result DTO가 더 안전하다.

## 실무에서 쓰는 모습

초심자 코드 리뷰에서는 아래처럼 짧은 리뷰 문장으로 충분하다.

- API 쪽: "응답 계약은 `OrderResponse`로 고정하고 JPA 엔티티는 컨트롤러 밖에서 끊어 주세요."
- Service 쪽: "유스케이스 입력을 `ApproveOrderCommand`나 `orderId`로 좁히면 JPA 세부 의존이 줄어듭니다."
- 모듈 쪽: "다른 모듈에는 `OrderEntity` 대신 command/result DTO를 공개하는 편이 경계가 덜 새어요."

리뷰 우선순위도 보통 이 순서가 효율적이다.

1. Controller 반환 타입
2. Service 시그니처
3. 공개 API 시그니처
4. 변환 위치가 한 곳에 모여 있는지

## 더 깊이 가려면

- API/서비스/도메인까지 번진 누수 anti-pattern을 더 보려면: [Persistence Model Leakage Anti-Patterns](./persistence-model-leakage-anti-patterns.md)
- service 시그니처에서 `ResponseEntity`, `Pageable`, `MultipartFile`까지 같이 점검하려면: [Service Contract Smell Cards](./service-contract-smell-cards.md)
- DTO/VO/Entity 구분을 먼저 다시 잡으려면: [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- 모듈 경계 DTO 기본값을 더 보려면: [Module API DTO Patterns](./module-api-dto-patterns.md)
- repository adapter에서 매핑 책임을 어디서 끊는지 보려면: [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)

## 면접/시니어 질문 미리보기

- "JPA Entity를 API 응답으로 직접 반환하면 왜 위험한가요?"
  - API 계약이 DB 구조와 연관관계 전략에 묶이고, LAZY/직렬화 문제가 함께 따라오기 쉽기 때문이다.
- "Service 시그니처에서 Entity를 지우면 뭐가 좋아지나요?"
  - 유스케이스 계약이 입력 의도 중심으로 보이고, 저장 기술 교체 영향이 줄어든다.
- "모듈 경계에서는 왜 DTO를 기본값으로 두나요?"
  - 다른 모듈이 내부 aggregate/JPA 구조를 모르고도 협력하게 만들기 위해서다.

## 한 줄 정리

초심자 코드 리뷰에서 entity leakage를 찾는 가장 빠른 방법은 `@Entity`가 Controller 응답, Service 계약, 모듈 공개 API에 등장하는지부터 차례로 보는 것이다.
