# Retry Policy vs Decorator Chain

> 한 줄 요약: Retry Policy는 재시도 규칙을 캡슐화하고, Decorator Chain은 호출에 기능을 층층이 덧씌운다. 둘을 섞으면 실패와 부가기능의 경계가 흐려진다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [데코레이터 vs 프록시](./decorator-vs-proxy.md)
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [전략 패턴](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

재시도는 단순한 부가 기능처럼 보이지만, 실제로는 **실패 정책**이다.  
그래서 retry는 decorator로만 처리하면 안 되고, 정책 객체로 분리하는 편이 더 안전한 경우가 많다.

- Retry Policy: 언제, 몇 번, 어떤 간격으로 다시 시도할지
- Decorator Chain: 로깅, 메트릭, 트레이싱, 캐싱 같은 부가 기능 조합

### Retrieval Anchors

- `retry policy object`
- `decorator chain`
- `backoff strategy`
- `idempotent operation`
- `failure semantics`

---

## 깊이 들어가기

### 1. 재시도는 의미론이 중요하다

재시도는 "한 번 더 호출"이 아니다.

- 어떤 예외를 다시 시도할지
- 멱등성이 보장되는지
- 지수 백오프를 쓸지
- 최종 실패 시 무엇을 남길지

이건 정책이다.

### 2. Decorator는 기능, Policy는 결정이다

Decorator는 기능을 추가한다.

- 로깅
- 인증 헤더 주입
- 메트릭 수집
- 압축

Retry는 이와 다르다.

- 실패 유형 판단
- 재시도 횟수 계산
- 지연 시간 계산
- 포기 조건 결정

### 3. 체인에 retry를 넣으면 복잡해진다

Decorator chain 안에 retry가 섞이면 다음이 어려워진다.

- 어느 단계가 몇 번 실행됐는지 추적
- 중복 side effect 처리
- 부분 실패와 최종 실패 구분

---

## 실전 시나리오

### 시나리오 1: 외부 PG 호출

네트워크 오류는 retry policy로 다루고, 호출 전후 로깅은 decorator로 분리하는 편이 좋다.

### 시나리오 2: 메일 발송

메시지 전송은 재시도 정책이 중요하고, 메트릭과 트레이싱은 decorator가 담당하기 좋다.

### 시나리오 3: 파일 업로드

재시도 가능한 예외와 하면 안 되는 예외를 분리해야 한다.

---

## 코드로 보기

### Retry Policy

```java
public interface RetryPolicy {
    boolean canRetry(int attempt, Exception ex);
    Duration delay(int attempt);
}

public class ExponentialBackoffRetryPolicy implements RetryPolicy {
    @Override
    public boolean canRetry(int attempt, Exception ex) {
        return attempt < 3;
    }

    @Override
    public Duration delay(int attempt) {
        return Duration.ofMillis(100L * (1L << attempt));
    }
}
```

### 적용

```java
public class PaymentClient {
    private final RetryPolicy retryPolicy;

    public PaymentResult pay(PaymentRequest request) {
        int attempt = 0;
        while (true) {
            try {
                return call(request);
            } catch (Exception ex) {
                if (!retryPolicy.canRetry(attempt++, ex)) {
                    throw ex;
                }
                sleep(retryPolicy.delay(attempt));
            }
        }
    }
}
```

### Decorator

```java
public class LoggingPaymentClient implements PaymentPort {
    private final PaymentPort delegate;

    @Override
    public PaymentResult pay(PaymentRequest request) {
        log(request);
        return delegate.pay(request);
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Retry Policy | 실패 규칙이 명시적이다 | 구현이 조금 길다 | 호출 실패 의미가 중요할 때 |
| Decorator Chain | 기능 추가가 쉽다 | 실패 의미가 흐려질 수 있다 | 로깅/메트릭/트레이싱 |
| 둘을 섞기 | 역할 분리가 좋다 | 조립이 복잡해진다 | 운영 안정성이 중요할 때 |

판단 기준은 다음과 같다.

- 실패 의미를 설계해야 하면 retry policy
- 기능을 덧붙이는 것이 목적이면 decorator
- retry를 decorator 내부에 숨기면 추적이 어려워진다

---

## 꼬리질문

> Q: Retry Policy를 decorator로 구현하면 왜 문제가 되나요?
> 의도: 실패 의미와 기능 추가를 구분하는지 확인한다.
> 핵심: 재시도는 정책이고 decorator는 기능이라 책임이 다르다.

> Q: Decorator chain에 retry가 들어가면 어떤 위험이 있나요?
> 의도: 중복 side effect와 추적성 문제를 아는지 확인한다.
> 핵심: 같은 작업이 여러 번 실행되면서 로그와 부작용이 꼬일 수 있다.

> Q: 멱등성이 왜 중요하죠?
> 의도: 재시도의 안전 조건을 아는지 확인한다.
> 핵심: 같은 요청이 다시 실행돼도 결과가 깨지지 않아야 한다.

## 한 줄 정리

Retry Policy는 실패 처리 규칙을 담고, Decorator Chain은 호출에 기능을 쌓는다. 둘을 섞되 역할은 분리해야 한다.

