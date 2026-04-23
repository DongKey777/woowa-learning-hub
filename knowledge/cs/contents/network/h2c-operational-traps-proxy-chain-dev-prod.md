# h2c Operational Traps: Proxy Chain, Dev/Prod Drift

> 한 줄 요약: h2c 장애는 대부분 "HTTP/2를 지원한다"는 믿음에서 시작된다. 실제로는 dev proxy, ingress, mesh sidecar, local grpc client가 cleartext 진입 방식을 다르게 기대하면서 환경별로만 깨지는 함정이 많다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [h2c, Cleartext Upgrade, Prior Knowledge, Routing](./h2c-cleartext-upgrade-prior-knowledge-routing.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
> - [gRPC vs REST](./grpc-vs-rest.md)

retrieval-anchor-keywords: h2c operational traps, cleartext h2 drift, dev prod protocol mismatch, prior knowledge trap, Upgrade h2c trap, ingress h2c, grpc cleartext mismatch, proxy chain protocol drift, local dev grpc h2c, mesh cleartext routing

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

h2c operational trap의 전형적인 모습은 이렇다.

- 로컬에선 된다
- 특정 ingress 뒤에서만 안 된다
- TLS 종단점 앞에선 괜찮다
- cleartext hop이 끼는 내부망에서만 깨진다

즉 문제는 HTTP/2 자체보다 **cleartext 진입 모드가 환경마다 다르게 가정되는 것**이다.

### Retrieval Anchors

- `h2c operational traps`
- `cleartext h2 drift`
- `dev prod protocol mismatch`
- `prior knowledge trap`
- `Upgrade h2c trap`
- `ingress h2c`
- `grpc cleartext mismatch`
- `proxy chain protocol drift`

## 깊이 들어가기

### 1. dev/prod drift가 가장 흔한 함정이다

예:

- 로컬 gRPC server는 prior knowledge 허용
- staging ingress는 `Upgrade: h2c`만 이해
- prod mesh는 cleartext H2 자체를 막음

개발자는 "같은 gRPC 서비스"라고 보지만, 실제 wire entry mode는 다르다.

### 2. cleartext hop이 숨어 있으면 문제를 놓치기 쉽다

외부에선 TLS+h2가 정상이어도 내부 경로는 다를 수 있다.

- ingress 이후 cleartext
- sidecar to app cleartext
- service-to-service cleartext in trusted subnet

이때 outer hop 기준으론 h2로 보여도, inner hop은 h2c mismatch일 수 있다.

### 3. proxy chain이 upgrade header를 보존하지 않을 수 있다

`Upgrade: h2c` 경로는 중간 홉이:

- header를 이해하고
- 보존하고
- 전환 결과를 일관되게 처리

해야 한다.

하지만 일부 hop이:

- header를 제거
- HTTP/1.1로 처리
- partial fallback

하면 "가끔은 되고 가끔은 안 되는" 이상한 상태가 생긴다.

### 4. prior knowledge는 더 단순해 보여도 더 날카롭다

처음부터 preface를 보내기 때문에:

- 지원하는 hop에선 단순하다
- 모르는 hop에선 즉시 protocol error/connection close

로 끝나기 쉽다.

즉 prior knowledge는 controlled environment엔 좋지만, heterogeneous proxy chain엔 예민하다.

### 5. gRPC는 fallback이 적어 더 거칠게 깨진다

browser 트래픽은 종종 H1/H2 fallback이 자연스럽다.  
gRPC cleartext는 그렇지 않다.

- 원하는 transport가 아니면 바로 실패
- client surface는 `UNAVAILABLE` 정도로 뭉개짐
- app 로그는 비어 있을 수 있음

그래서 h2c trap은 흔히 "gRPC만 안 됨"으로 드러난다.

### 6. 운영 체크리스트는 hop-by-hop이어야 한다

좋은 질문:

- 각 hop의 entry mode는 무엇인가
- TLS termination 이후 protocol이 어떻게 바뀌는가
- upgrade header/preface가 보존되는가
- fail 시 fallback인지 reset인지 protocol error인지

한 hop만 보면 환경 차이를 놓친다.

## 실전 시나리오

### 시나리오 1: dev에서는 되는 grpcurl이 prod ingress 뒤에서만 실패한다

cleartext hop에서 h2c entry mode mismatch일 수 있다.

### 시나리오 2: mesh 도입 후 internal gRPC가 갑자기 HTTP/1.1처럼 보이거나 reset 된다

sidecar가 cleartext H2 전제를 깨거나 prior knowledge를 못 넘기는 패턴일 수 있다.

### 시나리오 3: 일부 서비스만 h2c를 허용해 route별로 동작이 다르다

route/proxy config drift를 의심해야 한다.

### 시나리오 4: client는 `UNAVAILABLE`, server는 무로그

cleartext entry 단계에서 프록시가 protocol mismatch로 자른 것일 수 있다.

## 코드로 보기

### 운영 체크 포인트

```text
- outer hop protocol: h2 or h1?
- inner cleartext hop: h2c upgrade or prior knowledge?
- ingress / sidecar / app server support matrix aligned?
- failure surface: downgrade / reset / protocol error / local reply
```

### 설계 감각

```text
prefer one cleartext H2 entry mode per environment
document hop-by-hop protocol expectations
don't assume dev prior-knowledge == prod ingress support
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| one-mode-only h2c | 운영 인지가 쉽다 | 유연성이 줄어든다 | controlled internal env |
| mixed upgrade + prior knowledge | 일부 환경 호환성이 좋아질 수 있다 | drift와 debug cost가 커진다 | 과도기 |
| TLS+h2 everywhere | 표준적이다 | 인증서/termination 비용이 늘 수 있다 | production-default |
| cleartext gRPC | 단순하고 빠를 수 있다 | trap과 mismatch 리스크가 크다 | trusted/local-only |

핵심은 h2c를 단순 기능이 아니라 **환경 간 protocol drift를 만들기 쉬운 운영 선택**으로 보는 것이다.

## 꼬리질문

> Q: 왜 h2c 문제는 dev/prod에서 다르게 보이나요?
> 핵심: 각 환경의 proxy chain이 upgrade/prior knowledge를 다르게 이해할 수 있기 때문이다.

> Q: prior knowledge가 왜 더 예민한가요?
> 핵심: 모르는 hop에선 graceful fallback보다 즉시 protocol failure로 끝나기 쉽기 때문이다.

> Q: h2c 운영에서 가장 중요한 습관은 무엇인가요?
> 핵심: hop-by-hop protocol expectation을 명시하고 한 환경에서 하나의 cleartext 진입 모드만 쓰는 것이다.

## 한 줄 정리

h2c operational trap은 HTTP/2 지원 여부보다 환경별 proxy chain이 cleartext 진입 방식을 얼마나 일관되게 이해하느냐의 문제다.
