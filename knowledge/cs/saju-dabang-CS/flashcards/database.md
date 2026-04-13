# Database Flashcards

- Q: 트랜잭션이 필요한 이유는?
  A: 여러 write가 함께 성공/실패해야 정합성이 유지되기 때문

- Q: 멱등성이 필요한 이유는?
  A: 같은 요청이 반복되어도 결과가 한 번만 반영되게 해야 하기 때문

- Q: `transactions` 역할은?
  A: 실제 거래 흐름과 상태 전이

- Q: `coin_ledger` 역할은?
  A: 회계/감사 trail과 idempotency 보강

- Q: reserve/capture/refund를 쓰는 이유는?
  A: 긴 비동기 작업에서 돈/포인트 정합성을 유지하기 위해
