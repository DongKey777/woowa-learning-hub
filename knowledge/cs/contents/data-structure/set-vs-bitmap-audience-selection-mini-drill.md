# Set vs Bitmap Audience Selection Mini Drill

> 한 줄 요약: audience selection 문제를 볼 때는 "단건 membership만 확인하나"면 `Set`, "`0..n` 정수 id 집합을 여러 조건으로 계속 겹치나"면 `bitmap/bitset`으로 먼저 자르면 beginner도 과한 최적화를 덜 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
- [List contains vs Set contains symptom card](../language/java/list-contains-vs-set-contains-symptom-card.md)

retrieval-anchor-keywords: set vs bitmap audience selection drill, audience segment set or bitmap, dense integer id drill, membership only vs set algebra, bitmap beginner practice, set beginner practice, 대상자 선택 뭐 써요, audience selection 처음, bitmap set 헷갈림, set or bitmap when to use, segment intersection basics, what is bitmap drill, beginner membership drill, sparse id set bitset roaring, set bitset roaring 뭐 써요

## 핵심 개념

이 드릴은 새 이론을 더하는 문서가 아니라, 기존 decision table을 손으로 한 번 적용해 보는 연습장이다.

먼저 기준 한 줄만 다시 붙인다.

> 단건 `contains`면 `Set`, dense integer id 집합을 `AND/OR`로 반복하면 `bitmap/bitset`

여기서 beginner가 자주 미끄러지는 지점은 "`대상자 선택`이라는 말이 나오면 무조건 bitmap 아닌가?"라는 오해다.
실제로는 질문이 둘로 갈린다.

- 사용자 하나가 이미 포함됐는지 확인만 하나
- 큰 대상자 집합 여러 개를 매번 겹쳐 새 대상을 계산하나

## 한눈에 보기

드릴에 들어가기 전에 decision table을 아주 짧게 다시 본다.

| 먼저 확인할 질문 | `Set` 쪽 신호 | `bitmap/bitset` 쪽 신호 |
|---|---|---|
| id 타입이 자유로운가 | 강함 | 약함 |
| `0..n` 정수 id로 바로 매핑되나 | 약함 | 강함 |
| 단건 membership이 대부분인가 | 강함 | 약함 |
| `교집합/합집합/차집합`을 계속 반복하나 | 약함 | 강함 |
| audience 전체를 재계산하나 | 약함 | 강함 |

짧게 외우면 이렇다.

- `명단 한 번 확인`이면 `Set`
- `세그먼트 여러 장 겹치기`면 `bitmap/bitset`

## 4문장 미니 드릴

아래 각 상황에서 첫 선택을 `Set` 또는 `bitmap/bitset`으로 골라 본다.

| 상황 | 먼저 고를 것 |
|---|---|
| 1. `userId 42`가 오늘 알림을 이미 받았는지만 확인한다. 하루에 `contains/add`가 대부분이고, id는 `Long`이다. | ? |
| 2. `0..999999` 회원 중 `서울`, `프리미엄`, `휴면 아님` 세 조건을 매 배치마다 교집합으로 계산한다. | ? |
| 3. 쿠폰 운영 도구에서 오늘 제외할 사용자 id가 `17, 29, 103`처럼 몇 개 안 된다. 운영자가 명단을 눈으로 확인하는 일이 더 많다. | ? |
| 4. 광고 대상자는 정수 회원 id로 관리되고, `active`, `consented`, `recentBuyer` 집합을 `AND/OR/ANDNOT`으로 여러 번 조합한다. | ? |

정답을 바로 보기 전에 아래 질문으로 한 번 더 자르면 더 잘 맞는다.

1. 지금 필요한 게 사용자 한 명 membership인가
2. 아니면 audience 전체 set algebra인가
3. id 범위가 dense integer id로 이미 정리돼 있나

## sparse range follow-up 미니 드릴

위 4문장이 쉬웠다면, 이제 beginner가 한 번 더 헷갈리는 다음 질문으로 넘어간다.

> "`id`는 정수인데 듬성듬성이다. 그러면 `Set`, plain `BitSet`, `Roaring Bitmap` 중 무엇을 먼저 골라야 하죠?"

여기서는 "정수 id인가?"보다 아래 세 축을 같이 봐야 한다.

- `contains/add/remove` 같은 membership 위주인가
- `maxId`까지 칸을 깔아도 될 만큼 범위가 작고 촘촘한가
- sparse range인데도 exact `AND/OR/ANDNOT`를 반복하나

아래 3문장을 보고 첫 선택을 골라 본다.

| 상황 | 먼저 고를 것 |
|---|---|
| 5. 제외 대상자 id가 `17`, `29`, `10300000`처럼 멀리 떨어져 있고, 배치에서 `contains/remove`만 조금 한다. | ? |
| 6. 좌석 id가 `0..4095`로 딱 정해져 있고, 빈 좌석 집합과 VIP 집합의 교집합을 여러 번 계산한다. | ? |
| 7. 회원 id는 `10`, `5000000`, `9000000`처럼 sparse range인데, `active`, `consented`, `recentBuyer` 집합을 exact `AND/OR/ANDNOT`로 계속 합친다. | ? |

짧은 안전 규칙은 이 한 줄이다.

> sparse range에서 membership 위주면 `Set`, 범위가 작고 촘촘하면 plain `BitSet`, sparse range에서도 exact set algebra를 반복하면 `Roaring Bitmap`

## 정답과 이유

| 상황 | 정답 | 왜 이렇게 고르나 |
|---|---|---|
| 1 | `Set` | 단건 membership이 핵심이고 `contains/add` 위주라서 구조를 더 복잡하게 만들 이유가 작다 |
| 2 | `bitmap/bitset` | dense integer id 범위 위에서 세그먼트 교집합을 반복하므로 비트 집합 사고가 문제를 직접 표현한다 |
| 3 | `Set` | 값 개수가 작고 운영 명단 확인이 쉬워야 하며, 전체 집합 연산보다 단순성이 더 중요하다 |
| 4 | `bitmap/bitset` | 정수 id 세그먼트를 여러 번 조합하는 audience selection이라 set algebra 비용이 중심이다 |

한 줄 이유만 다시 모으면 아래처럼 정리된다.

- `한 명이 포함됐나` -> `Set`
- `큰 집합 세 장을 겹치나` -> `bitmap/bitset`
- `작은 예외 명단 관리` -> `Set`
- `반복 세그먼트 계산` -> `bitmap/bitset`

follow-up 3문장의 정답은 아래처럼 자른다.

| 상황 | 정답 | 왜 이렇게 고르나 |
|---|---|---|
| 5 | `Set` | id가 sparse range이고 질문도 membership 위주라서 plain `BitSet`은 빈 칸 비용이 크고, compressed bitmap까지 갈 이유도 작다 |
| 6 | plain `BitSet` | `0..4095`처럼 범위가 작고 촘촘해서 칸을 깔아도 낭비가 작고, exact 집합 연산도 바로 표현된다 |
| 7 | `Roaring Bitmap` | sparse range라 plain `BitSet`은 wasteful한데, exact set algebra를 계속 하므로 `Set`보다 압축 bitmap handoff가 더 잘 맞는다 |

이 follow-up은 절대 규칙이 아니라 beginner용 첫 분류다.
라이브러리 구현, id 분포, 실제 메모리 예산에 따라 세부 선택은 달라질 수 있지만, 초반에는 이 세 문장만 분리해도 오개념이 많이 줄어든다.

## 흔한 오해와 함정

- `대상자 선택`이라는 단어만 보고 무조건 `bitmap`으로 뛰어가면 안 된다. 작은 예외 명단이나 단건 membership은 아직 `Set`이 더 자연스럽다.
- id가 정수라는 사실만으로 충분하지 않다. `정수 id + 반복 집합 연산`이 같이 보여야 `bitmap/bitset` 가치가 커진다.
- sparse range라고 해서 항상 `Roaring Bitmap`부터 고르는 것도 아니다. membership 위주면 `Set`이 더 단순하고, range가 작고 촘촘하면 plain `BitSet`이 더 직접적이다.
- `Set`을 고르면 느린 선택이라고 생각하기 쉽다. beginner 단계에서는 읽기 쉬운 기본값이 더 중요할 때가 많다.
- `bitmap`을 고르는 순간 곧바로 `Roaring Bitmap` 내부 구현까지 파고들 필요는 없다. 먼저 `BitSet` 수준의 mental model로도 충분하다.

## 더 깊이 가려면

- decision table 설명을 다시 보고 싶으면 [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- 자료구조 선택 큰 그림에서 `bitmap` 위치를 다시 보고 싶으면 [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- dense id인데 sparse range까지 붙기 시작하면 [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
- "`contains` 기본값이 왜 list가 아니라 set인가"가 먼저 헷갈리면 [List contains vs Set contains symptom card](../language/java/list-contains-vs-set-contains-symptom-card.md)

## 한 줄 정리

audience selection도 결국 질문 분류다. 사용자 한 명 membership이면 `Set`, dense integer id 세그먼트를 여러 번 겹쳐 새 audience를 계산하면 `bitmap/bitset`으로 먼저 자르면 된다.
