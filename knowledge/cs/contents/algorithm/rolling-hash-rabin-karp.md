# Rolling Hash / Rabin-Karp

> 한 줄 요약: Rolling Hash는 문자열 구간 해시를 한 칸씩 밀어 갱신하고, Rabin-Karp는 그 해시로 패턴 후보를 빠르게 걸러낸다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: rolling hash rabin karp basics, rolling hash rabin karp beginner, rolling hash rabin karp intro, algorithm basics, beginner algorithm, 처음 배우는데 rolling hash rabin karp, rolling hash rabin karp 입문, rolling hash rabin karp 기초, what is rolling hash rabin karp, how to rolling hash rabin karp
> 관련 문서:
> - [문자열 처리 알고리즘](./string.md)
> - [KMP vs Z Algorithm](./kmp-vs-z-algorithm.md)
> - [Suffix Array and LCP](./suffix-array-lcp.md)

> retrieval-anchor-keywords: rolling hash, rabin-karp, substring hash, polynomial hash, collision, double hash, substring search, string fingerprint, modular hash, plagiarism detection

## 핵심 개념

Rolling Hash는 문자열의 구간 해시를 구하고, 다음 구간으로 이동할 때 계산을 재사용하는 기법이다.
Rabin-Karp는 이 해시를 이용해 패턴 후보를 빠르게 찾는 문자열 매칭 방식이다.

핵심 장점:

- 구간 비교를 빠르게 할 수 있다.
- 동일 길이 substring을 hash로 먼저 거를 수 있다.

핵심 주의점:

- collision이 있을 수 있다.
- 그래서 최종 확인이 필요할 수 있다.

## 깊이 들어가기

### 1. 왜 rolling이 빠른가

문자열의 hash를 한 번 계산해 두면, 다음 위치의 hash는 앞 문자 제거와 뒤 문자 추가만으로 갱신할 수 있다.

즉 매번 substring 전체를 다시 보지 않아도 된다.

### 2. Rabin-Karp가 하는 일

패턴 해시와 텍스트의 각 구간 해시를 비교한다.

- 해시가 다르면 즉시 탈락
- 해시가 같으면 실제 문자열을 한 번 더 확인

이 구조는 "대부분 안 맞는" 상황에서 특히 좋다.

### 3. collision 대응

해시는 완전한 equality 판정이 아니다.

그래서 실무에서는 보통 다음을 같이 쓴다.

- double hash
- 큰 모듈러
- 최종 문자열 비교

정확도와 속도를 함께 챙기는 방식이다.

### 4. backend에서의 활용

Rolling hash는 문자열 fingerprint처럼 쓰일 수 있다.

- 중복 로그 조각 검출
- 텍스트 chunk 비교
- 부분 문자열 캐시 키
- 유사 콘텐츠 탐지

## 실전 시나리오

### 시나리오 1: substring 후보 필터링

패턴이 길고 비교 대상이 많을 때, 해시로 대부분을 걸러내면 비교 비용을 줄일 수 있다.

### 시나리오 2: 중복 문자열 탐지

로그나 문서에서 비슷한 구간이 반복되는지 빠르게 확인할 때 유용하다.

### 시나리오 3: 오판

collision이 치명적인 정산/보안 문제에는 단독 사용이 어렵다.

### 시나리오 4: 빠른 fingerprint

작은 문자열 조각을 대표하는 fingerprint가 필요할 때 실용적이다.

## 코드로 보기

```java
public class RollingHash {
    private static final long MOD = 1_000_000_007L;
    private static final long BASE = 911382323L;

    public long[] buildPrefix(String s) {
        long[] pref = new long[s.length() + 1];
        for (int i = 0; i < s.length(); i++) {
            pref[i + 1] = (pref[i] * BASE + s.charAt(i)) % MOD;
        }
        return pref;
    }

    public long[] buildPower(int n) {
        long[] pow = new long[n + 1];
        pow[0] = 1;
        for (int i = 1; i <= n; i++) {
            pow[i] = (pow[i - 1] * BASE) % MOD;
        }
        return pow;
    }

    public long substringHash(long[] pref, long[] pow, int l, int r) {
        long value = pref[r + 1] - (pref[l] * pow[r - l + 1]) % MOD;
        return (value % MOD + MOD) % MOD;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Rolling Hash | substring 비교가 빠르다 | collision이 있다 | 후보 필터링 |
| KMP | collision이 없다 | 한 패턴 중심이다 | 정확한 매칭 |
| Suffix Array | 다량 substring 검색에 강하다 | 빌드가 무겁다 | 정적 인덱싱 |

Rabin-Karp는 "빠른 후보 필터"라는 감각으로 이해하면 좋다.

## 꼬리질문

> Q: 왜 collision 체크가 필요한가?
> 의도: 해시의 한계를 이해하는지 확인
> 핵심: 서로 다른 문자열이 같은 hash를 가질 수 있기 때문이다.

> Q: double hash를 왜 쓰나?
> 의도: 오차 감소 전략을 아는지 확인
> 핵심: 서로 다른 두 해시를 쓰면 collision 확률이 줄어든다.

> Q: KMP보다 언제 좋은가?
> 의도: 문제 유형 선택 감각 확인
> 핵심: 많은 substring 후보를 빠르게 거를 때다.

## 한 줄 정리

Rolling Hash와 Rabin-Karp는 문자열 구간 해시를 재사용해 후보를 빠르게 걸러내는 해시 기반 매칭 기법이다.
