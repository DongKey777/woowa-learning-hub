# API Key, HMAC Signed Request, Replay Protection

> 한 줄 요약: API key는 "누가 요청하는지"를 식별하는 값이고, HMAC 서명은 "요청이 중간에 바뀌지 않았고 비밀키를 가진 주체가 보냈다"를 증명한다. replay protection이 없으면 둘 다 쉽게 재사용된다.

**난이도: 🔴 Advanced**

> related-docs:
> - [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - [Secret Rotation / Leak Patterns](./secret-management-rotation-leak-patterns.md)
> - [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)

retrieval-anchor-keywords: api key, HMAC, signed request, request signing, replay protection, nonce, timestamp, canonical string, constant-time compare, body hash, idempotency key, nonce store outage

---

## 핵심 개념

API key와 HMAC signed request는 비슷해 보이지만 역할이 다르다.

- `API key`: 보통 고객, 앱, 서버를 식별하는 공개 식별자다
- `API secret`: HMAC 서명에 쓰는 비밀값이다
- `HMAC signed request`: 요청 본문과 메타데이터를 비밀키로 서명해 위변조를 막는다
- `nonce`: 한 번만 써야 하는 난수다
- `timestamp`: 요청이 언제 생성됐는지 나타낸다
- `replay protection`: 같은 요청을 다시 보내도 거부하는 방어다

가장 흔한 오해는 이거다.

- API key만 있으면 인증이 끝난다
- HMAC만 있으면 replay가 자동으로 막힌다
- timestamp만 있으면 재전송을 막을 수 있다

셋 다 틀리다.

- API key는 식별자일 뿐이며, 탈취되면 bearer credential처럼 재사용될 수 있다
- HMAC은 "무결성 + 비밀키 보유"를 증명하지만, 요청을 그대로 다시 보내는 replay는 막지 못한다
- timestamp는 유효 시간 창을 좁힐 뿐이고, 그 창 안에서는 같은 요청이 반복될 수 있다

실무에서 안전한 패턴은 보통 이 조합이다.

- `api_key`: 공개 식별자
- `secret`: HMAC 서명용 비밀키
- `timestamp`: 허용 시간 창 검증
- `nonce`: 재사용 여부 검증
- `signature`: canonical string의 HMAC-SHA256 결과
- `body hash`: 본문 위변조 검증

즉, 이 주제의 핵심은 "인증"보다 더 좁은 문제인 "요청 무결성과 재전송 방지"를 어떻게 보장하느냐다.

---

## 깊이 들어가기

### 1. API key는 왜 혼자 쓰면 위험한가

API key는 구조적으로 bearer token과 비슷하게 취급되기 쉽다.

- 헤더에 넣기 쉽다
- 로그에 남기 쉽다
- 프론트엔드에 박아두기 쉽다
- 한 번 유출되면 누가 썼는지 구별이 어렵다

그래서 API key만으로 중요한 호출을 허용하면 다음 문제가 생긴다.

- key 탈취 후 무제한 호출
- 호출자별 세부 권한 제어 불가
- 요청 내용이 바뀌어도 서버가 알아차리기 어려움

API key는 보통 다음 용도에 적합하다.

- 간단한 식별
- rate limit 키
- 비공개 서버 간 호출의 최소 식별자

하지만 `진짜 이 요청이 내가 보낸 것이 맞는가`를 증명하려면 HMAC 같은 서명이 필요하다.

### 2. HMAC signed request는 무엇을 증명하나

HMAC는 shared secret으로 메시지 전체에 MAC를 붙이는 방식이다.

- 비밀키를 가진 쪽만 올바른 서명을 만들 수 있다
- 메시지가 중간에 바뀌면 서명이 달라진다
- 서버는 같은 secret으로 다시 계산해 비교한다

즉 HMAC는 다음을 보장한다.

- 요청이 변조되지 않았다
- 비밀키를 가진 주체가 보냈다

하지만 HMAC는 기본적으로 다음을 막지 못한다.

- 같은 요청을 그대로 복사해서 재전송하는 replay
- 시계가 허용하는 범위 안에서의 재사용

그래서 signed request는 보통 replay protection과 같이 써야 한다.

### 3. replay protection이 왜 별도로 필요한가

공격자가 유효한 요청 하나를 가로챘다고 해보자.

```text
POST /v1/payments
X-Api-Key: demo-key
X-Timestamp: 1710000000
X-Nonce: 0f4f...
X-Signature: abc123...

{"amount":10000,"currency":"KRW"}
```

서명이 맞으면 서버는 이 요청을 정상 요청으로 본다.  
그런데 공격자가 이 요청을 1분 뒤 그대로 다시 보내면 어떨까?

- signature는 그대로 유효할 수 있다
- timestamp가 아직 허용 창 안이면 통과할 수 있다
- nonce를 저장하지 않으면 같은 요청인지 모른다

그래서 replay protection은 보통 둘을 같이 쓴다.

- `timestamp`로 허용 창을 제한한다
- `nonce`를 서버에 저장해 재사용을 막는다

실무적으로는 Redis 같은 저장소에 nonce를 TTL과 함께 보관한다.

- 예: 5분 허용 창이면 nonce도 5분만 보관
- 같은 key + nonce 조합이 다시 오면 거부

### 4. canonical string이 제일 잘 깨진다

HMAC이 실패하는 이유는 알고리즘보다 canonicalization 실수가 더 많다.

서명 대상 문자열이 조금만 달라도 검증은 실패한다.

흔한 함정:

- HTTP method 대소문자 차이
- path의 trailing slash 차이
- query parameter 정렬 차이
- URL encoding 차이 (`%20` vs `+`)
- JSON key order 차이
- body whitespace 차이
- header 대소문자나 공백 차이
- host / port 포함 여부 차이

중요한 원칙은 하나다.

> 클라이언트와 서버가 "완전히 같은 바이트"를 같은 규칙으로 만든다는 보장이 있어야 한다.

그래서 canonical string은 보통 이런 식으로 설계한다.

```text
METHOD\n
PATH\n
SORTED_QUERY\n
CONTENT-TYPE\n
BODY_SHA256\n
TIMESTAMP\n
NONCE
```

이때 주의할 점:

- body 전체를 직접 붙이지 말고 body hash를 붙이는 편이 안전하다
- query는 key/value 정렬 규칙을 고정해야 한다
- newline 규칙은 `\n` 하나로 강제해야 한다
- 빈 값과 없는 값은 구분해야 한다

### 5. signature 검증은 constant-time으로 해야 한다

서명 비교는 문자열 비교처럼 보이지만, 타이밍 차이로 정보가 새는 경우를 막아야 한다.

- `==` 비교는 피한다
- constant-time compare를 쓴다
- HMAC-SHA256 결과는 base64 또는 hex로 인코딩해서 전달한다

### 6. API key와 HMAC의 역할 분리

권장 구조는 이렇다.

- API key: 어느 고객인지 식별
- secret: 그 고객이 서명할 때 쓰는 비밀
- signature: 요청 검증

이 구조의 장점:

- key와 secret을 분리할 수 있다
- key 단위 rate limit이 쉽다
- secret rotation이 가능하다
- 특정 key만 폐기하기 쉽다

---

## 실전 시나리오

### 시나리오 1: 결제 API가 replay 공격을 받음

상황:

- 클라이언트가 `POST /payments`를 보냄
- 공격자가 동일 요청을 캡처함
- 같은 payload와 signature를 재전송함

문제:

- HMAC만 있으면 원 요청인지 재전송인지 구분이 안 된다

해결:

- timestamp 허용 창을 3~5분으로 줄인다
- nonce를 Redis에 저장한다
- `api_key + nonce` 조합이 재사용되면 거부한다
- 결제 같은 요청은 idempotency key도 같이 둔다

### 시나리오 2: canonical string이 달라져서 정상 요청이 실패함

상황:

- 클라이언트는 `?b=2&a=1` 순서로 서명
- 서버는 파싱 후 `?a=1&b=2`로 재조립

문제:

- 같은 의미의 URL인데 서명 문자열이 달라진다

해결:

- query parameter 정렬 규칙을 명시한다
- path는 원문 기준으로 처리한다
- body는 raw bytes 기준 hash를 사용한다

### 시나리오 3: 프론트엔드에서 HMAC secret을 넣으려는 경우

상황:

- 브라우저에서 직접 외부 API를 호출하고 싶다
- secret을 JS에 넣어 서명하려 한다

문제:

- 브라우저에 secret을 넣는 순간 secret이 secret이 아니다

해결:

- HMAC signed request는 서버-서버 통신에 두는 것이 일반적이다
- 브라우저는 CORS/SameSite/OAuth2/JWT 같은 브라우저 보안 모델로 처리한다
- 관련 경계는 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)와 [JWT 깊이 파기](./jwt-deep-dive.md)를 같이 본다

### 시나리오 4: secret rotation이 늦어 유출 사고가 커짐

상황:

- secret이 유출됐는데 모든 client가 같은 secret을 오래 쓴다

문제:

- 하나의 secret이 전체 계정을 위험에 빠뜨린다

해결:

- key id를 두고 secret을 버전 관리한다
- old secret과 new secret을 짧게 중복 허용한다
- 폐기 시각을 명확히 둔다

---

## 코드로 보기

### 1. curl 요청 예시

```bash
API_KEY="demo-client"
API_SECRET="super-secret-value"
METHOD="POST"
PATH="/v1/payments"
BODY='{"amount":10000,"currency":"KRW"}'
TS="$(date +%s)"
NONCE="$(uuidgen | tr '[:upper:]' '[:lower:]')"
BODY_SHA256="$(printf '%s' "$BODY" | openssl dgst -sha256 -binary | openssl base64 -A)"

CANONICAL="$(printf '%s\n%s\n%s\n%s\n%s\n%s\n%s' \
  "$METHOD" \
  "$PATH" \
  "" \
  "application/json" \
  "$BODY_SHA256" \
  "$TS" \
  "$NONCE")"

SIGNATURE="$(printf '%s' "$CANONICAL" | openssl dgst -sha256 -hmac "$API_SECRET" -binary | openssl base64 -A)"

curl -X POST "https://api.example.com/v1/payments" \
  -H "X-Api-Key: $API_KEY" \
  -H "X-Timestamp: $TS" \
  -H "X-Nonce: $NONCE" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  --data "$BODY"
```

### 2. Java 서명 생성 예시

```java
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

public class HmacSigner {
    public static String sign(String secret, String canonicalString) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] raw = mac.doFinal(canonicalString.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(raw);
        } catch (Exception e) {
            throw new IllegalStateException("failed to sign request", e);
        }
    }

    public static boolean constantTimeEquals(String a, String b) {
        return MessageDigest.isEqual(
            a.getBytes(StandardCharsets.UTF_8),
            b.getBytes(StandardCharsets.UTF_8)
        );
    }
}
```

### 3. 서버 검증 예시

```java
public class RequestVerifier {
    private final String secret;
    private final ReplayStore replayStore;

    public void verify(RequestEnvelope req) {
        if (Math.abs(req.timestamp() - System.currentTimeMillis() / 1000) > 300) {
            throw new IllegalArgumentException("timestamp out of range");
        }

        if (replayStore.exists(req.apiKey(), req.nonce())) {
            throw new IllegalArgumentException("replayed request");
        }

        String expected = HmacSigner.sign(secret, req.canonicalString());
        if (!HmacSigner.constantTimeEquals(expected, req.signature())) {
            throw new IllegalArgumentException("bad signature");
        }

        replayStore.save(req.apiKey(), req.nonce(), 300);
    }
}
```

### 4. canonical string 생성 예시

```java
public String canonicalize(String method,
                           String path,
                           String query,
                           String contentType,
                           String bodySha256,
                           String timestamp,
                           String nonce) {
    return String.join("\n",
        method.toUpperCase(),
        path,
        query == null ? "" : query,
        contentType == null ? "" : contentType.toLowerCase(),
        bodySha256,
        timestamp,
        nonce
    );
}
```

핵심은 클라이언트와 서버가 이 규칙을 완전히 공유해야 한다는 점이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| API key만 사용 | 구현이 가장 쉽다 | 탈취되면 재사용이 쉽고, 위변조를 못 막는다 | 낮은 위험의 식별자, rate limit 키 |
| API key + HMAC | 무결성과 호출자 보장을 얻는다 | canonical string과 nonce 관리가 필요하다 | 서버-서버 API, 결제, 정산 |
| API key + HMAC + nonce/timestamp | replay 방어까지 가능하다 | 저장소와 clock skew 처리가 필요하다 | 돈, 권한, 상태 변경 요청 |
| mTLS | 채널 레벨 신원이 강하다 | 운영과 인증서 회전이 무겁다 | 내부 서비스 간 통신, zero-trust | 
| JWT bearer token | 권한 전달이 쉽다 | 탈취 시 재사용이 쉽다 | 사용자 인증, 서비스 간 claim 전달 |

판단 기준은 다음이다.

- 단순 식별이면 API key만으로 충분할 수 있다
- 요청 무결성과 위변조 방지가 필요하면 HMAC이 필요하다
- 같은 요청의 반복 실행이 위험하면 nonce와 timestamp를 반드시 추가해야 한다
- 브라우저가 직접 호출하는 흐름이면 HMAC secret을 노출하지 않는 방식으로 바꿔야 한다

이때 브라우저 경계는 [CORS, SameSite, Preflight](./cors-samesite-preflight.md)가, 서비스 간 신원은 [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)가 더 적합하다.

---

## 꼬리질문

> Q: API key만 있으면 왜 안 되나요?
> 의도: 식별자와 무결성 보증을 구분하는지 확인한다.
> 핵심: API key는 "누구인지"만 말하고, 요청이 바뀌지 않았는지는 보장하지 못한다.

> Q: HMAC이면 replay attack은 자동으로 막히나요?
> 의도: 서명과 재전송 방어의 차이를 아는지 본다.
> 핵심: HMAC은 재전송된 같은 바이트도 유효할 수 있으므로 nonce와 timestamp가 별도로 필요하다.

> Q: canonical string을 왜 굳이 표준화해야 하나요?
> 의도: 클라이언트/서버 간 결정론적 검증을 이해하는지 본다.
> 핵심: 사소한 정규화 차이만 있어도 서명이 달라져 정상 요청이 실패한다.

> Q: nonce만 있으면 replay 방지가 충분한가요?
> 의도: nonce 저장과 TTL, timestamp의 역할 분담을 보는 질문이다.
> 핵심: nonce는 저장과 만료가 있어야 의미가 있고, timestamp는 허용 창을 줄여 준다.

> Q: 브라우저에서 HMAC secret을 직접 써도 되나요?
> 의도: 프론트엔드 보안 경계를 이해하는지 확인한다.
> 핵심: 안 된다. 브라우저는 secret을 숨길 수 없어서, 이 패턴은 서버-서버용이 더 적합하다.

> Q: HMAC signed request와 JWT는 어떤 차이가 있나요?
> 의도: 서명된 요청과 서명된 클레임 집합의 차이를 아는지 본다.
> 핵심: HMAC은 개별 요청 무결성, JWT는 주로 claim 전달과 인증/인가 상태 전달에 강하다.

## 한 줄 정리

API key는 식별자, HMAC은 요청 무결성 증명, nonce/timestamp는 replay 방지 장치다. 셋을 같이 써야 "누가 보냈고, 무엇이 바뀌지 않았고, 같은 요청이 다시 오지 않았는가"를 실무적으로 지킬 수 있다.
