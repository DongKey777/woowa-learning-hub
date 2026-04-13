# ClassLoader Delegation Edge Cases

> 한 줄 요약: parent delegation은 기본 원칙이지만 webapp classloader, child-first loaders, service loading, deadlock avoidance 같은 edge case에서는 delegation 순서와 lookup scope가 결과를 크게 바꾼다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [Java Module System Runtime Boundaries](./java-module-system-runtime-boundaries.md)
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)
> - [Class Initialization Ordering](./class-initialization-ordering.md)

> retrieval-anchor-keywords: classloader delegation, parent delegation, child-first, delegation edge case, service loader, context class loader, webapp classloader, deadlock, loadClass, findClass, bootstrap, visibility boundary

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄 정리)

</details>

## 핵심 개념

Java class loading은 보통 parent delegation model을 따른다.  
즉 먼저 부모에게 찾게 하고, 못 찾으면 자기 로더가 찾는다.

하지만 현실의 framework와 application server는 이 단순 모델에서 벗어나는 edge case가 많다.

## 깊이 들어가기

### 1. child-first는 왜 존재하나

webapp나 plugin system에서는 자기 버전의 라이브러리를 우선해야 할 때가 있다.  
이 경우 child-first 또는 local-first 전략을 쓰기도 한다.

### 2. service loading은 context classloader와 얽힌다

`ServiceLoader`나 SPI는 context classloader를 활용할 수 있다.  
그래서 "어디서 class를 찾는가"가 단순 parent delegation만으로 설명되지 않는다.

### 3. delegation은 deadlock 문제와도 연결된다

서로 다른 loader가 서로의 클래스 로딩을 기다리면 deadlock이 생길 수 있다.  
특히 동시 로딩과 상호 참조가 섞이면 더 위험하다.

### 4. bootstrap / platform / application 경계도 중요하다

기본 로더 계층을 건드릴 때는 클래스 가시성 범위와 native/library 경계도 같이 봐야 한다.

### 5. webapp loader는 예외가 많다

web container는 보통 웹 애플리케이션 격리 때문에 child-first에 가까운 전략을 쓸 수 있다.  
이건 일반 Java application과 다르다.

## 실전 시나리오

### 시나리오 1: 같은 클래스 이름인데 다른 버전이 로딩된다

child-first나 classpath 충돌을 의심한다.  
모듈 경계와도 연결해 봐야 한다.

### 시나리오 2: SPI가 못 찾아진다

context classloader 설정을 본다.  
로더가 다르면 `ServiceLoader` 결과도 달라질 수 있다.

### 시나리오 3: redeploy 후 이상 동작이 생긴다

loader leak뿐 아니라 delegation 경계가 바뀌며 이전 클래스가 남아 있을 수 있다.  
parent delegation과 webapp loader 규칙을 같이 본다.

## 코드로 보기

### 1. 기본 loadClass 감각

```java
// 부모가 먼저 찾고, 못 찾으면 findClass로 내려간다.
```

### 2. child-first 냄새

```java
// 일부 webapp/plugin loader는 local class를 먼저 보게 설계할 수 있다.
```

### 3. context classloader 감각

```java
Thread.currentThread().setContextClassLoader(loader);
```

### 4. deadlock을 경계해야 한다

```java
// 서로 의존하는 custom classloader를 동시 로딩하면 교착이 생길 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| parent-first delegation | 충돌이 적고 예측 가능하다 | local override가 어렵다 |
| child-first delegation | 버전 분리가 유리하다 | 충돌과 디버깅이 어려울 수 있다 |
| context classloader 사용 | SPI/플러그인에 유연하다 | 어디서 로딩되는지 복잡해진다 |
| 단일 loader | 단순하다 | 격리가 약하다 |

핵심은 classloader delegation을 단순 교과서 모델이 아니라 현실의 로더/컨테이너/플러그인 경계 문제로 보는 것이다.

## 꼬리질문

> Q: parent delegation은 왜 기본인가요?
> 핵심: 클래스 중복과 충돌을 줄이고 로딩을 예측 가능하게 만들기 때문이다.

> Q: child-first는 언제 쓰나요?
> 핵심: 웹앱이나 플러그인처럼 로컬 버전을 우선해야 할 때다.

> Q: context classloader는 왜 중요하나요?
> 핵심: SPI와 런타임 로딩 범위가 현재 thread의 context에 의존할 수 있기 때문이다.

## 한 줄 정리

ClassLoader delegation은 기본적으로 parent-first지만, webapp, plugin, SPI, deadlock 회피 같은 edge case에서는 로딩 순서와 context classloader가 결과를 바꾼다.
