---
schema_version: 3
title: Spring Data JPA save, persist, and merge State Transitions
concept_id: spring/data-jpa-save-persist-merge-state-transitions
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- data-jpa-save
- persist-merge-state
- transitions
- persist-vs-merge
aliases:
- Spring Data JPA save
- persist vs merge
- detached entity merge
- managed entity save unnecessary
- entity state transition
- isNew detection
- Persistable assigned id
- merge returns managed copy
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-persistence-context-flush-clear-detach-boundaries.md
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-open-session-in-view-tradeoffs.md
- contents/spring/spring-transaction-isolation-readonly-pitfalls.md
- contents/spring/spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md
expected_queries:
- Spring Data JPA save는 persist와 merge 중 무엇을 호출해?
- managed entity에 save를 다시 호출할 필요가 없는 이유는?
- merge는 detached 객체를 그대로 managed로 바꾸는 거야?
- assigned id나 Persistable을 쓰면 isNew 판단이 왜 중요해?
contextual_chunk_prefix: |
  이 문서는 Spring Data JPA repository.save가 entity 상태에 따라 persist 또는
  merge 의미로 갈리는 점을 deep dive한다. new/transient, managed, detached,
  removed, isNew detection, Persistable, assigned id, merge returns managed copy,
  dirty checking과 overwrite 위험을 설명한다.
---
# Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions

> 한 줄 요약: Spring Data JPA의 `save()`는 만능 저장 버튼이 아니라 엔티티가 new인지 detached인지에 따라 `persist`와 `merge` 의미가 갈리므로, 상태 전이를 모르면 불필요한 merge와 의도치 않은 값 덮어쓰기가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Open Session In View Trade-offs](./spring-open-session-in-view-tradeoffs.md)
> - [Spring Transaction Isolation / ReadOnly Pitfalls](./spring-transaction-isolation-readonly-pitfalls.md)
> - [Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)

retrieval-anchor-keywords: Spring Data JPA save, persist vs merge, detached entity merge, managed entity save unnecessary, entity state transition, isNew detection, Persistable, assigned id, merge returns managed copy

## 핵심 개념

Spring Data JPA를 쓰다 보면 `repository.save(entity)`를 거의 습관처럼 호출하기 쉽다.

하지만 JPA 관점에서 중요한 것은 메서드 이름이 아니라 **엔티티가 지금 어떤 상태인가**다.

- new/transient
- managed
- detached
- removed

여기서 핵심 차이는 다음이다.

- `persist`: 새 엔티티를 현재 영속성 컨텍스트에 붙인다
- `merge`: 전달한 객체를 그대로 붙이는 것이 아니라, 상태를 복사한 managed 인스턴스를 반환한다
- `save`: Spring Data JPA가 new 여부를 판단해 내부적으로 `persist` 또는 `merge`를 선택한다

즉 질문은 "저장할까?"가 아니라, **이 엔티티가 지금 누구의 관리 아래 있고, 어떤 state transition이 필요한가**다.

## 깊이 들어가기

### 1. managed 엔티티는 보통 `save()`가 없어도 flush 시 반영된다

트랜잭션 안에서 이미 조회한 managed 엔티티를 수정했다면, dirty checking으로 인해 flush 시점에 SQL이 나갈 수 있다.

```java
@Transactional
public void renameUser(Long id, String name) {
    User user = userRepository.findById(id).orElseThrow();
    user.rename(name);
}
```

이 코드는 `save()`를 안 불러도 반영될 수 있다.

그래서 managed 상태의 엔티티에 습관적으로 `save()`를 반복 호출하는 것은 종종 의미가 없다.

핵심은 Spring Data JPA를 "active record 스타일 저장 호출"로 보기보다, **영속성 컨텍스트와 dirty checking 위의 작업 단위**로 보는 것이다.

### 2. `merge`는 전달한 객체를 그대로 managed로 바꾸지 않는다

가장 많이 헷갈리는 포인트다.

```java
User detached = new User();
detached.setId(1L);
detached.rename("new-name");

User managed = entityManager.merge(detached);
```

이때 중요한 사실:

- `detached`가 managed가 되는 것이 아니다
- `managed`라는 다른 인스턴스가 현재 persistence context에 붙는다
- 이후 변경 추적은 `managed` 쪽에 붙는다

즉 merge를 쓰고도 여전히 detached 객체를 잡고 후속 수정하면 기대와 다르게 SQL이 안 나갈 수 있다.

### 3. Spring Data JPA `save()`는 new 여부 판단에 의존한다

`SimpleJpaRepository`는 대체로 엔티티가 new면 `persist`, 아니면 `merge`를 선택한다.

문제는 new 판단이 늘 직관적이지 않다는 점이다.

- 식별자가 `null`이면 보통 new로 본다
- assigned ID 전략이면 이미 ID가 있어도 실제론 new일 수 있다
- `Persistable` 구현체라면 `isNew()`가 판단을 바꾼다

즉 "ID가 있으니 update겠지"가 항상 맞지 않는다.

assigned ID나 복합 키를 쓰는 모델에서는 `save()`가 예상보다 merge로 기울 수 있고, 그 결과 insert/update 감각이 흔들릴 수 있다.

### 4. detached DTO merge는 값 덮어쓰기 사고를 부르기 쉽다

실무에서 자주 나오는 위험한 패턴은 아래와 비슷하다.

```java
User user = new User();
user.setId(command.id());
user.setNickname(command.nickname());
userRepository.save(user);
```

겉보기엔 "일부 필드만 수정" 같지만, 실제로는 detached 상태 객체를 merge하면서 누락된 값이 예상 밖으로 반영될 수 있다.

특히 다음이 위험하다.

- nullable 필드가 `null`로 덮어써짐
- 연관관계가 비어 있는 상태로 merge됨
- 버전/락 필드 감각이 흐려짐

보통 더 안전한 방향은 아래다.

- managed 엔티티를 먼저 조회한다
- 도메인 메서드로 필요한 필드만 바꾼다
- flush 시점에 반영되게 둔다

즉 patch update를 detached merge로 처리하는 것은 편해 보여도, **부분 수정 의도를 모델에 제대로 담지 못하기 쉽다**.

### 5. `save()`는 new/detached 경계를 숨겨 주지만, 그만큼 사고도 숨긴다

`save()`의 장점은 저장 API를 단순화한다는 점이다.

하지만 다음 경계를 가리기도 한다.

- 지금 persist가 일어나는가 merge가 일어나는가
- SQL이 언제 나가는가
- 지금 엔티티가 managed인지 detached인지

따라서 JPA를 깊게 쓸수록 `save()`를 "항상 호출하는 습관"보다, **현재 상태가 무엇인지 먼저 판단하는 습관**이 더 중요하다.

### 6. 테스트에서는 managed state가 `save` 오해를 더 키울 수 있다

테스트에서 같은 트랜잭션 안에서 엔티티를 다루면, managed 상태 덕분에 `save()`가 꼭 필요한 것처럼 보이거나 반대로 불필요한 merge가 숨어도 잘 드러나지 않을 수 있다.

예를 들어 repository 테스트에서:

- save 후 즉시 다시 읽으면 같은 영속성 컨텍스트에서 값이 보여 버림
- merge 후 detached 인스턴스를 계속 만져도 테스트는 이상해 보이지 않을 수 있음

그래서 save/persist/merge 의미를 확인하는 테스트는 flush/clear를 적절히 써서 **managed illusion을 걷어내는 것**이 좋다.

## 실전 시나리오

### 시나리오 1: update 코드인데 왜 전체 필드가 흔들리는 것 같나

detached 객체를 새로 만들어 `save()`했고, 내부적으로 merge가 일어나 누락 필드까지 의도치 않게 영향받았을 수 있다.

### 시나리오 2: `save()` 후 반환 객체와 원래 객체가 다르게 느껴진다

merge 경로였다면 반환값이 실제 managed 인스턴스일 수 있다.

원래 전달한 객체에 계속 의존하면 상태 추적이 어긋날 수 있다.

### 시나리오 3: assigned ID 엔티티가 insert 대신 이상한 merge 경로를 타는 것 같다

new 판단 기준과 `Persistable#isNew()` 구현 여부를 봐야 한다.

이건 repository API 문제라기보다 엔티티 상태 전이와 식별자 전략 문제다.

### 시나리오 4: service 안에서 조회 후 수정했는데 굳이 `save()`가 계속 붙어 있다

기능상 큰 문제는 아닐 수 있지만, 팀이 JPA를 "수정 후 저장 버튼"처럼 오해하고 있다는 신호일 수 있다.

## 코드로 보기

### managed 엔티티 수정

```java
@Transactional
public void changeStatus(Long orderId, OrderStatus status) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    order.changeStatus(status);
}
```

### detached merge

```java
@Transactional
public User updateDetached(User detachedUser) {
    return entityManager.merge(detachedUser);
}
```

### Spring Data `save()`

```java
User saved = userRepository.save(user);
```

이 호출은 내부적으로 `persist`일 수도 있고 `merge`일 수도 있다.

### assigned ID에서 new 판단 제어

```java
public class Coupon implements Persistable<String> {

    @Id
    private String id;

    @Transient
    private boolean isNew = true;

    @Override
    public String getId() {
        return id;
    }

    @Override
    public boolean isNew() {
        return isNew;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| managed 엔티티 조회 후 수정 | 의도가 분명하고 부분 수정에 안전하다 | 조회가 한 번 더 필요할 수 있다 | 일반적인 도메인 수정 |
| detached merge | 계층 간 전달이 단순해 보인다 | 값 덮어쓰기와 상태 혼동이 쉽다 | 제한적으로, 상태 의미를 분명히 알 때 |
| `save()` 습관적 호출 | 코드가 익숙해 보인다 | persist/merge 차이를 가린다 | 가급적 의식적으로 사용 |
| `Persistable`로 new 판단 제어 | assigned ID에서 정확도를 높인다 | 모델이 더 복잡해진다 | 식별자 전략상 필요할 때 |

핵심은 `save()`를 "항상 마지막에 부르는 의식"이 아니라, **현재 엔티티 상태 전이에 맞는 선택인지 점검하는 기준점**으로 보는 것이다.

## 꼬리질문

> Q: managed 엔티티를 수정할 때 `save()`가 꼭 필요하지 않은 이유는 무엇인가?
> 의도: dirty checking 이해 확인
> 핵심: 영속성 컨텍스트가 managed 상태 변화를 flush 시점에 반영할 수 있기 때문이다.

> Q: `merge()`의 가장 중요한 함정은 무엇인가?
> 의도: merge 반환 의미 확인
> 핵심: 전달한 객체를 그대로 붙이는 것이 아니라, 상태를 복사한 managed 인스턴스를 반환한다는 점이다.

> Q: Spring Data JPA `save()`가 insert/update를 어떻게 고르는가?
> 의도: new 판단 이해 확인
> 핵심: 엔티티가 new인지 여부를 보고 `persist` 또는 `merge` 경로를 선택한다.

> Q: detached 엔티티로 부분 수정을 구현하면 왜 위험한가?
> 의도: partial update semantics 이해 확인
> 핵심: 누락 필드와 연관관계까지 의도치 않게 merge될 수 있기 때문이다.

## 한 줄 정리

Spring Data JPA `save()`를 제대로 쓰려면 메서드 이름보다 먼저, 지금 엔티티가 new인지 managed인지 detached인지를 구분할 수 있어야 한다.
