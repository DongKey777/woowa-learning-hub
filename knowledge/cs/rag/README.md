# RAG Design for `CS-study`

> 한 줄 요약: 이 저장소를 검색 가능한 학습 지식베이스로 만들기 위한 chunking, metadata, citation, role routing 기준을 정리한다.
>
> 이 `README`도 개념 본문이 아니라 retrieval 운영용 **navigator**다.

> retrieval-anchor-keywords: rag design readme, role routing, routing helper, meta navigator, category navigator, survey, study order, big picture, primer, basics, intro, catalog, navigator, index guide, what to read next, deep dive, playbook, runbook, drill, incident matrix, incident badge vocabulary, troubleshooting, response ladder, game day guide, master note, question bank, readme labeling, role audit, taxonomy checklist, authority transfer route, scim deprovision route, decision parity route, access tail remains route, auth shadow divergence route, revoke lag route, stale authz cache route, 403 after revoke route, auth outage route, auth-outage route, login loop route, hidden session mismatch route, savedrequest route, sid mapping route, spring security symptom route, cookie 있는데 다시 로그인 route, cookie exists but session missing route, 401 302 bounce route, api login html route, fetch gets login page instead of 401 route, transaction isolation route, transaction-isolation route, @Transactional route, transactional not applied route, rollback-only route, self invocation route, UnexpectedRollbackException route, database spring transaction bridge, database + spring route, authz-focused synthesis route, database security system design bridge, database + system design route, database + security + system design route, spring + network route, spring + security route, security + system design route, database routing summary, network routing summary, cross-category bridge, bridge entrypoint, authority route parity, identity authority transfer route, database security authority bridge route, verification shadowing authority bridge route, timeout disconnect bridge, spring network bridge, http stateless route, cookie session spring security route, beginner auth bridge, hidden jsessionid route, incident recovery trust route, browser session troubleshooting path route, session boundary replay route, identity delegation lifecycle route, authz tenant response contracts route, system design handoff cue, control plane handoff cue, cutover handoff cue

## 이 폴더의 역할

`CS-study`는 단일 문서 모음이 아니라, 아래 네 층으로 나뉜다.

1. 진입점 문서: `README.md`는 `meta navigator`, roadmap은 `survey`, `SENIOR-QUESTIONS.md`는 `question bank`
2. 카테고리 인덱스: `contents/*/README.md`는 `catalog/navigator`
3. 본문 문서: `contents/**/**/*.md`는 `primer`, `deep dive`, `playbook`, `runbook`, `drill`, `incident matrix`가 섞여 있다
4. 보조 자산: `materials/`, `code/`, `img/`

RAG에서는 이 네 층을 같은 무게로 보지 않는다.  
질문 유형에 따라 먼저 찾을 문서와, 보조 근거로 붙일 문서를 분리해야 한다.

이 폴더의 `README`, taxonomy, topic map은 대부분 **routing helper**다.
실제 개념 설명 근거는 카테고리 `README`의 `primer`나 개별 `contents/**` 문서로 내려가서 읽는 편이 맞다.

문서 역할 이름이 헷갈리면 [Navigation Taxonomy](./navigation-taxonomy.md)를 먼저 본다.

## README 이름이 같아도 역할은 다르다

- [CS Root README](../README.md) = 저장소 전체 `meta navigator`
- 각 `contents/*/README.md` = 카테고리 `catalog / navigator`
- 이 `rag/README.md`와 [Navigation Taxonomy](./navigation-taxonomy.md) = retrieval `routing helper`
- 실제 개념 설명과 trade-off 판단 = 카테고리 `primer`, 개별 `deep dive`, `playbook`, `runbook`, `drill`, `incident matrix`, `master note`

## 역할 우선 바로가기

| 질문 | 먼저 볼 문서 | 기대하는 역할 |
|---|---|---|
| 이 README가 설명 문서인지, 길찾기 문서인지 헷갈린다 | [Navigation Taxonomy](./navigation-taxonomy.md) | 역할 판별 기준 |
| `playbook` / `runbook` / `drill` / `incident matrix`를 언제 붙일지, mixed incident catalog의 adjacent deep dive를 bare link로 둬도 되는지 헷갈린다 | [Navigation Taxonomy](./navigation-taxonomy.md#incident-badge-vocabulary) | incident badge 선택 기준 + mixed catalog deep-dive cue |
| 저장소 전체에서 어디로 들어가야 할지 모르겠다 | [CS Root README](../README.md) | `meta navigator` |
| 카테고리 안에서 primer/catalog/deep dive를 골라야 한다 | 각 `contents/*/README.md` | `catalog / navigator` |
| database README의 `역할별 라우팅 요약`과 bridge subsection을 어디까지 navigator로 봐야 할지 헷갈린다 | [Navigation Taxonomy](./navigation-taxonomy.md), [Database README](../contents/database/README.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) | database routing summary / bridge handoff |
| network README의 routing summary와 bridge subsection을 symptom-first route에 어떻게 연결할지 헷갈린다 | [Navigation Taxonomy](./navigation-taxonomy.md), [Network README](../contents/network/README.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) | network routing summary / spring bridge handoff |
| 학습 순서를 잡고 싶다 | `../JUNIOR-BACKEND-ROADMAP.md`, `../ADVANCED-BACKEND-ROADMAP.md` | `survey` |
| 검색어가 역할 이름과 섞여 들어온다 | [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md) | role alias 확장 |
| `LIS`, `subsequence`, `subarray`, `subwindow`, `lower_bound`가 섞여 들어온다 | [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Algorithm README](../contents/algorithm/README.md) | algorithm alias re-query + adjacency check |
| `transaction isolation`, `@Transactional`, `self invocation`, `UnexpectedRollbackException`, `readOnly isolation`이 같이 보이고 README를 거치지 않고 바로 ladder로 들어가고 싶다 | [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) | transaction isolation / `@Transactional` / rollback debugging route (`database ↔ spring`) |
| `HTTP stateless`, `cookie`, `session`, `JWT`, `왜 로그인 상태가 유지되나`, `hidden JSESSIONID`처럼 기초 auth 개념에서 Spring 경계로 올라가고 싶다 | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md), [Network README](../contents/network/README.md), [Security README](../contents/security/README.md) | beginner auth bridge (`network -> security -> spring`) |
| `SavedRequest`, `login loop`, `hidden session mismatch`, `cookie 있는데 다시 로그인`, `401 -> 302 bounce`, `API가 login HTML을 받음`이 보이는데 `cookie/session`부터 다시 잡고 싶다 | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md), [Query Playbook](./query-playbook.md), [Security README](../contents/security/README.md) | beginner auth bridge -> browser `401` vs `302` symptom route |
| `stale read`, `499`, `broken pipe`, `client disconnect`, `JWKS outage`, `backfill is green but access tail remains`, `auth shadow divergence`처럼 증상으로 먼저 묻는다 | [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) | symptom-first cluster match with canonical route labels |
| `auth-outage`, `login loop`, `hidden session mismatch`, `SavedRequest`, `cookie 있는데 다시 로그인`, `401 -> 302 bounce`, `API가 login HTML을 받음`, `logout token은 오는데 spring 앱 세션을 못 찾는다`처럼 spring/security/session symptom으로 먼저 묻는다 | [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) | spring+security symptom route + browser/API fallback split + session persistence handoff |
| `revoke lag`, `logout but still works`, `stale deny`, `grant but still denied`, `403 after revoke`처럼 revoke/authz cache symptom으로 먼저 묻는다 | [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md), [Master Notes Index](../master-notes/README.md) | revoke-lag vs stale-authz-cache split + authz synthesis handoff |
| `authority transfer`, `SCIM deprovision`, `decision parity`처럼 database/security/system-design을 같이 봐야 한다 | [Topic Map](./topic-map.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md), [Query Playbook](./query-playbook.md) | 3-way bridge route (`Authority Transfer / SCIM Deprovision / Decision Parity`) |

## README 혼선이 생길 때

- 역할 경계가 헷갈리면 [Navigation Taxonomy](./navigation-taxonomy.md)에서 README audit checklist까지 같이 본다.
- incident badge를 통일해야 하면 같은 문서의 [Incident Badge Vocabulary](./navigation-taxonomy.md#incident-badge-vocabulary)부터 본다.
- 링크 이름, 섹션 라벨, `materials/`·`img/`·`code/` asset filename을 손봐야 하면 [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)로 내려간다. lowercase image/PDF extension과 mixed-case extension scanner pitfall, local HTML `src` / `href` / `srcset` update 규칙도 여기서 같이 정리한다. linked `img/`·`code/` path와 local HTML asset form을 따로 audit하고 싶으면 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)을 먼저 본다.
- category 문서의 same-category `README.md#...` reverse-link가 빠졌거나 stale slug를 잡고 있는지 보고 싶으면 [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)를 먼저 돌린다.
- markdown이 이미 가리키는 local asset path 중 punctuation-heavy filename이나 mixed-case image/PDF extension만 review 전에 빠르게 걸러야 하면 [Asset Filename Lint](./asset-filename-lint.md)를 먼저 돌린다. HTML `<a href>` / `srcset` candidate도 같은 check에 포함된다.
- markdown link와 무관하게 `knowledge/cs/**` 실제 PDF/image basename에서 rename queue만 좁게 만들고 싶으면 [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)을 먼저 본다.
- `knowledge/cs/contents/**` 아래 실제 `img/`·`code/` file인데 contents 문서에서 더는 inbound markdown/HTML link가 없는 orphan queue를 보고 싶으면 [Orphaned Auxiliary Asset Drift Scan](./orphaned-auxiliary-asset-drift-scan.md)을 먼저 본다. relink 전 filename-risky orphan도 여기서 같이 좁힌다.
- asset rename 뒤 old basename을 `rg -n --glob '*.md' -F '<old-basename.ext>' knowledge/cs docs`로 즉시 확인하고 missing target inbound link까지 묶어서 봐야 하면 [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)을 먼저 돌린다. HTML `<a href>` / `srcset` stale path도 여기서 같이 본다.
- quick-start나 `역할별 라우팅 요약`의 bridge row가 later bridge bundle을 다시 펼치기 시작하면 [README Quick-Start / Bridge Overlap Check](./readme-bridge-overlap-check.md)로 중복 lint와 수동 rule을 함께 보고, anchor-first before/after 예시대로 entrypoint anchor만 남긴다.
- code fence 안 literal markdown 예시 때문에 link/reverse-link QA가 흔들리면 같은 문서의 spacing guard 규칙을 보고, `.md` path만 담은 metadata 샘플이면 fence를 `yaml`/`text`로 낮춘다.
- broken-link reporting 전에 fenced example만 먼저 걸러야 하면 [Fence False-Link Precheck](./fence-false-link-precheck.md)로 repo-local QA check를 돌린다.
- retrieval-anchor-keywords를 보강해야 하면 [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)에서 role alias를 함께 정리한다.

## 권장 흐름

1. 질문 분류
2. 문서 역할 결정 (`survey` / `primer` / `catalog` / `deep dive` / `master note` / `playbook` / `runbook` / `drill` / `incident matrix`)
3. 카테고리 선택
4. 인덱스 문서 우선 탐색
5. 심화 문서 검색
6. 필요하면 코드/재료로 보강
7. 인용은 가장 가까운 원문으로 고정

## 바로 읽을 문서

- [CS Root README](../README.md) - 저장소 전체 meta navigator와 role-first quick routes
- [Navigation Taxonomy](./navigation-taxonomy.md) - README 역할 경계, root snapshot heading normalization, incident badge vocabulary, mixed incident catalog의 `[deep dive]` cue 기준, audit checklist, role alias 힌트, database / network routing summary와 cross-category bridge handoff 예시, security `Identity / Delegation / Lifecycle` -> database `Identity / Authority Transfer 브리지` -> system-design `Database / Security Authority Bridge` -> `Verification / Shadowing / Authority Bridge` 같은 cross-README route-name parity
- [Chunking and Metadata](./chunking-and-metadata.md) - section chunking, `linked_paths`, 그리고 repo-local `img/`·`code/` 또는 local HTML asset form이 들어간 chunk에서 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md) route를 같이 남기는 기준
- [Source Priority and Citation](./source-priority-and-citation.md) - 1차/2차/3차 source 우선순위와 `img/`·`code/`·local HTML asset evidence를 인용하기 전에 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)으로 path QA를 먼저 고정하는 기준
- [Topic Map](./topic-map.md) - category cluster label과 stale read / transaction isolation / `@Transactional` / client disconnect / auth-outage / login loop / JWKS outage / revoke lag / stale authz cache / authority transfer symptom alias, security README의 `Incident / Recovery / Trust` / `Browser / Session Troubleshooting Path` / `Session / Boundary / Replay` / `Identity / Delegation / Lifecycle` / `AuthZ / Tenant / Response Contracts` route label, `database ↔ spring` transaction ladder, LIS/subsequence vs subarray/subwindow/binary-search adjacency를 같이 본다
- [Query Playbook](./query-playbook.md) - symptom-first 재질의 템플릿, transaction isolation / `@Transactional` / `self invocation` / `UnexpectedRollbackException` / stale read / 499 / auth-outage / login loop / `cookie 있는데 다시 로그인` / `401 -> 302 bounce` / `API가 login HTML을 받음` / JWKS outage / revoke lag / stale authz cache / authority-transfer bridge route, Topic Map과 같은 `Incident / Recovery / Trust` / `Browser / Session Troubleshooting Path` / `Session / Boundary / Replay` label parity, `database ↔ spring` rollback debugging ladder, browser `401` vs `302` beginner bridge, LIS/subsequence vs subarray/subwindow alias route
- [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md) - 역할 alias, 증상 anchor, 템플릿 삽입 위치와 cross-README sibling route label을 metadata anchor에 같이 남기는 규칙을 함께 정리
- [Cross-Domain Bridge Map](./cross-domain-bridge-map.md) - cross-category reading order와 freshness / client-disconnect / spring-security / auth-incident / revoke-lag / stale-authz-cache / authority-transfer section label을 topic map alias cluster와 같은 이름으로 맞춘 symptom-first bridge shortcut이며, security README의 handoff cue parity와 `System Design:` transition label도 여기서 먼저 확인한다
- [Question Decomposition Examples](./question-decomposition-examples.md)
- [Retrieval Failure Modes](./retrieval-failure-modes.md)
- [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md) - README 라벨, 링크 문구, scanner-safe `materials/`·`img/`·`code/` filename, repo-local PDF/image short rule, lowercase image/PDF extension, mixed-case extension scanner pitfall, local HTML `src` / `href` / `srcset` co-update rule, fenced literal markdown spacing guard, metadata snippet fence 선택을 같이 정리할 때
- [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md) - category 문서가 sibling `README.md#...` reverse-link를 잃었거나 stale heading slug를 들고 있지 않은지 touched path 기준으로 확인할 때
- [Asset Filename Lint](./asset-filename-lint.md) - markdown과 inline HTML이 이미 가리키는 local asset path만 대상으로 공백, 괄호, `&`, extra dot stem, mixed-case image/PDF extension 같은 punctuation-heavy filename을 review 전에 빠르게 거를 때
- [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md) - markdown link 유무와 무관하게 `knowledge/cs/**` 실제 PDF/image basename 전체에서 rename 후보만 작게 큐잉할 때
- [Orphaned Auxiliary Asset Drift Scan](./orphaned-auxiliary-asset-drift-scan.md) - `knowledge/cs/contents/**` 아래 실제 `img/`·`code/` file 중 contents 문서에서 더는 직접 링크하지 않는 orphan queue와 filename-risky orphan을 함께 보고 싶을 때
- [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md) - asset rename 뒤 `rg -n --glob '*.md' -F '<old-basename.ext>' knowledge/cs docs`로 old basename을 즉시 찾고, missing local target을 inbound reference별로 다시 묶어 보고 싶을 때. HTML `<a href>` / `srcset` stale path도 같이 본다
- [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md) - `contents/**`에서 실제로 링크된 `img/`·`code/` 자산과 local HTML asset form(`<img src>`, `<a href>`, `srcset`)을 따로 뽑아 charset/path hygiene를 점검할 때
- [README Quick-Start / Bridge Overlap Check](./readme-bridge-overlap-check.md) - category README quick-start와 `역할별 라우팅 요약` bridge row가 later grouped bridge bundle을 다시 복제했는지 잡고, anchor-first cleanup 패턴을 맞추는 repo-local QA check
- [Fence False-Link Precheck](./fence-false-link-precheck.md) - broken-link reporting 전에 fenced code 안 link-like pattern을 먼저 잡는 repo-local QA check
- [RAG Ready Checklist](../RAG-READY.md)
