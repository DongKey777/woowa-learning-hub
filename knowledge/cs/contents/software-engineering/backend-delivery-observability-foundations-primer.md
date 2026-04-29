# Backend Delivery and Observability Foundations Primer

> 한 줄 요약: 백엔드 운영 입문에서는 `변경을 내보낸다 -> 조금만 연다 -> 신호를 본다 -> 이상하면 빨리 줄이거나 끈다` 흐름으로 logs, metrics, feature flag, rollout, rollback, incident response를 한 묶음으로 보는 편이 가장 덜 헷갈린다.

**난이도: 🟢 Beginner**

> 문서 역할: 이 문서는 project-stage 백엔드 작업에서 자주 같이 등장하는 delivery/observability 용어를 한 번에 묶어 주는 beginner `entrypoint primer`다. 각 주제를 깊게 파기보다, 무엇이 어떤 질문에 답하는지 먼저 분리하고 다음 문서를 고르는 입구 역할을 한다.

관련 문서:

- [Software Engineering README: Beginner 10-Minute Follow-up Branches](./README.md#beginner-10-minute-follow-up-branches)
- [캐시, 메시징, 관측성](./cache-message-observability.md)
- [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
- [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
- [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [System Design Foundations](../system-design/system-design-foundations.md)

retrieval-anchor-keywords: backend delivery observability primer, software engineering entrypoint primer, logs vs metrics beginner, 로그랑 메트릭 뭐가 달라요, observability가 뭐예요, feature flag vs deploy, 배포와 릴리스 차이, rollout rollback beginner, rollout이 뭐예요, rollback은 언제 해요, canary가 뭐예요, incident response beginner, 장애 대응 처음 배우는데, 운영 용어 큰 그림, feature flag가 뭐예요

> 이 문서는 `로그랑 메트릭 뭐가 달라요`, `배포와 릴리스는 왜 따로 말해요`, `rollback은 언제 하고 canary는 왜 써요` 같은 첫 질문이 들어왔을 때 deep dive보다 먼저 걸리도록 만든 entrypoint primer다.

## 먼저 잡는 한 줄 멘탈 모델

용어부터 외우기보다, 변경을 내보내는 흐름을 5칸으로 본다.

| 칸 | 지금 하는 질문 | 대표 도구 | 왜 필요한가 |
|---|---|---|---|
| 1. 숨기기 | "코드는 올렸지만 아직 모두에게 보여 주고 싶지 않은가?" | feature flag | deploy와 release를 분리한다. |
| 2. 조금만 열기 | "문제가 나도 일부에서만 멈추게 할 수 있는가?" | rollout, canary, percentage release | blast radius를 줄인다. |
| 3. 보기 | "지금 괜찮은지 무엇으로 판단하는가?" | metrics, logs | 감으로 배포하지 않게 만든다. |
| 4. 줄이기/끄기 | "이상하면 가장 먼저 무엇을 되돌릴까?" | rollback, flag off, traffic reduction | 복구 시간을 줄인다. |
| 5. 배우기 | "다음엔 더 빨리 잡으려면 무엇을 바꿀까?" | incident response, runbook, alert tuning | 같은 실수를 반복하지 않게 만든다. |

핵심은 한 줄이다.

- delivery와 observability는 따로 있는 주제가 아니라, `안전하게 바꾸고 빨리 알아차리는 한 흐름`이다.

## 이런 문장으로 막히면 여기서 시작하면 된다

| 지금 떠오르는 말 | 먼저 잡을 질문 |
|---|---|
| "로그는 남기는데 배포가 안전한지는 뭘로 보지?" | logs와 metrics가 각각 어떤 판단을 맡는지 나눈다 |
| "배포만 했는데 왜 feature flag 얘기가 같이 나오지?" | deploy와 release를 분리하는 이유를 본다 |
| "이상하면 rollback만 하면 되지 않나?" | flag off, rollout 축소, rollback이 푸는 문제가 다른지 본다 |
| "incident response는 회고 문서 아닌가?" | 첫 목표가 분석보다 피해 축소라는 점을 먼저 잡는다 |

## before / after 한눈 비교

| 상태 | 운영 신호 | 결과 |
|---|---|---|
| before: 배포와 관측을 따로 배움 | deploy, flag, metric, rollback 용어를 각각 외운다 | 이상 징후가 생겨도 무엇을 먼저 줄이고 무엇을 볼지 연결이 느리다 |
| after: 한 흐름으로 묶어 읽음 | `숨기기 -> 조금만 열기 -> 보기 -> 줄이기 -> 배우기` 순서로 도구를 매칭한다 | 변경 안전장치와 복구 수단을 같은 문장으로 설명할 수 있다 |

## 용어를 가장 짧게 구분하기

| 용어 | 초심자용 한 줄 뜻 | 자주 같이 보는 것 |
|---|---|---|
| `log` | 특정 순간에 무슨 일이 있었는지 남긴 기록 | 에러 원인, 요청 ID, 예외 문맥 |
| `metric` | 상태를 숫자로 모아 본 계기판 | 에러율, p95 latency, queue lag |
| `feature flag` | 코드 배포와 기능 공개를 분리하는 스위치 | kill switch, gradual release |
| `rollout` | 변경을 한 번에 다 열지 않고 단계적으로 넓히는 과정 | canary, percentage, internal-only |
| `rollback` | 이상할 때 이전 상태로 빨리 돌아가는 행동 | 이전 버전 복귀, flag off, config revert |
| `incident response` | 장애를 길게 분석하는 문서가 아니라, 지금 피해를 줄이고 복구하는 움직임 | detect, mitigate, recover, learn |

## 같은 예시로 한 번에 보기

예시: `주문 할인 계산 개편`을 금요일 오후에 배포한다고 해 보자.

| 순간 | 초심자가 먼저 할 판단 | 가장 단순한 장치 |
|---|---|---|
| 배포 전 | 새 로직을 바로 전체 사용자에게 열어도 되는가? | 기본값 `OFF`인 feature flag |
| 첫 공개 | 전체가 아니라 일부만 먼저 볼 수 있는가? | 사내 사용자 또는 5% rollout |
| 관찰 | "정상"을 무엇으로 판단할까? | 주문 API 에러율, 결제 성공률, 할인 계산 예외 로그 |
| 이상 징후 | 무엇을 먼저 줄일까? | rollout 비율 축소 또는 flag `OFF` |
| 더 큰 문제 | 코드 자체가 잘못되었는가? | 이전 버전 rollback |

여기서 감각을 잡으면 된다.

- `logs`는 "왜 실패했는가"를 보여 준다.
- `metrics`는 "실패가 얼마나 넓게 퍼지는가"를 빨리 보여 준다.
- `feature flag`는 "코드는 둔 채 기능만 끌 수 있는가"를 결정한다.
- `rollout`은 "실패 범위를 얼마나 작게 시작하는가"를 결정한다.
- `rollback`은 "이미 넓게 퍼졌을 때 어디까지 되돌릴 수 있는가"를 결정한다.

## logs와 metrics를 따로 두는 이유

둘 다 "관측" 같아 보여서 초심자가 가장 자주 섞는 부분이다.

| 질문 | logs가 잘 답하는 것 | metrics가 잘 답하는 것 |
|---|---|---|
| 무슨 일이 있었나? | 특정 요청에서 어떤 예외가 났는지 | 전체 에러율이 얼마나 올랐는지 |
| 어디를 먼저 볼까? | `orderId`, `traceId`, exception class | API별 5xx, latency, retry count |
| 알림 기준으로 쓰기 좋은가? | 보통 직접 알림 기준으로 쓰기엔 noisy함 | threshold 기반 alert에 적합 |

짧게 외우면 아래처럼 정리하면 된다.

- logs는 `개별 사건 설명서`
- metrics는 `상태 계기판`

## feature flag와 rollout이 왜 둘 다 필요한가

둘 중 하나만 있으면 된다고 생각하기 쉽지만 질문이 다르다.

| 질문 | feature flag | rollout |
|---|---|---|
| 기능을 켤지 말지 | 강함 | 보조 |
| 누구에게 얼마나 열지 | 조건부 가능 | 핵심 역할 |
| 이상 시 즉시 끄기 | 매우 빠름 | 비율 축소로 완화 |
| 코드 버전 자체가 잘못된 경우 해결 | 약함 | 약함, 결국 rollback 필요 |

그래서 실무 감각은 보통 이렇게 잡는다.

- 기능 위험은 `flag`
- 노출 위험은 `rollout`
- 버전 위험은 `rollback`

## 이상할 때 무엇부터 줄일까

초심자가 가장 자주 막히는 지점은 "문제가 보였는데 첫 행동이 무엇인지"다.

| 지금 보이는 상황 | 먼저 시도할 것 | 이유 |
|---|---|---|
| 새 기능만 문제고 코드는 살아 있다 | `flag off` | 기능 노출만 빠르게 끊을 수 있다 |
| 일부 사용자만 이상하고 더 넓히기 불안하다 | rollout 비율 축소 | blast radius를 더 키우지 않는다 |
| 코드 버전 자체가 전반적으로 잘못됐다 | rollback | 이전 안정 버전으로 되돌아가야 한다 |

즉 `flag off`, `rollout 축소`, `rollback`은 비슷한 비상 버튼이 아니라 서로 다른 문제를 푸는 버튼이다.

## incident response를 초심자용으로 단순화하면

incident response를 거대한 운영 프로세스로 보기보다, 첫 5분 질문 세 개로 시작하면 된다.

1. 지금 사용자 영향이 커지고 있는가?
2. 가장 빠른 완화 수단이 `flag off`, `traffic reduction`, `rollback` 중 무엇인가?
3. 복구 후에는 어떤 log/metric/alert가 비어 있었는가?

초심자가 자주 놓치는 점:

- 원인을 완벽히 이해한 뒤에야 완화할 수 있다고 생각하기 쉽다.
- 하지만 incident response의 첫 목표는 `정답 찾기`보다 `피해 줄이기`다.

## 흔한 오해와 함정

- `로그가 많으면 observability가 좋다`는 말은 아니다. 검색 가능한 구조와 공통 ID가 더 중요하다.
- `metric이 정상`이어도 개별 사용자는 계속 실패할 수 있다. 그래서 sample log나 trace 문맥이 필요하다.
- `feature flag가 있으니 rollback은 필요 없다`가 아니다. 데이터 변경이나 버전 호환성 문제는 코드 rollback이 필요할 수 있다.
- `rollout`은 배포 기법 이름만이 아니라 `얼마나 작은 범위로 시작하나`의 문제다.
- `incident response`는 postmortem 문서를 쓰는 시간이 아니라, 먼저 피해를 제한하고 복구하는 시간이다.
- 테스트가 잘 있어도 rollout 없이 바로 전체 공개하면 운영 위험은 남는다. 테스트는 출시 전 confidence를 높이고, observability는 출시 후 이상 신호를 잡는다.

## 지금 막힌 문장으로 다음 문서 고르기

| 지금 머릿속 문장 | 여기서 먼저 볼 문서 | 이유 |
|---|---|---|
| "logs, metrics, traces가 아직 섞여 보인다" | [캐시, 메시징, 관측성](./cache-message-observability.md) | observability 3기둥을 가장 넓게 다시 잡아 준다. |
| "기능은 숨기고 배포하고 싶은데 용어가 헷갈린다" | [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md) | flag와 rollout을 운영 언어로 다시 분리한다. |
| "canary, rolling, blue-green 차이를 빨리 알고 싶다" | [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md) | rollout/rollback 전략을 한 표로 비교한다. |
| "장애 후 왜 팀이 recovery time을 같이 보는지 모르겠다" | [Lead Time, Change Failure, and Recovery Loop](./lead-time-change-failure-recovery-loop.md) | delivery 지표와 운영 안정성을 연결해 준다. |
| "사후 회고가 왜 다음 배포 규칙까지 바꾸는가?" | [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md) | incident 대응과 학습 루프를 연결한다. |

## 카테고리 복귀 경로

- software-engineering primer 목록으로 돌아가려면 [Software Engineering README](./README.md)
- beginner 다음 10분 분기를 다시 고르려면 [Beginner 10-Minute Follow-up Branches](./README.md#beginner-10-minute-follow-up-branches)

## 한 줄 정리

delivery와 observability를 따로 외우기보다, "조금만 열고 신호를 보고 이상하면 빨리 줄이는 흐름"으로 묶으면 초심자가 운영 용어를 훨씬 덜 헷갈린다.
