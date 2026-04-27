# 자바 언어의 구조와 기본 문법

> 한 줄 요약: Java를 처음 읽을 때 필요한 실행 모델, 타입, 배열, 제어문, 그리고 초보자 compile-error 감각을 한 번에 묶는 beginner primer다.

**난이도: 🟢 Beginner**

작성자 : [서그림](https://github.com/Seogeurim)

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [Junior Backend Roadmap: 1단계 자바 언어 감각 잡기](../../../JUNIOR-BACKEND-ROADMAP.md#1단계-자바-언어-감각-잡기)
- [Spring 요청 파이프라인과 Bean Container 기초](../../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- [HTTP 요청-응답 기본 흐름](../../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [SQL 읽기와 관계형 모델링 기초](../../database/sql-reading-relational-modeling-primer.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- [Java 반복문과 스코프 follow-up 입문](./java-loop-control-scope-follow-up-primer.md)
- [Java Array Equality Basics](./java-array-equality-basics.md)
- [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)
- [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md)
- [배열 vs 연결 리스트](../../data-structure/array-vs-linked-list.md)
- [객체지향 핵심 원리](./object-oriented-core-principles.md)
- [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
- [ClassLoader, Exception 경계, 객체 계약](./classloader-exception-boundaries-object-contracts.md)

retrieval-anchor-keywords: java language basics, java source bytecode jvm flow, jdk vs jvm beginner, java primitive vs reference, java data type basics, java type conversion promotion demotion, java cast overflow beginner, java variable scope basics, java field vs local variable initialization, java local variable not initialized compile error, java array basics, java control flow basics, java array equality copy sorting route, java array next step guide, java array compare false with ==, java copied original changed together, java sort changed original binarysearch wrong, java basics to class object instance, java syntax to oop bridge, java class object instance next doc, java class object instance beginner route, class object instance after java basics, 클래스 객체 인스턴스 다음 문서, 자바 문법 다음 객체지향, 자바 기초 다음 class object instance, 배열 비교 막힘 다음 문서, 배열 복사 같이 바뀜, 배열 정렬 후 binarySearch 이상, 자바 문법 기초, 자바 기초 문법 큰 그림, 처음 배우는데 자바 문법, 처음 배우는데 자바 큰 그림, 자바 실행 구조 기초, 자바 타입 기초, 자바 형변환 기초, 형변환 언제 쓰는지 기초, 자바 배열 기초, 자바 제어문 기초, 자바 배열 비교 복사 정렬 차이, 배열 다음 뭐 읽어야

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [Java 언어의 탄생 배경](#java-언어의-탄생-배경)
- [Java의 10가지 특징](#java의-10가지-특징)
- [Java 특징 이어서 보기](#java-특징-이어서-보기)
- [Java 플랫폼](#java-플랫폼)
- [Java 프로그램 구조](#java-프로그램-구조)
- [가장 작은 예시로 읽기](#가장-작은-예시로-읽기)
- [Java 데이터 타입 먼저 보는 큰 그림](#java-데이터-타입-먼저-보는-큰-그림)
- [Java 데이터 타입 기본형 한눈에 보기](#java-데이터-타입-기본형-한눈에-보기)
- [Java 형변환 자동 변환과 명시적 캐스팅](#java-형변환-자동-변환과-명시적-캐스팅)
- [Java 변수와 스코프 필드 vs 지역 변수](#java-변수와-스코프-필드-vs-지역-변수)
- [Java 연산자](#java-연산자)
- [Java 배열: 먼저 잡는 감각](#java-배열-먼저-잡는-감각)
- [일차원 배열 손추적과 자주 보는 오류](#일차원-배열-손추적과-자주-보는-오류)
- [이차원 배열과 명령행 매개변수](#이차원-배열과-명령행-매개변수)
- [Java 제어문](#java-제어문)
- [초보자 혼동 포인트](#초보자-혼동-포인트)
- [다음 읽을 문서](#다음-읽을-문서)
- [백엔드 4레인 연결](#백엔드-4레인-연결)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡는 mental model

Java를 처음 볼 때는 문법 항목을 전부 외우기보다, **소스 코드가 JVM에서 실행되는 흐름**을 먼저 잡는 편이 훨씬 쉽다.

```text
.java 소스 작성 -> javac가 .class 바이트코드 생성 -> JVM이 바이트코드를 실행
```

입문자 기준으로는 아래 네 개만 먼저 분리해도 큰 그림이 잡힌다.

| 이름 | 한 줄 뜻 | 지금 기억할 포인트 |
|---|---|---|
| `JDK` | 개발 도구 묶음 | `javac` 같은 컴파일 도구가 들어 있다 |
| `JVM` | 바이트코드를 실행하는 가상 머신 | OS마다 구현이 달라도 Java 코드는 비슷한 방식으로 실행된다 |
| `class` | 변수와 메서드를 묶는 설계도 | Java 파일의 기본 단위다 |
| `object` | class로 만든 실제 값 | 상태를 가지고 메서드를 호출할 수 있다 |

즉 Java는 "문법"만 배우는 언어가 아니라, **타입이 있는 소스 코드 + 표준 라이브러리 + JVM 실행 모델**을 함께 배우는 언어라고 보면 된다.

## Java 언어의 탄생 배경

### 썬마이크로시스템즈의 Green Project에서 시작

Green Project에서는 가정용 전자기기의 통합적 제어를 위해, 전자기기에서 사용되는 작은 컴퓨터 언어를 제안했다. 가정용 전자기기에 사용되는 power나 memory가 열악했기 때문에 여기에 사용되는 언어는 작고 견고하고, 신뢰할 수 있는 코드를 필요로 했다. 또한 다른 CPU가 선택될 수 있기 때문에 특정 디바이스에 종속되면 안 되었다. 따라서 **Virtual Machine에서 동작하는 중간 코드를 생성하여 이식성이 높은 언어를 디자인**하게 되었다.

초기에는 절차 지향 + 객체 지향 언어인 C++ 기반으로 개발되었다. 하지만 C++ 언어가 가진 한계에 부딪혀 **완벽한 객체 지향 언어**인 Oak 언어를 개발하였고, 이미 존재하는 이름이라 추후 **Java**로 이름이 바뀌게 되었다.

그 후 Java를 기반으로 한 HotJava라는 웹 브라우저를 제작하였는데, Java의 Applet 이라는 기능을 보여주기 위해 브라우저가 중간 코드(Bytecode)를 해석할 수 있도록 만들었다. 이 때 자바 붐이 일어나 Java 언어가 급격히 확산되었다. 이후 많은 업체들이 Java를 지원하기 시작하였고, 1996년 자바 2 플랫폼이라고 명명되었던 자바 버전 1.2가 출시되었다. 그리고 현재까지 많은 버전들이 출시되고 있다.

## Java의 10가지 특징

입문 단계에서는 10가지를 모두 외우기보다, `정적 타입`, `JVM 위 실행`, `가비지 컬렉션`, `풍부한 표준 라이브러리` 네 축을 먼저 기억하면 충분하다.

1. **단순 (Simple)**
   C(절차 지향) + C++(객체 지향) 언어를 기초로 하지만, C언어의 복잡한 기능을 제외하여 코드를 단순하게 작성할 수 있다. 특히 가비지 컬렉터(Garbage Collector)에 의한 자동 메모리 관리로 할당된 메모리 해제를 신경쓰지 않아도 된다.
2. **객체지향 (Object-Oriented)**
   자바는 클래스와 객체를 중심으로 프로그램을 구성한다. 이를 통해 상태와 동작을 함께 묶어 표현할 수 있고, 라이브러리와 재사용 가능한 코드 구조를 만들기 쉽다.
3. **분산 처리 (Distributed)**
   Java는 분산 환경에서 TCP/IP 등의 프로토콜을 통해 효율적으로 실행할 수 있도록 설계된 언어이다. Java는 다음을 지원한다.
   - TCP/IP 네트워크 기능 내장
   - HTTP, FTP 등과 같은 프로토콜에 대한 라이브러리 제공
   - 서로 다른 컴퓨터 상의 객체들도 원격으로 호출하여 실행할 수 있는 원격 메서드 호출과 관련된 RMI(Remote Method Invocation) 기능의 라이브러리 제공
4. **인터프리터 (Interpreter)**
   자바 소스 코드는 먼저 바이트코드로 컴파일되고, 그 바이트코드를 JVM이 실행한다. 자바 프로그램은 다음과 같은 실행 과정을 거친다.
   - 소스코드(.java) ▶︎ **컴파일(Compile): javac** ▶︎ 중간코드(.class): 바이트 코드, 클래스 파일 ▶︎ **기계어로 해석(Interprete): java** ▶︎ 실행
5. **견고 (Robust)**
   다양한 플랫폼(컴퓨터) 상에서 실행되기 위해서는 **높은 신뢰성**이 중요하다. 자바는 다음과 같은 기능들을 지원함으로서 높은 신뢰성을 구현하였다.
   - 포인터를 사용하지 않음
   - 가비지 컬렉션(Garbage Collector) 기능
   - 엄격한 데이터 타입의 검사 : 에러 조기 발견
   - Runtime 에러 처리

## Java 특징 이어서 보기

앞의 다섯 가지가 "왜 Java가 비교적 안전하게 실행되는가"를 설명했다면,
아래 다섯 가지는 "왜 여러 환경에서 계속 쓰이는가"를 설명한다고 보면 된다.

6. **안전 (Secure)**
   컴파일 시 엄격한 검사를 통해 프로그램 실행 시 발생할 수 있는 장애를 미리 방지한다. 소스코드가 컴파일된 .class 형태의 바이트코드는 **클래스 로더**, **바이트 코드 검증기**를 거친다. 이 때 문제가 없으면 인터프리터로 넘겨 실행하게 된다.
   - 클래스 로더 : 코드가 자신/다른 컴퓨터에서 온 것인지 판단하고 **코드를 분리**한다.
   - 바이트 코드 검증기 : **코드를 검증**하여 문제가 없을 시 인터프리터로 넘긴다.
7. **플랫폼 독립적 (Architecture Neutral)**
   운영체제, CPU 등의 **하드웨어 사양에 관계 없이 실행**될 수 있다. 작성된 자바 프로프램은 자바 컴파일러를 거쳐 자바 가상 머신에서 기계어로 번역되게 된다. 번역된 기계어 코드는 하드웨어 사양에 관계 없이 동일하게 실행된다.
8. **높은 성능 (High Performance)**
   자바는 JVM의 JIT 최적화와 런타임 최적화를 통해 많은 환경에서 실용적인 성능을 낸다. 자동 메모리 관리는 성능 그 자체라기보다 개발 생산성과 안전성에 큰 장점을 준다.
9. **멀티스레드 (Multithread)**
   자바는 멀티스레드를 지원한다. 이는 한 번에 여러 개의 스레드가 동시에 수행되는 과정으로, 하나의 CPU가 여러 프로그램을 동시에 수행하도록 함으로서 수행 속도를 빠르게 한다.
10. **동적 (Dynamic)**
    자바는 변화되는 환경에 잘 적응하도록 설계된 언어이다. 따라서 기존의 프로그램에 영향을 주지 않고 라이브러리에 새로운 메서드나 속성들을 추가할 수 있으며, 프로그램 간 라이브러리의 연결을 Runtime에 수행함으로써 라이브러리의 변화를 곧바로 적용할 수 있다.

## Java 플랫폼

플랫폼(Platform)이란, 프로그램이 실행될 수 있는 HW 및 SW 환경을 의미한다.

일반적인 플랫폼은 하드웨어 및 하드웨어를 제어하는 운영체제로 구성되어 있지만, 자바 플랫폼은 소프트웨어만으로 구성된다. 자바 플랫폼은 일반적으로 JDK(Java Development Kit)라는 툴로 설치된다.

### 자바 플랫폼의 종류

- **Java SE (Java 2 Platform Standard Edition)**
   가장 기본이 되는 에디션, 자바 언어 대부분의 패키지가 포함된다.
- **Java EE (Java 2 Platform Enterprise Edition)**
   현업에서 사용되는 API들이 집약된 에디션이다. (JSP, Servlet, JDBC 등)
- **Java ME (Java 2 Platform Micro Edition)**
   모바일 기기 등에서 사용되는 API가 포함된 에디션이다.

### 자바 플랫폼의 구조

자바 프로그램은 **자바 가상 머신** 위에서 동작한다. 자바 가상 머신에는 **자바 API** (자바 프로그램을 작성하는 데 기본적으로 활용할 수 있는 클래스 라이브러리, 즉 표준 API 라이브러리)가 제공된다.

![image](https://user-images.githubusercontent.com/22045163/104326478-20603f80-552d-11eb-8845-4a6bf5218570.png)

**자바 가상 머신(JVM, Java Virtual Machine)** 은 자바 프로그램과 운영체제 중간에 존재하여 서로를 분리함으로써, 애플리케이션이 운영체제에 영향 받지 않고 동작할 수 있는 환경을 제공한다. 단, JVM은 운영체제와 직접적으로 통신을 해야 하기 때문에 운영체제에 맞는 JVM을 설치해주어야 한다.

**자바 API(Application Programming Interface)** 는 프로그래머가 필요로 하는 기본적인 클래스(Class)들을 거대한 라이브러리로 미리 만들어서 제공한다. 자바 언어 자체는 작고 단순한 구조를 갖지만, 많은 기능들을 API에서 제공하고 있다. 자바 API는 관련된 기능의 클래스들을 묶어 패키지의 형태로 제공한다. _(주요 패키지 : java.applet, java.awt, java.io, java.lang, java.net, javax.swing, java.util)_

## Java 프로그램 구조

- **자바 클래스(class)** 는 자바 프로그램의 최소 구성 단위로, 선언된 클래스 내부에 실행에 필요한 변수나 메서드 등이 정의된다. 일반적으로 자바 프로그램은 하나의 `.java` 파일에 하나의 클래스 정의를 원칙으로 한다.
- **자바 애플리케이션** 은 바이트 코드로 번역된 후에 바로 실행할 수 있는 프로그램이다. 클래스 내에 `main()` 메서드를 가지고 있어야 한다.
- 자바는 **블록(`{}`)** 으로 자바 문장들의 집합을 표현한다. 블록의 시작과 끝이 짝을 이루지 않으면 컴파일 오류가 발생하며, 클래스, 메서드, 자바 구문(`if`, `for`, `try-catch` 등)에 사용된다.
- 자바 문장은 **세미콜론(`;`)** 을 사용해 문장들을 구분한다.

```java
public class 클래스명 {
  // 변수 정의
  // 메서드 정의
  public static void main(String args[]) {
    // 실행될 프로그램 코드
  }
}
```

## 가장 작은 예시로 읽기

처음에는 긴 문법 목록보다 짧은 예시 한 개를 끝까지 읽는 편이 낫다.

```java
public class HelloOrder {
  static int defaultPrice = 1000;

  public static void main(String[] args) {
    int quantity = 2;
    int totalPrice = defaultPrice * quantity;
    System.out.println(totalPrice);
  }
}
```

| 코드 조각 | 역할 |
|---|---|
| `public class HelloOrder` | 클래스 선언이다 |
| `static int defaultPrice = 1000;` | 클래스에 속한 필드다 |
| `main(String[] args)` | 프로그램 실행 시작점이다 |
| `int quantity = 2;` | 메서드 안에서만 쓰는 지역 변수다 |
| `System.out.println(totalPrice);` | 계산 결과를 콘솔에 출력한다 |

입문자가 보면 좋은 포인트는 두 가지다.

- Java는 **타입을 먼저 쓰고 변수 이름을 쓴다**. 예: `int quantity`
- 클래스 바깥에 바로 코드를 쓰는 것이 아니라, **클래스와 메서드 안에 코드를 넣는다**

## Java 데이터 타입 먼저 보는 큰 그림

타입은 값을 "어떤 규칙으로 저장하고 계산할지"를 정하는 이름표다.
처음에는 "칸의 종류를 먼저 정하고 값을 넣는다"는 감각으로 보면 된다.

| 구분 | 대표 예시 | 한 줄 감각 |
|---|---|---|
| 기본형(primitive) | `int`, `double`, `boolean`, `char` | 변수에 실제 값이 바로 들어간다 |
| 참조형(reference) | `String`, 배열, 사용자 정의 class | 변수에는 대상을 가리키는 참조가 들어간다 |

`int age = 20;`과 `String name = "Kim";`은 둘 다 변수 선언이지만, 내부적으로 저장되는 방식은 다르다.

자주 헷갈리는 포인트:

- `String`은 기본형이 아니라 참조형이다.
- 숫자 리터럴에서 형을 안 쓰면 정수는 `int`, 실수는 `double`로 본다.

## Java 데이터 타입 기본형 한눈에 보기

| 분류 | 타입 | 크기 | 기본값(필드 기준) |
|---|---|---|---|
| 논리 | `boolean` | JVM 구현 의존(보통 1byte 이상) | `false` |
| 문자 | `char` | 2byte | `'\u0000'` |
| 정수 | `byte` / `short` / `int` / `long` | 1 / 2 / 4 / 8byte | `0` / `0` / `0` / `0L` |
| 실수 | `float` / `double` | 4 / 8byte | `0.0F` / `0.0D` |

처음에는 `int`, `long`, `double`, `boolean`, `char` 다섯 개를 우선 익히면 충분하다.

- `long` 리터럴은 보통 `L`을 붙인다. 예: `3_000_000_000L`
- `float` 리터럴은 `F`를 붙인다. 예: `3.14F`
- 지역 변수는 자동 초기화되지 않고, 참조형 기본값 `null`도 지역 변수에는 자동 적용되지 않는다.

## Java 형변환 자동 변환과 명시적 캐스팅

작은 범위에서 큰 범위로 가는 변환은 보통 자동으로 된다(promotion).
반대로 큰 범위에서 작은 범위로 줄일 때는 명시적으로 캐스팅해야 한다(demotion).

```java
int age = 25;
double avgAge = age; // 자동 변환

double score = 24.56;
int roundedDown = (int) score; // 24
```

기본 규칙은 `byte -> short -> int -> long -> float -> double` 흐름으로 기억하면 된다.

자주 헷갈리는 포인트:

- `(int)24.56`처럼 축소 캐스팅하면 소수점 아래는 버려진다.
- 축소 캐스팅은 컴파일은 되더라도 값이 깨질 수 있다. 예: `int 128`을 `byte`로 캐스팅하면 `-128`이 된다.
- 연산 중 정수 오버플로우는 예외 없이 값이 wrap-around될 수 있다. 실전 체크는 [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)에서 이어서 본다.

## Java 변수와 스코프 필드 vs 지역 변수

변수는 "값에 이름을 붙여 다시 쓰기 쉽게 만든 칸"이고, 선언 위치에 따라 성질이 달라진다.

| 구분 | 주로 선언하는 위치 | 자동 초기화 | 사용 가능 범위(scope) |
|---|---|---|---|
| 필드(field) | 클래스 블록 안, 메서드 밖 | O | 객체/클래스 수명과 함께 유지 |
| 지역 변수(local) | 메서드/블록 안 | X | 선언된 블록 안에서만 사용 |

```java
public class InitExample {
  static int count;

  public static void main(String[] args) {
    int local;
    System.out.println(count); // 0
    // System.out.println(local); // 컴파일 에러
  }
}
```

- `count`처럼 필드는 기본값으로 초기화된다.
- `local`처럼 지역 변수는 값을 넣기 전에는 사용할 수 없다.
- `for (int i = 0; ... )`에서 선언한 `i`는 반복문 밖에서 쓸 수 없다.

scope와 지역 변수 초기화 감각을 코드로 더 연습하려면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)으로 이어서 보면 좋다.

## Java 연산자

### 산술 연산자

- 정수형, 실수형에 사용됨
- 증감 연산자 : `++`, `--` (단항)
- 부호 연산자 : `+`, `-`, `*`, `/` (이항)
- 나머지 연산자 : `%` (이항)

### 비교 연산자

- 대소 비교나 객체의 타입 비교 등에 사용됨
- 비교 연산을 수행한 결과로 `boolean` 타입의 결과를 리턴함
- `>`, `>=`, `<`, `<=`, `==`, `!=`, `instanceof`
  - `값1 instanceof 값2` : `값1`이 `값2` 데이터 타입의 객체인 경우 `true` 반환

### 논리 연산자

- `boolean` 데이터 타입에 적용되며, `boolean` 타입의 결과를 리턴함
- `&`, `&&`, `|`, `||`, `!`
  - `값1 && 값2`의 경우, `값1`이 `false`인 경우 `값2`를 수행하지 않고 `false`를 리턴한다.
  - `값1 || 값2`의 경우, `값1`이 `true`인 경우 `값2`를 수행하지 않고 `true`를 리턴한다.
  - `&`, `|` 연산자는 모든 조건을 다 확인한 후 그 결과를 리턴한다.

### 비트 연산자

- 값을 비트(bit)로 연산하는 연산자
- 메모리를 최대한 효율적으로 활용해야 하는 경우 비트 단위로 데이터를 관리해야 한다.
- `&` 논리곱(and), `|` 논리합(or), `^` 배타 논리합(exclusive or, XOR), `~` 보수(not)
- `>>`, `>>>`, `<<` 시프트
  - `값1 >> 값2` : `값1`을 비트 단위로 `값2`의 비트 수만큼 오른쪽으로 시프트, 왼쪽에는 현재 부호 비트가 채워짐
  - `값1 >>> 값2` : `값1`을 비트 단위로 `값2`의 비트 수만큼 오른쪽으로 시프트, 왼쪽에는 0이 채워짐
  - `값1 << 값2` : `값1`을 비트 단위로 `값2`의 비트 수만큼 왼쪽으로 시프트, 오른쪽에는 0이 채워짐

### 기타 연산자

- 대입 연산자 (`=`) : 변수의 값을 저장, 오른쪽의 값을 왼쪽에 대입
- 조건 삼항 연산자 (`? :`) : `if~else`문을 축약하여 사용할 수 있다.
  - `변수 = 조건 ? 값1 : 값2` : 조건이 참이면 `값1`이 변수에 대입되고, 거짓이면 `값2`가 변수에 대입된다.

## Java 배열: 먼저 잡는 감각

배열은 같은 타입 값을 여러 칸에 담는 자료형이다.
처음에는 "번호표(`index`)가 붙은 칸 묶음"으로 이해하면 된다.

| 기억할 것 | 초보자용 설명 |
|---|---|
| 길이(length) | 배열을 만들 때 칸 수가 정해진다 |
| 인덱스(index) | 첫 칸은 `0`, 두 번째 칸은 `1`이다 |
| 같은 타입 | `int[]`에는 `int`만, `String[]`에는 `String`만 넣는다 |
| 기본값 | 새 배열 칸은 타입별 기본값으로 채워진다 |

### 일차원 배열 선언과 생성

- 배열 변수 선언: `데이터타입[] 배열변수명;` 또는 `데이터타입 배열변수명[];`
- 배열 생성: `배열변수명 = new 데이터타입[길이];`
- 둘을 합치면 `int[] prices = new int[3];`처럼 한 줄로 쓸 수 있다.

## 일차원 배열 손추적과 자주 보는 오류

```java
int[] prices = new int[3];
prices[0] = 1200;
prices[1] = 1500;
prices[2] = 900;

int secondPrice = prices[1];
System.out.println(secondPrice);
```

이 코드는 "칸 3개짜리 `int` 배열을 만들고, 값을 넣고, 두 번째 칸을 읽는다"는 흐름이다.

| 단계 | 배열 상태 | 읽을 포인트 |
|---|---|---|
| `new int[3]` 직후 | `[0, 0, 0]` | `int` 배열 기본값은 `0`이다 |
| `prices[0] = 1200` 후 | `[1200, 0, 0]` | 첫 칸은 인덱스 `0`이다 |
| `prices[1] = 1500` 후 | `[1200, 1500, 0]` | 두 번째 칸은 인덱스 `1`이다 |
| `prices[2] = 900` 후 | `[1200, 1500, 900]` | 세 번째 칸은 인덱스 `2`다 |
| `prices[1]` 읽기 | `1500` | `[]` 안 숫자로 칸을 고른다 |

자주 막히는 포인트:

| 코드 | 왜 막히는가 | 바로 기억할 규칙 |
|---|---|---|
| `System.out.println(prices.length());` | 배열 `length`는 메서드가 아니라 필드다 | 배열은 `arr.length`, 문자열은 `str.length()` |
| `prices[0] = "1200";` | `int[]` 칸에 `String`을 넣으려 해서 타입 불일치가 난다 | 배열 원소 타입과 값 타입이 같아야 한다 |
| `int[] numbers; numbers[0] = 1;` | 지역 변수 `numbers`를 초기화하지 않고 사용했다 | 지역 배열 변수도 먼저 참조 대상을 넣어야 한다 |

`prices[3] = 1000;`은 컴파일 오류가 아니라 런타임 오류다.
길이가 3이면 유효한 인덱스는 `0`, `1`, `2`뿐이라 실행 중 `ArrayIndexOutOfBoundsException`이 난다.

## 이차원 배열과 명령행 매개변수

이차원 배열은 "배열 안에 배열이 들어 있는 구조"다.

- 선언 예: `int[][] seats;`
- 생성 예: `seats = new int[3][4];`
- 행 길이를 나중에 정하려면 `new int[3][]`로 만들고 각 행을 따로 `new` 한다.

`main(String[] args)`의 `args`는 명령행 매개변수 배열이다.

```java
public class CommandLineArgTest {
  public static void main(String[] args) {
    // code
  }
}
```

- 실행 시 넘긴 문자열이 `args`에 순서대로 들어간다.
- 공백으로 값을 여러 개 전달할 수 있다.
- 숫자로 쓰려면 `Integer.parseInt(...)`, `Double.parseDouble(...)` 같은 변환이 필요하다.

## Java 제어문

제어문은 "어느 줄을 실행할지, 몇 번 반복할지, 여기서 멈출지"를 정하는 문법이다.

| 종류 | 대표 문법 | 초보자용 감각 |
|---|---|---|
| 조건 제어문 | `if`, `if-else`, `if-else if`, `switch` | 조건에 따라 다른 길로 보낸다 |
| 반복 제어문 | `for`, `while`, `do-while` | 같은 작업을 여러 번 돌린다 |
| 이동 제어문 | `break`, `continue`, `return` | 반복이나 메서드 흐름을 중간에 바꾼다 |

### 손으로 따라가는 제어 흐름 예시

```java
int[] scores = {85, 72, 91};
int passedCount = 0;

for (int i = 0; i < scores.length; i++) {
  if (scores[i] >= 80) {
    passedCount++;
  }
}

System.out.println(passedCount);
```

이 코드는 "배열을 앞에서부터 한 칸씩 보고, 80점 이상이면 합격 수를 1 올린다"는 흐름이다.

| 반복 차수 | `i` | `scores[i]` | 조건 `scores[i] >= 80` | `passedCount` 변화 |
|---|---|---|---|---|
| 시작 전 | - | - | - | `0` |
| 1번째 | `0` | `85` | `true` | `0 -> 1` |
| 2번째 | `1` | `72` | `false` | `1 유지` |
| 3번째 | `2` | `91` | `true` | `1 -> 2` |
| 반복 종료 후 | `3` | 접근 안 함 | `i < scores.length`가 `false` | 최종값 `2` |

여기서 꼭 볼 포인트는 세 가지다.

- `for`는 `i = 0`부터 시작해서 `i < scores.length`가 `false`가 될 때 멈춘다
- `if`는 조건이 `true`일 때만 블록 안 코드를 실행한다
- `passedCount++`는 조건이 맞은 횟수만큼만 증가한다

### 제어문에서 초보자가 자주 보는 컴파일 오류

| 코드 | 왜 막히는가 | 바로 기억할 규칙 |
|---|---|---|
| `if (score = 80) { ... }` | `score = 80`은 대입식이고 `int` 결과라서 `if` 조건의 `boolean` 자리에 못 들어간다 | Java의 `if` 조건은 반드시 `boolean`이어야 한다 |
| `break;` | 반복문이나 `switch` 밖에서 쓰면 컴파일 오류가 난다 | `break`는 loop/switch 안에서만 쓴다 |
| `for (int i = 0; i < 3; i++) { } System.out.println(i);` | `i`는 `for` 블록 안에서만 살아 있어서 바깥에서 못 쓴다 | 제어문 안에서 선언한 변수는 scope 밖으로 나가면 사라진다 |

## 초보자 혼동 포인트

문법 항목을 따로 외우기보다, "지금 헷갈리는 게 실행 도구인지, 값 종류인지, 문법 규칙인지"로 먼저 자르면 다음 읽기도 빨라진다.

| 헷갈리는 질문 | 먼저 붙잡을 구분 | 지금 기억할 한 줄 |
|---|---|---|
| "`JDK`와 `JVM`이 같은 말 아닌가?" | 개발 도구 vs 실행 환경 | `JDK`는 도구 묶음, `JVM`은 실행기 핵심이다 |
| "필드도 지역 변수도 그냥 0으로 시작하지 않나?" | 필드 vs 지역 변수 | 필드는 기본값이 있지만 지역 변수는 직접 초기화해야 한다 |
| "`arr.length`와 `str.length()`는 왜 다르지?" | 필드 vs 메서드 | 배열은 `length` 필드, 문자열은 `length()` 메서드다 |
| "`if (score = 80)`도 되지 않나?" | 값 대입 vs 조건식 | `if`/`while` 조건은 반드시 `boolean`이어야 한다 |

- `배열`, `String`, `객체`를 전부 같은 종류의 값처럼 느끼기 쉽다. Java에서는 기본형과 참조형을 나눠 읽는 습관이 중요하다.
- 객체 비교에서 `==`와 `.equals()`를 같은 의미로 보면 뒤에서 계속 막힌다. 이 부분은 별도 문서로 바로 넘어가는 편이 안전하다.
- 배열 인덱스 범위 초과를 컴파일 오류라고 느끼기 쉽다. `arr[3]`처럼 범위를 벗어나는 접근은 대개 실행 중에 터진다.

## 다음 읽을 문서

- 학습 흐름 전체를 다시 잡고 싶으면 [Language README: Java primer](../README.md#java-primer), [Junior Backend Roadmap: 1단계 자바 언어 감각 잡기](../../../JUNIOR-BACKEND-ROADMAP.md#1단계-자바-언어-감각-잡기)부터 본다.
- 처음 배우는데 "문법은 읽었는데 `class`, `object`, `instance`가 아직 말로만 헷갈린다"면 다음 문서는 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)이다.

| 이 문서에서 본 것 | 다음 문서에서 바로 이어지는 것 | 왜 이 순서가 beginner에게 안전한가 |
|---|---|---|
| `public class HelloOrder` | `class`는 무엇을 정의하는가 | 문법에서 본 `class` 키워드를 설계도 개념으로 연결한다 |
| `String[] args`, `int[] prices` | 기본형 vs 참조형, 참조 변수가 무엇인가 | 배열과 `String`을 "객체를 가리키는 값"으로 다시 읽게 해 준다 |
| `HelloOrder` 안의 필드와 메서드 | 객체가 상태와 동작을 함께 가진다는 뜻 | 필드/메서드 문법이 왜 객체 모델로 이어지는지 큰 그림을 잡게 해 준다 |
| `new int[3]` 같은 생성 표현 | `new Student(...)`로 객체를 만드는 감각 | 배열 생성에서 본 `new`를 객체 인스턴스화로 자연스럽게 확장한다 |

- 한 줄로 줄이면 이렇다: `문법으로 class를 봄 -> new로 대상을 만듦 -> 그 결과를 object/instance라고 부름`.
- 그래서 이 문서 다음에는 배열 심화로 바로 흩어지기보다, 먼저 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)에서 `class/object/instance` 브리지를 한 번 통과하면 초반 이탈이 줄어든다.
- 메서드, 생성자, `this`, 반환값이 같이 헷갈리면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)으로 간다.
- package / import / 파일 구조가 걸리면 [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)으로 바로 이동한다.
- 배열은 "비교 / 복사 / 정렬-검색" 중 어디서 막혔는지 먼저 자르고 아래 표에서 고른다.

| 지금 보이는 증상 | 먼저 읽을 문서 | 이 문서를 먼저 읽는 이유 |
|---|---|---|
| "내용이 같은데 `==`가 false고, `equals()`도 기대처럼 안 맞는다" | [Java Array Equality Basics](./java-array-equality-basics.md) | "같은 배열 객체인가"와 "칸 값이 같은가"를 먼저 분리해 `==`/`Arrays.equals`/`Arrays.deepEquals` 선택을 고정해 준다 |
| "`copied = original` 했는데 원본/복사본이 같이 변한다" | [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md) | 대입(alias)과 실제 복사(`clone`/`copyOf`)를 분리하고, 중첩 배열에서 왜 shallow copy가 되는지까지 바로 연결해 준다 |
| "`sort` 후 원본 순서가 깨지고, `binarySearch` 결과가 이상하다" | [Sorting and Searching Arrays Basics](./java-array-sorting-searching-basics.md) | `sort`가 제자리 정렬이라는 점과 "정렬할 때 쓴 규칙으로 검색해야 한다"는 전제를 함께 잡아 준다 |

- 배열을 문법이 아니라 자료구조 감각으로 넓히려면 [배열 vs 연결 리스트](../../data-structure/array-vs-linked-list.md)

## 백엔드 4레인 연결

- Java 문법 다음에 Spring 실행 흐름으로 붙이려면 [Spring 요청 파이프라인과 Bean Container 기초](../../spring/spring-request-pipeline-bean-container-foundations-primer.md)로 넘어간다.
- HTTP 요청이 실제로 어떻게 들어오는지 먼저 보고 싶다면 [HTTP 요청-응답 기본 흐름](../../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)로 간다.
- SQL/모델링을 먼저 잡고 싶다면 [SQL 읽기와 관계형 모델링 기초](../../database/sql-reading-relational-modeling-primer.md)로 이어진다.

## 한 줄 정리

Java 배열은 "같은 타입 칸 묶음"으로, 제어문은 "실행 흐름 조절 장치"로 먼저 이해하고, `length`/scope/`boolean` 조건 같은 초보자 compile-error 포인트를 함께 익히면 첫 문법 독해가 훨씬 안정적이다.
