# 어댑터 패턴 기초 (Adapter Pattern Basics)

> 한 줄 요약: 어댑터는 서로 맞지 않는 인터페이스를 중간에서 번역해주는 변환기로, 기존 코드를 바꾸지 않고 외부 라이브러리나 레거시 API를 연결할 때 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Adapter (어댑터) — 심화](./adapter.md)
- [Adapter Chaining Smells](./adapter-chaining-smells.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [소프트웨어 공학 카테고리 인덱스](../software-engineering/README.md)

retrieval-anchor-keywords: adapter pattern basics, 어댑터 패턴, adapter pattern beginner, 인터페이스 변환, legacy api adapter, 외부 라이브러리 연결, adapter vs wrapper, 어댑터가 뭔가요, interface translation, incompatible interface, 기존 코드 바꾸지 않고, object adapter class adapter, adapter pattern example

---

## 핵심 개념

어댑터 패턴은 "내가 원하는 인터페이스"와 "외부 코드가 제공하는 인터페이스"가 맞지 않을 때 중간에서 번역하는 역할을 한다. 여행용 전기 플러그 변환 어댑터와 같다고 생각하면 된다.

입문자가 자주 막히는 부분은 "번역이 필요하지 않으면 어댑터가 필요 없다"는 점이다. 인터페이스가 이미 맞는다면 어댑터를 만들 필요가 없고, 그냥 바로 쓰면 된다.

## 한눈에 보기

```
Client → Target 인터페이스 → Adapter → Adaptee (외부/레거시)
```

| 역할 | 설명 |
|------|------|
| Target | 클라이언트가 기대하는 인터페이스 |
| Adaptee | 맞지 않는 외부/레거시 클래스 |
| Adapter | Target을 구현하면서 Adaptee를 내부에서 호출 |

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

## 실무에서 쓰는 모습

**외부 결제 SDK 연결**: 결제 PG사마다 API 형태가 다를 때, 공통 `PaymentGateway` 인터페이스를 정의하고 각 PG 클라이언트를 어댑터로 감싼다. 서비스 코드는 `PaymentGateway`만 알고, PG가 바뀌어도 어댑터만 교체한다.

**레거시 DAO 연결**: 기존 `LegacyDao.getByPk(String)` 시그니처를 새 `Repository.findById(Long)` 인터페이스로 맞출 때 어댑터가 타입 변환을 담당한다.

## 더 깊이 가려면

- [Adapter (어댑터) — 심화](./adapter.md) — 객체 어댑터 vs 클래스 어댑터, 양방향 어댑터, 안티 부패 계층과의 관계
- [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md) — 세 래퍼 패턴을 의도 기준으로 비교

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

## 한 줄 정리

어댑터는 인터페이스가 맞지 않는 두 코드 사이에서 번역만 담당하는 변환기로, 기존 코드를 바꾸지 않고 외부 코드를 내 인터페이스에 맞춰 연결할 때 쓴다.
