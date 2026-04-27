# API Versioning, Contract Testing, Anti-Corruption Layer


> 한 줄 요약: API Versioning, Contract Testing, Anti-Corruption Layer는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: api versioning contract testing anti corruption layer basics, api versioning contract testing anti corruption layer beginner, api versioning contract testing anti corruption layer intro, software engineering basics, beginner software engineering, 처음 배우는데 api versioning contract testing anti corruption layer, api versioning contract testing anti corruption layer 입문, api versioning contract testing anti corruption layer 기초, what is api versioning contract testing anti corruption layer, how to api versioning contract testing anti corruption layer
> 외부와 연결된 시스템이 오래 살아남기 위해 필요한 "진화 전략"을 정리한 문서

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [API 버전 관리](#api-버전-관리)
- [호환성의 기준](#호환성의-기준)
- [Contract Testing](#contract-testing)
- [Anti-Corruption Layer](#anti-corruption-layer)
- [모놀리스에서 마이크로서비스로 가는 길](#모놀리스에서-마이크로서비스로-가는-길)
- [실무에서 자주 실패하는 지점](#실무에서-자주-실패하는-지점)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

> retrieval-anchor-keywords:
> - API versioning
> - URI versioning
> - media type versioning
> - backward compatibility
> - contract testing
> - anti-corruption layer
> - ACL
> - monolith to microservice
> - 버전 관리

> 관련 문서:
> - [Software Engineering README: API Versioning, Contract Testing, Anti-Corruption Layer](./README.md#api-versioning-contract-testing-anti-corruption-layer)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)

## 왜 이 주제가 중요한가

API는 한 번 열면 끝나지 않는다.

- 클라이언트는 생각보다 느리게 업데이트된다
- 외부 시스템은 마음대로 바꿀 수 없다
- 내부 모델은 시간이 지나며 계속 변한다

즉 좋은 API는 "처음 만들기 쉬운 API"가 아니라 **오래 유지해도 덜 깨지는 API**다.

---

## API 버전 관리

버전 관리는 변경을 숨기는 기술이 아니라 **호환성 약속을 문서화하는 행위**다.

주요 방식:

- URL 경로 버전: `/v1/orders`
- 헤더 버전: `Accept: application/vnd.example.v1+json`
- 쿼리 파라미터 버전: `?version=1`

실무에서는 경로 버전을 가장 쉽게 접하지만, 중요한 것은 형식보다 정책이다.

### 언제 버전이 필요한가

- 응답 구조를 깨뜨리는 변경이 필요할 때
- 의미가 달라지는 필드가 생길 때
- 기존 클라이언트가 새 형식을 이해할 수 없을 때

### 버전을 남발하면 생기는 문제

- 코드와 테스트가 중복된다
- 오래된 버전이 기술 부채가 된다
- 어떤 버전이 "진짜"인지 모호해진다

그래서 버전은 자주 만들기보다, **호환 가능한 변경을 먼저 시도하고 정말 필요한 경우에만 분리**하는 편이 낫다.

---

## 호환성의 기준

API 변경은 크게 두 종류로 나뉜다.

- 호환 가능한 변경
- 호환 불가능한 변경

### 호환 가능한 변경

- 새 필드 추가
- 기존 필드의 의미를 깨지 않는 확장
- 새로운 엔드포인트 추가
- 응답에 optional 필드 추가

### 호환 불가능한 변경

- 필드 삭제
- 타입 변경
- 의미 변경
- 필수 필드 추가
- 에러 포맷 변경

좋은 기준은 이렇다.

- 기존 클라이언트가 무시해도 안전하면 대체로 호환 가능하다
- 기존 클라이언트가 오해하면 호환 불가능하다

즉 "컴파일이 되는가"보다 **기존 사용자가 의미를 잘못 해석하지 않는가**가 더 중요하다.

### 점진적 변경 전략

실무에서는 다음 순서를 자주 쓴다.

1. 새 필드를 먼저 추가한다
2. 클라이언트가 새 필드를 읽게 만든다
3. 충분히 전환되면 옛 필드를 deprecated 한다
4. 마지막에 제거한다

이 방식은 느리지만 안전하다.

---

## Contract Testing

Contract Testing은 제공자(provider)와 소비자(consumer) 사이의 약속이 깨지지 않았는지 검증하는 방식이다.

핵심 질문은 단순하다.

- 소비자가 기대하는 응답이 실제로 오는가?
- 제공자가 의도치 않게 응답 형식을 바꾸지 않았는가?

### 왜 필요한가

통합 테스트만으로는 분산 시스템의 모든 조합을 다 검증하기 어렵다.

- 서비스가 많아질수록 테스트 비용이 커진다
- 테스트 환경이 실제 운영과 달라질 수 있다
- 한쪽이 바뀌어도 다른 쪽에서 바로 깨지는지 늦게 알 수 있다

Contract Testing은 이런 문제를 좁혀준다.

### Consumer-driven contract

소비자가 "내가 기대하는 형식"을 계약으로 정의하고, 제공자가 그 계약을 만족하는지 확인한다.

장점:

- 실제 사용 관점에서 검증된다
- 불필요하게 넓은 통합 테스트를 줄일 수 있다
- API 변경 시 영향 범위를 빨리 찾을 수 있다

주의점:

- 계약이 너무 많아지면 유지비가 커진다
- 계약이 실제 비즈니스 규칙을 완전히 대체하지는 못한다
- 계약 테스트가 통과해도 시맨틱 문제가 남을 수 있다

즉 Contract Testing은 통합 테스트의 대체재가 아니라 **호환성 경보 장치**에 가깝다.

---

## Anti-Corruption Layer

Anti-Corruption Layer(ACL)는 외부 시스템의 모델이 내부 도메인을 오염시키지 않도록 막는 계층이다.

필요한 이유:

- 외부 API 모델은 우리 도메인 언어와 다를 수 있다
- 레거시 시스템은 이상한 필드명과 규칙을 가질 수 있다
- 외부 변경이 내부 모델로 그대로 전파되면 경계가 무너진다

ACL은 번역기 역할을 한다.

- 외부 DTO를 내부 도메인 모델로 변환한다
- 내부 도메인 개념을 외부 용어와 분리한다
- 외부 특이사항을 한 곳에 격리한다

### ACL이 없는 경우

- 서비스 전반에 외부 모델이 퍼진다
- 특정 벤더나 레거시 규칙에 종속된다
- 도메인 언어가 점점 흐려진다

### ACL이 있는 경우

- 교체가 쉬워진다
- 테스트가 쉬워진다
- 외부 의존성을 국소화할 수 있다

ACL은 비용이 들지만, 외부 시스템이 중요한 만큼 충분히 투자할 가치가 있다.

---

## 모놀리스에서 마이크로서비스로 가는 길

마이크로서비스 전환은 아키텍처 유행을 따라가는 일이 아니라 **경계와 운영 책임을 재배치하는 일**이다.

처음부터 마이크로서비스가 정답인 경우는 드물다.

- 조직이 작으면 분산의 이점보다 운영 복잡도가 크다
- 도메인 경계가 불명확하면 서비스 분리도 불명확해진다
- 데이터 분리가 어려우면 서비스는 많아져도 응집도는 낮다

그래서 실무에서는 보통 모놀리스로 시작하고, 필요한 부분만 분리한다.

### 모놀리스를 유지할 때의 장점

- 배포와 디버깅이 단순하다
- 트랜잭션 관리가 쉽다
- 개발 속도가 빠르다

### 분리가 필요한 신호

- 특정 모듈이 독립적으로 확장되어야 한다
- 팀별 배포 주기가 달라진다
- 장애의 전파 범위를 줄여야 한다
- 도메인 경계가 분명해지고 독립 운영 가치가 생긴다

### 전환 전략

- 먼저 모듈 경계를 명확히 한다
- 내부 의존성을 줄인다
- 데이터 접근을 캡슐화한다
- 이벤트나 메시지로 비동기 연결을 고려한다
- 한 번에 쪼개지 말고 경계 하나씩 분리한다

이때 ACL과 Contract Testing이 특히 중요하다.

- ACL은 외부/레거시 모델의 침투를 막는다
- Contract Testing은 분리 후에도 호환성을 지킨다

즉 마이크로서비스 전환은 "서비스를 나누는 일"이 아니라 **변경 비용을 독립화하는 일**이다.

---

## 실무에서 자주 실패하는 지점

실패는 대개 기술보다 의사결정에서 먼저 난다.

- 버전 정책 없이 임시로 버전을 만든다
- deprecated 기간을 정하지 않는다
- 계약 테스트를 일부 시나리오에만 적용한다
- ACL 없이 외부 DTO를 도메인에 그대로 흘린다
- 마이크로서비스를 먼저 만들고 경계를 나중에 찾는다

이런 문제는 코드가 아니라 **경계의 규칙이 없을 때** 생긴다.

---

## 시니어 관점 질문

- 이 변경은 기존 클라이언트를 깨는가?
- 버전 분리가 정말 필요한가, 아니면 호환 가능한 확장으로 해결 가능한가?
- 계약 테스트가 실제 리스크를 잘 커버하고 있는가?
- 외부 모델이 내부 도메인을 오염시키고 있지 않은가?
- 모놀리스를 유지하는 비용과 분리하는 비용 중 무엇이 더 큰가?

## 다음 읽기

- 다음 한 걸음: [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md) - 버전을 열어 둔 뒤 실제 소비자를 어떤 순서와 검증으로 옮길지 이어서 볼 수 있다.
- README로 돌아가기: [Software Engineering README](./README.md#api-versioning-contract-testing-anti-corruption-layer) - contract testing, ACL, migration 주변 문서를 다시 찾는 복귀 경로다.

## 한 줄 정리

API Versioning, Contract Testing, Anti-Corruption Layer는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
