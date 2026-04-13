# KMP vs Z Algorithm

> 한 줄 요약: KMP는 패턴 실패 지점을 기억하고, Z 알고리즘은 각 위치에서 접두사와 얼마나 길게 일치하는지 계산한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [문자열 처리 알고리즘](./string.md)
> - [Suffix Array and LCP](./suffix-array-lcp.md)
> - [Rolling Hash / Rabin-Karp](./rolling-hash-rabin-karp.md)

> retrieval-anchor-keywords: kmp, z algorithm, prefix function, failure function, pattern matching, string matching, exact match, linear time string search, prefix comparison

## 핵심 개념

두 알고리즘 모두 문자열 매칭을 선형 시간에 해결한다.

- KMP: 패턴의 prefix/suffix 정보를 이용한다.
- Z: 문자열의 각 위치가 전체 prefix와 얼마나 일치하는지 본다.

즉 KMP는 "실패했을 때 어디로 돌아갈까"에 강하고, Z는 "이 위치부터 prefix가 얼마나 이어질까"에 강하다.

## 깊이 들어가기

### 1. KMP가 하는 일

KMP는 패턴에 대해 failure function을 만든다.

- 패턴 내부의 prefix/suffix 일치 길이를 저장
- mismatch가 나면 비교 위치를 점프

이 덕분에 텍스트를 다시 되돌아보지 않는다.

### 2. Z 알고리즘이 하는 일

Z 배열은 `s[i...]`가 `s[0...]`와 얼마나 길게 같은지 저장한다.

이 값이 있으면 문자열 전체에서 prefix가 반복되는 위치를 한 번에 볼 수 있다.

### 3. 언제 더 어울리나

KMP가 자연스러운 경우:

- 한 패턴을 긴 텍스트에서 찾을 때
- 스트리밍처럼 왼쪽에서 오른쪽으로 읽을 때

Z가 자연스러운 경우:

- prefix 반복 패턴을 분석할 때
- `pattern + '$' + text` 형태로 일괄 처리할 때

### 4. backend에서의 감각

둘 다 로그, 시그니처, 템플릿 검출에 쓸 수 있다.

- KMP: 특정 오류 패턴이 포함되는지 검사
- Z: 반복 문자열이나 prefix 구조 분석

## 실전 시나리오

### 시나리오 1: 로그 패턴 탐지

정확한 에러 문자열이 포함됐는지 빠르게 찾을 때 KMP가 잘 맞는다.

### 시나리오 2: 반복 구조 분석

문자열 안에 prefix가 얼마나 반복되는지 보고 싶으면 Z가 편하다.

### 시나리오 3: 오판

해시 기반으로도 매칭할 수 있지만, collision을 허용하기 싫다면 KMP나 Z가 더 안전하다.

### 시나리오 4: 구현 선택

패턴 하나만 찾는다면 KMP, prefix 구조를 넓게 보고 싶다면 Z를 고른다.

## 코드로 보기

```java
public class KmpVsZNotes {
    public int[] prefixFunction(String p) {
        int[] pi = new int[p.length()];
        for (int i = 1, j = 0; i < p.length(); i++) {
            while (j > 0 && p.charAt(i) != p.charAt(j)) {
                j = pi[j - 1];
            }
            if (p.charAt(i) == p.charAt(j)) {
                pi[i] = ++j;
            }
        }
        return pi;
    }

    public int[] zFunction(String s) {
        int n = s.length();
        int[] z = new int[n];
        for (int i = 1, l = 0, r = 0; i < n; i++) {
            if (i <= r) z[i] = Math.min(r - i + 1, z[i - l]);
            while (i + z[i] < n && s.charAt(z[i]) == s.charAt(i + z[i])) z[i]++;
            if (i + z[i] - 1 > r) {
                l = i;
                r = i + z[i] - 1;
            }
        }
        return z;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| KMP | 패턴 검색에 직관적이다 | prefix function을 익혀야 한다 | 한 패턴을 찾을 때 |
| Z Algorithm | prefix 반복 분석에 강하다 | 패턴 검색으로 바꿔 쓰는 감각이 필요하다 | prefix 기반 분석 |
| Rolling Hash | 구현이 편할 수 있다 | collision 가능성이 있다 | 빠른 근사 검색 |

둘 다 선형 시간이지만, 문제를 바라보는 관점이 다르다.

## 꼬리질문

> Q: KMP와 Z는 결국 같은 문제를 푸나?
> 의도: 두 알고리즘의 관점 차이를 이해하는지 확인
> 핵심: 둘 다 문자열 비교를 최적화하지만, 정보의 저장 방식이 다르다.

> Q: Z가 유리한 상황은 무엇인가?
> 의도: prefix 중심 사고를 하는지 확인
> 핵심: prefix 반복 구조를 분석할 때다.

> Q: 해시 대신 왜 이걸 쓰나?
> 의도: 정확도와 collision trade-off를 이해하는지 확인
> 핵심: collision 없이 정확한 매칭을 원할 때다.

## 한 줄 정리

KMP는 실패한 뒤 돌아갈 위치를 기억하고, Z 알고리즘은 각 위치에서 prefix 일치 길이를 직접 계산한다.
