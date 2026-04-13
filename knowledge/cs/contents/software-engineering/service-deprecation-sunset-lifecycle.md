# Service Deprecation and Sunset Lifecycle

> 한 줄 요약: 서비스 deprecation은 오래된 API를 지우는 일이 아니라, 대체 경로와 관측 가능성을 유지한 채 소비자를 안전하게 이동시키는 수명 종료 관리다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)

> retrieval-anchor-keywords:
> - service deprecation
> - sunset lifecycle
> - replacement service
> - tombstone
> - migration window
> - consumer notice
> - hard delete
> - backward compatibility

## 핵심 개념

서비스 deprecation은 "없애자"가 아니다.
정확히는 **소비자들이 안전하게 떠날 수 있는 종료 절차를 설계하는 것**이다.

대부분의 서비스는 다음 이유로 바로 지우면 안 된다.

- 아직 쓰는 소비자가 있다
- 계약과 데이터가 뒤섞여 있다
- 호출 빈도는 낮아도 중요한 배치가 남아 있다
- 운영 대시보드와 알림이 아직 참조 중이다

즉 sunset은 기능 삭제가 아니라 **책임 있는 철수**다.

---

## 깊이 들어가기

### 1. deprecation은 공지부터 시작한다

좋은 종료는 먼저 알려야 한다.

필요한 것:

- 종료 예정일
- 대체 서비스/경로
- 남은 migration window
- 영향받는 소비자 목록
- 연락 채널

공지 없이 지우면 기술적으로는 깔끔해 보여도, 운영적으로는 사고다.

### 2. sunset은 단계적으로 진행해야 한다

보통 순서는 이렇다.

1. deprecation 공지
2. 신규 사용 차단
3. 기존 소비자 migration
4. read-only 또는 tombstone 모드
5. 최종 종료
6. 데이터/리소스 정리

이 순서는 소비자에게 준비 시간을 주고, 내부 관측을 유지한다.

### 3. 관측 가능성을 먼저 줄이지 말아야 한다

서비스를 내리기 전에 다음을 남겨야 한다.

- 에러 로그
- 호출 통계
- 소비자 식별
- 마지막 요청 시각

이게 없으면 누가 아직 쓰는지 알 수 없다.

### 4. hard delete는 가장 마지막이다

API endpoint를 내리는 것과, backing data를 지우는 것은 다르다.

특히 다음은 더 늦게 지워야 한다.

- 이벤트 토픽
- DB 테이블
- 배치 job
- 대시보드
- 알림 rule

서비스는 코드보다 주변 의존성이 더 오래 남을 수 있다.

### 5. 종료는 ADR과 연결되어야 한다

왜 종료하는지, 무엇이 대체인지, 어떤 조건이 충족되면 지우는지 남겨야 한다.
이 문맥은 [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)와 직접 연결된다.

---

## 실전 시나리오

### 시나리오 1: 낡은 조회 API를 종료한다

조회 API를 새 BFF와 새 contract로 옮겼다면:

- 구 API에 deprecation header를 붙인다
- 소비자 목록을 추적한다
- 일정 기간 후 read-only로 전환한다
- 마지막에 endpoint를 제거한다

### 시나리오 2: 내부 서비스가 더 이상 필요 없다

같은 기능을 제공하는 새 서비스가 안정화되면, 옛 서비스는 tombstone 상태로 바꾸고 호출 차단을 걸 수 있다.
하지만 바로 제거하지 말고 로그와 관측을 남긴다.

### 시나리오 3: 배치와 이벤트가 남아 있다

API는 지웠는데, 배치 job과 이벤트 consumer가 옛 서비스 이름을 바라보는 경우가 많다.
그래서 deprecation은 코드 삭제보다 dependencies cleanup이 더 오래 걸린다.

---

## 코드로 보기

```yaml
deprecation_plan:
  announce: 2026-05-01
  stop_new_consumers: true
  tombstone_after: 30d
  delete_after:
    - consumer_count == 0
    - last_access < 14d
    - dashboards_migrated: true
```

종료 조건이 명시되어야 sunset이 감정이 아닌 절차가 된다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 삭제 | 단순하다 | 소비자 충격이 크다 | 외부 노출이 없고 안전할 때 |
| tombstone 후 삭제 | 안전하다 | 종료가 길어진다 | 소비자가 남아 있을 때 |
| 장기 sunset | 리스크가 낮다 | 유지비가 든다 | 중요한 서비스일 때 |

deprecation은 지우는 속도가 아니라 **안전하게 떠나게 하는 능력**으로 평가해야 한다.

---

## 꼬리질문

- 누가 종료 결정을 승인하는가?
- 소비자 migration이 끝났는지 어떻게 확인하는가?
- 읽기/쓰기 경로는 언제 분리할 것인가?
- tombstone 상태를 운영 도구가 이해하는가?

## 한 줄 정리

서비스 deprecation은 서비스 삭제가 아니라, 소비자 migration과 관측 가능성을 유지한 채 수명을 정리하는 lifecycle 관리다.
