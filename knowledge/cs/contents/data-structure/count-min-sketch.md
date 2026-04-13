# Count-Min Sketch

> 한 줄 요약: Count-Min Sketch는 적은 메모리로 스트림의 빈도를 근사하고, 과대 추정만 허용하는 확률적 카운팅 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)
> - [Bloom Filter](./bloom-filter.md)
> - [HyperLogLog](./hyperloglog.md)

> retrieval-anchor-keywords: count-min sketch, CMS, approximate frequency, frequency sketch, heavy hitters, hot keys, streaming analytics, overestimation, hash rows, approximate count

## 핵심 개념

Count-Min Sketch는 `d`개의 해시 행과 `w`개의 열을 가진 카운트 테이블이다.  
원소가 들어올 때마다 각 행의 해시 위치를 하나씩 증가시키고, 조회할 때는 그 위치들의 **최솟값**을 빈도로 본다.

이 구조의 핵심은 두 가지다.

- 메모리를 고정할 수 있다.
- 빈도를 정확히 저장하지 않아도 된다.

다만 결과는 보통 **과소 추정이 아니라 과대 추정** 쪽으로 치우친다.  
다른 원소와 충돌한 카운트가 더해질 수 있기 때문이다.

## 깊이 들어가기

### 1. 왜 min을 쓰나

한 원소가 여러 행에서 같은 칸을 차지할 수 있고, 그 칸에는 다른 원소들의 카운트도 섞일 수 있다.

그래서 각 행의 값을 전부 믿지 않고, 가장 작은 값을 빈도로 본다.  
이렇게 하면 충돌에 의한 오차를 어느 정도 누를 수 있다.

### 2. 왜 과대 추정만 생기나

카운트를 더하는 구조이기 때문이다.

- 실제로는 3번 나온 원소가
- 충돌 때문에 5번처럼 보일 수 있다

반대로 진짜보다 작아지는 경로는 없다.  
이 성질이 hot key 탐지나 대략적인 빈도 추정에 유용하다.

### 3. backend에서 왜 유용한가

Count-Min Sketch는 완전한 카운터 대신 "가벼운 관측 센서"처럼 쓸 수 있다.

- API hot key 추적
- 테넌트별 요청 분포의 대략적 파악
- 비정상적으로 자주 나타나는 이벤트 탐지
- rate limit 보조 정보

### 4. Bloom Filter와의 차이

Bloom Filter는 membership, Count-Min Sketch는 frequency를 다룬다.

- Bloom Filter: 있는가/없는가
- Count-Min Sketch: 얼마나 자주 나오는가

둘 다 hash + compact array를 쓰지만 목적이 다르다.

## 실전 시나리오

### 시나리오 1: hot key 추적

분산 캐시에서 특정 key가 너무 자주 보이면 병목이 된다.  
Count-Min Sketch는 메모리를 크게 쓰지 않고도 이런 키를 빠르게 의심할 수 있게 해준다.

### 시나리오 2: 실시간 트래픽 분포

대량 요청 로그에서 정확한 count를 전부 들고 있지 않아도, 대략적인 분포를 볼 수 있다.

### 시나리오 3: rate limit 보조

엄밀한 차단 판단은 다른 구조가 하더라도, 스케치로 "대충 얼마나 자주 쓰였나"를 보조할 수 있다.

### 시나리오 4: 오판

정확한 순위가 필요한 재무/정산 시스템에는 부적합하다.  
이 경우는 정확한 카운터나 영속 저장소가 맞다.

## 코드로 보기

```java
public class CountMinSketch {
    private final int[][] table;
    private final int width;
    private final int depth;

    public CountMinSketch(int depth, int width) {
        this.depth = depth;
        this.width = width;
        this.table = new int[depth][width];
    }

    public void add(String value) {
        for (int i = 0; i < depth; i++) {
            table[i][indexOf(value, i)]++;
        }
    }

    public int estimate(String value) {
        int min = Integer.MAX_VALUE;
        for (int i = 0; i < depth; i++) {
            min = Math.min(min, table[i][indexOf(value, i)]);
        }
        return min;
    }

    private int indexOf(String value, int seed) {
        int hash = value.hashCode() ^ (seed * 0x9e3779b9);
        return Math.floorMod(hash, width);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Count-Min Sketch | 메모리가 작고 스트리밍에 강함 | 과대 추정 오차가 있다 | 대략적인 빈도 추적 |
| HashMap 카운터 | 정확하다 | 메모리를 많이 쓴다 | 정확도가 최우선일 때 |
| Top-k heap | 상위 후보를 바로 볼 수 있다 | 전체 분포는 놓친다 | 상위 항목만 중요할 때 |

핵심은 "정확한 값"이 아니라 "충분히 유용한 근사치"가 필요한가다.

## 꼬리질문

> Q: 왜 과소 추정이 거의 없나?
> 의도: 카운트 합산 구조를 이해하는지 확인
> 핵심: 충돌은 값을 더할 뿐, 빼지 않기 때문이다.

> Q: heavy hitter와 왜 같이 쓰이나?
> 의도: 빈도 근사와 상위 후보 추적을 구분하는지 확인
> 핵심: 스케치로 대략적인 빈도를 보고, top-k로 후보를 좁힌다.

> Q: Bloom Filter와 무엇이 다른가?
> 의도: membership vs frequency 구분 확인
> 핵심: Bloom은 존재 여부, Count-Min은 등장 횟수다.

## 한 줄 정리

Count-Min Sketch는 hash 충돌을 허용하는 대신, 스트림의 빈도를 작은 메모리로 빠르게 근사하는 자료구조다.
