# Class Initialization Ordering

> 한 줄 요약: Java 클래스 초기화는 로딩과 별개로 `clinit` 순서를 가지며, static 필드와 초기화 블록의 순서를 잘못 설계하면 NPE, 순환 초기화, 예상치 못한 side effect가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)

> retrieval-anchor-keywords: class initialization, clinit, static initializer, static field order, initialization-on-demand holder, circular initialization, class loading, initialization lock, constant variable, side effect, bootstrap

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

클래스가 JVM에 보인다고 해서 곧바로 초기화되는 것은 아니다.  
로드, 링크, 초기화는 다른 단계다.

초기화는 보통 `clinit`에서 일어나며, static field initialization과 static block이 순서대로 실행된다.  
이 순서가 중요하다.

### 왜 중요한가

- static 필드가 아직 준비되지 않았는데 다른 초기화 코드가 읽을 수 있다
- 순환 참조가 있으면 초기화 중에 반쯤 만들어진 값을 볼 수 있다
- side effect가 있으면 class load만으로도 동작이 생긴다

## 깊이 들어가기

### 1. static 초기화 순서를 읽는 법

Java는 선언 순서에 따라 static field와 static block을 초기화한다.  
즉 앞에서 뒤로 읽으며 값이 들어간다.

그래서 다음 패턴은 위험하다.

- 뒤에서 선언한 static 필드를 앞의 초기화 코드가 읽음
- static block에서 아직 null인 값을 사용
- 초기화 중 다른 클래스가 다시 현재 클래스를 건드림

### 2. 순환 초기화는 조용히 깨진다

클래스 A의 초기화가 클래스 B를 부르고, B의 초기화가 다시 A를 부르면 중간 상태를 볼 수 있다.  
이 문제는 컴파일 에러가 아니라 런타임 초기화 순서 문제다.

### 3. initialization-on-demand holder는 왜 자주 쓰나

holder 패턴은 lazy initialization을 안전하게 하려는 대표적 방법이다.  
중첩 static holder는 필요할 때만 초기화되므로, 단순 싱글턴에 자주 쓴다.

### 4. constant variable는 특별하다

컴파일 타임 상수는 클래스 초기화 타이밍에 영향을 덜 줄 수 있다.  
하지만 runtime 계산 값은 그렇지 않다.

## 실전 시나리오

### 시나리오 1: static 필드가 null인데 왜 벌써 쓰이나

초기화 순서가 잘못되면 `null` 참조나 예상 못 한 default 값이 나온다.  
이런 버그는 재현이 어렵고 부팅 순서에 따라 달라진다.

### 시나리오 2: class loading만으로 로그가 찍힌다

static initializer 안에 side effect가 있으면, class reference만 생겨도 외부 호출이 일어날 수 있다.  
초기화 로직은 가능하면 작고 결정적으로 유지하는 편이 좋다.

### 시나리오 3: 초기화 중 예외가 나서 이후에도 이상하다

클래스 초기화가 실패하면 이후 사용 시 `NoClassDefFoundError`처럼 보일 수 있다.  
이 경우 원래의 초기화 예외를 먼저 찾아야 한다.

## 코드로 보기

### 1. 선언 순서가 중요한 예

```java
public class Config {
    static final String BASE_URL = initBaseUrl();
    static final String FULL_URL = BASE_URL + "/api";

    private static String initBaseUrl() {
        return "https://example.com";
    }
}
```

### 2. 순환 초기화의 냄새

```java
public class A {
    static final String VALUE = B.VALUE + "-a";
}

public class B {
    static final String VALUE = A.VALUE + "-b";
}
```

### 3. holder 패턴

```java
public class Singleton {
    private Singleton() {}

    private static class Holder {
        private static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

### 4. 초기화 오류를 볼 때

```java
try {
    Class.forName("com.example.SomeClass");
} catch (ClassNotFoundException e) {
    // loading 문제
}
```

초기화 실패는 loading 실패와 다르므로 예외 체인을 함께 봐야 한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| eager static init | 단순하다 | 초기화 비용이 앞당겨진다 |
| lazy holder | 필요할 때만 만든다 | 초기화 경로가 숨겨진다 |
| heavy static block | 한곳에 모인다 | 순서와 side effect 문제가 커진다 |
| explicit factory | 제어가 명확하다 | 코드가 길어진다 |

핵심은 static initialization을 "편한 곳"이 아니라 "부팅 계약"으로 다루는 것이다.

## 꼬리질문

> Q: class loading과 class initialization은 같은가요?
> 핵심: 아니다. loading은 클래스를 JVM이 인식하는 단계이고, initialization은 static 초기화가 실제로 실행되는 단계다.

> Q: static field 순서가 왜 중요한가요?
> 핵심: 선언 순서대로 초기화되므로 앞선 코드가 뒤에 선언된 값을 읽으면 null이나 기본값을 볼 수 있다.

> Q: holder 패턴은 왜 안전한가요?
> 핵심: 필요할 때만 초기화되고 JVM 초기화 규칙을 이용해 lazy singleton을 만들 수 있기 때문이다.

## 한 줄 정리

클래스 초기화는 로딩과 별개이며, static 선언 순서와 순환 초기화를 제대로 다뤄야 `clinit` 기반 버그를 피할 수 있다.
