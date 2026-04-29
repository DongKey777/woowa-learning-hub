# Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머

> 한 줄 요약: 주니어가 자료구조를 고를 때는 이름보다 "반복해서 무슨 질문을 하느냐"를 먼저 잡아야 한다. `lookup`이면 `map`, `중복/존재 확인`이면 `set`, `도착 순서`면 `queue`, `가장 급한 것`이면 `priority queue`, `접두사 검색`이면 `trie`, `많은 id의 예/아니오 집합 연산`이면 `bitmap`이 첫 출발점이다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 README](./README.md)
- [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md)
- [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
- [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)
- [Search 시스템 설계](../system-design/search-system-design.md)

retrieval-anchor-keywords: map vs set vs queue vs priority queue vs trie vs bitmap, 자료구조 처음 배우는데 뭐부터, 자료구조 큰 그림, 자료구조 헷갈림, 처음 배우는데 map set queue 차이, map set queue 뭐예요, map set queue 언제 쓰는지, trie bitmap 뭐예요, priority queue가 뭐예요, queue가 왜 bfs에도 나와요, queue가 service 코드에도 왜 나와요, set이랑 map이 왜 달라요, bitmap은 언제 써요, what is bitmap, 첫 자료구조 선택 기준

## 이 문서가 먼저 잡아야 하는 첫 질문

이 문서는 아래처럼 **첫 질문 형태의 query**가 들어왔을 때 deep dive보다 먼저 잡히도록 만든 primer다.

- `자료구조 처음인데 뭐부터 봐요?`
- `map set queue 차이가 뭐예요?`
- `queue가 왜 bfs에도 나오고 service 코드에도 나와요?`
- `trie랑 bitmap은 언제 쓰는지 큰 그림만 먼저 알고 싶어요`

한 줄로 줄이면 `구현 디테일`보다 `질문 모양 번역`을 먼저 끝내는 문서다.

## 핵심 개념

이 여섯 구조는 "무엇을 저장하나"보다 "무슨 질문을 반복하나"로 자르는 편이 훨씬 쉽다.

- `map`: `이 key의 값이 뭐지?`
- `set`: `이 값이 이미 있나?`
- `queue`: `먼저 들어온 것을 먼저 꺼내야 하나?`
- `priority queue`: `가장 급한 것 하나를 먼저 꺼내야 하나?`
- `trie`: `"spr"`처럼 이 prefix로 시작하는 후보가 있나?`
- `bitmap`: `수많은 id 중 어떤 id들이 조건을 만족하나?`를 비트 집합으로 빠르게 합치고 싶나?

초급자가 가장 많이 헷갈리는 이유는 `찾기`라는 말이 너무 넓기 때문이다.
하지만 실제로는 아래처럼 질문 모양이 꽤 다르다.

| 반복 질문 | 첫 구조 | 핵심 이유 |
|---|---|---|
| `orderId -> 주문 상태` | `map` | key에 연결된 value가 필요하다 |
| `이 요청 이미 처리했나` | `set` | 존재 여부만 알면 된다 |
| `먼저 받은 작업부터 처리` | `queue` | 도착 순서가 규칙이다 |
| `다음 재시도 시각이 가장 이른 작업` | `priority queue` | 우선순위 키가 순서를 바꾼다 |
| `"app"`로 시작하는 검색어 후보` | `trie` | prefix 자체를 구조에 녹여 둔다 |
| `active 사용자 집합 ∩ premium 사용자 집합` | `bitmap` | 큰 집합의 교집합/합집합을 비트 연산으로 처리하기 쉽다 |

## 한눈에 보기

주니어가 처음 고를 때는 아래 표 하나로 출발해도 충분하다.

| 지금 문제에서 가장 먼저 필요한 답 | 먼저 떠올릴 구조 | 실무 예시 | 흔한 오진 |
|---|---|---|---|
| `id로 값을 바로 찾기` | `map` | `userId -> User` 캐시 | `list`를 끝까지 순회 |
| `중복만 막기` | `set` | 처리한 request id 기록 | `map<id, true>`를 습관처럼 사용 |
| `먼저 들어온 순서대로 넘기기` | `queue` | worker handoff, BFS | `priority queue`도 queue니까 비슷하다고 생각 |
| `가장 빠른 deadline/top-k` | `priority queue` | retry scheduler, 상위 점수 유지 | 매번 전체 정렬 |
| `접두사 자동완성` | `trie` | `"spr"` -> `spring`, `spring boot` | `map` 전체를 `startsWith`로 스캔 |
| `많은 정수 id의 집합 연산` | `bitmap` | 세그먼트 대상 계산, row 후보 필터 | `set`과 완전히 같은 층위라고 생각 |

`bitmap`만 낯설게 느껴질 수 있는데, 주니어 관점에서는 이렇게만 먼저 잡으면 된다.

- `set`은 "원소를 하나씩 담는 명단"
- `bitmap`은 "정수 id마다 비트 한 칸으로 표시한 명단"

즉 둘 다 "집합"이지만, `bitmap`은 **id 범위가 정수로 정해져 있고 집합 연산을 아주 많이 할 때** 더 유리한 쪽이다.

## 같은 서비스 장면에서 고르는 법

주문/검색 서비스를 예로 들면 같은 도메인 안에서도 질문에 따라 구조가 달라진다.

| 같은 서비스 장면 | 먼저 필요한 질문 | 첫 구조 |
|---|---|---|
| `orderId 42의 상태를 바로 보여 주기` | key로 값 조회 | `map` |
| `같은 결제 요청을 두 번 처리했는지 확인` | membership only | `set` |
| `메일 발송 작업을 받은 순서대로 소비` | arrival order | `queue` |
| `재시도 시각이 가장 이른 작업부터 실행` | earliest-first | `priority queue` |
| `spr`를 입력한 사용자에게 자동완성 후보 보여 주기 | prefix lookup | `trie` |
| `서울 거주 사용자`와 `이벤트 대상 사용자` 교집합 계산 | large set intersection | `bitmap` |

한 문장으로 다시 줄이면 이렇다.

- 값을 붙여 관리하면 `map`
- 있다/없다만 보면 `set`
- 줄 선 순서면 `queue`
- 새치기 허용 우선순위면 `priority queue`
- 문자열 앞부분으로 찾으면 `trie`
- 정수 id 집합을 대량으로 AND/OR 하면 `bitmap`

## 자주 헷갈리는 포인트

- `map` vs `set`
  - value가 필요하면 `map`
  - 존재 여부만 필요하면 `set`
- `queue` vs `priority queue`
  - 먼저 온 사람이 먼저면 `queue`
  - 더 급한 사람이 새치기하면 `priority queue`
- `map` vs `trie`
  - exact key lookup이면 `map`
  - `"이 prefix로 시작하는 것"`이면 `trie`
- `set` vs `bitmap`
  - key가 문자열/객체처럼 자유롭고 집합 크기도 유동적이면 보통 `set`
  - key가 `0..n` 범위의 정수 id이고 교집합/합집합을 자주 하면 `bitmap`
- `queue` vs `BFS용 queue`
  - 둘 다 queue를 쓰지만, `최소 이동 횟수`가 핵심이면 자료구조보다 알고리즘 질문이 먼저다
  - 이 경우는 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)으로 이어서 보는 편이 빠르다
- `bitmap`이 항상 최고 성능은 아니다
  - row 수가 작거나 id가 문자열 중심이면 구현 복잡도만 늘 수 있다
  - `bitmap`은 "정수 id 집합을 정말 많이 합치나?"를 먼저 확인할 때 의미가 있다

## beginner-safe 다음 한 칸

처음 읽은 뒤에는 제일 헷갈린 경계 하나만 따라가면 된다.

| 지금 가장 막히는 말 | 다음 한 칸 | 왜 여기로 가나 |
|---|---|---|
| `set이랑 map이 아직 헷갈려요` | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) | `있나?`와 `무슨 값이지?`를 다시 분리한다 |
| `queue가 왜 BFS랑 service 둘 다에 나와요?` | [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | FIFO 도구와 탐색 규칙을 다른 질문으로 자른다 |
| `trie가 map이랑 뭐가 달라요?` | [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md) | exact lookup과 prefix lookup을 분리한다 |
| `bitmap이 set보다 왜 유리할 수 있죠?` | [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md) | 정수 id 집합 연산이라는 전제를 붙인다 |

주니어가 특히 기억하면 좋은 분기 하나만 더 적으면:

> "원소 하나를 바로 찾는가?"와 "집합 전체를 자주 겹쳐 보는가?"는 다른 질문이다.

- 전자면 `map/set`
- 후자면 `bitmap` 가능성을 본다

## 다음 읽기

지금 막힌 문장에 따라 다음 문서를 하나만 이어서 읽으면 된다.

| 지금 더 궁금한 것 | 다음 문서 |
|---|---|
| `map`과 `set`을 더 또렷하게 나누고 싶다 | [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md) |
| `set`으로 충분한지, dense integer id라서 bitmap을 볼지 헷갈린다 | [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md) |
| `queue`와 `priority queue`를 실수 없이 고르고 싶다 | [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md) |
| `trie`가 자동완성에서 왜 자연스러운지 보고 싶다 | [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md) |
| `bitmap`을 실무에서 언제 꺼내는지 감을 잡고 싶다 | [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md) |
| `queue`가 자료구조 질문인지 BFS 도구인지 헷갈린다 | [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| 검색 자동완성 전체 흐름이 궁금하다 | [Search 시스템 설계](../system-design/search-system-design.md) |

## 한 줄 정리

주니어의 첫 선택은 "반복 질문 번역"으로 끝난다. `lookup`은 `map`, `dedupe`는 `set`, `FIFO`는 `queue`, `earliest/top-k`는 `priority queue`, `prefix`는 `trie`, `대량 정수 id 집합 연산`은 `bitmap`으로 먼저 자르면 대부분의 초급 혼동이 빠르게 정리된다.
