# Ledger와 Transaction Log

## 왜 이 문서를 보나

면접에서 “왜 테이블을 두 개나 뒀냐”는 질문이 나올 수 있다.

## 사주다방의 두 축

### transactions

- 사용자 거래 흐름
- reserve / completed / refunded
- order / reading 연결

### coin_ledger

- 회계/감사 기록
- balance_after
- idempotency_key
- `capture(amount=0)` 같은 감사용 기록

## 중요한 차이

`transactions`는 **상태 전이**를 담고,  
`coin_ledger`는 **회계적 사실**을 담는다.

즉:
- 하나는 workflow
- 하나는 audit

## 면접 포인트

“거래 상태를 표현하는 로그와 회계/감사 목적의 ledger는 분리될 수 있다. 사주다방은 이 둘을 분리해 workflow와 audit 요구를 동시에 만족시켰다.”
