# API 키 vs OAuth vs Client Credentials 한 장 비교

> 한 줄 요약: API 키는 "우리 앱 자체"를 식별할 때, 사용자 위임 OAuth는 "특정 사용자를 대신해" 외부 자원에 접근할 때, Client Credentials는 "사용자 없이 우리 서버 자체가 OAuth 토큰을 받아" 서버-서버 호출할 때 주로 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [API 키 기초](./api-key-basics.md)
- [OAuth2 기초](./oauth2-basics.md)
- [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
- [Workload Identity vs Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)

retrieval-anchor-keywords: api key vs oauth, api key vs client credentials, oauth client credentials beginner, user delegated oauth, server to server oauth, oauth 사용자 위임, client credentials가 뭐예요, 서버 서버 oauth 차이, 언제 api key 쓰나, 언제 client credentials 쓰나, oauth 비교표, access token vs api key, 외부 api 붙이려는데 뭐 써야 하나, 사용자 데이터 호출이 왜 안 맞지

## 핵심 개념

초보자는 용어보다 "지금 누구를 대표해서 요청하나"를 먼저 보면 덜 헷갈린다.

- API 키: 우리 앱이나 서버 자체를 식별한다.
- 사용자 위임 OAuth: 로그인한 사용자가 "내 캘린더를 읽어도 된다"처럼 자기 권한을 앱에 잠깐 맡긴다.
- Client Credentials: 사용자 없이 우리 서버가 자기 자격증명으로 OAuth access token을 받아 서버-서버로 호출한다.

짧게 비유하면 이렇다.

- API 키는 서비스용 출입증
- 사용자 위임 OAuth는 사용자가 써 준 위임장
- Client Credentials는 서버 법인카드로 발급받는 업무용 토큰

## 한눈에 보기

| 방식 | 누구를 대표하나 | 사용자 동의 화면 | 보통 받는 값 | 대표 예시 | 이걸로 풀기 어려운 문제 |
|---|---|---|---|---|---|
| API 키 | 우리 앱/서버 | 없음 | 고정 키 | 결제 SaaS, 번역 API, 내부 배치 호출 | 사용자별 외부 데이터 접근 |
| 사용자 위임 OAuth | 특정 사용자 | 있음 | access token, refresh token | 사용자의 구글 드라이브/캘린더 읽기 | 사용자 없이 백그라운드 작업만 처리 |
| Client Credentials | 우리 서버 애플리케이션 | 없음 | access token | 서버가 파트너 API를 OAuth로 호출 | "이 사용자가 허락했다"를 증명 |

30초 판단표로 다시 보면 더 간단하다.

| 지금 질문 | 먼저 고를 후보 |
|---|---|
| 사용자의 구글/깃허브/슬랙 데이터에 접근하나 | 사용자 위임 OAuth |
| 우리 서버가 밤마다 파트너 API를 호출하나 | API 키 또는 Client Credentials |
| 공급자가 "OAuth token으로 호출"을 요구하나 | Client Credentials부터 확인 |
| 공급자가 단순히 secret key 한 개를 주나 | API 키부터 확인 |

## 상세 분해

### 1. API 키는 "우리 앱 신분"에 가깝다

API 키는 보통 공급자가 발급한 긴 문자열 하나를 서버가 보관하고 요청마다 함께 보낸다. 사용자 동의 화면은 없고, 보통 "이 요청이 우리 고객 앱에서 왔는가"를 식별하는 데 쓴다.

예시:

- 우리 백엔드가 이미지 리사이즈 SaaS를 호출한다.
- 야간 배치가 외부 정산 API를 호출한다.

핵심은 키를 브라우저가 아니라 서버 시크릿으로 숨겨야 한다는 점이다.

### 2. 사용자 위임 OAuth는 "이 사용자가 허락했는가"를 다룬다

사용자 위임 OAuth는 사용자 로그인과 동의 화면이 앞에 있다. 그래서 토큰에는 "우리 앱"뿐 아니라 "어떤 사용자 범위의 권한을 위임받았는가"가 함께 들어간다.

예시:

- 사용자의 구글 캘린더 일정을 읽는다.
- 사용자의 드라이브 파일 목록을 보여 준다.

이 장면에서 API 키만 쓰면 "어느 사용자 것인가"와 "그 사용자가 허락했는가"를 표현하기 어렵다.

### 3. Client Credentials는 "사용자 없는 OAuth"다

Client Credentials도 OAuth지만, 앞에 사용자가 없다. 우리 서버가 `client_id`와 `client_secret` 같은 자기 자격으로 token endpoint에 가서 access token을 받아 온다.

예시:

- 우리 서버가 파트너의 관리 API를 서버-서버로 호출한다.
- 사내 마이크로서비스가 중앙 authorization server에서 service token을 받아 내부 API를 호출한다.

즉 "OAuth를 쓴다"와 "사용자 위임이다"는 같은 뜻이 아니다.

### 4. 같은 서버-서버여도 API 키와 Client Credentials가 갈리는 이유

둘 다 사용자 없이 서버-서버 호출에 쓰일 수 있지만 모양이 다르다.

| 비교 포인트 | API 키 | Client Credentials |
|---|---|---|
| 공급자 계약 | 미리 발급한 고정 키를 보낸다 | 토큰 endpoint에서 access token을 발급받는다 |
| 수명 | 길게 유지되는 경우가 많다 | 보통 짧은 수명 token |
| 회전 방식 | 키 재발급/교체가 중심 | token 만료 후 재발급이 기본 |
| 보통 보이는 값 | `x-api-key`, `Authorization: Bearer sk-...` | `Bearer eyJ...` 같은 OAuth access token |

초보자 관점에서는 "공급자가 정적 secret 하나를 주는가, 아니면 OAuth token을 발급해 주는가"를 먼저 보면 된다.

## 흔한 오해와 함정

- `OAuth를 쓰면 무조건 사용자 로그인이다`는 오해다. Client Credentials는 OAuth지만 사용자 위임이 아니다.
- `Client Credentials token이 있으면 사용자 행동도 대신할 수 있다`는 오해다. 이 토큰은 보통 앱/서비스 자체 권한이지 특정 사용자 동의가 아니다.
- `API 키가 더 단순하니 항상 더 좋은 선택이다`는 오해다. 사용자별 동의, 세밀한 scope, 짧은 수명 토큰이 필요하면 OAuth가 더 맞다.
- `Bearer`로 보내면 전부 OAuth token이다`도 오해다. 공급자에 따라 API 키도 `Authorization: Bearer ...` 헤더에 넣는다.

초보자가 가장 먼저 던질 질문은 아래 하나면 충분하다.

- "이 요청이 특정 사용자의 외부 자원을 대신 다루는가?"

`Yes`면 사용자 위임 OAuth를 먼저 본다. `No`면 API 키와 Client Credentials 중 공급자 계약을 보면 된다.

## 실무에서 쓰는 모습

같은 "외부 API 호출"도 상황에 따라 선택이 달라진다.

| 실제 장면 | 맞는 선택 | 이유 |
|---|---|---|
| 우리 서비스가 사용자의 구글 캘린더를 읽는다 | 사용자 위임 OAuth | 사용자의 동의와 사용자별 자원 범위가 핵심이다 |
| 우리 서버가 결제 대행사의 정산 API를 밤마다 호출한다 | API 키 가능 | 사용자 동의보다 서버 시크릿 보관이 핵심이다 |
| 파트너가 "token endpoint에서 access token 받아 호출하라"고 문서화했다 | Client Credentials | 서버-서버지만 OAuth 계약을 따르는 장면이다 |

처음 읽을 때는 이렇게 외우면 된다.

1. 사용자 데이터면 사용자 위임 OAuth
2. 사용자 없고 고정 secret이면 API 키
3. 사용자 없고 OAuth token 발급형이면 Client Credentials

## 더 깊이 가려면

- API 키를 브라우저에 넣어도 되는지, 서버 프록시가 필요한지가 먼저 막히면 [API 키 기초](./api-key-basics.md), [브라우저 직접 호출 vs 서버 프록시 결정 트리](./browser-direct-call-vs-server-proxy-decision-tree.md)를 본다.
- OAuth 기본 용어와 Authorization Code Grant 흐름을 다시 잡고 싶으면 [OAuth2 기초](./oauth2-basics.md), [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)로 이어 간다.
- `scope`, `audience`, 내부 permission이 다시 한 문장처럼 섞이면 [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)으로 내려간다.
- 장기 API 키 대신 workload identity 같은 더 나은 서버 자격증명을 보고 싶으면 [Workload Identity vs Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)를 본다.

## 한 줄 정리

`누구를 대표하나`만 먼저 보면 된다: 사용자면 사용자 위임 OAuth, 사용자 없고 정적 secret이면 API 키, 사용자 없고 OAuth token 발급형이면 Client Credentials다.
