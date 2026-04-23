# Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계

> 한 줄 요약: receiver warmup, cache prefill, write freeze cutover 설계는 상태를 새 수신 노드나 새 경로로 옮길 때 cold start와 stale routing, final write race를 줄이기 위해 예열, 사전 적재, 짧은 동결 구간을 조합하는 운영 전환 설계다.

retrieval-anchor-keywords: receiver warmup, cache prefill, write freeze cutover, cold start mitigation, prewarm cache, donor receiver handoff, fenced freeze, cutover soak, stateful warmup, staged traffic enable, rollback window

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)

## 핵심 개념

상태를 옮기는 cutover에서 데이터 복사 자체보다 더 자주 문제를 만드는 것은 "전환 직후의 cold path"다.

- receiver에는 데이터는 있지만 cache가 비어 있다
- 연결 풀과 index가 아직 뜨겁지 않다
- stale routing 때문에 old/new에 요청이 섞인다
- 마지막 write race가 정합성을 깨뜨린다

그래서 실전에서는 단순 `copy -> switch`보다 다음 네 단계를 갖는다.

- receiver warmup
- cache prefill
- short write freeze
- cutover soak

즉, 목표는 "전환"이 아니라 **전환 직후에도 사용자 체감 품질과 정합성을 유지하는 것**이다.

## 깊이 들어가기

### 1. 왜 warmup이 필요한가

receiver는 snapshot을 복구했다고 바로 준비된 것이 아니다.

- page cache 미적중
- index / compaction background 작업
- connection pool cold start
- JIT / runtime warmup
- dependency token / credential lazy fetch

특히 read-heavy 상태 시스템은 metadata copy보다 cache miss 폭주가 더 큰 장애를 만든다.

### 2. Capacity Estimation

예:

- shard당 state 40 GB
- hot key set 5 GB
- 평시 read QPS 2만
- final write freeze 허용 500ms

이때 봐야 할 숫자:

- prefill bytes
- cache hit recovery curve
- warmup duration
- freeze window p99
- post-cutover error burst

warmup 설계는 평균 latency보다 cutover 직후 tail spike를 얼마나 낮추는지가 핵심이다.

### 3. Warmup 대상 구분

모든 것을 미리 채울 필요는 없다.
보통 다음 층으로 나눈다.

- 필수 metadata
- hottest working set
- 최근 session / tenant state
- cold tail data

즉, full preload보다 **hotset-aware prefill**이 더 현실적일 때가 많다.

### 4. Cache prefill 전략

대표 전략:

- donor access log 기반 hotset prefill
- key popularity snapshot 기반 prefill
- tenant priority 기반 selective prefill
- read-through warmup traffic

주의할 점:

- prefill 자체가 donor와 backend를 압박할 수 있다
- stale 데이터를 미리 올려 버릴 수 있다
- prefill과 live delta apply 순서가 꼬이면 overwrite가 날 수 있다

그래서 versioned prefill이나 delta replay와의 순서 설계가 필요하다.

### 5. Write freeze는 짧고 fenced해야 한다

마지막 동기화 구간에서 흔히 짧은 write freeze가 필요하다.

원칙:

- 가능한 짧게 유지
- monotonic fence token 사용
- freeze 대상 scope를 좁게 유지
- freeze 동안 대기/거부 정책 명시

즉, freeze는 단순 뮤텍스가 아니라 **최종 handoff 경계**다.

### 6. Cutover soak과 rollback window

전환 직후 바로 cleanup하면 안 된다.

필요한 것:

- receiver-only soak window
- hit ratio 회복 추적
- stale route miss 감시
- donor read-only drain
- fast rollback 가능 시간 유지

이 기간이 있어야 "전환은 성공했지만 캐시 품질은 아직 불안정"한 상태를 안전하게 흡수할 수 있다.

### 7. Observability

운영자는 다음을 즉시 봐야 한다.

- receiver warmup progress
- prefill completion ratio
- freeze start/end time
- post-cutover cache hit ratio
- donor/receiver latency split
- rollback 가능한지 여부

전환 성공 여부는 switch 명령이 아니라 soak 구간 지표가 말해 준다.

## 실전 시나리오

### 시나리오 1: stateful cache shard 이동

문제:

- 새 노드로 shard를 옮기면 cache miss가 폭증한다

해결:

- donor hit log 기반으로 hot keys를 prefill한다
- delta apply가 끝난 뒤 짧은 write freeze를 건다
- cutover 후 receiver-only soak에서 hit ratio를 본다

### 시나리오 2: tenant reassignment

문제:

- 큰 tenant를 dedicated cell로 옮긴다

해결:

- tenant hotset을 우선 prefill한다
- tenant scope write freeze만 적용한다
- 다른 tenant는 계속 정상 처리한다

### 시나리오 3: region evacuation 중 shard 이동

문제:

- target region은 cold start 상태다

해결:

- low-rate warmup traffic부터 보낸다
- read-heavy prefill과 state catch-up을 병행한다
- full cutover 전 cache hit / latency guardrail을 확인한다

## 코드로 보기

```pseudo
function cutover(shard, donor, receiver):
  receiver.restore(snapshot(shard))
  prefillHotset(receiver, donor.hotKeys(shard))
  while lag(shard, donor, receiver) > threshold:
    receiver.apply(donor.delta(shard))
  token = issueFence(shard)
  donor.freezeWrites(shard, token, timeout=500ms)
  switchRouting(shard, receiver, token)
  startSoakWindow(shard)
```

```java
public void prewarm(ShardId shardId) {
    Hotset hotset = hotsetPlanner.plan(shardId);
    prefillExecutor.prefill(shardId, hotset);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| No warmup | 단순하다 | cold start spike가 크다 | 매우 작은 상태 |
| Hotset prefill | 효과가 좋다 | popularity metadata가 필요하다 | 대부분의 read-heavy state |
| Full preload | 전환 품질이 좋다 | 시간과 비용이 크다 | 상태가 작거나 매우 중요할 때 |
| Short write freeze | 정합성이 좋다 | 일시 대기/거부가 생긴다 | 최종 cutover 구간 |
| Freeze-free eventual cutover | 사용자 영향이 적다 | final race를 흡수할 설계가 필요하다 | 일부 eventual workloads |

핵심은 receiver warmup / cache prefill / write freeze가 부가 최적화가 아니라 **상태 전환의 마지막 품질과 정합성을 보장하는 운영 절차**라는 점이다.

## 꼬리질문

> Q: snapshot 복구만 끝나면 바로 cutover하면 안 되나요?
> 의도: state copy와 runtime readiness 차이 이해 확인
> 핵심: 안 된다. cache, connection, index, hotset이 아직 cold하면 전환 직후 tail latency가 크게 튈 수 있다.

> Q: write freeze를 왜 꼭 짧게 유지해야 하나요?
> 의도: handoff 경계 설계 확인
> 핵심: freeze는 정합성을 위해 필요하지만 길어지면 사용자 경로와 backlog에 직접 영향을 주기 때문이다.

> Q: prefill을 많이 할수록 항상 좋은가요?
> 의도: preload 비용 감각 확인
> 핵심: 아니다. donor/backend를 압박하거나 stale 데이터를 미리 올릴 수 있어 hotset 중심 전략이 더 현실적일 수 있다.

> Q: cutover 성공은 무엇으로 판단하나요?
> 의도: soak observability 확인
> 핵심: switch 완료 여부보다 post-cutover hit ratio, latency, stale route miss 같은 soak 지표로 보는 편이 정확하다.

## 한 줄 정리

Receiver warmup / cache prefill / write freeze cutover 설계는 상태 이동 직후의 cold start와 final write race를 줄여, 전환 순간뿐 아니라 전환 직후의 품질까지 안전하게 만드는 운영 설계다.
