---
schema_version: 3
title: 로드 밸런서 기초 (Load Balancer Basics)
concept_id: system-design/load-balancer-basics
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/backend
review_feedback_tags:
- l4-vs-l7-boundary
- sticky-session-vs-stateless
- health-check-readiness-basics
aliases:
- load balancer basics
- 로드 밸런서 입문
- load balancer 뭐예요
- l4 l7 로드밸런서
- health check 기초
- 서버 부하 분산
- 트래픽 분산
- sticky session 기초
- horizontal scaling with load balancer
symptoms:
- 서버를 여러 대 띄웠는데 요청을 어디로 나눠 보내야 하는지 모르겠어
- sticky session이 왜 필요하고 왜 위험한지 한 번에 정리가 안 돼
- L4랑 L7을 어디 기준으로 나누는지 헷갈려
intents:
- definition
- comparison
- troubleshooting
prerequisites:
- system-design/system-design-foundations
- system-design/stateless-vs-stateful-basics
next_docs:
- system-design/load-balancer-drain-and-affinity-primer
- system-design/service-discovery-health-routing-design
- system-design/global-traffic-failover-control-plane-design
linked_paths:
- contents/system-design/load-balancer-drain-and-affinity-primer.md
- contents/system-design/stateless-backend-cache-database-queue-starter-pack.md
- contents/system-design/stateless-vs-stateful-basics.md
- contents/system-design/system-design-foundations.md
- contents/system-design/service-discovery-health-routing-design.md
- contents/system-design/global-traffic-failover-control-plane-design.md
- contents/system-design/request-path-failure-modes-primer.md
- contents/system-design/api-gateway-basics.md
- contents/network/http-https-basics.md
confusable_with:
- system-design/service-discovery-health-routing-design
- system-design/api-gateway-basics
- system-design/stateless-vs-stateful-basics
forbidden_neighbors: []
expected_queries:
- 로드 밸런서는 왜 서버 여러 대 앞에 두는 거야?
- 처음 배우는 입장에서 L4 로드 밸런서와 L7 로드 밸런서를 어떻게 구분해?
- sticky session을 쓰면 수평 확장이 왜 불편해져?
- health check가 왜 없으면 장애 서버로 계속 요청이 가?
- 로드 밸런서와 stateless 앱 설계를 왜 같이 설명해?
contextual_chunk_prefix: |
  이 문서는 로드 밸런서를 처음 배우는 학습자가 요청 분산, health check,
  L4/L7 차이, sticky session과 stateless 확장 관계를 한 번에 잡게 돕는
  beginner primer다. 서버를 여러 대 두면 누가 나눠 보내나, 왜 health
  check가 필요하나, sticky session이 왜 scale-out을 꼬이게 하나 같은
  자연어 질문이 본 문서의 기본 mental model로 매핑된다.
---
# 로드 밸런서 기초 (Load Balancer Basics)

> 한 줄 요약: 로드 밸런서는 들어오는 요청을 여러 서버 인스턴스에 나눠 보내서 한 서버가 과부하되지 않도록 막는 중간 컴포넌트다.

**난이도: 🟢 Beginner**

관련 문서:

- [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)
- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md)
- [System Design Foundations](./system-design-foundations.md)
- [HTTP/HTTPS 기초](../network/http-https-basics.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: load balancer basics, 로드 밸런서 입문, load balancer 뭐예요, round robin 알고리즘, least connection, l4 l7 로드밸런서, health check 기초, 서버 부하 분산, 수평 확장 입문, beginner load balancing, 트래픽 분산, sticky session 기초, stateless app load balancer, 왜 sticky session 필요한가요, horizontal scaling with load balancer

---

## 핵심 개념

로드 밸런서는 "여러 서버 인스턴스 앞에서 요청을 분배하는 교통 정리 역할"을 한다.
입문자가 자주 헷갈리는 지점은 **로드 밸런서가 없으면 무슨 일이 생기는가**이다.

서버 하나에 트래픽이 몰리면:

- 응답이 느려지고 타임아웃이 발생한다.
- 서버가 다운되면 전체 서비스도 다운된다.
- 스케일 업(서버 사양 높이기)에는 한계가 있다.

로드 밸런서를 두면 요청을 여러 서버로 나눠 처리하고, 한 서버가 죽어도 나머지 서버가 계속 요청을 받는다.

---

## 한눈에 보기

```text
클라이언트 A -\
클라이언트 B --- 로드 밸런서 -> 서버 1
클라이언트 C -/              -> 서버 2
                             -> 서버 3
```

대표적인 분배 알고리즘:

| 알고리즘 | 설명 | 언제 쓰나 |
|---|---|---|
| Round Robin | 순서대로 돌아가며 배분 | 서버 성능이 같을 때 |
| Least Connection | 현재 연결 수가 적은 서버에 보냄 | 요청 처리 시간이 들쭉날쭉할 때 |
| IP Hash | 클라이언트 IP 기반으로 고정 | Sticky Session이 필요할 때 |

초보자가 자주 묶어서 묻는 질문은 "로드 밸런서가 있으면 왜 또 stateless app 이야기를 하나요?"이다. 연결은 아래 표로 보면 된다.

| 상황 | 로드 밸런서가 하는 일 | 앱 설계에서 같이 봐야 할 점 | 결과 |
|---|---|---|---|
| stateless app 여러 대 | 건강한 인스턴스로 요청을 고르게 나눈다 | 중요한 상태를 서버 메모리 대신 DB, Redis, 토큰 같은 바깥 저장소에 둔다 | 어느 서버가 받아도 처리 가능해서 수평 확장이 쉽다 |
| sticky session 사용 | 같은 사용자를 같은 서버에 붙여 보낸다 | 세션이 서버 로컬에 있으면 일단 동작하지만 서버 교체와 장애 대응이 불편해진다 | 로그인 유지 문제는 줄지만 scale-out 이점이 일부 줄어든다 |
| horizontal scaling 시작 | 인스턴스 수가 늘어나도 입구를 하나처럼 유지한다 | 새 서버가 들어와도 같은 규칙으로 처리되도록 stateless에 가깝게 설계한다 | 트래픽 증가 시 서버를 추가하는 방식이 단순해진다 |

---

## 상세 분해

- **L4 로드 밸런서**: TCP/UDP 레이어에서 동작한다. 패킷 내용을 보지 않고 IP/포트 기반으로 분배한다. 빠르지만 HTTP 헤더나 쿠키를 볼 수 없다.
- **L7 로드 밸런서**: HTTP 레이어에서 동작한다. URL 경로, 헤더, 쿠키를 보고 분배할 수 있다. API Gateway와 역할이 겹치기도 한다.
- **헬스 체크**: 로드 밸런서는 주기적으로 각 서버에 헬스 체크 요청을 보낸다. 응답이 없거나 에러가 나면 해당 서버를 분배 대상에서 제외한다.
- **Sticky Session**: 동일 사용자의 요청을 항상 같은 서버로 보내는 방식이다. 세션 상태를 서버 로컬에 저장할 때 자주 쓰지만, 서버 장애나 교체 시 세션도 함께 영향을 받기 쉽다.
- **Stateless app과의 연결**: 로드 밸런서는 요청을 나눌 뿐이고, 어느 서버로 가도 처리되게 만드는 책임은 애플리케이션 설계에 있다. 그래서 "로드 밸런서 도입"과 "상태 외부화"는 보통 한 묶음으로 설명된다.

---

## 흔한 오해와 함정

- **"로드 밸런서를 쓰면 서버가 무한 확장된다"**: 로드 밸런서 자체가 단일 장애점이 될 수 있다. 로드 밸런서도 이중화(Active-Passive, Active-Active)가 필요하다.
- **"L7 로드 밸런서가 항상 낫다"**: 처리 비용이 L4보다 크다. 단순 TCP 트래픽을 L7으로 처리하면 불필요한 오버헤드가 생긴다.
- **"Sticky Session을 쓰면 부하 분산이 안 된다"**: 일부 서버에 특정 사용자가 몰릴 수 있다. 세션은 외부 저장소(Redis 등)에 두고 서버를 stateless로 만드는 편이 낫다.
- **"Sticky Session은 무조건 나쁜 설계다"**: 꼭 그렇지는 않다. 기존 세션 기반 앱을 급하게 여러 대로 늘릴 때 임시 완충책이 될 수 있다. 다만 장기적으로는 stateless app 또는 외부 세션 저장소 쪽이 보통 운영과 배포에 유리하다.

---

## 실무에서 쓰는 모습

서비스 배포 시 가장 흔한 시나리오는 새 버전을 무중단으로 올리는 것이다.

1. 로드 밸런서에서 서버 2를 분배 대상에서 잠시 제외한다(드레이닝).
2. 서버 2에 새 버전을 배포한다.
3. 헬스 체크 통과 후 로드 밸런서가 서버 2를 다시 분배 대상에 추가한다.
4. 서버 1, 3도 동일하게 순차 교체한다.

AWS에서는 ALB(Application Load Balancer)가 L7, NLB(Network Load Balancer)가 L4 역할로 자주 쓰인다.

---

## 더 깊이 가려면

- [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md) — 연결 드레이닝, Sticky 배포 시 꼬리 문제, 실무 함정
- [System Design Foundations](./system-design-foundations.md) — 로드 밸런서가 전체 시스템 구조에서 어디에 위치하는지
- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md) — 로드 밸런서가 stateless app, DB, cache, queue와 한 그림에서 어떻게 이어지는지
- [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md) — sticky session이 왜 scale-out 제약으로 이어지는지

---

## 면접/시니어 질문 미리보기

> Q: L4 로드 밸런서와 L7 로드 밸런서의 차이는 무엇인가요?
> 의도: 네트워크 레이어와 분배 기준의 차이를 이해하는지 확인
> 핵심: L4는 TCP/IP 기반으로 패킷 내용을 보지 않고 빠르게 분배하고, L7은 HTTP 헤더/URL/쿠키를 보고 세밀한 분배가 가능하다.

> Q: Sticky Session의 장단점은 무엇인가요?
> 의도: 서버 상태 관리와 부하 분산 간의 트레이드오프 이해 확인
> 핵심: 동일 사용자를 같은 서버로 보내 세션 유지가 쉽지만, 특정 서버에 부하가 몰릴 수 있고 서버 장애 시 세션이 유실된다.

> Q: 로드 밸런서 없이 트래픽이 급증하면 어떤 일이 생기나요?
> 의도: 로드 밸런서 도입 동기와 단일 서버의 한계 이해 확인
> 핵심: 단일 서버는 CPU/메모리가 포화되어 응답 지연이 늘고, 서버 다운 시 전체 서비스가 중단된다.

---

## 한 줄 정리

로드 밸런서는 요청을 여러 서버로 분산해 단일 서버 과부하를 막고, 헬스 체크로 장애 서버를 자동으로 제외해 가용성을 높이는 컴포넌트다.
