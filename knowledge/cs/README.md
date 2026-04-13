# Basic Knowledge of Computer Science

> Since 2020.09.04

<p align="center">
  <img src="https://user-images.githubusercontent.com/22045163/111120575-d9370f00-85ae-11eb-8fa3-54f47ed3caa3.png" alt="coding" width="150px" />
</p>

## Table of Contents

- [About](#about)
  - [Repository Rule](#repository-rule)
  - [Collaborator](#collaborator)
  - [Reference](#reference)
- [Junior Backend Roadmap](#junior-backend-roadmap)
- [Advanced Backend Roadmap](#advanced-backend-roadmap)
- [Master Notes](#master-notes)
- [Senior-Level Questions](#senior-level-questions)
- [RAG Ready](#rag-ready)
- [Data Structure (자료구조)](#data-structure-자료구조)
- [Algorithm (알고리즘)](#algorithm-알고리즘)
- [Operating System (운영체제)](#operating-system-운영체제)
- [Database (데이터베이스)](#database-데이터베이스)
- [Network (네트워크)](#network-네트워크)
- [Design Pattern (디자인 패턴)](#design-pattern-디자인-패턴)
- [Software Engineering (소프트웨어 공학)](#software-engineering-소프트웨어-공학)
- [Spring Framework (스프링 프레임워크)](#spring-framework-스프링-프레임워크)
- [System Design (시스템 설계)](#system-design-시스템-설계)
- [Security (보안)](#security-보안)
- [Language](#language)

## About

알고리즘과 CS 기초 지식의 이론부터 구현까지, 컴퓨터공학 전공자 및 예비 개발자로서 알아야 할 필수 전공 지식들을 공부하고 기록한 저장소입니다. 매주 스터디한 흔적인 **발표 자료**들이 업로드되어 있으며, 더 나아가 **글**로, **질의응답** 형태로 문서화하는 것을 목표로 합니다.

### Repository Rule

> [CS-study Repo 가이드](https://www.notion.so/CS-study-Repo-3428a7e4213345ffa08362c7abea8528)

- **주제별 정리** : 이론정리, 구현, 자료업로드, 질의응답
- **Commit convention rule** : [대주제] 소주제 분류(이론정리/구현/...) _ex) [DataStructure] Stack 자료정리_
- **Branch naming convention** : 대주제/닉네임 _ex) DataStructure/Nickname_

### Collaborator

<p>
<a href="https://github.com/KimKwon">
  <img src="https://github.com/KimKwon.png" width="100">
</a>
<a href="https://github.com/Seogeurim">
  <img src="https://github.com/Seogeurim.png" width="100">
</a>
<a href="https://github.com/yoongoing">
  <img src="https://github.com/yoongoing.png" width="100">
</a>
<a href="https://github.com/3people">
  <img src="https://github.com/3people.png" width="100">
</a>
<a href="https://github.com/JuseobJang">
  <img src="https://github.com/JuseobJang.png" width="100">
</a>
<a href="https://github.com/Hee-Jae">
  <img src="https://github.com/Hee-Jae.png" width="100">
</a>
<a href="https://github.com/ggjae">
  <img src="https://github.com/ggjae.png" width="100">
</a>
</p>

### Reference

- [JaeYeopHan/Interview_Question_for_Beginner](https://github.com/JaeYeopHan/Interview_Question_for_Beginner)
- [gyoogle/tech-interview-for-developer](https://github.com/gyoogle/tech-interview-for-developer)
- [WeareSoft/tech-interview](https://github.com/WeareSoft/tech-interview)
- [jobhope/TechnicalNote](https://github.com/jobhope/TechnicalNote)

## Junior Backend Roadmap

- [신입 백엔드 CS 학습 순서 가이드](./JUNIOR-BACKEND-ROADMAP.md)

## Advanced Backend Roadmap

- [백엔드 심화 학습 순서 가이드](./ADVANCED-BACKEND-ROADMAP.md)

## Master Notes

- [마스터노트 인덱스](./master-notes/README.md)
- [Master Notes 안내](./MASTER-NOTES.md)

추천 진입:

- `latency / timeout / retry / backpressure`
- `transaction / consistency / idempotency / outbox`
- `auth / session / token / trust boundary`
- `migration / cutover / rollback / shadow traffic`
- `JVM / OS / native memory / page cache`

대표 노트:

- [Latency Debugging Master Note](./master-notes/latency-debugging-master-note.md)
- [Consistency Boundary Master Note](./master-notes/consistency-boundary-master-note.md)
- [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md)
- [Database to Spring Transaction Master Note](./master-notes/database-to-spring-transaction-master-note.md)
- [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md)
- [Migration Cutover Master Note](./master-notes/migration-cutover-master-note.md)

## Senior-Level Questions

- [시니어 레벨 질문 모음](./SENIOR-QUESTIONS.md)

## RAG Ready

- [RAG Ready Checklist](./RAG-READY.md)
- [RAG Design](./rag/README.md)
- [Topic Map](./rag/topic-map.md)
- [Query Playbook](./rag/query-playbook.md)
- [Retrieval Anchor Keywords](./rag/retrieval-anchor-keywords.md)
- [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md)
- [Learning Paths for Retrieval](./rag/learning-paths-for-retrieval.md)

### RAG Navigation

| 목적 | 먼저 볼 문서 |
|---|---|
| 학습 순서 잡기 | `JUNIOR-BACKEND-ROADMAP.md`, `ADVANCED-BACKEND-ROADMAP.md` |
| 개념 정의 찾기 | 루트 `README.md`, 각 카테고리 `README.md` |
| 운영/장애 판단 | `SENIOR-QUESTIONS.md`, playbook / failure pattern 문서 |
| 증상 기반 키워드 확장 | `rag/retrieval-anchor-keywords.md`, `rag/query-playbook.md` |
| 검색 라우팅 잡기 | `rag/topic-map.md`, `rag/query-playbook.md`, `rag/cross-domain-bridge-map.md` |

## Data Structure (자료구조)

### [📖 정리노트](./contents/data-structure)

#### 기본 자료 구조

- Array
- Linked List
- Stack
- Queue
- Tree
- Binary Tree
- Graph

#### 응용 자료 구조

- Deque
- Heap & Priority Queue
- Indexed Tree (Segment Tree)
- Trie
- Bloom Filter
- LRU Cache Design
- HashMap 내부 구조
- TreeMap / HashMap / LinkedHashMap 선택 기준
- Monotonic Queue / Stack
- Segment Tree Lazy Propagation
- Union-Find Deep Dive

[🔝 목차로 돌아가기](#table-of-contents)

## Algorithm (알고리즘)

### [📖 정리노트](./contents/algorithm)

#### 알고리즘 기본

- 시간복잡도와 공간복잡도
- 상각 분석과 복잡도 함정
- 완전 탐색 알고리즘 (Brute Force)
  - DFS와 BFS
  - 순열, 조합, 부분집합
- 백트래킹 (Backtracking)
- 분할 정복법 (Divide and Conquer)
- 탐욕 알고리즘 (Greedy)
- 동적 계획법 (Dynamic Programming)

#### 알고리즘 응용

- 정렬 알고리즘
- 그래프
  - 최단 경로 알고리즘
  - Union Find & Kruskal
  - 위상 정렬 패턴
- 두 포인터 (two-pointer)
- Sliding Window 패턴
- Binary Search 패턴
- Interval Greedy 패턴
- Shortest Path 알고리즘 비교
- Network Flow 기초 직관
- 문자열 처리 알고리즘
  - KMP 알고리즘

[🔝 목차로 돌아가기](#table-of-contents)

## Operating System (운영체제)

### [📖 정리노트](./contents/operating-system)

- 프로세스와 스레드
- 멀티 프로세스와 멀티 스레드
- 프로세스 스케줄링
- CPU 스케줄링
- 동기와 비동기의 차이
- 프로세스 동기화
- 메모리 관리 전략
- 가상 메모리
- 캐시
- 컨텍스트 스위칭
- 리눅스 프로세스 상태 / zombie / orphan
- epoll / kqueue / io_uring
- cgroup / namespace / container 격리
- false sharing / cache line
- futex / mutex / semaphore / spinlock
- clock / LRU 페이지 교체
- run queue / load average / CPU saturation
- page cache / dirty writeback / fsync
- NUMA 운영 디버깅 / signals / supervision
- 데드락 / 스타베이션 / lock-free

[🔝 목차로 돌아가기](#table-of-contents)

## Database (데이터베이스)

### [📖 정리노트](./contents/database)

- 데이터베이스
- 정규화
- Index
- Transaction
- NoSQL
- JDBC / JPA / MyBatis
- 트랜잭션 격리수준 / 락
- 인덱스 / 실행 계획
- MVCC / Replication / Sharding
- B+Tree / LSM-Tree
- Online Schema Change / Slow Query 분석
- Redo Log / Undo Log / Checkpoint / Crash Recovery
- Optimizer Hint / Index Merge / HikariCP / 정규화 트레이드오프
- Replica Lag / CDC / Pagination / Write Skew

[🔝 목차로 돌아가기](#table-of-contents)

## Network (네트워크)

### [📖 정리노트](./contents/network)

- OSI 7 계층
- TCP 3-way-handshake & 4-way-handshake
- TCP 와 UDP
- HTTP 요청 방식 - GET, POST
- HTTP 와 HTTPS
- HTTP 메서드 / REST / 멱등성
- HTTP의 무상태성 / 쿠키 / 세션 / 캐시
- TLS / 로드밸런싱 / 프록시
- gRPC / REST 비교
- HTTP/2 멀티플렉싱 / HOL blocking
- TCP congestion control
- Service Mesh / Sidecar Proxy
- NAT / Conntrack / Ephemeral Port Exhaustion
- Forwarded / X-Forwarded-For / X-Real-IP trust boundary
- connect/read/write timeout / healthcheck failure patterns
- HTTP/3 / QUIC / CDN Cache Key / WebSocket Heartbeat / DNS TTL
- DNS round robin 방식
- 웹 통신의 큰 흐름

[🔝 목차로 돌아가기](#table-of-contents)

## Design Pattern (디자인 패턴)

### [📖 정리노트](./contents/design-pattern)

- 디자인 패턴의 개념과 종류
- Strategy 패턴
- Decorator vs Proxy
- Observer / Pub-Sub / Application Event
- Singleton 패턴
- Factory 패턴
- Builder 패턴
- Template Method vs Strategy
- God Object / Spaghetti / Golden Hammer
- Facade / Adapter / Proxy 비교
- Factory / Abstract Factory / Builder 비교
- Composition over Inheritance
- Command Pattern / Undo / Queue
- MVC 패턴

[🔝 목차로 돌아가기](#table-of-contents)

## Software Engineering (소프트웨어 공학)

### [📖 정리노트](./contents/software-engineering)

- 프로그래밍 패러다임
  - 명령형 프로그래밍 vs 선언형 프로그래밍
  - 함수형 프로그래밍
  - 객체지향 프로그래밍
- DDD 바운디드 컨텍스트 실패 패턴
- Monolith → MSA 실패 패턴
- Event Sourcing / CQRS 도입 기준
- 기술 부채 / 리팩토링 타이밍
- Anti-Corruption Layer 통합 패턴
- Contract Testing / Modular Monolith / Feature Flag Cleanup / Idempotency Boundary
- Strangler Fig / Contract / Cutover
- Branch by Abstraction / Feature Flag / Strangler 선택 기준
- Repository / DAO / Entity / Mapper
- SOLID failure patterns
- 애자일 개발 프로세스

[🔝 목차로 돌아가기](#table-of-contents)

## Spring Framework (스프링 프레임워크)

### [📖 정리노트](./contents/spring)

- IoC 컨테이너와 DI
- AOP 프록시 메커니즘
- `@Transactional` 동작 원리와 함정
- Spring MVC 요청 생명주기
- Spring Boot 자동 구성
- Spring Security 아키텍처
- Spring MVC vs WebFlux
- Bean 생명주기 / Scope 함정
- OAuth2 + JWT 통합
- Test Slice / Context Caching
- Cache Abstraction 함정 / Transaction Debugging
- Scheduler / Async / Batch / Observability / WebClient
- Resilience4j / Retry / CircuitBreaker / Bulkhead

[🔝 목차로 돌아가기](#table-of-contents)

## System Design (시스템 설계)

### [📖 정리노트](./contents/system-design)

- 시스템 설계 면접 프레임워크
- Back-of-the-envelope 추정
- URL 단축기 설계
- Rate Limiter 설계
- 분산 캐시 설계
- 채팅 시스템 설계
- 뉴스피드 시스템 설계
- 알림 시스템 설계
- Consistent Hashing / Hot Key 전략
- Multi-tenant SaaS isolation
- Payment System / Ledger / Idempotency / Reconciliation
- Distributed Lock / Search / File Storage / Workflow
- 요구사항을 숫자와 병목으로 바꾸는 사고법
- 검색 / 분산 합의 / 워크플로우 / 멀티테넌시 주제로 확장

[🔝 목차로 돌아가기](#table-of-contents)

## Security (보안)

### [📖 정리노트](./contents/security)

- 인증(Authentication)과 인가(Authorization)의 차이
- 세션 / JWT / OAuth 역할 경계
- JWT 깊이 파기
- OAuth2 Authorization Code Grant
- Service-to-Service Auth / mTLS / SPIFFE
- API Key / HMAC Signature / Replay Protection
- 비밀번호 저장 / SQL Injection / XSS / CSRF / HTTPS
- CORS / SameSite / OIDC / Secret Rotation / Session Fixation / CSP
- Spring Security와 네트워크 상태성 개념을 연결하는 보안 기초

[🔝 목차로 돌아가기](#table-of-contents)

## Language

### [📖 정리노트](./contents/language)

- Java
  - 불변 객체 / 방어적 복사
  - JVM / GC / JMM
  - Java 동시성 유틸리티
  - Virtual Threads / Project Loom
  - G1 GC / ZGC 선택
  - Reflection 비용 / MethodHandle / Codegen
  - Generic Type Erasure / JIT / OOM Heap Dump
  - Direct Buffer / Off-Heap / Native Memory
  - ClassLoader Leak / JFR-JMC / Records-Sealed / VarHandle
  - ClassLoader / Exception / equals-hashCode-compareTo
  - Java Memory Model / happens-before / volatile / final
- C++

[🔝 목차로 돌아가기](#table-of-contents)
