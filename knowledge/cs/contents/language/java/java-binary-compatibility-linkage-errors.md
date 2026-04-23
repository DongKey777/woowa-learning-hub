# Java Binary Compatibility and Runtime Linkage Errors

> 한 줄 요약: 소스 코드는 컴파일되고 테스트도 통과했는데 운영에서 `NoSuchMethodError`, `AbstractMethodError`, `IncompatibleClassChangeError`가 터지는 이유는, Java 호환성이 source, binary, behavioral로 갈라져 있기 때문이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ClassLoader Delegation Edge Cases](./classloader-delegation-edge-cases.md)
> - [Java Module System Runtime Boundaries](./java-module-system-runtime-boundaries.md)
> - [추상 클래스 vs 인터페이스](./abstract-class-vs-interface.md)
> - [Serialization Compatibility and `serialVersionUID`](./serialization-compatibility-serial-version-uid.md)
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)

> retrieval-anchor-keywords: binary compatibility, source compatibility, behavioral compatibility, LinkageError, NoSuchMethodError, AbstractMethodError, IncompatibleClassChangeError, IllegalAccessError, mixed version deployment, library evolution, default method, erased signature, bridge method, shading, classpath hell

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

Java에서 "호환된다"는 말은 하나가 아니다.

- source compatibility: 다시 컴파일하면 소스가 통과하는가
- binary compatibility: 다시 컴파일하지 않아도 기존 바이너리가 새 라이브러리와 링크되는가
- behavioral compatibility: 링크는 되지만 의미가 바뀌지 않는가

운영 장애는 보통 binary compatibility가 깨졌을 때 보인다.

- `NoSuchMethodError`
- `AbstractMethodError`
- `IncompatibleClassChangeError`
- `IllegalAccessError`

즉 "컴파일된다"와 "운영에서 같은 조합으로 안전하다"는 전혀 다른 질문이다.

## 깊이 들어가기

### 1. 왜 runtime에서만 터질까

Java 호출 사이트는 컴파일 시점 심볼 정보를 class file constant pool에 기록한다.  
런타임에는 실제 로드된 클래스가 그 심볼과 맞아야 링크가 된다.

그래서 다음이 섞이면 위험하다.

- consumer는 예전 버전 API로 컴파일됨
- runtime에는 다른 버전 provider가 올라감
- 테스트는 한 classpath 조합만 검증함

이때 문제는 코드 문법이 아니라 "배포된 조합"이다.

### 2. 대표적인 breaking change 패턴

#### 메서드 삭제 또는 descriptor 변경

기존 호출 사이트가 찾는 심볼이 사라지면 `NoSuchMethodError`가 난다.

- 메서드 제거
- 파라미터 타입 변경
- 반환 타입까지 포함한 descriptor 변경

generic type parameter만 바꿔도 erasure가 같으면 binary는 유지될 수 있다.  
반대로 source에서 사소해 보이는 시그니처 변경도 runtime descriptor가 바뀌면 바로 깨진다.

#### 인터페이스에 abstract 메서드 추가

기존 구현체를 다시 컴파일하지 않은 상태에서 새 메서드를 호출하면 `AbstractMethodError`가 날 수 있다.

이 때문에 공개 SPI는 진화 전략이 중요하다.  
default method는 이 문제를 줄이는 도구지만 만능은 아니다.

#### instance/static, class/interface 성격 변경

호출 opcode 기대와 실제 정의가 어긋나면 `IncompatibleClassChangeError` 계열이 난다.

- 인스턴스 메서드를 static으로 바꿈
- static 필드를 인스턴스 필드로 바꿈
- class/interface 관계를 뒤집음

#### 접근 제한 강화

public이던 멤버를 package-private이나 private에 가깝게 바꾸면 `IllegalAccessError`가 날 수 있다.

### 3. default method는 "덜 위험한 진화"일 뿐이다

interface에 새 abstract 메서드를 넣는 것은 오래된 구현체에 가혹하다.  
그래서 default method가 binary-friendly evolution 수단으로 자주 쓰인다.

하지만 여전히 조심할 점이 있다.

- 기존 hierarchy에 같은 signature가 있으면 충돌 규칙을 확인해야 한다
- default body가 behavioral change를 숨길 수 있다
- binary는 유지되어도 semantic contract가 달라질 수 있다

즉 default method는 장애를 줄여주지만, compatibility review를 대체하지 않는다.

### 4. classpath와 classloader가 문제를 증폭한다

링크 오류는 코드 변경 하나만으로 생기지 않는다.  
배포 환경이 버전 혼합을 허용하면 문제가 늦게 드러난다.

대표 원인:

- transitive dependency 충돌
- fat jar 안의 오래된 라이브러리
- shading 후 일부 패키지만 relocation
- plugin/container classloader가 서로 다른 버전 로드

즉 linkage error는 종종 dependency management 사고다.

### 5. serialization 호환성과 binary 호환성은 다른 문제다

`serialVersionUID`가 맞아도 메서드 링크가 깨질 수 있고,  
반대로 링크는 살아 있어도 직렬화 포맷이 깨질 수 있다.

둘 다 "진화" 문제이지만 계층이 다르다.

- binary compatibility: method/field/supertype 링크
- serialization compatibility: persisted bytes와 object schema

## 실전 시나리오

### 시나리오 1: 배포 직후 `NoSuchMethodError`가 뜬다

서비스는 컴파일됐는데 운영에서만 특정 starter와 조합될 때 깨진다.  
대부분은 transitive dependency version mismatch다.

이때 먼저 볼 것:

- 어떤 jar가 실제 로드됐는가
- 호출한 쪽과 제공한 쪽이 같은 버전인가
- BOM이나 dependency lock이 drift했는가

### 시나리오 2: 플러그인 구현체가 갑자기 죽는다

공개 interface에 abstract 메서드를 추가했고, 기존 plugin jar는 재컴파일되지 않았다.  
프레임워크가 그 메서드를 부르는 순간 `AbstractMethodError`가 난다.

### 시나리오 3: 리팩터링했는데 운영에서만 `IncompatibleClassChangeError`가 난다

헬퍼를 instance method에서 static method로 바꿨다.  
같은 repo는 전부 재컴파일되어 테스트가 통과했지만, 일부 오래된 모듈이 같이 배포되면 runtime에 깨질 수 있다.

### 시나리오 4: 테스트는 멀쩡한데 고객 환경에서만 깨진다

애플리케이션 서버, plugin, agent가 각자 다른 classloader를 쓰면 로컬 재현이 어려워진다.  
이때는 "어떤 코드가 보이느냐"가 source tree보다 중요하다.

## 코드로 보기

### 1. 인터페이스 진화와 `AbstractMethodError`

```java
// v1
public interface PaymentPlugin {
    void charge();
}

// v2
public interface PaymentPlugin {
    void charge();
    int priority();
}
```

구현체가 v1 기준으로 컴파일된 상태에서 v2 runtime이 `priority()`를 호출하면 깨질 수 있다.

### 2. default method로 완충하기

```java
public interface PaymentPlugin {
    void charge();

    default int priority() {
        return 0;
    }
}
```

이 방식은 기존 구현체를 살릴 가능성이 높지만, 의미상 안전한 기본값인지 따로 검토해야 한다.

### 3. 메서드 descriptor 변경

```java
// v1
public interface TokenReader {
    String read(String key);
}

// v2
public interface TokenReader {
    String read(CharSequence key);
}
```

호출자 재컴파일 없이 runtime만 v2로 바꾸면 기존 `read(Ljava/lang/String;)Ljava/lang/String;` 심볼을 못 찾을 수 있다.

### 4. 운영 진단 감각

```bash
jcmd <pid> VM.system_properties
jcmd <pid> VM.classloader_stats
```

링크 오류는 stack trace만 보기보다 실제 로드된 버전과 classloader를 함께 봐야 한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| interface에 abstract 메서드 추가 | 계약이 명확해진다 | 기존 구현체 binary 호환성이 쉽게 깨진다 |
| default method 추가 | 기존 구현체를 덜 깨뜨린다 | 기본 동작이 의미상 위험할 수 있다 |
| aggressive refactor | API를 정리하기 쉽다 | mixed-version deployment에 취약하다 |
| compatibility-first evolution | 운영 안정성이 높다 | API 설계와 deprecated 기간 관리가 필요하다 |

핵심은 public type evolution을 코드 리팩터링이 아니라 배포 계약 관리로 보는 것이다.

## 꼬리질문

> Q: source compatibility와 binary compatibility 차이는 무엇인가요?
> 핵심: 다시 컴파일하면 되는가와, 다시 컴파일 없이도 기존 바이너리가 새 버전과 링크되는가는 다른 문제다.

> Q: 왜 interface에 메서드를 추가하면 위험한가요?
> 핵심: 기존 구현체가 그 메서드를 갖고 있지 않아서 runtime에 `AbstractMethodError`가 날 수 있다.

> Q: default method를 쓰면 항상 안전한가요?
> 핵심: binary 안정성에는 도움 되지만 behavioral change와 hierarchy 충돌은 여전히 검토해야 한다.

> Q: `NoSuchMethodError`가 뜨면 어디부터 봐야 하나요?
> 핵심: 코드보다 먼저 실제 classpath, transitive dependency, classloader 조합을 확인해야 한다.

## 한 줄 정리

Java 호환성 문제는 문법보다 배포 조합의 문제이므로, 공개 API를 바꿀 때는 source가 아니라 binary 링크와 mixed-version 운영을 기준으로 검토해야 한다.
