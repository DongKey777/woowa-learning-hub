# Class Data Sharing and AppCDS

> 한 줄 요약: CDS/AppCDS는 미리 공유 아카이브를 만들어 class metadata와 일부 로딩 비용을 줄여 startup과 footprint를 개선하는 JVM 기능이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)

> retrieval-anchor-keywords: CDS, AppCDS, class data sharing, shared archive, startup time, memory-mapped archive, class loading, archive generation, bootstrap classes, application classes

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

CDS(Class Data Sharing)는 클래스 메타데이터를 공유 아카이브로 만들어 여러 JVM이 재사용할 수 있게 하는 HotSpot 기능이다.  
AppCDS는 여기에 application class까지 확장한 버전이다.

주된 효과:

- startup time 감소
- memory footprint 감소
- 클래스 로딩 비용 일부 절감

## 깊이 들어가기

### 1. 왜 class data sharing이 효과가 있나

class metadata를 매번 새로 만들지 않고 미리 정리된 archive에서 가져오면 초기화 비용과 메모리 사용이 줄어든다.  
특히 대형 애플리케이션에서 수천~수만 개의 클래스를 쓰면 이득이 커질 수 있다.

### 2. AppCDS는 application class를 다룬다

bootstrap class만 공유하는 기본 CDS보다 AppCDS는 더 넓은 범위를 다룬다.  
즉 실무 application의 class loading 경로에 더 직접적으로 도움을 준다.

### 3. 아카이브는 빌드/운영과 연결된다

AppCDS는 보통 dump step이 필요하고, class set이 바뀌면 archive를 다시 만들어야 한다.  
그래서 애플리케이션 배포 프로세스와 연결해서 생각해야 한다.

### 4. startup 최적화와 warmup은 다르다

AppCDS는 class loading을 줄인다.  
하지만 JIT warmup이나 allocation pressure, downstream I/O 병목을 없애는 것은 아니다.

## 실전 시나리오

### 시나리오 1: cold start가 느리다

AppCDS는 startup time을 줄이는 대표적인 선택지다.  
특히 class loading이 많은 서비스에서 고려할 만하다.

### 시나리오 2: 여러 JVM 인스턴스를 띄운다

공유 아카이브를 통해 footprint를 줄일 여지가 있다.  
멀티 인스턴스 환경에서 더 체감될 수 있다.

### 시나리오 3: 배포 후 class set이 자주 바뀐다

아카이브를 자주 재생성해야 하므로 운영 복잡도가 올라간다.  
이 경우 이득과 관리 비용을 같이 봐야 한다.

## 코드로 보기

### 1. archive 생성 흐름 감각

```bash
java -Xshare:off -XX:+UseAppCDS -XX:DumpLoadedClassList=app.lst -cp app.jar Main
```

```bash
java -Xshare:dump -XX:+UseAppCDS -XX:SharedClassListFile=app.lst
```

### 2. runtime 사용 감각

```bash
java -XX:+UseAppCDS -cp app.jar Main
```

### 3. startup 최적화와 함께 볼 것

```java
// class loading은 줄어도
// JIT warmup과 allocation path는 따로 봐야 한다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| CDS/AppCDS | startup과 footprint를 줄일 수 있다 | archive 관리가 필요하다 |
| plain startup | 단순하다 | cold start 비용이 크다 |
| custom class loading | 유연하다 | 복잡도와 누수 위험이 있다 |
| JIT warmup 최적화 | steady state 성능에 좋다 | startup 문제는 직접 못 푼다 |

핵심은 AppCDS를 "성능 마법"이 아니라 "class loading 비용을 선불로 정리하는 도구"로 보는 것이다.

## 꼬리질문

> Q: CDS와 AppCDS 차이는 무엇인가요?
> 핵심: AppCDS는 application class까지 포함하는 확장판이다.

> Q: AppCDS가 startup에 왜 도움이 되나요?
> 핵심: class metadata를 미리 archive해서 로딩 비용을 줄일 수 있기 때문이다.

> Q: AppCDS가 JIT까지 해결하나요?
> 핵심: 아니다. class loading은 줄이지만 warmup과 runtime 최적화는 별개다.

## 한 줄 정리

CDS/AppCDS는 class metadata 공유로 startup과 footprint를 줄이는 기능이고, JIT warmup과는 분리해서 봐야 한다.
