# Compressed Oops and Class Pointers

> 한 줄 요약: compressed oops와 compressed class pointers는 64-bit JVM에서 포인터 표현을 줄여 메모리 효율과 캐시 친화성을 얻는 HotSpot 최적화이지만, heap 크기와 object header 해석을 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Stack vs Heap Escape Intuition](./stack-vs-heap-escape-intuition.md)
> - [Object Layout and JOL Intuition](./object-layout-jol-intuition.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)
> - [Class Data Sharing and AppCDS](./class-data-sharing-appcds.md)

> retrieval-anchor-keywords: compressed oops, class pointer, compressed class pointers, oop, object header, mark word, 64-bit JVM, heap footprint, pointer compression, HotSpot, narrow oop, narrow klass

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

64-bit JVM은 주소 공간이 넓지만, 모든 reference를 64-bit로 그대로 들고 다니면 메모리와 캐시 비용이 커진다.  
그래서 HotSpot은 많은 경우 compressed oops를 사용해 reference를 더 작은 형태로 저장한다.

비슷하게 클래스 메타데이터 참조에도 compressed class pointers가 쓰일 수 있다.

### 왜 이게 중요한가

- heap 사용량이 줄어들 수 있다
- object graph가 더 캐시 친화적이 된다
- object header와 포인터 해석을 이해해야 도구 출력이 덜 헷갈린다

## 깊이 들어가기

### 1. compressed oops는 무엇을 압축하는가

oop는 ordinary object pointer다.  
compressed oops는 이 포인터를 바로 64-bit로 저장하지 않고, 더 작은 표현으로 관리해서 메모리를 아낀다.

즉 "reference가 작아진다"는 것은 주소 공간을 줄이는 것이 아니라 **표현 방식**을 바꾸는 것이다.

### 2. class pointer도 비슷한 최적화가 있다

객체는 자기 class 메타데이터도 참조한다.  
이 class pointer도 compressed representation을 사용할 수 있다.

그래서 object layout을 볼 때는 다음을 같이 봐야 한다.

- mark word
- klass pointer
- instance fields

### 3. 언제 이득이 큰가

- 많은 객체를 오래 들고 있을 때
- reference-heavy object graph일 때
- cache locality가 중요할 때

반대로 이미 메모리 압박이 작거나 객체 수가 적으면 체감이 덜할 수 있다.

### 4. heap 크기와 함께 봐야 한다

compressed oops는 heap 크기에 따라 활성화/비활성화 조건이 달라질 수 있다.  
즉 "같은 JVM"이라도 heap sizing이 바뀌면 포인터 표현과 성능 감각이 달라질 수 있다.

## 실전 시나리오

### 시나리오 1: heap을 키웠더니 메모리 감각이 달라진다

heap 크기 변화는 object layout과 pointer compression의 전제에 영향을 줄 수 있다.  
그래서 단순히 `-Xmx`만 보고 성능을 해석하면 틀릴 수 있다.

### 시나리오 2: object header를 봤는데 숫자가 이상하다

JOL 같은 도구에서 헤더를 해석할 때 compressed klass pointer와 mark word를 구분해야 한다.  
압축 여부를 모르고 보면 layout이 이상해 보일 수 있다.

### 시나리오 3: 캐시 hit가 생각보다 낮다

reference 자체가 더 작아지면 cache density가 좋아질 수 있다.  
물론 애플리케이션의 접근 패턴이 더 중요하지만, heap footprint 최적화는 무시하기 어렵다.

## 코드로 보기

### 1. 객체 수가 많은 구조

```java
import java.util.ArrayList;
import java.util.List;

public class Graph {
    private final List<Node> nodes = new ArrayList<>();

    public void add(Node node) {
        nodes.add(node);
    }

    record Node(String id, List<Node> children) {}
}
```

### 2. 관측 커맨드

```bash
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintFlagsFinal -version | grep UseCompressed
```

### 3. 레이아웃을 읽는 감각

```java
// 객체의 실제 footprint는 fields만이 아니라
// header, klass pointer, alignment, compressed reference 표현에 영향을 받는다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| compressed oops | 메모리와 캐시 효율이 좋아질 수 있다 | 주소 해석이 더 복잡하다 |
| plain 64-bit pointers | 단순하다 | footprint가 커질 수 있다 |
| 큰 heap | 여유가 생긴다 | compression 전제가 달라질 수 있다 |
| 작은 heap | compact하다 | 압박이 빨리 올 수 있다 |

핵심은 포인터 크기를 "구현 디테일"로만 보지 말고 heap footprint와 캐시 효율의 핵심 변수로 보는 것이다.

## 꼬리질문

> Q: compressed oops는 왜 쓰나요?
> 핵심: 64-bit JVM에서 reference 표현을 줄여 메모리와 캐시 효율을 얻기 위해서다.

> Q: class pointer도 압축되나요?
> 핵심: HotSpot은 compressed class pointers를 사용할 수 있다.

> Q: object layout을 볼 때 무엇을 같이 봐야 하나요?
> 핵심: mark word, klass pointer, field alignment, reference 표현을 함께 봐야 한다.

## 한 줄 정리

compressed oops와 compressed class pointers는 64-bit JVM의 메모리 절약 장치이고, object layout과 heap sizing 해석의 기본 전제가 된다.
