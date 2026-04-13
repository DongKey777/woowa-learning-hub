# DPoP / Token Binding Basics

> 한 줄 요약: DPoP는 bearer token을 proof-of-possession token에 가깝게 만들어 토큰 재사용을 줄이지만, key 관리와 replay 방지를 같이 설계해야 의미가 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md)
> - [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
> - [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)

retrieval-anchor-keywords: DPoP, token binding, proof-of-possession, JWK thumbprint, cnf claim, htm, htu, replay protection, bearer token, sender-constrained token

---

## 핵심 개념

DPoP(Demonstration of Proof-of-Possession)는 access token을 단순 bearer로만 쓰지 않게 만드는 방식이다.  
클라이언트가 자신의 private key로 요청마다 proof를 만들고, 서버는 그 proof와 token이 같은 key에 묶였는지 본다.

핵심 효과:

- 토큰이 탈취돼도 key가 없으면 재사용하기 어렵다
- 요청마다 method와 URL에 대한 proof를 넣을 수 있다
- bearer token보다 재사용 면이 줄어든다

즉 DPoP는 "토큰만 있으면 된다"를 "토큰과 key 둘 다 있어야 한다"로 바꾸는 것이다.

---

## 깊이 들어가기

### 1. DPoP가 풀려는 문제

bearer token은 복사되는 순간 누구나 쓸 수 있다.

- 로그에서 새어 나간다
- 브라우저 storage에서 탈취된다
- proxy나 debug output에서 노출된다

DPoP는 토큰을 특정 키에 묶어서 이런 재사용을 줄인다.

### 2. proof에는 무엇이 들어가나

보통 proof는 다음을 포함한다.

- HTTP method
- request URI
- timestamp
- unique jti
- client private key로 생성한 서명

서버는 proof를 보고 토큰이 같은 key에 바인딩됐는지 확인한다.

### 3. cnf claim과 thumbprint

토큰에는 종종 confirmation claim이 들어간다.

- 어떤 key에 묶였는지 나타낸다
- JWK thumbprint로 key를 식별할 수 있다
- token과 proof의 키가 일치해야 한다

### 4. replay 방지가 별도다

DPoP proof도 재사용될 수 있다.

- 동일 proof 재전송
- 허용 창 내 재사용
- 중간 탈취 후 지연 replay

그래서 proof의 `jti` 캐시, timestamp window, `htu/htm` 검증이 필요하다.

### 5. DPoP가 만능은 아니다

DPoP는 유용하지만 다음 문제는 못 푼다.

- client private key 저장이 안전하지 않으면 끝난다
- 브라우저 XSS가 key를 직접 못 훔쳐도 proof를 대행할 수 있다
- 모든 API가 proof를 이해해야 한다

즉 DPoP는 bearer token보다 강하지만, 여전히 운영과 클라이언트 보안이 중요하다.

---

## 실전 시나리오

### 시나리오 1: access token이 로그에서 새어 나감

대응:

- DPoP proof와 key binding을 사용한다
- token replay를 줄인다
- key storage를 OS-backed storage로 옮긴다

### 시나리오 2: proof replay 공격이 발생함

대응:

- `jti`를 저장한다
- timestamp window를 좁힌다
- 동일 proof 재사용을 거부한다

### 시나리오 3: 브라우저 앱이 DPoP key를 안전하게 못 저장함

대응:

- memory-only key 또는 platform-backed key를 검토한다
- 공격면과 UX를 비교한다
- 대체로 BFF 구조와 함께 판단한다

---

## 코드로 보기

### 1. proof 생성 개념

```javascript
const proof = sign({
  htm: "GET",
  htu: "https://api.example.com/v1/orders",
  jti: crypto.randomUUID(),
  iat: Math.floor(Date.now() / 1000)
}, privateKey);
```

### 2. 서버 검증 개념

```java
public void verifyDpop(String accessToken, DpopProof proof, HttpRequest request) {
    verifyHtmHtu(proof, request);
    verifyJtiReplay(proof.jti());
    verifyTokenBinding(accessToken, proof.publicKey());
}
```

### 3. replay store 개념

```text
1. proof jti를 저장한다
2. timestamp 허용 창을 둔다
3. 같은 jti가 다시 오면 거부한다
4. token binding이 맞는지 확인한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| bearer token | 단순하다 | 재사용이 쉽다 | 낮은 위험 API |
| DPoP | token replay를 줄인다 | key와 proof 관리가 필요하다 | 보안 우선 API |
| mTLS sender-constrained | 매우 강하다 | 브라우저에 부적합하다 | service-to-service |
| BFF + cookie | 브라우저 UX가 좋다 | CSRF 경계가 필요하다 | SPA/BFF |

판단 기준은 이렇다.

- token 탈취 후 재사용이 큰 문제인가
- client가 private key를 안전하게 보관할 수 있는가
- API가 proof 검증을 감당할 수 있는가
- DPoP 실패 시 fallback이 필요한가

---

## 꼬리질문

> Q: DPoP는 무엇을 해결하나요?
> 의도: bearer token 재사용 문제를 아는지 확인
> 핵심: token만으로는 못 쓰게 하고 proof of possession을 요구한다.

> Q: proof replay를 어떻게 막나요?
> 의도: jti와 timestamp 검증을 아는지 확인
> 핵심: jti 저장과 짧은 허용 창이 필요하다.

> Q: DPoP가 bearer token보다 강한 이유는 무엇인가요?
> 의도: token binding 의미를 아는지 확인
> 핵심: 토큰이 특정 key에 묶여 있기 때문이다.

> Q: DPoP가 만능은 아닌 이유는 무엇인가요?
> 의도: 운영과 클라이언트 보안의 한계를 아는지 확인
> 핵심: key 관리와 브라우저 공격면이 여전히 남는다.

## 한 줄 정리

DPoP는 bearer token을 proof-of-possession으로 좁히는 장치지만, replay 저장소와 key 보관 전략이 같이 있어야 한다.
