# Secret Management, Rotation, Leak Patterns

> 한 줄 요약: 시크릿 관리는 "안 보이게 저장"이 끝이 아니라, 유출 경로를 줄이고, 회전하고, 회수할 수 있어야 운영된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTPS / HSTS / MITM](./https-hsts-mitm.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [System Design 면접 프레임워크](../system-design/system-design-framework.md)

---

## 핵심 개념

시크릿(secret)은 다음을 모두 포함한다.

- API key
- DB password
- OAuth client secret
- signing key
- private key
- webhook secret

문제는 시크릿이 "한 번만 잘 숨기면 되는 값"이 아니라는 점이다.

- 배포 전에 유출될 수 있다
- 로그에 찍힐 수 있다
- 빌드 산출물에 섞일 수 있다
- 운영 중 회전이 필요하다
- 사고 후 폐기해야 한다

---

## 깊이 들어가기

### 1. 가장 흔한 유출 경로

유출 패턴은 생각보다 단순하다.

- `.env` 파일이 저장소에 커밋됨
- CI 로그에 secret 값이 출력됨
- `application.yml`이 아티팩트에 포함됨
- debug log에 authorization header가 남음
- exception stack trace에 connection string이 드러남
- shell history에 `export SECRET=...`가 남음

### 2. 저장 위치보다 더 중요한 것은 권한 경계다

시크릿은 어디에 저장하느냐보다 누가 읽을 수 있느냐가 중요하다.

- 개발자 로컬
- CI/CD secret store
- 런타임 환경 변수
- KMS/Vault
- Kubernetes Secret

각 방식은 장단점이 있다.

| 방식 | 장점 | 단점 |
|---|---|---|
| env var | 단순하다 | 프로세스 덤프/로그/스크립트 노출 위험 |
| file secret | 앱이 읽기 쉽다 | 파일 권한과 배포 관리가 필요 |
| secret manager | 회전과 접근 제어가 좋다 | 런타임 의존성이 생긴다 |
| KMS envelope | 키 계층을 분리한다 | 설계가 복잡하다 |

### 3. rotation은 "교체"가 아니라 "전환"이다

시크릿을 바꿀 때 가장 중요한 건 무중단 전환이다.

흐름 예시:

1. 새 secret 생성
2. 애플리케이션이 둘 다 읽을 수 있게 준비
3. 새 secret으로 쓰기 전환
4. old secret 폐기
5. 실패 없는지 모니터링

특히 JWT signing key, DB password, OAuth client secret은 회전 전략이 다르다.

### 4. leak detection은 사후 대응이 아니라 상시 통제다

다음 장치를 함께 둔다.

- secret scanning
- commit hook
- CI regex guard
- log masking
- audit trail
- least privilege

### 5. "일단 환경변수로 넣자"의 함정

환경변수는 편하지만, 다음 문제를 숨긴다.

- `ps`/proc에서 노출 가능
- container inspect에서 보일 수 있음
- debug dump와 crash report에 섞일 수 있음
- rotation이 느려진다

---

## 실전 시나리오

### 시나리오 1: git history에 secret이 들어감

원인:

- 한 번 커밋된 secret을 지웠다고 끝난다고 생각함

해결:

- secret 회전
- git history rewrite 여부 판단
- downstream token invalidation
- audit 로그 점검

### 시나리오 2: 로그 마스킹을 안 해서 토큰이 남음

원인:

- access token, cookie, db url이 debug log에 그대로 출력

해결:

- log pattern masking
- authorization header redaction
- exception message 최소화

### 시나리오 3: DB password를 바꿨는데 서비스가 죽음

원인:

- rotation과 deployment가 분리되지 않음

해결:

- dual credential phase
- connection pool 재시작 전략
- canary rollout

### 시나리오 4: secret manager를 붙였더니 장애가 난다

원인:

- 런타임마다 secret manager를 동기 호출함

해결:

- 캐시와 TTL
- startup fetch + refresh
- fallback 전략

---

## 코드로 보기

### Spring 설정에서 시크릿 주입

```java
@ConfigurationProperties(prefix = "app.datasource")
public record DataSourceSecret(String username, String password) {}
```

```yaml
app:
  datasource:
    username: ${DB_USER}
    password: ${DB_PASSWORD}
```

### 로그 마스킹 예시

```java
public String maskSecret(String value) {
    if (value == null || value.length() < 8) {
        return value;
    }
    return value.substring(0, 2) + "****" + value.substring(value.length() - 2);
}
```

### 회전 체크리스트 의사코드

```text
new_secret = create()
deploy(app_reads_both)
switch_write_to(new_secret)
verify_traffic()
revoke(old_secret)
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| env var | 쉽다 | 노출 경로가 많다 | 소규모/단기 |
| secret manager | 회전과 감사가 좋다 | 런타임 의존성이 늘어난다 | 대부분의 실서비스 |
| KMS + envelope | 키 분리를 잘한다 | 설계가 복잡하다 | 규제/고보안 환경 |
| 주기적 rotation | 사고 범위를 줄인다 | 운영 작업이 늘어난다 | 중요한 키 |
| 상시 rotation | 침해 지속 시간을 줄인다 | 복잡도가 높다 | 매우 민감한 환경 |

핵심 판단 기준은 **유출을 0으로 만드는 것보다, 유출되더라도 회수 가능하게 만드는 것**이다.

---

## 꼬리질문

> Q: 환경변수에 secret을 넣으면 안전한가요?
> 의도: 편의성과 노출 범위를 구분하는지 본다.
> 핵심: 단순하지만 안전하지 않다.

> Q: rotation을 무중단으로 하려면 무엇이 필요하나요?
> 의도: 배포와 비밀 교체를 분리하는 사고를 확인한다.
> 핵심: dual read, cutover, revoke 단계가 필요하다.

> Q: 로그에서 secret이 유출되면 왜 키만 바꾸면 안 되나요?
> 의도: downstream 영향과 세션/토큰 폐기를 아는지 본다.
> 핵심: 이미 발급된 토큰/credential 회수 전략도 필요하다.

## 한 줄 정리

시크릿 관리는 저장 방식보다 유출 경로, 회전 절차, 폐기 전략이 핵심이다.
