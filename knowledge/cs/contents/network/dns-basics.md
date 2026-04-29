# DNS 기초

> 한 줄 요약: DNS는 사람이 읽는 도메인 이름을 IP 주소로 바꿔주는 분산 시스템이며, 캐시 계층이 있어서 같은 질의를 반복하지 않아도 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [운영체제 카테고리 인덱스](../operating-system/README.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: dns basics, dns 기초, dns 뭐예요, dns 왜 필요해요, 도메인 ip 변환, 도메인을 왜 ip로 바꿔요, url 입력하면 dns가 먼저 뭐 해요, dns 처음 배우는데, dns 큰 그림, dns 조회 흐름, dns resolver, dns cache, dns ttl 기초, cname record, nslookup 기초

## 핵심 개념

DNS(Domain Name System)는 `example.com` 같은 도메인을 실제 접속에 쓰이는 IP 주소로 바꿔주는 분산 데이터베이스다. 입문자가 가장 많이 헷갈리는 점은 "IP 주소가 있는데 왜 도메인이 따로 필요한가"다. IP 주소는 사람이 외우기 어렵고, 서버가 바뀌면 IP도 바뀌지만 도메인은 그대로 유지할 수 있기 때문이다.

## 한눈에 보기

```
브라우저 → OS DNS 캐시 → (캐시 없으면) → DNS Resolver
                                              ↓
                                        Root NS → TLD NS → 권한 NS
                                                              ↓
                                                          IP 응답
```

- 캐시에 있으면 바로 IP를 쓴다.
- 없으면 계층적으로 질의한다.
- 결과는 TTL 동안 캐시된다.

## 상세 분해

### DNS 질의 흐름

1. 브라우저가 `shop.example.com`의 IP가 필요하다.
2. OS의 로컬 캐시를 확인한다. 있으면 즉시 반환.
3. 없으면 설정된 **DNS Resolver(재귀 서버)**에 질의한다.
4. Resolver가 없으면 Root NS → TLD NS(`.com` 담당) → 권한 NS(`example.com` 담당) 순으로 질의한다.
5. 최종 IP를 받아서 Resolver가 캐시하고 브라우저에 돌려준다.

### 주요 DNS 레코드 종류

| 레코드 | 역할 |
|---|---|
| A | 도메인 → IPv4 주소 |
| AAAA | 도메인 → IPv6 주소 |
| CNAME | 도메인 → 다른 도메인 별칭 |
| MX | 도메인 → 이메일 서버 |
| TXT | 임의 텍스트, 도메인 인증 등 |

### HTTPS RR과 SVCB는 어디에 쓰이나

처음 DNS를 배울 때는 A, AAAA, CNAME만 먼저 익혀도 충분하다. 다만 웹 연결에서는 `HTTPS RR`과 `SVCB`가 "`이 도메인은 이런 웹 연결 힌트를 가진다`"는 정보를 줄 수 있다.

- A/AAAA는 "어느 IP로 갈까"에 가깝다.
- HTTPS RR/SVCB는 "이 웹 서비스가 H3 같은 경로를 먼저 시도해 볼 힌트가 있나"에 가깝다.
- 입문 단계에서는 "`DNS가 웹 연결 힌트도 줄 수 있다`" 정도만 기억하면 된다.

예를 들어 브라우저가 DNS에서 HTTPS RR을 먼저 받으면 첫 요청 전에도 "`HTTP/3를 시도해 볼까?`"를 판단하는 데 쓸 수 있다. 이 흐름은 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)에서 짧은 타임라인으로 이어서 볼 수 있다.

### TTL(Time To Live)

각 DNS 응답에는 TTL이 붙는다. 이 시간 동안은 캐시된 결과를 쓴다.

- TTL이 짧으면 변경이 빨리 반영되지만 DNS 질의 빈도가 높아진다.
- TTL이 길면 변경 반영이 느리지만 캐시 효율이 좋아진다.

## 흔한 오해와 함정

- "DNS를 바꾸면 바로 반영된다"고 오해하기 쉽다. TTL이 남아 있으면 이전 IP가 계속 쓰인다.
- CNAME은 IP를 직접 반환하지 않고 다른 도메인으로 위임한다. 그 도메인을 다시 A 레코드로 조회한다.
- "DNS가 느리면 HTTP가 느리다"는 맞는 말이다. DNS 조회는 HTTP 요청보다 먼저 일어나기 때문이다.
- HTTPS RR/SVCB를 봤다고 해서 항상 첫 요청이 곧바로 `h3`가 되는 것은 아니다. DNS는 힌트를 줄 뿐이고, 실제 성립은 이후 연결 협상이 결정한다.

## 실무에서 쓰는 모습

- AWS Route 53, Cloudflare DNS 같은 서비스에서 도메인 레코드를 직접 관리한다.
- 배포 전 도메인 전파를 기다릴 때 TTL 값을 확인한다.
- 로컬에서 `nslookup example.com` 또는 `dig example.com`으로 어떤 IP로 해석되는지 확인한다.

```
# 간단한 DNS 조회 확인
nslookup example.com
```

## 더 깊이 가려면

- "`URL 입력 후 무슨 일이 일어나요?`를 DNS 앞뒤까지 한 번에 보고 싶다면 [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)"
- [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md) — TTL 오설정, 전파 지연, 부정 캐시 등 운영 이슈
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md) — DNS의 HTTPS RR과 HTTP 응답의 `Alt-Svc`가 H3 discovery에 어떻게 이어지는지
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. 브라우저가 도메인을 IP로 바꾸는 과정을 설명해 주세요.**
로컬 캐시 → DNS Resolver → Root NS → TLD NS → 권한 NS 순으로 재귀 질의하여 IP를 얻는다. TTL 동안은 캐시를 재사용한다.

**Q. A 레코드와 CNAME의 차이는 무엇인가요?**
A 레코드는 도메인을 IP로 직접 매핑하고, CNAME은 도메인을 또 다른 도메인으로 별칭 처리한다. CNAME은 최종적으로 A 레코드까지 따라가야 IP를 얻는다.

**Q. DNS TTL을 짧게 설정하면 어떤 장단점이 있나요?**
배포나 IP 변경이 빠르게 전파되지만, 그만큼 DNS 질의 빈도가 높아져 Resolver 부하와 지연이 약간 늘어날 수 있다.

## 한 줄 정리

DNS는 도메인을 IP로 바꾸는 분산 캐시 시스템이며, TTL이 변경 전파 속도를 결정한다.
