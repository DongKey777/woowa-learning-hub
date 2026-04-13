# Mock Interview 50

## Network

1. 사주다방에서 SSE를 쓴 이유는 무엇인가요?
2. WebSocket 대신 SSE를 쓴 장단점은 무엇인가요?
3. replay 이벤트 저장이 왜 필요한가요?
4. `api-prelaunch.saju-dabang.com`은 어떤 의미인가요?
5. DNS가 서비스 운영에 왜 중요한가요?
6. reverse proxy는 왜 필요했나요?
7. HTTPS와 mTLS 차이를 설명해주세요.
8. 토스 WebView 환경에서 HTTPS가 중요한 이유는 무엇인가요?
9. 요청-응답 라이프사이클을 `/api/coins/balance` 기준으로 설명해주세요.
10. `/api/readings/jobs/{jobId}/events` 요청이 들어왔을 때 서버가 무엇을 하나요?

## Database

11. `users`, `transactions`, `coin_ledger`를 왜 분리했나요?
12. 멱등성을 사주다방에서 어떻게 보장했나요?
13. `ON CONFLICT DO NOTHING`은 어떤 상황에서 유용한가요?
14. 트랜잭션과 멱등성의 차이는 무엇인가요?
15. reserve/capture/refund 모델을 왜 사용했나요?
16. 비동기 작업에서 즉시 차감보다 reserve가 나은 이유는 무엇인가요?
17. `purchase_orders` 테이블은 왜 필요한가요?
18. `reading_jobs`와 `reading_results`를 왜 분리했나요?
19. race condition은 어떤 지점에서 생길 수 있나요?
20. ledger와 transaction log는 어떻게 다른가요?

## Operating System / Concurrency

21. 왜 worker 프로세스를 분리했나요?
22. producer-consumer 구조를 이 프로젝트에서 어떻게 적용했나요?
23. reliable queue가 필요한 이유는 무엇인가요?
24. processing queue와 execution queue를 나눈 이유는 무엇인가요?
25. lease key의 역할은 무엇인가요?
26. stale processing recovery는 어떤 문제를 해결하나요?
27. at-least-once와 exactly-once 차이를 설명해주세요.
28. Java virtual thread를 왜 사용했나요?
29. blocking vs non-blocking을 이 프로젝트 기준으로 설명해주세요.
30. worker가 죽었을 때 작업 유실을 줄이는 방법은 무엇인가요?

## Security

31. Bearer와 X-Device-Id를 왜 같이 쓰나요?
32. device ID를 인증으로 볼 수 있나요?
33. 세션을 Redis와 DB에 같이 두는 이유는 무엇인가요?
34. cache miss fallback은 어떤 패턴인가요?
35. token hash를 쓰는 이유는 무엇인가요?
36. AES-GCM을 사용한 이유는 무엇인가요?
37. mTLS는 어떤 상황에서 필요한가요?
38. unlink callback 이후 왜 세션 정리가 필요한가요?
39. IAP 적립을 왜 서버에서 최종 검증하나요?
40. 클라이언트만 믿고 결제를 처리하면 어떤 문제가 생기나요?

## Software Engineering / Architecture

41. layered architecture를 왜 적용했나요?
42. bounded context를 나눈 이유는 무엇인가요?
43. `BillingPort` 같은 포트가 필요한 이유는 무엇인가요?
44. reading과 billing을 왜 직접 연결하지 않았나요?
45. 왜 JPA보다 SQL 중심 접근이 맞다고 보나요?
46. 좋은 마이그레이션 전략은 무엇이라고 생각하나요?
47. legacy Node 구현을 왜 archive로 옮겼나요?
48. 문서 기준선을 Java로 바꾸면서 왜 active docs와 archive docs를 분리했나요?
49. 이 프로젝트에서 통합 테스트가 unit test보다 중요한 이유는 무엇인가요?
50. 사주다방을 통해 가장 잘 설명할 수 있는 CS 개념 세 가지는 무엇인가요?
