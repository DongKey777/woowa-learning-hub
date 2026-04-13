# Aho-Corasick

> 한 줄 요약: Aho-Corasick은 여러 패턴을 한 번의 텍스트 스캔으로 찾기 위해 trie에 실패 링크를 더한 다중 패턴 매칭 자동자다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Trie (Prefix Search / Autocomplete)](../data-structure/trie-prefix-search-autocomplete.md)
> - [KMP vs Z Algorithm](./kmp-vs-z-algorithm.md)
> - [Suffix Tree Intuition](./suffix-tree-intuition.md)

> retrieval-anchor-keywords: aho-corasick, multiple pattern matching, trie failure link, automaton, keyword search, text scanning, multi-pattern, fail link, spam filter, intrusion detection

## 핵심 개념

Aho-Corasick은 여러 패턴을 동시에 찾는 문자열 매칭 구조다.

- trie로 패턴을 모두 넣는다.
- failure link로 mismatch 시 돌아갈 곳을 정한다.
- 텍스트를 한 번 훑으면서 모든 패턴을 탐지한다.

이게 강한 이유는 패턴 수가 많아질수록 효율이 커지기 때문이다.

## 깊이 들어가기

### 1. 왜 trie가 필요한가

패턴들을 접두사 공유 구조로 넣으면 공통 prefix를 재사용할 수 있다.

### 2. failure link의 역할

현재 노드에서 다음 문자가 맞지 않으면,  
가장 긴 접두사-접미사 일치가 가능한 상태로 점프한다.

이건 KMP의 패턴 실패 이동을 다중 패턴으로 확장한 느낌이다.

### 3. output link

어떤 상태에 도달했을 때 그 상태가 끝나는 패턴을 모두 보고해야 한다.

그래서 한 노드에 여러 패턴 종료 정보가 붙을 수 있다.

### 4. backend에서의 감각

Aho-Corasick은 텍스트 스트리밍 필터링에 매우 잘 맞는다.

- 금칙어 검사
- 시그니처 탐지
- 로그 룰 매칭
- 보안 이벤트 필터

## 실전 시나리오

### 시나리오 1: 금칙어 필터

수만 개 패턴을 매번 하나씩 비교하는 대신 한 번의 스캔으로 검사할 수 있다.

### 시나리오 2: 스팸/시그니처 탐지

여러 탐지 패턴을 동시에 관리할 때 자연스럽다.

### 시나리오 3: 오판

패턴이 하나뿐이면 KMP가 더 간단하다.

### 시나리오 4: 대량 로그 필터

입력 스트림이 길고 패턴이 많을수록 장점이 커진다.

## 코드로 보기

```java
public class AhoCorasickNotes {
    // 설명용 노트: 실제 구현은 trie + failure link + output link가 필요하다.
    public boolean matchesAny(String text, String[] patterns) {
        for (String pattern : patterns) {
            if (text.contains(pattern)) return true;
        }
        return false;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Aho-Corasick | 다중 패턴 매칭에 강하다 | 전처리가 필요하다 | 여러 패턴 탐지 |
| KMP | 단일 패턴에 단순하다 | 다중 패턴에 불리하다 | 한 개 패턴 |
| Rolling Hash | 빠른 후보 필터링 가능 | collision이 있다 | 근사 탐지 |

## 꼬리질문

> Q: Aho-Corasick이 KMP의 확장처럼 보이는 이유는?
> 의도: failure link의 의미를 이해하는지 확인
> 핵심: mismatch 시 가장 긴 접두사-접미사 상태로 돌아가기 때문이다.

> Q: 어떤 상황에 가장 잘 맞나?
> 의도: 다중 패턴 탐지 감각 확인
> 핵심: 금칙어, 시그니처, 로그 룰 매칭이다.

> Q: 패턴이 하나면 왜 과한가?
> 의도: 문제 크기에 맞는 도구 선택 확인
> 핵심: 전처리 비용이 단일 패턴에 비해 불필요할 수 있다.

## 한 줄 정리

Aho-Corasick은 trie와 failure link로 여러 패턴을 한 번의 텍스트 스캔으로 찾는 다중 패턴 매칭 자동자다.
