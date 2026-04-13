# Java 마이그레이션 전략

## 핵심 질문

왜 기존 Node 백엔드를 바로 지우지 않고 Java로 병행 전환했는가?

## 답

### 이유 1. 위험 분산

한 번에 교체하면:
- 어디서 깨졌는지 모호
- 롤백 어려움

### 이유 2. parity 확인

Node와 Java가 같은 API 계약을 유지하는지 비교 가능

### 이유 3. 실기기 검증

토스 로그인/IAP는 코드만 맞다고 끝이 아니라 실제 runtime 검증이 필요

## 사주다방 전략

- `server-java/` 구현
- prelaunch single-box
- private 실기기 테스트
- legacy는 archive

## 면접 포인트

“마이그레이션은 기능 구현보다 전환 전략이 더 중요하다. 사주다방은 병행 구현, prelaunch 검증, archive 보존으로 리스크를 낮췄다.”
