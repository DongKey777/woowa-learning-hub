# Interval Tree

> 한 줄 요약: Interval Tree는 구간이 서로 겹치는지 빠르게 찾기 위해, 중앙 기준으로 구간을 분할해 저장하는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md)
> - [Binary Search Patterns](../algorithm/binary-search-patterns.md)
> - [Rate Limiter Algorithms](../algorithm/rate-limiter-algorithms.md)

> retrieval-anchor-keywords: interval tree, overlap query, range overlap, scheduling conflict, time window, center splitting, calendar booking, interval search, boundary query

## 핵심 개념

Interval Tree는 여러 구간 `[start, end]`를 저장해 두고,  
새 구간이 기존 구간과 겹치는지 빠르게 찾는 자료구조다.

이 구조가 필요한 대표 상황은 다음과 같다.

- 예약 시간 충돌 검사
- 작업 실행 시간 겹침 검사
- 리소스 점유 구간 관리
- 캘린더 이벤트 중복 탐지

## 깊이 들어가기

### 1. 왜 단순 선형 검색이 부족한가

구간이 많으면 새 구간 하나를 넣을 때마다 모든 기존 구간과 비교해야 할 수 있다.

이건 데이터가 적을 때는 괜찮지만, 예약 시스템이나 타임라인 분석처럼 구간이 쌓이면 비싸다.

### 2. center split의 감각

Interval Tree는 보통 중앙 기준점을 잡고, 그 기준을 가로지르는 구간은 현재 노드에 저장한다.

- 왼쪽에만 있는 구간은 왼쪽 서브트리
- 오른쪽에만 있는 구간은 오른쪽 서브트리
- 가운데를 가로지르는 구간은 현재 노드

이렇게 하면 overlap query를 때 구간이 갈라지는 범위를 줄일 수 있다.

### 3. overlap query가 핵심이다

질의는 보통 "이 구간과 겹치는 아무 구간이 있는가" 또는 "겹치는 모든 구간을 찾아라"다.

이때 기준점과 현재 노드에 저장된 구간만 잘 보면, 불필요한 전체 탐색을 피할 수 있다.

### 4. backend에서 유용한 이유

겹침 검사는 예약/배정/시간표 문제의 핵심이다.

- 회의실 예약
- 광고 슬롯 배치
- 작업 스케줄 충돌
- 부하 발생 구간 겹침

이런 문제는 사실상 "구간 충돌 데이터베이스"를 만드는 것과 비슷하다.

## 실전 시나리오

### 시나리오 1: 캘린더 중복 예약

새 이벤트를 넣을 때 기존 이벤트와 겹치는지 빠르게 확인할 수 있다.

### 시나리오 2: 작업 시간 충돌

서버 점검 창, 배포 시간, 백업 시간처럼 시간이 겹치면 안 되는 작업에 유용하다.

### 시나리오 3: 오판

단순히 최소/최대만 관리하는 문제라면 interval tree는 과하다.  
그땐 TreeMap이나 sweep line이 더 적합할 수 있다.

### 시나리오 4: 대량 데이터

겹침이 많고 질의가 많을수록 interval tree의 가치가 커진다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class IntervalTree {
    private static final class Interval {
        final int start;
        final int end;

        Interval(int start, int end) {
            this.start = start;
            this.end = end;
        }

        boolean overlaps(int s, int e) {
            return start <= e && s <= end;
        }
    }

    private static final class Node {
        final int center;
        final List<Interval> intervals = new ArrayList<>();
        Node left;
        Node right;

        Node(int center) {
            this.center = center;
        }
    }

    private final Node root;

    public IntervalTree(int center) {
        this.root = new Node(center);
    }

    public boolean overlaps(int start, int end) {
        return overlaps(root, start, end);
    }

    private boolean overlaps(Node node, int start, int end) {
        if (node == null) return false;
        for (Interval interval : node.intervals) {
            if (interval.overlaps(start, end)) return true;
        }
        if (end < node.center) return overlaps(node.left, start, end);
        if (start > node.center) return overlaps(node.right, start, end);
        return overlaps(node.left, start, end) || overlaps(node.right, start, end);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Interval Tree | overlap 질의에 강하다 | 구현이 복잡하다 | 시간/범위 충돌 검사 |
| TreeMap | 정렬과 경계 탐색이 쉽다 | 겹침 전체 탐색은 약하다 | 시작/끝 경계만 볼 때 |
| Segment Tree | 구간 합/최대 같은 집계에 강하다 | interval overlap과는 목적이 다르다 | 수치 집계 위주일 때 |

Interval Tree는 "범위가 겹치는가"에 특화된 구조다.

## 꼬리질문

> Q: 왜 center split이 유리한가?
> 의도: 구간 분할 전략을 이해하는지 확인
> 핵심: 겹치는 구간을 현재 노드에 모아 탐색 범위를 줄이기 때문이다.

> Q: Segment Tree와 뭐가 다른가?
> 의도: 범위 집계와 범위 충돌의 차이 이해 확인
> 핵심: Segment Tree는 값 집계, Interval Tree는 구간 겹침 검색이다.

> Q: 어디에 실무적으로 쓰이나?
> 의도: 예약/배치 문제 연결 확인
> 핵심: 캘린더, 스케줄러, 리소스 예약이다.

## 한 줄 정리

Interval Tree는 시간/범위가 겹치는지 빠르게 판정하기 위해 구간을 중심 기준으로 저장하는 자료구조다.
