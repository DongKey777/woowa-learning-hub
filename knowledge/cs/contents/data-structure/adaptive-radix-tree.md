# Adaptive Radix Tree

> 한 줄 요약: Adaptive Radix Tree(ART)는 radix tree의 prefix 압축에 노드 크기 적응 전략을 결합해, in-memory ordered index를 cache-friendly하게 만들려는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Radix Tree (Compressed Trie)](./radix-tree.md)
> - [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
> - [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md)
> - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)
> - [B+Tree vs LSM-Tree](../database/bptree-vs-lsm-tree.md)

> retrieval-anchor-keywords: adaptive radix tree, ART, compressed trie, node4 node16 node48 node256, prefix compression, in-memory index, point lookup, range scan, cache-friendly tree, ordered key-value index

## 핵심 개념

ART는 "문자 단위 Trie"보다 메모리를 아끼고, "일반 Radix Tree"보다 CPU cache 친화적으로 만들려는 ordered index 구조다.

핵심 아이디어는 세 가지다.

- prefix compression으로 긴 공통 경로를 줄인다
- fan-out 크기에 따라 node representation을 바꾼다
- key 순서를 유지해 range scan도 가능하게 한다

즉 `HashMap`처럼 exact lookup만 빠른 구조가 아니라,  
**정렬 순서가 있는 in-memory index**를 더 촘촘하게 구현하려는 발상이다.

## 깊이 들어가기

### 1. 왜 일반 Radix Tree에서 한 걸음 더 가나

Radix Tree만으로도 prefix 압축은 가능하지만, 각 노드가 자식 포인터를 넉넉하게 들고 있으면  
fan-out이 작은 구간에서 메모리 낭비가 커진다.

ART는 자식 수에 따라 노드 타입을 바꾼다.

- Node4: 자식이 아주 적을 때
- Node16: 조금 더 많을 때
- Node48: key index table로 중간 fan-out 처리
- Node256: 거의 꽉 찬 fan-out일 때 direct indexing

즉 sparse 구간에서는 compact하게, dense 구간에서는 lookup 친화적으로 행동한다.

### 2. node 적응이 cache locality를 만든다

일반 trie는 null 포인터가 많은 넓은 배열을 들고 있기 쉽다.  
ART는 작은 노드에서는 key 배열과 child 배열을 촘촘히 들고 있어 cache line 낭비를 줄인다.

이 차이가 중요한 이유는 in-memory index 병목이 종종 알고리즘 차수보다  
**pointer chasing과 cache miss**에서 오기 때문이다.

### 3. prefix compression과 lazy expansion

ART는 긴 단일 경로를 node마다 다 펼치지 않고, prefix를 압축해 저장한다.  
조회 시에는 압축 prefix를 한 번에 비교하고, 분기가 생길 때만 노드를 펼친다.

이 방식은 다음에 유리하다.

- 긴 문자열 키
- 공통 prefix가 많은 키
- sparse한 중간 단계

다만 삭제와 split 로직은 더 복잡해진다.  
압축된 prefix를 다시 나누고, node 타입 승격/강등도 고려해야 한다.

### 4. ordered index라는 점이 중요하다

ART는 해시 기반 구조가 아니므로 key 순서를 잃지 않는다.

- exact lookup
- prefix 탐색
- lexicographic range scan

이 세 가지를 한 구조에서 다루기 쉽다.  
그래서 메모리 내 key-value store, secondary index, router table 같은 곳에서 매력적이다.

### 5. backend에서의 함정

ART를 실전에 넣을 때는 자료구조 그 자체보다 운영 세부가 어렵다.

- 문자열/바이너리 키를 어떤 바이트 순서로 normalize할지
- 가변 길이 key의 종료 sentinel을 어떻게 표현할지
- concurrent update 시 memory reclamation을 어떻게 할지
- path compression과 range scan을 함께 어떻게 유지할지

즉 ART는 "빠른 Trie"라기보다 **고성능 in-memory ordered index 엔진 부품**에 가깝다.

## 실전 시나리오

### 시나리오 1: 메모리 기반 키-값 인덱스

정렬 순서와 prefix scan이 모두 필요하지만, B+Tree page 구조까지 가기엔 너무 무거운 in-memory index에서 잘 맞는다.

### 시나리오 2: 설정 키 / feature flag prefix 탐색

`payment.retry.*`, `feature.checkout.*` 같은 계층형 키를 exact lookup과 prefix enumerate 둘 다 해야 할 때 유용하다.

### 시나리오 3: 라우팅 / longest-prefix-near lookup

압축 trie 계열이 필요한 라우팅 문제에서, fan-out 분포가 고르지 않다면 adaptive node 전략이 도움이 된다.

### 시나리오 4: 부적합한 경우

정렬 순서가 필요 없고 단순 key lookup만 중요하면 `HashMap`이 더 단순하다.  
디스크 page 관리가 핵심이면 B+Tree 같은 storage-aware 구조가 더 적합하다.

## 코드로 보기

```java
import java.util.Arrays;

abstract class ArtNode {
    byte[] compressedPrefix = new byte[0];
    int childCount;

    abstract ArtNode findChild(byte keyByte);
    abstract ArtNode addChild(byte keyByte, ArtNode child);
}

final class Node4 extends ArtNode {
    private final byte[] keys = new byte[4];
    private final ArtNode[] children = new ArtNode[4];

    @Override
    ArtNode findChild(byte keyByte) {
        for (int i = 0; i < childCount; i++) {
            if (keys[i] == keyByte) {
                return children[i];
            }
        }
        return null;
    }

    @Override
    ArtNode addChild(byte keyByte, ArtNode child) {
        if (childCount < 4) {
            keys[childCount] = keyByte;
            children[childCount] = child;
            childCount++;
            return this;
        }

        Node16 upgraded = new Node16();
        upgraded.compressedPrefix = Arrays.copyOf(compressedPrefix, compressedPrefix.length);
        for (int i = 0; i < childCount; i++) {
            upgraded.addChild(keys[i], children[i]);
        }
        upgraded.addChild(keyByte, child);
        return upgraded;
    }
}

final class Node16 extends ArtNode {
    private final byte[] keys = new byte[16];
    private final ArtNode[] children = new ArtNode[16];

    @Override
    ArtNode findChild(byte keyByte) {
        for (int i = 0; i < childCount; i++) {
            if (keys[i] == keyByte) {
                return children[i];
            }
        }
        return null;
    }

    @Override
    ArtNode addChild(byte keyByte, ArtNode child) {
        keys[childCount] = keyByte;
        children[childCount] = child;
        childCount++;
        return this;
    }
}

final class LeafNode extends ArtNode {
    final byte[] fullKey;
    final String value;

    LeafNode(byte[] fullKey, String value) {
        this.fullKey = fullKey;
        this.value = value;
    }

    @Override
    ArtNode findChild(byte keyByte) {
        return null;
    }

    @Override
    ArtNode addChild(byte keyByte, ArtNode child) {
        throw new UnsupportedOperationException("leaf node");
    }
}
```

이 코드는 node 적응 아이디어만 보여준다.  
실제 ART는 Node48/Node256, prefix split, leaf shortcut, range iteration까지 포함한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Adaptive Radix Tree | ordered lookup, prefix scan, cache locality를 함께 노릴 수 있다 | 구현과 동시성, 메모리 회수가 복잡하다 | in-memory ordered index가 필요할 때 |
| 일반 Radix Tree | prefix 압축 개념이 단순하다 | fan-out 밀도 변화에 덜 적응적이다 | prefix 구조는 필요하지만 구현 단순성이 더 중요할 때 |
| HashMap | exact lookup이 빠르고 단순하다 | 정렬 순서와 range scan이 약하다 | 단건 조회 중심일 때 |
| B+Tree | disk/page 친화적이고 범위 조회에 강하다 | in-memory pointer cost와 page 관리가 더 무겁다 | storage engine이나 page 기반 인덱스일 때 |

핵심은 ART가 "Trie 대체재"라기보다 "메모리 안의 ordered index"라는 점이다.

## 꼬리질문

> Q: ART가 일반 Trie보다 나은 가장 큰 이유는 무엇인가?
> 의도: 압축과 adaptive node 전략을 함께 이해하는지 확인
> 핵심: prefix compression과 node size 적응으로 메모리와 cache miss를 줄이기 때문이다.

> Q: 왜 `Node4`, `Node16`, `Node48`, `Node256`처럼 여러 노드 타입이 필요한가?
> 의도: fan-out 분포에 대한 감각 확인
> 핵심: 자식 수가 적은 노드와 많은 노드의 최적 표현이 다르기 때문이다.

> Q: HashMap 대신 ART를 고르는 상황은 언제인가?
> 의도: ordered index의 의미 이해 확인
> 핵심: prefix 탐색, range scan, 정렬 순서 유지가 함께 필요할 때다.

## 한 줄 정리

Adaptive Radix Tree는 prefix 압축과 fan-out 적응을 결합해, 메모리 안에서 정렬된 키 인덱스를 효율적으로 다루려는 고성능 radix 계열 자료구조다.
