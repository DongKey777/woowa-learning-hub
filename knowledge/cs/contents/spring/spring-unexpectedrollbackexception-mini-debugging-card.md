# Mini Debugging Card for `UnexpectedRollbackException`

> 한 줄 요약: `UnexpectedRollbackException`은 "마지막 save가 문제"라는 뜻이 아니라, **이미 rollback-only가 된 트랜잭션을 catch-and-continue 코드가 끝까지 끌고 왔다**는 신호인 경우가 많다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 초급자가 `UnexpectedRollbackException`, `transaction marked as rollback-only`, `catch 했는데 마지막에 터짐`을 빠르게 symptom-to-cause로 연결하는 **beginner debugging card**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Spring Mini Card: rollback-only 실패 vs checked exception인데 commit된 것처럼 보이는 놀람](./spring-rollbackonly-vs-checked-exception-commit-surprise-card.md)
- [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)
- [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [트랜잭션 기초](../database/transaction-basics.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: unexpectedrollbackexception mini debugging card, rollback-only checklist, transaction marked rollback-only checklist, catch 했는데 마지막에 터짐, rollback 안 되는 것 같아요, swallow exception transaction, catch and continue transactional, unexpectedrollbackexception beginner, commit 시점에 터짐 why, 왜 마지막 커밋에서 터져요, audit save then unexpectedrollbackexception, same transaction continue after failure, rollback-only vs checked exception, checked exception commit surprise 비교, spring unexpectedrollbackexception basics

## 이 문서가 먼저 잡는 질문

이 문서는 아래처럼 **예외가 이미 한 번 지나갔는데 마지막에 다시 터진다**는 질문에서 먼저 잡히도록 조정했다.

| 학습자 질문 모양 | 이 문서에서 먼저 주는 답 |
|---|---|
| "`UnexpectedRollbackException`이 왜 마지막에 나와요?" | 마지막 줄보다 앞에서 같은 트랜잭션이 이미 rollback-only가 됐는지 먼저 보라고 답한다 |
| "예외를 catch 했는데 왜 결국 실패해요?" | catch는 예외 전달을 숨길 뿐 트랜잭션 상태를 복구하지 못한다고 먼저 자른다 |
| "audit save는 남길 줄 알았는데 왜 같이 롤백돼요?" | audit도 같은 트랜잭션이면 함께 rollback된다고 먼저 설명한다 |
| "rollback 안 된 게 아니라 마지막에 늦게 드러난 건가요?" | 맞다. 표면화 지점과 최초 실패 지점을 분리해서 보라고 안내한다 |

## 먼저 mental model 한 줄

`UnexpectedRollbackException`은 보통 "마지막 줄이 갑자기 실패했다"가 아니라, **중간에 이미 실패 판정이 난 트랜잭션을 바깥 코드가 모르고 계속 진행했다**는 뜻이다.

초급자는 아래 세 문장만 먼저 붙이면 된다.

- 중간 예외가 같은 트랜잭션에 영향을 줬다.
- 그 트랜잭션이 rollback-only가 됐다.
- 바깥에서 계속 진행하다가 commit 시점에 예외가 드러났다.

## 30초 symptom-to-cause 체크표

| 보이는 증상 | 가장 먼저 의심할 원인 | 지금 확인할 것 |
|---|---|---|
| `UnexpectedRollbackException`이 메서드 마지막에 터진다 | 앞에서 이미 rollback-only가 찍혔다 | 마지막 `save`보다 **더 앞의 첫 예외** |
| 로그에 `transaction marked as rollback-only`가 보인다 | 같은 tx 참여자가 실패했다 | inner method가 `REQUIRED`로 합류했는지 |
| `try/catch`로 예외를 먹었는데도 commit에서 실패한다 | catch는 예외 전달만 숨기고 tx 상태는 못 되돌린다 | catch 블록 앞에서 무슨 예외가 났는지 |
| audit/save 하나는 남길 줄 알았는데 같이 롤백된다 | audit도 같은 tx에 묶였다 | 정말 독립 커밋이어야 하는 작업인지 |
| stack trace는 outer service 끝에서 보이는데 원인은 inner service 같다 | 표면화 지점과 최초 실패 지점이 다르다 | 최초 예외 발생 메서드와 그 propagation |

핵심은 "`UnexpectedRollbackException`이 난 줄"이 아니라 **rollback-only를 처음 만든 줄**을 찾는 것이다.

## 가장 흔한 실수: catch-and-continue

```java
@Transactional
public void placeOrder() {
    try {
        paymentService.charge();
    } catch (Exception ex) {
        log.warn("결제 실패는 일단 무시", ex);
    }

    auditRepository.save(new AuditLog("done"));
}
```

초급자 눈에는 이렇게 보이기 쉽다.

- `charge()` 실패는 처리했다
- 그 뒤 `auditRepository.save(...)`는 정상 저장될 것 같다

하지만 실제로는 아래처럼 읽어야 할 때가 많다.

```text
1. placeOrder tx 시작
2. paymentService.charge()가 같은 tx에 참여
3. 안쪽 실패로 현재 tx가 rollback-only가 됨
4. catch가 예외 전달만 막음
5. 바깥 코드는 계속 진행
6. commit 시점에 UnexpectedRollbackException 발생
```

즉 catch는 "화면에 보이는 예외"를 숨길 수 있어도, **이미 실패 예정인 트랜잭션을 성공 상태로 복구하지는 못한다**.

## 어디를 보면 되나

### 1. 마지막 `save`부터 보지 말고, 그 앞 예외부터 본다

초급자가 자주 하는 오해:

- "`auditRepository.save()`가 문제인가?"
- "`마지막 repository 호출이 rollback을 만들었나?"

더 안전한 순서는 이것이다.

1. 같은 request / 같은 service call 안에서 처음 던져진 예외를 찾는다.
2. 그 예외를 누가 catch 했는지 본다.
3. 그 메서드들이 같은 transaction에 참여했는지 본다.

### 2. inner method가 같은 tx였는지 확인한다

가장 흔한 패턴은 inner method가 기본 전파인 `REQUIRED`라서 바깥 tx에 그냥 같이 탔던 경우다.

| 질문 | 예/아니오가 뜻하는 것 |
|---|---|
| inner method도 `@Transactional`이고 기본값인가 | 대개 같은 tx 참여 가능성이 크다 |
| outer와 inner가 같은 service call 흐름 안에 있나 | rollback-only가 전파되기 쉽다 |
| 예외를 inner 또는 outer에서 잡고 계속 갔나 | commit 시점 지연 폭발 패턴과 맞는다 |

### 3. "정말 같이 롤백돼야 하는 작업인지" 다시 본다

특히 아래 작업은 초급자가 같은 tx에 묶어 두고 기대를 잘못 잡기 쉽다.

- 실패 기록 audit
- 알림 발송 이력 저장
- 보조 테이블 상태 기록

이런 작업이 "본 작업 실패와 상관없이 남아야 하는 기록"이라면, 같은 tx에 두는 순간 기대와 어긋날 수 있다.

## 자주 보이는 원인 4개

| 원인 | 왜 `UnexpectedRollbackException`으로 보이나 | 초급자용 대응 방향 |
|---|---|---|
| inner `REQUIRED` 실패 후 outer가 계속 진행 | 같은 tx가 이미 rollback-only다 | 실패를 숨기지 말고 먼저 전파 여부를 본다 |
| `try/catch`로 예외만 먹음 | tx 상태는 그대로 실패 예정이다 | catch 뒤 계속 쓰는 코드가 있는지 본다 |
| audit/보조 기록도 같은 tx에 저장 | 함께 rollback된다 | 독립 경계가 필요한지 검토한다 |
| flush/commit 시점에 DB 제약 예외가 늦게 드러남 | 표면화 시점이 뒤로 밀린다 | 실제 최초 예외가 commit 근처인지도 확인한다 |

## 빠른 자기 점검 5문장

- "마지막 줄이 아니라 그 앞에서 예외가 있었나?"
- "그 예외를 내가 catch만 하고 끝내지 않았나?"
- "inner call이 같은 transaction에 참여한 건 아닌가?"
- "지금 저장하려는 audit/보조 기록이 정말 같은 transaction이어야 하나?"
- "`UnexpectedRollbackException`이 원인 자체가 아니라 결과 신호일 수 있다는 점을 놓치지 않았나?"

## 어디로 이어서 보면 좋나

- `REQUIRED`와 `REQUIRES_NEW` 감각이 아직 약하면 [Spring Transaction Propagation Beginner Primer: `REQUIRED`, `REQUIRES_NEW`, rollback-only](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)로 먼저 간다.
- rollback-only가 왜 찍히는지 더 자세히 보려면 [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./spring-unexpectedrollback-rollbackonly-marker-traps.md)로 이어간다.
- 실제 로그/TRACE 기준 디버깅 순서를 보고 싶으면 [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)로 간다.

## 한 줄 정리

`UnexpectedRollbackException`은 "rollback이 안 됐다"가 아니라, **앞에서 이미 rollback-only가 된 트랜잭션을 catch-and-continue가 끝까지 끌고 와 commit 시점에 드러난 신호**다.
