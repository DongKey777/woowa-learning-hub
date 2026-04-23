# CORS 기초

> 한 줄 요약: CORS는 브라우저가 "다른 출처의 리소스를 요청해도 되는가"를 서버에게 물어보는 메커니즘이고, 서버가 허용 응답 헤더를 내려줘야 브라우저가 응답을 자바스크립트에 넘긴다.

**난이도: 🟢 Beginner**

관련 문서:

- [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md)
- [API 보안 헤더 기초](./api-security-headers-beyond-csp.md)
- [security 카테고리 인덱스](./README.md)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)

retrieval-anchor-keywords: cors 기초, cors가 뭐예요, cross origin 오류, cors 에러 브라우저, preflight란 무엇인가, access-control-allow-origin, same origin policy beginner, cors allow headers, cors 해결 방법, beginner cors

## 핵심 개념

CORS(Cross-Origin Resource Sharing)는 브라우저의 동일 출처 정책(Same-Origin Policy)이 가로막는 요청을 서버 측에서 명시적으로 허용하는 메커니즘이다. "출처(origin)"는 `프로토콜 + 도메인 + 포트` 세 가지가 모두 같아야 동일 출처로 본다. 입문자가 헷갈리는 이유는 CORS 에러가 브라우저 콘솔에만 보이고 서버 로그엔 아무 이상이 없어서, "서버가 잘 응답했는데 왜 실패하냐"는 혼란이 생기기 때문이다.

## 한눈에 보기

출처(origin)는 `프로토콜 + 도메인 + 포트`가 모두 같아야 동일 출처다. 하나라도 다르면 브라우저가 CORS 체크를 시작한다.

```
[출처 비교 예시]
https://app.example.com  (프론트엔드)
https://api.example.com  (백엔드 API)
→ 도메인이 달라서 "다른 출처" → 브라우저가 CORS 체크

[서버가 내려줘야 하는 헤더]
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Content-Type, Authorization
```

허용 헤더가 없으면 브라우저가 응답을 자바스크립트에 넘기지 않고 콘솔에 "CORS policy" 에러를 표시한다. 서버 응답은 도착했어도 JS에서는 읽을 수 없다.

## 상세 분해

- **Same-Origin Policy**: 브라우저는 기본적으로 다른 출처의 응답 내용을 자바스크립트가 읽지 못하게 막는다. 이것이 CORS 체크의 출발점이다.
- **Preflight 요청**: `PUT`, `DELETE`, `Content-Type: application/json` 등 "단순하지 않은" 요청은 실제 요청 전에 브라우저가 `OPTIONS` 메서드로 먼저 서버에게 허용 여부를 물어본다.
- **허용 응답 헤더**: 서버가 `Access-Control-Allow-Origin` 헤더를 응답에 포함해야 브라우저가 JS에게 응답을 전달한다. 누락하면 브라우저가 응답을 차단한다.
- **`*` 와일드카드의 한계**: `Access-Control-Allow-Origin: *`는 쿠키나 Authorization 헤더가 포함된 자격증명(credentials) 요청에는 사용할 수 없다. 쿠키가 필요하면 정확한 출처를 명시해야 한다.

## 흔한 오해와 함정

- **"CORS는 보안 취약점이다"** → CORS는 취약점이 아니라 보안 기능이다. 브라우저가 동일 출처 정책으로 막는 것을 서버가 선택적으로 열어주는 메커니즘이다.
- **"서버에서 안 된다고 하는데, Postman에서는 된다"** → CORS 체크는 브라우저만 한다. Postman, curl, 서버 간 통신은 CORS 제한을 받지 않는다.
- **"프론트엔드에서 헤더를 추가하면 해결된다"** → CORS 허용 헤더는 반드시 서버 응답에 있어야 한다. 프론트엔드 요청 헤더를 아무리 바꿔도 서버가 응답하지 않으면 소용없다.

## 실무에서 쓰는 모습

Spring Boot에서는 `@CrossOrigin` 어노테이션이나 `WebMvcConfigurer`의 `addCorsMappings()`로 허용 출처를 등록한다. 로컬 개발 시에는 프론트엔드 개발 서버 주소(예: `http://localhost:3000`)를 명시적으로 허용하고, 운영 환경에서는 실제 배포 도메인만 허용 목록에 넣는다. `allowedOrigins("*")`와 `allowCredentials(true)`를 동시에 쓰면 Spring이 에러를 내는데, 이것은 올바른 제약이다.

## 더 깊이 가려면

- [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md) — Preflight 캐싱, SameSite 쿠키와의 관계, allowlist 설계
- [API 보안 헤더 기초](./api-security-headers-beyond-csp.md) — CORS 외에 응답 헤더로 설정하는 다른 보안 정책들

## 면접/시니어 질문 미리보기

- **"CORS 에러를 서버에서만 해결할 수 있는 이유가 뭔가요?"** → 브라우저가 서버 응답의 `Access-Control-Allow-Origin` 헤더를 보고 허용 여부를 결정하기 때문에, 클라이언트(브라우저)가 아닌 서버가 허용 선언을 해야 한다.
- **"`allowedOrigins(*)`와 `allowCredentials(true)`를 동시에 쓰면 왜 안 되나요?"** → 자격증명 요청에 와일드카드 출처를 허용하면 어떤 사이트에서도 쿠키를 포함한 요청이 가능해져 보안 의미가 사라지기 때문이다.

## 한 줄 정리

CORS는 브라우저가 다른 출처 요청을 막는 동일 출처 정책을, 서버가 `Access-Control-Allow-Origin` 헤더로 선택적으로 여는 메커니즘이다.
