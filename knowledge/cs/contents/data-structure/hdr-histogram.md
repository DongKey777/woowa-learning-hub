# HDR Histogram

> 한 줄 요약: HDR Histogram은 매우 넓은 값 범위를 고정된 상대 정밀도로 압축 저장해, latency percentile을 작은 메모리로 합산 가능하게 만드는 telemetry용 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HyperLogLog](./hyperloglog.md)
> - [Count-Min Sketch](./count-min-sketch.md)
> - [DDSketch](./ddsketch.md)
> - [KLL Sketch](./kll-sketch.md)
> - [t-Digest](./t-digest.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [Approximate Counting for Rate Limiting and Observability](./approximate-counting-rate-limiting-observability.md)

> retrieval-anchor-keywords: hdr histogram, high dynamic range histogram, latency percentile, percentile telemetry, p99 latency, fixed relative precision, histogram merge, bucketed latency, observability, coordinated omission, quantile sketch comparison

## 핵심 개념

latency telemetry에서 평균값만 보면 tail 문제를 놓치기 쉽다.  
그렇다고 모든 샘플을 그대로 저장하면 비용이 너무 크다.

HDR Histogram은 값을 "정밀도 수준을 유지한 채" bucket에 압축 저장한다.

- 작은 값 구간은 더 세밀하게
- 큰 값 구간은 더 넓게
- 하지만 상대 오차는 일정하게 유지

즉 값 범위가 `1us ~ 수시간`처럼 매우 넓어도,  
고정 메모리로 percentile 계산과 histogram merge를 할 수 있다.

## 깊이 들어가기

### 1. 왜 일반 fixed-width histogram이 아쉽나

고정 폭 bucket histogram은 구현이 단순하다.

- `0~1ms`
- `1~2ms`
- `2~3ms`

하지만 latency 범위가 넓어지면 둘 중 하나가 된다.

- 버킷 폭을 좁게 잡아 메모리가 폭증
- 버킷 폭을 넓게 잡아 p99 tail이 뭉개짐

HDR Histogram은 값이 커질수록 bucket 폭도 커지게 해  
**상대 정밀도**를 지키는 쪽으로 균형을 맞춘다.

### 2. significant digits가 핵심 파라미터다

HDR Histogram은 보통 "몇 자리 유효숫자 정밀도를 원하나"로 설정한다.

예를 들어 3 significant digits라면:

- 1000us 근처에서는 대략 1us 단위
- 100000us 근처에서는 대략 100us 단위

즉 절대 오차가 아니라 **값 크기에 비례한 정밀도**를 관리한다.

이게 latency telemetry에 잘 맞는 이유는,  
`1ms 오차`가 2ms 구간과 20초 구간에서 같은 의미가 아니기 때문이다.

### 3. merge 가능한 histogram이라는 점이 중요하다

분산 시스템 observability에서는 인스턴스별 통계를 합쳐야 한다.

HDR Histogram은 같은 설정을 쓰면 bucket count를 더해 merge할 수 있다.

- 인스턴스별 로컬 집계
- shard별 합산
- minute rollup -> hour rollup

이 성질 덕분에 raw sample 전체를 중앙으로 보내지 않고도  
p95/p99 같은 percentile을 집계 계층에서 재계산할 수 있다.

### 4. quantile sketch와 무엇이 다른가

t-digest나 DDSketch 같은 quantile sketch도 percentile을 다룬다.  
HDR Histogram은 그중에서도 **bucket histogram 기반**에 가깝다.

장점:

- merge가 단순하다
- 구현과 해석이 비교적 직관적이다
- wide dynamic range에서 안정적이다

한계:

- 설정한 precision과 범위에 맞춰 메모리가 정해진다
- raw sample 복원은 불가능하다

### 5. coordinated omission을 구조가 자동으로 해결해주진 않는다

HDR Histogram은 저장 구조일 뿐, 샘플링 오류를 고치진 않는다.

예를 들어 시스템이 10초 멈췄는데 요청을 못 보내서 측정이 빠졌다면,  
histogram은 "관측된 샘플"만 정리할 뿐 누락을 보정하지 않는다.

그래서 latency telemetry에서는 자료구조와 별개로 다음도 중요하다.

- 어떤 방식으로 샘플링했는가
- pause 동안 누락된 요청을 어떻게 해석할 것인가
- client-side vs server-side 측정이 무엇을 의미하는가

## 실전 시나리오

### 시나리오 1: RPC latency percentile

route별 p95/p99를 1분 단위로 집계할 때 raw latency 전부를 저장하지 않고도  
merge 가능한 histogram으로 충분한 정밀도를 얻을 수 있다.

### 시나리오 2: storage / queue wait time

disk latency, lock wait, queue wait처럼 값 범위가 넓은 지표는  
wide dynamic range 구조가 특히 유리하다.

### 시나리오 3: SLO burn 분석

단순 평균이 아니라 tail latency 비중을 봐야 하는 경우,  
HDR Histogram은 percentile과 분포 모양을 함께 볼 수 있게 한다.

### 시나리오 4: 부적합한 경우

개별 요청 raw sample 재분석이 필요하거나, quantile 정확도 요구가 특수하면  
원본 샘플 저장 또는 다른 sketch가 더 맞을 수 있다.

## 코드로 보기

```java
public class SimpleHdrHistogram {
    private final long[] counts;
    private final int significantDigits;
    private long maxValue = 1;

    public SimpleHdrHistogram(int significantDigits, int bucketCount) {
        this.significantDigits = significantDigits;
        this.counts = new long[bucketCount];
    }

    public void record(long value) {
        if (value < 0) {
            throw new IllegalArgumentException("value must be >= 0");
        }
        maxValue = Math.max(maxValue, value);
        counts[indexOf(value)]++;
    }

    public void add(SimpleHdrHistogram other) {
        if (other.counts.length != counts.length || other.significantDigits != significantDigits) {
            throw new IllegalArgumentException("incompatible histogram layout");
        }
        for (int i = 0; i < counts.length; i++) {
            counts[i] += other.counts[i];
        }
        maxValue = Math.max(maxValue, other.maxValue);
    }

    private int indexOf(long value) {
        int exponent = 63 - Long.numberOfLeadingZeros(Math.max(1, value));
        int precisionShift = Math.max(0, exponent - significantDigits * 3);
        int bucket = (int) (value >>> precisionShift);
        return Math.min(bucket, counts.length - 1);
    }
}
```

이 코드는 HDR Histogram의 핵심 감각만 흉내 낸다.  
실제 구현은 sub-bucket layout, equivalent value range, overflow-safe indexing이 훨씬 정교하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| HDR Histogram | wide range latency를 merge 가능하게 저장하고 percentile 계산이 쉽다 | precision/range 설계를 잘못하면 해석이 틀어질 수 있다 | 서비스 latency telemetry, wait time observability |
| Fixed-width Histogram | 단순하고 이해하기 쉽다 | 값 범위가 넓으면 메모리 또는 정밀도 둘 중 하나를 잃는다 | 범위가 좁고 안정적일 때 |
| Raw sample 저장 | 나중에 원하는 분석을 다 할 수 있다 | 저장/전송 비용이 크다 | 샘플 수가 작거나 forensic 분석이 중요할 때 |
| HyperLogLog | distinct count에 매우 효율적이다 | percentile은 계산할 수 없다 | cardinality 추정이 목적일 때 |

중요한 질문은 "분포를 알고 싶은가"와 "원본 값을 전부 저장할 수 있는가"다.

## 꼬리질문

> Q: HDR Histogram이 일반 histogram보다 telemetry에 유리한 이유는?
> 의도: dynamic range와 상대 정밀도 이해 확인
> 핵심: 작은 값과 큰 값을 모두 다루면서도 상대 정밀도를 유지할 수 있기 때문이다.

> Q: merge가 왜 중요한가?
> 의도: 분산 observability 집계 감각 확인
> 핵심: 인스턴스별 로컬 histogram을 합쳐 중앙 percentile을 계산할 수 있기 때문이다.

> Q: HDR Histogram이 coordinated omission을 해결하나요?
> 의도: 측정 구조와 샘플링 오류를 구분하는지 확인
> 핵심: 아니다. 저장 구조일 뿐, 누락된 샘플을 자동 보정하지는 않는다.

## 한 줄 정리

HDR Histogram은 latency 같은 wide-range telemetry를 고정된 상대 정밀도로 압축 저장해, 작은 메모리와 단순한 merge로 percentile 관측을 가능하게 하는 자료구조다.
