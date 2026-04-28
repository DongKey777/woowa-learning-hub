# Navigation Taxonomy

> 한 줄 요약: README와 navigator 문서에서 `survey`, `primer` / `primer bridge`, `catalog/navigator`, `deep dive`, `playbook` / `recovery`, `question bank`를 역할 기준으로 구분해 retrieval routing의 혼선을 줄인다.
 
**난이도: 🟢 Beginner**

관련 문서:

- [CS Root README](../README.md)
- [RAG Design](./README.md)
- [Topic Map](./topic-map.md)
- [Query Playbook](./query-playbook.md)
- [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
- [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
- [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
- [Master Notes](../master-notes/README.md)
- [Database README](../contents/database/README.md)
- [Network README](../contents/network/README.md)
- [Security README](../contents/security/README.md)

retrieval-anchor-keywords: navigation taxonomy, document role, survey, primer, primer bridge, catalog, deep dive, playbook, recovery, question bank, beginner route, readme labeling, 처음, 헷갈려요, what is

## 왜 필요한가

같은 `README.md` 안에 학습 순서, 입문 개념, 주제별 문서 목록, 실전 장애 문서가 함께 들어가면 읽는 사람도 RAG도 "지금 필요한 문서 역할"을 헷갈리기 쉽다.

이 문서는 파일명을 바꾸지 않고도 다음 질문에 답할 수 있게 만드는 최소 분류표다.

- 지금 필요한 게 큰 그림인가, 기초 개념인가, 문제별 진입점인가
- 단일 주제 깊이 파기인가, 여러 카테고리를 묶는 종합 정리인가
- 설명 문서가 필요한가, incident 대응 순서가 필요한가

beginner/junior 독자라면 첫 클릭 사다리는 아래 순서로 고정하면 안전하다.

`meta navigator -> survey -> category navigator -> primer -> primer bridge -> deep dive -> playbook/runbook/recovery`

카테고리 `README`에 이미 들어와 있다면 앞의 두 칸은 생략해도 된다.
그때는 `category navigator -> primer -> primer bridge -> deep dive`만 기억하면 된다.

`playbook`, `runbook`, `recovery`, `cutover`, `case study`는 useful해도 기본 entrypoint가 아니라 "증상이 생긴 뒤의 follow-up"으로 읽는다.
특히 mixed navigator에서는 section 제목에 역할이 먼저 보여야 한다.
`Beginner Entrypoints`, `Case Study Entrypoints`, `Replay and Cutover Entrypoints`, `Incident Bridge`처럼 이름만 봐도 "입문 / 사례 / 고급 전환 / 장애 대응"이 갈리면 junior reader가 advanced 문서를 첫 클릭으로 오해할 가능성이 줄어든다.

한 줄 경고도 같이 기억하면 좋다.
`advanced`, `incident`, `playbook`, `recovery`, `cutover`, `case study`, `master note`, `senior`가 제목 앞쪽에 보이면 beginner 첫 클릭 후보가 아니라 follow-up shelf일 가능성이 높다.

## 두 개의 안전 사다리

같은 저장소라도 출발 위치가 다르면 beginner-safe 기본 경로가 달라진다.

| 출발 위치 | 먼저 기억할 사다리 | 아직 미루는 것 |
|---|---|---|
| 루트 `README`, 검색 결과, category 미확정 상태 | `meta navigator -> survey -> category navigator -> primer -> primer bridge -> deep dive` | `master note`, `playbook`, `recovery`, `case study` |
| category `README` 안에서 topic을 고르는 중 | `category navigator -> primer -> primer bridge -> deep dive -> playbook/recovery` | category incident catalog를 primer처럼 읽기 |

## 처음 클릭 20초 결정표

| 질문 모양 | 먼저 고를 역할 | 안전한 첫 클릭 | 아직 미루는 것 |
|---|---|---|---|
| `처음`, `뭐예요`, `what is`, `basics` | `primer` | category `README`의 `기본 primer`, `beginner ladder` | incident `playbook`, `recovery`, cutover 설계 |
| `어디부터`, `학습 순서`, `큰 그림` | `survey` | roadmap, `추천 학습 흐름` | 단일 failure-mode deep dive |
| 증상은 있는데 원인 축이 헷갈림 | `category navigator` / `primer bridge` | symptom-first table, bridge subsection | master note, 여러 deep dive 동시 열기 |
| 이미 원인 축을 알고 있고 한 경계만 깊게 팜 | `deep dive` | 개별 topic 문서 | broad survey 재시작 |
| 실제 장애 대응 순서가 먼저 필요함 | `playbook` / `runbook` / `recovery` | incident catalog | beginner entrypoint로 오해하기 |

특히 mixed README에서는 같은 bullet 안에 `primer`와 `recovery`가 같이 있으면 순서도 역할을 말해 줘야 한다.
beginner-safe 순서는 `primer -> primer bridge -> deep dive -> playbook/recovery`다.
incident 링크를 먼저 두면 "운영 문서가 입문 문서인가?"라는 오해를 만들기 쉽다.

beginner-safe 기본 규칙은 하나만 기억하면 된다. `meta/category navigator -> survey -> primer -> primer bridge`까지는 "질문을 자르는 단계"이고, `deep dive`부터는 "한 원인을 끝까지 파는 단계"다.

mixed README를 손볼 때도 같은 규칙으로 정리하면 된다.

1. 첫 section에는 `meta navigator`, `category navigator`, `routing helper`, `survey` 중 주 역할 하나만 먼저 적는다.
2. beginner row에서는 `primer`나 `primer bridge`를 첫 링크로 두고, `deep dive` / `playbook` / `recovery`는 follow-up 위치로 내린다.
3. `advanced`, `incident`, `case study`, `cutover`, `recovery`, `master note`, `senior` 같은 표지판은 section 제목이나 bullet 앞쪽에 남겨 "첫 클릭 아님"을 숨기지 않는다.
4. `처음`, `헷갈려요`, `왜`, `what is`, `basics` query shape를 받을 beginner entrypoint와 실제 운영 절차 문서를 같은 줄에 섞었다면, beginner-safe 순서(`primer -> primer bridge -> deep dive -> playbook/recovery`)를 문장으로 다시 못 박는다.

## Mixed README shelf recipe

beginner/junior README가 길어질수록 "무엇을 먼저 클릭해야 안전한가"를 section 이름과 첫 문장에 같이 써 두는 편이 좋다.

| shelf 역할 | section에서 먼저 보여 줄 cue | beginner가 기대해야 하는 것 | 같은 줄에서 뒤로 미룰 것 |
|---|---|---|---|
| `entry shelf` | `처음`, `뭐부터`, `헷갈려요`, `basics`, `what is` | primer 1개와 다음 한 걸음 1개 | incident, runbook, recovery |
| `bridge shelf` | 증상 문구와 boundary 질문. 예: `메서드가 길어요`, `Controller가 너무 많은 걸 알아요`, `왜 서버 전체 테스트부터?` | symptom phrase를 역할 이름으로 번역 | catalog 전체 나열 |
| `deep dive shelf` | `trade-off`, `boundary`, `selection`, `why this design` | 선택지 비교와 한 경계 심화 | beginner starter 재설명 |
| `advanced follow-up shelf` | `incident`, `playbook`, `runbook`, `rollback`, `recovery`, `on-call` | 운영/장애 후속 경로 | beginner 첫 클릭 |

- mixed README에서 가장 많이 줄여야 하는 혼선은 "primer와 incident 링크를 한 줄 첫머리에 같이 두는 것"이다.
- 같은 section 안에서도 cue를 앞에 붙이면 안전하다. 예: `Beginner starter`, `Bridge after starter`, `Deep dive catalog`, `Advanced follow-up`.
- symptom phrase anchor가 있으면 retrieval도 초심자 route를 더 잘 고른다. `처음`, `헷갈려요`, `왜`, `뭐부터`, `basics`, `what is`는 primer shelf에, `incident`, `rollback`, `runbook`은 follow-up shelf에 남겨 역할을 분리한다.

## 파일명보다 역할 먼저 보기

`README.md`라는 파일명은 역할이 아니라 껍데기다.
같은 README라도 `meta navigator`, `category navigator`, `routing helper`가 서로 다를 수 있다.

| 자주 보는 파일/이름 | 먼저 붙일 역할 라벨 | 여기서 기대할 것 | 설명 본문이 필요하면 다음으로 갈 곳 |
|---|---|---|---|
| 루트 `README.md` | `meta navigator` | 저장소 전체 진입점과 역할 분기 | roadmap, 카테고리 `README`, `master note` |
| `contents/*/README.md` | `category navigator` / `catalog` | 카테고리 안에서 다음 문서 고르기 | `primer` 구간, 개별 `deep dive`, `playbook` |
| roadmap / learning path 문서 | `survey` | 학습 순서와 큰 그림 | 카테고리 `README`, 관련 `deep dive` |
| `rag/*.md` | `taxonomy` / `routing helper` | 역할 판별, 검색 라우팅, README 라벨 규칙 | 루트 `README`, 카테고리 `README`, `contents/**` |
| `SENIOR-QUESTIONS.md` | `question bank` | self-check 질문 묶음 | `primer`, `deep dive`, `master note` |

## 학습 진입 역할

| 역할 | 먼저 볼 때 | 이 저장소의 대표 예시 | 혼동하면 생기는 문제 |
|---|---|---|---|
| `survey` | "어디부터 보지?", "큰 그림을 먼저 잡고 싶다" | [JUNIOR-BACKEND-ROADMAP](../JUNIOR-BACKEND-ROADMAP.md), [ADVANCED-BACKEND-ROADMAP](../ADVANCED-BACKEND-ROADMAP.md), [Learning Paths for Retrieval](./learning-paths-for-retrieval.md) | 세부 trade-off를 바로 해결해 줄 거라고 기대하게 된다 |
| `primer` | 기본 개념 축이 약해서 깊은 문서가 아직 안 읽힐 때. cold-start로 여는 첫 문서가 필요할 때 | [시스템 설계 면접 프레임워크](../contents/system-design/system-design-framework.md), [Spring Boot 자동 구성](../contents/spring/spring-boot-autoconfiguration.md), [응용 자료 구조 개요](../contents/data-structure/applied-data-structures-overview.md) | 입문 문서를 catalog나 deep dive로 착각해 다음 링크를 놓친다 |
| `primer bridge` | primer 하나는 읽었지만, symptom 언어나 boundary 용어를 다음 `deep dive` / handoff 문서로 연결해 줄 2단계 설명이 필요할 때 | [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md), [Claim Freshness After Permission Changes](../contents/security/claim-freshness-after-permission-changes.md), [Grant Path Freshness and Stale Deny Basics](../contents/security/grant-path-freshness-stale-deny-basics.md) | first-step primer와 handoff 문서의 차이가 흐려져, 아직 기초가 없는 독자가 bridge를 너무 빨리 열거나 반대로 deep dive 직전 연결 문서를 놓친다 |

## 탐색과 심화 역할

| 역할 | 먼저 볼 때 | 이 저장소의 대표 예시 | 혼동하면 생기는 문제 |
|---|---|---|---|
| `catalog` / `navigator` | "이 주제에서 무엇을 읽어야 하지?"를 고를 때 | [CS Root README](../README.md), [Database README](../contents/database/README.md), [Network README](../contents/network/README.md), [RAG Design](./README.md) | 목록 문서에 정답 자체가 있다고 기대하게 된다 |
| `deep dive` | 특정 경계, trade-off, failure mode, 설계 결정을 파고들 때 | [Zero-Downtime Schema Migration Platform](../contents/system-design/zero-downtime-schema-migration-platform-design.md), [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md), [Timeout Budget Propagation](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) | broad survey와 구분이 흐려져 문서 난이도를 잘못 잡는다 |
| `master note` / `synthesis` | 여러 카테고리를 묶어 한 번에 설명해야 할 때 | [Latency Debugging Master Note](../master-notes/latency-debugging-master-note.md), [Consistency Boundary Master Note](../master-notes/consistency-boundary-master-note.md) | 단일 카테고리 문서를 읽어 놓고 전체 그림이 안 잡힌다고 느끼게 된다 |

## Incident 역할 표준

advanced incident 문서는 useful하지만 beginner entrypoint와 섞이면 오독이 커진다. 아래 네 라벨은 "장애가 났을 때 무엇이 먼저 필요한가"로만 고른다.

| 역할 | 먼저 볼 때 | 이 저장소의 대표 예시 | 혼동하면 생기는 문제 |
|---|---|---|---|
| `playbook` | live symptom, incident, debugging 순서가 먼저 필요할 때 | [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md), [JWT Signature Verification Failure Playbook](../contents/security/jwt-signature-verification-failure-playbook.md), [Signing Key Compromise Recovery Playbook](../contents/security/signing-key-compromise-recovery-playbook.md) | planned procedure나 rehearsal 문서까지 전부 incident triage처럼 읽게 된다 |
| `runbook` | owner가 아는 작업을 repeatable하게 수행해야 할 때 | [Key Rotation Runbook](../contents/security/key-rotation-runbook.md) | live triage와 steady-state operation의 경계가 흐려져 checkpoint와 rollback 기대치가 어긋난다 |
| `drill` | game day, failover rehearsal, readiness validation이 목적일 때 | [JWT / JWKS Outage Recovery / Failover Drills](../contents/security/jwt-jwks-outage-recovery-failover-drills.md), [Backup, Restore, Disaster Recovery Drill](../contents/system-design/backup-restore-disaster-recovery-drill-design.md) | 실제 incident 대응 문서와 연습 문서를 같은 의미로 읽게 된다 |

## Incident 분류와 follow-up 역할

incident 문서 묶음에서 분류표와 recovery 설명도 따로 구분해 둬야 advanced follow-up을 entrypoint로 오해하지 않는다.

| 역할 | 먼저 볼 때 | 이 저장소의 대표 예시 | 혼동하면 생기는 문제 |
|---|---|---|---|
| `incident matrix` | blast radius, severity, next owner/next doc를 먼저 판별해야 할 때 | [Auth Incident Triage / Blast-Radius Recovery Matrix](../contents/security/auth-incident-triage-blast-radius-recovery-matrix.md) | 분류표를 full step-by-step guide처럼 기대하게 된다 |
| `recovery` | outage/degradation recovery를 직접 다루지만 full step runbook은 아닐 때 | [JWKS Rotation Cutover Failure / Recovery](../contents/security/jwks-rotation-cutover-failure-recovery.md), [Replay Store Outage / Degradation Recovery](../contents/security/replay-store-outage-degradation-recovery.md) | playbook/runbook과 adjacent `[deep dive]` 사이 경계가 흐려진다 |
| `question bank` | 면접형 self-check나 빈틈 점검이 목적일 때 | [Senior-Level Questions](../SENIOR-QUESTIONS.md) | 질문 목록을 deep dive 본문처럼 읽다가 근거 문서 연결을 놓친다 |

## 30초 역할 판별

1. "어디부터 볼지"와 "공부 순서"가 먼저면 `survey`다.
2. "기초 개념 축"이 먼저면 `primer`다.
3. primer를 하나 읽은 뒤 "이 symptom을 어느 `deep dive`나 handoff로 넘기지?"가 먼저면 `primer bridge`다.
4. "이 주제에서 다음에 뭘 읽지"가 먼저면 `catalog / navigator`다.
5. "한 경계, trade-off, failure mode"를 끝까지 파고들고 싶으면 `deep dive`다.
6. "지금 incident 대응 순서"가 먼저면 `playbook`, "정해진 운영 절차 수행"이면 `runbook`, "연습/검증"이면 `drill`, "분류표/response ladder"가 먼저면 `incident matrix`다.
7. "질문으로 점검"이 목적이면 `question bank`다.
8. "README가 왜 이렇게 배치됐는지"가 궁금하면 `taxonomy / routing helper`다.
9. beginner/junior 독자라면 첫 클릭 후보를 `meta navigator -> survey -> category navigator -> primer -> primer bridge` 순서에서 먼저 고른다.
10. `playbook`, `runbook`, `drill`, `recovery`, incident-heavy `master note`는 "지금 장애 대응/운영 순서가 먼저 필요한가?"가 맞을 때만 entrypoint로 승격한다.

## Beginner Safe Ladder

이 표는 "지금 문서 역할이 헷갈린다"는 질문에 답하는 beginner entrypoint다.
특히 `처음`, `뭐예요`, `what is`, `헷갈려요`, `README가 왜 이렇게 많아요` 같은 검색은 advanced incident 문서보다 이 표를 먼저 타는 편이 안전하다.

| 지금 눈앞의 질문 | beginner-safe 첫 클릭 | 아직 첫 클릭으로 올리지 말 것 |
|---|---|---|
| `처음`, `뭐예요`, `what is`, `basics`, `헷갈려요` | `primer` | `deep dive`, `playbook`, `recovery` |
| `어디부터 공부하죠`, `순서가 궁금해요`, `big picture` | `survey` | incident 문서, `master note` |
| `이 증상을 어느 문서로 넘기죠`, `다음 문서가 뭐죠` | `category navigator` 또는 `primer bridge` | advanced incident catalog |
| `왜 이런 장애가 났죠`, `복구 순서가 뭐죠` | `playbook` / `recovery` / `incident matrix` | beginner primer를 incident 정답 문서처럼 기대하기 |

이 표의 목적은 catalog completeness가 아니라 entrypoint safety다. README나 navigator가 advanced incident 문서를 가지고 있더라도, beginner row에서는 먼저 `primer`나 `survey`가 눈에 들어와야 한다.

빠른 판별 문장도 같이 기억하면 좋다.

- `survey`: 큰 그림과 학습 순서를 고른다.
- `primer`: 기본 개념 축을 세운다.
- `primer bridge`: symptom phrase를 다음 본문으로 연결한다.
- `category navigator`: 카테고리 안에서 다음에 읽을 문서를 고른다.
- `deep dive`: 한 경계와 판단을 깊게 판다.
- `playbook / runbook / drill / recovery`: 장애 대응, 운영 절차, 연습, 복구 follow-up이다.

## 역할 라벨 운영 메모

한 링크 묶음에서는 이 역할 라벨을 하나만 전면에 내세우는 편이 혼선을 가장 적게 만든다.
`[primer bridge]`는 `primer` 계열 안에서 쓰는 inline route cue다. 새 top-level bucket을 하나 더 만드는 목적이 아니라, beginner route에서 "맨 처음 여는 문서"와 "그다음 deep dive로 넘기는 문서"를 구분할 때만 붙인다.
security의 login-loop row와 session-tail row처럼 인접한 beginner symptom shortcut에서도 `[catalog] -> [primer] -> [primer bridge] -> [deep dive]` 사다리를 끊지 않는 편이 안전하다. `401` / `403` / `404` response-code row도 `[primer]` auth failure response 문서에서 의미를 먼저 고정하고, browser redirect면 `[primer bridge]`, stale deny면 `[primer bridge]`, concealment / cache internals는 `[deep dive]`로 넘기는 식으로 같은 사다리를 유지하는 편이 덜 헷갈린다.
cookie shortcut row도 같은 원칙을 쓴다. `blocked Set-Cookie`처럼 저장 단계가 먼저 보이는 row는 `[primer]` `Cookie Rejection Reason Primer` -> `[primer bridge]` `Cookie Failure Three-Way Splitter`, `Application > Cookies`에는 보이는데 request `Cookie`가 비는 row는 `[primer]` `Cookie Scope Mismatch Guide` -> `[primer bridge]` `Duplicate Cookie vs Proxy Login Loop Bridge`처럼 primer 하나와 bridge 하나만 전면에 두고, duplicate cleanup / proxy scheme / Spring session persistence는 그 다음 단계에서만 드러내는 편이 beginner-safe하다.
특히 security의 `Browser / Session Coherence`처럼 같은 subsection 안에 symptom triage와 hardening / credential 설계 묶음이 나란히 있으면, hardening chain과 browser/server credential chain은 heading이 이미 catalog여도 bare link로 두지 말고 각 링크에 `[deep dive]` cue를 다시 붙이는 편이 beginner entrypoint 안전성이 높다.

## recovery badge 메모

`[recovery]`는 새 top-level role이 아니라 mixed incident catalog에서 쓰는 inline badge다. `playbook`처럼 step 순서를 전면에 두지는 않지만, outage/degradation/recovery incident를 직접 다루는 문서를 adjacent `[deep dive]`와 구분할 때 쓴다. mixed incident catalog 안의 개념 본문은 bare link로 두지 않고 `[deep dive]` cue를 붙이는 편이 가장 덜 헷갈린다.

<a id="incident-badge-vocabulary"></a>

## Incident Badge Vocabulary

README나 mixed catalog에서 inline badge를 붙일 때는 "이 문서를 여는 사람이 첫 30초 안에 무엇을 얻어야 하는가"를 기준으로 하나만 고른다.

| badge | 이 badge를 붙일 때 | 문서에서 기대하는 구조 | 이 badge를 피할 때 |
|---|---|---|---|
| `[playbook]` | 장애가 이미 발생했고, live symptom 기준으로 triage/containment/diagnosis 순서가 먼저 필요할 때 | symptom -> check -> contain -> escalate/rollback 같은 response ladder. 에러 문자열, blast-radius 확인, 우선순위 분기가 앞에 온다 | 정기 운영 절차, 사전 승인 작업, rehearsal 문서 |
| `[runbook]` | owner가 알고 있는 운영 작업을 repeatable하게 수행해야 할 때. 예: rotation, cutover, cleanup, bootstrap | preflight -> execute -> verify -> rollback/checkpoint. 입력값, 권한, verification checklist가 명확하다 | 원인 미상 incident triage, 실험/훈련 문서 |
| `[drill]` | 실제 장애 전에 failover/recovery path를 rehearsal하거나 readiness를 검증할 때 | scenario/setup -> inject/failover -> observe -> exit criteria -> retrospective. "연습"과 "검증"이 문서 목적에 드러난다 | live incident 첫 대응 가이드, 단순 self-check 질문 모음 |
| `[incident matrix]` | 먼저 분류하고 라우팅해야 할 때. 증상/영향 범위/심각도별로 next owner나 next doc를 고르는 표가 핵심일 때 | matrix, decision table, severity ladder, blast-radius map. 길게 설명하기보다 어떤 레버를 먼저 볼지 빨리 분기한다 | 긴 sequential procedure나 failure deep dive 본문 |
| `[recovery]` | incident를 직접 다루지만, dominant job이 "full step 절차"보다 recovery trade-off/failure mode 이해에 있을 때 | outage/degradation recovery case를 깊게 풀고, 관련 playbook/runbook/drill을 옆에 링크한다 | 첫 대응 순서나 운영 checklist를 전면에 내세워야 할 때 |

## Incident badge quick rule

빠른 선택 규칙:

1. "지금 장애가 났다. 첫 15분 대응이 필요하다"면 `[playbook]`이다.
2. "정해진 작업을 실수 없이 반복 수행해야 한다"면 `[runbook]`이다.
3. "실제 장애 전에 복구 절차를 연습하거나 readiness를 증명해야 한다"면 `[drill]`이다.
4. "어느 severity/owner/next doc로 갈지 먼저 골라야 한다"면 `[incident matrix]`다.
5. "장애 복구 사례를 깊게 설명하지만 step-by-step 주도 문서는 아니다"면 `[recovery]` 또는 `[deep dive]`다. mixed incident catalog에서는 개념 본문을 bare link로 남기지 않는다.

혼합형 문서라면 첫 화면에서 reader가 먼저 수행할 행동에 맞춰 badge를 고른다.
예를 들어 matrix 표가 앞에 있고 실제 절차는 linked playbook으로 넘기면 `[incident matrix]`가 맞고, 반대로 본문 대부분이 live response ladder라면 `[playbook]`이 맞다.

## 루트 README 규칙

루트 `README.md`는 모든 내용을 설명하는 본문이 아니라, 아래 역할로 갈라 보내는 라우터여야 한다.

- roadmap = `survey`
- 카테고리 `README` = `catalog/navigator`
- master notes = `synthesis`
- senior questions = `question bank`
- RAG 문서 = retrieval routing helper

루트에서 mixed shelf를 손볼 때는 순서도 고정한다.

| 루트 section 안에 같이 있으면 | beginner-safe 앞줄 | follow-up 뒤줄 |
|---|---|---|
| roadmap + primer + incident | `survey` 또는 category `README` | `deep dive`, `playbook/recovery` |
| category shortcut + master note | category `README`, `primer` | `master note` |
| taxonomy helper + incident badge 설명 | `routing helper` | incident-heavy category `README` |

## 카테고리 README 규칙

카테고리 `README.md`는 보통 이 순서를 유지하는 편이 덜 헷갈린다.

1. 빠른 탐색
2. `primer` 구간
3. `deep dive` 또는 문제 축별 `catalog`
4. cross-category bridge

한 문서가 두 역할을 겸할 수는 있지만, 빠른 탐색 블록에서는 **주 역할 하나만** 강조하는 편이 좋다.
특히 운영체제처럼 runtime topic이 길어지면 process / scheduler / memory / cgroup 같은 **scan-first bucket**을 먼저 세우고, 개별 문서명 나열은 그 아래로 내리는 편이 탐색 비용이 낮다.

beginner-first 정리에서는 한 줄 안의 역할 순서도 중요하다.

- `primer`나 `primer bridge`가 실제 첫 클릭이면, 같은 bullet에서 `master note`나 incident 문서보다 앞에 둔다.
- `master note`를 먼저 적고 뒤에서 "beginner-safe starter는 ..."라고 보정하면 junior reader가 첫 진입점을 잘못 잡기 쉽다.
- `playbook` / `recovery` / `incident matrix`는 장애 대응이나 운영 판단이 목적일 때만 첫 링크로 올리고, 그렇지 않으면 `catalog` 또는 `cross-category bridge` 뒤 follow-up으로 둔다.

## Bridge Handoff 원칙

최근 database / network / security category `README`는 `survey` -> `역할별 라우팅 요약` -> 문제 축별 `catalog` -> `cross-category bridge` 순서를 더 분명하게 드러낸다.
이때 `cross-category bridge` 구간은 deep dive 본문이 아니라, 질문이 카테고리 경계를 넘는 순간 다음 문서 묶음으로 넘기는 `category navigator`의 마지막 단계다.
특히 security처럼 incident 문서와 system-design handoff가 같이 섞이면, bullet 안에서도 `[playbook]` / `[deep dive]` / `[system design]` cue를 유지해 role shift를 숨기지 않는다.

## Database handoff 예시

- database pattern: [추천 학습 흐름](../contents/database/README.md#추천-학습-흐름-category-local-survey)으로 큰 축을 잡고 [역할별 라우팅 요약](../contents/database/README.md#역할별-라우팅-요약)에서 `survey / primer / catalog / playbook-runbook / taxonomy`를 고른 다음, [CDC / Outbox / Read Model Cutover 브리지](../contents/database/README.md#database-bridge-cdc-cutover)나 [Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority)로 진입한다. authority transfer route는 여기서 [Security README의 Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle), [System Design의 Database / Security Authority Bridge](../contents/system-design/README.md#system-design-database-security-authority-bridge), [Verification / Shadowing / Authority Bridge](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)까지 이어져야 bridge handoff parity가 맞는다.

## Network handoff 예시

- network pattern: [추천 학습 흐름](../contents/network/README.md#추천-학습-흐름-category-local-survey)과 [역할별 라우팅 요약](../contents/network/README.md#역할별-라우팅-요약)으로 진입한 뒤, [연결해서 보면 좋은 문서 (cross-category bridge)](../contents/network/README.md#연결해서-보면-좋은-문서-cross-category-bridge), [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md), [Service Discovery / Health Routing](../contents/system-design/service-discovery-health-routing-design.md)으로 spring / system-design handoff를 만든다.

## Security handoff 예시

- security pattern: [연결해서 보면 좋은 문서 (cross-category bridge)](../contents/security/README.md#연결해서-보면-좋은-문서-cross-category-bridge)에서 `[playbook]` / `[drill]` / `[incident matrix]`로 incident ladder를 먼저 열고, 이어지는 security 본문은 `[deep dive]`, system-design 쪽 handoff는 `[system design]`로 고정해 route-level 복구와 control-plane 설계를 한눈에 나눈다. system-design `README` 안의 bridge subsection이라도 handoff target이 system-design navigator라면 `[cross-category bridge]`로 되돌리지 않고 `[system design]` cue를 유지한다. 같은 bullet 안에서 security `deep dive`로 다시 돌아오면 `[deep dive]` cue를 재부착해서 later link가 앞 handoff badge를 암묵적으로 상속하지 않게 유지한다. 특히 `SCIM disable했는데 still access`, `support AOBO / break-glass transfer cleanup이 안 닫힌다`, `cleanup_confirmed`를 언제 내려야 할지 모르겠다 같은 symptom phrase를 concept label 앞에 둬야 retrieval entrypoint가 category 이름만 반복하지 않는다. beginner row에서는 delegated-access cleanup alias를 generic `revoke lag` incident wording과 분리해 둔다.

## System-Design Handoff Parity

- system-design bridge parity rule: security bridge에서 system-design bridge subsection으로 handoff될 때는 receiving subsection도 security-side badge ladder를 다시 보여 줘야 한다. `Incident / Recovery / Trust`에서 넘어온 bridge는 `[playbook] -> [drill] -> [incident matrix] -> [system design] -> [recovery]`, `Browser / Session Troubleshooting Path`와 `Session / Boundary / Replay`에서 넘어온 bridge는 `[catalog] -> [primer] -> [primer bridge] -> [deep dive] -> [recovery] -> [system design]`, authority-transfer route는 `[cross-category bridge] -> [system design] -> [system design] -> [deep dive]`를 유지하는 편이 beginner handoff 오독이 적다.
- authority-transfer route-name parity: 같은 bridge라도 security README는 `Identity / Delegation / Lifecycle`, database README는 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design README는 `Database / Security Authority Bridge` -> `Verification / Shadowing / Authority Bridge`로 이름이 갈린다. 초보자에게는 "DB row parity -> security runtime authority tail -> system-design shadow/retirement evidence"라는 한 route로 먼저 설명하고, 이 축을 손볼 때는 한 README만 rename하지 말고 metadata anchor, quick-start row, related-doc bullet에 sibling label을 같이 남겨 route-name mismatch를 retrieval layer에서 흡수해야 한다.

## 증상형 Bridge 사용 규칙

- category bridge usage: `SCIM disable했는데 still access`, `deprovision은 끝났는데 access tail remains`, `backfill is green but access tail remains` 같은 질문은 database README의 bridge subsection에서 시작해 [security README의 `Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle), [system-design README의 `Database / Security Authority Bridge`](../contents/system-design/README.md#system-design-database-security-authority-bridge), [`Verification / Shadowing / Authority Bridge`](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)까지 같은 축으로 넘긴다. `support AOBO / break-glass transfer cleanup이 안 닫힌다`, `cleanup_confirmed`를 언제 내려야 할지 모르겠다, `customer timeline closeout`과 delegated session cleanup이 같이 막힌다 같은 질문은 [security README의 `Service / Delegation Boundaries deep dive catalog`](../contents/security/README.md#service--delegation-boundaries-deep-dive-catalog)에서 시작해 [`Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle), [`Session / Boundary / Replay`](../contents/security/README.md#session--boundary--replay)까지 같은 cleanup 축으로 읽고, 실제 장애 복구가 먼저면 그때만 [`Incident / Recovery / Trust`](../contents/security/README.md#incident--recovery--trust)로 옮긴다. `499`, `broken pipe`, `proxy timeout인지 spring bug인지` 같은 질문은 network README bridge를 먼저 본다. 읽는 순서를 더 넓혀야 하면 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)으로 승격한다.

## survey와 deep dive 구분

- `survey`: 넓게 훑는다. 다음 문서를 고르기 쉽도록 만든다.
- `deep dive`: 하나의 경계나 판단을 끝까지 판다.

사례가 많더라도 목적이 "한 번에 넓게 훑기"면 survey에 가깝다.

## question bank 규칙

질문 목록은 스스로 점검하는 용도다.
설명과 근거가 필요하면 다시 `primer`, `deep dive`, `master note`로 내려가야 한다.

## README 라벨 최소 수정 규칙

파일명을 그대로 `README.md`로 두더라도, 맨 위의 라벨과 섹션 제목만 분리해도 혼선이 크게 줄어든다.

1. 첫 문장에 이 README가 `meta navigator`인지, 카테고리 `navigator`인지 먼저 적는다.
2. `빠른 탐색`에서는 링크 묶음마다 `survey`, `primer`, `primer bridge`, `catalog`, `deep dive`, `question bank` 중 하나를 붙인다.
3. incident 대응 문서가 deep dive와 섞이면 `[playbook]`, `[runbook]`, `[drill]`, `[incident matrix]`, `[recovery]` 같은 inline label을 붙인다.
각 badge의 경계는 [Incident Badge Vocabulary](#incident-badge-vocabulary)를 그대로 따른다. `[recovery]`는 outage/degradation incident를 직접 다루는 incident-oriented deep dive라는 뜻이다. cross-category bridge에서 system-design handoff까지 섞이면 `[deep dive]` / `[system design]` cue도 함께 붙여 role shift를 보이게 한다.
4. 본문 섹션 제목도 `기본 primer`, `응용 catalog`, `면접형 question bank`처럼 역할이 드러나게 쓴다.
5. 질문 모음이 있다면 "설명 본문이 아니라 self-check용"이라는 문장을 덧붙인다.

대표 예시:

- [Data Structure README](../contents/data-structure/README.md)
- [Operating System README](../contents/operating-system/README.md)
- [Spring README](../contents/spring/README.md)
- [Database README](../contents/database/README.md)
- [Security README](../contents/security/README.md)

## 자주 섞이는 조합과 최소 수정

| 자주 생기는 혼선 | 왜 헷갈리는가 | 이름 안 바꾸고 줄이는 방법 |
|---|---|---|
| 루트 `README`가 roadmap, category catalog, deep dive 추천까지 한꺼번에 말한다 | "여기서 다 읽으면 되나?"라는 기대를 만든다 | 상단에서 `meta navigator`라고 먼저 밝히고, 아래 대분류는 `catalog snapshot`이라고 한 번 더 못 박는다 |
| 루트 category snapshot heading이 전부 `정리노트`로만 반복된다 | heading만 보면 어느 링크가 category `README`인지, snapshot인지, 설명 본문인지 구분이 약해진다 | `자료구조 README (category navigator snapshot)`처럼 카테고리명 + 연결 대상 + 역할 라벨을 함께 적고, 가능하면 디렉터리 대신 `contents/*/README.md`를 직접 링크한다 |
| 루트 category snapshot이 raw topic 나열과 심화 문서를 한 덩어리로 보여 준다 | beginner가 `MST`, `Union-Find Deep Dive`, incident 문서를 첫 클릭으로 오해한다 | snapshot에서는 개별 심화 문서명보다 category `README` 안의 `primer`, `첫 분기`, `응용 catalog` anchor를 먼저 보여 주고, 심화 링크는 `deep dive follow-up`으로 한 줄 뒤로 민다 |
| 카테고리 `README`에 primer 링크와 question bank가 연속으로 붙어 있다 | 질문 목록을 설명 본문처럼 읽게 된다 | `기본 primer`, `응용 catalog`, `면접형 question bank`처럼 구간 제목을 분리한다 |
| database / network README의 bridge subsection이 deep dive 본문처럼 읽힌다 | bridge 구간이 "여기서 설명이 끝난다"는 신호로 오해된다 | subsection 이름에 `cross-category bridge`를 유지하고, 바로 아래에서 다음 카테고리 reading order와 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) handoff를 함께 적는다 |

## mixed navigator 혼선과 최소 수정

| 자주 생기는 혼선 | 왜 헷갈리는가 | 이름 안 바꾸고 줄이는 방법 |
|---|---|---|
| security 같은 mixed catalog에서 incident 대응 문서와 개념 deep dive, system-design handoff가 한 리스트에 섞여 있다 | step 문서를 찾는 사람도 개념 심화 문서를 찾는 사람도 같은 bullet 묶음에서 멈춘다 | mixed incident catalog 안의 incident 문서에는 `[playbook]`, `[runbook]`, `[drill]`, `[incident matrix]`, `[recovery]`, 나란히 놓인 개념 본문에는 `[deep dive]`, cross-category bridge 본문에는 `[deep dive]`, `[system design]` cue를 붙여 role shift를 드러낸다 |
| system-design handoff가 붙은 mixed navigator에서 beginner / case study / cutover / retirement 묶음이 나란히 보인다 | 모두 "추천 entrypoint"처럼 읽혀 advanced incident/cutover 문서가 primer 자리를 빼앗는다 | section 제목에 `Beginner Entrypoints`, `Case Study Entrypoints`, `Replay and Cutover Entrypoints`, `Retirement Route`처럼 역할을 먼저 못 박고, 첫 줄에서 "entrypoint 아님" 또는 "follow-up only"를 짧게 밝혀 둔다 |
| survey 문서가 사례가 많다는 이유로 deep dive처럼 소개된다 | 난이도와 기대 결과를 잘못 잡는다 | `넓게 훑는 survey`인지 `한 경계를 끝까지 파는 deep dive`인지 첫 문장에 적는다 |
| `RAG Design`이나 topic map이 개념 설명서처럼 읽힌다 | routing helper와 본문 근거 문서가 섞인다 | "역할 판별/라우팅용"이라고 적고, 실제 설명 문서는 category README나 deep dive로 내려 보낸다 |
| master note가 category index처럼 보인다 | synthesis 문서를 catalog로 오해해 누락된 세부 문서를 찾으려 한다 | `cross-domain synthesis`라는 표현을 붙이고, 세부 목록은 category README로 돌려보낸다 |

mixed navigator에서 junior reader를 보호하는 가장 싼 규칙은 heading만 보고도 위험도를 읽게 만드는 것이다.
`처음`, `뭐부터`, `헷갈려요`, `what is`, `basics` 같은 질문을 받는 섹션은 `Beginner`, `Primer`, `Quick Start`가 앞에 보여야 한다.
반대로 `Case Study`, `Replay`, `Cutover`, `Retirement`, `Incident`, `Recovery`는 제목만으로도 "고급 follow-up"임이 드러나야 하며, 같은 README 안에서 beginner 구간보다 먼저 배치하지 않는 편이 안전하다.

## symptom-first row badge 반복 규칙

`증상별 바로 가기`처럼 symptom-first row가 security `README` bridge subsection이나 system-design `README` / 설계 문서로 바로 점프할 때도 같은 badge를 다시 붙인다. 같은 row 안에서 security `README` subsection entrypoint는 `[catalog]` 또는 `[cross-category bridge]`, system-design anchor/문서는 `[system design]`, store outage/degradation 문서는 `[recovery]`로 반복 표기해 later handoff가 앞 링크 badge를 암묵적으로 상속하지 않게 유지한다. 예를 들어 `hidden session mismatch` row는 `[recovery]` [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md) -> `[system design]` [Auth Session Troubleshooting Bridge](../contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge) -> `[system design]` [Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md), `logout tail` row는 `[system design]` [Auth Session Troubleshooting Bridge](../contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge) -> `[system design]` [Canonical Revocation Plane Across Token Generations](../contents/system-design/canonical-revocation-plane-across-token-generations-design.md) -> `[recovery]` [Revocation Bus Regional Lag Recovery](../contents/system-design/revocation-bus-regional-lag-recovery-design.md)처럼 cue를 반복한다. beginner row라면 `이 표는 survey가 아니라 symptom-first catalog`라는 한 줄을 먼저 적고, `catalog -> primer/primer bridge -> deep dive/playbook/recovery` 순서를 짧은 안내 표로 못 박아 두면 role label 누락으로 인한 오독이 훨씬 줄어든다. mixed row의 마지막에 category `README` subsection으로 되돌아가는 링크가 있더라도 `[catalog]` badge를 다시 붙여 `deep dive` 문맥이 끝났음을 분명히 드러낸다.

## README 라벨 템플릿

복잡한 rename 없이도 상단 2~3줄만 고치면 혼선이 많이 줄어든다.

- 루트 `README`: `이 README는 저장소 전체의 meta navigator다.`
- 루트 category snapshot heading: `자료구조 README (category navigator snapshot)`처럼 카테고리명 + `README` + 역할 라벨을 같이 적고, generic `정리노트` 단독 heading은 피한다.
- 루트 category snapshot 본문: raw topic long-list를 바로 두기보다 `primer`, `primer bridge`, `catalog`, `deep dive follow-up`처럼 읽는 순서를 먼저 노출한다.
- 카테고리 `README`: `이 README는 category navigator다. primer 링크, routing summary, catalog, cross-category bridge를 묶고 필요하면 question bank를 덧붙인다.`

## mixed route 문구 템플릿

- security 같은 beginner symptom route: `[primer]`는 first-step 문서, `[primer bridge]`는 primer 다음 handoff 문서, 그 바로 뒤 심화 링크는 `[deep dive]` cue를 다시 붙인다고 짧게 못 박는다. login-loop row와 session-tail row가 나란히 있을 때도 같은 사다리(`[catalog] -> [primer] -> [primer bridge] -> [deep dive]`)를 유지한다. 예: `Login Redirect ... 입문 -> Browser 401 vs 302 Login Redirect Guide -> Spring RequestCache`, `Role Change and Session Freshness Basics -> Claim Freshness After Permission Changes -> Revocation Propagation Lag`.
- mixed incident catalog: `아래 목록에서 [playbook] / [runbook] / [drill] / [incident matrix]는 서로 다른 incident badge이고, 기준은 navigation-taxonomy의 Incident Badge Vocabulary를 따른다. [recovery]는 outage/degradation incident를 다루는 incident-oriented deep dive다. 같은 목록의 개념 본문은 bare link로 두지 말고 [deep dive] cue를 붙인다.`
- system-design bridge subsection: `security/database README에서 handoff된 role badge를 여기서도 다시 적는다. incident bridge면 [playbook] -> [drill] -> [incident matrix] -> [system design] -> [recovery], session bridge면 [catalog] -> [primer] -> [primer bridge] -> [deep dive] -> [recovery] -> [system design], authority bridge면 [cross-category bridge] -> [system design] -> [system design] -> [deep dive] 순서를 짧게 못 박는다.`
- `RAG README / taxonomy`: `이 문서는 routing helper이며, 개념 본문이 아니라 역할 판별용이다.`
- 대분류 섹션 안내: `아래 구간은 catalog snapshot이며, 설명 본문은 각 linked 문서에서 읽는다.`
- 질문 묶음 안내: `아래 구간은 self-check용 question bank이며 설명 본문이 아니다.`
- 역할 alias가 검색어로도 들어오면: [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)에 `roadmap`, `basics`, `index`, `troubleshooting`, `interview questions` 같은 표현을 같이 남긴다.

## README clarity audit checklist

README나 navigator 문서를 손볼 때는 아래 여섯 가지만 먼저 보면 혼선이 빠르게 줄어든다.

1. 첫 문장에서 문서의 **주 역할 하나**를 선언했는가 (`meta navigator`, `category navigator`, `routing helper`, `survey`, `question bank` 등).
2. `빠른 탐색` 링크 묶음마다 `survey`, `primer`, `primer bridge`, `catalog`, `deep dive`, `question bank` 중 **한 역할만** 붙였는가.
3. 루트/카테고리 `README`의 긴 목록 구간에 `catalog snapshot` 또는 `설명 본문 아님` 문장을 넣었는가.
4. 루트 category snapshot heading이 `정리노트`처럼 generic label만 반복되지 않고, `README` / `category navigator` / `survey` 같은 역할 cue를 노출하는가.
5. `master note`, `playbook`, `question bank`를 `deep dive`의 다른 이름처럼 쓰지 않았는가.
6. beginner/junior row라면 첫 safe next step이 `[primer] -> [primer bridge]` handoff를 드러내고, `[deep dive]` / `[playbook]` / `[recovery]`를 첫 링크로 올리지 않았는가.
7. 역할 이름이 검색어로도 들어올 문서라면 [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)와 맞물리게 alias를 남겼는가.
8. root/category snapshot의 `primer` bullet이 실제 beginner 문서를 가리키는가. `transaction-isolation-locking`, `failover`, `cutover`, `[playbook]`, `[runbook]`처럼 증상 대응 / 심화 냄새가 나는 링크를 primer 칸에 넣지 않았는가.
9. `Advanced Backend Roadmap`, `Master Notes`, `Senior-Level Questions`처럼 useful하지만 advanced인 구간에 `survey`, `synthesis`, `question bank` 역할과 "beginner 첫 클릭 아님"이 같이 적혀 있는가.

beginner row의 handoff cue를 따로 점검하고 싶다면 [Role-Cue Consistency Lint](./role-cue-consistency-lint.md)를 같이 본다.

## retrieval-anchor-keywords 보강 힌트

| 역할 | 같이 남기면 좋은 alias 예시 | 왜 필요한가 |
|---|---|---|
| `survey` | `roadmap`, `learning path`, `study order`, `big picture` | 넓게 훑는 문서를 deep dive로 오인하지 않게 한다 |
| `catalog` / `navigator` | `index`, `guide`, `entrypoint`, `what to read next`, `map`, `database routing summary`, `network routing summary`, `cross-category bridge`, `bridge entrypoint` | README를 설명 본문으로 착각하는 검색을 줄인다 |
| `primer` | `basics`, `intro`, `foundation`, `overview`, `first-step primer`, `starter` | 입문 문서를 catalog나 troubleshooting으로 잘못 고르지 않게 한다 |
| `primer bridge` | `follow-up primer`, `handoff primer`, `bridge primer`, `second-step primer`, `primer handoff` | beginner route에서 맨 첫 primer와 deep-dive 직전 handoff 문서를 구분하게 한다 |
| `deep dive` / `playbook` | `failure mode`, `trade-off`, `internals`, `troubleshooting`, `debugging`, `incident response`, `recovery`, `outage` | 증상 기반 검색이 본문 심화 문서로 곧바로 닿게 한다 |
| `runbook` / `drill` / `incident matrix` | `steady-state procedure`, `operations checklist`, `game day`, `rehearsal`, `failover exercise`, `severity matrix`, `blast radius matrix`, `response ladder` | incident badge가 섞인 catalog에서도 목적별 라우팅이 쉬워진다 |
| `question bank` | `interview questions`, `self-check`, `quiz` | 질문 목록과 설명 본문을 분리해 찾게 한다 |

## Retrieval routing shortcut

| 질문 형태 | 먼저 볼 역할 | 다음 단계 |
|---|---|---|
| "어디부터 공부하지?" | `survey` | `catalog/navigator`로 이동 |
| "기초 개념이 안 잡혀요" | `primer` | 필요한 부분만 `deep dive`로 확장 |
| "기초는 잡혔는데 이 symptom을 어디로 넘길지 모르겠어요" | `primer bridge` | 가장 가까운 `deep dive`, `[recovery]`, `[system design]` handoff로 이동 |
| "이 주제 관련 문서를 빨리 찾고 싶다" | `catalog/navigator` | 문제와 가장 가까운 `deep dive`를 고른다 |
| "왜 이런 장애가 나지?" | `playbook` 또는 `deep dive` | 필요하면 `master note`로 범위를 넓힌다 |
| "여러 레이어가 같이 얽힌 문제다" | `master note` | 이후 카테고리별 `deep dive`를 붙인다 |
| "면접 질문으로 점검하고 싶다" | `question bank` | 막히는 항목만 `primer`나 `deep dive`로 보강한다 |

## authority-transfer starter

- `SCIM disable했는데 still access`, `deprovision은 끝났는데 access tail remains`, `backfill is green but access tail remains`처럼 database/security/system-design이 같이 걸리면 `[primer]` [Identity Lifecycle / Provisioning Primer](../contents/security/identity-lifecycle-provisioning-primer.md) -> `[primer]` [Role Change and Session Freshness Basics](../contents/security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](../contents/security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database README의 `Identity / Authority Transfer 브리지`](../contents/database/README.md#database-bridge-identity-authority) -> `[cross-category bridge]` [Security README의 `Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle) -> `[system design]` [System Design의 `Database / Security Authority Bridge`](../contents/system-design/README.md#system-design-database-security-authority-bridge) 순으로 starter를 고정한다.

## delegated cleanup starter

- `support AOBO / break-glass transfer cleanup이 안 닫힌다`, `cleanup_confirmed`를 언제 내려야 하나, `customer timeline closeout`과 delegated session cleanup이 같이 막히면 `[primer]` [Support Access Alert Router Primer](../contents/security/support-access-alert-router-primer.md) -> [Security README의 `Service / Delegation Boundaries deep dive catalog`](../contents/security/README.md#service--delegation-boundaries-deep-dive-catalog) -> [`Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle) -> [`Session / Boundary / Replay`](../contents/security/README.md#session--boundary--replay) 순으로 읽고, 장애 복구가 급할 때만 [`Incident / Recovery / Trust`](../contents/security/README.md#incident--recovery--trust)로 옮긴다.

## network-spring boundary starter

- `499`, `broken pipe`, `proxy timeout인지 spring bug인지`처럼 network/spring 경계가 섞이면 [Network README](../contents/network/README.md)의 `역할별 라우팅 요약` -> [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md) -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) 순으로 읽는다.

증상 기반 질문이면 문서 역할을 고르기 전에 [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)로 alias를 먼저 늘리는 편이 안전하다.

## 한 줄 운영 규칙

README와 topic map이 여러 역할을 함께 소개하더라도, 링크 묶음 하나하나는 `survey`, `primer`, `primer bridge`, `catalog`, `deep dive`, `master note`, `playbook`, `runbook`, `drill`, `incident matrix`, `question bank` 중 무엇인지 바로 읽히게 써 두는 것이 좋다.

## 한 줄 정리

beginner-first taxonomy에서는 README와 navigator의 첫 링크가 `primer`인지, 아니면 incident follow-up인지 라벨만 봐도 바로 구분되어야 한다.
