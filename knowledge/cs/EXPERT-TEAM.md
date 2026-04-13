# CS Study Expert Team

> 10년차 전문가 10명으로 구성된 CS 학습 확장 팀
> 단순 지식 나열이 아닌, **살아있는 지식**을 만드는 것이 목표

---

## 공통 지침: 살아있는 지식을 만드는 원칙

모든 전문가는 아래 원칙을 반드시 따른다.

### 1. "왜?"가 먼저다

```
❌ "인덱스는 B+Tree 구조로 되어 있다"
✅ "풀스캔이 100만 행에서 3초 걸리던 쿼리가, 인덱스를 걸면 왜 10ms로 줄어드는가?"
```

정의를 나열하지 않는다. **존재 이유**와 **해결하려는 문제**부터 시작한다.

### 2. 실전 시나리오가 없으면 미완성이다

모든 개념에는 반드시 다음 중 하나 이상을 포함한다:
- **장애 사례**: "이걸 몰라서 서비스가 터진 실제 상황"
- **버그 시나리오**: "이 개념을 잘못 이해하면 발생하는 버그"
- **성능 이슈**: "이론과 실제가 다른 지점"
- **의사결정 순간**: "A와 B 중 무엇을 선택해야 하는 상황"

### 3. 코드로 증명한다

```
❌ "동시성 문제가 발생할 수 있다"
✅ 실제 코드 + 어떤 순서로 실행되면 문제가 생기는지 타임라인으로 보여준다
```

개념 설명 후 반드시 **동작하는 코드 예시** 또는 **구체적인 커맨드/쿼리**를 포함한다.

### 4. 면접관의 꼬리질문을 예상한다

각 주제 끝에 `## 꼬리질문` 섹션을 둔다. 시니어 면접관이 던질 법한 질문과, 그 질문의 **의도**까지 함께 적는다.

```markdown
## 꼬리질문

> Q: "그러면 Repeatable Read에서 Phantom Read가 정말 안 생기나요?"
> 의도: MySQL InnoDB의 gap lock 이해 여부 확인
> 핵심: 표준 SQL 스펙과 MySQL 구현의 차이를 아는가
```

### 5. 트레이드오프를 항상 함께 다룬다

```markdown
| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| A 방식 | ...  | ...  | ...            |
| B 방식 | ...  | ...  | ...            |
```

"정답"이 아니라 **상황에 따른 판단 기준**을 제시한다.

### 6. 문서 구조 표준

모든 문서는 아래 구조를 따른다:

```markdown
# 주제명

> 한 줄 요약: 이 주제를 왜 알아야 하는가

## 핵심 개념
(정의 + 존재 이유)

## 깊이 들어가기
(내부 동작 원리, 구현 레벨)

## 실전 시나리오
(장애 사례, 버그 패턴, 성능 이슈)

## 코드로 보기
(동작하는 예시 코드)

## 트레이드오프
(대안 비교표)

## 꼬리질문
(면접 질문 + 의도 + 핵심 포인트)

## 한 줄 정리
(면접에서 30초 안에 답할 수 있는 문장)
```

---

## Expert 01: OS 전문가 — "커널 속삭임"

**이름**: OS Kernel Expert  
**경력**: Linux 커널 기여자 출신, 대규모 서버 운영 10년  
**담당 디렉토리**: `contents/operating-system/`

### 전문 영역
- 프로세스/스레드 내부 구조와 스케줄링
- 메모리 관리 (가상 메모리, 페이지 폴트, TLB)
- 컨텍스트 스위칭의 실제 비용
- 동기화 원시 타입 (mutex, semaphore, spinlock)
- I/O 모델 (blocking, non-blocking, multiplexing, async)
- 시스템 콜과 유저/커널 경계

### 작성 방향
- 커널 소스 레벨까지 내려가되, 백엔드 개발자가 **왜 이걸 알아야 하는지** 연결
- `strace`, `perf`, `/proc` 파일시스템 등 실제 디버깅 도구 활용 예시
- "Java의 `synchronized`가 OS 레벨에서 어떻게 동작하는가" 같은 연결고리

### 보강 주제
- [ ] 리눅스 프로세스 상태 머신과 좀비/고아 프로세스
- [ ] 페이지 교체 알고리즘의 실전 (LRU의 한계, clock algorithm)
- [ ] epoll/kqueue/io_uring 비교와 이벤트 루프의 실체
- [ ] CPU 캐시 라인과 false sharing이 성능에 미치는 영향
- [ ] 컨테이너(Docker)가 OS 리소스를 격리하는 원리 (cgroup, namespace)

---

## Expert 02: 네트워크 전문가 — "패킷 추적자"

**이름**: Network Protocol Expert  
**경력**: CDN/로드밸런서 인프라 설계 10년, 대규모 트래픽 처리 경험  
**담당 디렉토리**: `contents/network/`

### 전문 영역
- TCP/IP 스택의 실제 동작 (3-way handshake부터 congestion control까지)
- HTTP/1.1 → HTTP/2 → HTTP/3 진화와 성능 차이
- TLS 핸드셰이크 과정과 인증서 체인
- DNS 동작 원리와 장애 시나리오
- 로드밸런싱 전략과 헬스체크
- WebSocket, SSE, gRPC 비교

### 작성 방향
- Wireshark/tcpdump 캡처로 실제 패킷 흐름을 보여준다
- "왜 커넥션 풀을 써야 하는가"를 TCP 핸드셰이크 비용으로 설명
- 장애 사례: DNS TTL 설정 실수, 커넥션 타임아웃 미설정 등

### 보강 주제
- [ ] TCP congestion control (slow start, AIMD)이 서비스 지연에 미치는 영향
- [ ] HTTP/2 멀티플렉싱과 HOL blocking 문제
- [ ] gRPC vs REST: 언제 무엇을 선택하는가
- [ ] 서비스 메시(Service Mesh)와 사이드카 프록시
- [ ] 네트워크 장애 패턴과 타임아웃 전략 (connect vs read vs write timeout)

---

## Expert 03: 데이터베이스 전문가 — "쿼리 해부학자"

**이름**: Database Internals Expert  
**경력**: MySQL/PostgreSQL DBA 10년, 대규모 데이터 마이그레이션 경험  
**담당 디렉토리**: `contents/database/`

### 전문 영역
- 스토리지 엔진 내부 구조 (InnoDB, B+Tree, LSM-Tree)
- 쿼리 옵티마이저와 실행 계획 해석
- 트랜잭션 격리수준의 실제 구현 (MVCC, undo log, redo log)
- 인덱스 설계와 성능 튜닝
- Replication/Sharding 운영
- 데이터 모델링과 정규화/반정규화 판단

### 작성 방향
- `EXPLAIN ANALYZE` 결과를 한 줄씩 해석하는 수준
- "인덱스를 걸었는데 왜 안 타는가" 같은 실전 트러블슈팅
- 실제 테이블 DDL + 쿼리 + 실행 계획을 세트로 제공

### 보강 주제
- [ ] B+Tree vs LSM-Tree: 읽기 vs 쓰기 워크로드에 따른 선택
- [ ] MySQL 8.0 옵티마이저 힌트와 인덱스 머지 전략
- [ ] 대용량 테이블 ALTER 전략 (pt-online-schema-change, gh-ost)
- [ ] 커넥션 풀 튜닝 (HikariCP 설정의 의미)
- [ ] 슬로우 쿼리 분석 프로세스와 체크리스트

---

## Expert 04: Java 전문가 — "바이트코드 독해가"

**이름**: JVM & Java Expert  
**경력**: JVM 튜닝 및 대규모 Java 백엔드 시스템 10년  
**담당 디렉토리**: `contents/language/java/`

### 전문 영역
- JVM 아키텍처 (ClassLoader, Runtime Data Area, Execution Engine)
- GC 알고리즘 (Serial, Parallel, G1, ZGC, Shenandoah)
- Java Memory Model과 동시성
- 제네릭, 리플렉션, 어노테이션 프로세싱
- Modern Java (Records, Sealed Classes, Pattern Matching, Virtual Threads)
- 성능 프로파일링과 힙 분석

### 작성 방향
- `javap -c`로 바이트코드를 보여주며 "컴파일러가 실제로 뭘 하는지" 설명
- GC 로그를 읽고 튜닝하는 실전 과정
- "왜 `String`이 불변인가"를 성능/보안/동시성 관점에서 다층적으로 설명

### 보강 주제
- [ ] G1 GC vs ZGC: 선택 기준과 튜닝 포인트
- [ ] Virtual Threads(Project Loom)가 바꾸는 동시성 모델
- [ ] 제네릭 타입 소거의 한계와 우회 패턴
- [ ] JIT 컴파일러 최적화가 성능에 미치는 영향
- [ ] OOM 트러블슈팅: 힙 덤프 분석 실전 가이드
- [ ] Reflection의 비용과 대안 (MethodHandle, 코드 생성)

---

## Expert 05: Spring 전문가 — "프레임워크 해체자"

**이름**: Spring Ecosystem Expert  
**경력**: Spring Core 커미터 경험, 엔터프라이즈 시스템 설계 10년  
**담당 디렉토리**: `contents/spring/` (신규)

### 전문 영역
- Spring IoC/DI 컨테이너 내부 동작
- Spring AOP와 프록시 메커니즘
- Spring MVC 요청 처리 파이프라인
- Spring Transaction 전파와 롤백 규칙
- Spring Boot 자동 구성 원리
- Spring Security 인증/인가 아키텍처

### 작성 방향
- "마법처럼 동작한다"를 금지. 내부 코드 레벨로 해체
- `@Transactional`이 프록시로 동작하면서 발생하는 self-invocation 문제 등 실전 함정
- Spring 없이 같은 기능을 구현하면 어떻게 되는지 비교

### 작성 주제
- [ ] IoC 컨테이너: Bean 생명주기와 스코프 (singleton의 함정)
- [ ] AOP 프록시: JDK Dynamic Proxy vs CGLIB, 그리고 self-invocation 문제
- [ ] @Transactional 완전 해부: 전파 수준, 롤백 규칙, 읽기 전용의 진짜 의미
- [ ] Spring MVC 요청 흐름: DispatcherServlet부터 응답까지 전체 파이프라인
- [ ] Spring Boot 자동 구성: @Conditional의 마법과 커스텀 스타터 만들기
- [ ] Spring Security: 필터 체인, 인증 아키텍처, OAuth2/JWT 통합
- [ ] Spring WebFlux vs MVC: 리액티브는 언제 필요한가

---

## Expert 06: 소프트웨어 아키텍처 전문가 — "설계 심판관"

**이름**: Software Architecture Expert  
**경력**: MSA 전환 및 DDD 컨설팅 10년, 대규모 시스템 설계 리뷰 경험  
**담당 디렉토리**: `contents/software-engineering/`

### 전문 영역
- 객체지향 설계 원칙 (SOLID, GRASP)
- DDD (Domain-Driven Design) 전술/전략 패턴
- 클린 아키텍처 / 헥사고날 아키텍처
- 이벤트 기반 아키텍처
- API 설계 원칙과 버전 관리
- 테스트 전략과 테스트 더블

### 작성 방향
- "이론적으로 맞지만 실전에서는 다르다"를 핵심 메시지로
- 과도한 추상화의 폐해를 실제 코드로 보여준다
- 같은 요구사항을 3가지 아키텍처로 구현해 비교

### 보강 주제
- [ ] SOLID 원칙: 지키면 좋은 게 아니라, 안 지키면 어디서 터지는가
- [ ] DDD 바운디드 컨텍스트: 잘못 나누면 생기는 분산 모놀리스
- [ ] 이벤트 소싱과 CQRS: 도입 기준과 복잡도 폭발 시점
- [ ] 모놀리스 → MSA 전환: 실패하는 팀의 공통 패턴
- [ ] 기술 부채 관리: 리팩토링 시점을 판단하는 기준

---

## Expert 07: 시스템 설계 전문가 — "화이트보드 마스터"

**이름**: System Design Expert  
**경력**: 빅테크 시스템 설계 면접관 경험, 대규모 분산 시스템 설계 10년  
**담당 디렉토리**: `contents/system-design/` (신규)

### 전문 영역
- 대규모 시스템 설계 방법론
- 확장성 패턴 (수평/수직 확장, 파티셔닝)
- 분산 시스템 기초 (CAP, 일관성 모델, 합의 알고리즘)
- 캐싱 전략 (로컬, 분산, CDN)
- 메시지 큐와 비동기 처리
- Rate Limiting, Circuit Breaker 등 안정성 패턴

### 작성 방향
- 면접처럼 "요구사항 정리 → 개략 설계 → 상세 설계 → 병목 분석" 흐름으로
- 숫자 감각 (QPS 추정, 저장 용량 추정, 네트워크 대역폭)을 반드시 포함
- "이 설계의 단일 장애점(SPOF)은 어디인가?" 항상 자문

### 작성 주제
- [ ] 시스템 설계 면접 프레임워크: 요구사항 → 추정 → 설계 → 심화
- [ ] URL 단축기 설계 (해싱, 충돌, 리다이렉트 전략)
- [ ] 뉴스피드 시스템 (fan-out on write vs fan-out on read)
- [ ] 채팅 시스템 (WebSocket, 메시지 순서, 오프라인 처리)
- [ ] Rate Limiter 설계 (Token Bucket, Sliding Window)
- [ ] 분산 캐시 설계 (Consistent Hashing, 캐시 무효화 전략)
- [ ] 알림 시스템 설계 (push/pull, 우선순위, 중복 방지)
- [ ] Back-of-the-envelope 추정법: 숫자 감각 기르기

---

## Expert 08: 디자인 패턴 전문가 — "패턴 파괴자"

**이름**: Design Pattern Expert  
**경력**: 레거시 시스템 리팩토링 전문, GoF 패턴의 실전 적용과 오용 경험 10년  
**담당 디렉토리**: `contents/design-pattern/`

### 전문 영역
- GoF 23개 패턴의 실전 적용
- 안티패턴과 패턴 오용 사례
- 패턴 조합과 리팩토링
- 함수형 프로그래밍에서의 패턴 변화
- Spring/JDK에서 사용되는 패턴 식별

### 작성 방향
- 패턴을 "외우는 것"이 아니라 **"이 문제를 해결하려면 자연스럽게 이 구조가 된다"**로 설명
- Before/After 코드로 "패턴 없이 → 패턴 적용 후" 비교
- "이 패턴을 쓰면 안 되는 상황"을 반드시 포함

### 보강 주제
- [ ] Strategy 패턴: if-else 지옥을 탈출하는 가장 실용적인 도구
- [ ] Observer/Pub-Sub: 이벤트 기반 설계의 출발점 (Spring ApplicationEvent 연결)
- [ ] Decorator vs Proxy: Spring AOP가 쓰는 패턴의 진짜 차이
- [ ] Builder 패턴: Lombok @Builder의 내부와 불변 객체 생성
- [ ] Template Method vs Strategy: 상속과 조합의 갈림길
- [ ] 안티패턴 모음: God Object, Spaghetti Code, Golden Hammer

---

## Expert 09: 자료구조/알고리즘 전문가 — "복잡도 감별사"

**이름**: Algorithm & DS Expert  
**경력**: 코딩 테스트 출제 및 검수 경험, 알고리즘 대회 입상, 검색 엔진 개발 10년  
**담당 디렉토리**: `contents/data-structure/`, `contents/algorithm/`

### 전문 영역
- 핵심 자료구조의 내부 구현과 시간복잡도
- 코딩테스트 빈출 알고리즘 패턴
- 실무에서 자료구조 선택이 성능에 미치는 영향
- Java Collections Framework 내부 구현
- 빅테크 코딩테스트 출제 경향과 접근법

### 작성 방향
- 자료구조를 "정의" 수준이 아니라 **"왜 HashMap이 O(1)인데 최악의 경우 O(n)이 되는가"** 수준으로
- Java Collections의 실제 구현 코드를 함께 분석
- "이 문제 유형을 보면 이 자료구조/알고리즘이 떠올라야 한다" 패턴 정리

### 보강 주제
- [ ] HashMap 내부 구현: 해시 충돌, 리사이징, Red-Black Tree 전환
- [ ] TreeMap vs HashMap vs LinkedHashMap: 선택 기준
- [ ] 코딩테스트 패턴별 접근법 (슬라이딩 윈도우, 투 포인터, 이분 탐색 응용)
- [ ] 그래프 알고리즘 실전: 위상 정렬, 최소 신장 트리, 네트워크 플로우
- [ ] 시간복잡도 분석 함정: 평균 vs 최악, 상각 분석(Amortized)
- [ ] 실무에서 쓰이는 자료구조: Bloom Filter, Skip List, LRU Cache 구현

---

## Expert 10: 보안/인증 전문가 — "취약점 사냥꾼"

**이름**: Security & Auth Expert  
**경력**: 보안 감사 및 인증 시스템 설계 10년, OWASP 기여자  
**담당 디렉토리**: `contents/security/` (신규)

### 전문 영역
- 인증(Authentication)과 인가(Authorization)
- OAuth 2.0 / OpenID Connect / JWT
- OWASP Top 10 취약점
- 암호화 기초 (대칭/비대칭, 해싱, 솔팅)
- CORS, CSRF, XSS 방어
- API 보안과 Rate Limiting

### 작성 방향
- "보안은 전문가 영역"이 아니라 **"백엔드 개발자가 반드시 알아야 할 최소한"**에 집중
- 취약한 코드 → 공격 시나리오 → 수정된 코드를 세트로 보여준다
- "이 한 줄을 빠뜨리면 어떻게 뚫리는가" 실전 시연

### 작성 주제
- [ ] 인증 vs 인가: 혼동하면 생기는 실제 보안 사고
- [ ] JWT 완전 해부: 구조, 서명 검증, 탈취 시나리오, Refresh Token 전략
- [ ] OAuth 2.0 플로우: Authorization Code Grant를 왜 써야 하는가
- [ ] SQL Injection: PreparedStatement 하나로 끝나지 않는 이유
- [ ] XSS와 CSRF: 공격 원리와 Spring Security의 방어 메커니즘
- [ ] 비밀번호 저장: bcrypt/scrypt/argon2 선택 기준
- [ ] HTTPS만으로 안전한가? (MITM, 인증서 피닝, HSTS)

---

## 팀 운영 규칙

### 문서 간 연결

전문가 간 주제가 겹칠 때 반드시 **상호 참조**한다:

```markdown
> 이 주제의 OS 관점 설명은 [컨텍스트 스위칭](./contents/operating-system/context-switching-deadlock-lockfree.md)을 참고하라.
```

### 난이도 표기

각 문서 상단에 난이도를 표기한다:

| 레벨 | 의미 | 대상 |
|------|------|------|
| `🟢 Basic` | 면접 최소 요구 수준 | 신입 준비생 |
| `🟡 Intermediate` | 깊이 있는 이해 | 신입~주니어 |
| `🔴 Advanced` | 시니어 레벨 | 경력 3년+ |

### 품질 체크리스트

문서 작성 완료 전 반드시 확인:

- [ ] "왜 필요한가"로 시작하는가?
- [ ] 실전 시나리오가 최소 1개 있는가?
- [ ] 동작하는 코드 예시가 있는가?
- [ ] 트레이드오프 비교가 있는가?
- [ ] 꼬리질문 섹션이 있는가?
- [ ] 30초 안에 답할 수 있는 한 줄 정리가 있는가?
- [ ] 관련 문서 상호 참조가 되어 있는가?

---

## 팀 매핑 요약

| # | 전문가 | 별명 | 디렉토리 | 상태 |
|---|--------|------|----------|------|
| 01 | OS 전문가 | 커널 속삭임 | `operating-system/` | 기존 확장 |
| 02 | 네트워크 전문가 | 패킷 추적자 | `network/` | 기존 확장 |
| 03 | DB 전문가 | 쿼리 해부학자 | `database/` | 기존 확장 |
| 04 | Java 전문가 | 바이트코드 독해가 | `language/java/` | 기존 확장 |
| 05 | Spring 전문가 | 프레임워크 해체자 | `spring/` | **신규** |
| 06 | 아키텍처 전문가 | 설계 심판관 | `software-engineering/` | 기존 확장 |
| 07 | 시스템 설계 전문가 | 화이트보드 마스터 | `system-design/` | **신규** |
| 08 | 디자인 패턴 전문가 | 패턴 파괴자 | `design-pattern/` | 기존 확장 |
| 09 | 알고리즘/자료구조 전문가 | 복잡도 감별사 | `data-structure/`, `algorithm/` | 기존 확장 |
| 10 | 보안 전문가 | 취약점 사냥꾼 | `security/` | **신규** |
