# ABA Problem and Tagged Pointers

> 한 줄 요약: ABA 문제는 lock-free CAS가 "값이 다시 같아졌으니 안전하다"고 오판하는 상황이며, tagged pointer나 sequence number는 세대 정보를 붙여 이런 재사용 착시를 줄이는 대표 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bounded MPMC Queue](./bounded-mpmc-queue.md)
> - [Sequencer-Based Ring Buffer Coordination](./sequencer-based-ring-buffer-coordination.md)
> - [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md)
> - [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md)
> - [Reclamation Cost Trade-offs](./reclamation-cost-tradeoffs.md)

> retrieval-anchor-keywords: aba problem, tagged pointer, versioned pointer, versioned index, sequence number as tag, lock-free cas bug, pointer reuse race, lock-free memory safety, compare and swap aba, stamped reference, concurrent pointer versioning, slot generation counter, ring buffer wraparound bug, nonblocking algorithm pitfall

## 핵심 개념

CAS는 "지금 읽은 값과 메모리 값이 같으면 안전하다"는 가정 위에 선다.  
ABA 문제는 이 가정이 깨지는 순간이다.

- thread A가 포인터 값을 읽음: `A`
- 다른 thread가 `A -> B -> A`로 바꿈
- thread A는 여전히 `A`를 보므로 안전하다고 착각

즉 값이 다시 같아졌다고 해서,  
**그 사이에 아무 일도 없었다는 뜻은 아니다**.

## 깊이 들어가기

### 1. 왜 lock-free 구조에서 치명적인가

linked stack, queue, free list는 포인터를 CAS로 많이 갱신한다.  
이때 node가 제거됐다가 재사용되면 pointer 값만 보고는 변화를 놓칠 수 있다.

대표 위험:

- stale next pointer
- double unlink
- reclaimed node reuse
- broken logical ordering

즉 ABA는 correctness bug이면서 memory safety bug로 이어질 수 있다.

핵심은 "같은 값"이 아니라  
**같은 identity와 같은 시점이 맞는가**다.

### 2. tagged pointer는 세대(version)를 같이 비교한다

가장 대표적인 완화책은 pointer에 version/stamp를 붙이는 것이다.

- `(ptr, version)`을 함께 CAS
- pointer 값이 같아도 version이 다르면 실패

그래서 `A -> B -> A`가 일어나도

- pointer는 `A`
- version은 증가

하게 만들어 "같아 보이는 착시"를 줄인다.

배열 기반 구조에선 꼭 pointer가 아니어도 된다.

- `(index, lap)` 조합
- slot sequence
- publish version

같이 **세대가 붙은 위치 정보**도 같은 역할을 한다.

### 3. bounded ring도 ABA 모양의 문제를 겪는다

"ABA는 linked list 전용 문제"라고 생각하면 위험하다.

bounded ring에서도 raw index만 보면 비슷한 착시가 생긴다.

- producer가 index `5`를 봄
- ring이 한 바퀴 돌아 다시 index `5`를 재사용
- 값은 같은 index `5`지만 slot의 의미는 이전 회차와 다름

그래서 bounded MPMC queue가 slot마다 sequence를 두는 것이다.

- `5`라는 index만 비교하지 않고
- `5`의 몇 번째 reuse 세대인지까지 본다

즉 per-slot sequence는 anti-ABA 성격의 generation tag다.  
sequencer cursor 역시 단순 배열 위치가 아니라 진행 세대를 표현한다.

### 4. tagged pointer가 만능은 아니다

ABA를 완화한다고 memory reclamation이 해결되진 않는다.

- tagged pointer: 재사용 착시 감지
- hazard pointer / EBR: 언제 free해도 안전한지 관리

즉 tagged pointer는 reclamation 대체재가 아니라  
**다른 종류의 문제를 줄이는 보조 기법**이다.

### 5. reclamation이 섞이면 더 위험해진다

ABA가 특히 위험해지는 순간은 object reuse가 빨라질 때다.

- freelist에서 방금 제거한 node를 즉시 재할당
- queue payload가 pooled descriptor를 재사용
- off-heap/native node를 짧은 주기로 돌려씀

이 경우 값이 다시 같아질 확률이 커지고,  
잘못 성공한 CAS는 stale pointer를 구조 내부로 되돌려놓을 수 있다.

그래서 실전 lock-free 구조는 보통 둘을 같이 본다.

- version tag로 "같아 보이는 착시"를 줄임
- safe reclamation으로 "아직 보면 안 되는 객체"를 늦게 회수

### 6. GC 언어에서도 개념은 중요하다

GC가 있으면 free/use-after-free 리스크는 줄지만,  
CAS linearization bug 자체가 사라지는 것은 아니다.

특히:

- stamped reference
- versioned index
- sequence number

같은 패턴은 JVM에서도 여전히 의미가 있다.

### 7. backend에서 어디에 맞나

ABA는 락프리 자료구조와 freelist/reuse path에 특히 민감하다.

- lock-free stack/list
- node pool 재사용
- intrusive queue
- bounded ring의 slot generation
- native runtime scheduler

즉 "값이 같으니 괜찮다"는 CAS 감각을 경계하게 만드는 기본 문서에 가깝다.

## 실전 시나리오

### 시나리오 1: freelist 재사용

node를 반환 후 곧바로 다시 할당하는 패턴이 있으면  
pointer reuse 때문에 ABA 위험이 커진다.

### 시나리오 2: lock-free stack

top pointer CAS 기반 구조는  
ABA 예시로 가장 자주 등장하는 고전 케이스다.

### 시나리오 3: queue next pointer race

MS Queue류 구조에서 reclamation과 재사용이 섞이면  
ABA와 safe reclamation을 동시에 봐야 한다.

### 시나리오 4: bounded ring slot reuse

배열 index만 보면 같은 slot처럼 보여도  
실제로는 몇 바퀴를 돌았는지에 따라 의미가 달라진다.  
이때 sequence/lap counter가 없으면 stale 판단이 들어오기 쉽다.

### 시나리오 5: 부적합한 이해

"GC 있으니 ABA는 없다"는 식의 이해가 가장 위험하다.  
free 문제와 CAS 선형화 문제는 층위가 다르다.

## 코드로 보기

```java
import java.util.concurrent.atomic.AtomicStampedReference;

public class TaggedPointerSketch<E> {
    private final AtomicStampedReference<Node<E>> head =
            new AtomicStampedReference<>(null, 0);

    public void push(Node<E> node) {
        while (true) {
            int[] stampHolder = new int[1];
            Node<E> current = head.get(stampHolder);
            node.next = current;
            int stamp = stampHolder[0];
            if (head.compareAndSet(current, node, stamp, stamp + 1)) {
                return;
            }
        }
    }

    static final class Node<E> {
        E value;
        Node<E> next;
    }
}
```

이 코드는 stamped pointer 감각만 보여준다.  
실전 native 구조에선 wider CAS, tagged pointer packing, ring slot sequence, reclamation 전략까지 같이 봐야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Tagged Pointer / Stamped Reference | ABA 착시를 줄일 수 있다 | pointer 외 메타데이터 관리가 필요하다 | CAS 기반 pointer update |
| Sequence Number / Versioned Index | 배열 slot 재사용과 wraparound를 세대 단위로 구분할 수 있다 | sequence protocol 설계가 복잡하다 | bounded ring, sequencer |
| Hazard Pointer / EBR | safe free 시점을 관리한다 | ABA 자체를 직접 해결하진 않는다 | memory reclamation 문제 |
| Lock 기반 구조 | reasoning이 단순해진다 | contention 비용이 커질 수 있다 | correctness가 더 중요할 때 |

중요한 질문은 "CAS가 같은 값을 봤다"가 아니라  
"그 사이에 값이 다른 상태를 거쳤는가", "같은 index/pointer가 몇 번째 세대인가"다.

## 꼬리질문

> Q: ABA가 왜 단순히 값 비교 문제를 넘어서 위험한가요?
> 의도: pointer reuse와 stale state 문제를 이해하는지 확인
> 핵심: 값이 다시 같아져도 그 사이 구조가 바뀌었을 수 있어 CAS가 잘못 성공할 수 있기 때문이다.

> Q: bounded ring의 slot sequence도 tagged pointer와 같은 계열인가요?
> 의도: pointer ABA와 generation counter를 연결하는지 확인
> 핵심: 그렇다. pointer 대신 slot index에 세대 정보를 붙여 wraparound 재사용을 구분하는 anti-ABA 기법으로 볼 수 있다.

> Q: tagged pointer가 reclamation을 대체하나요?
> 의도: ABA 방지와 safe free를 구분하는지 확인
> 핵심: 아니다. tagged pointer는 재사용 착시를 줄이고, reclamation은 free 시점을 관리한다.

> Q: GC 언어에서도 왜 stamped reference가 나오나요?
> 의도: memory safety와 linearization bug를 구분하는지 확인
> 핵심: free는 막아줘도 CAS의 중간 상태 착각은 막아주지 않기 때문이다.

## 한 줄 정리

ABA 문제는 CAS가 값의 동일성만 보고 구조적 변화를 놓치는 현상이고, tagged pointer나 sequence number는 그 착시를 줄이는 대표적인 세대 표식 기법이다.
