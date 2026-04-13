# 계층형 아키텍처

## 구조

- controller/api
- application service
- persistence/infra
- domain

이 구조는 역할 분리를 위한 기본 패턴이다.

## 사주다방 코드 예시

- API layer: `.../auth/api`, `.../billing/api`, `.../reading/api`
- application layer: `.../auth/application`, `.../reading/application`
- infra layer: `.../billing/infra/persistence`

## 면접 포인트

“계층 분리는 유지보수성과 테스트 용이성을 위해 적용했다.”
