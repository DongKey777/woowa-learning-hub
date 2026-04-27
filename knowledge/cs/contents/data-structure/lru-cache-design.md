# LRU Cache Design

> 한 줄 요약: 가장 오래 안 쓴 항목부터 버리는 캐시 정책으로, `HashMap`과 이중 연결 리스트 조합이 정석이다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: lru cache design basics, lru cache design beginner, lru cache design intro, data structure basics, beginner data structure, 처음 배우는데 lru cache design, lru cache design 입문, lru cache design 기초, what is lru cache design, how to lru cache design
> 관련 문서:
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Bloom Filter](./bloom-filter.md)
> - [분산 캐시 설계](../system-design/distributed-cache-design.md)

> retrieval-anchor-keywords: lru cache, least recently used, linkedhashmap, hashmap doubly linked list, cache eviction, access order, local cache, bounded cache, eviction policy, locality

## 핵심 개념

LRU(Least Recently Used) 캐시는 "최근에 가장 덜 사용한 항목을 먼저 내보내는" 정책이다.

왜 필요할까?

- 캐시 공간은 항상 제한되어 있다.
- 가장 최근에 쓴 데이터가 앞으로도 다시 쓰일 확률이 높다.
- 지역성(locality)을 활용하면 적은 메모리로 높은 적중률을 얻을 수 있다.

LRU의 핵심은 두 가지다.

- 키로 빠르게 조회할 수 있어야 한다.
- 최근 사용 순서를 빠르게 갱신할 수 있어야 한다.

## 깊이 들어가기

### 1. 왜 `HashMap + Doubly Linked List`인가

`HashMap`은 키 조회가 빠르고, 이중 연결 리스트는 노드를 앞뒤로 옮기기 쉽다.

조합하면 다음 연산을 O(1) 수준으로 만들 수 있다.

- `get(key)`
- `put(key, value)`
- `move-to-front`
- `evict-tail`

### 2. `LinkedHashMap`이 자주 쓰이는 이유

Java에서는 `LinkedHashMap`이 이미 접근 순서 유지와 제거 훅을 제공한다.
직접 구현할 수 있지만, 단순한 로컬 캐시라면 `LinkedHashMap`이 더 실용적이다.

```java
Map<String, String> cache = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 1000;
    }
};
```

`true`는 access-order를 의미한다.
`get()` 호출만으로도 최근 사용 순서가 갱신된다.

### 3. 수동 구현이 필요한 경우

세밀한 정책이 필요할 때는 직접 이중 연결 리스트를 제어하는 편이 낫다.

- TTL과 LRU를 함께 써야 할 때
- 메트릭과 eviction reason을 자세히 남겨야 할 때
- 멀티스레드 제어를 세밀하게 하고 싶을 때

---

## 실전 시나리오

### 시나리오 1: 로컬 핫키 캐시

애플리케이션 레벨에서 자주 읽는 설정값이나 사용자 세션을 캐싱할 때 LRU가 잘 맞는다.

문제는 캐시 크기를 잘못 잡으면 다음이 생긴다.

- 너무 작으면 미스가 많아진다.
- 너무 크면 GC 압박과 메모리 사용량이 커진다.

### 시나리오 2: 잘못된 eviction 정책

LFU가 좋아 보이지만 최근 폭발적인 트래픽 패턴에 약할 수 있다.
반대로 LRU는 "오래된 항목"을 내보내므로 burst 이후 복구가 단순하다.

---

## 코드로 보기

```java
import java.util.HashMap;
import java.util.Map;

public class LruCache<K, V> {
    private final int capacity;
    private final Map<K, Node<K, V>> index = new HashMap<>();
    private final Node<K, V> head = new Node<>(null, null);
    private final Node<K, V> tail = new Node<>(null, null);

    public LruCache(int capacity) {
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public V get(K key) {
        Node<K, V> node = index.get(key);
        if (node == null) return null;
        moveToFront(node);
        return node.value;
    }

    public void put(K key, V value) {
        Node<K, V> node = index.get(key);
        if (node != null) {
            node.value = value;
            moveToFront(node);
            return;
        }

        if (index.size() == capacity) {
            Node<K, V> lru = tail.prev;
            remove(lru);
            index.remove(lru.key);
        }

        Node<K, V> created = new Node<>(key, value);
        index.put(key, created);
        insertFront(created);
    }

    private void moveToFront(Node<K, V> node) {
        remove(node);
        insertFront(node);
    }

    private void remove(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    private void insertFront(Node<K, V> node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }

## 코드로 보기 (계속 2)

private static final class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;

        Node(K key, V value) {
            this.key = key;
            this.value = value;
        }
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| LRU | 구현이 직관적이고 최근성에 강함 | 오래됐지만 자주 쓰는 항목을 내보낼 수 있음 | 일반적인 로컬 캐시 |
| LFU | 자주 쓰는 항목을 오래 보존함 | 구현과 갱신 비용이 복잡함 | 반복 접근이 강한 워크로드 |
| FIFO | 단순함 | 지역성을 거의 활용하지 못함 | 아주 단순한 버퍼 |
| LinkedHashMap | 구현이 쉽고 실수 적음 | 정책을 세밀하게 커스터마이즈하기 어려움 | 빠른 구현이 필요할 때 |

LRU는 만능이 아니다.
트래픽이 갑자기 바뀌는 시스템에서는 TTL, LFU, admission policy를 같이 봐야 한다.

---

## 꼬리질문

> Q: 왜 `HashMap`만으로는 LRU를 만들기 어려운가?
> 의도: 조회와 순서 관리의 두 요구를 분리해서 생각하는지 확인
> 핵심: 순서 갱신이 O(1)이 아니면 캐시 정책이 느려진다.

> Q: `LinkedHashMap`으로 충분한데 굳이 직접 구현하는 경우는 언제인가?
> 의도: 표준 라이브러리와 커스텀 구현의 경계 이해 확인
> 핵심: 관측성, 동시성, TTL 조합, 상세 정책이 필요할 때다.

> Q: LRU가 잘못 맞는 워크로드는 무엇인가?
> 의도: 정책 선택을 상황 기반으로 보는지 확인
> 핵심: 반복적으로 뜨거운 항목과 일시적 버스트가 섞인 경우다.

## 한 줄 정리

LRU 캐시는 최근 사용 순서를 빠르게 갱신해야 하므로, `HashMap`과 이중 연결 리스트의 조합이 표준 해법이다.
