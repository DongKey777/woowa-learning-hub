# Sketch and Filter Selection Playbook

> 한 줄 요약: Bloom, Cuckoo, Xor, Quotient는 모두 "정답기"가 아니라 membership 선필터이고, 초보자는 `정답 필요 여부 -> 삭제 필요 여부 -> 메모리 우선 여부` 3축만 먼저 보면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
- [Bloom Filter](./bloom-filter.md)
- [Cuckoo Filter](./cuckoo-filter.md)
- [Xor Filter](./xor-filter.md)
- [Quotient Filter](./quotient-filter.md)
- [Reservoir Sampling](../algorithm/reservoir-sampling.md)

retrieval-anchor-keywords: sketch filter selection, bloom vs cuckoo vs xor vs quotient, membership filter basics, approximate membership intro, beginner filter decision, exact vs approximate membership, deletion needed filter, memory first filter, static set filter, filter choice for beginners, prefilter vs exact lookup

## 핵심 개념

이 문서는 sketch 전체를 다루기보다, 초보자가 membership filter를 고를 때 처음 묻는 세 질문만 정리한다.

- `정답이 바로 필요하다`면 이 문서의 네 구조가 아니라 `HashSet`, DB index 같은 exact 경로를 본다.
- `없으면 빨리 버리면 된다`면 Bloom, Cuckoo, Xor, Quotient 같은 선필터를 고른다.

즉 첫 질문은 "누가 더 고급 구조인가?"가 아니라 "이 경로가 정답 경로인가, 선필터 경로인가?"다.
초급 규칙으로는 아래 세 줄만 먼저 기억해도 된다.

| 질문 | yes | no |
|---|---|---|
| 정답이 바로 필요한가? | 필터 말고 exact set | 다음 질문으로 |
| 삭제가 필요한가? | Cuckoo Filter | 다음 질문으로 |
| 메모리를 특히 아껴야 하나? | Xor Filter | Bloom Filter부터 |

Quotient Filter는 이 세 줄로 충분하지 않을 때 보는 "보충 선택지"다.
즉 초반 기본값은 Bloom, 삭제가 있으면 Cuckoo, 정적 집합에서 메모리가 특히 중요하면 Xor로 먼저 자른다.

## 한눈에 보기

| 먼저 묻는 질문 | yes면 | no면 |
|---|---|---|
| 정답이 바로 필요한가? | exact set / DB lookup | 다음 질문으로 |
| 삭제가 필요한가? | Cuckoo Filter | 다음 질문으로 |
| 집합이 거의 안 바뀌고 메모리가 특히 중요한가? | Xor Filter | Bloom Filter부터 |

한 문장으로 줄이면 이렇다.

- 정답 필요: 필터 말고 exact
- 삭제 필요: Cuckoo 우선
- 메모리 최우선 + 정적 집합: Xor 우선
- 그 외 기본값: Bloom
- Bloom이 너무 단순하고 locality까지 보고 싶으면 Quotient 검토

## 첫 분기표

| 정답 필요 | 삭제 필요 | 메모리 우선 | 먼저 볼 선택지 | 이유 |
|---|---|---|---|---|
| yes | - | - | exact set | 확률 오답이 허용되지 않는다 |
| no | yes | no | Cuckoo Filter | 삭제와 재삽입이 자연스럽다 |
| no | no | yes | Xor Filter | 정적 집합에서 매우 compact하다 |
| no | no | no | Bloom Filter | 가장 단순한 기본값이다 |
| no | no | no(단, locality도 중요) | Quotient Filter | Bloom보다 좁은 구간 scan 감각을 기대할 수 있다 |

`메모리 우선`은 "같은 역할이면 몇 MB라도 더 줄이고 싶다"는 뜻이다.
`locality`는 lookup 때 여기저기 흩어진 비트를 찍기보다, 비교적 가까운 구간을 읽는 감각을 뜻한다.
초보자라면 Quotient를 첫 선택으로 두기보다 "Bloom으로 충분한가?"를 먼저 보는 편이 안전하다.

## 다른 sketch로 갈 때

이 문서의 네 구조는 전부 `membership` 질문용이다.
질문이 바뀌면 구조도 바로 바뀐다.

| 질문 | 가야 할 구조 |
|---|---|
| "이 key가 있나 없나?" | Bloom / Cuckoo / Xor / Quotient |
| "이 key가 몇 번 나왔나?" | [Count-Min Sketch](./count-min-sketch.md) |
| "서로 다른 개수는 몇 개인가?" | [HyperLogLog](./hyperloglog.md) |
| "p99는 얼마인가?" | [DDSketch](./ddsketch.md), [KLL Sketch](./kll-sketch.md) |

초보자가 자주 틀리는 지점은 Bloom과 HyperLogLog를 둘 다 "메모리 아끼는 구조"로만 보고 같은 줄에 세우는 것이다.
하지만 하나는 membership, 다른 하나는 cardinality다.

## 흔한 오해와 함정

- `mightContain=true`를 정답으로 받아들이면 안 된다. 네 구조 모두 exact path 앞의 선필터다.
- 삭제가 없는데도 무조건 Cuckoo로 시작할 필요는 없다. 단순성이 더 중요하면 Bloom이 더 낫다.
- 메모리가 중요하다고 항상 Xor를 고르면 안 된다. 집합이 자주 바뀌면 build 부담이 커진다.
- Quotient는 "Bloom의 상위호환"이 아니다. locality 장점 대신 구현 복잡도가 올라간다.
- "메모리 우선"과 "정답 필요"를 섞어 읽으면 안 된다. 메모리를 아끼고 싶어도 정답이 필요하면 필터가 아니라 exact 구조다.

가장 안전한 초급 규칙은 "삭제 없으면 Bloom부터, 삭제 있으면 Cuckoo부터, 정적 집합 메모리 최우선이면 Xor 검토"다.

## 실무에서 쓰는 모습

예를 들어 "로그인 차단 토큰이 blacklist에 있나"를 빠르게 앞단에서 거른다고 해보자.

| 상황 | 추천 출발점 |
|---|---|
| 차단 규칙이 자주 바뀌고 만료도 많다 | Cuckoo Filter |
| 배포 때만 목록이 바뀌고 조회가 대부분이다 | Xor Filter |
| 일단 가장 단순하게 선필터를 붙이고 싶다 | Bloom Filter |
| Bloom보다 locality까지 같이 보고 싶다 | Quotient Filter |

어느 경우든 `필터가 있다 = 차단 확정`은 아니다.
최종 판단은 blacklist DB, exact set, 원본 저장소가 맡아야 한다.

## 더 깊이 가려면

- 삭제와 rolling window 쪽은 [Cuckoo Filter](./cuckoo-filter.md)
- 가장 단순한 기본형은 [Bloom Filter](./bloom-filter.md)
- 정적 집합 압축은 [Xor Filter](./xor-filter.md)
- locality 중심 비교는 [Quotient Filter](./quotient-filter.md)
- membership 말고 스트림 샘플링으로 질문이 바뀌면 [Reservoir Sampling](../algorithm/reservoir-sampling.md)

## 한 줄 정리

membership 선필터 첫 선택은 `정답 필요 여부 -> 삭제 필요 여부 -> 메모리 우선 여부` 순서로 자르면 Bloom, Cuckoo, Xor, Quotient가 훨씬 덜 헷갈린다.
