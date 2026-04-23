# Reflection 비용과 대안

> 한 줄 요약: Reflection은 편하지만 비싸고, 런타임 동적성이 꼭 필요하지 않다면 MethodHandle이나 코드 생성이 더 낫다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Reflection, Generics, Annotations](./reflection-generics-annotations.md)
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [ClassLoader, Exception 경계, 객체 계약](./classloader-exception-boundaries-object-contracts.md)
> - [Spring Framework](../../spring/README.md)
> - [Spring Boot 자동 구성](../../spring/spring-boot-autoconfiguration.md)

retrieval-anchor-keywords: Java reflection cost, reflection overhead, MethodHandle vs reflection, reflection alternative, classpath scanning cost, runtime dynamic invocation, code generation vs reflection, annotation processing alternative, JIT unfriendly reflection, Spring reflection startup cost

---

## 핵심 개념

Reflection은 런타임에 클래스, 메서드, 필드 정보를 조회하고 호출하는 기술이다.

장점:

- 프레임워크가 코드를 미리 알지 못해도 동작한다
- 어노테이션 기반 설정과 궁합이 좋다
- DI, ORM, 테스트 프레임워크, JSON 매핑에 널리 쓰인다

단점:

- 호출 비용이 높다
- 정적 분석과 JIT 최적화가 약해진다
- 에러가 런타임에 늦게 터진다

즉 Reflection은 "나쁜 기술"이 아니라, **동적성이 필요한 순간에만 써야 하는 기술**이다.

---

## 깊이 들어가기

### 1. Reflection이 느린 이유

비용은 단순한 "동적 호출"만이 아니다.

| 비용 | 설명 |
|---|---|
| 접근 검사 | private/public 접근 체크가 들어간다 |
| 조회 비용 | `Class`/`Method`를 문자열 기반으로 찾는다 |
| 박싱/언박싱 | primitive가 `Object` 경로로 바뀐다 |
| JIT 불리함 | 정적 호출보다 인라이닝이 어렵다 |
| 예외 경로 | 잘못된 이름/시그니처가 런타임까지 숨는다 |

Spring이 기동 시 느려지는 이유 중 하나가 클래스 스캔과 Reflection이다.  
이 문맥은 [Spring Framework](../../spring/README.md)와 [Spring Boot 자동 구성](../../spring/spring-boot-autoconfiguration.md) 문서와도 이어진다.

### 2. MethodHandle이 더 나은 경우

`MethodHandle`은 Reflection보다 JIT 친화적인 동적 호출 방식이다.

```java
MethodHandles.Lookup lookup = MethodHandles.lookup();
MethodHandle handle = lookup.findVirtual(User.class, "getName",
        MethodType.methodType(String.class));

String name = (String) handle.invokeExact(user);
```

왜 더 낫나:

- 룩업 시점에 타입을 더 강하게 검증한다
- 호출 경로가 더 정교해서 JIT 최적화 여지가 있다
- 람다/`invokedynamic` 기반 기능과 맞물린다

### 3. 코드 생성이 필요한 경우

런타임 호출 자체보다 더 빠른 길은 아예 코드를 만들어 두는 것이다.

예:

- Annotation Processing
- ByteBuddy / ASM 기반 생성
- Lombok 같은 컴파일 타임 확장

이 접근은 Reflection을 없애거나 줄여준다.

---

## 실전 시나리오

### 시나리오 1: JSON 매핑이 느리다

증상:

- 요청 수는 많은데 CPU가 의외로 높다
- profiler를 보면 reflection 호출이 반복된다

대응:

1. 매 요청마다 `Class.getMethod()` 같은 조회를 하지 않는지 본다
2. `Method`/`Field`를 캐시한다
3. 가능하면 `MethodHandle` 또는 codegen을 검토한다
4. Jackson 같은 라이브러리의 내부 최적화 옵션을 확인한다

### 시나리오 2: Spring 빈 생성이 늘어나면서 기동 시간이 길다

Reflection 기반 스캔은 편하지만 시작 비용을 만든다.

이럴 때는:

- 패키지 스캔 범위를 줄인다
- Bean 수를 줄인다
- AOT/프리컴파일 옵션을 검토한다

### 시나리오 3: 테스트에서만 잘 되던 코드가 운영에서 깨진다

런타임 Reflection은 타이핑 실수를 늦게 발견하게 만든다.

예를 들면:

- 메서드명 오타
- 필드명 변경
- 접근 제한자 변경

이건 컴파일 타임에 잡히지 않고 운영에서 터질 수 있다.

---

## 코드로 보기

### Reflection 호출

```java
Method method = User.class.getMethod("getName");
String name = (String) method.invoke(user);
```

### MethodHandle 호출

```java
MethodHandle handle = MethodHandles.lookup()
    .findVirtual(User.class, "getName", MethodType.methodType(String.class));
String name = (String) handle.invokeExact(user);
```

### 캐시를 두는 간단한 최적화

```java
private static final Map<String, Method> METHOD_CACHE = new ConcurrentHashMap<>();

public static Method findMethod(Class<?> type, String name) {
    return METHOD_CACHE.computeIfAbsent(type.getName() + "#" + name, key -> {
        try {
            return type.getMethod(name);
        } catch (NoSuchMethodException e) {
            throw new IllegalArgumentException(e);
        }
    });
}
```

Reflection이 꼭 필요하면, 최소한 **조회 비용을 반복하지 않도록 캐싱**하는 게 기본이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Reflection | 가장 유연하다 | 느리고 늦게 실패한다 | 프레임워크/범용 라이브러리 |
| MethodHandle | 동적이면서 더 빠르다 | API가 어렵다 | 호출 대상을 자주 바꾸는 고성능 코드 |
| Codegen | 빠르고 명시적이다 | 빌드/생성 복잡도가 올라간다 | 반복 호출이 많은 핵심 경로 |
| Direct call | 가장 단순하고 빠르다 | 유연성이 낮다 | 일반 비즈니스 코드 |

핵심 기준은 이렇다.

- 프레임워크 내부라면 Reflection이 합리적일 수 있다
- 애플리케이션의 hot path라면 Reflection을 줄여야 한다
- "어차피 한 번만"인지 "요청마다"인지 구분해야 한다

---

## 꼬리질문

> Q: Reflection이 느린 이유를 한 문장으로 설명하면?
> 의도: 호출 비용의 구조를 이해하는지 확인
> 핵심: 문자열 조회, 접근 검사, 박싱, JIT 최적화 제한이 겹친다

> Q: MethodHandle이 Reflection보다 나은 이유는 무엇인가요?
> 의도: 동적 호출 대안을 알고 있는지 확인
> 핵심: JIT 친화적이고 호출 경로가 더 명확하다

> Q: Spring은 왜 Reflection을 많이 쓰면서도 성능이 괜찮나요?
> 의도: 프레임워크와 애플리케이션 hot path를 구분하는지 확인
> 핵심: 주로 초기화/조립 단계에 쓰고, 실행 경로는 프록시/캐시로 줄인다

## 한 줄 정리

Reflection은 프레임워크에 필요하지만, hot path에서는 캐시·MethodHandle·코드 생성 같은 대안을 먼저 검토해야 한다.
