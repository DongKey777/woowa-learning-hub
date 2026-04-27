# TLB and Page Table Walk Bridge

> 한 줄 요약: TLB miss는 주소 변환 캐시를 못 찾았다는 뜻이고, page fault는 page table walk가 끝난 뒤에도 지금 쓸 수 있는 번역을 얻지 못했다는 뜻이다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)


retrieval-anchor-keywords: tlb page table walk bridge basics, tlb page table walk bridge beginner, tlb page table walk bridge intro, operating system basics, beginner operating system, 처음 배우는데 tlb page table walk bridge, tlb page table walk bridge 입문, tlb page table walk bridge 기초, what is tlb page table walk bridge, how to tlb page table walk bridge
> 관련 문서:
> - [Process, Thread, Virtual Memory, Context Switch, Scheduler Basics](./process-thread-virtual-memory-context-switch-scheduler-basics.md)
> - [가상 메모리 기초](./virtual-memory-basics.md)
> - [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)
> - [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)
> - [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)
> - [가상 메모리](./README.md#가상-메모리)

> retrieval-anchor-keywords: tlb bridge, page table walk bridge, tlb miss vs page fault, virtual address translation, address translation hardware, tlb hit miss basics, page table walk basics, virtual page number, physical frame number, translation cache, present bit, permission fault, copy-on-write fault, minor vs major page fault, tlb refill, virtual memory follow-up, beginner handoff box, memory handoff, 주소 변환 후속 학습, 가상 메모리 다음 문서

## 핵심 개념

가상 메모리를 처음 배울 때는 보통 "프로세스는 가상 주소를 본다"까지 이해하고 넘어간다. 그런데 실제 CPU 입장에서는 다음 질문이 바로 붙는다.

- 이 가상 주소를 물리 주소로 **언제** 바꾸는가
- page table은 매 접근마다 보는가
- TLB miss와 page fault는 같은 일인가
- major/minor fault는 주소 변환의 어느 단계에서 갈리는가

이 문서는 현대 서버 CPU 대부분(x86_64, arm64처럼 **hardware page-table walk**를 쓰는 경우)을 기준으로, 가상 주소가 실제 번역으로 바뀌는 경로를 `TLB -> page table walk -> page fault handler` 순서로 이어 주는 `bridge`다.

## 한눈에 보기

| 단계 | 누가 처리하나 | 질문 | 결과 |
|------|---------------|------|------|
| TLB lookup | CPU MMU | "이 가상 페이지 번역을 이미 알고 있나?" | hit면 바로 접근, miss면 walk로 진행 |
| page table walk | CPU MMU | "page table이 지금 쓸 수 있는 번역을 주나?" | present + 권한 OK면 TLB 채우고 재시도 |
| page fault handler | 커널 | "지금 번역을 만들어 줄 수 있나?" | minor/major/COW로 해결하거나 예외로 종료 |

핵심은 이렇다.

- `TLB miss`는 **번역 캐시 miss**다
- `page fault`는 **walk 결과만으로는 접근을 계속할 수 없다**는 뜻이다
- 그래서 **많은 TLB miss는 page fault 없이 끝난다**
- 반대로 page fault를 처리한 뒤에는 보통 새 번역이 TLB에 다시 채워진다

## 1. 가장 빠른 경로: TLB hit

CPU가 load/store/instruction fetch를 하려면 먼저 가상 주소를 물리 주소로 바꿔야 한다.

- 가상 주소는 보통 `virtual page number + page offset`으로 생각할 수 있다
- TLB는 최근에 쓴 `virtual page number -> physical frame number` 번역과 권한 정보를 캐시한다
- TLB hit면 page table 전체를 다시 읽지 않고 바로 물리 주소를 만든다

```text
CPU가 가상 주소 접근
  -> TLB hit
  -> physical frame number + offset 결합
  -> 메모리 접근 계속
```

이 경로에서는 운영체제가 개입하지 않는다. page fault도 없다.

## 2. TLB miss는 "번역 캐시 miss"일 뿐이다

TLB miss가 나면 많은 학습자가 "그 페이지가 메모리에 없는가 보다"라고 생각한다. 그건 절반만 맞다.

TLB miss가 의미하는 것은 단 하나다.

- **지금 CPU가 바로 쓸 수 있는 번역 캐시 엔트리가 없다**

그 다음에는 CPU MMU가 page table walk를 한다.

- 상위 레벨 page table부터 내려가며 엔트리를 찾는다
- 중간 엔트리와 최종 PTE가 cache에 있으면 꽤 빨리 끝날 수 있다
- 최종 엔트리가 `present`이고 권한도 맞으면 번역을 얻는다
- 얻은 번역을 TLB에 채우고 같은 메모리 접근을 다시 진행한다

```text
CPU가 가상 주소 접근
  -> TLB miss
  -> hardware page table walk
  -> usable translation 발견
  -> TLB refill
  -> 같은 접근 계속
```

이 경우는 **느릴 수는 있어도 page fault는 아니다**.
운영체제 입장에서는 조용히 지나간다.

## 3. page fault는 walk가 "지금은 못 한다"고 말할 때 생긴다

page fault는 TLB miss 자체가 아니라, page table walk가 끝난 뒤에도 CPU가 접근을 계속할 수 없을 때 발생한다.

대표적인 경우:

- 최종 PTE가 not-present라서 아직 물리 페이지가 준비되지 않았다
- write하려는데 읽기 전용/COW 상태라 커널이 private page를 만들어야 한다
- 권한이 맞지 않아 접근이 허용되지 않는다
- file-backed page를 가져오려면 page cache 연결이나 디스크 I/O가 필요하다

흐름으로 보면 이렇게 구분된다.

```text
CPU가 가상 주소 접근
  -> TLB miss
  -> hardware page table walk
     -> usable translation 있음
        -> TLB refill, fault 없음
     -> usable translation 없음
        -> page fault trap
        -> 커널이 zero-fill / page cache 연결 / COW / disk I/O / 보호 예외 판단
```

즉 page fault는 **"번역 캐시가 없다"**가 아니라 **"page table 상태만으로는 지금 접근을 끝낼 수 없다"**에 가깝다.

## 4. minor/major는 page fault 이후 커널 경로에서 갈린다

major/minor 구분은 TLB lookup 단계가 아니라 **page fault handler 안**에서 결정된다.

| 상황 | TLB miss 가능성 | page fault 여부 | 보통 분류 |
|------|------------------|-----------------|-----------|
| 이미 매핑된 hot page 재접근 | 낮음 | 없음 | 해당 없음 |
| 매핑은 되어 있지만 TLB 엔트리만 사라짐 | 높음 | 없음 | 해당 없음 |
| `malloc()` 후 첫 touch | 높음 | 있음 | minor |
| `mmap()` 파일 첫 접근 + page cache hit | 높음 | 있음 | minor |
| `mmap()` 파일 첫 접근 + page cache miss | 높음 | 있음 | major |
| `fork()` 뒤 첫 write(COW) | 높음 | 있음 | minor인 경우가 많음 |

이 표에서 중요한 포인트는 두 가지다.

- **TLB miss는 성능 이벤트**일 수 있지만 커널 trap이 아닐 수 있다
- **major/minor는 trap 이후 서비스 경로**를 설명한다

그래서 "TLB miss가 많다"와 "major fault가 많다"는 서로 다른 문제를 가리킨다.

## 5. 자주 헷갈리는 예시 네 가지

### 1. 같은 페이지를 계속 읽을 때

- 첫 몇 번 접근: TLB miss가 날 수 있다
- 이후: TLB hit가 많아진다
- page table에 정상 매핑이 있으면 page fault는 없다

즉 TLB locality가 좋아지면 성능이 좋아져도, page fault 통계는 원래부터 거의 0일 수 있다.

### 2. anonymous memory를 처음 touch할 때

`malloc()`이나 stack 확장 직후 첫 접근은 보통 lazy allocation 상태다.

- TLB miss
- walk 결과, 아직 usable translation이 없음
- page fault trap
- 커널이 zero-filled page를 준비
- page table 갱신 후 재시도

이 경로는 보통 **minor fault**다.

### 3. `mmap()`한 파일을 처음 읽을 때

파일이 이미 page cache에 있으면:

- TLB miss
- fault trap
- 커널이 기존 page cache 페이지를 연결
- 보통 minor fault

파일이 page cache에 없으면:

- 같은 시작점에서
- 실제 디스크 I/O가 붙어
- major fault가 된다

즉 file-backed 첫 접근은 "TLB miss 다음에 항상 major fault"가 아니라, **그 뒤 커널이 어떤 준비 상태를 보느냐**로 갈린다.

### 4. `fork()` 뒤 첫 write를 할 때

물리 페이지가 이미 메모리에 있어도 page fault가 날 수 있다.

- 부모/자식은 처음에 같은 물리 페이지를 읽기 전용으로 공유할 수 있다
- write 시점에 walk는 "지금 권한으로는 못 쓴다"는 상태를 본다
- page fault trap
- 커널이 private page를 복제하고 writable mapping으로 바꾼다

즉 COW fault는 "페이지가 RAM에 없어서"가 아니라 **현재 번역과 권한으로는 write를 완료할 수 없어서** 발생한다.

## 6. 성능 관점에서 무엇을 따로 봐야 하나

### TLB miss를 볼 때

- 주소 변환 locality가 깨졌는지
- 작은 page가 너무 많아 TLB pressure가 큰지
- huge page가 도움이 될 workload인지

이 축은 [THP, Huge Pages, TLB Latency](./thp-huge-pages-tlb-latency.md)와 이어진다.

### page fault를 볼 때

- lazy allocation, `mmap()`, COW 중 어떤 fault인지
- page cache hit/miss 때문에 minor/major가 어떻게 갈리는지
- 디스크 I/O나 reclaim이 tail latency를 흔드는지

이 축은 [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)와 [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)로 이어진다.

### page table walk 자체를 볼 때

- page table depth와 cache miss가 CPU cost를 키우는지
- mapping 수와 small page 비중이 translation overhead를 키우는지

이 축은 [Page Table Overhead, Memory Footprint](./page-table-overhead-memory-footprint.md)로 이어진다.

## 자주 나오는 오해

### "TLB miss면 page fault다"

아니다. TLB miss 뒤 page table walk가 성공하면 커널은 전혀 모른다.

### "page가 RAM에 있으면 page fault가 절대 없다"

아니다. COW나 권한 fault처럼 페이지는 있어도 현재 번역으로는 접근을 끝낼 수 없는 경우가 있다.

### "major/minor는 하드웨어가 결정한다"

아니다. 하드웨어는 fault를 올리고, major/minor는 커널이 그 fault를 어떻게 해결했는지에 대한 분류다.

### "TLB만 크면 page fault 문제도 같이 해결된다"

아니다. TLB는 번역 캐시 문제를 줄여 주지만, lazy allocation, file I/O, reclaim, swap-in 같은 fault 원인을 없애 주지는 않는다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "가상 메모리 다음에 주소 변환이 실제로 어디서 갈리는지"를 한 번 더 고정하려면: [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)
> - "TLB miss와 page fault를 runtime counter로 어떻게 구분하는지"가 궁금하면: [Major, Minor Page Faults, Runtime Diagnostics](./major-minor-page-faults-runtime-diagnostics.md)
> - "주소 변환보다 reclaim 때문에 major fault가 커지는 장면"까지 이어 보려면: [Swap-In, Reclaim, and Major Fault Path Primer](./swap-in-reclaim-fault-path-primer.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 꼬리질문

> Q: TLB miss가 났는데 왜 `perf`에는 page fault가 안 보이나요?
> 핵심: page table walk만으로 번역을 찾았고, 커널 trap까지 가지 않았기 때문이다.

> Q: page fault는 항상 TLB miss 뒤에 오나요?
> 핵심: 현대 hardware walker 기준으로는 보통 그렇지만, fault의 본질은 miss가 아니라 walk 결과가 unusable translation이라는 점이다.

> Q: `fork()` 뒤 첫 write는 왜 page가 메모리에 있어도 fault인가요?
> 핵심: 물리 페이지 존재 여부가 아니라 현재 PTE 권한과 COW 규칙 때문에 커널 개입이 필요하기 때문이다.

> Q: huge page는 어디에 영향을 주나요?
> 핵심: 주로 TLB pressure와 walk 비용을 줄이는 쪽에 가깝고, fault 종류 자체를 바꾸는 도구는 아니다.

## 한 줄 정리

가상 주소 변환은 보통 `TLB lookup -> page table walk -> 필요하면 page fault handler` 순서로 이어지며, TLB miss는 번역 캐시 사건이고 page fault는 그 이후에도 접근을 계속할 수 없을 때만 커널로 올라온다.
