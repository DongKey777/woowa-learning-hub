# Plain BitSet vs Compressed Bitmap Decision Card

> 한 줄 요약: `plain BitSet`은 `0..maxId`를 그대로 펼쳐 두는 쪽이 자연스러운 dense 정수 id 집합에 잘 맞고, compressed bitmap은 `maxId`는 큰데 실제 값이 듬성듬성하거나 구간별 밀도가 섞인 집합을 exact set algebra로 계속 다뤄야 할 때 보는 intermediate 다음 카드다.

**난이도: 🟡 Intermediate**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [Roaring Bitmap](./roaring-bitmap.md)
- [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
- [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)

retrieval-anchor-keywords: plain bitset vs compressed bitmap, dense vs sparse bitmap decision, compressed bitmap decision card, roaring vs bitset intermediate, sparse range exact set algebra, dense integer id bitmap follow-up, bitset 언제 충분한가, compressed bitmap 언제 쓰나, bitmap dense sparse 헷갈림, why plain bitset wasteful, what is compressed bitmap, bitmap bridge basics

## 핵심 개념

이 카드는 "`Set` 대신 `BitSet`까지는 이해했는데, 그다음 왜 compressed bitmap이 나오죠?"라는 follow-up을 자르기 위한 중간 다리다.

핵심은 이름이 아니라 저장 방식이다.

- `plain BitSet`: `0..maxId` 자리를 길게 펴 둔 뒤 비트를 켠다
- compressed bitmap: 비어 있는 구간이나 구간별 밀도 차이를 더 compact하게 들고 가면서 exact bitmap set algebra를 유지하려고 한다

비유로 말하면 `plain BitSet`은 좌석표 전체를 한 장으로 펼쳐 두는 방식이고, compressed bitmap은 빈 블록을 접거나 구간별 표현을 바꾸는 방식에 가깝다.
다만 이 비유는 저장 모양만 설명한다.
실제 구현은 라이브러리마다 다르고, 어떤 압축 bitmap이 더 유리한지는 데이터 분포와 연산 패턴에 따라 달라진다.

## 한눈에 보기

| 지금 보이는 신호 | plain `BitSet` 쪽 | compressed bitmap 쪽 |
|---|---|---|
| `maxId`가 작거나 범위가 촘촘하다 | 강함 | 약함 |
| 실제 값은 적은데 `maxId`만 매우 크다 | 약함 | 강함 |
| 구간마다 어떤 곳은 빽빽하고 어떤 곳은 비어 있다 | 약함 | 강함 |
| exact `AND/OR/ANDNOT`를 반복한다 | 보통 이상 | 강함 |
| 목표가 알고리즘 문제 풀이, dense bit tricks, 간단한 세그먼트 계산이다 | 강함 | 약함 |
| 목표가 sparse range 세그먼트/필터 집합을 계속 합치는 것이다 | 약함 | 강함 |
| 구현 단순성과 디버깅 직관성이 가장 중요하다 | 강함 | 약함 |

짧게 외우면 이 한 줄이다.

> `빈 칸이 별로 없으면 plain BitSet`, `빈 칸이 많지만 exact 집합 연산은 계속 하고 싶으면 compressed bitmap`

## 상세 분해

### 1. dense 쪽이면 왜 plain BitSet이 먼저인가

`plain BitSet`은 사고가 직선적이다.
정수 id 하나가 비트 한 칸에 바로 대응되고, dense 범위에서는 빈 칸 낭비도 크지 않다.

예를 들어 `0..200000` 사용자 중 active, premium, coupon 대상자 집합을 몇 번 교집합하는 정도라면,
학습자 관점에서는 plain bitmap mental model만으로도 대부분 설명이 끝난다.

### 2. sparse 쪽이면 왜 plain BitSet이 아쉬워지나

문제는 `maxId`가 실제 원소 수보다 지나치게 클 때다.
예를 들어 id가 `10`, `5_000_000`, `9_000_000`처럼 퍼져 있으면, plain `BitSet`은 많은 빈 칸을 같이 끌고 다니는 발상이 된다.

이때 중요한 건 "sparse니까 무조건 `Set`"이 아니라, 아래 둘을 같이 보는 것이다.

1. membership 몇 번이면 끝나는가
2. exact set algebra를 반복하는가

첫 번째만 중요하면 `Set`이 더 단순할 수 있다.
두 번째가 중요하면 compressed bitmap이 `Set`과 plain `BitSet` 사이의 다리가 된다.

### 3. compressed bitmap은 무엇을 보완하나

compressed bitmap 계열은 보통 아래 방향을 노린다.

- 빈 구간을 raw bit array처럼 전부 펼치지 않는다
- 구간별 밀도 차이에 맞춰 표현을 바꾼다
- exact bitmap `AND/OR/ANDNOT` 감각을 버리지 않는다

다만 "`compressed`라서 항상 더 작고 항상 더 빠르다"는 뜻은 아니다.
Dense 범위에서는 plain `BitSet`이 더 단순하고 잘 맞을 수 있고, analytic run-heavy workload에서는 `Roaring` 외 다른 계열이 더 자연스러울 수도 있다.

## 흔한 오해와 함정

- "`sparse`면 무조건 compressed bitmap인가요?"
  아니다. membership 위주면 먼저 `Set`이 더 단순하다.
- "`compressed bitmap`은 `Roaring`만 뜻하나요?"
  아니다. beginner/junior 단계에서는 `Roaring`이 가장 자주 보이지만, WAH/EWAH/CONCISE처럼 다른 exact compressed bitmap 계열도 있다.
- "`plain BitSet`은 dense 전용 장난감인가요?"
  아니다. 범위가 촘촘하고 연산이 단순하면 여전히 가장 설명하기 쉬운 기본형이다.
- "`compressed`면 메모리도 성능도 항상 이긴다`?"
  보장되지 않는다. 데이터 분포, 구간 locality, 라이브러리 구현에 따라 달라진다.

## 실무에서 쓰는 모습

실무 문장으로 바꾸면 보통 이렇게 자른다.

- `오늘 대상자 명단을 몇 개의 세그먼트로 교집합한다`, 그리고 사용자 id가 `0..n`에 가깝다
  -> plain `BitSet`부터 검토
- `광고 세그먼트 id`, `실험군 id`, `지역 id`를 exact하게 계속 합치는데 id 범위가 넓고 sparse하다
  -> compressed bitmap 검토

여기서 intermediate 학습자가 기억할 포인트는 "`dense vs sparse`만이 아니라 `membership only vs repeated set algebra`도 같이 봐야 한다"는 점이다.
같은 sparse 정수 id라도 연산이 단건 조회뿐이면 `Set`이 더 자연스러운 경우가 많다.

## 더 깊이 가려면

- `BitSet`에서 어디까지 멈추면 되는지 먼저 다시 보고 싶으면 [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
- `Set`과 `bitmap`의 첫 갈림길부터 다시 보고 싶으면 [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- Java/일반론에서 가장 흔한 compressed bitmap 예시를 보고 싶으면 [Roaring Bitmap](./roaring-bitmap.md)
- run-heavy analytic bitmap까지 넓히고 싶으면 [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
- 알고리즘 문제에서 dense bitset 사고를 먼저 굳히고 싶으면 [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)

## 면접/시니어 질문 미리보기

1. compressed bitmap으로 넘어가는 첫 신호를 한 문장으로 말해보세요.
   `maxId`는 큰데 실제 값은 sparse하고, 그래도 exact set algebra를 반복해야 할 때다.
2. sparse 정수 id에서 왜 바로 `HashSet`으로 끝내면 안 될 수도 있나요?
   membership만이 아니라 집합 전체 `AND/OR/ANDNOT`가 핵심이면 비트 기반 연산 모델을 유지하는 편이 더 자연스러울 수 있다.
3. 왜 `dense vs sparse`만으로는 결정이 부족한가요?
   같은 sparse 데이터라도 연산 패턴이 단건 membership인지 repeated set algebra인지에 따라 선택이 달라지기 때문이다.

## 한 줄 정리

`plain BitSet`과 compressed bitmap의 경계는 단순히 dense/sparse가 아니라, `빈 칸 비용`과 `exact 집합 연산 반복 필요`가 함께 보이느냐로 자르는 것이 intermediate 단계에서 가장 안전하다.
