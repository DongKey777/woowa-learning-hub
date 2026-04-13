# Java Module System Runtime Boundaries

> 한 줄 요약: Java module system은 package export와 opens로 런타임 경계를 명시하고, reflection과 deep access는 `--add-opens` 같은 예외를 통해서만 제한적으로 허용된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)
> - [Reflection Cost and Alternatives](./reflection-cost-and-alternatives.md)
> - [Class Initialization Ordering](./class-initialization-ordering.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)

> retrieval-anchor-keywords: module system, runtime boundaries, export, opens, strong encapsulation, reflection, add-opens, unnamed module, module path, layer, encapsulation boundary, illegal reflective access

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

JPMS(Java Platform Module System)는 패키지를 모듈 단위로 묶고, 무엇을 공개할지와 무엇을 reflection에 열지 명시하게 만든다.  
즉 runtime boundary를 코드와 런치 옵션으로 표현한다.

중요한 키워드:

- `exports`
- `opens`
- named module
- unnamed module
- module path
- `--add-opens`

## 깊이 들어가기

### 1. export와 open은 다르다

- `exports`: 컴파일/런타임에서 public API를 노출
- `opens`: reflection과 deep access를 허용

둘은 비슷해 보이지만 목적이 다르다.

### 2. runtime boundary는 reflective access에서 특히 중요하다

모듈 경계는 reflection으로 내부 타입에 접근할 때 효과가 크다.  
그래서 프레임워크와 라이브러리가 내부 접근을 하려면 `opens` 또는 `--add-opens`가 필요할 수 있다.

### 3. unnamed module은 과도한 자유의 출발점이다

classpath에 있는 코드는 종종 unnamed module로 취급된다.  
이 경계는 편하지만, 강한 캡슐화 이점은 줄어든다.

### 4. layer도 runtime boundary다

ModuleLayer를 통해 런타임에 모듈 레이어를 구성할 수 있다.  
플러그인, 런타임 격리, custom image 경계와 연결된다.

## 실전 시나리오

### 시나리오 1: reflection이 갑자기 깨진다

JDK 업그레이드 후 illegal reflective access가 막히는 경우가 있다.  
이때 module boundary와 `--add-opens` 설정을 점검한다.

### 시나리오 2: 라이브러리가 private field를 못 읽는다

deep reflection이 막혔을 수 있다.  
단순히 코드 문제가 아니라 module boundary 설계 문제일 수 있다.

### 시나리오 3: 모듈화가 빌드와 실행을 복잡하게 만든다

경계가 명확해지는 대신 설정과 패키징 비용이 늘어난다.  
이득과 복잡도를 같이 봐야 한다.

## 코드로 보기

### 1. module-info 감각

```java
module com.example.app {
    exports com.example.api;
    opens com.example.internal to com.example.framework;
}
```

### 2. runtime 옵션 감각

```bash
java --add-opens java.base/java.lang=ALL-UNNAMED -jar app.jar
```

### 3. reflection boundary 예

```java
// opens가 없으면 deep reflection이 실패할 수 있다.
```

### 4. module layer 감각

```java
// 모듈 경계를 런타임에 구성하면 플러그인 격리에 유리하다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| strong encapsulation | 경계가 명확하다 | reflection 호환성 문제가 생길 수 있다 |
| `--add-opens` | 기존 프레임워크를 살리기 쉽다 | 예외를 남용하면 경계가 흐려진다 |
| named modules | 구조가 선명하다 | 패키징과 설정이 복잡해진다 |
| unnamed module | 도입이 쉽다 | 장기적으로 통제가 약하다 |

핵심은 module system을 단순 패키징 기능이 아니라 runtime access boundary 설계로 보는 것이다.

## 꼬리질문

> Q: exports와 opens 차이는 무엇인가요?
> 핵심: exports는 API 노출이고 opens는 reflection용 접근 허용이다.

> Q: 왜 모듈 시스템이 reflection에 중요하나요?
> 핵심: deep reflective access가 런타임 경계를 직접 건드리기 때문이다.

> Q: `--add-opens`는 언제 쓰나요?
> 핵심: 기존 라이브러리나 테스트가 모듈 경계 때문에 깨질 때 제한적으로 쓴다.

## 한 줄 정리

Java module system은 runtime access boundary를 `exports`와 `opens`로 표현하고, reflection 경계는 `--add-opens` 같은 예외로만 넘는 것이 원칙이다.
