---
schema_version: 3
title: DNS 변경 후 일부 사용자만 예전 서버로 감 원인 라우터
concept_id: network/dns-change-some-users-old-server-symptom-router
canonical: false
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- ttl-vs-split-horizon
- dig-vs-browser-resolver-drift
- stale-connection-after-cutover
aliases:
- DNS 바꿨는데 일부만 옛 서버로 가요
- 도메인은 같은데 어떤 사람만 이전 서버로 붙어요
- 배포 후 일부 사용자만 예전 IP를 봐요
- DNS 전환했는데 몇 명만 오래된 경로를 타요
- 같은 URL인데 네트워크마다 다른 서버로 가요
- DNS 바꿨는데 회사 사람만 예전 주소로 가요
symptoms:
- DNS를 바꿨다고 들었는데 어떤 사용자만 계속 이전 서버나 이전 IP로 붙어서 배포가 안 끝난 것처럼 보인다
- 내 브라우저에서는 새 서버가 보이는데 동료 브라우저나 특정 네트워크에서는 아직 예전 화면이 떠서 어느 캐시가 남았는지 헷갈린다
- terminal `dig` 결과와 브라우저 실제 접속 서버가 달라서 DNS가 안 바뀐 건지 브라우저가 다른 힌트를 쓰는 건지 판단이 안 된다
- 회사 VPN이나 사무실 와이파이에서만 예전 경로로 가고 집이나 모바일망에서는 새 경로로 가서 DNS view가 갈린 것처럼 보인다
intents:
- symptom
- troubleshooting
prerequisites:
- network/dns-basics
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
next_docs:
- network/dns-ttl-cache-failure-patterns
- network/dns-split-horizon-behavior
- network/https-rr-resolver-drift-primer
- network/connection-reuse-vs-service-discovery-churn
linked_paths:
- contents/network/dns-ttl-cache-failure-patterns.md
- contents/network/dns-split-horizon-behavior.md
- contents/network/https-rr-resolver-drift-primer.md
- contents/network/browser-cache-toggles-vs-alt-svc-dns-cache-primer.md
- contents/network/alt-svc-vs-https-rr-freshness-bridge.md
- contents/network/connection-reuse-vs-service-discovery-churn.md
- contents/network/dns-over-https-operational-tradeoffs.md
confusable_with:
- network/first-request-h2-next-request-h3-symptom-router
- network/postman-works-browser-fails-symptom-router
- network/browser-421-but-curl-200-symptom-router
forbidden_neighbors:
expected_queries:
- DNS를 바꿨는데 왜 일부 사용자만 계속 예전 서버로 가요?
- 배포 후 몇 명만 이전 IP를 보는 상황이면 어디부터 의심해야 해?
- 브라우저는 새 서버로 가는데 동료는 옛 서버로 가면 DNS 캐시를 어떻게 나눠 봐야 해?
- 회사 와이파이에서만 이전 경로로 가고 집에서는 정상일 때 무슨 차이를 봐야 해?
- dig 결과와 실제 브라우저 접속 서버가 다를 때 DNS 전파 문제인지 어떻게 판단해?
contextual_chunk_prefix: |
  이 문서는 DNS를 변경했는데도 일부 사용자만 이전 서버, 이전 IP, 예전 경로로
  계속 붙는 장면에서 원인을 캐시 TTL 잔존, split-horizon DNS, browser DoH와
  system resolver 차이, connection reuse와 discovery churn으로 가르는 network
  symptom_router다. DNS 바꿨는데 몇 명만 옛 서버로 감, 회사 와이파이에서만
  예전 주소로 감, dig와 브라우저가 다른 서버를 봄 같은 학습자 표현이 이 문서의
  분기와 다음 학습 문서 추천으로 매핑된다.
---

# DNS 변경 후 일부 사용자만 예전 서버로 감 원인 라우터

## 한 줄 요약

> 같은 도메인인데 일부 사용자만 예전 서버로 가면 "DNS가 아직 안 바뀌었다"보다 먼저 어떤 캐시와 어떤 resolver가 아직 다른 현실을 보고 있는지 분리해서 본다.

## 가능한 원인

1. DNS TTL이 끝나지 않아 브라우저, OS resolver, recursive resolver 중 일부가 이전 answer를 아직 들고 있을 수 있다. 이런 경우 authoritative zone은 이미 바뀌었는데도 사용자마다 다른 IP를 본다. 다음 문서: [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
2. 회사 DNS와 외부 DNS가 의도적으로 다른 답을 주는 split-horizon 환경일 수 있다. 사무실, VPN, 내부망에서만 예전 서버를 보면 "전파 지연"보다 "다른 view"일 가능성을 먼저 남겨 둔다. 다음 문서: [DNS Split-Horizon Behavior](./dns-split-horizon-behavior.md)
3. 브라우저는 DoH나 `HTTPS` RR, `Alt-Svc` 힌트를 보고 있고 terminal `dig`는 다른 resolver를 보고 있을 수 있다. 그래서 `dig`에는 새 answer가 없는데 브라우저는 이미 다른 경로를 타거나, 반대로 `dig`는 새 answer인데 브라우저는 옛 힌트를 쓸 수 있다. 다음 문서: [HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나](./https-rr-resolver-drift-primer.md), [Browser Cache Toggles vs Alt-Svc DNS Cache Primer](./browser-cache-toggles-vs-alt-svc-dns-cache-primer.md)
4. DNS answer는 이미 바뀌었지만 기존 connection reuse나 service discovery churn 때문에 실제 요청은 잠시 예전 경로를 탈 수 있다. 특히 long-lived connection이나 pool이 남아 있으면 "DNS는 바뀌었는데 트래픽은 안 옮겨갔다"처럼 보인다. 다음 문서: [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)

## 빠른 자기 진단

1. 영향을 받는 사용자를 네트워크별로 나눈다. 사무실 와이파이, VPN, 집, 모바일망 중 어디서만 예전 서버로 가는지 적으면 TTL 문제와 view 차이를 빨리 가를 수 있다.
2. browser 주소창의 host와 terminal에서 확인한 host가 정말 같은지 맞춘다. `www`와 apex가 섞이거나 다른 서브도메인을 보면 DNS 문제를 잘못 읽기 쉽다.
3. 같은 시점에 `dig`를 system resolver와 지정 resolver 둘 다로 비교하고, 브라우저 Secure DNS 여부도 같이 확인한다. 관측 지점이 다르면 answer가 달라도 이상하지 않다.
4. 응답 헤더나 접속 로그로 실제로 어느 서버에 붙었는지 확인한다. DNS answer가 새 값이어도 기존 connection이 살아 있으면 요청 owner는 여전히 예전 서버일 수 있다.
5. 브라우저 캐시를 껐다고 DNS, `Alt-Svc`, socket pool이 함께 초기화된다고 가정하지 않는다. "새로고침했는데 그대로"라는 증상은 캐시 종류가 다르다는 신호일 수 있다.

## 다음 학습

- TTL과 캐시 층이 왜 사용자별 시간차를 만드는지 보려면 [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
- 회사망과 외부망이 다른 답을 주는 장면을 분리하려면 [DNS Split-Horizon Behavior](./dns-split-horizon-behavior.md)
- 브라우저 DoH, `HTTPS` RR, `dig` 결과가 왜 어긋나는지 좁히려면 [HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나](./https-rr-resolver-drift-primer.md)
- DNS는 바뀌었는데 기존 연결이 남아 트래픽 이동이 늦는 장면을 보려면 [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)
