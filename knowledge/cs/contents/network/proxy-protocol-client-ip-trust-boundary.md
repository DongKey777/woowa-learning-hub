# Proxy Protocol, Client IP, Trust Boundary

> 한 줄 요약: Proxy Protocol은 L4/L7 앞단이 원래 client 정보를 백엔드에 전달하는 장치지만, 그 값을 믿을 수 있는 범위는 결국 trust boundary 안으로만 제한해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)

retrieval-anchor-keywords: PROXY protocol, proxy protocol v1, proxy protocol v2, original source address, TLV, trust boundary, L4 load balancer, TCP proxy, client IP preservation

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`Proxy Protocol`은 TCP 연결의 시작 부분에 원래 source/destination 정보를 실어 보내는 방식이다.  
주로 LB나 proxy가 백엔드에 "이 연결은 원래 여기서 왔다"는 메타데이터를 전달할 때 쓴다.

이게 중요한 이유는 다음과 같다.

- 앱이 보게 되는 TCP peer IP는 프록시 IP일 수 있다
- HTTP 헤더는 클라이언트가 임의로 넣을 수 있다
- 하지만 Proxy Protocol은 연결 계층에서 전달되므로, 올바른 trust boundary 안에서 보면 더 강한 신호가 된다

### Retrieval Anchors

- `PROXY protocol`
- `proxy protocol v1`
- `proxy protocol v2`
- `original source address`
- `TLV`
- `trust boundary`
- `L4 load balancer`
- `client IP preservation`

## 깊이 들어가기

### 1. Proxy Protocol이 해결하는 문제

프록시가 앞에 있으면 backend는 보통 `remote_addr`만 본다.

- 실제 client IP가 사라진다
- Geo/IP 기반 정책이 꼬인다
- rate limit과 audit log가 부정확해진다

HTTP의 `Forwarded`나 `X-Forwarded-For`는 이 문제를 해결하지만, HTTP 위에서만 쓸 수 있다.  
반면 Proxy Protocol은 TCP 연결의 앞부분에 붙기 때문에, HTTP가 아니어도 client 정보를 전달할 수 있다.

### 2. v1과 v2는 어떻게 다른가

- `v1`: 사람이 읽을 수 있는 텍스트 형태
- `v2`: 바이너리 형태라 더 유연하고, TLV 같은 확장 필드를 실을 수 있다

운영에서는 v2를 더 자주 선호한다.

- 더 많은 메타데이터를 넣을 수 있다
- 비HTTP 프로토콜과도 잘 맞는다
- 파싱이 명확하다

### 3. 언제 쓰는가

Proxy Protocol은 다음 환경에서 특히 유용하다.

- TCP pass-through TLS termination
- gRPC backend
- Postgres/MySQL/Redis 앞단 L4 proxy
- HTTP가 아닌 자체 프로토콜

즉, **헤더를 넣을 수 없는 레이어**에서 원본 client identity를 보존하고 싶을 때 쓴다.

### 4. trust boundary를 잘못 잡으면 왜 위험한가

Proxy Protocol은 "신뢰되는 앞단"이 붙여 줬을 때만 의미가 있다.

- 외부 client가 임의로 보내면 안 된다
- backend는 listener가 proxy protocol을 기대하는지 알아야 한다
- 중간 proxy가 두 번 붙이면 header가 중복될 수 있다

이걸 놓치면 다음 문제가 생긴다.

- 앱이 잘못된 client IP를 신뢰한다
- health check가 protocol mismatch로 실패한다
- 로그가 깨진다
- 연결 초기화 시점에 바로 에러가 난다

### 5. HTTP 헤더와의 차이

`X-Forwarded-For`는 HTTP request header다.

- HTTP 라우팅과 로그에 좋다
- 클라이언트가 직접 조작할 수 있다
- trusted proxy chain이 반드시 필요하다

`Proxy Protocol`은 transport layer 메타데이터에 가깝다.

- HTTP뿐 아니라 TCP 서비스에도 쓸 수 있다
- LB가 실제 연결 정보를 넘길 수 있다
- 하지만 backend가 이를 지원해야 한다

둘은 경쟁 관계가 아니라 **레이어가 다른 도구**다.

## 실전 시나리오

### 시나리오 1: backend 로그에 LB IP만 찍힌다

원인:

- TCP source는 LB가 되고
- backend가 Proxy Protocol을 읽지 못한다

대응:

- backend listener에 proxy protocol을 켠다
- LB에서 send-proxy를 맞춘다
- 앱의 client IP 파싱 경로를 수정한다

### 시나리오 2: health check는 되는데 실제 요청은 실패한다

health check는 plain TCP 또는 별도 경로로 나가고, 실제 서비스 연결은 Proxy Protocol을 기대한다면 protocol mismatch가 생길 수 있다.

이때는 health check 경로와 service path의 설정이 같은지 봐야 한다.

### 시나리오 3: TLS pass-through 뒤에서 원본 IP가 사라진다

HTTP 헤더를 못 넣는 구조라면 `X-Forwarded-For`만으로는 부족하다.

이 경우 Proxy Protocol이 더 맞을 수 있다.

### 시나리오 4: 로그는 맞는데 rate limit이 이상하다

앱이 proxy IP를 client IP로 오인하면 모든 요청이 같은 IP로 보일 수 있다.

그 결과:

- 너무 빨리 차단되거나
- 반대로 allowlist가 무력화된다

## 코드로 보기

### HAProxy에서 Proxy Protocol을 내보내는 예시

```haproxy
frontend tcp_in
    bind :443 ssl crt /etc/haproxy/cert.pem
    default_backend app_backend

backend app_backend
    server app1 10.0.1.10:8443 send-proxy-v2
```

### Nginx stream에서 받는 예시

```nginx
stream {
    server {
        listen 8443 proxy_protocol;
        proxy_pass app_backend;
    }
}
```

### HTTP 계층과 함께 쓸 때

```nginx
server {
    listen 443 ssl proxy_protocol;

    set_real_ip_from 10.0.0.0/8;
    real_ip_header proxy_protocol;

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

포인트:

- transport metadata와 HTTP header를 섞어도 된다
- 하지만 둘의 source of truth를 분명히 해야 한다

### 앱에서 IP를 읽는 감각

```text
1. peer IP가 trusted proxy인지 확인
2. Proxy Protocol 정보가 있으면 그 값을 읽는다
3. 없으면 fallback으로 remote_addr를 쓴다
4. 외부 client가 직접 넣은 값은 믿지 않는다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| X-Forwarded-For | HTTP에서 간단하다 | 조작 가능성이 크다 | HTTP-only chain |
| Proxy Protocol | L4/L7에서 client IP 보존이 쉽다 | backend와 LB 설정이 맞아야 한다 | TCP proxy, TLS pass-through |
| remote_addr만 사용 | 가장 단순하다 | 원본 IP를 잃는다 | 단일 홉 또는 내부 디버깅 |

핵심은 메타데이터가 아니라 **그 메타데이터를 누가 붙였는지**다.

## 꼬리질문

> Q: Proxy Protocol과 X-Forwarded-For는 어떤 차이가 있나요?
> 핵심: 전자는 TCP 연결 레벨, 후자는 HTTP 헤더 레벨이다.

> Q: Proxy Protocol은 보안 기능인가요?
> 핵심: 아니다. 신뢰된 proxy가 붙여 줬을 때만 의미가 있으며, trust boundary 밖에서는 믿으면 안 된다.

> Q: v2를 왜 더 많이 쓰나요?
> 핵심: 바이너리와 TLV 확장이 가능해서 더 유연하기 때문이다.

## 한 줄 정리

Proxy Protocol은 원본 client identity를 transport 레벨에서 전달하는 유용한 도구지만, 신뢰 경계를 잘못 잡으면 그 정보가 오히려 오염된 진실이 된다.
