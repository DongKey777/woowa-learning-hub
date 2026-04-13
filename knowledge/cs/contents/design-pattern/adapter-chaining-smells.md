# Adapter Chaining Smells: 어댑터를 줄줄이 엮을 때 생기는 냄새

> 한 줄 요약: Adapter chaining은 여러 변환을 얹어 호환성을 만들지만, 단계가 늘면 디버깅과 의미 추적이 어려워진다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)

---

## 핵심 개념

어댑터는 한 번의 번역을 담당할 때 가장 읽기 쉽다.  
하지만 어댑터를 계속 겹치면 다음 문제가 생긴다.

- 어디서 변환됐는지 추적이 어렵다
- 예외가 어느 층에서 생겼는지 모른다
- 변환 책임이 분산된다

### Retrieval Anchors

- `adapter chaining`
- `adapter layering smell`
- `translation pipeline`
- `debugging complexity`
- `multi-step conversion`

---

## 깊이 들어가기

### 1. 한 단계 변환과 여러 단계 변환은 다르다

단일 어댑터는 호환성 해결에 좋다.  
여러 어댑터를 연결하면 사실상 변환 파이프라인이 된다.

### 2. 냄새의 신호

- 어댑터가 `AAdapter -> BAdapter -> CAdapter`로 이어진다
- 같은 데이터가 계속 복사된다
- 중간 포맷 이름이 코드에 드러난다

### 3. 대안은 번역 책임 재배치다

핵심 번역은 translator로 모으고, 호출 순서는 facade나 orchestration으로 둔다.  
성격이 다르면 같은 계층에 두지 않는다.

---

## 실전 시나리오

### 시나리오 1: 레거시 API 통합

응답 포맷이 여러 번 바뀌면 chaining이 생기기 쉽다.

### 시나리오 2: 외부 SDK 래핑

SDK 변환이 중첩되면 내부 도메인이 외부 포맷을 너무 많이 알게 된다.

### 시나리오 3: 데이터 정규화

정규화 단계는 pipeline, 호환 단계는 adapter로 나눠야 한다.

---

## 코드로 보기

### Chaining

```java
PaymentPort port = new LegacyAdapter(
    new JsonAdapter(
        new XmlAdapter(new ExternalClient())
    )
);
```

### Smell

```java
// 각 단계가 무엇을 책임지는지 코드만 보고 알기 어렵다.
```

### Better layering

```java
PaymentFacade facade = new PaymentFacade(new PaymentTranslator(), new ExternalClient());
```

어댑터가 많다고 좋은 게 아니라, 책임 경계가 선명해야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 adapter | 단순하다 | 변환이 복잡하면 비대해진다 | 한 번의 변환 |
| adapter chain | 단계별 변환이 가능하다 | 추적이 어렵다 | 임시 호환 |
| facade + translator | 경계가 명확하다 | 구조가 조금 늘어난다 | 복잡한 연동 |

판단 기준은 다음과 같다.

- 어댑터가 2개 이상 연쇄되면 냄새를 의심한다
- 변환과 조율은 같은 책임이 아니다
- 중간 포맷이 보이면 계층을 다시 짠다

---

## 꼬리질문

> Q: adapter chaining이 왜 문제인가요?
> 의도: 단계 추적과 책임 분리 문제를 아는지 확인한다.
> 핵심: 변환 위치와 원인이 흐려진다.

> Q: adapter와 facade를 섞으면 안 되나요?
> 의도: 패턴 조합을 상황별로 판단하는지 확인한다.
> 핵심: 가능하지만 역할을 분명히 해야 한다.

> Q: chaining을 줄이는 방법은 무엇인가요?
> 의도: 번역 책임 재구성을 아는지 확인한다.
> 핵심: translator와 facade로 분리한다.

## 한 줄 정리

Adapter chaining은 호환성을 만들지만, 단계가 늘면 디버깅과 책임 추적이 어려워지는 냄새가 된다.

