---
schema_version: 3
title: 'baseball 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나'
concept_id: spring/baseball-mvc-controller-binding-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/baseball
review_feedback_tags:
- request-binding
- bean-validation
- console-to-http
aliases:
- baseball Spring MVC
- 야구 미션 Controller
- 콘솔 야구 → HTTP
- 야구 게임 RequestBody 바인딩
- baseball 입력 검증 MVC
- baseball 게임 상태 매 요청 유지
- baseball session vs DB
- stateless HTTP game state
- gameId path vs session state
intents:
- mission_bridge
- design
prerequisites:
- spring/mvc-controller-basics
linked_paths:
- contents/spring/spring-mvc-controller-basics.md
- contents/spring/spring-modelattribute-vs-requestbody-binding-primer.md
- contents/spring/spring-bindingresult-local-validation-400-primer.md
- contents/spring/baseball-game-id-session-boundary-bridge.md
- contents/spring/baseball-game-state-singleton-bean-scope-bridge.md
forbidden_neighbors:
- contents/spring/spring-requestbody-400-before-controller-primer.md
confusable_with:
- spring/mvc-controller-basics
- spring/modelattribute-vs-requestbody-binding-primer
- spring/spring-bindingresult-local-validation-400-primer
- spring/baseball-game-id-session-boundary-bridge
expected_queries:
- 콘솔 야구를 Spring MVC로 옮기면 입력 처리는 어디서 해?
- 3자리 숫자 추측을 RequestBody로 받을 때 어떻게 검증해?
- "@ModelAttribute랑 @RequestBody 중 야구 미션엔 뭐가 맞아?"
- BindingResult를 Controller에서 어떻게 다뤄야 해?
- baseball 게임 상태를 매 요청마다 어떻게 유지해? 세션? DB?
contextual_chunk_prefix: |
  이 문서는 baseball 콘솔 미션을 Spring MVC로 옮길 때 입력 binding뿐 아니라
  stateless HTTP에서 gameId, session, DB 중 어디에 게임 상태를 둘지 묻는 mission
  bridge query를 받는다. Controller는 요청 DTO와 path/session 식별자를 받고,
  매 요청마다 필요한 game state는 singleton bean 필드가 아니라 session 또는 DB에
  두어야 한다는 boundary를 함께 설명한다.
---

# baseball 미션을 Spring MVC로 옮길 때 Controller binding/validation 어떻게 다루나

> 한 줄 요약: 콘솔 baseball의 *Scanner.nextLine() → 파싱*은 Spring MVC에서 *DTO + @Valid + @RequestBody*로 그대로 분리된다. 컨트롤러는 *형식만* 검증하고, 도메인 (`Numbers`, `Guess`)이 *3자리·중복없음·1-9 불변식*을 책임진다. 두 검증층을 섞지 않는 게 핵심.

**난이도: 🟢 Beginner**

**미션 컨텍스트**: baseball (Woowa Java 트랙) — 콘솔 → MVC 마이그레이션

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "콘솔 야구의 `Scanner.nextLine()`을 Spring에서는 어디로 옮겨요?" | 입력 수집, 문자열 파싱, 게임 판정이 controller에 한꺼번에 들어간 코드 | HTTP 요청 바인딩과 도메인 `Guess` 생성 책임을 분리한다 |
| "3자리 숫자 형식 검증과 중복 없음 규칙을 둘 다 `@Valid`로 처리하나요?" | `@Pattern`과 도메인 불변식이 한 DTO annotation 묶음으로 섞인 구조 | 형식 검증은 controller 입구, 3자리/중복 없음/1-9 규칙은 도메인으로 본다 |
| "게임 상태는 controller 필드에 둬도 되나요?" | 콘솔 객체 수명을 웹 singleton/controller 필드 수명으로 그대로 옮기는 시도 | 요청마다 gameId/session/DB로 같은 게임을 다시 찾는 경계를 세운다 |

관련 문서:

- [Spring MVC Controller Basics](./spring-mvc-controller-basics.md) — 일반 개념
- [@ModelAttribute vs @RequestBody](./spring-modelattribute-vs-requestbody-binding-primer.md) — 바인딩 분기
- [BindingResult / 400 응답](./spring-bindingresult-local-validation-400-primer.md) — 검증 실패 응답

## 미션의 어디에 binding 결정이 등장하는가

콘솔 baseball에서는 다음 두 단계를 한 메소드가 처리했다:

```java
String input = scanner.nextLine();           // 1) 입력 수집
Guess guess = parseGuess(input);             // 2) 파싱 + 검증
int strike = computer.judge(guess);
```

Spring MVC로 옮기면 *입력 수집*은 HTTP 요청이 되고, *파싱+검증*은 *DTO 바인딩 + Bean Validation*으로 분리된다:

```java
// dto/GuessRequest.java
public record GuessRequest(
    @NotBlank
    @Pattern(regexp = "\\d{3}", message = "3자리 숫자")
    String numbers
) {}

// controller/BaseballController.java
@RestController
@RequestMapping("/games")
public class BaseballController {
    private final BaseballService service;

    @PostMapping("/{gameId}/guesses")
    public GuessResponse guess(
        @PathVariable Long gameId,
        @Valid @RequestBody GuessRequest request
    ) {
        Guess guess = Guess.from(request.numbers());  // 도메인 불변식 검증
        return service.judge(gameId, guess);
    }
}
```

여기서 분기 결정 두 가지:

1. **요청 본문 형식 — JSON `@RequestBody` vs 폼 `@ModelAttribute`?**
2. **검증 위치 — 컨트롤러 `@Valid` vs 도메인 `Guess.from(...)` vs 둘 다?**

## 두 결정의 분기

### 결정 1 — `@RequestBody` (JSON) vs `@ModelAttribute` (form)

baseball을 *REST API*로 노출하면 답은 `@RequestBody`다:

- *프론트엔드*가 `fetch('/games/1/guesses', {method: 'POST', body: JSON.stringify({numbers: '123'})})`로 요청
- *Content-Type: application/json*
- 응답도 JSON

`@ModelAttribute`는 *form-encoded* (HTML form, `application/x-www-form-urlencoded`)일 때 자연스럽다. baseball UI가 *전통 form 페이지*라면 그쪽이 맞고, *SPA*라면 `@RequestBody`.

### 결정 2 — 컨트롤러 검증 vs 도메인 검증

두 층을 *모두 두되 책임을 분리*한다:

| 검증 층 | 무엇을 본다 |
| ------- | ----------- |
| `@Valid` + Bean Validation | *입력 형식* (null, 패턴, 길이) — 컨트롤러 진입 전 |
| `Guess.from(...)` | *도메인 불변식* (3자리·중복없음·1-9) — 도메인 안 |

```java
public class Guess {
    private final List<Integer> numbers;

    private Guess(List<Integer> numbers) { this.numbers = numbers; }

    public static Guess from(String input) {
        List<Integer> nums = parse(input);
        if (nums.size() != 3) throw new IllegalArgumentException("3자리여야 합니다");
        if (new HashSet<>(nums).size() != 3) throw new IllegalArgumentException("중복 안 됨");
        for (int n : nums)
            if (n < 1 || n > 9) throw new IllegalArgumentException("1-9 범위");
        return new Guess(nums);
    }
}
```

컨트롤러의 `@Pattern(regexp = "\\d{3}")`은 *3자 숫자*만 보장한다 (예: `999`도 통과). *중복 없음*과 *1-9 범위 (0 제외)*는 도메인이 본다.

## baseball MVC 마이그레이션 함정

### 함정 1 — Bean Validation으로 도메인 규칙까지 우겨넣기

```java
@Pattern(regexp = "[1-9]{3}",
         message = "1-9 사이의 서로 다른 3자리...")  // 중복은 정규식으로 안 됨
```

정규식으로는 *서로 다른* 3개를 표현하기 어렵다. 억지로 표현하면 정규식이 *읽을 수 없게* 된다. 도메인 검증으로 미루는 게 깔끔.

### 함정 2 — 컨트롤러에서 IllegalArgumentException을 그대로 응답

```java
@PostMapping
public ... guess(@RequestBody GuessRequest req) {
    Guess g = Guess.from(req.numbers());  // 도메인 예외가 500 응답으로
    ...
}
```

도메인 예외 (`IllegalArgumentException`)는 *400 Bad Request*로 변환해야 한다. `@ControllerAdvice` + `@ExceptionHandler`로 일관되게 처리:

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handle(IllegalArgumentException e) {
        return ResponseEntity.badRequest().body(new ErrorResponse(e.getMessage()));
    }
}
```

### 함정 3 — Controller가 도메인을 직접 다룸

```java
@PostMapping
public GuessResponse guess(@RequestBody GuessRequest req) {
    List<Integer> answer = sessionStore.get(...);     // ❌ 컨트롤러에 게임 상태
    int strike = ...;                                  // ❌ 컨트롤러에서 판정
}
```

판정 로직은 *Service + 도메인*에 있어야 한다. Controller는 *바인딩 → 위임 → 응답 변환*만.

### 함정 4 — `@Valid`를 빠뜨려서 검증이 실행되지 않음

```java
public GuessResponse guess(@RequestBody GuessRequest req) { ... }   // ❌ @Valid 없음
public GuessResponse guess(@Valid @RequestBody GuessRequest req) {} // OK
```

`@Valid`가 없으면 Bean Validation 어노테이션이 *동작하지 않는다*. 흔한 실수.

## 자가 점검

- [ ] `@RequestBody` + `@Valid`가 *함께* 붙어 있는가?
- [ ] DTO에는 *형식 검증*만 있고, *도메인 불변식*은 도메인이 책임지는가?
- [ ] `IllegalArgumentException` → 400 변환이 `@ControllerAdvice`에 있는가?
- [ ] Controller가 *판정 로직*을 직접 들고 있지 않은가?
- [ ] 게임 상태가 *세션/메모리*가 아닌 *Service/Repository*에 저장되는가?

## 다음 문서

- 더 큰 그림: [Spring MVC Controller Basics](./spring-mvc-controller-basics.md)
- @ModelAttribute vs @RequestBody 분기: [관련 Primer](./spring-modelattribute-vs-requestbody-binding-primer.md)
- BindingResult와 400 응답 모양: [BindingResult Local Validation 400 Primer](./spring-bindingresult-local-validation-400-primer.md)
