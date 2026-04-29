# BitSet vs Roaring Bitmap Beginner Handoff

> 한 줄 요약: beginner는 먼저 `BitSet`을 "정수 id 칸에 체크하는 집합"으로 이해하면 충분하고, `범위가 너무 넓은데 exact 집합 연산을 계속 해야 한다`는 신호가 보일 때만 `Roaring Bitmap`으로 한 단계 더 내려가면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- [Roaring Bitmap](./roaring-bitmap.md)
- [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
- [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)

retrieval-anchor-keywords: bitset vs roaring bitmap beginner, roaring bitmap beginner handoff, compressed bitmap first step, bitset 언제까지만 알면 되나요, roaring bitmap 뭐예요, sparse range bitmap basics, exact set algebra beginner, bitset vs roaring 차이, dense id 처음, 왜 bitset으로 충분해요, 언제 roaring으로 넘어가요, bitmap basics, what is roaring bitmap, beginner compressed bitmap, bitset 헷갈림

## 핵심 개념

처음에는 `BitSet`과 `Roaring Bitmap`을 둘 다 "정수 id 집합"으로만 묶어 이해해도 된다.
차이는 같은 집합을 **어떻게 들고 다니는지**에 있다.

- `BitSet`: `0..maxId` 칸을 길게 펴 두고 체크한다
- `Roaring Bitmap`: 필요한 구간만 더 작게 나눠 들고 다니면서, 구간별로 표현을 바꾼다

beginner에게 중요한 첫 판단은 내부 자료구조 이름이 아니다.
아래 질문 두 개가 먼저다.

1. 지금 문제를 `BitSet` mental model만으로 설명할 수 있는가
2. `BitSet`이 아쉬운 이유가 실제로 보였는가

둘 다 아직 아니면 `Roaring` 내부로 더 들어가지 않아도 된다.

## 한눈에 보기

| 지금 보이는 문제 문장 | 여기서 멈춰도 되는가 | 다음 한 걸음 |
|---|---|---|
| `0..100000 사용자 중 active 여부만 표시` | 보통 `BitSet`에서 멈춰도 된다 | 비트 집합 감각만 익히기 |
| `dense integer id` 집합을 몇 번 `AND/OR` 한다 | `BitSet`으로 충분할 때가 많다 | 먼저 plain bitmap 사고 고정 |
| `id`는 정수인데 `10`, `5000000`, `9000000`처럼 듬성듬성이다 | `BitSet`만으로는 아쉬울 수 있다 | 왜 빈 칸 비용이 큰지 확인 |
| sparse range 집합들을 exact `AND/OR/ANDNOT`로 계속 합친다 | `Roaring`으로 handoff할 시점이다 | 압축 bitmap을 다음 단계로 보기 |
| 지금은 `contains` 몇 번과 작은 실험 코드가 전부다 | `BitSet`에서 멈추는 편이 안전하다 | advanced internals는 보류 |

짧게 외우면 이 한 줄이다.

> `범위가 작고 촘촘하면 BitSet`, `범위가 넓고 듬성듬성인데 exact 집합 연산을 계속 하면 Roaring`

## BitSet에서 멈춰도 되는 순간

아래 조건이 맞으면 beginner는 `BitSet` mental model만으로 충분하다.

1. 값이 이미 `0..n` 정수 id다
2. `maxId`가 아주 크지 않거나, 실제로 값이 촘촘하다
3. 목표가 비트 기반 집합의 기본 감각을 익히는 것이다
4. 연산이 몇 번의 `set`, `get`, `and`, `or` 정도로 끝난다

예를 들어 `0..9999 좌석`, `0..50000 방문 여부`, `오늘 대상자 집합 2개 교집합` 정도는
굳이 압축 bitmap까지 가지 않아도 설명이 된다.

이 단계에서 꼭 잡아야 하는 감각은 세 가지다.

- 비트 한 칸이 "정수 id 하나의 membership"이라는 점
- `AND/OR`가 집합 연산과 직접 연결된다는 점
- `maxId`까지 칸을 깐다는 비용이 있다는 점

이 셋만 이해해도 beginner 목표는 이미 많이 달성된 상태다.

## Roaring으로 넘어가야 하는 신호

`Roaring Bitmap`은 "`BitSet`이 틀렸다"가 아니라 "`BitSet`을 그대로 크게 펼치기엔 아깝다"에서 시작한다.

아래 신호가 같이 보이면 handoff가 자연스럽다.

1. id는 여전히 정수라서 비트 집합 사고는 유지하고 싶다
2. 그런데 `maxId`가 커서 빈 칸이 너무 많다
3. membership 한 번보다 exact 집합 연산 반복이 더 중요하다
4. `Set`으로 돌아가기엔 비트 기반 `AND/OR` 감각이 이미 문제와 잘 맞는다

대표 예시는 이런 장면이다.

| 장면 | 왜 `BitSet`만으로 아쉬운가 | 왜 `Roaring` 후보가 되나 |
|---|---|---|
| `10`, `5000000`, `9000000` 같은 sparse id 집합 | `maxId`까지 칸을 깔면 빈 공간이 너무 많다 | 빈 구간을 더 압축적으로 다룰 수 있다 |
| 여러 세그먼트를 exact 교집합으로 계속 합친다 | `Set`은 집합 전체 연산 감각이 덜 직접적이다 | 비트 집합 연산 장점을 유지한다 |
| 어떤 구간은 빽빽하고 어떤 구간은 비어 있다 | 한 가지 표현으로만 들고 가기 아깝다 | 구간별로 다른 표현을 쓸 수 있다 |

여기서 beginner가 알면 되는 끝선은 이 정도다.

> `Roaring`은 sparse range에서도 비트 집합 연산을 계속 쓰고 싶을 때 등장하는 "압축 bitmap"이다.

## 흔한 오해와 함정

- "`BitSet`을 알면 `Roaring`도 거의 다 아는 건가요?"
  반은 맞고 반은 아니다. 집합 연산 감각은 이어지지만, `Roaring`은 "필요한 구간만 더 영리하게 들고 간다"는 추가 아이디어가 있다.
- "`maxId`가 크기만 하면 바로 Roaring인가요?"
  아니다. 단건 `contains` 위주면 여전히 `Set`이 더 단순할 수 있다.
- "`Roaring`을 배우려면 container threshold 같은 숫자를 먼저 외워야 하나요?"
  아니다. beginner는 `sparse range용 압축 bitmap`이라는 역할만 먼저 이해하면 충분하다.
- "`BitSet`은 dense data 전용이라 실무성이 없나요?"
  아니다. 범위가 작고 촘촘한 정수 집합에서는 가장 직관적인 출발점이다.

## 실무에서 쓰는 모습

초급자가 가장 이해하기 쉬운 비교는 "같은 대상자 계산을 세 단계로 보는 것"이다.

1. 원소가 문자열이면 먼저 `Set`
2. 원소가 `0..n` 정수 id이고 범위가 작고 촘촘하면 `BitSet`
3. 원소가 정수 id인데 sparse range이고 exact 집합 연산을 계속 하면 `Roaring`

예를 들어 `activeUsers`, `premiumUsers`, `couponEligibleUsers`를 계속 교집합한다고 하자.

- id 범위가 작고 촘촘하다 -> `BitSet`으로도 충분히 설명 가능
- id 범위가 매우 넓고 듬성듬성하다 -> `Roaring`이 왜 필요한지 자연스럽게 나온다

즉 `Roaring`은 `BitSet`을 버리는 다음 단계가 아니라,
`BitSet` mental model을 유지한 채 더 큰 sparse range로 확장하는 다리라고 보면 된다.

## 더 깊이 가려면

- `bitmap`과 `Set`의 출발점부터 다시 자르고 싶으면 [Bitmap vs Set Dense Integer ID Beginner Bridge](./bitmap-vs-set-dense-integer-id-beginner-bridge.md)
- plain bitmap이 알고리즘 문제에서 어떻게 쓰이는지 보고 싶으면 [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)
- `Roaring`을 처음 advanced 층위로 읽고 싶으면 [Roaring Bitmap](./roaring-bitmap.md)
- `Roaring`과 다른 압축 표현까지 비교하고 싶으면 [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)

## 면접/시니어 질문 미리보기

1. `BitSet`에서 `Roaring`으로 handoff하는 첫 신호는 무엇인가요?
   `maxId`가 커서 빈 칸 비용이 큰데도 exact 집합 연산을 계속 해야 할 때다.
2. `Roaring`은 `Set`의 대체인가요, `BitSet`의 확장인가요?
   beginner 관점에서는 `BitSet` mental model을 sparse range까지 확장하는 쪽으로 이해하는 편이 안전하다.
3. 왜 beginner에게 `Roaring` internals를 바로 설명하지 않나요?
   먼저 비트 집합과 집합 연산 감각이 잡혀야 handoff 이유가 자연스럽게 보이기 때문이다.

## 한 줄 정리

beginner는 `BitSet`으로 비트 집합 감각을 먼저 고정하고, `범위가 넓고 듬성듬성한 정수 id 집합을 exact하게 계속 합쳐야 한다`는 신호가 보일 때만 `Roaring Bitmap`으로 넘어가면 된다.
