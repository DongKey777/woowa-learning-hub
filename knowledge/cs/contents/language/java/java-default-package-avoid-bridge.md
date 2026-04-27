# Java default package 회피 브리지

> 한 줄 요약: 파일명 규칙까지 익혔다면 다음으로는 `package` 선언을 생략한 default package를 왜 실제 Java 코드에서 피하는지, "처음엔 편하지만 곧 연결이 막힌다"는 관점으로 짧게 이어서 보면 된다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java default package avoid bridge basics, java default package avoid bridge beginner, java default package avoid bridge intro, java basics, beginner java, 처음 배우는데 java default package avoid bridge, java default package avoid bridge 입문, java default package avoid bridge 기초, what is java default package avoid bridge, how to java default package avoid bridge
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Java Top-level 타입 접근 제한자 브리지](./top-level-type-access-modifier-bridge.md)
> - [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
> - [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)

> retrieval-anchor-keywords: java default package avoid bridge, java unnamed package beginner, java package declaration why needed, java no package declaration problem, java default package cannot import, java named package cannot use default package class, java default package avoid beginner, java source file package declaration basics, java top-level file name next step, 자바 default package 왜 피하나, 자바 package 선언 왜 붙이나, 자바 package 선언 생략 문제, 자바 unnamed package, 자바 default package import 안됨, 자바 default package 회피 브리지, 자바 파일명 규칙 다음 단계

## 먼저 잡는 멘탈 모델

default package는 "주소 없이 메모만 붙여 둔 파일"에 가깝다.

- 처음 한 파일만 만들 때는 빨라 보인다.
- 파일이 두세 개로 늘어나면 어디 소속인지, 다른 코드가 어떻게 연결하는지 바로 흐려진다.
- named package 코드는 이 파일들을 정상적으로 import해서 쓰기 어렵다.

초보자 기준 기본값은 단순하다.

> 연습 코드라도 top-level 타입을 만들면 `package ...;`부터 붙이는 습관이 더 안전하다.

## 왜 곧 불편해지나

| 선택 | 처음 느낌 | 금방 생기는 문제 |
|---|---|---|
| default package | 빨리 시작하는 것처럼 보임 | 구조화, import, 파일 이동이 금방 어색해짐 |
| named package | 한 줄 더 써야 함 | 파일 소속과 경계가 바로 보임 |

핵심 이유는 세 가지면 충분하다.

1. `package`가 없으면 파일 소속이 코드에 드러나지 않는다.
2. named package 쪽으로 코드를 옮기기 시작하면 연결이 끊기기 쉽다.
3. helper와 API를 package 경계로 나누는 연습을 못 하게 된다.

## 가장 많이 막히는 지점: import

초보자가 많이 하는 기대는 이것이다.

"처음엔 default package로 쓰다가, 나중에 package 있는 코드에서 import하면 되겠지?"

보통 여기서 막힌다.

```java
// Hello.java
public class Hello {
    public String message() {
        return "hi";
    }
}
```

```java
// com/example/app/Main.java
package com.example.app;

public class Main {
    public static void main(String[] args) {
        Hello hello = new Hello();
    }
}
```

`Main`은 named package 안에 있고, `Hello`는 default package에 있다.
이 조합은 초보자가 기대하는 식으로 자연스럽게 연결되지 않는다.

즉 "package 없는 파일을 나중에 import해서 쓰자"는 흐름이 잘 안 통한다.
처음부터 `package com.example.app;`처럼 소속을 붙여 두는 편이 훨씬 덜 꼬인다.

## 같은 예시를 package로 바꾸면

```java
// com/example/app/Hello.java
package com.example.app;

public class Hello {
    public String message() {
        return "hi";
    }
}
```

```java
// com/example/app/Main.java
package com.example.app;

public class Main {
    public static void main(String[] args) {
        Hello hello = new Hello();
    }
}
```

이제 초보자 눈에도 구조가 바로 읽힌다.

- 둘 다 `com.example.app` 소속이다.
- 같은 package라면 import 없이도 simple name으로 이어진다.
- 나중에 `internal`, `api`처럼 역할을 나눌 자리도 생긴다.

## 자주 하는 오해

- default package는 "더 쉬운 package"가 아니다. 그냥 `package` 선언을 생략한 특별 케이스에 가깝다.
- 파일명 규칙을 지켜도 package 설계 문제는 별도로 남는다. `Hello.java`가 맞는 이름이어도 default package 문제는 해결되지 않는다.
- "연습용인데 한 파일뿐"이면 잠깐은 가능하다. 하지만 두 번째, 세 번째 파일이 생기는 순간부터 named package 습관이 더 이득이다.
- `import`는 이름을 줄여 주는 문법이지, default package의 구조 문제를 해결해 주는 도구가 아니다.

## 초보자용 기본 선택

| 상황 | 추천 |
|---|---|
| 지금 막 Java 문법 한 줄 실험 | 잠깐 default package 가능 |
| 두 파일 이상으로 나누기 시작함 | 바로 named package로 전환 |
| helper / service / model을 구분하려 함 | 처음부터 package 선언 사용 |

## 한 줄 정리

default package는 시작은 빨라 보여도 파일이 늘어날수록 연결과 구조가 막히기 쉬우므로, top-level 파일을 만들기 시작했다면 `package` 선언을 붙이는 쪽이 초보자에게 더 안전하다.
