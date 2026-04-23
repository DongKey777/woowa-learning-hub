# Skip List

> 한 줄 요약: 스킵 리스트는 여러 수준의 연결 리스트를 쌓아 "빠른 탐색"과 "쉬운 구현"을 동시에 노리는 확률적 정렬 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [Balanced BST vs Unbalanced BST Primer](./balanced-bst-vs-unbalanced-bst-primer.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Concurrent Skip List Internals](./concurrent-skiplist-internals.md)
> - [Graph / 정렬 응용](../algorithm/README.md)

retrieval-anchor-keywords: skip list, probabilistic ordered index, skiplist search insert delete, range query ordered structure, balanced tree alternative, balanced bst alternative, skip list vs bst, unbalanced bst alternative, random level promotion, Redis sorted set intuition, concurrent skip list intuition, sorted set data structure, O(log n) probabilistic search

## 핵심 개념

스킵 리스트는 정렬된 연결 리스트를 기반으로, 일부 노드만 더 높은 레벨로 "건너뛰게" 만든 자료구조다.

- 최하층은 전체 원소를 담는 일반 연결 리스트다.
- 상위 레벨은 하위 레벨의 일부 원소만 건너뛰는 지름길 역할을 한다.
- 탐색은 위에서 아래로, 오른쪽에서 왼쪽으로 진행한다.

평균적으로 탐색/삽입/삭제가 O(log n)이고, 구현이 트리보다 단순한 편이다.

## 깊이 들어가기

### 1. 왜 쓰는가

plain BST는 삽입 순서가 나쁘면 높이가 `O(n)`까지 무너질 수 있고, 균형을 맞추는 트리는 회전/재균형 로직이 들어간다.
스킵 리스트는 같은 ordered search 문제를 더 단순한 "레벨 지름길" 방식으로 풀려는 쪽에 가깝다.

스킵 리스트는 확률적 높이 배치를 사용하므로 구현이 비교적 단순하고,  
정렬된 순서를 유지하면서 range query도 지원하기 쉽다.

### 2. 레벨 생성 방식

각 노드는 동전 던지기 같은 확률로 상위 레벨에 복제된다.

- 1/2 확률로 한 단계 위로 올라간다고 생각할 수 있다.
- 높이가 높을수록 탐색 지름길 역할을 한다.

이 확률 구조 때문에 평균 시간복잡도는 좋지만, 최악의 경우는 O(n)이다.

### 3. 실무에서의 의미

스킵 리스트는 Redis sorted set 구현 아이디어를 이해할 때 자주 등장하고,  
동시성 환경에서 균형 트리보다 구현 단순성이 장점이 된다.

## 실전 시나리오

### 시나리오 1: 정렬된 순서 + 빠른 검색

회원 등급, 포인트, 랭킹처럼 "정렬된 상태를 유지하면서 검색/범위 조회"를 해야 하는 경우가 있다.

스킵 리스트는 정렬 구조를 유지하면서 탐색이 빠르다.

### 시나리오 2: 구현 단순성이 중요한 저장소

트리 회전이나 재균형이 부담스러운 시스템에서는,  
확률적 균형을 쓰는 스킵 리스트가 더 직관적일 수 있다.

## 코드로 보기

```java
import java.util.Random;

class SkipNode {
    int value;
    SkipNode[] next;

    SkipNode(int value, int level) {
        this.value = value;
        this.next = new SkipNode[level + 1];
    }
}

public class SkipList {
    private static final int MAX_LEVEL = 16;
    private final Random random = new Random();
    private final SkipNode head = new SkipNode(Integer.MIN_VALUE, MAX_LEVEL);
    private int level = 0;

    public boolean search(int target) {
        SkipNode current = head;
        for (int i = level; i >= 0; i--) {
            while (current.next[i] != null && current.next[i].value < target) {
                current = current.next[i];
            }
        }
        current = current.next[0];
        return current != null && current.value == target;
    }

    public void insert(int value) {
        SkipNode[] update = new SkipNode[MAX_LEVEL + 1];
        SkipNode current = head;

        for (int i = level; i >= 0; i--) {
            while (current.next[i] != null && current.next[i].value < value) {
                current = current.next[i];
            }
            update[i] = current;
        }

        int newLevel = randomLevel();
        if (newLevel > level) {
            for (int i = level + 1; i <= newLevel; i++) {
                update[i] = head;
            }
            level = newLevel;
        }

        SkipNode node = new SkipNode(value, newLevel);
        for (int i = 0; i <= newLevel; i++) {
            node.next[i] = update[i].next[i];
            update[i].next[i] = node;
        }
    }

    private int randomLevel() {
        int lvl = 0;
        while (lvl < MAX_LEVEL && random.nextBoolean()) {
            lvl++;
        }
        return lvl;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 스킵 리스트 | 구현이 비교적 단순하고 range query가 자연스럽다 | 확률 구조라 최악 보장이 약하다 | 정렬 + 검색 + 범위 조회 |
| 균형 트리 | worst-case 보장이 좋다 | 회전/재균형 구현이 복잡하다 | 강한 보장이 필요할 때 |
| 배열 + 이진 탐색 | 탐색이 빠르고 메모리 연속성이 좋다 | 삽입/삭제가 비싸다 | 읽기 위주일 때 |

## 꼬리질문

> Q: 스킵 리스트가 왜 트리보다 구현이 쉽다고 하나?
> 의도: 자료구조 선택 기준을 구조적 복잡도로 볼 수 있는지 확인
> 핵심: 회전/재균형 대신 확률적 레벨 배치를 쓰기 때문이다.

> Q: 최악의 경우 O(n)인데 왜 실무에서 쓰나?
> 의도: 평균 성능과 엔지니어링 비용의 균형을 이해하는지 확인
> 핵심: 평균적으로 빠르고 구현이 단순하며, 범위 조회와 정렬 유지가 편하다.

## 한 줄 정리

스킵 리스트는 확률적 레벨을 이용해 정렬된 순서를 유지하면서 평균 O(log n) 탐색을 제공하는 구현 친화적 구조다.
