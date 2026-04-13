# Senior-Level CS Questions

> 10년 차 시니어 개발자가 신입/주니어에게 던질 법한 질문을 기준으로 정리한 심화 질문 모음

## 이 문서를 어떻게 써야 하나

각 질문은 단순 암기 확인용이 아니다.  
아래 4가지를 동시에 답할 수 있어야 한다.

1. 정의
2. 왜 그런 선택을 하는지
3. 대안과 트레이드오프
4. 장애/실패 시나리오

즉 “정답 맞히기”보다 **설계와 운영 관점으로 설명하기**가 목표다.

---

## Database

### JDBC / JPA / MyBatis

- JDBC를 직접 쓰는 구조와 JPA를 쓰는 구조는 유지보수 비용이 어떻게 달라지는가?
- JPA를 도입했을 때 생산성은 올라가는데도, 왜 어떤 팀은 여전히 MyBatis를 선호하는가?
- SQL을 직접 통제하는 것과 객체 중심 추상화 사이에서 언제 균형이 깨지는가?
- ORM이 도메인 모델링을 더 잘하게 만드는가, 아니면 오히려 DB 구조에 맞춘 모델을 만들게 하는가?

### Transaction / Isolation / Lock

- Read Committed와 Repeatable Read의 차이를 단순 정의 말고 실제 버그 사례로 설명할 수 있는가?
- 비관적 락을 도입하면 정합성은 올라가지만 어떤 비용을 지불하는가?
- 낙관적 락 재시도를 애플리케이션 레벨에서 처리할지, 사용자에게 실패를 돌려줄지 어떻게 결정하는가?
- 트랜잭션 범위를 넓게 잡으면 어떤 문제가 생기고, 너무 좁게 잡으면 어떤 문제가 생기는가?

### Index / Explain

- 인덱스를 추가해서 빨라졌다고 말하려면 무엇을 근거로 제시해야 하는가?
- “인덱스를 걸었는데도 느리다”를 어떤 순서로 진단할 것인가?
- 복합 인덱스의 컬럼 순서를 왜 그렇게 잡았는지 설명할 수 있는가?
- covering index가 성능을 높이는 이유를 디스크 접근 관점에서 설명할 수 있는가?

### MVCC / Replication / Sharding

- MVCC가 읽기 성능에는 유리한데도 write-heavy 환경에서는 어떤 비용이 생기는가?
- primary/replica 구조에서 “방금 쓴 데이터를 바로 읽어야 하는” 요구사항은 어떻게 처리할 수 있는가?
- sharding key를 잘못 잡으면 어떤 운영 문제가 생기는가?
- replication은 가용성 전략이고 sharding은 확장 전략인데, 둘을 함께 쓸 때 사고방식이 어떻게 달라져야 하는가?

### Storage Engine / Write Path

- B+Tree와 LSM-Tree를 읽기/쓰기 워크로드 관점에서 어떻게 비교할 것인가?
- compaction이 write 성능을 높이는 대신 어떤 지연 비용을 만드는가?
- range scan이 중요한 서비스에서 LSM 계열 저장소를 고를 때 어떤 점을 먼저 의심해야 하는가?
- 대용량 테이블의 온라인 스키마 변경에서 “DDL이 끝났지만 서비스는 죽었다”가 왜 가능한가?
- 슬로우 쿼리 분석을 할 때 실행 계획만 보고 결론 내리면 어떤 실수를 하기 쉬운가?
- replica lag와 read-after-write 문제를 애플리케이션에서 어떻게 완화할 것인가?
- Debezium / binlog tailing / outbox를 각각 언제 선택할 것인가?
- offset pagination과 seek pagination의 차이를 성능과 UX 모두로 설명할 수 있는가?
- write skew와 phantom read를 실제 비즈니스 버그로 설명할 수 있는가?
- optimizer hint와 index merge를 언제 “튜닝”으로 보고 언제 “모델링 실패의 신호”로 봐야 하는가?
- HikariCP 같은 커넥션 풀 설정을 건드릴 때 DB 병목과 애플리케이션 병목을 어떻게 구분할 것인가?
- 정규화와 반정규화 중 무엇이 맞는지는 성능이 아니라 어떤 변경 비용 기준으로 판단해야 하는가?
- redo log, undo log, checkpoint, crash recovery를 커밋 지연과 복구 시간 관점에서 설명할 수 있는가?
- `innodb_flush_log_at_trx_commit`, `sync_binlog`, doublewrite 조정이 왜 단순 성능 튜닝이 아니라 durability 정책 결정인가?
- `Using index condition`, `Using filesort`, `Using temporary`가 EXPLAIN에 같이 뜰 때 어떤 순서로 해석하고 어디부터 줄일 것인가?

---

## Network

### HTTP / REST / Idempotency

- `POST`를 멱등적으로 만들고 싶다면 어떤 전략을 쓸 수 있는가?
- REST를 “URL 예쁘게 짓는 규칙”이 아니라 시스템 설계 원칙으로 설명할 수 있는가?
- 멱등성이 서버 상태 기준인지, 응답 결과 기준인지 구분해서 설명할 수 있는가?
- 클라이언트 재시도를 허용하려면 API 설계에서 무엇을 먼저 정해야 하는가?

### Cookie / Session / Cache

- 세션을 서버 메모리에 둘 때와 외부 저장소에 둘 때 운영상 차이는 무엇인가?
- JWT는 왜 stateless 인증이라고 불리지만, 실제 서비스에서는 완전한 stateless가 어려운가?
- HTTP 캐시와 애플리케이션 캐시를 혼동하면 어떤 문제가 생기는가?
- 개인화된 응답을 캐싱할 때 어떤 사고가 발생할 수 있는가?

### TLS / Proxy / Load Balancing

- TLS termination을 로드밸런서에서 할지 애플리케이션 서버에서 할지 어떻게 결정하는가?
- L4와 L7 로드밸런싱 차이를 단순 정의가 아니라 실제 운영 포인트로 설명할 수 있는가?
- reverse proxy가 단순 전달자 이상으로 어떤 역할을 하는가?
- 장애 상황에서 로드밸런서 헬스체크가 부정확하면 어떤 일이 생기는가?

### gRPC / HTTP2 / API Protocol

- REST 대신 gRPC를 선택하면 어떤 계층의 복잡도를 줄이고 어떤 계층의 복잡도를 새로 떠안게 되는가?
- 브라우저 클라이언트가 포함된 환경에서 gRPC가 애매해지는 이유는 무엇인가?
- streaming이 가능하다는 이유만으로 gRPC를 선택하면 어떤 운영/관측성 비용을 놓치기 쉬운가?

### TCP / Mesh / Proxy

- 혼잡 제어가 애플리케이션 p99 지연 시간에 영향을 주는 경로를 설명할 수 있는가?
- service mesh를 도입하면 개발팀이 얻는 표준화와 운영팀이 떠안는 복잡도는 각각 무엇인가?
- sidecar proxy가 장애 원인이 되었을 때 애플리케이션 코드와 어떻게 분리해서 진단할 것인가?
- HTTP/3 / QUIC를 도입할 때 얻는 장점보다 잃는 운영 단순성은 무엇인가?
- CDN cache key를 잘못 잡으면 개인화 응답과 정적 캐시가 어떻게 섞여 사고가 나는가?
- WebSocket heartbeat와 reconnect 정책을 잘못 잡으면 어떤 종류의 증폭 장애가 생기는가?
- DNS TTL이 너무 길거나 짧을 때 각각 어떤 운영 문제가 생기는가?
- HTTP/2 멀티플렉싱이 있어도 HOL blocking 문제가 완전히 사라지지 않는 이유는 무엇인가?
- connect timeout, read timeout, write timeout을 하나로 묶어 말하면 왜 장애 대응이 틀어지는가?
- 로드밸런서 healthcheck가 너무 엄격하거나 느슨할 때 각각 어떤 장애가 생기는가?
- NAT gateway 뒤에서 outbound 연결이 많을 때 conntrack table 포화와 ephemeral port exhaustion을 어떻게 구분하고 진단할 것인가?
- keep-alive가 왜 성능 최적화일 뿐 아니라 port churn과 TIME_WAIT 완화 전략이 되는가?
- `Forwarded`, `X-Forwarded-For`, `X-Real-IP`를 모두 남기는 환경에서 어떤 hop까지만 신뢰해야 하는가?

---

## Operating System / Concurrency

### Process / Thread / Context Switching

- 멀티스레드가 항상 멀티프로세스보다 낫지 않은 이유는 무엇인가?
- 컨텍스트 스위칭 비용이 높은 이유를 CPU 캐시와 커널 개입 관점에서 설명할 수 있는가?
- blocking I/O와 non-blocking I/O를 스레드 개수 관점으로 비교하면 어떤 차이가 생기는가?
- zombie process와 orphan process를 구분하지 못하면 실제 운영에서 어떤 문제가 생기는가?
- 컨테이너 안에서 PID 1이 프로세스를 제대로 reap하지 않으면 어떤 일이 벌어지는가?
- epoll, kqueue, io_uring 중 무엇이 “더 최신”이 아니라 어떤 제약에서 유리한지 설명할 수 있는가?
- cgroup과 namespace를 모르면 컨테이너 리소스 문제를 왜 잘못 해석하게 되는가?
- false sharing이 lock contention 없이도 성능을 무너뜨릴 수 있는 이유는 무엇인가?
- futex, mutex, semaphore, spinlock을 모두 “락”으로만 설명하면 어떤 중요한 차이를 놓치게 되는가?
- page replacement 정책을 모르면 메모리 압박 상황에서 왜 CPU/디스크 문제를 헷갈리기 쉬운가?
- load average와 CPU 사용률이 다르게 보일 때 어떤 지표를 먼저 의심해야 하는가?
- page cache와 dirty writeback을 모르면 왜 디스크 병목을 애플리케이션 문제로 오해하기 쉬운가?
- signal 기반 graceful shutdown과 supervision을 모르면 프로세스 운영에서 어떤 문제가 생기는가?
- NUMA 환경에서 특정 인스턴스만 느린 이유를 어떻게 추적할 것인가?
- `strace`, `perf`, `eBPF`를 각각 언제 쓰고 어떤 질문에 답하게 하는가?
- CPU는 한가한데 off-CPU 대기가 길 때 무엇을 먼저 의심할 것인가?
- monotonic clock과 wall clock을 헷갈리면 timeout, retry scheduler, deadline propagation에서 어떤 버그가 생기는가?

### Deadlock / Starvation / Lock-free

- deadlock을 예방하는 가장 실용적인 방법은 무엇인가?
- starvation이 실무에서 발생하는 전형적인 패턴은 무엇인가?
- lock-free가 멋져 보여도 실제 프로젝트에서 함부로 적용하면 안 되는 이유는 무엇인가?
- CAS 기반 알고리즘이 왜 ABA 문제를 만들 수 있는지 설명할 수 있는가?

---

## Java

### JVM / GC / JMM

- GC가 자동 메모리 관리라는 말로 끝나면 왜 부족한가?
- stop-the-world가 실제 서비스 지연 시간에 어떤 영향을 주는가?
- JMM에서 가시성과 원자성을 혼동하면 어떤 버그가 생기는가?
- `volatile`로 해결되는 문제와 절대 해결되지 않는 문제를 구분할 수 있는가?

### Concurrency Utilities

- `ExecutorService`를 쓰는 것과 직접 `Thread`를 만드는 것의 운영상 차이는 무엇인가?
- `CompletableFuture`가 편리한데도 디버깅이 어려워지는 이유는 무엇인가?
- `ConcurrentHashMap`이 thread-safe라고 해서 복합 연산까지 안전한 것은 아닌데, 어떤 경우 문제가 되는가?

### Collections / Virtual Threads

- `HashMap`이 평균적으로 O(1)인데도 최악의 경우 왜 느려질 수 있는가?
- mutable key를 `HashMap`에 넣으면 어떤 종류의 버그가 생기는가?
- Virtual Threads가 많아도 되는 이유와, 그래도 무한정 만들면 안 되는 이유를 설명할 수 있는가?
- pinning이 발생하면 Virtual Threads의 장점이 왜 줄어드는가?
- TreeMap, HashMap, LinkedHashMap 중 무엇을 고를지 순서/정렬/성능 기준으로 설명할 수 있는가?
- GC를 G1에서 ZGC로 바꾸는 선택이 왜 단순한 “최신 GC 사용” 문제로 끝나지 않는가?
- Reflection이 느리다고 할 때 실제로 느린 비용은 어디서 나오고, 무엇으로 대체할 수 있는가?
- 제네릭 타입 소거 때문에 런타임에 무엇을 잃고, 프레임워크는 그걸 어떻게 우회하는가?
- JIT warmup과 deoptimization을 모르면 왜 “재시작 직후만 느린 서비스”를 잘못 해석하게 되는가?
- OOM이 났을 때 힙 덤프를 어떻게 읽어야 원인 객체와 누수 경로를 찾을 수 있는가?
- ClassLoader leak가 왜 재배포/테스트 환경에서 특히 잘 드러나는가?
- JFR/JMC를 써야 하는 상황과 단순 로그/메트릭만으로 충분한 상황을 구분할 수 있는가?
- records와 sealed classes는 문법 설탕인지, 설계 제약을 표현하는 도구인지 설명할 수 있는가?
- VarHandle과 Unsafe를 써야 하는 상황이 정말 존재하는가?
- heap은 괜찮은데 RSS만 오를 때 direct buffer, mmap, thread stack을 어떻게 구분할 것인가?
- Native Memory Tracking 없이 off-heap 문제를 보면 왜 잘못된 결론을 내리기 쉬운가?
- `equals`/`hashCode`/`Comparable` 계약이 HashMap, TreeMap, 정렬 로직에서 어떤 형태로 깨지는가?
- happens-before, `volatile`, `final` publication을 구분하지 못하면 어떤 visibility 버그가 생기는가?

### ClassLoader / equals / Exception

- ClassLoader의 부모 위임 모델이 왜 중요한가?
- `equals`와 `hashCode` 계약이 깨지면 어떤 버그가 발생하는가?
- 비즈니스 예외와 시스템 예외를 구분하는 기준은 무엇인가?
- 예외를 많이 만드는 것과 결과 객체로 실패를 표현하는 것 사이에서 언제 무엇을 택하는가?

---

## Spring

### IoC / AOP / Proxy

- IoC 컨테이너가 객체 생명주기를 관리한다는 말을 Bean 생성, 초기화, 프록시 생성 시점까지 내려가서 설명할 수 있는가?
- JDK Dynamic Proxy와 CGLIB 중 어떤 방식이 선택되는지, 그리고 그 차이가 디버깅과 성능에 어떤 영향을 주는가?
- self-invocation 때문에 `@Transactional`이나 `@Cacheable`이 동작하지 않는 상황을 실제 코드 구조로 설명할 수 있는가?
- singleton 빈에 상태를 두면 왜 동시성 버그가 생기는가?

### Transaction / MVC / Boot / Security

- `@Transactional(readOnly = true)`가 정말로 "쓰기 방지"라고 말할 수 있는가?
- 트랜잭션 전파 수준을 단순 암기 말고 서비스 계층 경계 설계 관점에서 설명할 수 있는가?
- Spring MVC 요청이 들어와서 컨트롤러 메서드가 호출되기까지 어떤 컴포넌트들이 개입하는가?
- Spring Boot 자동 구성이 편리한데도 운영 환경에서 명시적 설정이 필요한 순간은 언제인가?
- Spring Security 필터 체인에서 인증과 인가가 각각 어디서 수행되는지 설명할 수 있는가?
- WebFlux가 MVC보다 “더 현대적”이라서가 아니라 특정 제약에서만 유리하다는 점을 설명할 수 있는가?
- Virtual Threads 기반 MVC와 WebFlux의 차이를 thread model과 디버깅 난이도 관점에서 비교할 수 있는가?
- singleton/prototype/request scope를 잘못 섞었을 때 어떤 버그가 생기는가?
- OAuth2 로그인 결과를 서비스 자체 JWT로 바꾸는 경계에서 가장 자주 생기는 실수는 무엇인가?
- 테스트 슬라이스와 context caching을 모르면 왜 Spring 테스트가 느려지는지 설명할 수 있는가?
- `@Cacheable`이 붙어 있는데도 캐시가 안 먹는 상황을 프록시/키/TTL 관점에서 어떻게 진단할 것인가?
- 트랜잭션 디버깅 시 로그만 보고 잘못 결론 내리기 쉬운 포인트는 무엇인가?
- `@Scheduled`와 `@Async`를 같이 쓸 때 스레드 경계와 예외 처리를 어떻게 봐야 하는가?
- Spring Batch의 chunk/retry/skip 모델은 왜 트랜잭션 모델과 같이 봐야 하는가?
- Micrometer/Tracing을 붙였는데도 병목 위치가 안 보이는 상황은 왜 생기는가?
- WebClient가 RestTemplate보다 항상 낫지 않은 이유는 무엇인가?
- Resilience4j의 retry, circuit breaker, bulkhead, timeout을 어떤 순서와 전제로 조합해야 하는가?
- fallback이 있다고 해서 장애 대응이 끝난 것이 아닌 이유는 무엇인가?
- `@EventListener`, `@TransactionalEventListener`, Outbox를 각각 언제 쓰고 phase를 잘못 고르면 어떤 정합성 사고가 나는가?

---

## Software Engineering / Architecture

### Repository / DAO / Entity

- Repository와 DAO를 왜 굳이 나누는가?
- 작은 프로젝트에서 이 계층 분리가 과해지는 신호는 무엇인가?
- Entity를 도메인과 분리하지 않으면 어떤 결합이 생기는가?
- persistence 편의 때문에 도메인 객체에 getter/setter가 늘어나는 것을 어디까지 허용할 것인가?

### Design Pattern / OOP / SOLID

- “패턴을 쓴다”와 “문제를 해결한다”를 어떻게 구분할 것인가?
- 추상화가 좋은 설계인지, 단지 파일 수만 늘린 설계인지 어떻게 판단할 것인가?
- DIP를 지키려다 오히려 코드가 과도하게 복잡해지는 경우를 설명할 수 있는가?
- 상속보다 조합이 낫다는 말을 언제 반대로 생각해야 하는가?
- SOLID를 지키지 않았을 때 가장 먼저 드러나는 냄새와 운영 비용은 무엇인가?
- if-else 분기를 Strategy로 바꾸는 것이 언제는 개선이고 언제는 과설계인가?
- Decorator와 Proxy를 코드 구조만 보고 구분할 수 있는가?
- Builder가 가독성을 높이는 순간과, 오히려 객체 생성 규칙을 흐리는 순간을 구분할 수 있는가?

### DDD / MSA / Boundary

- 바운디드 컨텍스트를 잘못 자르면 왜 분산 모놀리스가 되는가?
- 모놀리스를 MSA로 나누는 시점보다 더 중요한 질문은 무엇인가?
- 팀 경계와 도메인 경계가 어긋날 때 어떤 종류의 API 지옥이 생기는가?
- Event Sourcing과 CQRS를 도입하면 얻는 것보다 잃는 것이 더 큰 팀은 어떤 특징을 가지는가?
- 기술 부채를 “나중에 갚자”로 미루는 판단과 지금 바로 리팩토링해야 하는 판단의 경계는 어디인가?
- Anti-Corruption Layer가 없는 통합이 장기적으로 어떤 도메인 오염을 만드는가?
- Consumer-driven contract testing이 없을 때 API 팀 사이에 어떤 회귀 비용이 생기는가?
- Modular monolith에서 경계 강제가 느슨하면 왜 결국 분산 전환도 더 어려워지는가?
- Feature Flag를 잘 넣는 것보다 잘 지우는 것이 중요한 이유는 무엇인가?
- retry, idempotency, consistency boundary를 한 문장으로 설명하려 하면 왜 설계가 흐려지는가?
- Strangler Fig migration에서 dual write, shadow traffic, contract testing, rollback 경로를 어떤 순서로 설계할 것인가?
- 점진 전환에서 배포와 cutover를 같은 것으로 보면 왜 위험한가?
- Branch by Abstraction, Feature Flag, Strangler Fig를 같은 점진 전환 도구로 보면 어떤 과설계/과소설계가 생기는가?

---

## System Design

### Requirements / Estimation / Scalability

- 요구사항 정리 단계에서 반드시 먼저 확인해야 하는 비기능 요구사항은 무엇인가?
- "하루 100만 요청"을 들었을 때 이를 QPS, 피크 트래픽, 저장 용량으로 어떻게 변환할 것인가?
- 캐시를 도입하면 빨라지는데도 왜 데이터 정합성 설명이 먼저 나와야 하는가?
- 단일 장애점(SPOF)을 찾을 때 어떤 순서로 컴포넌트를 의심할 것인가?

### Data / Consistency / Reliability

- fan-out on write와 fan-out on read를 뉴스피드 같은 시나리오에서 어떻게 비교할 것인가?
- URL 단축기 같은 서비스에서 키 생성 전략이 충돌, 예측 가능성, 운영 복잡도에 어떤 차이를 만드는가?
- 메시지 큐를 도입했을 때 처리량은 좋아지는데도 디버깅 난이도는 왜 올라가는가?
- eventual consistency를 허용할 수 있는 도메인과 절대 허용하면 안 되는 도메인을 어떻게 구분할 것인가?
- 분산 Rate Limiter를 만들 때 강한 일관성과 높은 가용성 중 무엇을 우선할지 어떻게 결정할 것인가?
- 분산 캐시에서 캐시 무효화와 정합성 보장 중 무엇을 먼저 기준으로 세워야 하는가?
- 채팅 시스템에서 메시지 순서 보장과 지연 시간 중 무엇을 우선할지 어떻게 판단할 것인가?
- 뉴스피드에서 fan-out on write와 fan-out on read를 혼합하는 하이브리드 전략은 언제 필요한가?
- 알림 시스템에서 push/pull, 중복 방지, 우선순위를 동시에 만족시키려면 어떤 계층 분리가 필요한가?
- consistent hashing만 넣으면 hot key 문제가 해결된다고 말하면 왜 틀린가?
- distributed lock이 정말 필요한 상황과, DB/queue/idempotency로 풀어야 하는 상황을 구분할 수 있는가?
- 검색 시스템에서 indexing freshness, ranking, shard rebalance 중 무엇이 먼저 병목이 되는가?
- presigned URL과 CDN을 같이 쓸 때 보안/캐시/비용 경계는 어떻게 달라지는가?
- workflow orchestration과 choreography를 선택할 때 장애 복구 책임이 어떻게 이동하는가?
- 멀티 테넌트 SaaS에서 shared schema, separate schema, separate database를 보안/운영/비용 관점으로 어떻게 고를 것인가?
- noisy neighbor를 DB만의 문제가 아니라 cache, queue, authz까지 포함해 설명할 수 있는가?
- payment auth/capture/refund와 ledger/reconciliation/idempotency를 하나의 정합성 모델로 설명할 수 있는가?

---

## Security

### Authentication / Authorization / Session

- 인증과 인가를 혼동하면 어떤 보안 사고가 실제로 생길 수 있는가?
- 세션 기반 인증과 JWT 기반 인증은 각각 어떤 운영 비용을 숨기고 있는가?
- OAuth2 로그인과 애플리케이션 자체 세션/JWT 발급을 같은 것으로 설명하면 왜 위험한가?
- stateless 인증이라고 해도 로그아웃, 권한 변경, 토큰 폐기 문제는 어떻게 남는가?
- JWT refresh 전략을 잘못 잡으면 어떤 탈취/재발급 문제가 생기는가?
- OAuth2 Authorization Code Grant에서 PKCE가 필요한 이유를 실제 공격 시나리오로 설명할 수 있는가?
- PreparedStatement를 써도 SQL Injection 사고가 끝나지 않는 이유는 무엇인가?
- XSS와 CSRF를 모두 “브라우저 공격”으로만 설명하면 어떤 방어 경계를 놓치게 되는가?
- bcrypt, scrypt, argon2 중 무엇을 고를지는 보안성이 아니라 어떤 운영 조건과 연결되는가?
- HTTPS를 쓰는데도 MITM이나 잘못된 신뢰 모델 문제가 남는 이유는 무엇인가?
- CORS와 SameSite를 둘 다 “브라우저 옵션”으로 보면 어떤 중요한 경계가 사라지는가?
- OIDC에서 ID Token과 UserInfo를 혼동하면 어떤 인증/인가 오류가 생기는가?
- secret rotation을 운영 절차로 보지 않으면 어떤 사고가 반복되는가?
- session fixation, clickjacking, CSP를 한 묶음으로 봐야 하는 이유는 무엇인가?
- 서비스 간 인증에서 mTLS와 JWT는 각각 무엇을 증명하며, 왜 둘 중 하나만으로 끝내기 어려운가?
- SPIFFE/SPIRE 같은 workload identity 체계가 없으면 인증서 회전과 zero-trust 운영이 왜 어려워지는가?

---

## 답변 연습 기준

각 질문에 답할 때는 아래 포맷으로 연습하면 좋아.

1. 한 줄 정의
2. 왜 중요한지
3. 실제 예시
4. 대안 비교
5. 내가 선택할 기준

예를 들어 “JDBC와 JPA 차이”를 물으면,

- 정의만 말하는 것이 아니라
- 생산성, SQL 통제, 성능 튜닝, 팀 경험치

까지 같이 얘기할 수 있어야 한다.

이 문서는 앞으로 새로운 주제를 공부할 때마다 계속 확장해도 된다.
