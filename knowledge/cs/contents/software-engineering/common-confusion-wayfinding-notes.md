# Common-Confusion Wayfinding Notes

> 한 줄 요약: `batch/헥사고날`, `영속성/JPA`, `테스트`, `계층 책임`이 섞여 보일 때는 "흐름(유스케이스)", "저장 구현", "검증 전략", "계층 경계"를 분리해 보고 첫 문서를 고르면 오독이 크게 줄어든다.

**난이도: 🟢 Beginner**

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 4칸 지도](#먼저-잡는-4칸-지도)
- [먼저 잡는 한 줄 멘탈 모델](#먼저-잡는-한-줄-멘탈-모델)
- [자주 헷갈리는 4개 케이스](#자주-헷갈리는-4개-케이스)
- [FAQ: `테스트 전략 기초`와 `Hexagonal Testing Seams Primer`는 무엇이 다른가](#faq-테스트-전략-기초와-hexagonal-testing-seams-primer는-무엇이-다른가)
- [짧은 예시: "쿠폰 만료 배치" 변경](#짧은-예시-쿠폰-만료-배치-변경)
- [같은 예시로 보는 `첫 테스트 선택 -> seam 분리`](#같은-예시로-보는-첫-테스트-선택---seam-분리)
- [before / after 한눈 비교](#before--after-한눈-비교)
- [흔한 오해와 함정](#흔한-오해와-함정)

</details>

관련 문서:

- [Software Engineering README: Common-Confusion Wayfinding Notes](./README.md#common-confusion-wayfinding-notes)
- [Controller / Service / Repository before 예시 - 주문 생성 로직이 Controller에 몰린 상태](./layered-architecture-basics.md#before-주문-생성-로직이-controller에-몰린-상태)
- [Controller / Service / Repository after 예시 - 주문 생성 흐름을 Controller Service Repository로 나눈 상태](./layered-architecture-basics.md#after-주문-생성-흐름을-controller-service-repository로-나눈-상태)
- [Service 계층 기초](./service-layer-basics.md)
- [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
- [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
- [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
- [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md)

retrieval-anchor-keywords: common confusion wayfinding notes, beginner wayfinding, 어디부터 읽어야 하나, 테스트 전략 기초 vs hexagonal testing seams primer, 첫 테스트 선택과 seam 차이, service 변경 springboottest 오해, inbound adapter test slices primer, controller service repository boundary confusion, batch hexagonal jpa test confusion, saveall 오해 다음 문서, coupon expiration first test seam, 초심자 문서 길잡이

## 먼저 잡는 한 줄 멘탈 모델

헷갈릴 때는 문서 이름보다 먼저, **"흐름(유스케이스) / 저장 구현 / 검증 전략 / 계층 경계" 중 지금 막힌 칸 하나만 고른다.**

Controller가 이미 얇은데도 "규칙은 어디에 두고 Service는 어디까지 알아야 하지?"가 흐리면, [계층형 아키텍처 기초](./layered-architecture-basics.md)와 [Service 계층 기초](./service-layer-basics.md)부터 연달아 본다.

## 먼저 잡는 4칸 지도

초심자는 먼저 "무엇이 바뀌는지"를 4칸으로 나누면 된다.

| 칸 | 질문 | 대표 문서 |
|---|---|---|
| 흐름(유스케이스) | "배치를 기존 유스케이스 loop로 돌릴까, 배치 전용 서비스로 올릴까?" | [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md) |
| 저장 구현(JPA/ORM) | "`saveAll`, `batch_size`, `flush`는 어디 책임인가?" | [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md) |
| 검증 전략(테스트) | "이번 변경의 첫 테스트 1개는 무엇으로 시작할까?" | [테스트 전략 기초](./test-strategy-basics.md) |
| 계층 경계(Controller/Service/Repository) | "입력 검증, 규칙 판단, DB 조회를 누가 가져가야 하지?" | [계층형 아키텍처 기초](./layered-architecture-basics.md) → [Service 계층 기초](./service-layer-basics.md) |

핵심은 "무조건 한 문서부터"가 아니라, **지금 막힌 질문의 칸부터** 시작하는 것이다.

## 자주 헷갈리는 4개 케이스

| 혼동 케이스 | 먼저 읽을 1개 | 바로 이어 읽을 1개 | 왜 이 순서가 안전한가 |
|---|---|---|---|
| 1) "스케줄러 배치니까 `saveAll` 포트를 먼저 만들면 되나요?" | [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md) | [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md) | 먼저 유스케이스 경계를 결정하고, 바로 다음에 `saveAll`이 진짜 batch 계약인지 단순 JPA batch 착시인지 확인해야 계약 오염을 막을 수 있다. |
| 2) "JPA batch가 느린데 이게 헥사고날 설계 문제인가요?" | [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md) | [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md) | 대부분은 adapter/설정 문제다. 경계 문제인지 확인할 때만 헥사고날 문서로 확장한다. |
| 3) "테스트를 먼저 짤지, 구조를 먼저 읽을지 모르겠어요" | [테스트 전략 기초](./test-strategy-basics.md) | [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md) | 첫 테스트 1개로 변경 위험을 고정한 뒤, seam 문서로 테스트 경계를 정교화하면 학습 부담이 작다. |
| 4) "Controller는 얇은데 Service가 너무 비대해요. 검증/조회/응답 조립을 어디까지 Service가 맡나요?" | [계층형 아키텍처 기초](./layered-architecture-basics.md) | [Service 계층 기초](./service-layer-basics.md) | 먼저 Controller/Service/Repository의 기본 경계를 잡고, 그다음 Service가 규칙 조합과 트랜잭션 orchestration까지만 맡는다는 기준을 읽어야 "얇은 Controller"를 핑계로 Service에 모든 책임을 밀어 넣는 오해를 줄일 수 있다. |

`saveAll`이라는 단어가 먼저 보였더라도, 초심자에게 첫 분기 질문은 "`묶음 자체가 일인가?`"와 "`아니면 JPA가 묶어 보내는가?`" 두 개다. 앞 질문은 [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)에서, 뒤 질문은 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)에서 바로 확인하면 된다.

계층 책임이 먼저 막히면 질문도 짧게 줄인다. "`입력을 거르는 일인가?`", "`업무 규칙을 조합하는 일인가?`", "`DB에서 찾고 저장하는 일인가?`" 세 질문만 먼저 답하면 Controller/Service/Repository 경계가 훨씬 빨리 보인다.

## FAQ: `테스트 전략 기초`와 `Hexagonal Testing Seams Primer`는 무엇이 다른가

둘 다 "테스트" 문서지만 초심자 기준 역할이 다르다. [테스트 전략 기초](./test-strategy-basics.md)는 "`지금 이 변경에서 첫 테스트 1개를 무엇으로 시작할까?`"를 고르는 입구 문서라서 단위 테스트, `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest` 중 **가장 싼 시작점**을 정하게 해 주고, [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)는 그다음 단계에서 "`이 테스트를 유스케이스 규칙 검증으로 둘지, adapter 연결 검증으로 둘지`"를 **경계(seam)** 기준으로 나눠 준다. 짧게 말해 전자는 "첫 삽을 어디에 뜰까", 후자는 "그 삽을 어느 경계까지만 팔까"에 가깝다. 만약 지금 질문이 "`Service`를 바꿨는데 왜 바로 `@SpringBootTest`가 아니지?"에 더 가깝다면 [Service 계층 기초](./service-layer-basics.md#자주-하는-오해-faq-service를-바꿨으면-무조건-springboottest-아닌가요)부터 먼저 보고, "`@WebMvcTest`나 message handler slice를 어디까지 믿어야 하지?"가 먼저 막히면 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)로 바로 이어 읽으면 첫 분기 비용이 더 작다.

## 짧은 예시: "쿠폰 만료 배치" 변경

상황: 매일 자정에 만료 쿠폰을 비활성화하는 기능을 추가한다.

1. 먼저 [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)를 보고, 이 작업이 "기존 단건 유스케이스 반복"인지 "run/chunk/checkpoint가 필요한 배치 계약"인지 결정한다.
2. 저장 성능이 걱정되면 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)에서 `flush`, ID 전략, batch 설정을 adapter 관점으로 점검한다.
3. 마지막으로 [테스트 전략 기초](./test-strategy-basics.md)에서 "첫 테스트 1개"를 고른다. 예: 상태 전이 규칙은 단위 테스트, JPA 매핑은 `@DataJpaTest`.
4. 첫 테스트를 골랐다면 바로 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)로 넘어가, 그 테스트를 "유스케이스 규칙 검증"까지만 볼지 아니면 "adapter 연결 검증"까지 볼지 seam 기준으로 나눈다.

이 순서를 따르면 "구조 선택"과 "ORM 튜닝"과 "테스트 착수"가 섞여서 뒤엉키는 상황을 줄일 수 있다.

## 같은 예시로 보는 `첫 테스트 선택 -> seam 분리`

같은 "쿠폰 만료 배치" 예시를 한 번 더 보면, 초심자가 가장 자주 헷갈리는 지점은 **테스트 종류를 고르는 일**과 **검증 경계를 자르는 일**을 한 번에 처리하려는 것이다.

먼저 생각할 질문은 하나다.

`지금 가장 먼저 깨질 위험이 규칙인가, 연결인가?`

| 순서 | 먼저 답할 질문 | 선택 | 이유 |
|---|---|---|---|
| 1. 첫 테스트 선택 | "만료 시각이 지나면 `ACTIVE -> EXPIRED`로 바뀌는가?" | `unit test` | 가장 싼 비용으로 핵심 규칙을 바로 고정할 수 있다. |
| 2. seam 분리 | "DB 조회 조건, 저장 매핑, 스케줄러 wiring도 같이 확인해야 하는가?" | 아니오면 유스케이스 seam에서 멈춤 | fake repository로 상태 전이 규칙만 검증한다. |
| 3. seam 분리 확장 | "정말 DB 쿼리/매핑이 걱정되는가?" | 예면 `@DataJpaTest` 추가 | 이때부터는 adapter seam을 별도 테스트로 분리한다. |

짧게 말하면:

- [테스트 전략 기초](./test-strategy-basics.md)는 `무엇부터 검증할지`를 고른다.
- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)는 `어디까지를 한 테스트에 넣을지`를 자른다.

처음부터 `@SpringBootTest`로 쿠폰 만료 배치 전체를 붙이면, "상태 전이 규칙이 깨진 것인지", "DB 조건이 틀린 것인지", "스케줄러 wiring이 안 맞는 것인지"가 한 번에 섞여 초심자가 원인을 읽기 어려워진다.

## before / after 한눈 비교

| 상태 | 읽기 방식 | 결과 |
|---|---|---|
| before: 문서를 주제별로 무작정 순회 | 배치/JPA/테스트 문서를 한 번에 넘나듦 | 용어만 늘고 지금 결정해야 할 질문이 흐려진다 |
| after: 막힌 질문 기준으로 1칸 선택 | 유스케이스/저장/검증/계층 경계 중 하나를 먼저 정하고 해당 primer부터 시작 | 첫 읽기 부담이 줄고 다음 문서 연결이 선명해진다 |

## 흔한 오해와 함정

- "배치"라는 단어가 나오면 곧바로 `saveAll` 포트부터 설계한다.
  - 보정: 먼저 batch가 업무 계약인지(유스케이스) 확인하고, 아니면 adapter 최적화로 제한한다.
  - 다음 문서: `saveAll`이 정말 batch 계약인지, 아니면 `batch_size`/`flush`/`IDENTITY` 같은 JPA 설정 오해인지 바로 가려면 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)를 이어서 본다.
- JPA 성능 이슈를 보면 헥사고날 구조를 전면 수정하려고 한다.
  - 보정: `batch_size`, `flush`, ID 전략은 대개 영속성 계층에서 먼저 해결한다.
- 테스트는 마지막에 한 번에 붙이면 된다고 생각한다.
  - 보정: 변경 1건마다 "가장 먼저 깨질 1개" 테스트를 선행하면 리팩터링 비용이 줄어든다.
- Controller만 얇게 만들면 자동으로 계층 분리가 끝난다고 생각한다.
  - 보정: Controller는 입력/응답 경계, Service는 규칙 조합과 트랜잭션, Repository는 조회/저장을 맡는지 따로 확인해야 한다.
  - 다음 문서: before/after 예시로 한 번에 감을 잡으려면 [계층형 아키텍처 기초](./layered-architecture-basics.md)를 먼저 보고, Service에 무엇을 남길지 더 또렷하게 잡으려면 [Service 계층 기초](./service-layer-basics.md)로 이어 읽는다.

한 줄 기준:

- 경계가 막히면 `batch/헥사고날`
- SQL/성능이 막히면 `영속성/JPA`
- 변경 안전성이 막히면 `테스트`
- Controller/Service/Repository 역할이 막히면 `계층형 아키텍처 -> Service 계층`

## 한 줄 정리

초심자는 테스트 FAQ에서 막히면 `첫 테스트 선택 -> seam 분리` 순서로 읽고, `Service 변경`이나 `slice 범위`처럼 자주 붙는 질문은 바로 연결된 primer 링크로 한 단계만 더 이동하면 된다.
