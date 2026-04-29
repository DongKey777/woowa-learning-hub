# Bitmap vs Set Dense Integer ID Beginner Bridge

> 한 줄 요약: `Set`은 "이 값이 있나?"를 가장 자연스럽게 시작하는 기본 명단이고, `bitmap/bitset`은 `0..n` 정수 id를 아주 많이 겹쳐 보거나 메모리를 더 빡빡하게 아껴야 할 때 고려하는 한 단계 더 구조화된 명단이다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [Set vs Bitmap Audience Selection Mini Drill](./set-vs-bitmap-audience-selection-mini-drill.md)
- [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)
- [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
- [Roaring Bitmap](./roaring-bitmap.md)
- [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)

retrieval-anchor-keywords: bitmap vs set beginner, bitset vs set basics, dense integer id membership, set or bitmap when to use, sparse integer id range, sparse range bitset wasteful, roaring bitmap beginner handoff, compressed bitmap first step, 비트맵 셋 차이, bitset 뭐예요, dense id 처음, sparse id 처음, bitmap 언제 worth it, 정수 id 집합 헷갈림, 왜 bitset이 아까워요

## 핵심 개념

처음엔 `Set`을 "이름표를 하나씩 꽂는 명단"으로, `bitmap/bitset`을 "번호표 칸마다 체크 하나씩 두는 명단"으로 보면 된다.

- `Set`: 값 자체를 원소로 저장한다
- `bitmap/bitset`: `0`, `1`, `2`처럼 정수 id 위치에 비트를 켠다

둘 다 membership 구조지만 출발 질문이 다르다.

- 값이 문자열, UUID, 객체처럼 자유롭다 -> 보통 `Set`
- 값이 `0..n` 범위의 정수 id로 이미 정규화돼 있다 -> `bitmap/bitset` 후보

입문자가 가장 많이 헷갈리는 지점은 "`bitmap`이 더 빠르다던데 처음부터 다 비트로 해야 하나요?"다.
대부분의 초급 문제는 그렇지 않다.
먼저는 `Set`이 더 읽기 쉽고, `dense integer id`, `집합 교집합 반복`, `메모리 압박`이 같이 보일 때만 `bitmap/bitset`을 꺼내면 된다.

## 한눈에 보기

| 지금 문제에서 먼저 필요한 답 | 먼저 떠올릴 구조 | 이유 |
|---|---|---|
| `이 requestId 이미 처리했나?` | `Set<String>` | id가 일반 문자열이고 membership 한 번이면 충분하다 |
| `회원 1, 7, 42가 대상에 포함되나?` | `Set<Long>` | 규모가 아직 작고 구현 단순성이 더 중요하다 |
| `0..999999 회원 중 active 집합과 premium 집합의 교집합` | `bitmap/bitset` | 정수 id 범위가 고정되고 집합 전체 연산이 핵심이다 |
| `오늘 대상자 집합을 여러 조건으로 AND/OR 한다` | `bitmap/bitset` | membership 한 번보다 대량 집합 연산 비용이 중요하다 |
| `id는 정수인데 3, 5000000, 9000000처럼 듬성듬성 있다` | `Set` 또는 압축 bitmap | plain bitset은 빈 칸이 너무 많아질 수 있어 먼저 분리해서 봐야 한다 |

짧은 결정표로 다시 보면 더 쉽다.

| 질문 | `Set` 쪽 신호 | `bitmap/bitset` 쪽 신호 |
|---|---|---|
| 원소 타입이 자유로운가 | 강함 | 약함 |
| `0..n` 정수 id로 바로 매핑되나 | 약함 | 강함 |
| 단건 `contains`가 대부분인가 | 강함 | 약함 |
| 교집합/합집합을 계속 반복하나 | 약함 | 강함 |
| 범위가 작고 촘촘한가 | 약함 | 강함 |

처음 판단할 때는 아래 한 줄을 기본값으로 두면 된다.

> `contains` 몇 번 하고 끝나면 `Set`, 같은 정수 id 집합들을 매번 겹쳐 계산하면 `bitmap/bitset`

## 언제 Set으로 충분한가

아래 셋 중 두 개 이상이 맞으면 대부분 `Set`으로 끝내도 된다.

1. id가 문자열, UUID, 이메일처럼 바로 비트 칸에 놓기 어렵다
2. 질문이 거의 항상 `"있나?"` 한 번에서 끝난다
3. 집합 전체를 `AND/OR`로 겹쳐 보는 일은 드물다
4. 구현 단순성과 코드 가독성이 지금 더 중요하다

예를 들어 `processedRequestIds`, `visitedUsers`, `blockedEmails` 같은 장면은 보통 `Set`이 자연스럽다.
`bitmap`으로 바꾸려면 먼저 문자열을 정수 id로 바꾸는 별도 매핑이 필요하고, 그 비용이 더 클 수 있다.

즉 beginner 기준의 안전한 기본값은 이렇다.

> "정수 id 집합 연산이 핵심이라는 증거가 아직 없으면 일단 Set"

### dense integer id여도 그냥 Set에 머물러도 되는 장면

입문자가 자주 놓치는 점은 "`정수 id`라는 사실 하나만으로는 아직 부족하다"는 것이다.
아래처럼 `dense integer id`여도 질문이 단순하면 `Set<Long>`이 더 낫다.

| 장면 | `Set`에 머물러도 되는 이유 |
|---|---|
| `오늘 본 사용자 id를 중복 처리만 막기` | 단건 `contains/add`가 전부라서 비트 연산 이득이 거의 없다 |
| `테스트/운영 도구에서 작은 대상자 명단 보관` | 코드 설명성과 디버깅 편의가 더 중요하다 |
| `정수 id지만 실제 값 개수가 적고 집합 합치기도 거의 없음` | bitmap용 별도 구조를 유지하는 비용이 먼저 생긴다 |

핵심은 "id가 숫자인가"보다 "집합 전체를 계산 대상으로 다루는가"다.

## 언제 bitmap/bitset이 worth it 한가

아래 신호가 모이면 `bitmap/bitset`이 추가 구조값을 하기 시작한다.

1. 원소가 이미 `0..n` 정수 id다
2. id 범위가 비교적 촘촘하거나 상한이 뚜렷하다
3. `contains`보다 `교집합`, `합집합`, `차집합`을 자주 한다
4. 같은 집합을 여러 번 재사용한다
5. 메모리 사용량이나 대량 대상 계산 시간이 실제 문제다

예를 들어 `activeUsers`, `premiumUsers`, `couponEligibleUsers`를 매번 겹쳐 대상자를 계산한다면, 원소를 하나씩 비교하는 사고보다 비트 집합 연산 사고가 더 잘 맞는다.

### extra structure 비용을 감수할 이유가 생기는 순간

`bitmap/bitset`은 단순히 "빠른 set"이 아니라, 아래 비용을 받아들이는 대신 집합 연산을 싸게 만드는 구조다.

- 정수 id 범위를 기준으로 비트 칸을 관리해야 한다
- 문자열/UUID면 먼저 정수 id로 바꾸는 별도 매핑이 필요하다
- 디버깅할 때도 "값 목록"보다 "비트 표현"을 한 번 더 번역해야 할 수 있다

그래서 아래 둘이 함께 보여야 beginner도 납득하기 쉽다.

1. `dense integer id`라서 비트 칸을 만들기 쉽다
2. `AND/OR/NOT`를 반복해서 extra structure 비용을 회수할 수 있다

Java 기준으로는 초급 단계에서 `bitmap`을 "`BitSet` 같은 비트 기반 집합" 정도로 이해해도 충분하다.
데이터가 더 커지고 희소/밀집 구간이 섞이면 그다음에 [Roaring Bitmap](./roaring-bitmap.md)으로 내려가면 된다.

## 같은 서비스 장면에서 갈리는 기준

같은 "대상자 선택" 문제도 질문이 어디에 있느냐에 따라 달라진다.

| 같은 장면 | 먼저 고를 구조 | 이유 |
|---|---|---|
| `이 사용자 id가 이미 알림을 받았나?` | `Set<Long>` | 단건 membership이 핵심이다 |
| `서울 사용자 ∩ 프리미엄 사용자 ∩ 휴면 아님` | `bitmap/bitset` | 여러 집합을 계속 겹쳐 본다 |
| `이 이메일이 블랙리스트에 있나?` | `Set<String>` | 문자열 membership 문제다 |
| `오늘 0..999999 사용자 중 3개 세그먼트 교집합` | `bitmap/bitset` | dense integer id와 대량 집합 연산이 같이 있다 |

짧은 mental model 하나만 기억하면 초반 실수가 많이 줄어든다.

- 원소 하나하나를 들고 다니면 `Set`
- 번호판 전체에 체크 상태를 깔아두면 `bitmap/bitset`

## 정수 id인데 sparse range라면 무엇이 달라지나

beginner가 자주 멈추는 follow-up은 이 질문이다.

> "`id`는 분명 정수인데, `10`, `5000000`, `9000000`처럼 듬성듬성 있으면 bitset이 맞나요?"

여기서는 `정수 id`라는 사실만 보면 안 되고, `칸을 얼마나 넓게 깔아야 하는지`를 같이 봐야 한다.

- `Set`: 실제로 들어 있는 id만 들고 다닌다
- plain `BitSet`: `maxId`까지 칸을 미리 펼친다고 생각하면 쉽다
- compressed bitmap (`Roaring Bitmap` 등): 빈 칸이 많은 구간은 더 작게 들고 가고, 필요한 구간만 비트맵처럼 다룬다

짧은 예시로 보면 감이 빨리 온다.

| id 집합 | beginner가 먼저 떠올릴 구조 | 이유 |
|---|---|---|
| `10, 11, 12, 13` | plain `BitSet` 후보 | 범위가 짧고 촘촘해서 칸을 깔아도 낭비가 작다 |
| `10, 5000000, 9000000` | `Set` 기본값 | membership 몇 번이면 `maxId`까지 칸을 까는 발상이 너무 비싸다 |
| `10, 5000000, 9000000`를 여러 집합과 계속 `AND/OR` | compressed bitmap 후보 | sparse range인데도 exact set algebra를 자주 하므로 plain `BitSet`과 `Set` 사이 다리가 필요하다 |

핵심 mental model은 한 줄이다.

> 정수 id여도 `범위가 넓고 듬성듬성`이면 plain `BitSet`은 빈 칸 비용이 커질 수 있어서, 먼저 `Set`에 머무르거나 compressed bitmap으로 넘어갈지 따로 판단해야 한다.

### sparse range에서 beginner가 안전하게 고르는 순서

처음엔 아래 순서로 자르면 실수가 적다.

1. 그냥 `contains/add/remove` 위주인가? -> 우선 `Set`
2. `maxId`가 작고 실제 값도 촘촘한가? -> plain `BitSet` 후보
3. `maxId`는 큰데 exact `AND/OR/ANDNOT`를 반복하나? -> compressed bitmap 후보

표로 다시 보면 더 명확하다.

| 질문 | `Set` 쪽 | plain `BitSet` 쪽 | compressed bitmap 쪽 |
|---|---|---|---|
| 값이 몇 개 안 되고 듬성듬성 떨어져 있나 | 강함 | 약함 | 보통 |
| `maxId`가 작고 촘촘한가 | 약함 | 강함 | 보통 |
| exact 집합 연산을 반복하나 | 약함 | 보통 | 강함 |
| 구현 단순성이 제일 중요한가 | 강함 | 보통 | 약함 |

여기서 beginner 기본값은 여전히 `Set`이다.
`정수 id + sparse range`만으로 바로 compressed bitmap까지 갈 필요는 없다.
정말로 다음 두 조건이 같이 보여야 handoff가 안전하다.

- plain `BitSet`은 `maxId` 기준으로 너무 wasteful하다
- 그런데도 exact 집합 연산을 자주 해서 `Set`보다 비트 기반 사고가 여전히 유리하다

## sparse range follow-up에서 많이 하는 오해

- "`id`가 int니까 무조건 bitset 아닌가요?"
  아니다. `int`인지보다 `range가 촘촘한지`, `빈 칸이 너무 많은지`가 더 중요하다.
- "`BitSet`이 낭비면 바로 HashSet으로 끝인가요?"
  membership 위주면 맞다. 하지만 sparse range에서도 exact 집합 연산을 계속 하면 compressed bitmap이 중간 해답이 될 수 있다.
- "`Roaring`은 완전히 다른 자료구조라 beginner가 몰라도 되나요?"
  내부는 advanced지만, beginner는 "`sparse range용 압축 bitmap`이라는 안전한 다음 단계가 있다"까지만 알아도 충분하다.

## sparse range에서 다음 안전한 한 걸음

여기까지 이해했다면 handoff는 이렇게 잡으면 된다.

- `정수 id지만 집합 연산보다 membership이 대부분이다` -> 계속 `Set`
- `정수 id가 촘촘하고 범위가 작다` -> plain `BitSet`
- `정수 id가 sparse range인데도 exact 집합 연산을 반복한다` -> [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md)로 한 단계 더 안전하게 내려가기

`Roaring Bitmap`은 "희소한 구간은 배열처럼, 조밀한 구간은 비트맵처럼" 다루는 쪽으로 이 간극을 메운다.
더 넓게 비교하고 싶다면 아래 순서가 beginner-safe 하다.

1. [BitSet vs Roaring Bitmap Beginner Handoff](./bitset-vs-roaring-bitmap-beginner-handoff.md): `BitSet` mental model에서 어디까지 멈추고 언제 handoff할지
2. [Roaring Bitmap](./roaring-bitmap.md): sparse range에서 plain `BitSet`이 왜 아쉬운지
3. [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md): `Roaring`, `BitSet`, 다른 압축 표현의 질문 차이
4. [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md): run-heavy analytic bitmap까지 넓히기

## 처음 도입할 때 쓰는 30초 체크

처음엔 아래 4문항만 체크해도 충분하다.

| 질문 | `예`면 어디로 기우나 |
|---|---|
| 값이 문자열/UUID가 아니라 이미 `0..n` 정수 id인가 | `bitmap/bitset` 후보 |
| 질문이 대부분 단건 `contains`인가 | `Set` 쪽 |
| 같은 집합들을 `교집합/합집합/차집합`으로 여러 번 합치나 | `bitmap/bitset` 쪽 |
| 구현을 단순하게 끝내는 편이 지금 더 중요한가 | `Set` 쪽 |

4개 중 앞의 2개가 `bitmap/bitset` 쪽으로 모이더라도, 단건 membership 위주라면 아직 `Set`이 안전한 기본값이다.
반대로 `dense integer id`와 `반복 set algebra`가 같이 보이면 그때부터는 비트 구조가 "과한 최적화"가 아니라 문제를 직접 표현하는 방법이 된다.

## 흔한 오해와 함정

- "`bitmap`이 더 저수준이니 항상 더 빠른가요?"
  아니다. 작은 집합이나 문자열 id 문제에서는 `Set`이 더 단순하고 충분하다.
- "`Set<Long>`이면 이미 정수니까 바로 bitmap으로 바꿔야 하나요?"
  아니다. `Long`이라는 타입보다 `dense integer id`와 `반복 set algebra`가 더 중요한 신호다.
- "`bitmap`은 membership을 못 하나요?"
  할 수 있다. 다만 가치가 커지는 순간이 단건 조회보다 집합 전체 연산일 때가 많다.
- "`bitset`과 `bitmap`은 다른 건가요?"
  beginner 층위에서는 비트 기반 집합이라는 큰 묶음으로 이해해도 된다. Java 표준 라이브러리 이름은 `BitSet`이고, 더 큰 실무 구조로는 `Roaring Bitmap` 같은 변형이 있다.
- "`문자열 id도 hash해서 bitmap에 넣으면 되지 않나요?"
  그러면 별도 매핑, 충돌 관리, 역조회 문제가 생긴다. beginner 단계에서는 그 복잡도보다 `Set`이 더 안전하다.

## 더 깊이 가려면

- `set` 자체가 아직 헷갈리면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- audience selection 문장에 decision table을 바로 적용해 보고 싶으면 [Set vs Bitmap Audience Selection Mini Drill](./set-vs-bitmap-audience-selection-mini-drill.md)
- 자료구조 선택 큰 그림에서 `bitmap` 위치를 다시 보고 싶으면 [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- Java의 비트 기반 사고를 알고리즘 관점에서 보고 싶으면 [Bitset Optimization Patterns](../algorithm/bitset-optimization-patterns.md)
- 큰 정수 집합에서 왜 `Roaring Bitmap`이 따로 나오는지 알고 싶으면 [Roaring Bitmap](./roaring-bitmap.md)
- `BitSet`, `Roaring`, `Elias-Fano`, filter 계열까지 비교하고 싶으면 [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)

## 면접/시니어 질문 미리보기

1. `Set` 대신 `bitmap`을 고려하는 첫 신호는 무엇인가요?
   원소가 dense한 정수 id로 정규화돼 있고, 집합 전체 AND/OR를 반복할 때다.
2. 왜 문자열 membership 문제는 보통 `Set`에서 시작하나요?
   비트 칸으로 바로 펼치기 어렵고, 단순 membership에는 `Set`이 더 직접적이기 때문이다.
3. `bitmap`을 도입했는데도 항상 이득이 아닌 이유는 무엇인가요?
   id 매핑 비용, 희소 데이터, 낮은 집합 연산 빈도 때문에 구조 추가 이득이 작을 수 있기 때문이다.

## 한 줄 정리

`있나?`를 단순하게 답하면 `Set`, `0..n` 정수 id 집합을 여러 번 겹쳐 보거나 메모리까지 줄여야 하면 그때 `bitmap/bitset`을 고려한다고 먼저 자르면 된다.
