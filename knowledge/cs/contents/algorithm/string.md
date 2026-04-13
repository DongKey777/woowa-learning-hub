# 문자열 처리 알고리즘

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: 문자열 알고리즘은 텍스트를 빠르게 찾고, 비교하고, 압축하고, 반복 패턴을 읽어내는 방법을 다룬다.

**난이도: 🟡 Intermediate**

> retrieval-anchor-keywords: string matching, kmp, failure function, prefix function, pattern matching, text search, substring, exact match, rolling hash, aho-corasick, suffix array, backend text processing

<details>
<summary>Table of Contents</summary>

- [KMP 알고리즘 (Knuth-Morris-Pratt Algorithm)](#kmp-알고리즘-knuth-morris-pratt-algorithm)

</details>

---

문자열은 가장 흔한 입력 형태지만, 단순 비교만으로는 금방 느려진다.  
실무에서는 로그, 사용자 입력, 검색어, 식별자, 경로, 시그니처 등으로 등장하고, 문자열 알고리즘은 이들을 효율적으로 다루는 기반이 된다.

- 정확히 같은 패턴을 찾을 때는 KMP, Z, rolling hash를 본다.
- 여러 패턴을 동시에 찾을 때는 Aho-Corasick을 본다.
- 부분 문자열 전체를 구조화할 때는 suffix array/tree/automaton을 본다.

이 문서는 그 출발점으로 KMP를 중심에 두되, 다른 문자열 구조로 이어지는 맥락도 같이 잡아준다.  
관련해서 [KMP vs Z Algorithm](./kmp-vs-z-algorithm.md), [Rolling Hash / Rabin-Karp](./rolling-hash-rabin-karp.md), [Aho-Corasick](./aho-corasick.md), [Suffix Array and LCP](./suffix-array-lcp.md), [Suffix Automaton](./suffix-automaton.md)을 함께 보면 좋다.

---

# 문자열 패턴 매칭

문자열 T 안에 문자열 패턴 P가 있는지 찾는 문제는 매우 흔하다.

- 로그에서 특정 에러 문자열 찾기
- 정책 위반 문구 필터링
- 검색어 자동 완성 전처리
- 문서 내 서명/토큰 탐색

완전탐색은 가장 직관적이지만, 텍스트가 길고 패턴이 많아질수록 비효율적이다.

## 왜 문자열은 특별한가

문자열은 단순 배열처럼 보이지만, 다음 특성이 자주 섞인다.

- 접두사/접미사 관계
- 반복 패턴
- 정규화 전후 비교
- 대소문자/공백/구두점 차이

이 때문에 문자열 알고리즘은 단순한 `equals()`보다 더 많은 정보를 재사용하려고 한다.

### 실무 감각

- 검색 시스템: 검색어 prefix, n-gram, autocomplete
- 보안/필터링: 금칙어, 시그니처, 룰 매칭
- 데이터 분석: 반복 템플릿, 중복 로그, 패턴 클러스터링

---

## KMP 알고리즘 (Knuth-Morris-Pratt Algorithm)

완전탐색에서 버려지는 정보는 "어디까지 일치했는가"이다.  
KMP는 이 정보를 `fail` 배열에 저장해, 불일치가 생겨도 텍스트 포인터를 되돌리지 않고 패턴 포인터만 점프한다.

즉 KMP는 **텍스트 재검사를 줄이는 알고리즘**이다.

### 알고리즘 설계 및 구현

1. 패턴 P에 대해 `fail[k]`를 계산한다.
2. 텍스트 T와 패턴 P를 한 방향으로 비교한다.
3. 불일치가 나면 `j = fail[j-1]`로 이동한다.

### 실패함수 fail 만들기

`fail[i]`는 `P[0..i]`의 접두사와 접미사가 가장 길게 일치하는 길이다.

- `fail[0] = 0`
- 같은 문자를 만나면 접두사 길이를 늘린다.
- 불일치하면 이전 fail 값으로 돌아간다.

### 왜 빠른가

패턴이 한 번 밀려난 뒤 다시 처음부터 비교하지 않는다.  
이 점이 KMP의 핵심이며, 전체 시간복잡도가 `O(T+P)`가 되는 이유다.

### backend에서의 감각

KMP는 "한 패턴을 길게 스캔하는" 상황에 특히 잘 맞는다.

- 로그 필터링
- 파일 내 시그니처 탐지
- 에디터/IDE 내부 패턴 검색
- 프로토콜 문자열 검사

### 실전 시나리오

#### 시나리오 1: 에러 문자열 탐지

긴 로그 파일에서 특정 에러 문자열이 포함됐는지 빠르게 확인할 수 있다.

#### 시나리오 2: 금칙어 필터의 일부

패턴이 하나이거나 소수일 때는 KMP가 단순하고 안정적이다.

#### 시나리오 3: 오판

패턴이 매우 많다면 KMP를 패턴 수만큼 반복하는 것은 비효율적이다.  
그럴 때는 [Aho-Corasick](./aho-corasick.md)이 더 자연스럽다.

### 코드로 보기

```java
public class KMPTest {

    public static int[] buildFail(String pattern) {
        int[] fail = new int[pattern.length()];
        int j = 0;

        for (int i = 1; i < pattern.length(); i++) {
            while (j > 0 && pattern.charAt(i) != pattern.charAt(j)) {
                j = fail[j - 1];
            }

            if (pattern.charAt(i) == pattern.charAt(j)) {
                fail[i] = ++j;
            }
        }
        return fail;
    }

    public static int find(String text, String pattern) {
        if (pattern.isEmpty()) return 0;

        int[] fail = buildFail(pattern);
        int j = 0;

        for (int i = 0; i < text.length(); i++) {
            while (j > 0 && text.charAt(i) != pattern.charAt(j)) {
                j = fail[j - 1];
            }

            if (text.charAt(i) == pattern.charAt(j)) {
                if (j == pattern.length() - 1) {
                    return i - pattern.length() + 1;
                }
                j++;
            }
        }
        return -1;
    }
}
```

### 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| KMP | collision 없이 정확하다 | 단일 패턴 중심이다 | 정확한 패턴 매칭 |
| Rolling Hash | 후보 필터가 빠르다 | collision 가능성이 있다 | 빠른 substring 후보 제거 |
| Aho-Corasick | 다중 패턴에 강하다 | 전처리가 필요하다 | 패턴이 많을 때 |

### 꼬리질문

> Q: KMP가 왜 텍스트를 되돌아보지 않나요?
> 의도: fail 배열의 역할을 이해하는지 확인
> 핵심: 이미 일치한 prefix 정보를 패턴 쪽으로 재활용하기 때문이다.

> Q: fail 배열이 의미하는 것은 무엇인가요?
> 의도: prefix/suffix 일치 개념 확인
> 핵심: 현재까지 본 패턴에서 다시 시작할 수 있는 가장 긴 접두사 길이다.

> Q: 패턴이 여러 개면 어떻게 하나요?
> 의도: 다중 패턴 매칭 구조로 확장할 수 있는지 확인
> 핵심: Aho-Corasick 같은 다중 패턴 자동자를 고려한다.

---

## 문자열 알고리즘의 큰 그림

문자열 문제는 "어떤 정보를 재사용할 수 있는가"를 찾는 문제다.

- 접두사 재사용 -> KMP, Z
- 후보 필터링 -> rolling hash
- 다중 패턴 -> Aho-Corasick
- 정적 substring 인덱스 -> suffix array/tree
- substring 공간 압축 -> suffix automaton

### backend angle

실서비스 텍스트는 종종 정규화가 필요하다.

- 공백/대소문자/특수문자 정리
- 로그 토큰화
- 경로 prefix 검사
- 시그니처 룰 매칭

그래서 문자열 알고리즘은 단순 정답 풀이보다 "전처리 파이프라인"과 함께 읽어야 한다.

## 한 줄 정리

문자열 알고리즘은 텍스트에서 반복과 접두사 정보를 재사용해 검색과 매칭 비용을 줄이는 도구이며, KMP는 그 가장 기본적인 출발점이다.
