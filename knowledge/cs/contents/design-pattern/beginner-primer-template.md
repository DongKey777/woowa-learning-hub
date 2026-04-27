# Beginner Primer 작성 템플릿: 30초 비교표 + 1분 예시 박스 스켈레톤

> 한 줄 요약: 새 beginner primer를 쓸 때는 "큰 그림 2~3문장 -> 30초 비교표 -> Quick-Check -> Confusion Box -> 1분 예시 -> 다음 문서" 순서와 제목 톤을 고정해 두면 첫 독해 리듬이 안정된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> - [템플릿 메소드 첫 질문 라우터: `hook method`, `abstract step`, `template method vs strategy`](./template-method-query-router-beginner.md)
> - [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)
> - [Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때](./policy-object-vs-strategy-map-beginner-bridge.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: beginner primer template, design pattern beginner primer template, quick check skeleton, confusion box skeleton, beginner bridge template, primer writing guide, beginner doc checklist, quick-check section template, common confusion section template, first read template pattern docs, pattern primer skeleton, example box title standard, comparison table title standard, 1분 예시 제목 규칙, 30초 비교표 제목 규칙

---

> Primer Scope: `support-template`

## 먼저 잡을 멘탈 모델

초보자용 primer는 설명을 많이 넣는다고 좋아지지 않는다.
첫 독해에서는 보통 아래 두 가지가 먼저 필요하다.

- 이 패턴을 **어떤 문제 그림**으로 보면 되는가
- 지금 읽는 이름이 **무엇과 자주 헷갈리는가**

그래서 beginner primer는 "정의"보다 **빠른 판별과 혼동 교정**을 먼저 준다.

## 가장 작은 기본 뼈대

새 primer를 만들 때는 아래 순서를 기본으로 둔다.

| 섹션 | 하는 일 | 길이 가이드 |
|---|---|---|
| 한 줄 요약 | 검색 첫 클릭에서 큰 그림 제공 | 1문장 |
| 10초 질문 | 전문 용어보다 문제 그림 먼저 제시 | 2~3문장 |
| 30초 비교표 | 가까운 대안과 경계 자르기 | 3~5행 |
| Quick-Check | "지금 이 문서가 맞는가"를 빠르게 판별 | 3문항 |
| Confusion Box | 초보자가 가장 자주 틀리는 오해 2~4개 교정 | 2~4개 |
| 1분 예시 | 코드 3~10줄 또는 미니 상황표 | 1개 |
| 다음 읽기 | advanced detail을 밖으로 밀어내기 | 3~5링크 |

짧게 외우면 이 한 줄이면 충분하다.

**큰 그림을 먼저 주고, Quick-Check로 붙잡고, Confusion Box로 잘못 읽는 길을 막는다.**

## 맨 위에 붙일 scope marker

이제 beginner 문서는 파일명 추측보다 **명시적 분류**를 먼저 남긴다.
lint의 정답표는 [Primer Scope Manifest](./primer-scope-manifest.md)를 우선으로 보되, 새 문서 본문에도 아래 한 줄을 붙여 두는 것을 기본값으로 삼는다.

| 문서 역할 | 권장 marker |
|---|---|
| 첫 진입 primer | `> Primer Scope: \`true-beginner-primer\`` |
| 질문 라우터형 entrypoint | `> Primer Scope: \`beginner-entrypoint-router\`` |
| 비교/연결 bridge | `> Primer Scope: \`beginner-bridge\`` |
| review/판별 checklist | `> Primer Scope: \`beginner-checklist\`` |

초보자용 primer를 새로 쓰는 경우에는 보통 첫 줄 요약 아래에 이 한 줄만 추가하면 충분하다.

## 표준 제목과 톤 먼저 고정하기

처음 읽는 사람이 리듬을 빨리 익히려면 섹션 순서만 맞추는 것보다 제목 문구를 비슷하게 유지하는 편이 더 낫다.
beginner primer에서는 아래 네 줄을 기본 라벨로 통일해 둔다.

| 섹션 | 기본 제목 | 톤 규칙 |
|---|---|---|
| 질문 블록 | `### 10초 질문` | 정의가 아니라 "지금 이 문제인가?"를 묻는 질문형 |
| 비교표 | `### 30초 비교표: A / B / C` | 패턴 이름 나열보다 비교 대상을 제목에 직접 드러내기 |
| 예시 박스 | `### 1분 예시: [도메인 상황]` | 추상 용어보다 `PG 응답 번역`, `회원 등급 할인`처럼 장면 이름 쓰기 |
| 혼동 교정 | `### 자주 헷갈리는 포인트 N개` | 항목 수를 제목에 넣어 스캔 속도 높이기 |

짧게 외우면 이 기준이면 된다.

- 비교표 제목은 "무엇과 무엇을 자르는지"를 바로 보이게 쓴다.
- 예시 제목은 "패턴 이름 설명"보다 "현업 장면 한 컷"처럼 쓴다.
- 첫 화면에서 `작은 예시`, `짧은 예시`, `코드 예시`처럼 제각각 쓰지 말고 `1분 예시`로 맞춘다.

## 바로 복붙할 Quick-Check 스켈레톤

아래 블록은 beginner primer에 그대로 가져다 써도 된다.
문항 수는 3개를 기본으로 두는 편이 가장 읽기 쉽다.

```md

## Quick-Check

아래 3문항 중 2개 이상이 "예"면 이 문서를 먼저 읽으면 된다.

1. [지금 패턴/개념]이 필요한 상황이 [짧은 상황 문장]인가?
2. 내가 바꾸려는 것은 [흐름 / 규칙 / 생성 / 조회] 중 [핵심 축]인가?
3. 지금 헷갈리는 대상이 [비교 패턴 A] / [비교 패턴 B] / [단순 대안] 중 하나인가?
```

### Quick-Check 작성 규칙

- 문항은 정의 암기가 아니라 **상황 판별** 질문으로 쓴다.
- "정확한 용어를 아는가"보다 "**이 문제가 내 문제인가**"를 먼저 묻는다.
- 답이 애매하면 다음 문서 링크로 자연스럽게 빠지게 한다.

## 바로 복붙할 Confusion Box 스켈레톤

Confusion Box는 glossary가 아니라 오해를 교정하는 작은 박스다.
입문 primer에서 항목 수가 보이면 스캔 속도가 빨라지므로, 가능하면 `자주 헷갈리는 포인트 3개`처럼 **개수까지 제목에 함께 적는 방식**을 기본으로 둔다.
아래처럼 box 스타일 문장으로도 쓸 수 있다.

```md

## Confusion Box

> 자주 헷갈리는 포인트
>
> - "[오해 문장]" -> 아니다. [가장 짧은 교정 문장].
> - "[오해 문장]" -> 먼저 [구분 기준]부터 본다.
> - "[오해 문장]" -> 이 문서는 [경계 A]까지 다루고, [경계 B]는 관련 문서로 넘긴다.
```

### Confusion Box 작성 규칙

- 오해 문장을 실제 검색어/리뷰 코멘트 말투로 쓴다.
- 교정 문장은 길게 설명하지 말고 **구분 기준 1개**만 준다.
- advanced edge case는 박스 안에서 다 풀지 말고 관련 문서로 넘긴다.

## 두 섹션을 함께 놓는 추천 위치

초보자 primer에서는 보통 아래 순서가 가장 안정적이다.

1. 큰 그림
2. 30초 비교표
3. Quick-Check
4. Confusion Box
5. 1분 예시
6. 다음 읽기

이 순서를 쓰는 이유는 단순하다.

- 비교표가 먼저 있어야 Quick-Check 문항이 뜬금없지 않다.
- Quick-Check가 먼저 있어야 Confusion Box를 "내 오해 교정"으로 읽는다.
- Confusion Box 뒤에 예시를 두면 교정된 기준으로 예시를 다시 볼 수 있다.

## 1분 예시 박스 제목을 붙이는 법

예시 박스 제목은 "패턴 설명"이 아니라 "처음 읽는 사람이 떠올릴 장면"이어야 한다.

| 덜 읽히는 제목 | 더 나은 표준 제목 | 이유 |
|---|---|---|
| `### 작은 예시` | `### 1분 예시: 회원 등급 할인` | 무엇을 보는지 제목만 읽어도 안다 |
| `### 코드 예시` | `### 1분 예시: 외부 PG 응답 번역` | 코드보다 문제 장면이 먼저 들어온다 |
| `### 사용 예` | `### 1분 예시: 주문 요청 조립` | 예시의 책임과 문맥이 같이 보인다 |

예시 박스 본문도 같은 톤으로 맞춘다.

- 첫 문장은 "아래처럼 [흐름/규칙/번역/생성]이 바뀌는지 보면 된다"처럼 관찰 포인트를 먼저 준다.
- 표나 코드는 3~5행 안에서 끝내고, 마지막 한 줄은 "여기까지가 이 패턴 책임"으로 닫는다.
- 운영 edge case나 프레임워크 세부 API는 여기서 길게 풀지 말고 다음 읽기로 넘긴다.

## 1분 예시 문장을 Strategy primer에 붙인다면

| 섹션 | 들어갈 문장 예시 |
|---|---|
| Quick-Check | "규칙은 자주 바뀌는데 전체 주문 흐름은 거의 같나요?" |
| Quick-Check | "호출자나 DI가 이번 구현을 골라 넣을 수 있나요?" |
| Confusion Box | "`if-else`가 있으면 strategy가 아닌가요? -> 아니다. 핵심은 변경 축 분리다." |
| Confusion Box | "`Context`가 구현을 스스로 고르면 더 strategy답나요? -> 보통은 아니다. 선택 책임은 호출자/설정/DI 쪽이 더 자연스럽다." |

즉 섹션 이름만 복사하는 것이 아니라,
각 패턴에서 초보자가 **어디서 멈추는지**를 먼저 문장으로 바꿔 넣어야 한다.

## 새 beginner primer 작성 체크리스트

- 한 줄 요약이 용어 정의보다 문제 그림을 먼저 주는가
- 첫 20줄 안에 비교표나 `1분 예시`가 있는가
- Quick-Check가 3문항 안팎으로 들어가 있는가
- Confusion Box가 실제 오해 문장으로 적혀 있는가
- 비교표와 예시 제목이 `30초 비교표: ...`, `1분 예시: ...` 톤으로 맞춰져 있는가
- advanced failure mode가 본문 중심이 아니라 관련 문서 링크로 밀려 있는가
- 마지막에 "다음 읽기"가 있어 beginner -> bridge -> deep dive 경로가 보이는가

## 바로 시작용 미니 템플릿

```md
# [문서 제목]

> 한 줄 요약: [문제 그림 + 패턴 역할]
> Primer Scope: `true-beginner-primer`

**난이도: 🟢 Beginner**

## 큰 그림 먼저

[문제 상황 2~3문장]

## 30초 비교표: [비교 대상 A] / [비교 대상 B]

| 질문 | 이 문서 쪽 | 자주 헷갈리는 다른 쪽 |
|---|---|---|
| [질문 1] | [답] | [답] |

## Quick-Check

아래 3문항 중 2개 이상이 "예"면 이 문서를 먼저 읽으면 된다.

1. ...
2. ...
3. ...

## Confusion Box

> 자주 헷갈리는 포인트
>
> - "..." -> ...
> - "..." -> ...

## 1분 예시: [도메인 상황]

[짧은 코드 또는 표]

## 다음 읽기

- [bridge 문서]
- [deep dive 문서]
- [관련 anti-pattern / smell 문서]
```

## 한 줄 정리

beginner primer는 완전한 사전이 아니라 첫 진입용 안내판이다. 그래서 `30초 비교표: ...`와 `1분 예시: ...` 제목 톤까지 고정해 두면 초보자가 문서마다 새 리듬을 다시 배우지 않아도 된다.
