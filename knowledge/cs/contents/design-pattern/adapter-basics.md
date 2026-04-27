# 어댑터 패턴 기초 (Adapter Pattern Basics)

> 한 줄 요약: 어댑터는 서로 맞지 않는 인터페이스를 중간에서 번역해주는 변환기로, 기존 코드를 바꾸지 않고 외부 라이브러리나 레거시 API를 연결할 때 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Adapter (어댑터) — 심화](./adapter.md)
- [Adapter Chaining Smells](./adapter-chaining-smells.md)
- [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [소프트웨어 공학 카테고리 인덱스](../software-engineering/README.md)

retrieval-anchor-keywords: adapter pattern basics, 어댑터 패턴, adapter pattern beginner, 인터페이스 변환, legacy api adapter, 외부 라이브러리 연결, adapter vs wrapper, adapter vs facade, adapter vs decorator, 어댑터가 뭔가요, interface translation, incompatible interface, 기존 코드 바꾸지 않고, object adapter class adapter, adapter pattern example, external sdk translation, adapter beginner checklist, adapter quick check, adapter beginner quick check, 어댑터 패턴 10초, 어댑터 패턴 30초 비교표, 어댑터 패턴 1분 예시, adapter example box, adapter comparison table, adapter 언제 쓰나, adapter not facade not decorator, translation boundary adapter, 어댑터 자주 헷갈리는 포인트, adapter confusion points beginner, adapter facade confusion check, adapter micro check beginner

---

## 먼저 멘탈 모델

어댑터 패턴은 "내가 원하는 인터페이스"와 "외부 코드가 제공하는 인터페이스"가 맞지 않을 때 중간에서 번역하는 역할을 한다. 여행용 전기 플러그 변환 어댑터와 같다고 생각하면 된다.

입문자가 자주 막히는 부분은 "번역이 필요하지 않으면 어댑터가 필요 없다"는 점이다. 인터페이스가 이미 맞는다면 어댑터를 만들 필요가 없고, 그냥 바로 쓰면 된다.

<a id="adapter-quick-entry"></a>

## 빠른 진입: 10초/30초/1분

처음 읽을 때는 `10초 질문 -> 30초 비교표 -> 1분 예시` 순서로만 먼저 훑는다.

### 10초 질문

- 서비스가 외부 SDK 타입 대신 우리 `Target` 인터페이스만 보게 만들 수 있는가?
- 어댑터 책임이 인터페이스/타입/단위 번역으로 닫혀 있는가?
- 공급자 교체 시 수정이 adapter 구현체 쪽으로만 모이게 만들 수 있는가?

## 핵심 개념

처음에는 아래 한 줄로 보면 된다.

```text
서비스가 쓰는 표준 인터페이스(Target) <-번역- Adapter <-호출- 외부 API(Adaptee)
```

어댑터가 하는 일은 두 가지뿐이다.

- 호출 형태를 맞춘다. 예: `pay(int won)` -> `charge(double dollar)`
- 타입/단위를 변환한다. 예: `String status` -> `PaymentStatus enum`

비즈니스 정책 자체를 결정하는 자리가 아니다. 그 역할은 서비스나 도메인 객체 쪽에 둔다.

## 한눈에 보기

```
Client → Target 인터페이스 → Adapter → Adaptee (외부/레거시)
```

| 역할 | 설명 |
|------|------|
| Target | 클라이언트가 기대하는 인터페이스 |
| Adaptee | 맞지 않는 외부/레거시 클래스 |
| Adapter | Target을 구현하면서 Adaptee를 내부에서 호출 |

### 30초 비교표: Adapter / Facade / Decorator

아래 표는 "무엇을 더 편하게 만들려는가?" 한 질문으로 읽으면 된다.

| 패턴 | 핵심 질문 | 초보자용 한 줄 |
|---|---|---|
| Adapter | 인터페이스가 서로 안 맞는가 | "형태를 맞춰 붙인다" |
| Facade | 복잡한 서브시스템을 단순 창구로 감싸는가 | "사용법을 단순화한다" |
| Decorator | 같은 인터페이스에 기능을 덧붙이는가 | "기능을 추가한다" |

### 1분 예시: 외부 PG 응답을 우리 표준으로 번역하기

아래처럼 상태, 금액, 에러 코드를 우리 쪽 언어로 바꾸는 장면이면 adapter를 떠올리면 된다.

외부 결제 SDK를 붙일 때 어댑터는 보통 아래 세 가지 번역을 맡는다.

| 외부 SDK 응답(Adaptee) | 우리 서비스 표준(Target) | 어댑터에서 하는 번역 |
|---|---|---|
| `"OK"` / `"FAIL"` 문자열 상태 | `PaymentStatus.SUCCESS/FAILED` enum | 문자열 -> enum 매핑 |
| `amount=12.34` (달러) | `amount=12340` (원, 정수) | 단위/타입 변환 |
| `errorCode="E102"` | `PaymentError.CARD_EXPIRED` | 공급자 코드 -> 도메인 코드 매핑 |

핵심은 같다. "상태/단위/코드 번역"까지만 어댑터가 맡고, 환불 정책 같은 비즈니스 판단은 서비스 계층에 남긴다.
즉 이 예시 박스의 결론은 "어댑터는 번역까지만 맡는다"다.

### 자주 헷갈리는 포인트 3개

- 어댑터의 중심 책임은 "번역"이다. 정책 결정까지 넣으면 서비스/도메인 책임과 섞인다.
- wrapper 모양이 비슷해도 목적이 다르면 다른 패턴이다. 인터페이스 불일치 해소가 아니면 어댑터가 아닐 수 있다.
- 외부 SDK 타입을 서비스 전역에 노출하면 교체 비용이 커진다. Target 인터페이스를 먼저 고정해 경계를 만든다.

## 상세 분해

어댑터의 구성 요소:

- **Target 인터페이스** — 클라이언트가 사용하고 싶은 인터페이스다. 예: `PaymentGateway.pay(int amount)`.
- **Adaptee** — 기존에 있는 외부 클래스이지만 인터페이스가 다르다. 예: `LegacyPgClient.charge(double money)`.
- **Adapter** — Target을 구현하고, Adaptee를 내부에 보유해 위임 호출한다. 타입·단위 변환 등 번역 로직이 여기에 들어간다.

```java
public class LegacyPgAdapter implements PaymentGateway {
    private final LegacyPgClient client;
    public LegacyPgAdapter(LegacyPgClient client) { this.client = client; }
    public void pay(int amount) {
        client.charge(amount / 100.0);  // int 원 → double 달러 변환
    }
}
```

## 흔한 오해와 함정

- **"어댑터와 데코레이터는 같다"** — 어댑터는 인터페이스를 맞추는 것이고, 데코레이터는 기능을 추가하는 것이다. 어댑터는 두 인터페이스가 달라야 의미가 있다.
- **"어댑터 안에 비즈니스 로직을 넣으면 좋다"** — 어댑터는 번역만 해야 한다. 로직이 들어가면 역할이 흐려지고 테스트가 어려워진다.
- **"레거시 코드는 무조건 어댑터로 감싸야 한다"** — 레거시를 직접 쓰는 게 더 단순하다면 어댑터가 오히려 불필요한 간접층이 된다.
- **"DTO 변환 코드도 전부 어댑터 패턴인가요?"** — 단순 매핑 유틸리티일 수도 있다. 핵심은 "외부 인터페이스 불일치를 안정적으로 경계화하는가"다.
- **"ACL(안티 부패 계층) = 어댑터 하나인가요?"** — ACL은 여러 번역 규칙/검증/정책을 포함한 경계 설계다. 어댑터는 그 안에서 인터페이스 번역을 맡는 한 조각일 수 있다.

## 실무에서 쓰는 모습

**외부 결제 SDK 연결**: 결제 PG사마다 API 형태가 다를 때, 공통 `PaymentGateway` 인터페이스를 정의하고 각 PG 클라이언트를 어댑터로 감싼다. 서비스 코드는 `PaymentGateway`만 알고, PG가 바뀌어도 어댑터만 교체한다.

**레거시 DAO 연결**: 기존 `LegacyDao.getByPk(String)` 시그니처를 새 `Repository.findById(Long)` 인터페이스로 맞출 때 어댑터가 타입 변환을 담당한다.

### 호출부가 어떻게 단순해지는가

```java
// 서비스는 항상 PaymentGateway만 안다.
PaymentGateway gateway = new LegacyPgAdapter(legacyPgClient);
gateway.pay(12_000);
```

서비스는 외부 SDK의 메서드 이름이나 단위 체계를 몰라도 된다. SDK 교체가 생겨도 adapter 교체에 수정 범위를 묶을 수 있다.

## 다음 학습 경로 (막히는 지점별)

- adapter 기본 틀은 이해했고 객체/클래스 adapter 차이가 궁금하면: [Adapter (어댑터) — 심화](./adapter.md)
- wrapper 패턴끼리 계속 헷갈리면: [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
- 번역층이 너무 길어져 책임이 흐려지면: [Adapter Chaining Smells](./adapter-chaining-smells.md)

## Quick-Check

아래 3개가 빠르게 갈리면 beginner 첫 읽기는 충분하다.

| 질문 | `예`면 가까운 쪽 | `아니오`면 먼저 볼 것 |
|---|---|---|
| 외부 인터페이스를 우리 표준 인터페이스로 번역해야 하는가? | `Adapter` | 직접 호출 또는 단순 사용 |
| 복잡한 여러 호출을 한 창구로만 감싸려는가? | `Facade` | `Adapter`가 아닐 수 있음 |
| 같은 인터페이스에 기능을 덧붙이려는가? | `Decorator` | 번역 책임과 다름 |

## 면접/시니어 질문 미리보기

> Q: 어댑터와 데코레이터가 구조는 비슷한데 어떻게 다른가?
> 의도: 패턴의 의도를 구조와 분리해 설명할 수 있는지 확인한다.
> 핵심: 어댑터는 인터페이스 불일치 해소, 데코레이터는 같은 인터페이스에서 기능 추가다.

> Q: 어댑터 안에 비즈니스 로직이 들어가면 어떤 문제가 생기는가?
> 의도: 단일 책임 원칙과 어댑터 역할 경계를 아는지 확인한다.
> 핵심: 번역만 해야 하는 어댑터에 로직이 쌓이면 테스트와 유지보수가 어려워진다.

> Q: PG사가 하나 더 생길 때 어댑터 패턴이 어떻게 도움이 되는가?
> 의도: 확장-변경 분리를 설명하는지 확인한다.
> 핵심: 기존 서비스 코드를 바꾸지 않고 새 어댑터 구현체만 추가하면 된다.

## Confusion Box

| 헷갈리는 쌍 | 먼저 던질 질문 | 빠른 기준 |
|---|---|---|
| Adapter vs Facade | "형태를 맞추는가, 사용 순서를 단순화하는가?" | 번역이면 `Adapter`, 단순 창구면 `Facade` |
| Adapter vs Decorator | "인터페이스가 다른가, 같은가?" | 다르면 `Adapter`, 같고 기능 추가면 `Decorator` |
| Adapter vs Mapper | "외부 경계를 가리고 인터페이스를 고정하는가?" | 경계 번역이면 `Adapter`, 값 복사만 하면 mapper/helper에 가깝다 |

## 3문항 미니 오해 점검

짧게 구분해 본다. wrapper처럼 보여도 역할이 다르면 다른 패턴이다.

| 문항 | 헷갈리는 포인트 | 한 줄 정답 기준 |
|---|---|---|
| 1 | Adapter vs Facade | Adapter는 인터페이스를 맞추고, Facade는 사용법을 단순화한다 |
| 2 | Adapter vs Decorator | Adapter는 번역이 핵심이고, Decorator는 같은 인터페이스 위에 기능을 덧붙인다 |
| 3 | Adapter vs 단순 Mapper/Helper | 외부 인터페이스 불일치를 경계화하지 않으면 그냥 변환 유틸일 수 있다 |

### Q1. 여러 하위 서비스를 `orderFacade.placeOrder()` 하나로 묶었다. 이건 Adapter인가?

- 정답: 보통 Facade다.
- 왜: 인터페이스 번역보다 "복잡한 사용 순서를 단순 창구 하나로 감쌌다"는 점이 중심이기 때문이다.
- 같이 보면 좋은 문서: [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)

### Q2. 외부 PG의 `charge(double dollar)`를 우리 `pay(int won)`로 바꿨다. 이건 Facade인가?

- 정답: 아니다. Adapter에 가깝다.
- 왜: 메서드 이름, 타입, 단위를 우리 표준 인터페이스에 맞게 번역하고 있기 때문이다.
- 기억법: "호환되게 바꾼다"가 보이면 Adapter 쪽이다.

### Q3. 응답 DTO를 다른 DTO로 복사하는 코드도 전부 Adapter인가?

- 정답: 꼭 그렇지 않다.
- 왜: 단순 데이터 매핑일 수도 있다. 어댑터라고 부르려면 외부 인터페이스 차이를 안정적으로 가리고, 서비스가 Target 인터페이스만 보게 만드는 경계 역할이 있어야 한다.
- 체크 질문: "이 코드가 인터페이스 불일치를 해결하는가, 아니면 값만 옮기는가?"

## 한 줄 정리

어댑터는 인터페이스가 맞지 않는 두 코드 사이에서 번역만 담당하는 변환기로, 기존 코드를 바꾸지 않고 외부 코드를 내 인터페이스에 맞춰 연결할 때 쓴다.
