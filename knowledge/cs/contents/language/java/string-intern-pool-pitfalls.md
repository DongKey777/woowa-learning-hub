# String Intern and Pool Pitfalls

> 한 줄 요약: `String.intern()`은 문자열의 canonical representation을 돌려주지만, 무분별하게 쓰면 전역 pool lookup 비용, 메모리 보류, `==` 오해 같은 문제를 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: String intern, string pool, canonical representation, string literal, `==`, equals, constant expression, pool lookup, deduplication, memory retention, class loader, canonicalization, Locale.ROOT, Unicode normalization

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

`String.intern()`은 문자열의 canonical representation을 반환한다.  
문자열 리터럴과 상수 표현식도 intern된다.

즉 다음을 기억하면 된다.

- 같은 내용을 가진 문자열은 하나의 대표 문자열로 모일 수 있다
- 리터럴은 이미 intern되어 있을 수 있다
- `==`는 내용 비교가 아니라 참조 비교다

문제는 "문자열을 하나로 묶는다"는 장점이 항상 이득이 되지는 않는다는 점이다.  
특히 입력 종류가 많고 유니크 값이 큰 서비스에서는 오히려 손해가 된다.

## 깊이 들어가기

### 1. 왜 `==`가 위험한가

`intern()` 때문에 우연히 `==`가 참이 되는 경우가 있다.  
그러면 코드가 "가끔 맞는 것처럼" 보여서 더 위험하다.

예를 들어 리터럴 비교는 참이지만, 네트워크나 DB에서 읽어온 문자열은 별도 객체일 수 있다.  
이 차이를 `==`가 아니라 `equals()`가 해결한다.

다만 "보이는 글자가 같은가"와 "같은 문자열 객체인가"는 또 다른 문제다.  
Unicode canonicalization이나 locale-sensitive case mapping은 [Locale.ROOT, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)와 함께 보는 편이 정확하다.

### 2. pool은 전역 공유 자원처럼 봐야 한다

intern된 문자열은 JVM이 관리하는 공유 풀에 들어간다.  
그 말은 많은 호출이 같은 테이블을 본다는 뜻이고, 유니크 문자열이 많으면 lookup과 보관 비용이 함께 커질 수 있다는 뜻이다.

이런 특성 때문에 다음 패턴은 주의해야 한다.

- 요청마다 새로운 ID를 intern한다
- 로그 라인 전체를 intern한다
- 외부 입력을 거의 그대로 intern한다

### 3. classloader 경계와도 엮인다

문자열 pool 자체는 JVM 수준의 공유 구조이므로, 특정 classloader local cache처럼 가볍게 생각하면 안 된다.  
직접적인 classloader leak은 아니더라도, intern된 값이 많아지면 메모리 프로파일과 수명 추적이 어려워진다.

관련해서 [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)도 같이 보면 좋다.

### 4. 언제 intern이 유리한가

intern이 쓸모 있는 경우는 제한적이다.

- 아주 작은 vocabulary가 반복된다
- canonical key를 명시적으로 만들고 싶다
- 이미 bounded set임이 보장된다

예: 몇 개의 상태 코드, 고정된 도메인 토큰, 엄격히 제한된 keyword set.

## 실전 시나리오

### 시나리오 1: 문자열 비교가 `==`로 되어 있다

처음에는 잘 동작할 수 있다.  
그러나 입력이 리터럴이 아닌 순간 깨진다.

대응은 단순하다.

- 내용 비교는 `equals()`
- 정렬은 `compareTo()`
- identity 기반 최적화는 정말 bounded 할 때만

### 시나리오 2: 요청 값 전체를 intern했다

이 패턴은 보통 손해다.

- lookup 비용이 추가된다
- pool이 커질 수 있다
- 메모리 회수가 늦게 느껴질 수 있다
- 실익이 없는 값까지 canonicalization한다

### 시나리오 3: 반복되는 소수의 토큰만 intern했다

이건 경우에 따라 좋을 수 있다.  
같은 값이 반복적으로 들어오는 프로토콜, 파서, state machine에서는 중복 객체를 줄일 수 있다.

다만 먼저 측정해야 한다.

## 코드로 보기

### 1. `==`가 아닌 `equals()`를 써야 하는 예

```java
public class AuthChecker {
    public boolean isAdmin(String role) {
        return "ADMIN".equals(role);
    }
}
```

### 2. intern이 의미 있을 수 있는 bounded vocabulary

```java
public class TokenNormalizer {
    public String normalize(String raw) {
        if (raw == null) {
            return null;
        }
        return switch (raw) {
            case "GET", "POST", "PUT", "DELETE" -> raw.intern();
            default -> raw;
        };
    }
}
```

이 예시는 아주 제한된 집합일 때만 생각할 수 있다.  
임의 입력에 그대로 적용하면 안 된다.

### 3. 직접적인 canonical map 대안

```java
import java.util.concurrent.ConcurrentHashMap;

public class StringCanon {
    private final ConcurrentHashMap<String, String> pool = new ConcurrentHashMap<>();

    public String canonicalize(String value) {
        return pool.computeIfAbsent(value, k -> k);
    }
}
```

이 방식은 용도를 명확히 드러내지만, 역시 bounded set과 eviction 정책이 필요하다.

### 4. 운영 관측

```bash
jcmd <pid> GC.class_histogram
jcmd <pid> JFR.start name=strings settings=profile duration=60s filename=/tmp/strings.jfr
```

문자열 문제가 메모리 이슈로 번지면 heap dump보다 먼저 "얼마나 많은 distinct string이 생겼는가"를 보는 편이 좋다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `equals()` | 안전하고 명확하다 | identity 최적화는 못 쓴다 |
| `intern()` | canonical identity를 만들 수 있다 | pool lookup과 메모리 보류 비용이 있다 |
| canonical map | 정책을 직접 통제한다 | eviction과 동시성 설계가 필요하다 |
| 그냥 둔다 | 가장 단순하다 | 중복 객체와 비교 비용이 남을 수 있다 |

핵심은 intern을 "문자열 최적화의 기본값"으로 보면 안 된다는 것이다.

## 꼬리질문

> Q: 문자열 리터럴은 왜 `==`가 같게 보이나요?
> 핵심: 리터럴과 constant expression은 intern되기 때문에 같은 canonical instance를 가리킬 수 있다.

> Q: `intern()`을 왜 남용하면 안 되나요?
> 핵심: 유니크 값이 많을수록 pool lookup과 메모리 유지 비용이 커지고, 참조 비교 습관까지 잘못될 수 있다.

> Q: 언제 intern이 유용할 수 있나요?
> 핵심: 반복되는 작은 vocabulary, bounded token set, 명시적 canonicalization이 필요한 경우다.

## 한 줄 정리

`String.intern()`은 canonicalization 도구이지 기본 최적화가 아니며, 비교는 `equals()`로 하고 intern은 작은 bounded set에만 신중하게 써야 한다.
