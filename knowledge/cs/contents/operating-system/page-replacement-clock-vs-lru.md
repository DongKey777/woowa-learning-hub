---
schema_version: 3
title: Page Replacement, Clock vs LRU
concept_id: operating-system/page-replacement-clock-vs-lru
canonical: false
category: operating-system
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- clock-vs-lru-tradeoff
- working-set-vs-policy
aliases:
- page replacement basics
- clock vs lru
- lru replacement algorithm
- clock page replacement algorithm
- page eviction basics
- page cache eviction
- working set memory basics
- thrashing page replacement
- 왜 lru 대신 clock 써요
- 메모리 꽉 차면 무엇을 버리나요
- os cache eviction beginner
- 언제 clock 알고리즘 쓰나요
symptoms:
- Clock이랑 LRU를 왜 따로 배우는지 감이 안 와요
- page cache eviction이 LRU cache 구현이랑 같은 말인가요
- page replacement를 볼 때 working set이 더 중요하다는 말이 헷갈려요
intents:
- comparison
- design
prerequisites:
- operating-system/demand-paging-page-fault-primer
- operating-system/memory-management-basics
next_docs:
- operating-system/workingset-refault-page-cache-reclaim-debugging
- operating-system/page-cache-thrash-vs-direct-io
linked_paths:
- contents/operating-system/memory-management-numa-page-replacement-thrashing.md
- contents/operating-system/workingset-refault-page-cache-reclaim-debugging.md
- contents/operating-system/page-cache-thrash-vs-direct-io.md
- contents/data-structure/lru-cache-basics.md
confusable_with:
- operating-system/memory-management-numa-page-replacement-thrashing
- data-structure/lru-cache-basics
forbidden_neighbors:
- contents/data-structure/lru-cache-basics.md
expected_queries:
- OS에서 Clock이 LRU를 어떻게 근사하는지 비교해줘
- page replacement에서 Clock과 LRU를 언제 다르게 이해해야 해?
- 캐시 교체 정책 LRU랑 운영체제 페이지 교체 LRU는 뭐가 달라?
- page cache eviction 설명할 때 working set이 왜 더 중요하다고 해?
- page replacement 알고리즘을 처음 비교할 때 Clock vs LRU부터 보고 싶어
contextual_chunk_prefix: |
  이 문서는 운영체제 학습자가 메모리가 모자랄 때 어떤 페이지를 밀어낼지
  볼 때 Clock과 LRU를 어떻게 가를지 결정하게 돕는 chooser다. 최근 사용
  이력 추적 비용, 참조 비트로 대충 근사하기, page fault 급증, 운영체제
  교체 정책과 cache 구현의 차이, working set을 먼저 봐야 하는 이유 같은
  자연어 paraphrase가 본 문서의 비교 기준에 매핑된다.
---
# Page Replacement, Clock vs LRU

> 한 줄 요약: 메모리가 부족할 때 무엇을 내보내는지가 page fault, page cache hit ratio, tail latency를 좌우한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [스케줄러 공정성, page cache, 파일 시스템 기초](./scheduler-fairness-page-cache.md)
> - [NUMA, page replacement, thrashing](./memory-management-numa-page-replacement-thrashing.md)
> - [memory management basics](./memory-management-basics.md)
> - [workingset refault, page cache reclaim debugging](./workingset-refault-page-cache-reclaim-debugging.md)
> - [file descriptor, socket, syscall cost](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [LRU cache basics](../data-structure/lru-cache-basics.md)
> - [buffer pool, read ahead, eviction interaction](../database/buffer-pool-read-ahead-eviction-interaction.md)
> - [operating-system 카테고리 인덱스](./README.md)

> retrieval-anchor-keywords: page replacement basics, clock vs lru, lru replacement algorithm, clock page replacement algorithm, page eviction basics, page cache eviction, working set memory basics, thrashing page replacement, 처음 배우는데 lru clock 차이, 왜 lru 대신 clock 써요, page replacement 큰 그림, 메모리 꽉 차면 무엇을 버리나요, page fault cache hit ratio basics, os cache eviction beginner, buffer pool eviction vs page cache, 언제 clock 알고리즘 쓰나요

---

## 핵심 개념

Page replacement는 메모리가 꽉 찼을 때 어떤 페이지를 쫓아낼지 정하는 일이다.

실무에서 중요한 이유는 단순하다.

- 메모리가 부족하면 page fault가 늘어난다
- page fault가 늘면 CPU가 계산보다 메모리 회수에 시간을 쓴다
- DB buffer pool, Linux page cache, JVM 힙 주변 메모리 압박이 같이 흔들릴 수 있다

`LRU`는 이상적이지만, 모든 접근을 정교하게 기록하는 비용이 크다.  
그래서 커널과 저장소 엔진은 보통 `Clock` 같은 근사 알고리즘을 쓴다.

---

## 깊이 들어가기

### 1. LRU가 이상적인 이유

가장 오래 참조되지 않은 페이지를 버리면 지역성을 잘 살릴 가능성이 높다.

문제는 정확한 LRU를 유지하려면:

- 접근마다 순서를 갱신해야 하고
- 자료구조 유지 비용이 크고
- 락 경쟁이 생기기 쉽다

즉, 정확도는 좋지만 운영 비용이 높다.

### 2. Clock이 현실적인 이유

Clock은 페이지를 원형으로 돌면서 `reference bit`를 확인한다.

- 최근에 사용된 페이지는 한 번 봐주고
- 다시 안 쓰였으면 교체 후보로 삼는다

근사지만 구현이 단순하고, 많은 시스템에서 충분히 잘 작동한다.

### 3. Linux와 저장소 엔진에서의 감각

Linux page cache와 DB buffer pool은 같은 문제가 반복된다.

- 자주 읽는 페이지를 남겨야 한다
- 쓰기 중 dirty page는 즉시 버리기 어렵다
- flush와 reclaim이 겹치면 지연이 커진다

이때 "LRU냐 Clock이냐"보다 더 중요한 건 **working set이 메모리에 들어오는가**다.

---

## 실전 시나리오

### 시나리오 1: 배치 작업 이후 API가 느려짐

배치가 큰 파일을 순차적으로 읽고 나가면서 page cache를 밀어내면, 그 뒤 API는 다시 디스크를 읽어야 할 수 있다.

진단:

```bash
vmstat 1
sar -B 1
grep -E 'pgfault|pgmajfault' /proc/vmstat
free -m
```

### 시나리오 2: DB는 CPU가 낮은데 응답이 튐

buffer pool hit ratio가 떨어지면 page fault와 디스크 I/O가 늘어난다.

이럴 때는 쿼리만 볼 게 아니라:

- 데이터셋 크기
- 캐시 워크셋
- 스키마 변경 직후인지
- batch job 동시 실행 여부

를 같이 봐야 한다.

### 시나리오 3: swap storm

메모리보다 working set이 크면 교체가 연쇄적으로 일어난다.  
이 상태에서는 더 많은 worker를 넣어도 해결되지 않는다.

---

## 코드로 보기

### Clock 의사 코드

```c
while (true) {
    if (frames[hand].reference == 0) {
        victim = frames[hand];
        break;
    }

    frames[hand].reference = 0;
    hand = (hand + 1) % frame_count;
}
```

### LRU가 비싼 이유를 보는 감각

```text
access(page):
  page를 최근 사용 위치로 이동
  자료구조 갱신
  락 확보
  빈번한 교체 시 오버헤드 증가
```

정확한 LRU는 이상적이지만, 고동시성 환경에서는 "정확함" 자체가 비용이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| LRU | 지역성을 잘 반영 | 유지 비용이 높다 | 정확성이 중요한 일부 캐시 |
| Clock | 단순하고 싸다 | 근사치다 | 커널, buffer pool, 일반 캐시 |
| LFU | 자주 쓰는 항목을 보존 | 최근성 반영이 약하다 | 장기 hot key가 뚜렷할 때 |
| FIFO | 구현이 쉽다 | 실제 워크로드와 잘 안 맞는다 | 교육용, 단순 시스템 |

---

## 꼬리질문

> Q: LRU가 왜 항상 최선이 아닌가요?
> 의도: 이론과 구현 비용을 같이 보는지 확인
> 핵심: 정확한 순서 유지 비용과 락 경쟁이 크다.

> Q: Clock이 왜 현실적인가요?
> 의도: 근사 알고리즘의 가치 이해 확인
> 핵심: 구현과 유지 비용이 낮고, 충분히 좋은 히트율을 낼 수 있다.

> Q: page cache와 DB buffer pool은 무엇이 다른가요?
> 의도: OS와 저장소 엔진의 경계를 아는지 확인
> 핵심: 둘 다 페이지를 캐시하지만 관리 주체와 정책이 다르다.

---

## 한 줄 정리

LRU는 이상적이지만 비싸고, Clock은 근사치지만 싸다. 운영에서는 정확도보다 working set과 reclaim 비용이 더 중요하다.
