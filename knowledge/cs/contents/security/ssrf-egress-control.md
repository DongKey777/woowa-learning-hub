# SSRF / Egress Control

> 한 줄 요약: SSRF는 단순한 URL 검증 실패가 아니라, 사용자 입력이 내부 네트워크로 이어지는 신뢰 경계 붕괴다. 앱 검증과 네트워크 egress 통제가 같이 있어야 막을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway, Reverse Proxy 운영 포인트](../network/api-gateway-reverse-proxy-operational-points.md)
> - [X-Forwarded-For / X-Real-IP trust boundary](../network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [Service Mesh, Sidecar Proxy](../network/service-mesh-sidecar-proxy.md)
> - [NAT / conntrack / ephemeral port exhaustion](../network/nat-conntrack-ephemeral-port-exhaustion.md)

retrieval-anchor-keywords: SSRF, egress control, allowlist, denylist, metadata service, DNS rebinding, redirect chain, URL parser, network policy, IMDS, outbound proxy

---

## 핵심 개념

SSRF(Server-Side Request Forgery)는 서버가 외부 요청을 대신 보내는 기능을 악용해, 공격자가 우리 서버를 내부 스캐너처럼 쓰게 만드는 취약점이다.

대표적인 위험 대상은 이런 것들이다.

- 내부 관리 페이지
- VPC 내부 API
- 클라우드 metadata service
- loopback 및 private IP 대역
- 내부 DNS 이름

흔한 착각은 "URL만 화이트리스트로 검사하면 끝"이라는 생각이다.  
하지만 SSRF는 parser, DNS, redirect, proxy 설정, 네트워크 경계까지 걸친다.

즉 이 문제는 입력 검증만으로 끝나지 않고, outbound traffic을 어디까지 허용할지 정해야 하는 egress control 문제다.

---

## 깊이 들어가기

### 1. SSRF가 생기는 전형적인 기능

다음 기능은 모두 SSRF 표적이 될 수 있다.

- 이미지/파일 URL 미리보기
- webhook test URL 호출
- PDF/HTML 스크래핑
- 원격 import
- health check 대상 등록
- OAuth callback/verification 보조 기능

공통점은 서버가 사용자를 대신해 네트워크 연결을 만든다는 점이다.

### 2. URL allowlist만으로는 부족한 이유

문자열 검사만 하면 쉽게 우회된다.

- `http://127.0.0.1`
- `http://localhost`
- `http://169.254.169.254`
- `http://[::1]`
- `http://internal.example.com`가 private IP로 해석되는 경우
- redirect를 타고 내부 주소로 바뀌는 경우

심지어 DNS가 나중에 다른 IP를 가리키는 DNS rebinding도 있다.  
그래서 "호스트 문자열이 안전하다"와 "실제로 연결한 IP가 안전하다"는 다르다.

### 3. 검증 순서는 URL 문자열이 아니라 연결 대상 IP를 봐야 한다

안전한 흐름은 대체로 이렇다.

1. scheme을 제한한다
2. 호스트를 허용 목록과 비교한다
3. DNS를 resolve 한다
4. resolve된 IP가 private, loopback, link-local, multicast인지 확인한다
5. redirect를 제한하거나 다시 검증한다
6. timeout과 최대 응답 크기를 제한한다

특히 `Location` redirect는 또 다른 입력이다.

- 첫 URL은 허용됐어도
- redirect 후 최종 URL이 내부 자원일 수 있다

### 4. egress control이 마지막 방어선이다

애플리케이션 검증은 중요하지만, 혼자서는 충분하지 않다.

네트워크 계층에서도 막아야 한다.

- Kubernetes NetworkPolicy
- cloud security group / firewall egress rule
- outbound proxy allowlist
- sidecar 기반 egress policy
- metadata service 차단 또는 hop limit 강화

이렇게 하면 앱이 실수해도 내부망 전체가 바로 열리지 않는다.

### 5. 클라우드 metadata service는 특수하게 다뤄야 한다

SSRF에서 가장 위험한 표적 중 하나는 metadata service다.

- instance role credential을 빼낼 수 있다
- 임시 토큰으로 다른 리소스에 접근할 수 있다
- 사고가 곧 lateral movement로 이어진다

그래서 metadata endpoint는 기본 차단이 안전하다.  
필요하면 별도 경로와 강한 정책으로만 접근하게 둔다.

---

## 실전 시나리오

### 시나리오 1: URL preview 기능이 내부 admin 페이지를 읽음

문제:

- 사용자가 미리보기 URL에 내부 주소를 넣는다
- 서버가 해당 페이지를 대신 가져온다

대응:

- 허용 scheme을 `https`로 제한한다
- private IP와 localhost를 차단한다
- redirect를 제한한다
- outbound proxy에서 최종 목적지를 검사한다

### 시나리오 2: DNS는 외부였는데 연결 시점에 내부 IP로 바뀜

문제:

- 검증 시점과 연결 시점 사이에 DNS 응답이 달라진다

대응:

- resolve된 IP를 고정해서 사용한다
- connect 직전에 다시 IP 범위를 검증한다
- DNS cache 정책과 TTL을 명확히 둔다

### 시나리오 3: cloud metadata service에서 credentials가 새나감

문제:

- 공격자가 서버를 통해 metadata endpoint에 접근한다

대응:

- metadata service 접근을 기본 차단한다
- 필요 시 workload identity와 최소 권한만 허용한다
- outbound 로그에서 metadata 호출을 별도 감시한다

---

## 코드로 보기

### 1. URL fetch 전 검증 예시

```java
public byte[] fetchRemote(String input) throws Exception {
    URI uri = URI.create(input);
    if (!Set.of("https").contains(uri.getScheme())) {
        throw new IllegalArgumentException("unsupported scheme");
    }

    InetAddress[] addresses = InetAddress.getAllByName(uri.getHost());
    for (InetAddress address : addresses) {
        if (address.isAnyLocalAddress()
                || address.isLoopbackAddress()
                || address.isSiteLocalAddress()
                || address.isLinkLocalAddress()) {
            throw new SecurityException("blocked private destination");
        }
    }

    return httpClient.get()
        .uri(uri)
        .timeout(Duration.ofSeconds(3))
        .retrieve()
        .bodyToMono(byte[].class)
        .block();
}
```

### 2. redirect를 다시 검증하는 개념

```java
public HttpResponse executeWithRedirectGuard(URI start) {
    URI current = start;
    for (int i = 0; i < 3; i++) {
        validateDestination(current);
        HttpResponse response = doRequest(current);
        if (!response.isRedirect()) {
            return response;
        }
        current = response.redirectLocation();
    }
    throw new SecurityException("too many redirects");
}
```

### 3. egress policy 사고방식

```text
1. 앱에서 allowlist를 적용한다
2. 네트워크에서 private ranges를 차단한다
3. proxy에서 최종 목적지를 다시 본다
4. metadata service는 별도 예외로 처리한다
5. 모든 outbound 호출을 로그와 메트릭으로 남긴다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 앱 수준 allowlist | 구현이 빠르다 | 우회와 parser 차이로 깨지기 쉽다 | 기본 방어 |
| DNS 후 IP 검증 | 훨씬 강하다 | 구현이 더 복잡하다 | 거의 필수 |
| outbound proxy | 중앙 통제가 쉽다 | 운영 병목이 생길 수 있다 | 민감한 조직 |
| NetworkPolicy / SG | 앱 실수도 막는다 | 네트워크 관리가 어렵다 | 강한 보안 경계 |
| metadata hard block | credential 탈취를 줄인다 | 일부 운영 기능이 제한될 수 있다 | 클라우드 환경 |

판단 기준은 이렇다.

- 사용자가 입력한 URL을 서버가 실제로 가져가나
- 내부망 자원에 닿으면 어떤 피해가 나는가
- 네트워크 레벨 차단을 도입할 수 있는가
- redirect와 DNS rebinding을 고려했는가

---

## 꼬리질문

> Q: SSRF를 왜 URL 문자열 검사만으로 막기 어려운가요?
> 의도: parser, DNS, redirect, IP 해석 차이를 아는지 확인
> 핵심: 문자열이 안전해 보여도 실제 연결 대상은 내부일 수 있다.

> Q: egress control이 왜 중요한가요?
> 의도: 앱 방어와 네트워크 방어의 역할 분리를 이해하는지 확인
> 핵심: 앱이 실수해도 네트워크가 마지막으로 막아야 한다.

> Q: redirect는 왜 위험한가요?
> 의도: 최초 URL과 최종 목적지의 차이를 이해하는지 확인
> 핵심: 처음엔 안전해 보여도 중간에 내부 주소로 바뀔 수 있다.

> Q: metadata service가 왜 특별한 표적인가요?
> 의도: 클라우드 credential 탈취 경로를 이해하는지 확인
> 핵심: instance role credential을 빼낼 수 있기 때문이다.

## 한 줄 정리

SSRF 방어는 "입력 URL을 믿지 않기"가 아니라 "실제 연결 지점과 네트워크 경계를 끝까지 검증하기"다.
