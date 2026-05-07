---
schema_version: 3
title: Version Column Retry Walkthrough
concept_id: database/version-column-retry-walkthrough
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- optimistic-locking
- version-column
- retry
- spring
- conflict
aliases:
- version column retry walkthrough
- optimistic locking failure flow
- ObjectOptimisticLockingFailureException walkthrough
- stale object state retry
- version conflict user message
- rollback only optimistic lock
- update count 0 version column
- 409 conflict optimistic locking
- retry boundary optimistic lock
- other user already changed message
symptoms:
- version column optimistic locking 실패를 예외 한 줄이 아니라 UPDATE count 0, rollback-only, service response 흐름으로 이해해야 해
- ObjectOptimisticLockingFailureException 이후 같은 transaction 안에서 다시 시도하려 해
- 자동 retry와 409 conflict 사용자 메시지 중 무엇을 선택할지 service-layer에서 결정해야 해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/compare-and-set-version-columns
- database/spring-jpa-locking-example-guide
next_docs:
- database/spring-retry-proxy-boundary-pitfalls
- database/idempotent-transaction-retry-envelopes
- database/lost-update-detection-patterns
linked_paths:
- contents/database/compare-and-set-version-columns.md
- contents/database/spring-jpa-locking-example-guide.md
- contents/database/transaction-retry-serialization-failure-patterns.md
- contents/database/spring-retry-proxy-boundary-pitfalls.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/database/lost-update-detection-patterns.md
confusable_with:
- database/compare-and-set-version-columns
- database/spring-retry-proxy-boundary-pitfalls
- database/spring-jpa-locking-example-guide
forbidden_neighbors: []
expected_queries:
- @Version optimistic locking 실패는 update count 0에서 ObjectOptimisticLockingFailureException으로 어떻게 전파돼?
- version column conflict 이후 같은 transaction을 살리는 게 아니라 새 attempt나 409 conflict를 선택해야 하는 이유는?
- rollback-only optimistic lock 상태에서 retry loop를 돌리면 UnexpectedRollbackException이 생기는 흐름을 설명해줘
- 사용자에게 다른 사람이 먼저 수정했다는 409 conflict message를 낼지 자동 retry할지 어떻게 판단해?
- JPA version column retry boundary는 transactional service와 facade를 어떻게 나눠야 해?
contextual_chunk_prefix: |
  이 문서는 version column optimistic locking failure를 UPDATE WHERE version count 0, rollback-only transaction, retry facade, user conflict message로 추적하는 advanced playbook이다.
  ObjectOptimisticLockingFailureException, update count 0, 409 conflict optimistic locking 질문이 본 문서에 매핑된다.
---
# Version Column Retry Walkthrough

> 한 줄 요약: optimistic locking 실패는 `@Version` 예외 한 줄이 아니라, `UPDATE ... WHERE version = ?` 실패가 transaction rollback, service-layer 분기, 사용자 conflict 메시지까지 전파되는 전체 흐름으로 이해해야 한다.

**난이도: 🔴 Advanced**

관련 문서: [Compare-and-Set와 Version Columns](./compare-and-set-version-columns.md), [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md), [Spring Retry Proxy Boundary Pitfalls](./spring-retry-proxy-boundary-pitfalls.md), [Idempotent Transaction Retry Envelopes](./idempotent-transaction-retry-envelopes.md), [Lost Update Detection Patterns](./lost-update-detection-patterns.md)
retrieval-anchor-keywords: version column retry walkthrough, optimistic locking failure flow, optimistic lock failure propagation, objectoptimisticlockingfailureexception walkthrough, stale object state retry, version conflict user message, rollback only optimistic lock, update count 0 version column, 409 conflict optimistic locking, retry boundary optimistic lock, other user already changed message, stale write beginner guide, spring retry proxy boundary, outer transaction retry optimistic lock, unexpectedrollbackexception optimistic retry

## 핵심 개념

버전 컬럼 기반 optimistic locking은 "누가 먼저 저장했는가"를 **저장 시점**에 판정한다.  
중요한 것은 예외 이름보다 실패가 어디까지 번지는지다.

- DB는 `WHERE version = ?` 조건이 맞지 않으면 update count `0`을 돌려준다
- ORM/Spring은 이를 optimistic lock 예외로 번역할 수 있다
- 해당 transaction attempt는 rollback-only가 된다
- 그 바깥 계층이 "자동 retry", "409 conflict", "사용자에게 다시 불러오라고 안내" 중 하나를 선택한다

즉 version column은 단순 필드가 아니라, **한 번의 시도가 더 이상 유효하지 않다는 신호**다.

## 먼저 큰 흐름 잡기

아래 순서를 머리에 넣으면 beginner도 흐름을 놓치지 않는다.

1. 사용자가 수정 요청을 보낸다
2. 서비스가 row와 `version=7`을 읽는다
3. 다른 요청이 먼저 저장해서 `version=8`로 올린다
4. 내 요청이 `WHERE version = 7`로 update를 시도한다
5. update count가 `0`이어서 optimistic lock 예외가 난다
6. 현재 transaction은 버리고, 바깥 계층이 retry 또는 conflict 응답을 결정한다

핵심은 5번 이후다. 여기서 "같은 transaction 안에서 한 번 더"가 아니라 **새 attempt를 시작할지**를 판단해야 한다.

## 예제 코드: 서비스 코드까지 어떻게 전파되나

아래는 beginner가 보기 쉬운 전형적인 구조다.

### 1. 엔티티는 `@Version`으로 충돌 감지 지점을 가진다

```java
@Entity
public class Article {

    @Id
    private Long id;

    private String title;

    @Version
    private long version;

    public void rename(String newTitle) {
        this.title = newTitle;
    }
}
```

Hibernate/JPA는 flush 또는 commit 시점에 대략 아래 SQL을 만든다.

```sql
update article
   set title = ?,
       version = ?
 where id = ?
   and version = ?;
```

이 SQL에서 중요한 값은 결과 row count다.

- `1`: 내가 읽은 version이 아직 최신이었다
- `0`: 누군가 먼저 커밋해서 내 시도가 stale해졌다

### 2. `@Transactional` 서비스는 "한 번의 시도"만 책임진다

```java
@Service
@RequiredArgsConstructor
class ArticleTxService {

    private final ArticleRepository articleRepository;

    @Transactional
    public Article renameOnce(Long articleId, String newTitle) {
        Article article = articleRepository.findById(articleId)
                .orElseThrow(() -> new IllegalArgumentException("article not found"));

        article.rename(newTitle);
        return article;
    }
}
```

이 메서드는 "한 번 읽고, 한 번 바꾸고, 한 번 커밋하는 시도"를 뜻한다.  
optimistic lock 예외가 나면 이 시도는 끝난다. 살릴 수 없다.

### 3. facade가 retry와 사용자 메시지 경계를 가진다

```java
@Service
@RequiredArgsConstructor
class ArticleCommandFacade {

    private final ArticleTxService articleTxService;

    public RenameResult rename(Long articleId, String newTitle) {
        try {
            Article article = articleTxService.renameOnce(articleId, newTitle);
            return RenameResult.success(article.getId(), article.getVersion());
        } catch (ObjectOptimisticLockingFailureException ex) {
            return RenameResult.conflict(
                    "다른 사용자가 먼저 수정했습니다. 최신 내용을 확인한 뒤 다시 시도해 주세요."
            );
        }
    }
}
```

여기서 분리하고 싶은 의미는 명확하다.

- `ArticleTxService`: 한 번의 시도
- `ArticleCommandFacade`: 실패를 사용자 의미로 번역하는 곳

사용자가 직접 수정 충돌을 이해해야 하는 화면이라면, 자동 retry보다 conflict 응답이 더 맞다.

### 4. controller는 HTTP/user message로 최종 번역한다

```java
@RestController
@RequiredArgsConstructor
class ArticleController {

    private final ArticleCommandFacade facade;

    @PatchMapping("/articles/{id}")
    public ResponseEntity<?> rename(@PathVariable Long id, @RequestBody RenameRequest request) {
        RenameResult result = facade.rename(id, request.title());

        if (result.isConflict()) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of(
                            "code", "ARTICLE_STALE",
                            "message", result.message()
                    ));
        }

        return ResponseEntity.ok(result);
    }
}
```

이렇게 해야 "DB 예외"가 바로 사용자에게 노출되지 않고,  
**도메인 의미가 있는 안내문**으로 바뀐다.

## 단계별로 어떤 일이 일어나는지 다시 따라가기

### 1. 첫 번째 요청이 `version=7`을 읽는다

- 서비스 코드는 평범하게 row를 읽는다
- 아직 아무 예외도 없다
- 이 시점의 `version=7`은 "내 계산의 기준점"일 뿐이다

### 2. 다른 요청이 먼저 저장해서 `version=8`이 된다

- 내 코드 입장에서는 아직 모른다
- DB row의 최신 상태만 조용히 바뀐다
- optimistic locking은 여기서 바로 막지 않고, **내 저장 순간**에만 잡는다

### 3. 내 요청이 flush/commit에서 실패한다

- SQL은 `WHERE version = 7`로 나간다
- DB는 맞는 row가 없으니 update count `0`을 돌려준다
- JPA/Spring은 `ObjectOptimisticLockingFailureException` 같은 예외를 던질 수 있다

이 실패는 "validation 실패"가 아니라 **stale write 실패**다.

### 4. 현재 transaction attempt는 rollback-only가 된다

이 지점이 가장 많이 헷갈린다.

- 같은 `@Transactional` 메서드 안에서 다시 읽고 다시 저장하면 안 된다
- 이미 persistence context와 transaction 상태가 실패한 시도에 묶여 있다
- retry가 필요하면 facade/application service에서 **새 transaction**을 다시 열어야 한다

즉 "쿼리 한 줄 재실행"이 아니라 "시도 전체 재실행"이다.

### 5. 바깥 계층이 retry와 conflict를 분기한다

여기서 질문은 하나다.  
`최신 상태를 다시 읽어도 같은 요청을 안전하게 다시 적용할 수 있는가?`

- `예`: bounded retry 후보다
- `아니오`: 사용자 conflict 메시지가 맞다

## 자동 retry가 안전한 경계와 위험한 경계

| 상황 | 자동 retry | 이유 |
|---|---|---|
| 포인트 `+100`, 재고 `-1`처럼 최신 값을 다시 읽고 같은 계산을 다시 적용할 수 있다 | 가능 | 연산이 재계산 가능하고, 사용자 의도가 비교적 명확하다 |
| 배치가 상태 플래그를 `PENDING -> DONE`으로 짧게 넘긴다 | 가능 | bounded retry와 idempotency를 붙이기 쉽다 |
| 사용자가 폼에서 제목/본문을 수정했다 | 보통 비권장 | 최신 내용 위에 다시 덮어쓰면 다른 사람 변경을 숨길 수 있다 |
| transaction 안에 결제, 이메일, 외부 API 호출이 있다 | 비권장 | DB만 롤백되고 외부 부작용은 이미 발생했을 수 있다 |

beginner 기준으로 가장 안전한 규칙은 이것이다.

- 자동 retry는 **짧은 DB 작업 + 재계산 가능 + 외부 부작용 없음**일 때만
- 나머지는 conflict 응답 후 최신 데이터 재조회가 기본

## beginner가 가장 자주 틀리는 retry 위치

### 틀린 위치 1: `@Transactional` 메서드 안에서 catch 후 다시 저장

이 방식은 실패한 transaction을 되살리려 하기 때문에 보통 잘못이다.

### 틀린 위치 2: repository 계층에서 조용히 무한 retry

repository는 DB 접근 모양을 책임지는 곳이지, 사용자 의미와 retry budget을 결정하는 곳이 아니다.

### 맞는 위치: facade 또는 application service 바깥 루프

retry가 필요하다면 다음이 같이 있어야 한다.

- 최대 시도 횟수
- 짧은 backoff
- retry 가능한 예외 분류
- 멱등성 또는 중복 부작용 방지 장치

이 구성이 없으면 optimistic lock retry가 아니라 **경합 증폭기**가 된다.

## 사용자 메시지는 어떻게 써야 하나

좋은 메시지는 실패 원인과 다음 행동을 같이 준다.

- 좋은 예: `다른 사용자가 먼저 수정했습니다. 최신 내용을 확인한 뒤 다시 시도해 주세요.`
- 나쁜 예: `저장 실패`, `서버 오류`, `다시 시도하세요`

왜냐하면 optimistic locking 실패는 보통 서버 장애가 아니라 **동시 수정 충돌**이기 때문이다.

API라면 보통 `409 Conflict`가 자연스럽고, UI라면 아래 둘 중 하나가 많이 쓰인다.

- 최신 데이터를 다시 불러오고 사용자의 draft와 차이를 보여주기
- 저장을 막고 충돌 사실을 명확히 알려준 뒤 사용자가 다시 편집하게 하기

## 운영에서 이 예외를 어떻게 해석하나

optimistic lock 예외가 조금 나온다고 해서 곧장 장애는 아니다.

- 정상적인 동시 수정이 보이는 것일 수 있다
- 하지만 비율이 급증하면 hot row, 긴 편집 세션, 잘못된 retry 설계를 의심해야 한다

즉 "예외가 생겼다"보다 **예외를 어디서 얼마나 어떻게 소비하는가**가 더 중요하다.

## 꼬리질문

> Q: optimistic locking 실패는 왜 같은 transaction 안에서 재시도하면 안 되나요?
> 의도: 실패한 attempt와 새 attempt를 구분하는지 확인
> 핵심: 현재 transaction은 이미 rollback-only가 되었기 때문이다

> Q: 언제 409 conflict를 주고, 언제 자동 retry하나요?
> 의도: 사용자 충돌과 재계산 가능한 충돌을 구분하는지 확인
> 핵심: 최신 상태로 안전하게 재적용 가능한 작업만 bounded retry 후보다

> Q: 사용자 메시지에 왜 "다른 사용자가 먼저 수정"이라고 써야 하나요?
> 의도: 동시성 실패를 서버 장애와 구분하는지 확인
> 핵심: optimistic lock은 시스템 오류보다 경쟁 상황 설명이 더 중요하다

## 한 줄 정리

Version column optimistic locking은 `UPDATE ... WHERE version = ?` 실패가 transaction 종료, service-layer 분기, 사용자 conflict 안내까지 이어지는 흐름으로 봐야 retry 위치와 메시지 설계가 헷갈리지 않는다.
