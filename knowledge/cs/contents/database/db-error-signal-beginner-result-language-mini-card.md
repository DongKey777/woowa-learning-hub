# DB 입문 오류 신호 미니카드

> 한 줄 요약: `duplicate key` / `lock wait timeout` / `deadlock`은 모두 "DB 에러"처럼 보이지만, 초보자 기본 해석은 각각 `이미 있음` / `지금 막힘` / `이번 시도만 다시`로 먼저 나누면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [DB 신호 -> 서비스 결과 enum -> HTTP 응답 브리지](./db-signal-service-result-http-bridge.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: db error signal mini card, duplicate key lock wait timeout deadlock one page, beginner db error translation, duplicate key beginner meaning, lock wait timeout beginner meaning, deadlock beginner meaning, already exists busy retryable one page, db error to user result language, duplicate key lock timeout deadlock result table, 초급자 db 오류 신호 표, duplicate key lock wait timeout deadlock 분류표, 이미 있음 지금 막힘 이번 시도만 다시, 중복 키 락 대기 타임아웃 데드락 한 장, beginner database error card

## 먼저 멘탈모델

초보자는 에러 이름보다 **결과 문장**부터 잡는 편이 덜 흔들린다.

- `duplicate key`: 이미 누가 먼저 만들었다
- `lock wait timeout`: 아직 결론을 못 봤다. 지금 줄이 막혀 있다
- `deadlock`: 이번 시도끼리 서로 막아서, DB가 한쪽을 다시 하라고 돌려보냈다

한 줄 기억법:

> `이미 있음` / `지금 막힘` / `이번 시도만 다시`

## 1페이지 분류표

| 에러 신호 | 초급자 결과 언어 | DB가 말하는 뜻 | 첫 기본 동작 | 바로 하면 안 되는 것 |
|---|---|---|---|---|
| `duplicate key` | `이미 있음` | 같은 key의 winner가 이미 있다 | 기존 row나 기존 결과를 fresh read로 다시 본다 | 같은 `INSERT`를 blind retry |
| `lock wait timeout` | `지금 막힘` | 누가 락을 오래 쥐고 있어 이번 시도는 결론을 못 봤다 | blocker/긴 트랜잭션/혼잡부터 확인하고, 필요하면 매우 짧은 제한 retry | 곧바로 `이미 있음`으로 단정 |
| `deadlock` | `이번 시도만 다시` | 서로가 서로를 기다려 DB가 희생자 하나를 골랐다 | **트랜잭션 전체**를 bounded retry | timeout 늘리기만 하거나 SQL 한 줄만 재실행 |

## 작은 예시

같은 쿠폰을 두 요청이 동시에 발급한다고 가정하자.

| 장면 | 보이는 신호 | 초급자 해석 | 서비스 기본 반응 |
|---|---|---|---|
| A가 먼저 insert commit, B가 같은 key로 insert | `duplicate key` | 이미 승자가 있다 | "이미 발급됨" 또는 기존 성공 결과 재사용 |
| A가 row를 오래 잡고 있고 B는 기다리다 포기 | `lock wait timeout` | 아직 줄이 안 빠졌다 | "지금 혼잡"으로 답하고 blocker/트랜잭션 길이 확인 |
| A는 row 1 -> row 2, B는 row 2 -> row 1 순서로 잠금 | `deadlock` | 이번 판의 잠금 순서가 꼬였다 | 전체 발급 시도 1~2회 bounded retry |

## 자주 헷갈리는 지점

- `duplicate key`는 보통 "이미 winner가 있음"이지 "재시도를 더 세게 걸어야 함"이 아니다.
- `lock wait timeout`은 보통 `already exists`가 아니라 `busy`에 가깝다.
- `deadlock`은 "DB가 완전히 고장남"보다 "이번 시도 하나를 다시 하라"에 가깝다.
- `deadlock` retry는 SQL 한 줄이 아니라 트랜잭션 전체를 다시 시작해야 안전하다.
- 세 신호를 다 같은 `409`나 같은 재시도 정책으로 묶으면 서비스 의미가 흐려진다.

## 안전한 다음 단계

| 지금 본 신호 | 다음 문서 |
|---|---|
| `duplicate key` 뒤에 `409` / 재사용 / 진행중 구분이 헷갈린다 | [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md) |
| `lock wait timeout`을 자꾸 `이미 있음`처럼 읽게 된다 | [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md) |
| `deadlock`과 `lock timeout`을 한 예외 이름에서 분리 못 하겠다 | [3버킷 결정 트리 미니카드](./three-bucket-decision-tree-mini-card.md) |
| 실제 DB 운영 신호까지 더 파고들어야 한다 | [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md) |
