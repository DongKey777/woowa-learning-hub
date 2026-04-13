# Treap vs Skip List

> 한 줄 요약: Treap과 Skip List는 둘 다 확률적으로 균형을 맞춰 정렬 구조를 유지하지만, Treap은 트리 회전이고 Skip List는 레벨 점프다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Skip List](./skip-list.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Order Statistic Tree](./order-statistic-tree.md)

> retrieval-anchor-keywords: treap, skip list, randomized balanced tree, probabilistic balance, rotation, level list, ordered set, range query, expected logarithmic time

## 핵심 개념

둘 다 정렬된 상태를 유지하면서 `search/insert/delete`를 평균적으로 빠르게 만드는 구조다.

- Treap: BST + heap priority
- Skip List: 여러 레벨의 linked list

둘 다 랜덤성이 균형을 만들어 준다.

## 깊이 들어가기

### 1. Treap 감각

Treap은 key는 BST 순서를 따르고, priority는 heap 순서를 따른다.

랜덤 priority 덕분에 회전이 균형을 잡아 준다.

장점:

- 이론과 구현이 비교적 단순하다
- order statistics와 결합하기 좋다

### 2. Skip List 감각

Skip List는 노드가 여러 레벨에 걸쳐 "건너뛰기" 링크를 가진다.

장점:

- 구현이 직관적이다
- range query와 정렬 순회가 자연스럽다

### 3. backend에서의 선택

둘 다 정렬된 key space가 필요할 때 고려된다.

- 메모리 내 ordered set
- range query
- 순위 기반 조회

### 4. 무엇이 다른가

- Treap은 회전이 있어도 트리 구조를 유지한다.
- Skip List는 링크 기반이라 수평 이동과 수직 이동으로 탐색한다.

## 실전 시나리오

### 시나리오 1: range query 중심

범위 조회가 많으면 Skip List의 직관성이 좋다.

### 시나리오 2: subtree aggregate 필요

Treap은 서브트리 크기나 합계를 붙이기 편하다.

### 시나리오 3: 오판

완전 결정론적 worst-case 보장이 필요하면 둘 다 조심해야 한다.

## 코드로 보기

```java
public class TreapVsSkipListNotes {
    public static String choose(boolean treeAugment, boolean simplerPointers) {
        if (treeAugment) return "Treap";
        if (simplerPointers) return "Skip List";
        return "Need a different structure";
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Treap | BST와 heap을 결합해 강력하다 | 회전 구현이 필요하다 | order statistic, split/merge |
| Skip List | 구현이 직관적이다 | 확률적 최악 보장이 약하다 | 정렬 + 범위 조회 |
| Balanced Tree | worst-case가 안정적이다 | 구현이 복잡하다 | 강한 보장이 필요할 때 |

## 꼬리질문

> Q: Treap은 왜 균형이 잡히나?
> 의도: 랜덤 priority의 역할을 아는지 확인
> 핵심: 우선순위가 무작위라 평균적으로 균형이 맞는다.

> Q: Skip List와 가장 큰 차이는?
> 의도: 트리와 linked list의 구조 차이 확인
> 핵심: 하나는 회전 기반 트리, 다른 하나는 레벨 점프다.

> Q: 실무에서 어느 쪽이 더 낫나?
> 의도: 구현/운영 trade-off 이해 확인
> 핵심: 상황에 따라 다르며, 구현 친화성은 Skip List가 좋다.

## 한 줄 정리

Treap과 Skip List는 둘 다 랜덤성으로 정렬 구조의 균형을 맞추지만, Treap은 트리 회전형이고 Skip List는 레벨 점프형이다.
