# CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook

> 한 줄 요약: CDC schema evolution의 핵심은 컬럼을 추가하는 DDL이 아니라, old producer·new connector·old consumer가 한동안 동시에 살아도 이벤트 계약이 깨지지 않게 만드는 expand-contract 절차다.

**난이도: 🔴 Advanced**

관련 문서:

- [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md)
- [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
- [Destructive Schema Cleanup, Column Retirement, and Contract-Phase Safety](./destructive-schema-cleanup-column-retirement.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md)
- [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
- [Zero-Downtime Schema Migration Platform 설계](../system-design/zero-downtime-schema-migration-platform-design.md)

retrieval-anchor-keywords: cdc schema evolution, event compatibility, expand contract migration, backward compatible event, forward compatible consumer, versioned payload, debezium schema change, contract-safe rollout

## 핵심 개념

CDC를 쓰는 순간 DB 스키마 변경은 로컬 DDL이 아니라 이벤트 계약 변경이 된다.

문제는 보통 다음처럼 생긴다.

- producer는 새 컬럼을 쓰기 시작했다
- connector는 새 schema를 내보낸다
- 일부 consumer는 아직 옛 payload를 기대한다

이때 "DDL은 성공했다"와 "시스템은 안전하다"는 전혀 다른 말이다.  
CDC schema evolution의 본질은 **expand-contract를 데이터 계약 관점에서 운영하는 것**이다.

핵심 질문:

- old consumer가 new event를 받아도 깨지지 않는가
- new consumer가 old event를 받아도 동작하는가
- replay 시 과거 schema와 현재 code가 충돌하지 않는가
- cutover 중 어떤 버전을 source of truth로 볼 것인가

## 깊이 들어가기

### 1. schema change는 DB change와 event change가 동시에 일어난다

일반적인 DB 마이그레이션은 다음만 보면 될 수 있다.

- 컬럼 추가
- nullable 여부
- backfill
- cutover

하지만 CDC가 붙으면 추가로 봐야 한다.

- connector가 schema metadata를 어떻게 표현하는가
- sink의 serializer/registry가 바뀌는가
- consumer가 새로운 필드를 optional로 처리하는가
- replay 중 과거 이벤트를 현재 consumer가 읽을 수 있는가

즉 CDC 환경에서는 DDL이 곧 **계약 변경 이벤트**다.

### 2. expand-contract가 기본 전략이다

안전한 순서는 대체로 이렇다.

1. DB에 새 컬럼/새 표현을 추가한다
2. producer는 old+new를 함께 쓸 수 있게 한다
3. consumer는 new field를 optional하게 이해하도록 먼저 배포한다
4. backfill/catch-up을 수행한다
5. 읽기/처리를 new field 기준으로 전환한다
6. old field 제거는 가장 나중에 한다

이 순서를 거꾸로 하면, connector나 consumer 한 군데라도 늦게 배포될 때 즉시 호환성 문제가 난다.
그리고 old field를 실제로 제거하는 contract phase는 별도의 retirement 증거와 cleanup 절차가 필요하다.

### 3. backward/forward compatibility를 따로 봐야 한다

실무에서 자주 헷갈리는 점:

- backward compatible
  - new consumer가 old event를 읽을 수 있는가
- forward compatible
  - old consumer가 new event를 받아도 무너지지 않는가

CDC replay와 staged rollout이 있는 시스템은 둘 다 중요하다.

예를 들어 컬럼 추가는 보통 비교적 안전하지만:

- 필수 필드로 바꾸기
- enum 값 추가
- 의미 변경된 rename

은 forward compatibility를 쉽게 깨뜨린다.

### 4. rename은 추가/복사/전환/제거로 봐야 한다

컬럼 rename이나 payload field rename을 한 번에 처리하면 위험하다.

더 안전한 흐름:

- 새 이름의 필드 추가
- old -> new 복사 또는 dual publish
- consumer를 새 필드 우선 읽기로 전환
- 충분한 검증 후 old 필드 제거

즉 rename은 명령 하나가 아니라, 사실상 **새 필드 도입 후 old 필드 퇴역** 절차다.

### 5. replay 가능성이 있으면 schema registry만으로 끝나지 않는다

Avro/Protobuf/schema registry가 있어도 끝이 아니다.

여전히 필요한 것:

- consumer code의 optional/default handling
- old event version을 읽는 테스트
- repair/replay 시 어떤 decoder를 쓸지
- DLQ에 쌓인 과거 메시지 재처리 전략

registry는 선언이고, 실제 안전성은 consumer behavior에서 완성된다.

### 6. backfill과 CDC를 함께 쓸 때는 dual meaning 기간을 최소화해야 한다

새 필드를 backfill하는 동안 old/new 값이 함께 존재할 수 있다.

이때 위험:

- 일부 row는 old만 채워짐
- 일부 row는 new만 채워짐
- 일부 consumer는 둘 중 하나만 읽음

그래서 전환 기간에는 보통 다음 중 하나를 정한다.

- read path는 old 우선, new는 shadow verify만 함
- write path는 old+new 동시 기록
- verification 완료 후 read path를 new로 스위치

핵심은 "두 필드가 섞여 있는 기간"을 명시적으로 운영하는 것이다.

## 실전 시나리오

### 시나리오 1. outbox payload에 새 필드 추가

`order_created` 이벤트에 `tenant_id`를 추가하고 싶다.

안전한 방식:

- consumer가 `tenant_id` 없을 때도 동작하도록 먼저 수정
- producer가 새 필드 포함 시작
- 이후 downstream에서 새 필드를 활용

### 시나리오 2. status enum 값 추가

consumer가 `READY|DONE`만 알고 있는데 `RETRYING`이 추가되면 old consumer가 깨질 수 있다.

대응:

- unknown enum 처리 기본값 제공
- fail-closed가 맞는지, fail-open이 맞는지 정책화
- replay 테스트로 과거/미래 값 동작 확인

### 시나리오 3. old field 제거 후 replay 실패

현재 코드는 새 필드만 읽는데, 장애 복구 중 과거 DLQ를 replay하니 old schema 메시지가 들어온다.

이 경우는:

- decoder 호환성 유지
- replay window 동안 old version 지원
- old event adapter layer

가 필요하다.

## 코드로 보기

```java
record OrderCreatedEventV2(
    long orderId,
    String status,
    Long tenantId
) {}
```

```java
String tenantScope(OrderCreatedEnvelope event) {
    if (event.tenantId() != null) {
        return "tenant:" + event.tenantId();
    }
    return "tenant:unknown";
}
```

```sql
ALTER TABLE outbox_event
  ADD COLUMN tenant_id BIGINT NULL;
```

핵심은 코드 조각보다, old/new schema가 동시에 흐르는 기간에도 consumer가 무너지지 않도록 optional handling과 rollout order를 맞추는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| one-shot breaking change | 빨라 보인다 | consumer 장애와 replay 실패 위험이 크다 | 거의 피해야 한다 |
| expand-contract | staged rollout이 안전하다 | 전환 기간이 길어진다 | 대부분의 CDC schema 변화 |
| dual publish | 검증이 쉽다 | write path와 consumer 로직이 복잡하다 | rename/semantic migration |
| adapter layer 유지 | replay 안전성이 높다 | 레거시 처리 비용이 남는다 | 긴 replay window가 필요한 시스템 |

## 꼬리질문

> Q: CDC 환경에서 컬럼 추가가 왜 이벤트 계약 변경이 되나요?
> 의도: 로컬 DDL과 downstream 계약을 연결하는지 확인
> 핵심: connector와 consumer가 그 변경을 외부 이벤트 형태로 보게 되기 때문이다

> Q: backward compatibility와 forward compatibility 중 무엇이 더 중요하나요?
> 의도: staged rollout과 replay 문맥을 함께 보는지 확인
> 핵심: 둘 다 중요하고, replay와 점진 배포가 있으면 어느 한쪽만 맞아도 부족하다

> Q: rename을 왜 add/switch/remove 절차로 봐야 하나요?
> 의도: breaking change를 피하는 expand-contract 감각 확인
> 핵심: old/new consumer가 함께 살아 있는 기간을 안전하게 통과해야 하기 때문이다

## 한 줄 정리

CDC schema evolution의 정답은 DDL 성공이 아니라, old/new producer·connector·consumer가 함께 살아 있는 기간을 expand-contract로 통과하며 replay 호환성까지 보장하는 것이다.
