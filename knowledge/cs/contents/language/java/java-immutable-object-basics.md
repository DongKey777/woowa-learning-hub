# 불변 객체와 방어적 복사 입문

> 한 줄 요약: 불변 객체는 생성 후 상태가 바뀌지 않는 객체이고, 방어적 복사는 외부에서 넘어온 가변 객체가 내부를 몰래 바꾸는 것을 막는 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [record-serialization-evolution](./record-serialization-evolution.md)
- [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)
- [language 카테고리 인덱스](../README.md)
- [database README](../../database/README.md)

retrieval-anchor-keywords: immutable object java beginner, 불변 객체 입문, defensive copy basics, 방어적 복사 입문, final field basics, java string immutable why, value object basics, mutable vs immutable java, 가변 불변 차이 java, java immutable class design, 불변 클래스 만드는 법, shallow copy deep copy immutable

## 핵심 개념

불변(immutable) 객체는 한번 만들어지면 내부 상태가 절대 바뀌지 않는 객체다. Java의 `String`이 대표적이다. `"hello".toUpperCase()`는 기존 문자열을 바꾸지 않고 새 문자열 `"HELLO"`를 반환한다.

입문자가 헷갈리는 이유는 `final` 키워드와 불변을 동일시하기 때문이다. `final` 필드는 참조 자체를 바꾸지 못할 뿐이고, 그 참조가 가리키는 객체 내부는 여전히 바뀔 수 있다.

## 한눈에 보기

```
가변 객체 (mutable)          불변 객체 (immutable)
┌────────────┐              ┌────────────┐
│ name: "홍" │  → 변경 가능  │ name: "홍" │  → 변경 불가
└────────────┘              └────────────┘
   .setName("김") 가능          setter 없음, final 필드
```

- **가변**: `ArrayList`, 일반 `Person` 클래스 등
- **불변**: `String`, `Integer`, `LocalDate`, `record` 등

## 상세 분해

### 불변 클래스 만드는 네 가지 조건

1. 클래스를 `final`로 선언해 상속 차단
2. 모든 필드를 `private final`로 선언
3. setter를 제공하지 않음
4. 생성자에서 가변 객체를 받으면 **방어적 복사**로 저장

```java
public final class Period {
    private final Date start;
    private final Date end;

    public Period(Date start, Date end) {
        // 방어적 복사: 외부 Date가 나중에 바뀌어도 내부는 안전
        this.start = new Date(start.getTime());
        this.end   = new Date(end.getTime());
    }

    public Date getStart() {
        return new Date(start.getTime()); // 반환 시에도 방어적 복사
    }
}
```

### 왜 방어적 복사가 필요한가

```java
Date d = new Date();
Period p = new Period(d, d);
d.setTime(0); // 이 시점에서 p 내부가 바뀔 수 있음 (방어적 복사 없으면)
```

외부에서 넘긴 `Date`를 그대로 저장하면, 외부 코드가 나중에 그 `Date`를 수정할 때 `Period`의 불변성이 깨진다.

## 흔한 오해와 함정

**오해 1: `final` 변수 = 불변 객체**
`final List<String> list = new ArrayList<>()` 에서 `list`가 가리키는 참조는 못 바꾸지만, `list.add("항목")`은 여전히 된다. 참조 고정과 객체 불변은 다르다.

**오해 2: 불변이면 항상 느리다**
불변 객체는 복사 비용이 있지만, 공유 안전성(스레드 간 락 불필요), 캐싱 가능성으로 상쇄되는 경우가 많다. `String`의 `intern()` 풀이 그 예다.

**오해 3: getter를 제공하면 불변이 깨진다**
기본 타입이나 `String` 같은 불변 타입을 반환하면 안전하다. 가변 타입(`Date`, `List` 등)을 반환할 때만 방어적 복사가 필요하다.

## 실무에서 쓰는 모습

도메인 설계에서 `Money`, `Address`, `Period` 같은 값 객체를 불변으로 만드는 것이 흔하다.

1. `Money(amount, currency)`를 불변으로 만들면 두 코드가 같은 객체를 공유해도 한쪽이 금액을 바꿀 수 없음
2. Java 14+의 `record`는 불변 값 객체를 위한 간결한 문법을 제공함: `record Money(int amount, String currency) {}`
3. Spring의 `@Value` 빈이나 JPA `@Embeddable` 값 타입에도 불변 설계가 어울린다

## 더 깊이 가려면

- record 직렬화와 진화 패턴은 [record-serialization-evolution](./record-serialization-evolution.md)
- JPA Entity와 값 타입 분리는 [database README](../../database/README.md)

## 면접/시니어 질문 미리보기

**Q. String은 왜 불변으로 만들었나?**
String 풀(intern)로 공유가 가능하고, 해시코드 캐싱, 보안(네트워크 파라미터 변조 방지), 스레드 안전성이 주요 이유다.

**Q. 방어적 복사를 생성자에서도 하고 getter에서도 하는 이유는?**
생성자에서는 외부가 나중에 넘긴 객체를 바꾸는 것을 막고, getter에서는 내부 객체를 반환받은 쪽이 수정하는 것을 막는다. 두 방향 모두 막아야 진짜 불변이다.

**Q. `Collections.unmodifiableList()`를 쓰면 불변 리스트가 되나?**
뷰만 불변이다. 원본 리스트를 수정하면 뷰를 통해서도 변경이 보인다. 진짜 불변이 필요하면 `List.copyOf()`나 `List.of()`를 써야 한다.

## 한 줄 정리

불변 객체는 생성 후 상태가 변하지 않으며, 가변 객체를 다룰 때 방어적 복사로 외부 수정을 차단해야 진짜 불변이 보장된다.
