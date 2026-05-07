---
schema_version: 3
title: Dirty Page Ratios Writeback Tuning
concept_id: operating-system/dirty-page-ratios-writeback-tuning
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- dirty-page-ratios
- writeback-tuning
- dirty-background-ratio
- dirty-ratio
aliases:
- dirty page ratios
- writeback tuning
- dirty_background_ratio dirty_ratio
- dirty_bytes dirty_background_bytes
- flush latency spike
- page cache dirty tuning
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/fsync-tail-latency-dirty-writeback-debugging.md
- contents/operating-system/dirty-throttling-balance-dirty-pages-writeback-stalls.md
- contents/operating-system/page-cache-thrash-vs-direct-io.md
- contents/operating-system/psi-pressure-stall-information-runtime-debugging.md
- contents/operating-system/vm-swappiness-reclaim-behavior.md
- contents/operating-system/kswapd-vs-direct-reclaim-latency.md
symptoms:
- write burst를 완충하려다 dirty page가 쌓여 한 번에 flush되며 latency spike가 난다.
- dirty_ratio와 dirty_background_ratio를 높였더니 writer throttling 시점이 늦어졌지만 p99가 커진다.
- memory reclaim과 writeback이 겹쳐 application write latency가 흔들린다.
expected_queries:
- dirty page ratio와 writeback tuning은 latency spike와 어떻게 연결돼?
- dirty_background_ratio dirty_ratio dirty_bytes를 어떻게 해석해야 해?
- writeback tuning을 잘못하면 flush가 몰려 p99가 커질 수 있어?
- page cache dirty writeback과 reclaim, PSI를 함께 보는 기준은?
contextual_chunk_prefix: |
  이 문서는 dirty page ratio와 writeback tuning이 write burst를 완충하지만 너무 크게 잡거나
  storage 속도와 맞지 않으면 flush가 몰려 latency spike와 dirty throttling을 만드는
  trade-off를 다룬다.
---
# Dirty Page Ratios, Writeback Tuning

> 한 줄 요약: dirty page 비율과 writeback 튜닝은 쓰기 폭주를 완충하는 장치지만, 잘못 잡으면 flush가 몰려 latency spike를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [Fsync Tail Latency, Dirty Writeback, Backend Debugging](./fsync-tail-latency-dirty-writeback-debugging.md)
> - [Dirty Throttling, balance_dirty_pages, Writeback Stalls](./dirty-throttling-balance-dirty-pages-writeback-stalls.md)
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)
> - [vm.swappiness, Reclaim Behavior](./vm-swappiness-reclaim-behavior.md)
> - [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)

> retrieval-anchor-keywords: dirty_ratio, dirty_background_ratio, dirty_bytes, dirty_background_bytes, writeback, balance_dirty_pages, flush burst, dirty page pressure, writer throttling, dirty throttling, page cache debt

## 핵심 개념

파일 쓰기는 바로 디스크로 가지 않고 page cache에 dirty page로 쌓인 뒤 writeback으로 내려간다. dirty page 비율은 이 누적을 얼마나 허용할지 정한다.

- `dirty_ratio`: 전체 메모리에서 dirty page가 차지할 수 있는 비율
- `dirty_background_ratio`: background writeback이 시작되는 기준이다
- `dirty_bytes`: 절대 바이트 기준 설정이다
- `balance_dirty_pages`: 쓰기 속도를 조절하는 메커니즘이다

왜 중요한가:

- dirty page를 너무 많이 허용하면 flush burst가 생긴다
- 너무 빡빡하면 write path가 자주 막힌다
- writeback은 디스크 문제 같지만 사실 메모리 정책과도 연결된다

이 문서는 [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)와 [kswapd vs Direct Reclaim, Latency](./kswapd-vs-direct-reclaim-latency.md)를 writeback 관점에서 잇는다.

## 깊이 들어가기

### 1. dirty page는 버퍼이자 위험 신호다

dirty page는 성능을 위해 쌓인다.

- 잠깐의 burst를 흡수한다
- 디스크를 배치로 쓰게 한다
- 하지만 너무 쌓이면 한 번에 몰아서 쓰게 된다

### 2. background ratio와 ratio는 역할이 다르다

- background 기준은 "이제 천천히 치우자"는 신호다
- ratio 기준은 "이제 더는 안 된다"는 신호다

이 둘이 너무 멀거나 가까우면 둘 다 문제가 된다.

### 3. writeback burst는 latency spike를 만든다

쓰기 큐가 한 번에 밀리면 다음이 생긴다.

- flush thread가 바빠진다
- storage queue가 밀린다
- direct reclaim과 겹치면 더 느려진다

### 4. dirty tuning은 workload별로 달라야 한다

- 로그/append workload
- DB/WAL
- mixed API with temp files
- batch ETL

각각 허용 가능한 dirty buffering이 다르다.

## 실전 시나리오

### 시나리오 1: 주기적으로 디스크가 버벅인다

가능한 원인:

- dirty page가 많이 쌓였다가 한 번에 flush된다
- background writeback이 너무 늦게 시작된다
- flush와 reclaim이 겹친다

진단:

```bash
cat /proc/meminfo | grep -E 'Dirty|Writeback'
sysctl vm.dirty_ratio
sysctl vm.dirty_background_ratio
iostat -x 1
```

### 시나리오 2: log writer가 갑자기 느려진다

가능한 원인:

- balance_dirty_pages가 강하게 작동한다
- dirty page 허용치가 너무 낮다
- fsync와 writeback이 겹친다

### 시나리오 3: 배치 후 전체 노드 latency가 오른다

가능한 원인:

- 대량 writeback burst
- page cache pressure
- io pressure와 memory pressure 동시 상승

이 경우는 [PSI, Pressure Stall Information, Runtime Debugging](./psi-pressure-stall-information-runtime-debugging.md)와 같이 본다.

## 코드로 보기

### dirty 설정 확인

```bash
sysctl vm.dirty_ratio
sysctl vm.dirty_background_ratio
sysctl vm.dirty_bytes
sysctl vm.dirty_background_bytes
```

### dirty 상태 확인

```bash
cat /proc/meminfo | grep -E 'Dirty|Writeback'
```

### 단순 모델

```text
write -> dirty page accumulates
  -> background writeback starts
  -> dirty limit reached
  -> writer throttled or flush burst occurs
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 높은 dirty ratio | write burst를 흡수 | flush가 몰릴 수 있다 | throughput 우선 |
| 낮은 dirty ratio | burst를 줄인다 | writer가 자주 막힌다 | latency 우선 |
| byte-based tuning | 예측성이 높다 | 운영 설계가 필요하다 | 대형 메모리 서버 |
| 기본값 유지 | 단순하다 | workload와 안 맞을 수 있다 | 일반 환경 |

## 꼬리질문

> Q: dirty page는 왜 쌓이나요?
> 핵심: 디스크 쓰기를 배치하고 write throughput을 높이기 위해서다.

> Q: dirty_ratio를 높이면 무조건 좋은가요?
> 핵심: 아니다. flush burst와 latency spike가 커질 수 있다.

> Q: background ratio와 ratio의 차이는?
> 핵심: 하나는 미리 치우는 기준이고, 다른 하나는 더 못 쌓게 하는 기준이다.

## 한 줄 정리

dirty page ratios와 writeback tuning은 write burst를 흡수하지만, 너무 느슨하거나 너무 빡빡하면 둘 다 latency 문제를 만든다.
