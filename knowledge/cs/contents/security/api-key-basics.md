# API 키 기초

> 한 줄 요약: API 키는 "누가 이 요청을 보냈는가"를 식별하는 토큰이고, 노출되면 즉시 재발급이 필요하므로 코드에 하드코딩하지 않고 환경 변수나 시크릿 관리 도구에 보관해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [시크릿 관리·로테이션·누출 패턴](./secret-management-rotation-leak-patterns.md)
- [API 보안 헤더 기초](./api-security-headers-beyond-csp.md)
- [security 카테고리 인덱스](./README.md)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)

retrieval-anchor-keywords: api key 기초, api 키가 뭐예요, api key 노출 위험, 환경변수에 api key 보관, api key vs oauth, 시크릿 하드코딩 안 되는 이유, beginner api key, api key rotation, api key 깃헙 노출, api 인증 기초

## 핵심 개념

API 키는 서버에 요청할 때 "나는 이 키를 발급받은 클라이언트다"를 증명하는 문자열이다. 사용자 인증(로그인)과 달리, API 키는 주로 서버-투-서버나 클라이언트 애플리케이션이 외부 서비스를 호출할 때 쓴다. 입문자가 가장 많이 저지르는 실수는 API 키를 소스 코드에 직접 작성(하드코딩)하고 GitHub에 push해서 키가 노출되는 상황이다.

## 한눈에 보기

API 키는 헤더로 전달하는 것이 가장 안전하다. 쿼리 파라미터는 URL 로그에 노출될 수 있어 비권장이다.

```
[API 키 전달 방법]
헤더:   Authorization: Bearer sk-xxx  (가장 일반적)
        X-API-Key: sk-xxx
쿼리:   https://api.example.com/data?api_key=sk-xxx  (URL에 노출되어 비권장)
```

API 키는 코드에 직접 쓰지 않고 환경 변수로 분리한다.

- 나쁜 예: `String apiKey = "sk-abc123";` — 코드에 하드코딩
- 좋은 예: `String apiKey = System.getenv("EXTERNAL_API_KEY");` — 환경 변수로 주입

`.env` 파일이나 `application.properties`에 실제 값이 포함된 채로 commit하면 GitHub에 키가 공개된다. 노출 즉시 무효화 후 재발급이 필요하다.

## 상세 분해

- **API 키의 역할**: 인증(Authentication) 목적으로 쓴다. "이 키를 가진 주체가 허가된 클라이언트"임을 확인한다. 세션이나 JWT처럼 사용자 개인을 식별하는 것이 아니라, 애플리케이션 또는 서비스 단위로 식별한다.
- **환경 변수 보관**: `application.properties`에 실제 값을 쓰지 말고 `${ENV_VAR_NAME}` 형식으로 참조한다. CI/CD 파이프라인에서는 시크릿 변수로 주입한다.
- **키 로테이션(재발급)**: API 키가 노출됐거나 의심되는 상황에서는 즉시 새 키를 발급하고 기존 키를 무효화한다. 주기적으로 교체하는 것도 좋은 습관이다.
- **권한 최소화(Least Privilege)**: 외부 서비스에서 API 키를 발급할 때 필요한 권한만 선택한다. 읽기만 필요하면 읽기 전용 키를 발급한다. 전체 권한 키는 최후 수단이다.

## 흔한 오해와 함정

- **"내 저장소는 private이라 괜찮다"** → private 저장소도 팀원에게 공유되고, 나중에 실수로 public이 될 수 있다. 코드와 시크릿은 분리하는 것이 원칙이다.
- **"쿼리 파라미터로 API 키를 보내도 HTTPS니까 안전하다"** → HTTPS로 전송 구간은 암호화되지만, URL은 서버 로그, 브라우저 히스토리, 프록시 로그에 남는다. 헤더로 전달하는 것이 더 안전하다.
- **"API 키와 OAuth 토큰은 같은 것이다"** → API 키는 정적인 문자열이고 유효 기간이 따로 없는 경우가 많다. OAuth 토큰은 짧은 유효 기간을 가지고 재발급(refresh) 메커니즘이 있다. 사용자 인증이 필요하면 OAuth를 쓰는 것이 일반적이다.

## 실무에서 쓰는 모습

Spring Boot 프로젝트에서 외부 API를 호출할 때 `application.yml`에 `external.api.key: ${EXTERNAL_API_KEY}`로 작성하고, `@Value("${external.api.key}")` 또는 `@ConfigurationProperties`로 주입한다. 로컬 개발용 `.env` 파일은 `.gitignore`에 반드시 포함시킨다. 사내 시스템이라면 AWS Secrets Manager나 Vault 같은 시크릿 관리 도구를 사용한다.

## 더 깊이 가려면

- [시크릿 관리·로테이션·누출 패턴](./secret-management-rotation-leak-patterns.md) — 키 로테이션 전략, 누출 감지, 대응 절차 심화
- [API 보안 헤더 기초](./api-security-headers-beyond-csp.md) — API 키 전달 이외의 API 보안 헤더 패턴

## 면접/시니어 질문 미리보기

- **"API 키가 GitHub에 노출됐을 때 제일 먼저 해야 할 일이 뭔가요?"** → 해당 키를 즉시 무효화(revoke)하고 새 키를 발급한다. 로그를 확인해 노출 이후 비정상적인 호출이 있었는지 확인한다.
- **"API 키 대신 OAuth를 쓰는 상황은 언제인가요?"** → 사용자 개인의 자원에 접근하거나 위임 권한이 필요한 경우, 또는 만료·갱신 메커니즘이 필요한 경우에는 OAuth를 선택한다.

## 한 줄 정리

API 키는 코드에 하드코딩하지 않고 환경 변수나 시크릿 관리 도구에 보관하며, 노출 즉시 무효화하는 것이 API 키 보안의 핵심이다.
