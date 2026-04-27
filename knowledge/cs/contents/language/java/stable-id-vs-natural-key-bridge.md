# Stable ID vs Natural Key Bridge

> 한 줄 요약: `Map` key는 "사람이 자주 보는 값"보다 "시간이 지나도 같은 대상을 계속 가리키는 값"이 더 안전하며, 초보자 기본값은 보통 immutable surrogate ID이고, business key는 불변성·유일성·정규화 정책이 분명할 때만 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [Locale.ROOT, Unicode Normalization, and String Canonicalization](./locale-root-case-mapping-unicode-normalization.md)

retrieval-anchor-keywords: language-java-00143, stable id vs natural key bridge, surrogate id vs business key java, natural key map key beginner, business key map key beginner, email as map key java, code as map key java, name as map key java, immutable surrogate id hashmap, business key canonicalization java, stable identifier vs natural key, java map key email change risk, java map key product code safe, java map key display name unsafe, java beginner id vs business key, map key uniqueness immutability normalization, value object key entity value java, 자바 surrogate id natural key, 자바 비즈니스 키 map key, 자바 이메일 key 안전한가, 자바 코드 key 안전한가, 자바 이름 key 위험, 자바 불변 id business key 비교, 자바 map key 기준 기초

## 먼저 잡을 멘탈 모델

초보자에게는 이 질문 하나가 가장 중요하다.

> 이 값이 다음 달에도 같은 대상을 같은 규칙으로 가리킬까?

`Map` key는 "보기 좋은 라벨"이 아니라 "찾는 기준"이다.

- 이름표처럼 자주 바뀌는 값은 보통 `value`
- 신분증 번호처럼 오래 유지되는 값은 `key`

그래서 기본값은 보통 아래 둘 중 하나다.

- `Map<MemberId, Member>`: surrogate ID를 key로 둔다
- `Map<ProductCode, Product>`: business key가 정말 안정적이면 그 값을 key로 둔다

## 용어를 아주 짧게 정리

| 용어 | 초보자용 뜻 | 대표 예시 |
|---|---|---|
| surrogate ID | 시스템이 붙인 식별자 | DB PK, `MemberId(1L)` |
| natural key / business key | 도메인 자체가 이미 가진 식별 기준 | 상품 코드, 국가 코드, 사번 |
| display field | 사람에게 보여 주는 값 | 이름, 별명, 화면 표시용 제목 |

핵심 차이는 "사람이 이해하기 쉬운가"가 아니라 "정말 안 바뀌는가"다.

## 가장 안전한 beginner 기본값

초보자는 먼저 이렇게 기억하면 된다.

| 상황 | 먼저 떠올릴 key | 이유 |
|---|---|---|
| 회원, 주문, 게시글처럼 lifecycle이 긴 entity | surrogate ID | 이름, 이메일, 상태가 바뀌기 쉽다 |
| 표준 코드, 발급 코드처럼 규칙상 고정된 값 | business key 가능 | 이미 도메인 식별자 역할을 한다 |
| 화면 표시 이름, 제목, 별명 | key로 피함 | 중복과 변경 가능성이 높다 |

즉 "자연스러워 보이는 값"보다 "정책상 안정적인 값"이 key에 더 중요하다.

## surrogate ID가 왜 기본값이 되기 쉬운가

surrogate ID의 장점은 판단 기준이 단순하다는 데 있다.

- 보통 생성 후 바뀌지 않는다
- 유일성 정책이 분명하다
- 표시값 변경과 조회 규칙을 분리하기 쉽다

```java
import java.util.HashMap;
import java.util.Map;

record MemberId(long value) {}

final class Member {
    private final MemberId id;
    private String email;
    private String name;

    Member(MemberId id, String email, String name) {
        this.id = id;
        this.email = email;
        this.name = name;
    }

    MemberId id() {
        return id;
    }

    void changeEmail(String email) {
        this.email = email;
    }

    void changeName(String name) {
        this.name = name;
    }
}

Map<MemberId, Member> membersById = new HashMap<>();
Member member = new Member(new MemberId(1L), "mina@example.com", "Mina");

membersById.put(member.id(), member);
member.changeEmail("momo@example.com");
member.changeName("Momo");
```

이 구조에서는 이메일과 이름이 바뀌어도 조회 기준은 흔들리지 않는다.

## business key는 언제 안전한가

business key도 충분히 좋은 key가 될 수 있다.
다만 아래 조건을 같이 만족하는지 먼저 봐야 한다.

| 질문 | `Yes`면 더 안전 | `No`면 더 위험 |
|---|---|---|
| 생성 후 바뀌지 않는가? | key 후보 가능 | surrogate ID 쪽이 안전 |
| 중복 없이 유일한가? | key 후보 가능 | 조회 충돌 위험 |
| 비교 전에 정규화 규칙이 분명한가? | key 후보 가능 | `"A-01"` vs `"a-01"` 혼란 |
| 조직/서비스 전체에서 같은 의미로 쓰는가? | key 후보 가능 | 경계마다 다른 값일 수 있음 |

대표적으로 이런 값은 business key로 안전할 가능성이 높다.

- 발급 후 변경하지 않는 상품 코드
- 규격이 고정된 국가 코드
- 회사 정책상 재사용되지 않는 사번

```java
import java.util.HashMap;
import java.util.Map;

record ProductCode(String value) {}

final class Product {
    private final ProductCode code;
    private String displayName;

    Product(ProductCode code, String displayName) {
        this.code = code;
        this.displayName = displayName;
    }

    ProductCode code() {
        return code;
    }

    void rename(String displayName) {
        this.displayName = displayName;
    }
}

Map<ProductCode, Product> productsByCode = new HashMap<>();
productsByCode.put(new ProductCode("SKU-2026-001"), new Product(new ProductCode("SKU-2026-001"), "Mug"));
```

여기서 `displayName`은 바뀌어도 되지만 `ProductCode` 정책은 흔들리면 안 된다.

## 이메일, 코드, 이름은 언제 safe map key인가

초보자가 가장 많이 묻는 세 값만 따로 보면 이렇게 정리할 수 있다.

| 값 | 기본 판단 | 이유 |
|---|---|---|
| 이메일 | 보통 신중 또는 비추천 | 변경 가능, 대소문자/정규화 정책 이슈 |
| 코드 | 조건부 추천 | 불변·유일 정책이 분명하면 좋다 |
| 이름 | 보통 비추천 | 중복 쉽고 표시값 성격이 강하다 |

### 1. 이메일

이메일은 얼핏 unique해 보여서 key로 쓰고 싶어진다.
하지만 beginner 기본값으로는 조심하는 편이 안전하다.

- 회원이 이메일을 변경할 수 있을 수 있다
- 대소문자, trim, alias 처리 등 canonicalization 정책이 필요할 수 있다
- 로그인 ID와 연락처 이메일이 같은 값이 아닐 수 있다

즉 "현재 이메일"은 자주 business attribute이지, 항상 stable identity는 아니다.

안전한 경우:

- 시스템 정책상 이메일이 가입 후 절대 바뀌지 않는다
- 비교 규칙이 명확하다
- 서비스 경계 전체에서 그 정책을 지킨다

그렇지 않다면 보통은 `MemberId`를 key로 두고 이메일은 value 안 필드로 둔다.

### 2. 코드

코드는 safe key가 되기 가장 쉬운 편이다.
단, "코드처럼 생겼다"와 "정말 안정적이다"는 다른 말이다.

안전한 경우:

- 상품 코드, 사번, 발급 번호가 생성 후 고정된다
- 같은 코드를 재사용하지 않는다
- `"sku-01"`과 `"SKU-01"`을 어떻게 다룰지 규칙이 있다

위 조건이 맞으면 `Map<ProductCode, Product>` 같은 구조는 초보자에게도 읽기 쉽다.

### 3. 이름

이름은 beginner 기본값으로 key에서 빼는 쪽이 거의 항상 낫다.

- 중복이 흔하다
- 변경될 수 있다
- 표기 규칙이 일정하지 않을 수 있다
- 대소문자, 공백, 현지화 문제도 있다

즉 이름은 보통 "찾는 기준"보다 "보여 주는 값"에 가깝다.

## 한 장 판단표

| 후보 값 | 유일성 | 변경 가능성 | 정규화 필요성 | beginner key 추천도 |
|---|---|---|---|---|
| `MemberId`, `OrderId` | 높음 | 낮음 | 낮음 | 높음 |
| `ProductCode`, `EmployeeNumber` | 보통 높음 | 정책에 따라 낮음 | 중간 | 중간~높음 |
| 이메일 | 상황 따라 다름 | 중간 | 높음 | 낮음~중간 |
| 이름, 별명, 제목 | 낮음 | 높음 | 중간 | 낮음 |

## "불변이면 무조건 safe key인가요?"에서 한 번 더 보기

불변은 중요하지만, 그것만으로 충분하지는 않다.

예를 들어 `String name`이 불변이어도 아래 문제는 남는다.

- 같은 이름이 여러 명일 수 있다
- "Mina"와 "mina"를 같은 사람으로 볼지 정책이 애매할 수 있다
- 이름 변경 요구가 들어오면 key 정책 전체가 흔들린다

즉 safe key는 보통 아래 네 가지를 같이 본다.

1. 불변성
2. 유일성
3. 정규화 규칙
4. 도메인 수명 동안의 안정성

## 초보자가 자주 하는 오해

- "이메일은 거의 안 바뀌니까 무조건 key로 써도 되지 않나요?"
  - "거의 안 바뀐다"와 "정책상 안 바뀐다"는 다르다.
- "name도 `String`이라 immutable인데 왜 안 되나요?"
  - `String`의 불변성과 도메인 값의 안정성은 다른 문제다.
- "business key가 더 자연스러우니 surrogate ID보다 항상 좋은 것 아닌가요?"
  - 읽기 쉬울 수는 있지만, 변경 정책이 불명확하면 오히려 위험하다.
- "surrogate ID는 DB 저장 후에야 생기니 저장 전에는 못 쓰나요?"
  - 그 시점에는 임시 key, 별도 생성 전략, 또는 business key 후보를 잠깐 쓸 수 있다. 다만 정책을 분리해서 생각해야 한다.

## 빠른 체크리스트

- 지금 key 후보가 "보여 주는 값"인가, "계속 같은 대상을 가리키는 값"인가?
- 이 값은 생성 후 바뀌지 않는가?
- 같은 값이 두 개 생기지 않는가?
- 대소문자/공백/포맷 정규화 규칙이 있는가?
- 헷갈리면 `Map<SurrogateId, Entity>`가 더 단순하지 않은가?

## 다음에 읽으면 좋은 문서

- stable ID 패턴 자체를 먼저 익히려면 [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
- record/value object 경계가 헷갈리면 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- 문자열 canonicalization 감각이 더 필요하면 [Locale.ROOT, Unicode Normalization, and String Canonicalization](./locale-root-case-mapping-unicode-normalization.md)
- `TreeMap`에서 business key와 `id` tie-breaker가 왜 갈리는지 보려면 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)

## 한 줄 정리

초보자 기본값은 "surrogate ID면 거의 안전, business key는 정책이 분명할 때만 안전, 이름은 보통 key로 쓰지 않기"라고 잡으면 `Map` key 선택 실수를 크게 줄일 수 있다.
