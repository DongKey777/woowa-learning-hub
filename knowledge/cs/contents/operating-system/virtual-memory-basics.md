---
schema_version: 3
title: 가상 메모리 기초
concept_id: operating-system/virtual-memory-basics
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- virtual-vs-physical-address
- page-fault-not-always-error
aliases:
- 가상 메모리란
- 가상 메모리 뭐예요
- 가상 메모리 큰 그림
- virtual memory basics
- 가상 주소 물리 주소 차이
- 왜 가상 메모리를 써요
- page fault가 뭐예요
- 페이징 기초
- mmu 기초
- 처음 배우는데 가상 메모리
- 힙에 new 했는데 왜 바로 ram 안 써요
- xmx인데 왜 메모리를 다 안 먹어요
- oom이랑 page fault 차이
- 주소 공간 독립
symptoms:
- 가상 주소와 물리 주소가 왜 따로 있는지 직관이 안 와요
- page fault가 뜨면 무조건 메모리 오류라고 이해해서 계속 헷갈려요
- JVM 힙을 크게 줬는데 RSS가 바로 안 늘어나는 이유를 가상 메모리로 설명하고 싶어요
intents:
- definition
prerequisites:
- operating-system/memory-management-basics
next_docs:
- operating-system/demand-paging-page-fault-primer
- operating-system/page-table-overhead-memory-footprint
- operating-system/memory-management-numa-page-replacement-thrashing
linked_paths:
- contents/operating-system/memory-management-numa-page-replacement-thrashing.md
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/beginner-symptom-to-doc-map.md
- contents/operating-system/demand-paging-page-fault-primer.md
- contents/operating-system/page-table-overhead-memory-footprint.md
- contents/database/lock-basics.md
confusable_with:
- operating-system/memory-management-basics
- operating-system/demand-paging-page-fault-primer
- operating-system/page-table-overhead-memory-footprint
forbidden_neighbors: []
expected_queries:
- 프로세스마다 자기 주소를 가진다는 말을 초보자 기준으로 그림처럼 설명해줘
- 큰 힙을 잡아도 실제 메모리가 바로 차지 않는 이유를 운영체제 관점으로 알고 싶어
- MMU와 페이지 테이블이 정확히 어떤 역할을 하는지 첫 설명이 필요해
- 필요한 페이지가 아직 RAM에 없을 때 무슨 일이 일어나는지 쉽게 설명해줘
- 메모리 격리와 주소 변환이 왜 같은 가상 메모리 이야기인지 감으로 이해하고 싶어
contextual_chunk_prefix: |
  이 문서는 처음 배우는 학습자가 프로세스마다 따로 보이는 메모리 지도와 실제 RAM 연결, MMU와 페이지 테이블, 정상적인 page fault 흐름을 처음 잡는 primer다. 각자 자기 주소를 본다, 실제 위치는 따로 있다, 크게 잡아도 바로 차지하지 않는다, 처음 건드릴 때 메모리가 붙는다, page fault가 곧장 장애는 아니다 같은 자연어 paraphrase가 본 문서의 핵심 개념에 매핑된다.
---
# 가상 메모리 기초

> 한 줄 요약: 가상 메모리는 각 프로세스에게 물리 RAM과 독립된 주소 공간을 제공해 서로 간섭하지 않게 만드는 OS의 핵심 추상화다.

**난이도: 🟢 Beginner**

관련 문서:

- [메모리 관리, NUMA, 페이지 교체, 스래싱](./memory-management-numa-page-replacement-thrashing.md)
- [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
- [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)
- [Database Lock Basics](../database/lock-basics.md)

retrieval-anchor-keywords: 가상 메모리란, 가상 메모리 뭐예요, 가상 메모리 큰 그림, virtual memory basics, 가상 주소 물리 주소 차이, 왜 가상 메모리를 써요, page fault가 뭐예요, 페이징 기초, mmu 기초, 처음 배우는데 가상 메모리, 힙에 new 했는데 왜 바로 ram 안 써요, xmx인데 왜 메모리를 다 안 먹어요, oom이랑 page fault 차이, 주소 공간 독립

이 문서는 "`가상 메모리 뭐예요`", "`왜 `-Xmx`만큼 바로 메모리를 안 써요?`", "`page fault가 나면 무조건 에러인가요?`" 같은 첫 질문에서 먼저 읽는 입문 문서다.

## 먼저 잡는 멘탈 모델

가상 메모리가 없다면 두 프로세스가 같은 메모리 주소에 쓰면 서로 덮어씌울 수 있다. 운영체제는 **각 프로세스에게 가상 주소 공간**을 부여해서 이 문제를 해결한다.

프로세스가 `0x1000` 주소를 읽을 때, CPU 안의 MMU(Memory Management Unit)가 이 가상 주소를 실제 RAM의 물리 주소로 변환한다. 두 프로세스가 같은 가상 주소 `0x1000`을 써도 각각 다른 물리 주소로 매핑되어 충돌이 없다.

입문용으로는 "각 프로세스가 자기 전용 메모리 지도를 한 장씩 받는다"라고 생각하면 쉽다. 다만 이 비유는 **지도 자체가 곧 RAM은 아니라는 점**까지만 유효하다. 실제 RAM 배치와 디스크에서 가져오는 시점은 커널과 MMU가 따로 관리한다.

## 한눈에 보기

```
프로세스 A              프로세스 B
가상: 0x1000  →  물리: 0xA000
가상: 0x2000  →  물리: 0xB000

가상: 0x1000  →  물리: 0xC000   (다른 물리 주소)
가상: 0x2000  →  물리: 0xD000
```

변환 정보는 **페이지 테이블(page table)**에 저장되고, OS가 프로세스별로 관리한다.

## 30초 비교표: 처음 헷갈리는 용어 4개

| 용어 | 초보자용 한 줄 | 자주 헷갈리는 상대 |
|------|----------------|-------------------|
| 가상 주소 | 프로세스가 보는 주소 | 물리 주소 |
| 물리 주소 | 실제 RAM 위치 | 가상 주소 |
| 페이지 | 가상 메모리를 자른 고정 크기 조각 | 바이트 하나하나 |
| page fault | 필요한 페이지가 아직 RAM에 없어서 커널 도움이 필요한 사건 | OOM, 에러 |

처음에는 "`가상 주소`는 앱이 보는 번호, `물리 주소`는 RAM의 실제 위치"까지만 잡아도 충분하다. `page fault`는 곧장 실패가 아니라, 필요한 페이지를 아직 올리지 않았다는 **처리 이벤트**일 수 있다는 점이 특히 중요하다.

## 1분 예시: `-Xmx4g`인데 왜 처음부터 4GB를 다 안 먹을까

Java 애플리케이션을 `-Xmx4g`로 띄워도 시작 직후 RSS가 4GB로 바로 찍히지 않는 경우가 많다.

1. JVM은 큰 힙 **가상 주소 공간**을 먼저 예약한다.
2. 하지만 실제 객체가 아직 없으면 모든 페이지가 곧바로 **물리 RAM**에 올라오지는 않는다.
3. 코드가 힙의 어떤 주소를 처음 만질 때 page fault가 발생하고, 그때 필요한 페이지만 물리 프레임이 연결된다.

즉 `-Xmx4g`는 "최대 여기까지 쓸 수 있다"는 상한에 가깝고, "부팅과 동시에 RAM 4GB를 확정 점유한다"는 뜻은 아니다.

## 상세 분해

- **페이지(Page)**: 가상 주소 공간을 고정 크기(보통 4 KB)로 나눈 단위. 물리 메모리도 같은 크기의 프레임(frame)으로 나뉜다.
- **페이지 테이블**: 가상 페이지 번호 → 물리 프레임 번호 매핑 테이블. 프로세스마다 독립적으로 존재한다.
- **MMU**: CPU에 내장된 하드웨어. 명령 실행 시 마다 가상 주소를 물리 주소로 자동 변환한다.
- **페이지 폴트(Page Fault)**: 프로세스가 접근하려는 가상 페이지가 아직 RAM에 올라오지 않았을 때 발생하는 예외. OS가 해당 페이지를 디스크에서 RAM으로 불러온 뒤 재실행한다.
- **스왑(Swap)**: RAM이 부족할 때 OS가 사용 빈도가 낮은 페이지를 디스크로 내보내는 것. 접근 시 page fault → swap-in 발생.

## 흔한 오해와 함정

- "가상 메모리 = 스왑 메모리"라는 오해가 많다. 스왑은 가상 메모리 구현의 한 기법일 뿐이다. 스왑을 끈 시스템에서도 가상 메모리는 동작한다.
- "힙에 `new` 했는데 바로 RAM에 올라간다"는 틀렸다. 실제로는 가상 주소만 예약되고, 처음 접근할 때 page fault가 발생해야 물리 프레임이 배정된다(lazy allocation).
- "두 프로세스가 같은 라이브러리 코드를 쓰면 메모리가 두 배 든다"는 오해다. 읽기 전용 코드 페이지는 물리 프레임을 공유(shared library)할 수 있다.
- "page fault가 떴다 = 시스템이 망가졌다"도 과한 해석이다. first-touch, lazy allocation, 파일 매핑처럼 **정상 흐름의 page fault**도 많다. 다만 major fault가 자주 늘면 실제 지연 원인이 될 수 있어 [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)로 이어서 보면 좋다.
- "OOM이 나면 page fault랑 같은 문제다"도 다르다. page fault는 필요한 페이지를 가져오는 과정이고, OOM은 가져오거나 유지할 메모리 여유가 더는 없을 때의 실패 상태다.

## 실무에서 쓰는 모습

Java 프로세스를 `-Xmx4g`로 띄웠을 때, 실제 RAM 사용량이 처음에 낮다가 점점 오르는 이유가 lazy allocation 때문이다. JVM이 힙 가상 주소를 미리 예약하지만, 실제 객체 생성 시 page fault가 발생해 물리 프레임이 하나씩 채워진다.

OOM(Out Of Memory) 상황도 이 구조에서 비롯된다. 물리 RAM + 스왑이 모두 소진되면 OS는 OOM killer로 프로세스를 강제 종료한다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "메모리 관련 질문이 너무 넓어서 어디부터 읽을지 다시 고르고 싶으면": [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md)
> - "page fault 흐름을 first-touch 기준으로 더 보려면": [Demand Paging and Page Fault Primer](./demand-paging-page-fault-primer.md)
> - "major fault가 실제 지연으로 커지는 경로"를 보려면: [Swap-In, Reclaim, and Major Fault Path Primer](./swap-in-reclaim-fault-path-primer.md)
> - "NUMA/페이지 교체/스래싱까지 한 단계 확장"하려면: [메모리 관리, NUMA, 페이지 교체, 스래싱](./memory-management-numa-page-replacement-thrashing.md)

## 더 깊이 가려면

- [메모리 관리, NUMA, 페이지 교체, 스래싱](./memory-management-numa-page-replacement-thrashing.md) — 페이지 교체 알고리즘과 스래싱
- [페이지 테이블 오버헤드와 메모리 풋프린트](./page-table-overhead-memory-footprint.md) — 페이지 테이블 자체의 비용
- [Beginner Symptom-to-Doc Map](./beginner-symptom-to-doc-map.md) — 메모리 말고 다른 축으로 다시 분기할 때

## 면접/시니어 질문 미리보기

1. "가상 메모리를 왜 쓰나요?"
   - 핵심 답: 프로세스 격리(서로 간섭 방지), RAM보다 큰 주소 공간 제공, 공유 라이브러리 가능.
2. "Page fault가 무엇이고, 언제 발생하나요?"
   - 핵심 답: 접근한 가상 페이지가 RAM에 없을 때 발생하는 예외. OS가 페이지를 디스크나 파일에서 올려 해결한다.
3. "스왑을 무한정 늘리면 메모리 문제가 해결되나요?"
   - 핵심 답: 아니다. 스왑 I/O는 RAM 접근보다 수백~수천 배 느리다. 스왑이 자주 발생하면 성능이 급격히 떨어진다(스래싱).

## 한 줄 정리

가상 메모리는 각 프로세스에게 독립된 주소 공간이라는 환상을 제공해 격리와 안전을 확보하고, 페이지 테이블과 MMU가 그 환상을 실제 물리 주소로 투명하게 바꿔준다.
