---
schema_version: 3
title: "IP Address and Port Basics"
concept_id: network/ip-address-port-basics
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- network-basics
- ip-port-socket
- beginner-network
aliases:
- IP address basics
- port basics
- IP와 포트 차이
- socket endpoint
- well-known port
- localhost 127.0.0.1
- 8080 port
symptoms:
- IP 주소와 포트를 모두 물리적 통로처럼 이해한다
- 같은 서버 포트에 여러 클라이언트가 동시에 붙는 이유를 설명하지 못한다
- localhost, 127.0.0.1, 서버 포트, 클라이언트 임시 포트를 섞는다
- HTTP 기본 포트 80과 HTTPS 기본 포트 443 생략 규칙을 모른다
intents:
- definition
- comparison
- deep_dive
prerequisites: []
next_docs:
- network/osi-7-layer-basics
- network/dns-basics
- network/ipv4-vs-ipv6-operational-tradeoffs
- system-design/load-balancer-basics
linked_paths:
- contents/network/tcp-congestion-control.md
- contents/network/dns-ttl-cache-failure-patterns.md
- contents/network/osi-7-layer-basics.md
- contents/network/dns-basics.md
- contents/system-design/load-balancer-basics.md
confusable_with:
- network/dns-basics
- network/osi-7-layer-basics
- network/ipv4-vs-ipv6-operational-tradeoffs
forbidden_neighbors: []
expected_queries:
- "IP 주소와 포트의 차이를 초보자에게 설명해줘"
- "소켓이 IP와 포트 조합이라는 말이 무슨 뜻이야?"
- "같은 서버 443 포트에 여러 클라이언트가 동시에 연결되는 이유는?"
- "localhost 127.0.0.1과 8080 포트를 어떻게 이해하면 돼?"
- "well-known port와 dynamic port 차이는 뭐야?"
contextual_chunk_prefix: |
  이 문서는 IP address, port number, socket endpoint, localhost,
  well-known/registered/dynamic port, 서버 포트와 클라이언트 임시 포트를
  설명하는 beginner primer다.
---
# IP 주소와 포트 기초

> 한 줄 요약: IP 주소는 인터넷에서 컴퓨터를 찾는 주소이고, 포트는 그 컴퓨터 안에서 어느 프로세스와 통신할지를 구분하는 번호다.

**난이도: 🟢 Beginner**

관련 문서:

- [TCP 혼잡 제어](./tcp-congestion-control.md)
- [DNS TTL과 캐시 실패 패턴](./dns-ttl-cache-failure-patterns.md)
- [network 카테고리 인덱스](./README.md)
- [로드밸런서 기초](../system-design/load-balancer-basics.md)

retrieval-anchor-keywords: ip address basics, port basics, ip 주소 뭔가요, 포트 번호 뭔가요, ip와 포트 차이, 소켓이란 뭔가요, ipv4 ipv6 입문, well-known port, 8080 포트가 뭐예요, beginner ip port socket, ip address port basics basics, ip address port basics beginner, ip address port basics intro, network basics, beginner network

## 핵심 개념

인터넷에서 데이터를 전달하려면 목적지를 두 단계로 좁혀야 한다. 첫째로 어느 **컴퓨터**인지 식별해야 하고, 둘째로 그 컴퓨터 안의 어느 **프로세스**인지 알아야 한다. IP 주소는 첫 번째 문제를, 포트는 두 번째 문제를 해결한다. 입문자가 헷갈리는 부분은 "포트가 뭔지는 알겠는데 실제로 어떻게 쓰이는지" 모른다는 것이다.

## 한눈에 보기

| 개념 | 역할 | 예시 |
|---|---|---|
| IP 주소 | 네트워크에서 호스트(컴퓨터) 식별 | 192.168.0.1, 203.0.113.5 |
| 포트 | 같은 호스트에서 프로세스 구분 | 80, 443, 8080, 5432 |
| 소켓 | IP + 포트 조합, 통신 끝점 | 203.0.113.5:443 |

## 상세 분해

### IP 주소

IPv4 주소는 0~255 사이 숫자 4개를 점(.)으로 구분한 형식이다. 예: `192.168.0.1`. 총 약 43억 개의 주소가 가능한데, 인터넷 사용 기기가 폭발적으로 늘면서 부족해졌다. 그래서 IPv6가 등장했다. IPv6는 `2001:db8::1` 형식의 훨씬 긴 주소 체계다.

로컬 환경에서 자주 보는 `127.0.0.1`은 **루프백 주소**로 "자기 자신"을 가리킨다. `localhost`를 DNS로 해석하면 이 주소가 나온다.

### 포트 번호

0~65535 사이의 숫자다. 한 호스트에서 여러 프로세스가 동시에 네트워크 통신을 하므로, 어느 프로세스가 해당 패킷을 받을지 구분하는 식별자다.

- **Well-known ports (0~1023)**: 예약된 번호. HTTP=80, HTTPS=443, SSH=22, MySQL=3306.
- **등록 포트 (1024~49151)**: 서비스가 등록해서 쓰는 번호. Spring Boot 기본값 8080 같은 것.
- **동적 포트 (49152~65535)**: OS가 클라이언트 측 임시 포트로 할당한다.

### 소켓

IP + 포트의 조합을 **소켓**이라 한다. 연결 하나는 `(클라이언트 IP:포트, 서버 IP:포트)` 쌍으로 고유하게 식별된다. 같은 서버 포트에 여러 클라이언트가 동시에 연결할 수 있는 이유는 클라이언트 쪽 포트가 각각 다르기 때문이다.

## 흔한 오해와 함정

- "서버가 8080 포트를 열었다"는 말을 듣고 포트 자체가 물리적 통로라고 오해하는 경우가 있다. 포트는 번호일 뿐이고, 실제로는 OS가 해당 번호로 들어오는 패킷을 어느 프로세스에 전달할지 매핑을 관리한다.
- 포트 80과 443은 각각 HTTP, HTTPS의 기본값이다. 브라우저가 `http://example.com`에 접속할 때 `:80`을 생략해도 되는 이유가 기본값이기 때문이다.
- 같은 포트를 두 프로세스가 동시에 열 수 없다. Spring Boot를 두 번 실행하면 `Address already in use: 8080` 오류가 나는 이유다.

## 실무에서 쓰는 모습

Spring Boot 애플리케이션은 기본으로 8080 포트를 연다. 외부에서 접근할 때 `http://localhost:8080/api/users` 처럼 URL에 포트를 명시한다. 운영 환경에서는 Nginx 같은 로드밸런서가 80/443으로 들어오는 요청을 내부 8080으로 포워딩한다. 이때 클라이언트는 포트 번호를 몰라도 된다.

DB 접속 시에는 MySQL 3306, PostgreSQL 5432 같은 포트를 커넥션 URL에 명시한다. 예: `jdbc:mysql://db.example.com:3306/mydb`.

## 더 깊이 가려면

- [OSI 7계층 기초](./osi-7-layer-basics.md) — IP와 포트가 OSI 모델 어느 계층에서 동작하는지
- [DNS 기초](./dns-basics.md) — IP 주소를 사람이 읽기 쉬운 도메인으로 매핑하는 방법

## 면접/시니어 질문 미리보기

**Q. IP 주소와 포트의 차이를 설명해 주세요.**
IP 주소는 네트워크에서 호스트를 식별하고, 포트는 그 호스트 안의 어느 프로세스와 통신할지 구분한다. 조합하면 소켓이 된다.

**Q. 같은 서버에 여러 클라이언트가 동시에 연결할 수 있는 이유는?**
서버 포트는 동일하지만, 각 클라이언트는 OS가 자동으로 다른 임시 포트를 할당하므로 `(클라이언트 IP:포트, 서버 IP:포트)` 쌍이 각 연결마다 고유하다.

**Q. Well-known port를 직접 쓰려면 왜 관리자 권한이 필요한가요?**
1024 미만 포트는 시스템 예약 범위여서 OS가 루트(관리자) 권한 없이는 바인딩을 허용하지 않는다. 보안 및 서비스 충돌 방지 목적이다.

## 한 줄 정리

IP 주소는 컴퓨터를 찾고, 포트는 그 컴퓨터 안의 프로세스를 찾는다.
