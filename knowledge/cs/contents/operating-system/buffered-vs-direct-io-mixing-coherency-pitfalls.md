---
schema_version: 3
title: Buffered vs Direct IO Mixing Coherency Pitfalls
concept_id: operating-system/buffered-vs-direct-io-mixing-coherency-pitfalls
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- buffered-vs-direct
- io-mixing-coherency
- pitfalls
- io-mixing
aliases:
- buffered vs direct IO mixing
- O_DIRECT page cache coherency
- direct IO invalidation
- page cache direct IO pitfall
- mixing buffered direct same file
- file coherency contract
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/page-cache-thrash-vs-direct-io.md
- contents/operating-system/direct-io-alignment-checklist.md
- contents/operating-system/page-cache-dirty-writeback-fsync.md
- contents/operating-system/mmap-vs-read-page-cache-behavior.md
- contents/operating-system/io-scheduler-blk-mq-basics.md
- contents/operating-system/posix-fadvise-madvise-page-cache-hints.md
symptoms:
- O_DIRECT를 켰는데 같은 file 영역을 buffered I/O로도 만져 latency와 coherency가 흔들린다.
- direct I/O가 page cache를 우회한다고 믿었지만 invalidation과 alignment 비용을 놓쳤다.
- mmap/read와 direct write를 섞은 뒤 읽은 데이터 freshness가 헷갈린다.
expected_queries:
- O_DIRECT와 buffered I/O를 같은 파일에서 섞으면 왜 위험해?
- direct I/O는 page cache coherency와 invalidation을 어떻게 직접 관리하게 해?
- buffered vs direct I/O mixing이 성능 튜닝이 아니라 계약인 이유는?
- page cache, mmap, direct I/O를 섞을 때 어떤 pitfall을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 O_DIRECT와 buffered/page-cache I/O를 같은 file이나 같은 range에서 섞는 것이
  단순 성능 튜닝이 아니라 coherency, invalidation, alignment, freshness 계약을 직접
  관리하는 선택이라는 점을 설명한다.
---
# Buffered vs Direct I/O Mixing, Coherency Pitfalls

> 한 줄 요약: `O_DIRECT`와 buffered/page-cache I/O를 같은 파일·같은 영역에서 섞는 것은 성능 튜닝이 아니라 coherency와 invalidation 계약을 직접 관리하는 선택이어서, 잘못 섞으면 기대보다 느리고 더 헷갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Page Cache Thrash vs Direct I/O](./page-cache-thrash-vs-direct-io.md)
> - [Direct I/O Alignment Checklist](./direct-io-alignment-checklist.md)
> - [Page Cache, Dirty Writeback, fsync](./page-cache-dirty-writeback-fsync.md)
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [I/O Scheduler, blk-mq Basics](./io-scheduler-blk-mq-basics.md)
> - [posix_fadvise, madvise, Page Cache Hints](./posix-fadvise-madvise-page-cache-hints.md)

> retrieval-anchor-keywords: buffered vs direct I/O, O_DIRECT mixing, page cache coherency, direct I/O invalidation, cache bypass, same file mixed I/O, direct buffered race, file region consistency

## 핵심 개념

많은 팀이 direct I/O를 "page cache를 안 쓰니 캐시 오염만 줄어드는 옵션"으로 이해한다. 하지만 buffered I/O와 direct I/O를 같은 파일 또는 같은 file range에서 섞으면, 문제는 단순 속도가 아니라 visibility/coherency/invalidation이 된다.

- `buffered I/O`: page cache를 통해 읽고 쓰는 일반 파일 I/O다
- `direct I/O`: page cache를 우회하려는 I/O 경로다
- `coherency`: 어느 경로가 최신 데이터를 본다고 믿을 수 있는지에 대한 계약이다
- `invalidation`: stale page cache나 stale view를 비우는 과정이다

왜 중요한가:

- DB, analytics, export pipeline이 같은 파일을 서로 다른 I/O 경로로 접근할 수 있다
- 일부 경로는 최신 데이터를 읽는다고 믿지만 실제로는 stale cache가 남을 수 있다
- direct I/O가 page cache pollution을 줄여도 전체 시스템 계약은 더 복잡해진다

## 깊이 들어가기

### 1. direct I/O는 page cache를 "항상 완전히 안전하게 무시"하는 주문이 아니다

`O_DIRECT`는 cache bypass 성격을 주지만, 운영 감각에서는 다음을 같이 봐야 한다.

- alignment 제약
- filesystem/driver 특성
- 같은 file range를 buffered path가 동시에 건드리는지

즉 direct I/O는 단일 path에서는 단순할 수 있어도 mixed path에서는 계약이 급격히 어려워진다.

### 2. 같은 file region을 mixed path로 접근하면 stale view 문제가 생긴다

한쪽은 page cache를 믿고, 다른 쪽은 직접 storage를 본다고 생각하면 다음이 꼬일 수 있다.

- buffered reader는 old cached page를 본다
- direct writer는 storage에 새 내용을 썼다고 믿는다
- invalidate/serialization이 없으면 두 경로의 최신성 계약이 모호해진다

이 문제는 "가끔 이상한 값이 읽힌다"는 형태로 나타나서 더 위험하다.

### 3. page cache pollution을 줄이는 것과 전체 시스템을 단순하게 만드는 것은 다르다

direct I/O의 장점은 분명하다.

- 큰 scan이 hot page cache를 덜 오염시킨다
- DB/analytics path에 유리할 수 있다

하지만 그 대가도 크다.

- app이 buffering/backpressure를 더 직접 다룬다
- mixed readers/writers 계약이 복잡해진다
- readahead/cache hint로 해결될 문제를 과하게 어렵게 만들 수 있다

즉 direct I/O는 성능 isolation 도구이지, 무조건적인 정답이 아니다.

### 4. `mmap()`이 섞이면 더 위험해진다

mapped reader는 page cache/coherency 문제를 더 복잡하게 만든다.

- path는 file-backed mapping을 믿는다
- 다른 path는 direct I/O로 storage를 건드린다
- 어느 쪽을 authoritative view로 볼지 애매해진다

이 경우는 단순 buffered vs direct 문제가 아니라 mapping coherence 문제로 읽어야 한다.

## 실전 시나리오

### 시나리오 1: analytics batch는 direct I/O로 읽는데 API는 buffered read로 같은 파일을 본다

가능한 원인:

- batch는 cache pollution을 줄였지만
- API는 page cache stale/hotness 계약을 별도로 가진다
- 같은 file region을 두 경로가 다르게 해석한다

대응 감각:

- file/range ownership을 분리한다
- mixed path를 같은 region에서 피한다
- 꼭 섞어야 한다면 serialization/invalidation contract를 명시한다

### 시나리오 2: direct write 이후 buffered read가 바로 최신 데이터를 못 보는 것 같다

가능한 원인:

- stale cached page
- invalidate timing이 불분명하다
- 파일시스템/경로 특성에 대한 가정이 지나치게 낙관적이다

### 시나리오 3: direct I/O로 바꿨는데 성능이 좋아지지 않고 디버깅만 어려워졌다

가능한 원인:

- 실제 병목은 cache pollution이 아니었다
- readahead/fadvise로도 충분했다
- mixed path coherency와 alignment 비용이 새 복잡도를 만들었다

## 코드로 보기

### 위험한 mental model

```text
buffered API readers
  + direct batch writer
  + maybe mmap reader too
  -> same file regions
  -> unclear freshness contract
```

### 더 나은 질문

```text
Can one file region have one dominant I/O mode?
Can scan/export data be separated from latency-sensitive buffered data?
Would fadvise/drop-behind solve the pollution without changing the coherency model?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| all buffered I/O | contract가 단순하다 | cache pollution에 약할 수 있다 | general-purpose files |
| all direct I/O | cache 간섭을 줄인다 | 앱 복잡도와 alignment 부담이 크다 | DB-like engines |
| mixed by file/region ownership | isolation과 coherency를 같이 관리하기 쉽다 | 설계 discipline이 필요하다 | complex storage paths |
| mixed ad hoc | 구현은 쉬워 보인다 | stale view와 debug complexity가 커진다 | 피하는 편이 좋다 |

## 꼬리질문

> Q: direct I/O를 쓰면 buffered 경로도 자동으로 최신 데이터를 보나요?
> 핵심: 그렇게 단순화하면 안 된다. mixed path에서는 invalidate와 ownership 계약을 따로 생각해야 한다.

> Q: direct I/O는 page cache thrash를 줄이는데 왜 위험한가요?
> 핵심: cache pollution은 줄일 수 있어도, 같은 file/range를 buffered path와 섞으면 coherency 모델이 복잡해지기 때문이다.

> Q: 언제 direct I/O 대신 다른 선택지를 먼저 보나요?
> 핵심: readahead 조정이나 `fadvise`로 cache pollution을 줄일 수 있는 mixed workload에서는 먼저 그 경로를 검토하는 편이 안전하다.

## 한 줄 정리

direct I/O는 캐시를 덜 섞이게 할 수 있지만, buffered/mmap 경로와 같은 file region을 공유하는 순간 성능 문제보다 coherency 계약 문제가 더 커질 수 있다.
