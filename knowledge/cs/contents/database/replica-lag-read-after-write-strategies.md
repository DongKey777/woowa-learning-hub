# Replica Lag and Read-after-write Strategies

> 한 줄 요약: replica를 붙인 뒤 "방금 쓴 데이터가 안 보인다"는 문제는 설계가 아니라 전파 지연을 다루는 방식의 문제다.

> 관련 문서: [MVCC, Replication, Sharding](./mvcc-replication-sharding.md), [트랜잭션 실전 시나리오](./transaction-case-studies.md), [HikariCP 튜닝](./hikari-connection-pool-tuning.md)

## 핵심 개념

primary/replica 구조에서는 쓰기와 읽기가 다른 서버로 갈 수 있다.  
이때 replica lag 때문에 read-after-write 일관성이 깨질 수 있다.

왜 중요한가:

- 주문 직후 상세 조회가 옛 데이터를 보여줄 수 있다
- 재고/결제/권한 변경처럼 즉시 반영이 필요한 화면이 있다
- replica는 읽기 확장을 주지만 일관성 비용을 숨긴다

## 깊이 들어가기

### 1. lag가 생기는 이유

복제는 완전히 동기적이지 않은 경우가 많다.

- binlog apply 지연
- 네트워크 지연
- replica I/O/SQL thread 지연
- 긴 트랜잭션 블로킹

### 2. read-after-write 전략

대표적인 전략:

- write 후 일정 시간 primary 읽기
- 세션 sticky
- version token 기반 재조회
- 중요 경로만 강한 일관성 유지

### 3. 언제 replica를 믿을 수 없는가

- 결제 직후 조회
- 상태 전이 직후 화면
- 멱등성 키 검증 직후

## 실전 시나리오

### 시나리오 1: 주문 성공 직후 주문 목록에 없다

replica lag가 원인일 수 있다.  
이 경우 주문 생성 직후는 primary, 그 후는 replica로 분기한다.

### 시나리오 2: 관리자 페이지에서 상태 변경이 늦게 보인다

관리 화면은 보통 강한 일관성이 더 중요하다.

## 코드로 보기

```text
write path -> primary
read path -> replica

하지만 최근 write가 있었으면:
  -> primary fallback
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| replica read | 확장성 좋음 | lag 문제 | 조회 위주 |
| primary read on recent write | 일관성 높음 | 라우팅 복잡 | 주문/결제 |
| session stickiness | 구현 단순 | 분산 부하 감소 | 사용자 단위 일관성 |
| version-based routing | 정교함 | 저장/판정 비용 | 대규모 서비스 |

## 꼬리질문

> Q: replica를 썼는데 왜 최신 데이터가 안 보이는가?
> 의도: 복제 지연 이해 여부 확인
> 핵심: 읽기 확장은 일관성 비용을 가져온다.

> Q: read-after-write를 보장하려면 어떤 전략이 현실적인가?
> 의도: 운영 가능한 일관성 설계 이해 여부 확인
> 핵심: primary fallback, sticky session, version routing.

## 한 줄 정리

replica lag는 읽기 확장과 즉시 일관성의 trade-off이며, read-after-write가 중요한 경로는 라우팅을 따로 설계해야 한다.
