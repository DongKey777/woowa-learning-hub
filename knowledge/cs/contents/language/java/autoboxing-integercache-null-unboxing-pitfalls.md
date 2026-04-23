# Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls

> 한 줄 요약: wrapper type은 primitive처럼 보여도 identity, nullability, allocation, caching semantics가 다르다. autoboxing에 기대면 `==` 비교 버그, `NullPointerException`, hot path boxing overhead, `Map#get()` 함정이 조용히 들어온다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [Java Collections 성능 감각](./collections-performance.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
> - [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)

> retrieval-anchor-keywords: autoboxing, unboxing, IntegerCache, wrapper equality, `==`, null unboxing, boxing overhead, Map get null, Long cache, Boolean boxing, primitive specialization, OptionalInt, IntStream, primitive vs wrapper field, DTO boolean

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

autoboxing은 primitive와 wrapper 사이 변환을 자동으로 넣어준다.

- `int` -> `Integer`
- `long` -> `Long`
- `boolean` -> `Boolean`

문제는 문법이 비슷해 보여도 의미가 다르다는 점이다.

- primitive는 null이 없다
- wrapper는 객체다
- wrapper는 identity와 cache를 가진다
- unboxing은 숨겨진 메서드 호출과 NPE 가능성을 만든다

즉 autoboxing은 편의 기능이지 semantic noise remover가 아니다.

## 깊이 들어가기

### 1. `==`는 값 비교가 아니라 reference 비교다

wrapper에 `==`를 쓰면 primitive와 달리 객체 참조를 비교할 수 있다.  
여기에 `IntegerCache`가 섞이면 더 위험하다.

작은 값은 cache 덕분에 우연히 같아 보일 수 있다.

- 어떤 값은 `==`가 `true`
- 다른 값은 `false`

이 패턴은 테스트 데이터에선 지나가고 운영 데이터에서만 깨지기 쉽다.

### 2. unboxing NPE는 생각보다 흔하다

wrapper가 null일 수 있는데 primitive 문맥에 들어가면 자동 unboxing이 일어난다.

예:

- `if (flag)` where `flag` is `Boolean`
- `sum += map.get(key)` where value is `Integer`
- `long id = maybeNullLong`

문법은 간단하지만, 런타임에는 `NullPointerException`이 된다.

### 3. boxing은 allocation과 GC 압력을 만들 수 있다

hot loop, stream pipeline, collection 누적에서 wrapper boxing이 쌓이면  
성능 이슈는 알고리즘보다 allocation rate로 나타날 수 있다.

대표 패턴:

- `Stream<Integer>` instead of `IntStream`
- `Map<Long, Long>` 카운터
- metrics, aggregation, parsing pipeline의 반복 boxing

즉 primitive specialization이 존재하는 이유가 있다.

### 4. wrapper nullability는 값 의미를 흐릴 수 있다

`Integer`를 쓰는 이유가 세 가지로 섞이기 쉽다.

- primitive를 collection에 넣기 위해
- nullability를 표현하기 위해
- framework binding 때문에

이 세 이유가 뒤섞이면 "값이 없음"과 "값이 0"이 혼동된다.  
도메인적으로 중요한 곳이면 wrapper보다 명시적 value object나 tri-state model이 낫다.

특히 JSON payload DTO에서는 `boolean`/`Boolean`, `int`/`Integer` 선택이 바로 API semantics가 된다.  
이 부분은 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)에서 더 자세히 다룬다.

### 5. map lookup과 defaulting은 특히 조심해야 한다

`Map#get()`은 "키가 없음"과 "값이 null"을 둘 다 `null`로 돌려줄 수 있다.  
여기에 unboxing이 붙으면 버그가 더 잘 숨는다.

즉 다음 질문을 먼저 해야 한다.

- map이 null value를 허용하는가
- missing과 zero를 구분해야 하는가
- `getOrDefault()`가 정말 같은 의미인가

## 실전 시나리오

### 시나리오 1: 작은 ID 비교는 되는데 큰 ID 비교는 깨진다

wrapper `Long`이나 `Integer`를 `==`로 비교했다.  
작은 값은 cache 때문에 지나가지만 범위가 커지면 버그가 드러난다.

### 시나리오 2: 카운터 증가 코드가 가끔 NPE를 낸다

```java
counts.put(key, counts.get(key) + 1);
```

처음 보는 key에서 `counts.get(key)`가 null이면 unboxing NPE가 발생한다.

### 시나리오 3: stream 리팩터링 후 allocation이 늘어난다

`IntStream`으로 충분한 계산을 `Stream<Integer>`로 바꾸면  
박싱과 언박싱이 hot path에 계속 끼어든다.

### 시나리오 4: Boolean flag가 세 가지 의미를 가진다

`Boolean enabled`가 `true`, `false`, `null`을 다 의미하기 시작하면  
도메인 정책과 바인딩 편의가 섞이면서 의도가 흐려진다.

## 코드로 보기

### 1. wrapper 비교는 `equals`나 primitive 변환으로

```java
Integer a = 127;
Integer b = 127;
Integer c = 128;
Integer d = 128;

System.out.println(a == b); // true 일 수 있다
System.out.println(c == d); // false 일 수 있다
```

### 2. unboxing NPE 예시

```java
Integer count = null;
int next = count + 1; // NullPointerException
```

### 3. map counter는 명시적으로 처리

```java
counts.merge(key, 1, Integer::sum);
```

혹은 고경합이면 `LongAdder` 기반 구조가 더 맞을 수 있다.

### 4. primitive specialization 활용

```java
int sum = java.util.stream.IntStream.of(1, 2, 3).sum();
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| primitive | 빠르고 null이 없다 | collection/generic API와 바로 맞지 않는다 |
| wrapper | 프레임워크와 generic API에서 쓰기 쉽다 | identity, nullability, boxing 비용을 이해해야 한다 |
| primitive specialization | allocation을 줄이기 좋다 | API가 다소 덜 일반적이다 |
| 명시적 value object | 의미가 선명하다 | 타입과 변환 코드가 늘어난다 |

핵심은 wrapper를 primitive 대체재가 아니라 다른 semantics를 가진 객체로 보는 것이다.

## 꼬리질문

> Q: 왜 wrapper에 `==`를 쓰면 안 되나요?
> 핵심: 값이 아니라 객체 참조를 비교하고, cache 때문에 가끔만 맞는 것처럼 보일 수 있기 때문이다.

> Q: autoboxing이 왜 NPE를 만들죠?
> 핵심: null wrapper가 primitive 문맥에 들어가며 자동 unboxing될 때 런타임 예외가 난다.

> Q: boxing overhead는 언제 문제 되나요?
> 핵심: hot loop, stream, aggregation, 대량 컬렉션 처리처럼 반복이 많은 경로에서 누적될 수 있다.

> Q: wrapper null은 그냥 "값 없음" 아닌가요?
> 핵심: 그 의미가 도메인적으로 중요하면 missing/unknown/default와 구분되는 더 명시적 모델이 필요할 수 있다.

## 한 줄 정리

autoboxing은 문법을 줄여주지만 wrapper의 identity, nullability, allocation semantics까지 지워주지 않으므로, 비교와 기본값 처리에서 특히 조심해야 한다.
