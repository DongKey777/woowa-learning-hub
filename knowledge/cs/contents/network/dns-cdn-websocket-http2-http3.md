# DNS, CDN, HTTP/2, HTTP/3
> 브라우저 주소창에 URL을 치는 순간부터 픽셀이 찍히기까지, 보이지 않는 인프라 계층을 이해하기 위한 문서

## 핵심 개념

### DNS — 왜 첫 번째 병목인가

DNS는 도메인 이름을 IP 주소로 변환하는 분산 데이터베이스다. 중요한 이유는 **모든 HTTP 요청보다 먼저 실행되기 때문**이다. DNS가 느리면 TCP 연결조차 시작할 수 없다.

해석 순서:
1. 브라우저 캐시 → OS 캐시 → `/etc/hosts`
2. Stub Resolver → Recursive Resolver (ISP 또는 8.8.8.8 등)
3. Root NS → TLD NS (.com) → Authoritative NS
4. 응답을 TTL 동안 캐시

핵심 레코드 타입:
- `A` / `AAAA`: 도메인 → IPv4 / IPv6
- `CNAME`: 별칭 → 다른 도메인 (CDN 연결 시 자주 사용)
- `NS`: 권한 네임서버 지정
- `MX`: 메일 서버
- `TXT`: SPF, DKIM, 도메인 소유 확인 등

### CDN — 단순 캐시가 아니라 분산 인프라

CDN(Content Delivery Network)은 **지리적으로 분산된 에지 서버 네트워크**다. 원본 서버(Origin)의 부하를 줄이고 사용자에게 물리적으로 가까운 위치에서 응답한다.

동작 흐름:
1. 클라이언트가 `static.example.com`에 요청
2. DNS가 CNAME으로 CDN 도메인을 반환
3. CDN의 글로벌 로드밸런서가 가장 가까운 PoP(Point of Presence)를 선택
4. 에지에 캐시가 있으면 즉시 반환 (Cache Hit)
5. 없으면 Origin에서 가져와 캐시 후 반환 (Cache Miss)

### HTTP/2 — 멀티플렉싱과 HOL Blocking 🟡

HTTP/1.1의 문제:
- **Head-of-Line Blocking**: 하나의 TCP 연결에서 앞 요청이 끝나야 다음 요청을 보낼 수 있다
- 브라우저가 도메인당 6개 연결을 열어 우회하지만, 연결 비용이 크다
- 헤더가 매 요청마다 중복 전송된다

HTTP/2의 해결:
- **멀티플렉싱**: 하나의 TCP 연결 위에 여러 스트림을 동시에 전송
- **HPACK 헤더 압축**: 중복 헤더를 제거하고 허프만 인코딩 적용
- **서버 푸시**: 클라이언트가 요청하기 전에 리소스를 미리 전송
- **스트림 우선순위**: 중요한 리소스를 먼저 전송

**그러나 HTTP/2에도 HOL Blocking이 있다.** 이것은 TCP 레벨에서 발생한다. TCP는 바이트 스트림을 순서대로 전달해야 하므로, 하나의 패킷이 유실되면 해당 패킷이 재전송될 때까지 **같은 TCP 연결 위의 모든 스트림이 멈춘다.** HTTP/1.1에서는 6개 연결이 독립적이라 한 연결의 손실이 다른 연결에 영향을 주지 않았지만, HTTP/2는 단일 연결이라 더 치명적일 수 있다.

### HTTP/3 — QUIC으로 전송 계층 자체를 교체 🔴

HTTP/3는 TCP 대신 **QUIC(UDP 기반)** 위에서 동작한다.

QUIC의 핵심:
- **스트림 단위 독립 전송**: 한 스트림의 패킷 손실이 다른 스트림에 영향을 주지 않음 → TCP HOL Blocking 해결
- **0-RTT / 1-RTT 연결**: TLS 1.3이 내장되어 TCP 3-way handshake + TLS handshake를 합침
- **연결 마이그레이션**: Connection ID 기반이라 IP가 바뀌어도(Wi-Fi → LTE) 연결 유지
- **개선된 혼잡 제어**: 각 스트림 독립적으로 혼잡 제어 가능

---

## 깊이 들어가기

### DNS 장애 패턴 🟡

1. **TTL이 너무 길면**: Origin IP가 바뀌어도 오래된 IP로 요청이 간다. 마이그레이션이나 장애 시 전환이 느리다.
2. **TTL이 너무 짧으면**: Recursive Resolver 캐시 적중률이 떨어지고 DNS 조회 지연이 매 요청마다 추가된다.
3. **DNS 서버 자체 장애**: 애플리케이션 헬스체크는 통과하지만 외부 사용자가 접속 불가. "서버는 살아있는데 서비스가 죽은" 상황.
4. **DNS 캐시 포이즈닝**: 공격자가 위조된 DNS 응답을 주입해 사용자를 악성 서버로 유도.

### CDN 캐시 전략 🟡

| 시나리오 | 전략 |
|---------|------|
| 해시 파일명의 JS/CSS | `Cache-Control: public, max-age=31536000, immutable` |
| API 응답 | CDN에 태우지 않거나 `s-maxage=60`으로 짧게 |
| HTML 페이지 | `no-cache` + ETag로 재검증 |
| 사용자별 응답 | `private` 또는 `no-store`, CDN 캐시 금지 |

CDN에서 자주 발생하는 문제:
- **Cache Key 불일치**: 쿼리스트링, Accept-Encoding, Cookie 등이 캐시 키에 포함되어 Hit율 저하
- **Purge 지연**: 전 세계 PoP에 무효화가 전파되는 시간(보통 수초~수분)
- **Origin Shield**: CDN → Origin 트래픽을 줄이기 위한 중간 캐시 계층

### HTTP/2 서버 푸시의 현실 🔴

서버 푸시는 이론적으로 좋지만 실전에서는 거의 사용되지 않는다:
- 브라우저 캐시에 이미 있는 리소스를 중복 전송할 수 있다
- 푸시된 리소스가 클라이언트의 캐시 정책과 충돌
- Chrome 106 이후 서버 푸시 지원을 제거했다
- 대안: `103 Early Hints` 응답으로 preload 힌트를 먼저 전달

---

## 실전 시나리오

### 시나리오 1: DNS 전환 중 장애

상황: Origin 서버를 AWS에서 GCP로 마이그레이션하면서 DNS A 레코드를 변경했다.

문제: TTL을 3600초(1시간)로 설정해두었기 때문에, 변경 후에도 최대 1시간 동안 일부 사용자가 구 서버로 접속한다. 구 서버를 너무 일찍 내리면 장애가 된다.

해결:
1. 마이그레이션 전 TTL을 60초로 낮춘다 (최소 기존 TTL 시간 전에)
2. 양쪽 서버를 동시에 운영하며 전환
3. 전환 완료 후 TTL을 다시 올린다

### 시나리오 2: HTTP/2에서 패킷 손실 시 성능 역전

상황: 모바일 네트워크(패킷 손실률 2~5%)에서 HTTP/2 단일 연결로 서비스 중.

문제: TCP HOL Blocking으로 인해 HTTP/1.1(6개 연결)보다 오히려 느려진다. 하나의 패킷 손실이 모든 스트림을 블로킹한다.

해결:
- HTTP/3(QUIC)로 전환하여 스트림 독립 전송
- 전환이 어려우면 HTTP/2 연결을 여러 개 열어 위험 분산 (표준 위반이지만 실전에서 사용)

---

## 코드로 보기

### DNS 조회 확인

```bash
# DNS 해석 경로와 응답 시간 확인
dig +trace www.example.com

# TTL 확인
dig www.example.com +noall +answer
# www.example.com.     300     IN      A       93.184.216.34
#                      ^^^TTL(초)

# DNS 응답 시간 측정
dig @8.8.8.8 www.example.com | grep "Query time"
# ;; Query time: 12 msec

# 특정 네임서버에 직접 질의
dig @ns1.example.com example.com A +short
```

### HTTP 버전 확인 및 비교

```bash
# HTTP/2 지원 확인
curl -I --http2 https://www.google.com 2>&1 | head -5
# HTTP/2 200

# HTTP/3 지원 확인 (curl 7.86+)
curl --http3 -I https://www.google.com

# 연결 타이밍 상세 측정
curl -w "\
  DNS:        %{time_namelookup}s\n\
  Connect:    %{time_connect}s\n\
  TLS:        %{time_appconnect}s\n\
  TTFB:       %{time_starttransfer}s\n\
  Total:      %{time_total}s\n\
  Protocol:   %{http_version}\n" \
  -o /dev/null -s https://www.example.com
```

### CDN 캐시 상태 확인

```bash
# CDN 캐시 히트 여부 확인 (헤더에서 판단)
curl -sI https://static.example.com/app.js | grep -i "x-cache\|cf-cache\|age"
# X-Cache: HIT
# Age: 3600

# CDN을 우회하여 Origin 직접 호출 (디버깅용)
curl -H "Host: www.example.com" http://origin-ip-address/path
```

---

## 트레이드오프

### HTTP/1.1 vs HTTP/2 vs HTTP/3

| 비교 항목 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|-----------|----------|--------|--------|
| 전송 계층 | TCP | TCP | QUIC (UDP) |
| 다중화 | 연결당 1 요청 | 스트림 멀티플렉싱 | 스트림 멀티플렉싱 |
| HOL Blocking | HTTP 레벨 | TCP 레벨 (더 심각) | 없음 |
| 헤더 압축 | 없음 | HPACK | QPACK |
| 연결 수립 | TCP + TLS (2~3 RTT) | TCP + TLS (2~3 RTT) | 1 RTT (0-RTT 가능) |
| 모바일 환경 | 보통 | 패킷 손실 시 나쁨 | 좋음 |
| 인프라 지원 | 보편적 | 거의 보편적 | 방화벽/미들박스에서 UDP 차단 가능 |
| 디버깅 | 쉬움 (텍스트) | 바이너리 프레임 | 암호화 필수 + UDP |

### DNS TTL 트레이드오프

| TTL | 장점 | 단점 |
|-----|------|------|
| 짧음 (60s) | 빠른 전환, 장애 복구 | DNS 조회 빈번, 해석 지연 추가 |
| 김 (3600s) | 캐시 활용, 해석 비용 감소 | 전환 느림, 장애 시 오래 지속 |

---

## 꼬리질문

### 🟢 Basic
- DNS가 없으면 인터넷이 작동하지 않는가? → IP 직접 입력은 가능하지만 사실상 불가능. HTTPS 인증서도 도메인 기반이다.
- CDN은 어디에 두는가? → 사용자와 가까운 곳(PoP). 한국 사용자가 많으면 서울 리전의 에지 서버.

### 🟡 Intermediate
- HTTP/2가 있는데 왜 HTTP/1.1보다 항상 빠르지 않은가? → 패킷 손실이 있는 환경에서 TCP HOL Blocking이 모든 스트림에 영향. 면접관은 "무조건 좋다"가 아닌 **조건부 판단**을 보고 싶다.
- CDN에서 캐시 무효화(Purge)는 즉시 반영되는가? → 아니다. 전 세계 PoP에 전파 시간이 필요. 이것이 파일명 해시 전략을 쓰는 이유다.

### 🔴 Advanced
- HTTP/3 도입 시 가장 큰 장벽은? → UDP를 차단하는 기업 방화벽/미들박스. QUIC fallback으로 TCP(HTTP/2)를 함께 지원해야 한다.
- DNS over HTTPS(DoH)는 왜 논란인가? → 보안/프라이버시는 좋지만, 기업 네트워크의 DNS 기반 필터링/모니터링을 우회하게 된다.

---

## 한 줄 정리

DNS는 모든 요청의 시작점이고, CDN은 사용자와 Origin 사이의 거리를 줄이며, HTTP/2는 다중화로 효율을 높이지만 TCP의 한계가 남아있고, HTTP/3(QUIC)는 전송 계층 자체를 교체하여 그 한계를 근본적으로 해결한다.
