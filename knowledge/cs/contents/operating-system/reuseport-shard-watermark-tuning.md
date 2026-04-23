# SO_REUSEPORT Shard Imbalance and Per-Listener Pause Watermark Tuning

> 한 줄 요약: `SO_REUSEPORT`는 accept 경합을 줄여 주지만 backlog도 listener별로 쪼개 버린다. 그래서 port 전체 평균이 멀쩡해 보여도 특정 shard만 먼저 넘칠 수 있고, pause/resume 정책도 "포트 하나"가 아니라 "listener마다 다른 headroom" 기준으로 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Listener Overload Thresholds and Accept Pause Policy](./listener-overload-thresholds-accept-pause-policy.md)
> - [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)
> - [Socket Accept Queue, Kernel Diagnostics](./socket-accept-queue-kernel-diagnostics.md)
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)

> retrieval-anchor-keywords: reuseport shard watermark tuning, SO_REUSEPORT shard imbalance, reuseport shard skew, per-listener backlog threshold, per-listener accept watermark, reuseport pause policy, reuseport resume policy, hot shard backlog, cold shard backlog, listener-local backlog, listener-local headroom, port aggregate backlog lie, max shard fill ratio, fill spread, hot listener fill, weighted shard share, reuseport BPF steering, per-shard accept queue, shard-local session-init queue, shard-local CQ budget, listener hysteresis under reuseport, accept overload shard skew

## 핵심 개념

`SO_REUSEPORT`에서 중요한 변화는 "워커가 많아진다"가 아니라, **listen socket 자체가 여러 개로 분리된다**는 점이다.

- 각 shard는 자기 `listen fd`, 자기 accept queue, 자기 `sk_ack_backlog`를 가진다
- `listen(backlog)`와 `somaxconn`이 만드는 상한도 shard별로 적용된다
- port 전체 합계는 capacity planning에는 쓸 수 있지만, pause trigger에는 늦다
- pause/resume은 "전체 포트를 한꺼번에 멈출지"와 "hot shard만 멈출지"를 분리해 설계해야 한다

왜 중요한가:

- hot shard 하나가 `ListenOverflows`를 만들 때 다른 shard는 거의 비어 있을 수 있다
- aggregate `Recv-Q`만 보면 overload를 늦게 감지한다
- shared downstream이 아닌데도 global pause를 걸면 cold shard capacity를 버린다
- 반대로 shared session-init queue나 shared memory budget이 있는 서버는 local pause만으로는 보호가 안 된다

## 깊이 들어가기

### 1. `SO_REUSEPORT`는 backlog도 shard별로 쪼갠다

`SO_REUSEPORT`를 켜면 "포트 하나, backlog 하나"가 아니라 아래처럼 바뀐다.

```text
port :443
  -> listener A backlog
  -> listener B backlog
  -> listener C backlog
  -> listener D backlog
```

이때 중요한 지표는 port 합계보다 shard별 fill ratio다.

```text
local_fill_i = ack_backlog_i / effective_backlog_i
effective_backlog_i = min(listen_backlog_i, somaxconn_i)
```

예를 들어 4개 shard가 모두 `effective_backlog = 512`라고 하자.

| shard | `ack_backlog` | `local_fill` |
|---|---:|---:|
| A | 460 | 0.90 |
| B | 40 | 0.08 |
| C | 32 | 0.06 |
| D | 20 | 0.04 |

이때 port aggregate는 `552 / 2048 = 0.27`이라서 멀쩡해 보인다. 하지만 shard A는 이미 90%까지 찼다. aggregate 70% 기준 정책은 아무 일도 안 하다가 shard A에서 먼저 overflow를 맞는다.

즉 `SO_REUSEPORT` 환경에서는:

- port average보다 `max(local_fill_i)`가 더 중요하다
- `ListenOverflows`/`ListenDrops`는 host-level 누적 카운터라 "어느 shard가 터졌는지"를 직접 알려 주지 않는다
- `ss -ltn`도 row별로 읽어야 한다. 한 줄로 합쳐 보면 hot shard가 가려진다

### 2. 기대 분배가 균등하지 않을 수도 있다

기본 hash가 꽤 잘 분산되더라도 실무에서는 shard 편중이 자주 생긴다.

- RSS / IRQ affinity 때문에 특정 CPU 쪽 listener가 더 자주 깨어난다
- warm connection, sticky client source port, NAT 패턴이 hash를 한쪽으로 몰 수 있다
- `SO_REUSEPORT` BPF selector를 쓰면 의도적으로 가중 분배를 할 수 있다

그래서 "1/N씩 들어와야 정상"이라고 단정하면 안 된다. 먼저 **의도된 share**를 정하고, 실제 분배가 그 share에서 얼마나 벗어났는지 봐야 한다.

```text
planned_share_i = default 1 / active_shards
               or BPF / deployment weight

accept_rate_skew_i =
  actual_accept_rate_i / max(port_accept_rate * planned_share_i, 1)
```

해석 규칙:

- `planned_share_i`가 다르면 watermark도 똑같이 둘 필요가 없다
- 의도적으로 2배 traffic을 받는 shard라면 backlog 자체는 같아도 high-water를 더 보수적으로 둘 수 있다
- 의도치 않은 skew라면 watermark 튜닝과 함께 steering, IRQ, CPU locality까지 같이 봐야 한다

### 3. per-listener watermark는 "비율"과 "남은 슬롯"을 같이 본다

`SO_REUSEPORT` shard에서는 보통 local ratio 하나만 보기보다, free slot budget을 같이 두는 편이 낫다.

```text
local_free_i = effective_backlog_i - ack_backlog_i

pause_i if
  local_fill_i >= accept_high_i ||
  local_free_i <= drain_reserve_i + skew_burst_i ||
  local_init_depth_i >= init_high_i
```

여기서:

- `drain_reserve_i`: cancel 이후 CQE drain, terminal CQE, in-flight handoff를 흡수하는 기본 reserve
- `skew_burst_i`: hot shard가 샘플 한두 번 사이에 더 받아올 수 있는 추가 burst budget
- `local_init_depth_i`: shard별 init queue가 있다면 그 로컬 depth, shared queue라면 global queue depth다

`skew_burst_i`는 복잡한 공식보다 아래처럼 운영적으로 잡는 편이 실용적이다.

- hot shard의 최근 1초 accept burst p95
- 또는 한 reactor turn에서 실제로 handoff한 accept batch 상한
- 또는 "rearm 직후 한 번에 더 들어올 수 있는 connection 수"의 보수 추정치

핵심은 `SO_REUSEPORT` hot shard에서는 **"몇 퍼센트 찼나"보다 "안전하게 남겨 둬야 할 슬롯이 얼마인가"**가 더 중요해진다는 점이다.

### 4. shard skew가 커질수록 high-water는 hot shard만 더 낮춰야 한다

출발점으로는 balanced case와 skew case를 분리해 두는 편이 좋다.

| 상태 | 조건 예시 | hot shard high-water | hot shard low-water | 운영 의미 |
|---|---|---:|---:|---|
| balanced | `max_fill - median_fill < 0.10` | 0.65 ~ 0.70 | 0.35 ~ 0.40 | shard 간 차이가 작다. 일반 listener 정책으로 충분하다 |
| moderate skew | `max_fill - median_fill >= 0.15` | 0.55 ~ 0.60 | 0.25 ~ 0.35 | hot shard만 먼저 pause 후보로 본다 |
| severe skew | `max_fill >= 0.80` 그리고 `max_fill - median_fill >= 0.25` | 0.45 ~ 0.55 | 0.20 ~ 0.30 | aggregate가 낮아도 local pause를 먼저 건다 |

이 표의 핵심은 간단하다.

- skew가 커질수록 **모든 shard를 같이 낮추는 게 아니라 hot shard만 보수적으로 만든다**
- low-water도 함께 더 낮춰야 resume flap이 줄어든다
- cold shard는 계속 accept를 받아 전체 처리량을 지킬 수 있다

### 5. pause/resume은 local policy와 global policy를 분리해야 한다

`SO_REUSEPORT` 환경의 실전 정책은 보통 세 가지다.

| 정책 | 언제 맞는가 | 장점 | 함정 |
|---|---|---|---|
| local-only pause | shard별 ring, shard별 init queue, shard별 memory budget이 분리됨 | hot shard만 보호하고 cold shard는 계속 살린다 | shared downstream이 있으면 보호 범위가 부족하다 |
| global-only pause | 모든 shard가 하나의 shared session-init queue나 shared mem budget을 씀 | 보호 규칙이 단순하다 | hot shard 하나 때문에 전체 포트를 너무 일찍 멈출 수 있다 |
| hybrid pause | accept는 shard별, init/auth/TLS는 shared budget을 씀 | skew와 shared saturation을 같이 다룬다 | 지표 설계가 조금 더 복잡하다 |

실무 기본값으로는 hybrid가 가장 안전하다.

1. hot shard는 local fill과 local free slot으로 먼저 pause한다
2. shared init queue, shared CQ backlog, shared memory pressure가 임계치를 넘으면 global pause로 승격한다
3. resume은 local low-water와 global low-water를 둘 다 만족할 때만 한다

즉 `SO_REUSEPORT`에서는 "어느 shard를 멈출지"와 "포트 전체를 멈출지"가 다른 질문이다.

### 6. resume는 hottest shard 기준으로 보수적으로 해야 한다

pause보다 resume이 더 자주 실패한다. 이유는 hot shard가 rearm 직후 다시 traffic를 빨아들이기 때문이다.

권장 규칙:

- `max(local_fill_i)`가 low-water 아래로 내려왔는지 본다
- `max_fill - median_fill` spread가 충분히 줄었는지 본다
- hot shard의 `recent_overflow_delta == 0`인 window를 한 번 더 확인한다
- shared downstream이 있으면 global init/CQ low-water도 같이 만족해야 한다

resume 조건을 aggregate backlog나 port 평균만으로 두면, cold shard가 비어 있다는 이유로 hot shard를 너무 빨리 다시 열게 된다.

## 코드로 보기

아래는 local-first, global-second 정책의 예시다.

```text
for each shard i:
  effective_backlog_i = min(cfg.listen_backlog_i, metrics.somaxconn_i)
  fill_i = ack_backlog_i / max(effective_backlog_i, 1)
  free_i = effective_backlog_i - ack_backlog_i

median_fill = median(fill_*)
spread = max(fill_*) - median_fill

for each shard i:
  is_hot = fill_i - median_fill >= 0.15
  accept_high_i = is_hot ? 0.55 : 0.70
  accept_low_i  = is_hot ? 0.25 : 0.40

  should_pause_local_i =
    fill_i >= accept_high_i ||
    free_i <= drain_reserve_i + skew_burst_i ||
    local_init_depth_i >= init_high_i

should_pause_global =
  shared_init_depth >= shared_init_high ||
  shared_cq_backlog >= shared_cq_high ||
  hot_shard_count >= 2

resume_i =
  paused_i &&
  fill_i <= accept_low_i &&
  local_init_depth_i <= init_low_i &&
  shared_init_depth <= shared_init_low &&
  shared_cq_backlog <= shared_cq_low &&
  recent_overflow_delta_i == 0
```

여기서 중요한 포인트:

- port aggregate 대신 `median_fill`, `spread`, `hot_shard_count`를 쓴다
- hot shard에만 더 낮은 high-water를 적용한다
- shared budget이 있으면 global pause 승격 조건을 따로 둔다

## 관측 체크리스트

`SO_REUSEPORT` shard skew는 "queue가 찼다"보다 "어느 shard만 찼는가"를 먼저 보여 줘야 한다.

- `ss -ltn` LISTEN row별 `Recv-Q`, `Send-Q`
- `hot_fill = max(Recv-Q_i / max(Send-Q_i, 1))`
- `median_fill`, `fill_spread = hot_fill - median_fill`
- shard별 accept rate, pause count, rearm count, cancel count
- shard별 CQ backlog 또는 accept CQE batch 크기
- shard별 또는 shared session-init queue depth / init latency
- host-level `ListenOverflows`, `ListenDrops` delta

해석 순서:

1. row별 `ss -ltn`으로 hot shard를 찾는다
2. `fill_spread`가 큰지 본다
3. host-level overflow/drop으로 실제 손실이 있었는지 본다
4. hot shard의 CQ / init queue가 local bottleneck인지, shared bottleneck인지 가른다

세부 관측 절차는 [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)에서 이어서 보면 된다.

## 실전 시나리오

### 시나리오 1: 포트 전체 backlog는 30%인데 connect timeout이 난다

가능한 원인:

- `SO_REUSEPORT` shard 하나만 85~95%까지 찼다
- `ListenOverflows`는 늘지만 aggregate snapshot은 낮다
- pause trigger가 port 평균 기준이라 너무 늦다

대응:

- per-listener fill ratio로 정책을 바꾼다
- hot shard만 더 낮은 high-water를 둔다
- shard별 accept rate와 IRQ / CPU affinity를 같이 본다

### 시나리오 2: hot shard 하나 때문에 전체 listener가 자주 멈춘다

가능한 원인:

- local bottleneck인데 global pause만 쓰고 있다
- shard별 init queue는 분리돼 있는데 policy가 전역 평균 기준이다

대응:

- local pause를 먼저 적용한다
- global pause는 shared queue나 shared memory pressure 때만 승격한다
- cold shard는 계속 수용하게 둬서 전체 처리량을 지킨다

### 시나리오 3: local pause는 잘 되는데 resume 직후 같은 shard가 다시 터진다

가능한 원인:

- hot shard low-water가 너무 높다
- spread가 줄기 전에 rearm한다
- rearm 직후 burst를 흡수할 skew reserve가 없다

대응:

- hot shard low-water를 더 낮춘다
- `max_fill - median_fill` spread가 줄어드는지 확인한다
- `skew_burst_i` reserve를 키우고 recent overflow zero window를 요구한다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| aggregate port watermark | 구현이 단순하다 | hot shard overflow를 놓치기 쉽다 | `SO_REUSEPORT`가 없거나 shard skew가 거의 없을 때 |
| per-listener watermark | local overload를 빨리 잡는다 | 지표와 제어가 조금 더 복잡하다 | 대부분의 `SO_REUSEPORT` 서버 |
| hot shard만 보수적 tuning | cold shard capacity를 살린다 | skew 원인을 숨긴 채 운영으로만 버티게 될 수 있다 | steering 수정 전 임시 방어 |
| global pause 승격 | shared downstream 보호에 좋다 | 전체 수용량이 크게 줄 수 있다 | shared init/TLS/auth queue가 실제 병목일 때 |

## 꼬리질문

> Q: `SO_REUSEPORT`면 backlog도 자동으로 균등하게 쓰이나요?
> 핵심: 아니다. 분산은 좋아지지만 skew는 여전히 생길 수 있고, 각 listener backlog는 별도다.

> Q: 왜 port 전체 `Recv-Q` 합계로는 안 되나요?
> 핵심: hot shard 하나가 먼저 터질 수 있어서 aggregate는 늦은 지표가 되기 쉽다.

> Q: high-water를 모든 shard에 똑같이 낮추면 안 되나요?
> 핵심: 가능은 하지만 cold shard capacity까지 버리게 된다. local bottleneck이면 hot shard만 더 보수적으로 두는 편이 낫다.

> Q: global pause는 언제 꼭 필요한가요?
> 핵심: shard 뒤에 shared session-init queue, shared CQ budget, shared memory pressure가 있을 때다.

## 한 줄 정리

`SO_REUSEPORT` 서버의 accept 정책은 port 평균 backlog가 아니라 listener별 effective backlog와 shard skew를 기준으로 세워야 하며, pause/resume도 hot shard local control과 shared downstream global control을 분리해서 설계해야 한다.
