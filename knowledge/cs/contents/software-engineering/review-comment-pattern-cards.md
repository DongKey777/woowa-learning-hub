# Review Comment Pattern Cards

> 한 줄 요약: "service가 너무 비대함", "controller가 일을 너무 많이 함" 같은 리뷰 문장은 설계 이론 시험이 아니라, **지금 코드에서 책임이 섞인 지점을 먼저 자르라**는 신호로 읽으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Mission Review Vocabulary Primer](./mission-review-vocabulary-primer.md)
- [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md)
- [Service 계층 기초](./service-layer-basics.md)
- [계층형 아키텍처 기초](./layered-architecture-basics.md)
- [DTO, VO, Entity 기초](./dto-vo-entity-basics.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: review comment pattern cards, review feedback cards beginner, service가 너무 비대함, controller가 일을 너무 많이 함, validation 위치가 섞여 있음, dto entity 경계 모호, 리뷰 문장 해석 카드, 첫 수정 체크리스트, review feedback translation beginner, 우테코 리뷰 문장 해석, service too big checklist, fat service beginner, fat controller beginner, review comment first fix, beginner review feedback router

## 먼저 잡는 한 줄 멘탈 모델

리뷰 문장은 "너무 틀렸다"는 낙인이 아니라, **한 클래스가 두 개 이상 질문에 동시에 답하고 있다**는 경고로 읽으면 된다.

## 30초 번역표

| 자주 보는 리뷰 문장 | 보통 뜻 | 첫 질문 |
|---|---|---|
| `service가 너무 비대합니다` | 유스케이스 조립, 규칙, 저장 세부, 외부 연동이 한곳에 몰렸다 | "이 메서드가 지금 몇 단계 일을 동시에 하나?" |
| `controller가 일을 너무 많이 합니다` | HTTP 입력 처리 바깥의 규칙이나 저장 판단이 controller에 들어왔다 | "이 로직이 웹 말고 다른 진입점에서도 필요할까?" |
| `validation 위치가 섞여 있어요` | 형식 검증과 업무 규칙 검증이 뒤섞였다 | "포맷 검사인가, 도메인 규칙인가?" |
| `DTO / Entity 경계가 모호합니다` | API 계약과 내부 저장 모델이 한 타입으로 묶였다 | "응답 모양이 DB 구조에 끌려가고 있나?" |

## 카드 1. `service가 너무 비대합니다`

**1문장 해석**

Service가 "흐름 조립자"를 넘어 규칙, 저장 세부, 응답 조립, 외부 호출까지 한꺼번에 떠안고 있다는 뜻이다.

**첫 수정 체크리스트**

- 한 메서드 안에서 `검증 -> 계산/상태 변경 -> 저장 -> 응답 조립`이 모두 같이 있는지 표시한다.
- `Order.place(...)`처럼 객체 스스로 지킬 수 있는 규칙이 있으면 Domain 쪽으로 먼저 뺀다.
- SQL/JPA 옵션, `saveAndFlush`, 외부 API 요청 세부가 Service에 보이면 Repository나 Client 경계로 내린다.
- Service 메서드 이름이 `process`, `handle`, `doEverything`처럼 뭉뚱그려져 있으면 유스케이스 이름으로 다시 붙인다.
- 규칙을 뺀 뒤에는 [테스트 전략 기초](./test-strategy-basics.md)에서 단위 테스트 1개를 먼저 잠근다.

**작은 예시**

| before 신호 | after 방향 |
|---|---|
| `OrderService.create()` 안에 수량 검증, 재고 차감, JPA 저장, 응답 DTO 생성이 다 있다 | Service는 `place order` 순서만 조립하고, 규칙은 `Order`/`Stock` 쪽으로, 응답 조립은 Controller/Assembler로 나눈다 |

**흔한 오해**

- "메서드 줄 수가 길면 무조건 비대하다"
  - 교정: 줄 수보다 서로 다른 책임 종류가 몇 개 섞였는지가 먼저다.
- "service가 비대하니 클래스를 무조건 여러 개로 쪼개면 된다"
  - 교정: 파일 개수를 늘리기 전에 규칙, 조립, 저장 세부의 경계를 먼저 설명할 수 있어야 한다.

## 카드 2. `controller가 일을 너무 많이 합니다`

**1문장 해석**

Controller가 요청 해석을 넘어서 업무 규칙 판단이나 저장소 조회까지 직접 하고 있다는 뜻이다.

**첫 수정 체크리스트**

- `@RequestBody`, `@PathVariable` 근처에서 `if` 규칙 분기나 repository 호출이 바로 나오는지 본다.
- `null`, 빈 문자열, 형식 오류처럼 HTTP 입력 문제만 controller에 남긴다.
- `중복 이메일이면 가입 불가` 같은 규칙은 다른 진입점에서도 필요하므로 Service/Domain으로 올린다.
- Controller 테스트는 요청/응답 계약에 집중하고, 규칙 테스트는 Service/Domain 쪽으로 옮긴다.

**흔한 오해**

- "조회가 한 번 들어가면 무조건 controller에서 처리해도 된다"
  - 교정: 조회가 있다는 사실보다, 그 판단이 업무 규칙인지가 더 중요하다.

## 카드 3. `validation 위치가 섞여 있어요`

**1문장 해석**

입력 형식 검사와 비즈니스 규칙 검사가 같은 층에 뒤엉켜 있어 재사용과 테스트가 어려워졌다는 뜻이다.

**첫 수정 체크리스트**

- `@NotBlank`, `@Email`, 숫자 형식처럼 요청 포맷 검사는 controller/request DTO 쪽으로 분리한다.
- `재고는 0보다 작아질 수 없다`, `주문 수량은 1 이상`처럼 상태 규칙은 Domain 또는 Service로 모은다.
- "이 검증이 배치나 다른 API에서도 똑같이 필요할까?"를 기준으로 위치를 정한다.
- 검증 위치를 나눈 뒤에는 포맷 검사는 슬라이스/통합 테스트, 규칙 검사는 단위 테스트로 나눠 본다.

**짧은 비교표**

| 검증 종류 | 먼저 둘 곳 | 예시 |
|---|---|---|
| 입력 형식 검증 | Controller / Request DTO | 이메일 형식, 빈 값, JSON 필드 누락 |
| 도메인 규칙 검증 | Domain / Service | 재고 부족, 중복 가입 금지, 최소 주문 수량 |

## 카드 4. `DTO / Entity 경계가 모호합니다`

**1문장 해석**

바깥 계약(API 응답/요청)과 안쪽 저장 모델(DB/JPA 엔티티)이 같은 타입으로 섞여 변경 이유가 충돌하고 있다는 뜻이다.

**첫 수정 체크리스트**

- Controller 응답이 Entity를 그대로 반환하는지 먼저 본다.
- 응답에서 꼭 필요한 필드만 가진 Response DTO를 하나 만든다.
- Request DTO에서 바로 엔티티를 수정하기보다 Service에서 필요한 command/값으로 번역한다.
- `@Entity` 필드 추가가 API 스펙 변경으로 바로 이어지는 구조인지 확인한다.

**흔한 오해**

- "작은 프로젝트니까 entity를 그대로 써도 괜찮다"
  - 교정: 처음엔 빠르지만, 리뷰에서 말하는 문제는 지금보다 다음 수정 때 비용이 커진다는 신호다.

## 어디부터 열어야 할지 막힐 때

| 지금 받은 코멘트 | 바로 이어서 읽을 문서 |
|---|---|
| `service가 너무 비대함` | [Service 계층 기초](./service-layer-basics.md), [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md) |
| `controller가 일을 너무 많이 함` | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| `validation 위치가 섞임` | [계층형 아키텍처 기초](./layered-architecture-basics.md#controller-검증트랜잭션-경계-self-check-3문항), [Service 계층 기초](./service-layer-basics.md#검증트랜잭션-경계-quick-sync) |
| `DTO / Entity 경계가 모호함` | [DTO, VO, Entity 기초](./dto-vo-entity-basics.md) |

## 한 줄 정리

리뷰 문장을 용어 해설로만 읽지 말고, "지금 이 클래스가 맡으면 안 되는 책임이 무엇인가"를 먼저 찾는 카드로 쓰면 첫 수정 방향이 훨씬 빨리 잡힌다.
