# Xor Filter

> 한 줄 요약: Xor Filter는 정적 key 집합에 대해 매우 작은 메모리로 approximate membership을 제공하는 구조로, Bloom/Cuckoo보다 더 압축적인 읽기 중심 prefilter가 필요할 때 강력한 선택지다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bloom Filter](./bloom-filter.md)
> - [Cuckoo Filter](./cuckoo-filter.md)
> - [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)

> retrieval-anchor-keywords: xor filter, approximate membership, static set filter, fingerprint filter, xor-based filter, read-mostly filter, compact prefilter, bloom alternative, cuckoo alternative, negative lookup filter

## 핵심 개념

Xor Filter도 "있을 수도 있다 / 없다"를 빠르게 말하는 approximate membership 구조다.  
하지만 Bloom Filter처럼 비트 배열을 여러 번 찍는 방식도, Cuckoo Filter처럼 relocation bucket을 유지하는 방식도 아니다.

핵심 발상은 이렇다.

- 각 key는 몇 개의 후보 위치를 가진다
- 각 위치에는 fingerprint 하나가 저장된다
- 후보 위치들의 fingerprint xor를 이용해 membership을 검사한다

즉 정적 집합에 대해 매우 작은 공간으로 membership prefilter를 만드는 구조다.

## 깊이 들어가기

### 1. 왜 "정적 집합"이라는 조건이 중요한가

Xor Filter는 보통 한 번 집합을 만들고, 그다음엔 주로 조회만 하는 상황에 맞는다.

- 배포 시 로드되는 blacklist
- 읽기 전용 dictionary prefilter
- immutable segment별 key prefilter

삽입/삭제를 실시간으로 자유롭게 지원하는 구조가 아니라,  
**빌드 비용을 먼저 치르고 조회 효율을 얻는 구조**라고 보는 편이 맞다.

### 2. build가 lookup보다 훨씬 복잡하다

lookup은 간단한 편이다.

- key에서 후보 위치를 계산한다
- 그 위치들의 fingerprint xor와 대상 fingerprint를 비교한다

하지만 build 과정은 더 어렵다.

- hypergraph peeling처럼 key를 배치해야 한다
- 순환이 심하면 다시 시도해야 한다
- seed를 바꿔 재생성할 수 있다

즉 runtime lookup은 매우 가볍지만, construction은 오프라인 성격이 강하다.

### 3. Bloom / Cuckoo와 어디서 갈리나

대략적인 감각은 이렇다.

- Bloom: 단순하고 삽입이 쉬움
- Cuckoo: 삭제 가능, 동적 운영 가능
- Xor: 정적 집합에서 더 작은 메모리와 빠른 조회를 노림

따라서 선택 기준은 "누가 더 최신인가"가 아니라  
**집합이 얼마나 자주 바뀌는가**에 가깝다.

### 4. backend에서 왜 매력적인가

backend에서는 immutable/append-segment 기반 구조가 많다.

- SSTable / segment file
- 읽기 전용 룰셋
- 배포 단위 dictionary

이 경우 segment별 Xor Filter를 만들면 negative lookup을 매우 싸게 걸러낼 수 있다.  
특히 hot path에서 메모리 사용량이 작은 것이 장점이 된다.

### 5. 부작용과 한계

Xor Filter는 정적 집합에서 매우 좋지만, 그만큼 제약이 뚜렷하다.

- 동적 삽입/삭제가 불편하다
- 빌드 실패 시 재시도가 필요할 수 있다
- construction pipeline이 필요하다

즉 online mutable cache admission filter보다  
immutable snapshot prefilter에 더 잘 맞는다.

## 실전 시나리오

### 시나리오 1: immutable segment prefilter

읽기 전용 세그먼트 파일마다 Xor Filter를 두면  
없는 key를 빠르게 배제해 disk lookup을 줄일 수 있다.

### 시나리오 2: 배포 단위 blacklist / allowlist

룰셋이 배포 시점마다 통째로 바뀌는 구조라면  
동적 업데이트보다 compact lookup이 더 중요할 수 있다.

### 시나리오 3: edge negative lookup filter

메모리 예산이 빡빡한 edge/node process에서  
정적 key set membership precheck를 아주 작게 들고 가기 좋다.

### 시나리오 4: 부적합한 경우

실시간 삽입/삭제가 중요한 idempotency key window나 rolling membership에는  
Cuckoo Filter나 다른 구조가 더 자연스럽다.

## 코드로 보기

```java
public class XorFilterSketch {
    private final short[] fingerprints;

    public XorFilterSketch(short[] fingerprints) {
        this.fingerprints = fingerprints;
    }

    public boolean mightContain(String key) {
        short fp = fingerprint(key);
        int h1 = index(key, 0);
        int h2 = index(key, 1);
        int h3 = index(key, 2);

        short combined = (short) (fingerprints[h1] ^ fingerprints[h2] ^ fingerprints[h3]);
        return combined == fp;
    }

    private short fingerprint(String key) {
        short fp = (short) (key.hashCode() & 0xFFFF);
        return fp == 0 ? 1 : fp;
    }

    private int index(String key, int seed) {
        return Math.floorMod((key.hashCode() * 0x9e3779b9) ^ seed, fingerprints.length);
    }
}
```

이 코드는 lookup 감각만 보여준다.  
실제 Xor Filter의 핵심은 fingerprint 배열을 어떻게 생성하느냐는 build 알고리즘 쪽이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Xor Filter | 정적 집합에서 메모리 효율이 매우 좋고 lookup이 가볍다 | 동적 업데이트가 불편하고 build 단계가 복잡하다 | immutable segment prefilter, read-mostly membership |
| Bloom Filter | 단순하고 삽입이 쉽다 | 공간 효율이 상대적으로 떨어질 수 있다 | 동적 추가가 있는 일반 prefilter |
| Cuckoo Filter | 삭제와 동적 운영이 가능하다 | 삽입 실패/relocation 관리가 필요하다 | mutable membership filter |
| HashSet | 정확하다 | 메모리를 더 쓴다 | 정확 membership이 절대적일 때 |

중요한 질문은 "필터가 정적 집합용인가"다.  
그 답이 yes면 Xor Filter가 매우 강력해진다.

## 꼬리질문

> Q: Xor Filter가 Bloom보다 더 잘 맞는 경우는 언제인가요?
> 의도: 동적/정적 membership filter 구분 이해 확인
> 핵심: 집합이 빌드 후 거의 변하지 않고, 메모리 효율이 특히 중요할 때다.

> Q: 왜 build가 lookup보다 어렵나요?
> 의도: runtime fast path와 construction cost를 분리해 보는지 확인
> 핵심: key들을 xor 제약을 만족하도록 배치하는 오프라인 구성 과정이 필요하기 때문이다.

> Q: rolling window membership에는 왜 부적합한가요?
> 의도: 자료구조의 적용 경계를 보는지 확인
> 핵심: 삽입/삭제를 온라인으로 자연스럽게 처리하는 구조가 아니기 때문이다.

## 한 줄 정리

Xor Filter는 읽기 중심의 정적 key 집합에 대해 매우 작은 메모리로 negative lookup prefilter를 제공하는 approximate membership 구조다.
