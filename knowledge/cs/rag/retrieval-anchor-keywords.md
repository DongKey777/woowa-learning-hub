# Retrieval Anchor Keywords

> 한 줄 요약: 사용자가 문서 제목이 아니라 증상, 에러 문자열, 약어, 운영 용어로 질문할 때 검색을 붙잡아 주는 보조 키워드 규칙이다.

## 왜 필요한가

실제 질문은 문서 제목 그대로 들어오지 않는다.

예를 들면:

- `heap은 괜찮은데 RSS만 올라요`
- `nf_conntrack table full 떠요`
- `retry storm 같아요`
- `mTLS랑 SPIFFE 차이가 뭐예요`

이런 질문은 문서 제목보다 **증상, 에러 문자열, 약어, 도구 이름**으로 들어온다.
그래서 deep dive 문서에는 제목 외에 retrieval anchor를 남겨 두는 편이 RAG 회수율에 유리하다.

## 추천 형식

문서 상단 메타데이터 근처에 한 줄로 남긴다.

```markdown
> retrieval-anchor-keywords: direct buffer, off-heap, native memory, RSS, NMT
```

## 무엇을 넣는가

### 1. 한글 개념 + 영어 원어

- `서비스 간 인증, service-to-service auth`
- `멀티 테넌트, multi-tenant`

### 2. 약어 + 풀네임

- `mTLS, mutual TLS`
- `NMT, Native Memory Tracking`
- `WAL, write-ahead logging`

### 3. 증상과 에러 문자열

- `EADDRNOTAVAIL`
- `Direct buffer memory`
- `table full, dropping packet`

### 4. 운영 도구 이름

- `ss`
- `conntrack`
- `perf`
- `strace`
- `bpftrace`

### 5. 제품/구현체 이름

- `SPIFFE`
- `SPIRE`
- `Resilience4j`
- `HikariCP`

## 좋은 anchor의 특징

- 문서 제목을 그대로 반복하지 않는다.
- 사용자가 실제로 검색할 법한 표현을 넣는다.
- 같은 뜻의 표현을 4~8개 정도로 압축한다.
- 증상, 원인, 도구를 섞되 너무 길게 늘리지 않는다.

## 예시

| 문서 | anchor 예시 |
|---|---|
| `nat-conntrack-ephemeral-port-exhaustion.md` | `NAT gateway`, `conntrack`, `TIME_WAIT`, `EADDRNOTAVAIL` |
| `direct-buffer-offheap-memory-troubleshooting.md` | `off-heap`, `RSS`, `Direct buffer memory`, `NMT` |
| `service-to-service-auth-mtls-jwt-spiffe.md` | `mTLS`, `SPIFFE`, `SPIRE`, `workload identity` |
| `strangler-fig-migration-contract-cutover.md` | `shadow traffic`, `dual write`, `cutover`, `rollback` |
| `api-key-hmac-signature-replay-protection.md` | `HMAC`, `nonce`, `timestamp`, `replay attack`, `canonical string` |
| `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md` | `X-Forwarded-For`, `Forwarded`, `X-Real-IP`, `trusted proxy` |
| `monotonic-clock-wall-clock-timeout-deadline.md` | `CLOCK_MONOTONIC`, `wall clock`, `deadline propagation`, `NTP jump` |
| `payment-system-ledger-idempotency-reconciliation-design.md` | `ledger`, `reconciliation`, `auth capture refund`, `double-entry` |

## 관리 규칙

- 새 운영형 문서를 만들면 anchor를 같이 넣는다.
- anchor는 metadata로 올려 query expansion에 쓴다.
- anchor가 늘어나면 `query-playbook.md`와 `topic-map.md`도 함께 점검한다.

## 한 줄 정리

Retrieval anchor keyword는 제목 밖 검색어를 붙잡는 장치라서, 운영/장애형 문서일수록 꼭 챙기는 편이 좋다.
