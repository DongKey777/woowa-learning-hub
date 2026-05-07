---
schema_version: 3
title: Annotation Processing
concept_id: language/java-annotation-processing
canonical: true
category: language
difficulty: intermediate
doc_role: primer
level: intermediate
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- annotation-processing
- compile-time-code-generation
- java-build-pipeline
aliases:
- Java annotation processing
- annotation processor
- AbstractProcessor
- javac round processing
- compile time code generation
- Filer RoundEnvironment
- 어노테이션 처리
symptoms:
- annotation processing을 runtime reflection처럼 이해해서 compile-time code generation과 검증 역할을 구분하지 못해
- Processor, RoundEnvironment, Filer가 javac round에서 어떻게 협력하는지 큰 그림이 필요해
- Lombok, MapStruct, Dagger 같은 도구가 빌드 시점에 무엇을 생성하거나 검증하는지 설명해야 해
intents:
- definition
- deep_dive
prerequisites:
- language/java-language-basics
next_docs:
- spring/bean-definition-registry-postprocessor-import-registrar
- language/reflection-generics-annotations
- language/reflection-cost-and-alternatives
- spring/bean-lifecycle-basics
linked_paths:
- contents/language/java/java-language-basics.md
- contents/spring/spring-bean-definition-registry-postprocessor-import-registrar.md
- contents/language/java/reflection-generics-annotations.md
- contents/language/java/reflection-cost-and-alternatives.md
- contents/spring/spring-bean-lifecycle-basics.md
confusable_with:
- language/reflection-generics-annotations
- language/reflection-cost-and-alternatives
- spring/bean-lifecycle-basics
forbidden_neighbors: []
expected_queries:
- Java annotation processing이 runtime reflection과 어떻게 다른지 설명해줘
- AbstractProcessor RoundEnvironment Filer가 javac compile round에서 하는 일을 알려줘
- Lombok MapStruct 같은 annotation processor가 빌드 시점에 코드를 생성하는 흐름이 궁금해
- annotation processing으로 컴파일 타임 검증을 하는 장단점을 알려줘
- 어노테이션 처리기를 만들 때 deterministic output과 에러 메시지가 왜 중요해?
contextual_chunk_prefix: |
  이 문서는 Java annotation processing을 javac compile round, AbstractProcessor, RoundEnvironment, Filer, source generation, compile-time validation 관점으로 설명하는 intermediate primer다.
  annotation processor, Lombok, MapStruct, Dagger, runtime reflection difference, build pipeline 질문이 본 문서에 매핑된다.
---
# Annotation Processing


> 한 줄 요약: Annotation Processing는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: annotation processing basics, annotation processing beginner, annotation processing intro, java basics, beginner java, 처음 배우는데 annotation processing, annotation processing 입문, annotation processing 기초, what is annotation processing, how to annotation processing
> 컴파일 타임에 코드를 생성하거나 검증하는 자바 메타프로그래밍 정리

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [어노테이션 처리란](#어노테이션-처리란)
- [처리 흐름](#처리-흐름)
- [핵심 API](#핵심-api)
- [어디에 쓰는가](#어디에-쓰는가)
- [설계할 때의 기준](#설계할-때의-기준)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 왜 중요한가

자바에서 어노테이션은 메타데이터다. 그런데 이 메타데이터를 단순히 런타임에 읽는 수준을 넘어서, **컴파일 타임에 코드 생성과 검증에 활용**할 수 있다.

이 차이가 크다.

- 런타임 리플렉션은 편하지만 실행 시점까지 문제를 숨길 수 있다
- 어노테이션 처리기는 빌드 단계에서 오류를 드러내고, 반복 코드를 없애고, 규칙을 강제할 수 있다

즉 annotation processing은 “자바 문법 위에 얹는 작은 DSL”이 아니라, **빌드 파이프라인을 설계하는 기술**에 가깝다.

---

## 어노테이션 처리란

Annotation Processing은 `javac`가 소스를 컴파일하는 동안 어노테이션을 읽고, **추가 소스 파일이나 리소스를 생성**하는 기능이다.

대표적인 사용 예:

- DTO 변환 코드 생성
- Builder / Mapper 생성
- 검증 규칙 자동화
- DI 설정 검증

여기서 중요한 점은, 처리기는 바이트코드를 직접 만지는 것이 아니라 **소스 레벨의 산출물**을 만든다는 것이다.

---

## 처리 흐름

전형적인 흐름은 다음과 같다.

1. `javac`가 소스를 읽는다
2. 어노테이션이 붙은 요소를 찾는다
3. `Processor`가 해당 요소를 검사한다
4. 필요하면 새로운 `.java` 파일이나 리소스를 생성한다
5. 생성된 소스도 다음 라운드에서 다시 컴파일된다

이 구조 때문에 annotation processing은 보통 **round-based**로 설명한다.

주의할 점:

- 한 번에 모든 파일이 처리된다고 생각하면 안 된다
- 생성된 코드가 다시 입력이 될 수 있다
- 순환 생성은 쉽게 빌드 문제를 만든다

---

## 핵심 API

자주 보는 API는 아래와 같다.

- `javax.annotation.processing.AbstractProcessor`
- `javax.annotation.processing.RoundEnvironment`
- `javax.annotation.processing.Filer`
- `javax.lang.model.element.Element`
- `javax.lang.model.element.TypeElement`
- `javax.lang.model.util.Elements`
- `javax.lang.model.util.Types`

간단한 구조는 이렇다.

```java
@SupportedAnnotationTypes("com.example.GenerateHello")
@SupportedSourceVersion(SourceVersion.RELEASE_21)
public class HelloProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
        // annotated element를 찾고 생성 코드 작성
        return true;
    }
}
```

`process()`에서 보통 하는 일은 두 가지다.

- 어노테이션이 붙은 타입이 규칙을 만족하는지 검증
- 새 소스를 생성하거나 메타데이터를 출력

프로세서를 빌드 도구가 찾도록 하려면 보통 서비스 등록이 필요하다.

- `META-INF/services/javax.annotation.processing.Processor`

---

## 어디에 쓰는가

실무에서 자주 만나는 사례는 다음과 같다.

- Lombok 스타일의 보일러플레이트 감소
- MapStruct 같은 매퍼 생성
- Dagger / AutoService 계열의 코드 생성
- JPA 메타모델 생성
- 도메인 규칙 검증

이 방식이 좋은 이유는 런타임에 리플렉션으로 일일이 찾는 대신, **컴파일 시점에 실패하게 만들 수 있기 때문**이다.

예를 들어:

- 반드시 특정 필드가 있어야 한다
- 특정 인터페이스를 구현해야 한다
- 이름 규칙이 맞지 않으면 빌드를 실패시킨다

이런 검사는 런타임보다 컴파일 타임이 더 싸고, 더 빠르고, 더 안전하다.

---

## 설계할 때의 기준

어노테이션 처리기를 만들 때는 편의성보다 **예측 가능성**을 먼저 봐야 한다.

### 1. 비즈니스 로직을 넣지 말 것

처리기는 애플리케이션 로직을 실행하는 곳이 아니다.

- 입력 어노테이션을 분석하고
- 규칙을 검증하고
- 코드나 리소스를 생성하는

역할에 집중해야 한다.

### 2. 생성 결과가 결정적이어야 한다

같은 입력이면 같은 출력이 나와야 한다.

- 빌드 캐시
- 증분 컴파일
- 재현 가능한 빌드

를 생각하면 결정성은 필수다.

### 3. 에러 메시지는 구체적이어야 한다

처리기 오류는 사용자 경험에 직접 영향을 준다.

- 어떤 타입이 잘못됐는지
- 어떤 어노테이션 속성이 잘못됐는지
- 어떻게 고쳐야 하는지

를 바로 알 수 있게 해야 한다.

### 4. 런타임 리플렉션 대체와 혼동하지 말 것

어노테이션 처리는 리플렉션처럼 보일 수 있지만 목적이 다르다.

- 리플렉션은 실행 중 동작을 바꾸는 데 가깝다
- annotation processing은 컴파일 시 구조를 고정하는 데 가깝다

---

## 시니어 관점 질문

- annotation processing을 쓰면 무엇을 얻고 무엇을 잃는가?
- 런타임 리플렉션보다 컴파일 타임 생성이 더 좋은 경우는 언제인가?
- 생성 코드가 많아질수록 디버깅과 유지보수는 어떻게 달라지는가?
- 프로세서가 빌드를 느리게 만들지 않으려면 어떤 기준을 가져야 하는가?
- 어노테이션 기반 설계가 과해지는 지점은 어디인가?

## 한 줄 정리

Annotation Processing는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
