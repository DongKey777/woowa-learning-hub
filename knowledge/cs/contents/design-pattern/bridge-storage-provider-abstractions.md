# Bridge Pattern: 저장소와 제공자를 분리하는 추상화

> 한 줄 요약: Bridge 패턴은 추상화와 구현을 분리해, 저장소 타입과 provider 종류가 서로 폭발하지 않게 만든다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Bridge 패턴은 **추상화와 구현을 독립적으로 확장**하려는 패턴이다.  
backend에서는 특히 storage, provider, transport 같은 축이 동시에 바뀔 때 유용하다.

예를 들면:

- storage abstraction: S3, GCS, local fs
- provider abstraction: image, document, backup
- notification abstraction: email, sms, push

### Retrieval Anchors

- `bridge pattern`
- `abstraction implementation split`
- `storage provider abstraction`
- `provider matrix`
- `independent extensibility`

---

## 깊이 들어가기

### 1. 브릿지는 두 축의 변화가 있을 때 빛난다

만약 저장 방식과 파일 타입이 함께 바뀐다면 단순 상속은 곧 폭발한다.

- `S3ImageStorage`
- `S3DocumentStorage`
- `LocalImageStorage`
- `LocalDocumentStorage`

Bridge는 이런 조합 폭발을 막는다.

### 2. 추상화와 구현을 묶지 않는다

Bridge는 상위 추상화가 구현 세부를 직접 모르도록 한다.

- Abstraction: "저장한다"
- Implementor: "어디에 어떻게 저장한다"

이 분리는 Ports and Adapters와 감각이 비슷하지만, Bridge는 패턴 수준의 구조다.

### 3. interface 폭발을 줄인다

Bridge는 생성되는 클래스 수를 줄이는 데도 도움이 된다.

---

## 실전 시나리오

### 시나리오 1: 파일 저장 서비스

업로드 파일의 종류와 저장소가 서로 독립적으로 바뀔 때 유용하다.

### 시나리오 2: 알림 발송

메시지 종류와 채널이 분리되어 바뀌는 경우 Bridge가 잘 맞는다.

### 시나리오 3: 레거시 provider 전환

구현체를 교체해도 추상화 API는 유지할 수 있다.

---

## 코드로 보기

### Abstraction

```java
public abstract class FileService {
    protected final StorageProvider provider;

    protected FileService(StorageProvider provider) {
        this.provider = provider;
    }

    public abstract void save(String name, byte[] data);
}
```

### Implementor

```java
public interface StorageProvider {
    void save(String name, byte[] data);
}
```

### Concrete abstraction

```java
public class ImageFileService extends FileService {
    public ImageFileService(StorageProvider provider) {
        super(provider);
    }

    @Override
    public void save(String name, byte[] data) {
        provider.save(name, data);
    }
}
```

Bridge는 "저장 객체"와 "저장소 구현"의 결합을 늦춘다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 상속 조합 | 단순해 보인다 | 조합 폭발이 생긴다 | 축이 하나일 때 |
| Bridge | 독립 확장이 가능하다 | 구조가 다소 추상적이다 | 두 축이 동시에 바뀔 때 |
| Adapter | 기존 구현을 연결한다 | 구조 분리는 약하다 | 호환성 문제일 때 |

판단 기준은 다음과 같다.

- 구현 축과 추상화 축이 둘 다 변하면 Bridge
- 단순한 변환이면 Adapter
- 경계 보호가 목표면 Port/Adapter 계층을 본다

---

## 꼬리질문

> Q: Bridge와 Adapter의 차이는 무엇인가요?
> 의도: 연결과 분리의 목적 차이를 확인한다.
> 핵심: Adapter는 호환성, Bridge는 독립 확장이다.

> Q: Bridge가 저장소 abstraction에 잘 맞는 이유는 무엇인가요?
> 의도: 두 축의 독립성을 이해하는지 확인한다.
> 핵심: 저장 대상과 저장 방식이 서로 따로 바뀌기 때문이다.

> Q: Bridge를 과하게 쓰면 어떤가요?
> 의도: 추상화 과잉을 경계하는지 확인한다.
> 핵심: 불필요한 레이어만 늘어나서 읽기 어려워진다.

## 한 줄 정리

Bridge 패턴은 storage와 provider 같은 두 변화 축을 분리해 조합 폭발을 막는다.

