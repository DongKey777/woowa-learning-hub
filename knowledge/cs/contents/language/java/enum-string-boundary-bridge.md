# DTO boundary에서 문자열/코드값을 enum으로 넘기는 위치부터 잡기

> 한 줄 요약: controller/DTO boundary에서는 `"PAID"`뿐 아니라 `"P"`, `"01"` 같은 외부 코드값도 enum으로 해석하고, domain 내부에서는 해석이 끝난 enum만 다루는 식으로 역할을 나누면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java enum 기초](./java-enum-basics.md)
- [Enum equality quick bridge](./enum-equality-quick-bridge.md)
- [Java String 기초](./java-string-basics.md)
- [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
- [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
- [객체지향 설계 기초](../../software-engineering/oop-design-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: dto enum boundary beginner, controller dto domain enum handoff, enum string bridge, enum code value boundary, java dto string to enum, java code to enum mapping, external code value enum primer, enum vs string compare, enum 문자열 비교 헷갈, status string payload, p 01 enum mapping beginner, dto에서 enum 변환 언제, 처음 enum boundary, what is enum boundary, valueof 왜 실패해요

## 핵심 개념

처음 enum을 배우면 `status == OrderStatus.PAID`가 자연스럽게 보인다.  
그다음 controller DTO에서 `"PAID"` 문자열을 만나면, 초급자는 "이걸 어디서 enum으로 바꿔야 하지?"에서 막히기 쉽다.

실무 쪽으로 한 걸음만 가도 입력이 enum 이름 그대로 오지 않을 때가 더 많다.

- `"PAID"` 대신 `"P"`
- `"READY"` 대신 `"01"`
- `"CANCELLED"` 대신 `"CN"`

이때 핵심 질문은 같다.

- `OrderStatus.PAID`는 이미 domain 안으로 들어온 enum 값이다
- `"PAID"`, `"P"`, `"01"`은 아직 controller/DTO boundary에 있는 외부 표현이다

짧게 말하면 **enum 비교와 문자열/코드값 해석은 같은 작업이 아니다.**

## 한눈에 보기

| 지금 손에 든 값 | 바로 해도 되는 것 | 먼저 하면 안 되는 것 |
|---|---|---|
| `OrderStatus status` | `status == OrderStatus.PAID` | 굳이 `status.name()`으로 문자열 비교하기 |
| `String rawStatus` | DTO/controller boundary에서 enum으로 변환 시도하기 | `rawStatus == "PAID"` 뒤에 enum처럼 믿기 |
| `String rawCode`가 `"P"`, `"01"` 같은 외부 코드다 | 코드값을 enum으로 매핑하는 해석 단계 두기 | domain 메서드가 `"P"` 같은 문자열을 직접 받기 |
| `String rawStatus`가 `null`/빈 문자열일 수도 있음 | null/blank/unknown 정책 먼저 정하기 | 바로 `Enum.valueOf(...)` 호출하기 |

핵심 기준은 이것 하나다.

> 외부에서 들어온 문자열이나 코드값은 "상태처럼 보이는 텍스트"일 뿐이고, enum으로 변환되기 전까지는 진짜 상태값이 아니다.

한 줄로 더 줄이면 이렇다.

- DTO는 아직 "문자열/코드값을 들고 있는 상자"다
- domain 메서드는 가능하면 "이미 enum인 값"만 받게 한다

## 왜 `==` 비교와 코드값 비교를 섞으면 헷갈릴까

enum 비교 문서는 보통 이렇게 배운다.

```java
if (status == OrderStatus.PAID) {
    ship();
}
```

이 코드는 `status`가 이미 `OrderStatus` 타입이기 때문에 맞다.

그런데 controller, DTO, query parameter에서는 보통 처음 값이 문자열이나 코드값으로 들어온다.

```java
String rawStatus = "PAID";
String rawCode = "P";
```

이 순간에는 아직 "상태 판별"보다 "이 텍스트를 enum으로 받아들여도 되는가"가 먼저다.  
즉 비교 전에 boundary 해석 단계가 하나 더 있다.

특히 `"P"`나 `"01"`은 `Enum.valueOf()`로 바로 올릴 수도 없다.  
이 값들은 enum 이름이 아니라 **외부 시스템이 정한 코드값**이기 때문이다.

## 안전한 흐름: DTO 문자열/코드값 -> enum 변환 -> domain enum 비교

초급자는 아래 3단계 흐름으로 고정해 두면 실수가 줄어든다.

1. DTO가 외부 문자열이나 코드값을 받는다
2. boundary에서 허용된 enum 값인지 확인하며 변환한다
3. domain은 변환이 끝난 enum끼리 `==`로 비교한다

enum 이름이 그대로 오는 경우 예시는 이렇게 읽으면 된다.

```java
OrderRequest request = new OrderRequest("PAID");
OrderStatus status = OrderStatus.valueOf(request.status());

if (status == OrderStatus.PAID) {
    ship();
}
```

여기서 중요한 포인트는 `valueOf(...)`가 비교를 대신하는 것이 아니라,  
**비교할 수 있는 타입으로 올려 주는 입구**라는 점이다.

코드값이 들어오는 경우에는 `valueOf(...)` 대신 "코드값 해석기"가 하나 더 필요하다.

```java
enum PaymentStatus {
    PENDING("P"),
    COMPLETED("C");

    private final String code;

    PaymentStatus(String code) {
        this.code = code;
    }

    static PaymentStatus fromCode(String rawCode) {
        for (PaymentStatus status : values()) {
            if (status.code.equals(rawCode)) {
                return status;
            }
        }
        throw new IllegalArgumentException("지원하지 않는 결제 코드: " + rawCode);
    }
}

record PaymentRequest(String statusCode) {
    PaymentStatus toPaymentStatus() {
        return PaymentStatus.fromCode(statusCode);
    }
}
```

여기서 `"P"`는 domain의 본질이 아니라 **바깥 세계와 대화하기 위한 번역 키**다.  
그래서 `"P"`를 domain 메서드 파라미터로 오래 들고 들어가기보다, boundary에서 `PaymentStatus.PENDING`으로 올리는 편이 안전하다.

## 어디서 변환할까: controller, DTO, domain 책임표

정답은 "항상 한 클래스"가 아니다. beginner 단계에서는 **domain에 raw string/code를 오래 들고 들어가지 않는 방향**만 고정하면 충분하다.

| 위치 | 두어도 되는 책임 | 두지 않는 편이 좋은 책임 |
|---|---|---|
| controller | 요청을 받고 변환 실패를 400 같은 입력 오류로 연결 | 상태 전이 규칙까지 직접 판단 |
| DTO | raw string/code를 잠깐 보관, 필요하면 간단한 `toEnum()` 제공 | 여러 domain 규칙을 안쪽에 품기 |
| domain service / entity | enum끼리 비교, 상태 전이, 정책 판단 | `"PAID"`나 `"P"` 같은 raw input parsing |

처음에는 아래 기준으로만 기억하면 된다.

- "외부 입력을 읽는 쪽"에서 문자열이나 코드값을 enum으로 바꾼다
- "비즈니스 규칙을 판단하는 쪽"에서는 enum만 받는다

## enum 이름과 외부 코드값은 왜 따로 봐야 할까

처음에는 `"P"`도 그냥 enum 상수 이름을 줄여 쓴 것처럼 보일 수 있다.  
하지만 실제로는 역할이 다르다.

| 구분 | 예시 | 누가 정하나 | 바뀌면 어디가 흔들리나 |
|---|---|---|---|
| enum 이름 | `PENDING`, `COMPLETED` | 우리 코드 | 내부 switch, 비교식, 리팩터링 |
| 외부 코드값 | `"P"`, `"C"`, `"01"` | API/DB/협력 시스템 계약 | DTO 역직렬화, 저장 포맷, 외부 연동 |

초급자 기준 핵심은 이것이다.

> enum 이름은 내부 모델이고, 코드값은 boundary 계약이다.

그래서 domain 메서드를 아래처럼 만들면 boundary 계약이 안쪽으로 새기 시작한다.

```java
void approve(String statusCode) { ... }
```

초기에는 편해 보여도 곧 이런 질문이 붙는다.

- `"P"`와 `"01"`이 같은 뜻인가?
- 소문자 `"p"`는 허용할까?
- 코드 체계가 바뀌면 domain 메서드를 다 바꿔야 하나?

이 질문들은 비즈니스 규칙보다 입력 해석 규칙에 가깝다.  
즉 domain 메서드 시그니처보다 boundary mapper 쪽 질문이다.

## 자주 나오는 실수 5가지

| 실수 | 왜 문제인가 | beginner 기본 교정 |
|---|---|---|
| `rawStatus == "PAID"` | 문자열 비교 규칙부터 잘못 잡을 수 있다 | 문자열 단계에서는 validation/변환을 먼저 본다 |
| `"PAID".equals(status)` | 왼쪽은 문자열, 오른쪽은 enum이라 질문 자체가 어긋난다 | 타입을 맞춘 뒤 비교한다 |
| `status.name().equals("PAID")`를 기본 패턴으로 굳힌다 | 매번 enum을 다시 문자열로 내려 boundary를 흐린다 | 내부에서는 enum끼리 비교한다 |
| `Enum.valueOf(rawStatus)`를 바로 호출한다 | `null`, 빈 문자열, 소문자, 오타에서 바로 실패한다 | boundary 정책을 먼저 둔다 |
| domain 메서드가 `"P"`나 `"01"`을 직접 받는다 | 외부 계약이 domain 시그니처에 새어 들어온다 | boundary에서 `fromCode(...)`로 끊는다 |

특히 `status.name().equals("PAID")`는 "되긴 되는 코드"라서 더 자주 남는다.  
하지만 내부 enum을 다시 문자열로 내려 비교하기 시작하면, 코드가 enum의 장점을 스스로 지우게 된다.

## boundary에서 먼저 정할 정책

문자열 payload와 코드값은 enum 상수와 달리 흔들릴 수 있다.

| 들어온 값 | 먼저 물어볼 질문 |
|---|---|
| `null` | 필드 누락인가, 값 제거 의도인가 |
| `""` 또는 `"   "` | invalid input인가, 빈 값 허용인가 |
| `"paid"` | 대소문자 보정을 허용할 것인가 |
| `"P"` | 축약 코드 체계가 고정돼 있는가 |
| `"01"` | 숫자가 아니라 코드로 봐야 하는가 |
| `"DONEE"` | 오타를 400으로 돌릴 것인가, fallback을 둘 것인가 |

즉 beginner 기준 첫 감각은 이렇다.

- 내부 도메인에서는 enum이 규칙을 준다
- boundary에서는 문자열/코드값 해석 정책이 규칙을 준다

이 둘을 한 줄 비교식으로 뭉개지 않는 편이 안전하다.

## `Enum.valueOf()`가 자주 실패하는 경우

처음에는 `Enum.valueOf(OrderStatus.class, rawStatus)`가 "문자열을 enum으로 바꾸는 기본 도구"처럼 보인다.  
맞지만, **입력이 enum 이름과 정확히 같을 때만** 성공한다.

작게 외우면 이렇게 정리할 수 있다.

| 들어온 payload | `Enum.valueOf()` 바로 호출 결과 | beginner 첫 대응 |
|---|---|---|
| `null` | `NullPointerException` | null 허용 여부를 먼저 정하고, 보통은 validation 에러로 돌린다 |
| `""`, `"   "` | `IllegalArgumentException` | `trim()` 후 비었는지 먼저 검사한다 |
| `"paid"` | `IllegalArgumentException` | 대소문자 보정을 허용할지 정책을 정한 뒤, 허용하면 `toUpperCase(Locale.ROOT)` 후 변환한다 |
| `"DONEE"` 같은 unknown 값 | `IllegalArgumentException` | 오타/미지원 값으로 보고 400 에러 또는 fallback 정책을 둔다 |
| `"PAID"`처럼 정확히 일치 | 성공 | 변환 뒤 enum끼리 `==` 비교한다 |
| `"P"`, `"01"` 같은 코드값 | 보통 실패 | `valueOf()` 대신 `fromCode()` 같은 명시적 매핑을 둔다 |

핵심은 "`valueOf()`가 알아서 친절하게 맞춰 주겠지"라고 기대하지 않는 것이다.  
`valueOf()`는 parser라기보다 **정확히 맞는 enum 이름만 받는 lookup**에 가깝다.

## 코드값이 들어올 때의 최소 결정표

처음에는 모든 edge case를 한 번에 일반화하려 하기보다, 아래 표처럼 "무엇을 먼저 볼지"만 고정해 두면 충분하다.

| 지금 받은 값 | 먼저 할 질문 | 첫 선택 |
|---|---|---|
| `"PAID"` | enum 이름과 정확히 같은가 | 필요하면 `valueOf()` 후보 |
| `"P"` | 이 시스템만의 축약 코드인가 | `fromCode()` 같은 명시적 매핑 |
| `"01"` | 숫자처럼 보여도 의미 코드인가 | 숫자 계산 말고 코드 매핑으로 해석 |
| `"paid"` | 표현만 다른가 | 정규화 정책 후 매핑 |

`"01"`이 들어왔다고 해서 `1`로 바꿔도 된다는 뜻은 아니다.  
이 값은 "숫자"가 아니라 "코드"일 수 있다. leading zero까지 의미일 수 있으니, 우선 문자열 코드로 본 뒤 mapping 정책을 정하는 편이 안전하다.

## DTO에서 domain으로 넘기는 가장 단순한 handoff

controller나 DTO boundary에서는 문자열이나 코드값을 enum으로 바꾸는 책임이 있고,  
domain 로직에서는 enum 비교와 상태 전이가 중심이 된다.

```java
enum OrderStatus {
    READY("01"),
    PAID("02"),
    CANCELLED("99");

    private final String code;

    OrderStatus(String code) {
        this.code = code;
    }

    static OrderStatus fromCode(String rawCode) {
        for (OrderStatus status : values()) {
            if (status.code.equals(rawCode)) {
                return status;
            }
        }
        throw new IllegalArgumentException("지원하지 않는 status code입니다: " + rawCode);
    }
}

record OrderRequest(String statusCode) {
    OrderStatus toOrderStatus() {
        if (statusCode == null || statusCode.isBlank()) {
            throw new IllegalArgumentException("statusCode가 비어 있습니다.");
        }
        return OrderStatus.fromCode(statusCode.trim());
    }
}

void handle(OrderRequest request) {
    OrderStatus status = request.toOrderStatus();
    if (status == OrderStatus.PAID) {
        ship();
    }
}
```

이 코드의 핵심은 `"01"`이나 `"02"`를 계속 들고 다니지 않는 handoff 지점이다.

- `OrderRequest`: 외부 코드값을 어떻게 받아들일지 결정
- `handle(...)` 이후: 변환이 끝난 enum으로 상태를 읽음

여기서 더 중요한 것은 "DTO에 꼭 `toOrderStatus()` 메서드를 넣어라"가 아니다.  
프로젝트에 따라 controller mapper나 별도 assembler가 변환을 맡아도 된다. 초급자 기준 핵심은 **domain 메서드가 `String statusCode` 대신 `OrderStatus status`를 받도록 끊는 것**이다.

## beginner용 빠른 결정표

| 지금 고민 | 첫 선택 |
|---|---|
| 요청 JSON/파라미터에서 `"PAID"`가 들어온다 | boundary에서 enum으로 바꾼다 |
| 요청 JSON/파라미터에서 `"P"`나 `"01"`이 들어온다 | boundary에서 `fromCode()` 같은 명시적 매핑을 둔다 |
| domain 메서드 파라미터를 뭘로 받을지 고민된다 | 가능하면 `OrderStatus` 같은 enum을 받는다 |
| 변환 실패를 어디서 설명할지 고민된다 | controller 가까운 곳에서 입력 오류로 다룬다 |
| enum 이름 외 별칭, 코드값, 직렬화 포맷까지 섞인다 | 내부 enum 이름과 외부 code 필드를 분리해 둔다 |

## 흔한 오해

- "`enum`은 결국 이름 문자열이니까 그냥 문자열 비교해도 된다"
  아니다. enum은 문자열과 다르게 허용된 값 집합을 타입으로 고정한다.
- "DTO가 있으니 domain도 `String status`를 받아도 된다"
  아니다. DTO가 string을 들고 들어오는 것과, domain이 string에 의존하는 것은 다른 문제다.
- "`valueOf()`만 호출하면 boundary 문제는 끝난다"
  아니다. `null`, blank, unknown value 정책은 여전히 남고, `"P"`/`"01"` 같은 코드값은 `valueOf()` 대상도 아닐 수 있다.
- "내부에서도 `name()`으로 비교하면 더 단순하다"
  단순해 보이지만 enum 타입 안전성을 버리고 문자열 의존을 다시 늘린다.
- "문자열 payload가 있으니 enum은 쓸모없다"
  오히려 반대다. 외부 문자열을 내부 enum으로 올리는 순간부터 잘못된 상태값을 줄일 수 있다.
- "코드값이 짧으니 domain에서도 그냥 `String`으로 두는 편이 낫다"
  짧은 것과 안정적인 것은 다르다. `"P"`의 의미를 아는 곳은 boundary mapper여야지, 모든 domain 메서드가 아니어야 한다.

## 다음 한 칸

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`==`와 `equals()`를 enum에서 왜 다르게 보지 않아도 되지?" | [Enum equality quick bridge](./enum-equality-quick-bridge.md) |
| "enum 자체를 아직 처음 배우는 중이다" | [Java enum 기초](./java-enum-basics.md) |
| "`P`, `01` 같은 코드값이 외부 계약으로 굳는 문제를 더 보고 싶다" | [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md) |
| "문자열 payload의 `null`/missing/unknown도 같이 헷갈린다" | [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md) |
| "문자열을 value object나 더 명시적인 boundary 타입으로 올리고 싶다" | [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md) |
| "상태 비교 다음에 상태 전이 규칙까지 묶고 싶다" | [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md) |

## 한 줄 정리

DTO boundary에서는 `"PAID"`뿐 아니라 `"P"`, `"01"` 같은 외부 코드값도 enum으로 해석하고, domain 내부에서는 해석이 끝난 enum만 받게 두면 boundary 계약이 domain 안으로 새지 않는다.
