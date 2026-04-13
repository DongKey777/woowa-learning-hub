# Page Table Overhead, Memory Footprint

> 한 줄 요약: page table은 주소 변환을 위해 필요하지만, 매핑 수와 메모리 크기가 커질수록 숨은 메모리 오버헤드와 fault 비용이 커진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)
> - [vm.max_map_count, mmap-heavy Apps](./vm-max-map-count-mmap-heavy-apps.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)
> - [NUMA, Page Replacement, Thrashing](./memory-management-numa-page-replacement-thrashing.md)

> retrieval-anchor-keywords: page table overhead, page table memory, PTE, PMD, PGD, vmalloc, large address space, mmap footprint, address translation

## 핵심 개념

page table은 가상 주소를 물리 주소로 바꾸는 자료구조다. 메모리가 커지고 매핑이 많아질수록 page table 자체도 메모리를 먹는다.

- `PTE`: 페이지 단위 변환 엔트리다
- `PMD/PGD`: 더 상위 레벨의 page table 엔트리다
- `page table overhead`: 주소 공간 관리에 드는 숨은 메모리다

왜 중요한가:

- 큰 heap이나 mmap-heavy 앱은 page table 메모리도 무시 못 한다
- TLB miss와 page table walk 비용이 늘 수 있다
- 프로세스 RSS만 보면 진짜 footprint를 놓칠 수 있다

이 문서는 [mmap vs read, Page Cache Behavior](./mmap-vs-read-page-cache-behavior.md)와 [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)를 주소 변환 구조 관점에서 잇는다.

## 깊이 들어가기

### 1. page table도 메모리다

가상 주소 공간이 크고 매핑이 많으면 변환 구조도 커진다.

- 매핑 수가 많아질수록 관리 비용이 증가한다
- 일부는 커널 메모리로 잡힌다
- 작은 페이지를 많이 쓰면 오버헤드가 커질 수 있다

### 2. page table walk는 지연을 만든다

TLB miss가 발생하면 page table을 따라 내려가며 변환해야 한다.

- 여러 단계의 lookup이 필요하다
- 캐시 miss가 붙을 수 있다
- huge page는 이 비용을 줄이는 데 도움될 수 있다

### 3. mmap-heavy 앱은 page table footprint가 크다

- 많은 file-backed mapping
- JIT/heap/segment 분리
- shard별 페이지 구조

이런 구조는 footprint뿐 아니라 startup과 fault 경로에도 영향을 준다.

### 4. page table overhead는 RSS보다 늦게 보인다

앱 메모리를 볼 때 heap/RSS만 보면 안 된다.

- page table 메모리는 별도 관찰이 필요하다
- `smaps_rollup`, `pmap`, `/proc/*` 정보가 중요하다
- huge page로 줄어들 수도 있지만 항상 그런 것은 아니다

## 실전 시나리오

### 시나리오 1: 메모리는 충분해 보이는데 커널 메모리가 늘어난다

가능한 원인:

- page table footprint가 커졌다
- 매핑 수가 많다
- VMA와 PTE가 누적된다

진단:

```bash
cat /proc/<pid>/smaps_rollup | grep -E 'Rss|Pss|AnonHugePages'
pmap -x <pid> | tail -n 20
cat /proc/meminfo | grep -E 'PageTables|AnonHugePages'
```

### 시나리오 2: 대형 mmap 앱의 메모리 footprint가 예상보다 크다

가능한 원인:

- page table 자체 오버헤드
- 작은 page 단위의 변환 비용
- 매핑 분할이 지나치다

### 시나리오 3: huge page를 켰는데도 모든 문제가 해결되지 않는다

가능한 원인:

- TLB 이득은 있었지만 page table footprint는 여전히 크다
- fragmentation이나 reclaim이 더 큰 병목이다
- NUMA locality 문제도 함께 있다

## 코드로 보기

### page table 관련 메트릭 보기

```bash
cat /proc/meminfo | grep -E 'PageTables|AnonHugePages|HugePages'
```

### 프로세스 주소 공간 보기

```bash
pmap -x <pid> | head
cat /proc/<pid>/maps | head
```

### 단순 모델

```text
more mappings and more pages
  -> more page table entries
  -> more memory footprint and translation work
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| small pages | 유연하다 | page table overhead가 커질 수 있다 | 일반 목적 |
| huge pages | translation 비용을 줄인다 | fragmentation과 compaction 부담 | 대형 워킹셋 |
| mapping 수 축소 | 관리 비용이 줄어든다 | 앱 구조 수정 필요 | 장기 최적화 |
| read 기반 전환 | 단순하다 | copy overhead가 늘 수 있다 | mmap 과다 앱 |

## 꼬리질문

> Q: page table도 메모리를 먹나요?
> 핵심: 그렇다. 많은 매핑과 페이지가 있으면 눈에 띄는 오버헤드가 된다.

> Q: RSS만 보면 왜 부족한가요?
> 핵심: page table과 VMA overhead는 별도로 봐야 하기 때문이다.

> Q: huge page는 page table overhead를 줄이나요?
> 핵심: 그렇다. 더 큰 페이지가 더 적은 엔트리로 같은 메모리를 표현한다.

## 한 줄 정리

page table overhead는 큰 주소 공간과 많은 매핑에서 은근히 커지며, RSS만 보는 운영은 실제 메모리 footprint를 놓치기 쉽다.
