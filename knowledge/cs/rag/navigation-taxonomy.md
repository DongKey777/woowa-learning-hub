# Navigation Taxonomy

> 한 줄 요약: README와 navigator 문서에서 `survey`, `primer` / `primer bridge`, `catalog/navigator`, `deep dive`, `playbook` / `recovery`, `question bank`를 역할 기준으로 구분해 retrieval routing의 혼선을 줄인다.
>
> 관련 문서:
> - [CS Root README](../README.md)
> - [RAG Design](./README.md)
> - [Topic Map](./topic-map.md)
> - [Query Playbook](./query-playbook.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Master Notes](../master-notes/README.md)
> - [Database README](../contents/database/README.md)
> - [Network README](../contents/network/README.md)
> - [Security README](../contents/security/README.md)

> retrieval-anchor-keywords: navigation taxonomy, document role, meta navigator, category navigator, routing helper, survey, study order, big picture, primer, primer bridge, first-step primer, follow-up primer, handoff primer, basics, intro, catalog, navigator, deep dive, playbook, runbook, drill, incident matrix, recovery label, outage recovery guide, incident-oriented recovery, mixed incident catalog, bare deep dive link, explicit deep dive cue, troubleshooting, incident badge vocabulary, response ladder, live triage, steady-state procedure, rehearsal guide, game day guide, blast radius matrix, master note, question bank, interview questions, readme labeling, role audit, catalog snapshot, root snapshot heading, category readme heading, category navigator snapshot, 정리노트 heading normalization, index guide, entrypoint routing, what to read next, learning path, inline label, role badge, bridge role cue, bridge role label, deep dive label, system design label, system design bridge cue, bridge handoff parity, route-name parity, authority route parity, authority handoff naming, identity authority label parity, row parity authority parity retirement gate, mixed incident bridge, database routing summary, network routing summary, security routing summary, cross-category bridge, category bridge entrypoint, database bridge entrypoint, network bridge entrypoint, security bridge entrypoint, authority transfer route, identity delegation lifecycle alias, identity authority transfer alias, database security authority alias, verification shadowing authority alias, timeout disconnect bridge, spring network bridge, database security system design bridge, symptom-first bridge wording, scim tail cleanup route, scim disable but still access route, deprovision tail route, break glass cleanup symptom, cleanup_confirmed bridge, incident close blocked active override route

## 왜 필요한가

같은 `README.md` 안에 학습 순서, 입문 개념, 주제별 문서 목록, 실전 장애 문서가 함께 들어가면 읽는 사람도 RAG도 "지금 필요한 문서 역할"을 헷갈리기 쉽다.

이 문서는 파일명을 바꾸지 않고도 다음 질문에 답할 수 있게 만드는 최소 분류표다.

- 지금 필요한 게 큰 그림인가, 기초 개념인가, 문제별 진입점인가
- 단일 주제 깊이 파기인가, 여러 카테고리를 묶는 종합 정리인가
- 설명 문서가 필요한가, incident 대응 순서가 필요한가

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

## 문서 역할 표준

| 역할 | 먼저 볼 때 | 이 저장소의 대표 예시 | 혼동하면 생기는 문제 |
|---|---|---|---|
| `survey` | "어디부터 보지?", "큰 그림을 먼저 잡고 싶다" | [JUNIOR-BACKEND-ROADMAP](../JUNIOR-BACKEND-ROADMAP.md), [ADVANCED-BACKEND-ROADMAP](../ADVANCED-BACKEND-ROADMAP.md), [Learning Paths for Retrieval](./learning-paths-for-retrieval.md) | 세부 trade-off를 바로 해결해 줄 거라고 기대하게 된다 |
| `primer` | 기본 개념 축이 약해서 깊은 문서가 아직 안 읽힐 때. cold-start로 여는 첫 문서가 필요할 때 | [시스템 설계 면접 프레임워크](../contents/system-design/system-design-framework.md), [Spring Boot 자동 구성](../contents/spring/spring-boot-autoconfiguration.md), [응용 자료 구조 개요](../contents/data-structure/applied-data-structures-overview.md) | 입문 문서를 catalog나 deep dive로 착각해 다음 링크를 놓친다 |
| `primer bridge` | primer 하나는 읽었지만, symptom 언어나 boundary 용어를 다음 `deep dive` / handoff 문서로 연결해 줄 2단계 설명이 필요할 때 | [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md), [Claim Freshness After Permission Changes](../contents/security/claim-freshness-after-permission-changes.md), [Grant Path Freshness and Stale Deny Basics](../contents/security/grant-path-freshness-stale-deny-basics.md) | first-step primer와 handoff 문서의 차이가 흐려져, 아직 기초가 없는 독자가 bridge를 너무 빨리 열거나 반대로 deep dive 직전 연결 문서를 놓친다 |
| `catalog` / `navigator` | "이 주제에서 무엇을 읽어야 하지?"를 고를 때 | [CS Root README](../README.md), [Database README](../contents/database/README.md), [Network README](../contents/network/README.md), [RAG Design](./README.md) | 목록 문서에 정답 자체가 있다고 기대하게 된다 |
| `deep dive` | 특정 경계, trade-off, failure mode, 설계 결정을 파고들 때 | [Zero-Downtime Schema Migration Platform](../contents/system-design/zero-downtime-schema-migration-platform-design.md), [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md), [Timeout Budget Propagation](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) | broad survey와 구분이 흐려져 문서 난이도를 잘못 잡는다 |
| `master note` / `synthesis` | 여러 카테고리를 묶어 한 번에 설명해야 할 때 | [Latency Debugging Master Note](../master-notes/latency-debugging-master-note.md), [Consistency Boundary Master Note](../master-notes/consistency-boundary-master-note.md) | 단일 카테고리 문서를 읽어 놓고 전체 그림이 안 잡힌다고 느끼게 된다 |
| `playbook` | live symptom, incident, debugging 순서가 먼저 필요할 때 | [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md), [JWT Signature Verification Failure Playbook](../contents/security/jwt-signature-verification-failure-playbook.md), [Signing Key Compromise Recovery Playbook](../contents/security/signing-key-compromise-recovery-playbook.md) | planned procedure나 rehearsal 문서까지 전부 incident triage처럼 읽게 된다 |
| `runbook` | owner가 아는 작업을 repeatable하게 수행해야 할 때 | [Key Rotation Runbook](../contents/security/key-rotation-runbook.md) | live triage와 steady-state operation의 경계가 흐려져 checkpoint와 rollback 기대치가 어긋난다 |
| `drill` | game day, failover rehearsal, readiness validation이 목적일 때 | [JWT / JWKS Outage Recovery / Failover Drills](../contents/security/jwt-jwks-outage-recovery-failover-drills.md), [Backup, Restore, Disaster Recovery Drill](../contents/system-design/backup-restore-disaster-recovery-drill-design.md) | 실제 incident 대응 문서와 연습 문서를 같은 의미로 읽게 된다 |
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

한 링크 묶음에서는 이 역할 라벨을 하나만 전면에 내세우는 편이 혼선을 가장 적게 만든다.
`[primer bridge]`는 `primer` 계열 안에서 쓰는 inline route cue다. 새 top-level bucket을 하나 더 만드는 목적이 아니라, beginner route에서 "맨 처음 여는 문서"와 "그다음 deep dive로 넘기는 문서"를 구분할 때만 붙인다.
security의 login-loop row와 session-tail row처럼 인접한 beginner symptom shortcut에서도 `[catalog] -> [primer] -> [primer bridge] -> [deep dive]` 사다리를 끊지 않는 편이 안전하다.
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

빠른 선택 규칙:

1. "지금 장애가 났다. 첫 15분 대응이 필요하다"면 `[playbook]`이다.
2. "정해진 작업을 실수 없이 반복 수행해야 한다"면 `[runbook]`이다.
3. "실제 장애 전에 복구 절차를 연습하거나 readiness를 증명해야 한다"면 `[drill]`이다.
4. "어느 severity/owner/next doc로 갈지 먼저 골라야 한다"면 `[incident matrix]`다.
5. "장애 복구 사례를 깊게 설명하지만 step-by-step 주도 문서는 아니다"면 `[recovery]` 또는 `[deep dive]`다. mixed incident catalog에서는 개념 본문을 bare link로 남기지 않는다.

혼합형 문서라면 첫 화면에서 reader가 먼저 수행할 행동에 맞춰 badge를 고른다.
예를 들어 matrix 표가 앞에 있고 실제 절차는 linked playbook으로 넘기면 `[incident matrix]`가 맞고, 반대로 본문 대부분이 live response ladder라면 `[playbook]`이 맞다.

## README에서의 적용 규칙

### 1. 루트 README는 meta navigator가 우선이다

루트 `README.md`는 모든 내용을 설명하는 본문이 아니라, 아래 역할로 갈라 보내는 라우터여야 한다.

- roadmap = `survey`
- 카테고리 `README` = `catalog/navigator`
- master notes = `synthesis`
- senior questions = `question bank`
- RAG 문서 = retrieval routing helper

### 2. 카테고리 README는 진입점과 분류를 먼저 보여 준다

카테고리 `README.md`는 보통 이 순서를 유지하는 편이 덜 헷갈린다.

1. 빠른 탐색
2. `primer` 구간
3. `deep dive` 또는 문제 축별 `catalog`
4. cross-category bridge

한 문서가 두 역할을 겸할 수는 있지만, 빠른 탐색 블록에서는 **주 역할 하나만** 강조하는 편이 좋다.
특히 운영체제처럼 runtime topic이 길어지면 process / scheduler / memory / cgroup 같은 **scan-first bucket**을 먼저 세우고, 개별 문서명 나열은 그 아래로 내리는 편이 탐색 비용이 낮다.

### 2-1. database / network / security navigator는 bridge handoff를 노출해야 한다

최근 database / network / security category `README`는 `survey` -> `역할별 라우팅 요약` -> 문제 축별 `catalog` -> `cross-category bridge` 순서를 더 분명하게 드러낸다.
이때 `cross-category bridge` 구간은 deep dive 본문이 아니라, 질문이 카테고리 경계를 넘는 순간 다음 문서 묶음으로 넘기는 `category navigator`의 마지막 단계다.
특히 security처럼 incident 문서와 system-design handoff가 같이 섞이면, bullet 안에서도 `[playbook]` / `[deep dive]` / `[system design]` cue를 유지해 role shift를 숨기지 않는다.

- database pattern: [추천 학습 흐름](../contents/database/README.md#추천-학습-흐름-category-local-survey)으로 큰 축을 잡고 [역할별 라우팅 요약](../contents/database/README.md#역할별-라우팅-요약)에서 `survey / primer / catalog / playbook-runbook / taxonomy`를 고른 다음, [CDC / Outbox / Read Model Cutover 브리지](../contents/database/README.md#database-bridge-cdc-cutover)나 [Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority)로 진입한다. authority transfer route는 여기서 [Security README의 Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle), [System Design의 Database / Security Authority Bridge](../contents/system-design/README.md#system-design-database-security-authority-bridge), [Verification / Shadowing / Authority Bridge](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)까지 이어져야 bridge handoff parity가 맞는다.
- network pattern: [추천 학습 흐름](../contents/network/README.md#추천-학습-흐름-category-local-survey)과 [역할별 라우팅 요약](../contents/network/README.md#역할별-라우팅-요약)으로 진입한 뒤, [연결해서 보면 좋은 문서 (cross-category bridge)](../contents/network/README.md#연결해서-보면-좋은-문서-cross-category-bridge), [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md), [Service Discovery / Health Routing](../contents/system-design/service-discovery-health-routing-design.md)으로 spring / system-design handoff를 만든다.
- security pattern: [연결해서 보면 좋은 문서 (cross-category bridge)](../contents/security/README.md#연결해서-보면-좋은-문서-cross-category-bridge)에서 `[playbook]` / `[drill]` / `[incident matrix]`로 incident ladder를 먼저 열고, 이어지는 security 본문은 `[deep dive]`, system-design 쪽 handoff는 `[system design]`로 고정해 route-level 복구와 control-plane 설계를 한눈에 나눈다. system-design `README` 안의 bridge subsection이라도 handoff target이 system-design navigator라면 `[cross-category bridge]`로 되돌리지 않고 `[system design]` cue를 유지한다. 같은 bullet 안에서 security `deep dive`로 다시 돌아오면 `[deep dive]` cue를 재부착해서 later link가 앞 handoff badge를 암묵적으로 상속하지 않게 유지한다. 특히 `SCIM disable했는데 still access`, `break-glass는 종료됐는데 access/session tail이 남는다`, `cleanup_confirmed`를 언제 내려야 할지 모르겠다 같은 symptom phrase를 concept label 앞에 둬야 retrieval entrypoint가 category 이름만 반복하지 않는다.
- authority-transfer route-name parity: 같은 bridge라도 security README는 `Identity / Delegation / Lifecycle`, database README는 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design README는 `Database / Security Authority Bridge` -> `Verification / Shadowing / Authority Bridge`로 이름이 갈린다. 초보자에게는 "DB row parity -> security runtime authority tail -> system-design shadow/retirement evidence"라는 한 route로 먼저 설명하고, 이 축을 손볼 때는 한 README만 rename하지 말고 metadata anchor, quick-start row, related-doc bullet에 sibling label을 같이 남겨 route-name mismatch를 retrieval layer에서 흡수해야 한다.
- category bridge usage: `SCIM disable했는데 still access`, `deprovision은 끝났는데 access tail remains`, `backfill is green but access tail remains` 같은 질문은 database README의 bridge subsection에서 시작해 [security README의 `Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle), [system-design README의 `Database / Security Authority Bridge`](../contents/system-design/README.md#system-design-database-security-authority-bridge), [`Verification / Shadowing / Authority Bridge`](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)까지 같은 축으로 넘긴다. `break-glass는 종료됐는데 access/session tail이 남는다`, `incident close가 active override 때문에 막힌다` 같은 질문은 [security README의 `Incident / Recovery / Trust`](../contents/security/README.md#incident--recovery--trust)에서 시작해 [`Session / Boundary / Replay`](../contents/security/README.md#session--boundary--replay), [`Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle)까지 함께 본다. `499`, `broken pipe`, `proxy timeout인지 spring bug인지` 같은 질문은 network README bridge를 먼저 본다. 읽는 순서를 더 넓혀야 하면 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)으로 승격한다.

### 3. survey와 deep dive를 같은 말처럼 쓰지 않는다

- `survey`: 넓게 훑는다. 다음 문서를 고르기 쉽도록 만든다.
- `deep dive`: 하나의 경계나 판단을 끝까지 판다.

사례가 많더라도 목적이 "한 번에 넓게 훑기"면 survey에 가깝다.

### 4. question bank는 deep dive가 아니다

질문 목록은 스스로 점검하는 용도다.
설명과 근거가 필요하면 다시 `primer`, `deep dive`, `master note`로 내려가야 한다.

### 5. 이름을 안 바꿔도 README 혼선은 줄일 수 있다

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
| 카테고리 `README`에 primer 링크와 question bank가 연속으로 붙어 있다 | 질문 목록을 설명 본문처럼 읽게 된다 | `기본 primer`, `응용 catalog`, `면접형 question bank`처럼 구간 제목을 분리한다 |
| database / network README의 bridge subsection이 deep dive 본문처럼 읽힌다 | bridge 구간이 "여기서 설명이 끝난다"는 신호로 오해된다 | subsection 이름에 `cross-category bridge`를 유지하고, 바로 아래에서 다음 카테고리 reading order와 [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) handoff를 함께 적는다 |
| security 같은 mixed catalog에서 incident 대응 문서와 개념 deep dive, system-design handoff가 한 리스트에 섞여 있다 | step 문서를 찾는 사람도 개념 심화 문서를 찾는 사람도 같은 bullet 묶음에서 멈춘다 | mixed incident catalog 안의 incident 문서에는 `[playbook]`, `[runbook]`, `[drill]`, `[incident matrix]`, `[recovery]`, 나란히 놓인 개념 본문에는 `[deep dive]`, cross-category bridge 본문에는 `[deep dive]`, `[system design]` cue를 붙여 role shift를 드러낸다 |
| survey 문서가 사례가 많다는 이유로 deep dive처럼 소개된다 | 난이도와 기대 결과를 잘못 잡는다 | `넓게 훑는 survey`인지 `한 경계를 끝까지 파는 deep dive`인지 첫 문장에 적는다 |
| `RAG Design`이나 topic map이 개념 설명서처럼 읽힌다 | routing helper와 본문 근거 문서가 섞인다 | "역할 판별/라우팅용"이라고 적고, 실제 설명 문서는 category README나 deep dive로 내려 보낸다 |
| master note가 category index처럼 보인다 | synthesis 문서를 catalog로 오해해 누락된 세부 문서를 찾으려 한다 | `cross-domain synthesis`라는 표현을 붙이고, 세부 목록은 category README로 돌려보낸다 |

`증상별 바로 가기`처럼 symptom-first row가 security `README` bridge subsection이나 system-design `README` / 설계 문서로 바로 점프할 때도 같은 badge를 다시 붙인다. 같은 row 안에서 security `README` subsection entrypoint는 `[catalog]` 또는 `[cross-category bridge]`, system-design anchor/문서는 `[system design]`으로 반복 표기해 later handoff가 앞 링크 badge를 암묵적으로 상속하지 않게 유지한다. 예를 들어 `hidden session mismatch` row는 `[system design]` [Auth Session Troubleshooting Bridge](../contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge) -> `[system design]` [Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md), `logout tail` row는 `[system design]` [Auth Session Troubleshooting Bridge](../contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge) -> `[system design]` [Canonical Revocation Plane Across Token Generations](../contents/system-design/canonical-revocation-plane-across-token-generations-design.md) -> `[recovery]` [Revocation Bus Regional Lag Recovery](../contents/system-design/revocation-bus-regional-lag-recovery-design.md)처럼 bridge anchor와 downstream design docs 둘 다 cue를 반복한다.

### README 라벨 템플릿

복잡한 rename 없이도 상단 2~3줄만 고치면 혼선이 많이 줄어든다.

- 루트 `README`: `이 README는 저장소 전체의 meta navigator다.`
- 루트 category snapshot heading: `자료구조 README (category navigator snapshot)`처럼 카테고리명 + `README` + 역할 라벨을 같이 적고, generic `정리노트` 단독 heading은 피한다.
- 카테고리 `README`: `이 README는 category navigator다. primer 링크, routing summary, catalog, cross-category bridge를 묶고 필요하면 question bank를 덧붙인다.`
- security 같은 beginner symptom route: `[primer]`는 first-step 문서, `[primer bridge]`는 primer 다음 handoff 문서, 그 바로 뒤 심화 링크는 `[deep dive]` cue를 다시 붙인다고 짧게 못 박는다. login-loop row와 session-tail row가 나란히 있을 때도 같은 사다리(`[catalog] -> [primer] -> [primer bridge] -> [deep dive]`)를 유지한다. 예: `Login Redirect ... 입문 -> Browser 401 vs 302 Login Redirect Guide -> Spring RequestCache`, `Role Change and Session Freshness Basics -> Claim Freshness After Permission Changes -> Revocation Propagation Lag`.
- mixed incident catalog: `아래 목록에서 [playbook] / [runbook] / [drill] / [incident matrix]는 서로 다른 incident badge이고, 기준은 navigation-taxonomy의 Incident Badge Vocabulary를 따른다. [recovery]는 outage/degradation incident를 다루는 incident-oriented deep dive다. 같은 목록의 개념 본문은 bare link로 두지 말고 [deep dive] cue를 붙인다.`
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
6. 역할 이름이 검색어로도 들어올 문서라면 [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)와 맞물리게 alias를 남겼는가.

### retrieval-anchor-keywords 보강 힌트

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
| "`SCIM disable했는데 still access`, `deprovision은 끝났는데 access tail remains`, `backfill is green but access tail remains`처럼 database/security/system-design이 같이 걸린다" | `catalog/navigator` + `cross-category bridge` | [Database README](../contents/database/README.md)의 `역할별 라우팅 요약` -> `Identity / Authority Transfer 브리지` -> [Security README의 `Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle) -> [System Design의 `Database / Security Authority Bridge`](../contents/system-design/README.md#system-design-database-security-authority-bridge) -> [`Verification / Shadowing / Authority Bridge`](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge) -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) 순으로 읽는다 |
| "`break-glass는 종료됐는데 access/session tail이 남는다`, `cleanup_confirmed`를 언제 내려야 하나, `incident close가 active override 때문에 막힌다`" | `catalog/navigator` + `cross-category bridge` | [Security README](../contents/security/README.md)의 `연결해서 보면 좋은 문서` -> [`Incident / Recovery / Trust`](../contents/security/README.md#incident--recovery--trust) -> [`Session / Boundary / Replay`](../contents/security/README.md#session--boundary--replay) -> [`Identity / Delegation / Lifecycle`](../contents/security/README.md#identity--delegation--lifecycle) -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) 순으로 읽는다 |
| "`499`, `broken pipe`, `proxy timeout인지 spring bug인지`처럼 network/spring 경계가 섞인다" | `catalog/navigator` + `cross-category bridge` | [Network README](../contents/network/README.md)의 `역할별 라우팅 요약` -> [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md) -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) 순으로 읽는다 |
| "여러 레이어가 같이 얽힌 문제다" | `master note` | 이후 카테고리별 `deep dive`를 붙인다 |
| "면접 질문으로 점검하고 싶다" | `question bank` | 막히는 항목만 `primer`나 `deep dive`로 보강한다 |

증상 기반 질문이면 문서 역할을 고르기 전에 [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)로 alias를 먼저 늘리는 편이 안전하다.

## 한 줄 운영 규칙

README와 topic map이 여러 역할을 함께 소개하더라도, 링크 묶음 하나하나는 `survey`, `primer`, `primer bridge`, `catalog`, `deep dive`, `master note`, `playbook`, `runbook`, `drill`, `incident matrix`, `question bank` 중 무엇인지 바로 읽히게 써 두는 것이 좋다.
