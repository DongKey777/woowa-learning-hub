# 사주다방 기반 예상 면접 질문

## 분야별 문서

- [01-network-answers.md](./01-network-answers.md)
- [02-database-answers.md](./02-database-answers.md)
- [03-operating-system-answers.md](./03-operating-system-answers.md)
- [04-security-answers.md](./04-security-answers.md)
- [05-architecture-answers.md](./05-architecture-answers.md)

## 공통 질문 목록

### 네트워크

1. 왜 SSE를 썼나요?
2. WebSocket과 차이는?
3. 도메인과 DNS는 어떻게 연결되나요?
4. HTTPS와 mTLS 차이는?

### 데이터베이스

5. 트랜잭션은 왜 필요했나요?
6. 멱등성은 어떻게 보장했나요?
7. `transactions`와 `coin_ledger`를 왜 분리했나요?
8. reserve/capture/refund 모델은 왜 썼나요?

### 운영체제 / 동시성

9. worker를 왜 따로 뒀나요?
10. reliable queue가 필요한 이유는?
11. virtual thread를 쓴 이유는?
12. 비동기 작업 실패 시 어떻게 복구하나요?

### 보안

13. 세션을 Redis와 DB에 같이 두는 이유는?
14. AES-GCM을 사용한 이유는?
15. mTLS가 필요한 이유는?

### 소프트웨어 공학

16. layered architecture를 왜 썼나요?
17. port/adaptor를 왜 도입했나요?
18. legacy Node를 archive로 옮긴 이유는?
19. 컷오버를 어떻게 안전하게 했나요?
20. 설계를 바꾸지 않고 구현체만 바꾸려면 무엇이 중요하나요?

## 답변 훈련 방법

각 질문은 두 버전으로 준비한다.

### 30초 버전

- 핵심 개념 1문장
- 사주다방 사례 1문장
- 결과/이유 1문장

### 2~3분 버전

1. 개념 정의
2. 사주다방 코드 위치
3. 왜 그렇게 설계했는지
4. 대안과 비교
5. trade-off

## 꼬리질문 대응 원칙

면접관은 보통 아래 식으로 더 판다.

- “왜?”
- “대안은?”
- “실패하면?”
- “그럼 정확히 코드는 어디서?”
- “장단점은?”

즉 답변할 때 처음부터

`개념 -> 코드 -> 이유 -> 대안`

순서로 말하는 습관을 들이면 좋다.
