# 3버킷 공통 용어 카드

> 한 줄 요약: `already exists` / `busy` / `retryable`은 예외 이름을 외우는 카드가 아니라, "지금 서비스가 어떤 문장으로 답해야 하는가"를 먼저 맞추는 공통 언어다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: three bucket common terms card, already exists busy retryable glossary, already exists busy retryable primer, service outcome bucket vocabulary, duplicate key busy retryable terms, beginner bucket terms card, 3버킷 공통 용어 카드, already exists busy retryable 용어 카드, 서비스 결과 버킷 공통 언어, 중복 혼잡 재시도 용어 정리, beginner 예외 용어 번역 카드, duplicate key lock timeout deadlock terminology

## 먼저 멘탈모델

초보자는 예외 이름보다 "지금 이 실패를 어떤 한국어 문장으로 번역할까?"를 먼저 잡는 편이 덜 헷갈린다.

- `already exists`: 이미 누군가 먼저 끝냈다
- `busy`: 아직 결과를 확정할 수 없을 만큼 막혀 있다
- `retryable`: 이번 시도만 실패했고, 새 시도로 다시 해 볼 수 있다

이 3버킷은 DB 원문을 그대로 복사한 말이 아니라, **서비스가 다음 동작을 고르기 위한 번역 언어**다.

## 한 장 용어표

| 용어 | 초보자용 한 줄 뜻 | 자주 보이는 신호 | 기본 동작 |
|---|---|---|---|
| `already exists` | 이미 승자가 있다 | `duplicate key`, unique violation | 기존 row/기존 결과를 다시 읽는다 |
| `busy` | 지금은 막혀 있어서 승패를 못 본다 | `lock timeout`, `connection timeout`, winner가 아직 `PROCESSING` | 즉시 무한 재시도보다 짧은 대기/조회/혼잡 확인을 먼저 한다 |
| `retryable` | 이번 attempt만 무효다 | `deadlock`, `serialization failure` | 새 트랜잭션으로 처음부터 다시 시도한다 |

## 가장 작은 예시

쿠폰 발급에서 `(coupon_id, member_id)`가 유일하다고 하자.

| 장면 | 공통 용어 |
|---|---|
| 다른 요청이 먼저 발급을 끝내서 `duplicate key`가 났다 | `already exists` |
| 먼저 들어온 요청이 아직 처리 중이라 후속 요청이 오래 기다린다 | `busy` |
| 잠금 순서가 꼬여 deadlock victim이 됐다 | `retryable` |

핵심은 "실패" 하나로 묶지 않는 것이다.
이미 끝난 실패, 아직 결론을 못 본 실패, 이번 시도만 무효인 실패는 다음 동작이 다르다.

## 자주 헷갈리는 지점

- `already exists`는 HTTP 상태코드 이름이 아니다. 같은 버킷 안에서도 `200`, `201`, `409`는 서비스 계약에 따라 달라질 수 있다.
- `busy`는 "조금만 더 하면 무조건 성공"을 뜻하지 않는다. blocker, 풀 고갈, 긴 트랜잭션 때문에 잠깐 실패한 상태일 수 있다.
- `retryable`은 보통 SQL 한 줄 재실행이 아니라 **트랜잭션 전체 재시도**를 뜻한다.
- `duplicate key`를 무조건 `retryable`로 읽으면 같은 winner에 계속 부딪힐 수 있다.

## 문서를 읽을 때 이렇게 연결하면 된다

- 예외 신호를 30초 안에 고르고 싶으면 [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md)
- duplicate 경로와 lock 경로를 한 장 비교하고 싶으면 [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- service 코드에서 outcome mapper까지 보고 싶으면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- MySQL `1062`를 `already exists` / `busy`로 더 자세히 나누고 싶으면 [MySQL Duplicate-Key Retry Handling Cheat Sheet](./mysql-duplicate-key-retry-handling-cheat-sheet.md)
