# Try-With-Resources and Suppressed Exceptions

> 한 줄 요약: try-with-resources는 자원 해제를 자동화하지만, 본문 예외와 close 예외가 동시에 나올 수 있으므로 suppressed exceptions를 읽지 못하면 장애 원인을 반대로 해석할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)

> retrieval-anchor-keywords: try-with-resources, AutoCloseable, close, suppressed exception, exception masking, resource cleanup, finally, JDBC, file handle, network socket, primary exception

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

try-with-resources는 `AutoCloseable`을 자동으로 닫는다.  
핵심은 close가 실패해도 본문 예외를 덮어쓰지 않도록 설계되어 있다는 점이다.

본문에서 예외가 발생한 뒤 close에서도 예외가 발생하면, close 예외는 suppressed exception이 된다.  
즉 "진짜 원인"은 primary exception일 가능성이 높다.

## 깊이 들어가기

### 1. 왜 suppressed exceptions가 중요한가

자원 해제 실패는 자주 본문 실패와 함께 일어난다.

- SQL query 실패 후 connection close 실패
- 파일 처리 실패 후 stream close 실패
- socket write 실패 후 flush/close 실패

이때 close 예외만 보면 원인을 잘못 볼 수 있다.

### 2. `finally`보다 try-with-resources가 좋은 이유

`finally`는 수동으로 닫아야 해서 실수하기 쉽다.  
try-with-resources는 닫는 순서와 예외 처리를 JVM이 더 일관되게 관리한다.

특히 다음 실수를 줄여 준다.

- close 누락
- 중복 close
- 원인 예외 마스킹

### 3. close 순서도 중요하다

리소스가 여러 개면 선언 역순으로 닫힌다.  
의존 관계가 있는 자원은 이 순서를 이해하고 있어야 한다.

예:

- buffered wrapper
- underlying stream
- JDBC statement/connection

### 4. suppressed exceptions를 로그에서 버리면 안 된다

애플리케이션 로깅이 primary exception만 찍고 suppressed를 버리면 close 실패가 사라진다.  
하지만 그 close 실패가 커넥션 풀 고갈이나 파일 핸들 누수의 신호일 수 있다.

## 실전 시나리오

### 시나리오 1: 파일 처리는 실패했는데 close도 실패한다

이때 본문 예외가 먼저, close 예외가 나중에 붙는다.  
원인 분석은 primary exception부터 해야 한다.

### 시나리오 2: JDBC에서 connection leak처럼 보인다

try-with-resources를 쓰지 않으면 close 누락이 생기기 쉽다.  
리소스 경계가 긴 코드일수록 자동화가 더 중요하다.

### 시나리오 3: close 실패가 진짜 원인일 수 있다

물론 close 예외가 늘 secondary인 것은 아니다.  
자원 해제 과정에서 실제 장애가 드러나는 경우도 있으므로 suppressed를 함께 봐야 한다.

## 코드로 보기

### 1. 기본 try-with-resources

```java
try (InputStream in = new FileInputStream("a.txt");
     OutputStream out = new FileOutputStream("b.txt")) {
    in.transferTo(out);
}
```

### 2. suppressed exception 확인

```java
try {
    work();
} catch (Exception e) {
    for (Throwable suppressed : e.getSuppressed()) {
        // close failure or secondary error
    }
    throw e;
}
```

### 3. `AutoCloseable` 구현

```java
public final class TempResource implements AutoCloseable {
    @Override
    public void close() {
        // release native/file/socket resources
    }
}
```

### 4. 수동 finally보다 선언형 close가 명확하다

```java
try (TempResource resource = new TempResource()) {
    use(resource);
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| try-with-resources | 자동 cleanup과 예외 처리에 강하다 | `AutoCloseable` 설계가 필요하다 |
| finally | 유연하다 | 실수와 중복이 많다 |
| 수동 close | 제어가 명시적이다 | 마스크/누락 위험이 있다 |
| suppressed 로그 포함 | 원인 분석에 좋다 | 로그가 길어질 수 있다 |

핵심은 자원 해제 실패를 본문 예외와 분리해서 읽는 것이다.

## 꼬리질문

> Q: suppressed exception은 왜 생기나요?
> 핵심: 본문 예외가 이미 있는 상태에서 close가 또 실패하면 secondary error가 suppressed로 붙는다.

> Q: try-with-resources가 `finally`보다 좋은 이유는 무엇인가요?
> 핵심: close 누락과 예외 마스킹을 줄여 주기 때문이다.

> Q: suppressed를 로그에 꼭 남겨야 하나요?
> 핵심: 가능하면 남겨야 한다. close 실패가 누수나 downstream 장애의 신호일 수 있기 때문이다.

## 한 줄 정리

try-with-resources는 cleanup을 안전하게 만들지만, primary exception과 suppressed exception을 함께 읽어야 진짜 원인을 놓치지 않는다.
