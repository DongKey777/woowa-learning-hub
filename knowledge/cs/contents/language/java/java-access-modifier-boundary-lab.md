---
schema_version: 3
title: Access Modifier Boundary Lab
concept_id: language/java-access-modifier-boundary-lab
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- protected-reference-qualifier
- same-package-vs-cross-package
- access-modifier-prediction
aliases:
- java access modifier boundary lab basics
- java access modifier boundary lab beginner
- java access modifier boundary lab intro
- java basics
- beginner java
- 처음 배우는데 java access modifier boundary lab
- java access modifier boundary lab 입문
- java access modifier boundary lab 기초
- what is java access modifier boundary lab
- how to java access modifier boundary lab
symptoms:
- protected가 하위 클래스 안이면 무조건 되는 줄 알았는데 참조에 따라 달라져
- 같은 패키지와 다른 패키지 접근 결과를 손으로 확인하고 싶어
- 컴파일 성공 실패를 직접 예측해 보면서 접근 제한자를 익히고 싶어
intents:
- definition
prerequisites:
- language/java-access-modifiers-member-model-basics
- language/java-package-import-boundary-basics
- language/java-package-boundary-quickcheck-card
- language/java-access-modifier-top-level-member-mini-quiz
next_docs:
- language/java-inheritance-overriding-basics
linked_paths:
- contents/language/java/java-access-modifiers-member-model-basics.md
- contents/language/java/java-package-import-boundary-basics.md
- contents/language/java/java-package-boundary-quickcheck-card.md
- contents/language/java/java-access-modifier-top-level-member-mini-quiz.md
- contents/language/java/top-level-type-access-modifier-bridge.md
- contents/language/java/java-inheritance-overriding-basics.md
confusable_with:
- language/java-access-modifier-top-level-member-mini-quiz
- language/java-package-boundary-quickcheck-card
forbidden_neighbors:
- contents/language/java/top-level-type-access-modifier-bridge.md
- contents/language/java/java-access-modifier-top-level-member-mini-quiz.md
- contents/language/java/java-package-boundary-quickcheck-card.md
expected_queries:
- protected this childRef parentRef 차이를 손으로 확인하는 실습이 필요해
- 같은 패키지와 다른 패키지에서 private package-private protected 결과를 직접 보고 싶어
- 접근 제한자 컴파일 성공 실패를 예제로 연습할 문서를 찾고 있어
- Java protected가 부모 타입 참조에서는 왜 막히는지 워크시트로 보고 싶어
- subclass 내부 접근과 외부 접근을 같이 비교하는 lab이 필요해
contextual_chunk_prefix: |
  이 문서는 학습자가 private, package-private, protected가 같은
  패키지와 다른 패키지 하위 클래스에서 어떻게 갈리는지 손으로
  확인하며 처음 잡는 primer다. 컴파일 성공 실패 예측, this와 부모
  참조 차이, 다른 패키지 subclass 내부 접근, 표로 확인하는 접근
  경계, 직접 돌려 보는 작은 실습, protected가 왜 참조 타입에 따라
  막히는지 같은 자연어 paraphrase가 본 문서의 실습 흐름에
  매핑된다.
---
# Access Modifier Boundary Lab

> 한 줄 요약: `private`/package-private/`protected`를 "같은 클래스, 같은 패키지, 다른 패키지" 3개 경계에서 직접 확인하는 초소형 실행 실습이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java access modifier boundary lab basics, java access modifier boundary lab beginner, java access modifier boundary lab intro, java basics, beginner java, 처음 배우는데 java access modifier boundary lab, java access modifier boundary lab 입문, java access modifier boundary lab 기초, what is java access modifier boundary lab, how to java access modifier boundary lab
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md) - `this`/`childRef`/`parentRef` follow-up 예제를 먼저 읽고 오면 아래 3문항 follow-up이 더 빨라진다
> - [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
> - [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)

> retrieval-anchor-keywords: java access modifier boundary lab, java private package-private protected example, java same package access, java cross package access, java protected subclass access, java access modifier compile error lab, java beginner access modifier practice, java access modifier mini quiz, java compile success fail prediction worksheet, java protected compile error quiz, java protected this childRef parentRef lab, java protected 3 question follow-up, java this protected vs baseRef protected quiz, java childRef protected access quiz, java access modifier follow-up example practice, 자바 접근제한자 실습, 자바 private protected package-private 차이 예제, 같은 패키지 다른 패키지 접근 테스트, 자바 컴파일 성공 실패 퀴즈, 자바 protected 후속 문제, 접근제한자 워크시트

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교표](#한-장-비교표)
- [패키지 분리 실습 코드](#패키지-분리-실습-코드)
- [실행해서 결과 확인하기](#실행해서-결과-확인하기)
- [기본 경계 미니 퀴즈 (2문항)](#기본-경계-미니-퀴즈-2문항)
- [protected 3문항 follow-up 워크시트](#protected-3문항-follow-up-워크시트)
- [초보자가 자주 헷갈리는 포인트](#초보자가-자주-헷갈리는-포인트)
- [다음 읽기](#다음-읽기)

</details>

## 먼저 잡을 mental model

처음에는 용어보다 "문을 몇 겹으로 잠그는가"로 보면 쉽다.

- `private`: 같은 클래스 안에서만 여는 개인 금고
- package-private: 같은 패키지(같은 팀 방)까지만 여는 문
- `protected`: 같은 패키지는 열고, 다른 패키지는 "하위 클래스 내부"에서만 여는 문

즉 판단 순서는 아래 2단계면 충분하다.

1. 지금 호출 위치가 같은 패키지인가?
2. 다른 패키지라면 하위 클래스 내부인가?

이 lab은 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)의 마지막 `protected` follow-up 예제를 손으로 확인하는 버전이다.

- primer에서 `this.points` / `childRef.points` / `parentRef.points` 차이를 봤다면
- 여기서는 그 차이를 `BetaSubVault`와 퀴즈 3~4번으로 바로 검증하면 된다

## 한 장 비교표

| 접근 위치 | `private` | package-private | `protected` |
|---|---|---|---|
| 같은 클래스 | 가능 | 가능 | 가능 |
| 같은 패키지 다른 클래스 | 불가 | 가능 | 가능 |
| 다른 패키지 일반 클래스 | 불가 | 불가 | 불가 |
| 다른 패키지 하위 클래스 내부 | 불가 | 불가 | 가능 |

## 패키지 분리 실습 코드

아래처럼 `lab.alpha`와 `lab.beta` 두 패키지를 만든다.

```text
src/
  lab/alpha/
    Vault.java
    SamePackageProbe.java
  lab/beta/
    BetaSubVault.java
    BetaOtherProbe.java
```

`Vault.java`

```java
package lab.alpha;

public class Vault {
    private int privatePin = 1111;
    int packagePin = 2222;                 // package-private
    protected int protectedPin = 3333;

    public int readInsideClass() {
        return privatePin + packagePin + protectedPin; // OK
    }
}
```

`SamePackageProbe.java`

```java
package lab.alpha;

public class SamePackageProbe {
    public static void main(String[] args) {
        Vault v = new Vault();

        // System.out.println(v.privatePin);  // compile error
        System.out.println(v.packagePin);      // OK
        System.out.println(v.protectedPin);    // OK
    }
}
```

`BetaSubVault.java`

```java
package lab.beta;

import lab.alpha.Vault;

public class BetaSubVault extends Vault {
    public void testInSubclass() {
        // System.out.println(privatePin);  // compile error
        // System.out.println(packagePin);  // compile error
        System.out.println(protectedPin);   // OK (subclass 내부)
    }

    public void compareRefs(BetaSubVault childRef, Vault baseRef) {
        System.out.println(this.protectedPin);      // OK
        System.out.println(childRef.protectedPin);  // OK
        // System.out.println(baseRef.protectedPin); // compile error
    }
}
```

## 패키지 분리 실습 코드 (계속 2)

위 두 메서드는 primer의 "`this.points`/`childRef.points`는 되지만 `parentRef.points`는 안 된다"는 follow-up 예제를 그대로 옮긴 것이다.
그래서 이 파일을 읽을 때는 "하위 클래스 자기 자신이나 같은 하위 클래스 계열 참조인가, 아니면 부모 타입 참조인가?"를 먼저 체크하면 된다.

`BetaOtherProbe.java`

```java
package lab.beta;

import lab.alpha.Vault;

public class BetaOtherProbe {
    public static void main(String[] args) {
        Vault v = new Vault();

        // System.out.println(v.privatePin);   // compile error
        // System.out.println(v.packagePin);   // compile error
        // System.out.println(v.protectedPin); // compile error
    }
}
```

## 실행해서 결과 확인하기

`compile error` 라인이 주석 해제되면 실패하고, 나머지는 성공해야 한다.

```bash
javac -d out $(find src -name "*.java")
java -cp out lab.alpha.SamePackageProbe
```

예상 결과:

- `SamePackageProbe`: `packagePin`, `protectedPin` 접근 성공
- `BetaSubVault`: 하위 클래스 내부에서 `protectedPin` 접근 성공
- `BetaOtherProbe`: 세 필드 모두 접근 실패

## 기본 경계 미니 퀴즈 (2문항)

먼저 실행하지 말고, 각 문항을 보고 `성공`/`실패`를 먼저 적는다.

| 문항 | 예측 (`성공`/`실패`) | 한 줄 이유 |
|---|---|---|
| 1 |  |  |
| 2 |  |  |

### 문항 1

`lab.alpha.SamePackageProbe` 안에서:

```java
Vault v = new Vault();
System.out.println(v.packagePin);
```

### 문항 2

`lab.beta.BetaOtherProbe` 안에서:

```java
Vault v = new Vault();
System.out.println(v.protectedPin);
```

<details>
<summary>정답 확인</summary>

| 문항 | 정답 | 핵심 이유 |
|---|---|---|
| 1 | 성공 | 같은 패키지에서 package-private 접근 가능 |
| 2 | 실패 | 다른 패키지 일반 클래스에서는 `protected` 불가 |

</details>

## protected 3문항 follow-up 워크시트

이제 핵심 오개념만 따로 본다.
포인트는 "`하위 클래스 안`이면 끝"이 아니라 "`어떤 참조로 보느냐`까지 봐야 한다"는 점이다.

| 문항 | 예측 (`성공`/`실패`) | 한 줄 이유 |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

### follow-up 1

`lab.beta.BetaSubVault extends Vault` 안의 메서드에서:

```java
System.out.println(this.protectedPin);
```

### follow-up 2

`lab.beta.BetaSubVault extends Vault` 안의 메서드에서:

```java
BetaSubVault childRef = new BetaSubVault();
System.out.println(childRef.protectedPin);
```

### follow-up 3

`lab.beta.BetaSubVault extends Vault` 안의 메서드에서:

```java
Vault baseRef = new Vault();
System.out.println(baseRef.protectedPin);
```

이 문항이 가장 중요하다.
같은 `protectedPin`이어도 `this`/`childRef`와 `baseRef`의 결과가 갈린다는 점을 일부러 비교하는 자리다.

<details>
<summary>정답 확인</summary>

| 문항 | 정답 | 핵심 이유 |
|---|---|---|
| 1 | 성공 | `this`는 하위 클래스 자기 자신의 inherited `protected` 멤버 접근 |
| 2 | 성공 | `childRef`도 `BetaSubVault` 계열 참조라 허용 |
| 3 | 실패 | 하위 클래스 내부라도 `baseRef`가 `Vault` 타입 참조라서 막힘 |

</details>

## 초보자가 자주 헷갈리는 포인트

- `protected`를 "다른 패키지면 무조건 가능"으로 오해하기
- 하위 클래스 안이면 `this.protectedPin`과 `baseRef.protectedPin`이 둘 다 될 거라고 오해하기
- package 이름이 비슷하면 같은 패키지라고 오해하기
- `import`하면 접근 제한이 풀린다고 오해하기

빠른 점검 질문:

1. 호출 코드가 같은 패키지인가?
2. 아니라면, 지금 코드가 하위 클래스 내부인가?
3. 하위 클래스 내부라면 `this`/`childRef`인가, 아니면 `baseRef` 같은 부모 타입 참조인가?
4. 둘 다 아니면 `protected`도 접근할 수 없다.

## 다음 읽기

- 기본 개념 먼저: [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 특히 `protected`의 `this`/`childRef`/`parentRef` 차이가 헷갈리면 primer의 [protected 3문항 follow-up](./java-access-modifiers-member-model-basics.md#protected-3문항-follow-up)부터 다시 본다
- 패키지 경계 보강: [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
- 상속 문맥 보강: [Java 상속과 오버라이딩 기초](./java-inheritance-overriding-basics.md)

## 한 줄 정리

`private`/package-private/`protected`를 "같은 클래스, 같은 패키지, 다른 패키지" 3개 경계에서 직접 확인하는 초소형 실행 실습이다.
