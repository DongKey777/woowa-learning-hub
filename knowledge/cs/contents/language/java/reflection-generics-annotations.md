# Reflection, Generics, Annotations

**난이도: 🔴 Advanced**
> 자바 플랫폼의 메타프로그래밍 3대 축 -- 런타임 타입 정보 조작, 컴파일 타임 타입 안전성, 선언적 메타데이터

## 핵심 개념

| 요소 | 시점 | 핵심 역할 |
|---|---|---|
| Reflection | 런타임 | 클래스/메서드/필드 정보를 동적으로 조회 및 호출 |
| Generics | 컴파일 타임 | 타입 파라미터로 재사용성과 타입 안전성 확보 |
| Annotations | 컴파일 + 런타임 | 코드에 메타데이터를 부착하여 도구/프레임워크가 활용 |

---

## 깊이 들어가기

### Reflection 🟡 Intermediate

Reflection은 **런타임에 클래스의 구조를 탐색하고 조작하는 API**다.

```java
Class<?> clazz = Class.forName("com.example.User");
Object instance = clazz.getDeclaredConstructor().newInstance();
Method method = clazz.getMethod("getName");
Object result = method.invoke(instance);
```

#### Reflection의 비용

Reflection이 느린 이유는 단순히 "동적이니까"가 아니다. 구체적 비용은 다음과 같다.

1. **접근 검사(Access Check)**: 매 호출마다 `SecurityManager`와 접근 제한자를 확인한다
2. **박싱/언박싱**: `Method.invoke()`는 `Object[]`를 받으므로 primitive 인자가 박싱된다
3. **JIT 최적화 불가**: 컴파일러가 호출 대상을 정적으로 알 수 없어 인라이닝 등 최적화가 제한된다
4. **메서드 조회 비용**: `getMethod()`는 상속 계층을 탐색하며 문자열 비교를 수행한다

#### javap로 보는 차이

일반 호출:
```
invokevirtual #4  // Method com/example/User.getName:()Ljava/lang/String;
```

Reflection 호출:
```
invokevirtual #7  // Method java/lang/reflect/Method.invoke:(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
```

일반 호출은 바이트코드에서 직접 대상 메서드를 가리키지만, Reflection은 `Method.invoke()`라는 간접 경로를 거친다. JIT가 이를 인라이닝하기 어렵다.

#### Reflection의 대안: MethodHandle 🔴 Advanced

Java 7에서 도입된 `MethodHandle`은 Reflection보다 **JIT 친화적인 동적 호출 방식**이다.

```java
MethodHandles.Lookup lookup = MethodHandles.lookup();
MethodHandle mh = lookup.findVirtual(User.class, "getName",
        MethodType.methodType(String.class));
String name = (String) mh.invoke(user);
```

| 비교 항목 | Reflection | MethodHandle |
|---|---|---|
| JIT 최적화 | 어려움 | 인라이닝 가능 |
| 접근 검사 시점 | 매 호출 | 룩업 시 1회 |
| 타입 안전성 | Object[] 기반 | MethodType으로 검증 |
| 사용 편의성 | 높음 (문자열 기반) | 낮음 (타입 명시 필요) |

`invokedynamic` 바이트코드 명령어도 내부적으로 MethodHandle을 사용한다. 람다 표현식이 빠른 이유 중 하나다.

---

### Generics와 타입 소거 🟡 Intermediate

#### 타입 소거(Type Erasure)란

Java Generics는 **컴파일 타임에만 존재**한다. 컴파일러가 타입 검사를 끝낸 뒤, 바이트코드에서는 타입 파라미터가 지워진다.

```java
// 소스코드
List<String> list = new ArrayList<>();
list.add("hello");
String s = list.get(0);
```

```
// 바이트코드 (javap -c)
invokevirtual #3  // Method java/util/ArrayList.add:(Ljava/lang/Object;)Z
invokevirtual #4  // Method java/util/ArrayList.get:(I)Ljava/lang/Object;
checkcast     #5  // class java/lang/String
```

`ArrayList<String>`이 아니라 `ArrayList`로 처리되고, `get()` 반환 후 `checkcast`로 캐스팅한다.

#### 타입 소거의 한계

1. **런타임에 타입 파라미터를 알 수 없다**
   ```java
   // 불가능
   if (list instanceof List<String>) { ... }
   
   // 불가능
   new T();
   T[] arr = new T[10];
   ```

2. **primitive 타입을 타입 파라미터로 쓸 수 없다**
   - `List<int>`는 불가 -> `List<Integer>` 사용 (박싱 비용 발생)

3. **오버로딩 제한**
   ```java
   // 컴파일 에러: 소거 후 둘 다 process(List)가 됨
   void process(List<String> list) { }
   void process(List<Integer> list) { }
   ```

#### 타입 소거 우회 기법 🔴 Advanced

**Super Type Token 패턴**: 익명 클래스의 제네릭 상위 타입 정보는 바이트코드에 남는다는 점을 이용한다.

```java
// TypeReference를 상속한 익명 클래스
TypeReference<List<String>> typeRef = new TypeReference<List<String>>() {};

// 내부적으로 이렇게 꺼낸다
Type type = getClass().getGenericSuperclass();
Type actualType = ((ParameterizedType) type).getActualTypeArguments()[0];
// actualType = java.util.List<java.lang.String>
```

이 패턴은 Jackson의 `TypeReference`, Guice의 `TypeLiteral` 등에서 널리 쓰인다.

**왜 가능한가?** JLS 4.6에 따르면 타입 소거는 "타입 변수"에 적용되지만, 클래스 선언부의 제네릭 상위 타입 정보는 `Signature` 속성으로 `.class` 파일에 보존된다.

#### Bounded Type Parameter와 와일드카드

```java
// Upper Bound: T는 Comparable을 구현해야 함
public <T extends Comparable<T>> T max(List<T> list) { ... }

// 와일드카드: 읽기 전용으로 사용
public void printAll(List<? extends Number> list) { ... }

// PECS (Producer Extends, Consumer Super)
public void copy(List<? extends T> src, List<? super T> dest) { ... }
```

PECS 원칙:
- `? extends T`: 데이터를 꺼내는(produce) 쪽 -> 읽기만 가능
- `? super T`: 데이터를 넣는(consume) 쪽 -> 쓰기만 가능

---

### Annotations 🟢 Basic

어노테이션은 **코드에 메타데이터를 부착하는 선언적 방법**이다.

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Cacheable {
    long ttlSeconds() default 300;
}
```

#### Retention 정책

| 정책 | 설명 | 대표 예 |
|---|---|---|
| SOURCE | 컴파일 후 사라짐 | `@Override`, `@SuppressWarnings` |
| CLASS | .class에 남지만 런타임에 접근 불가 | 기본값 |
| RUNTIME | 런타임에 Reflection으로 조회 가능 | `@Entity`, `@Test`, `@Autowired` |

#### 어노테이션이 프레임워크를 만드는 방식

1. **런타임 Reflection**: Spring의 `@Autowired` -> 리플렉션으로 필드/생성자를 찾아 주입
2. **컴파일 타임 처리**: Lombok의 `@Data` -> Annotation Processor가 소스 생성
3. **바이트코드 조작**: `@Transactional` -> CGLIB/ByteBuddy가 프록시 생성

---

## 실전 시나리오

### 시나리오 1: Reflection으로 인한 성능 저하

Spring 애플리케이션 시작이 느린 이유 중 하나가 클래스 스캐닝 시 대량의 Reflection 호출이다.
- **증상**: 기동 시간 30초 이상
- **원인**: `@Component` 스캔 범위가 너무 넓음
- **해결**: 스캔 범위 축소, Spring Native/AOT 활용, 또는 명시적 Bean 등록

### 시나리오 2: 타입 소거로 인한 직렬화 실패

```java
// Jackson으로 List<User>를 역직렬화하려 할 때
String json = "[{\"name\":\"Kim\"}]";
List<User> users = objectMapper.readValue(json, List.class);
// users.get(0)은 LinkedHashMap이지 User가 아니다!

// 해결: TypeReference 사용
List<User> users = objectMapper.readValue(json,
    new TypeReference<List<User>>() {});
```

### 시나리오 3: 어노테이션 남용으로 인한 유지보수 악화

```java
@Validated @Transactional @Cacheable @Retryable @Async
@PreAuthorize("hasRole('ADMIN')")
public UserResponse updateUser(@Valid @RequestBody UserRequest req) { ... }
```

어노테이션이 6개 이상 쌓이면 메서드의 실제 비즈니스 로직보다 횡단 관심사가 더 눈에 들어온다. 이 경우 AOP 설정을 분리하거나, 커스텀 어노테이션으로 합치는 것을 고려해야 한다.

---

## 코드로 보기

### Reflection vs MethodHandle 성능 비교

```java
public class ReflectionBenchmark {
    static final int ITERATIONS = 1_000_000;

    public static void main(String[] args) throws Throwable {
        User user = new User("Kim");

        // 1. 직접 호출
        long start = System.nanoTime();
        for (int i = 0; i < ITERATIONS; i++) {
            user.getName();
        }
        long directTime = System.nanoTime() - start;

        // 2. Reflection
        Method method = User.class.getMethod("getName");
        start = System.nanoTime();
        for (int i = 0; i < ITERATIONS; i++) {
            method.invoke(user);
        }
        long reflectTime = System.nanoTime() - start;

        // 3. MethodHandle
        MethodHandle mh = MethodHandles.lookup()
            .findVirtual(User.class, "getName", MethodType.methodType(String.class));
        start = System.nanoTime();
        for (int i = 0; i < ITERATIONS; i++) {
            mh.invoke(user);
        }
        long mhTime = System.nanoTime() - start;

        System.out.printf("Direct: %dms, Reflection: %dms, MethodHandle: %dms%n",
            directTime/1_000_000, reflectTime/1_000_000, mhTime/1_000_000);
    }
}
```

일반적으로 Direct < MethodHandle < Reflection 순으로 빠르다. 단, JIT 워밍업 후에는 MethodHandle이 직접 호출에 근접할 수 있다.

---

## 트레이드오프

| 관점 | Reflection | MethodHandle | Annotation Processing |
|---|---|---|---|
| 유연성 | 매우 높음 | 높음 | 컴파일 타임 고정 |
| 성능 | 느림 | 빠름 (JIT 친화) | 런타임 비용 없음 |
| 안전성 | 런타임 에러 | 타입 검증 가능 | 컴파일 에러 |
| 학습 곡선 | 낮음 | 중간 | 높음 |

| 관점 | Generics (소거 방식) | Reified Generics (Kotlin inline) |
|---|---|---|
| 바이너리 호환성 | Java 5 이전과 호환 | 호환성 깨짐 |
| 런타임 타입 정보 | 없음 | 있음 |
| 메모리 | 타입별 클래스 생성 없음 | 타입별 특수화 필요 |

---

## 꼬리질문

1. `Class.forName()`과 `ClassLoader.loadClass()`의 차이는 무엇인가?
   - `forName()`은 기본적으로 클래스를 초기화(static 블록 실행)하지만, `loadClass()`는 로딩만 한다.

2. 제네릭 타입 소거 때문에 불가능한 것 3가지를 말해보라.
   - `new T()`, `T[].class`, `instanceof List<String>`

3. `@Retention(RUNTIME)` 어노테이션은 바이트코드 어디에 저장되는가?
   - `.class` 파일의 `RuntimeVisibleAnnotations` 속성에 저장된다.

4. Spring이 `@Transactional`을 처리하는 방식과 Lombok이 `@Data`를 처리하는 방식의 근본적 차이는?
   - Spring: 런타임 프록시(CGLIB/JDK Proxy) + Reflection
   - Lombok: 컴파일 타임 Annotation Processor + 소스 생성

5. MethodHandle이 Reflection보다 빠른 이유를 JIT 관점에서 설명하라.
   - MethodHandle은 `invokedynamic`의 CallSite에 바인딩되어 JIT가 호출 대상을 상수처럼 취급하고 인라이닝할 수 있다. Reflection의 `Method.invoke()`는 간접 호출이라 인라이닝이 제한된다.

---

## 한 줄 정리

Reflection은 강력하지만 느리고, Generics는 안전하지만 런타임에 사라지며, Annotation은 선언적이지만 과하면 마법이 된다 -- 각각의 한계를 아는 것이 제대로 쓰는 시작이다.
