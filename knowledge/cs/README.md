# Basic Knowledge of Computer Science

> Since 2020.09.04

**난이도: 🟢 Beginner**

<p align="center">
  <img src="https://user-images.githubusercontent.com/22045163/111120575-d9370f00-85ae-11eb-8fa3-54f47ed3caa3.png" alt="coding" width="150px" />
</p>

> retrieval-anchor-keywords: cs root readme, meta navigator, readme router, roadmap, survey, study order, big picture, category readme, category navigator, category navigator snapshot, category readme snapshot, primer, basics, intro, catalog snapshot, navigator, index guide, what to read next, deep dive, troubleshooting, incident badge vocabulary, playbook label, runbook label, drill label, incident matrix label, master note, synthesis, question bank, interview questions, senior questions, rag routing, navigation taxonomy, security bridge cluster, auth session bridge, auth session troubleshooting bridge, auth session shortcut, root auth session shortcut, beginner auth session shortcut, why login state is kept, login state beginner route, cookie session jwt beginner bridge, role change session freshness, grant path freshness, tenant membership freshness, tenant session scope bridge, tenant context stale, active tenant stale, authority bridge, scim tail bridge first, deprovision tail bridge first, access tail bridge first, replay session defense bundle, service delegation boundary bundle, hardware trust recovery bundle, incident recovery trust, session boundary replay, identity delegation lifecycle, auth outage, auth-outage, login loop, cookie drop, session store outage, saved request loop, savedrequest, sid mapping, post-login session persistence, logout token session miss, replay store down, nonce store down, replay-safe retry, duplicate request after retry, backfill replay, revoke lag, logout still works, logout tail, revocation tail, allowed after revoke, stale authz cache, stale deny, tenant-specific 403, cached 404 after grant, missing audit trail, missing-audit-trail, audit trail missing, auth signal gap, auth-signal-gap, auth telemetry gap, decision log missing, no decision log, observability blind spot, acting on behalf of, break glass, delegated admin, support access notification, authority transfer, SCIM deprovision, SCIM disable but still access, auth shadow divergence, trust bundle recovery, trust bundle rollback, hardware attestation failure, database category navigator, database category survey, database routing summary, database primer, database deep dive catalog, network category survey, network routing summary, network category primer, network deep dive catalog, network legacy primer, network modern topic catalog, minimum spanning tree, MST, mst router, prim vs kruskal, connect all nodes minimum cost, connect all cities minimum cost, connect all points minimum cost, minimum spanning forest, shortest path vs mst, 모든 정점을 최소 비용으로 연결, 최소 신장 트리, 프림, 크루스칼, stale read, stale-read, read-after-write, replica lag, transaction beginner side path, REQUIRES_NEW beginner route, rollback-only beginner route, readOnly beginner route, routing datasource confusion, inner readOnly writer pool, partial commit beginner, client disconnect, client-disconnect, 499, broken pipe, cancellation propagation, 502, 504, bad gateway, gateway timeout, local reply, upstream reset, timeout mismatch, async timeout mismatch, idle timeout mismatch, deadline budget mismatch, jwks outage, JWKS outage, auth verification outage, invalid signature, kid miss, unable to find JWK, stale jwks cache, browser session troubleshooting path, 302 login loop, hidden session mismatch
> retrieval-anchor-keywords: cookie exists but not sent, cookie stored but not sent, application tab cookie but request Cookie header missing, secure cookie behind proxy branch, blocked set-cookie vs stored not sent vs sent but anonymous, cookie three-way splitter
> retrieval-anchor-keywords: login loop primer bridge, canonical beginner entry route login loop, saved request primer bridge, savedrequest primer bridge, hidden session beginner route, cookie 있는데 다시 로그인 beginner route, session tail beginner route, logout tail primer bridge, revocation tail beginner route, session freshness primer bridge, cookie-missing beginner route, server-anonymous beginner route, cookie-not-sent beginner route, server-mapping-missing beginner route, normalized auth session route table
> retrieval-anchor-keywords: primer-first browser session ladder, root primer first auth ladder, auth session safe next step, browser session primer ladder, saved request before requestcache, browser 401 302 before spring deep dive, redirect 기억 cookie 전송 server 복원, redirect memory cookie transfer server persistence, cookie transfer auth shortcut, server persistence session mapping auth shortcut, root auth alias split, cookie not sent root handoff, server anonymous root handoff, server mapping missing root handoff, safe next doc before spring deep dive
> retrieval-anchor-keywords: woowacourse backend learning ladder, woowacourse backend beginner ladder, 우테코 백엔드 사다리, 우테코 백엔드 학습 순서, java basics http web basics mvc jdbc transactions di aop system design ladder, java to http to mvc to jdbc transaction to di aop to system design, backend mission safe ladder
> retrieval-anchor-keywords: social login primer route, social login beginner route, oauth oidc social login root route, google login beginner route, auth app subdomain login, auth app subdomain callback, auth callback app anonymous root route, auth.example.com callback app.example.com anonymous root route, subdomain callback beginner detour, callback success app anonymous primer, broad cs entry social login primer, oauth oidc before callback hardening, social login before advanced callback docs

처음 들어온 junior reader가 가장 먼저 볼 것은 "설명 본문"이 아니라 "어느 shelf에서 멈춰야 안전한가"다.
이 루트 `README`는 `meta navigator`이고, 아래 4칸만 먼저 구분하면 `primer`, `deep dive`, `playbook`이 한 화면에 섞여 있어도 첫 클릭을 덜 헷갈린다.

| 지금 검색한 말 | 루트에서 먼저 붙일 역할 | 여기서 먼저 여는 문서 | 아직 첫 클릭으로 올리지 않는 것 |
|---|---|---|---|
| `처음`, `뭐부터`, `학습 순서`, `big picture` | `survey` | [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md) | incident / recovery 문서, master note |
| `what is`, `basics`, `헷갈려요`, `왜 이렇게 나뉘어요` | `category README -> primer` | 각 category `README` | deep dive catalog, senior question bank |
| 증상은 있는데 카테고리가 헷갈림 | `category navigator` | [Quick Routes](#quick-routes) 아래 beginner shortcut | recovery playbook를 primer처럼 읽기 |
| 이미 원인 축을 알고 한 경계만 더 파고 싶음 | `deep dive follow-up` | category `README` 안의 deep-dive 구간 | 루트에서 advanced shelf를 첫 클릭으로 쓰기 |

- 루트에서 안전한 순서는 `survey -> category README -> primer -> primer bridge -> deep dive`다.
- `advanced`, `incident`, `recovery`, `cutover`, `master note`, `senior`가 제목 앞에 보이면 beginner entrypoint가 아니라 follow-up shelf로 읽는다.

처음 검색 결과에서 `README`만 보여도 아래처럼 파일 역할부터 나누면 incident 문서를 entrypoint로 오해할 가능성이 줄어든다.

| 검색 결과에서 먼저 보인 파일 | 이 파일의 역할 | beginner-safe first click? | 다음 안전한 한 걸음 |
|---|---|---|---|
| 루트 `README.md` | `meta navigator` | yes | `survey`나 category `README`로 내려가기 |
| `contents/*/README.md` | `category navigator` | yes | 같은 README 안의 `primer` / `primer bridge` 고르기 |
| `rag/README.md`, `rag/navigation-taxonomy.md` | `routing helper` | yes, but only for role decoding | 역할을 확인한 뒤 category `README`나 linked `primer`로 이동 |
| `Advanced Backend Roadmap`, `Master Notes`, `Senior Questions` | advanced `survey` / `synthesis` / `question bank` | no | beginner 사다리(`survey -> category README -> primer`)를 먼저 끝낸 뒤 보기 |

문서 이름이 아니라 제목 앞 역할 단어로 멈출 shelf를 판단한다.
`survey`, `primer`, `primer bridge`, `navigator`면 entry shelf이고, `deep dive`, `playbook`, `recovery`, `master note`면 follow-up shelf다.

## Table of Contents

- [About](#about)
  - [Repository Rule](#repository-rule)
  - [Collaborator](#collaborator)
  - [Reference](#reference)
- [Beginner Entrypoints / Quick Routes](#quick-routes)
  - [Woowacourse Backend Beginner Ladder](#woowacourse-backend-beginner-ladder)
  - [Auth / Session Beginner Shortcut](#auth--session-beginner-shortcut)
  - [Symptom-First Primer Bridge Routes](#symptom-first-quick-routes)
- [Junior Backend Roadmap](#junior-backend-roadmap)
- [Advanced Backend Roadmap](#advanced-backend-roadmap)
- [Master Notes](#master-notes)
- [Senior-Level Questions](#senior-level-questions)
- [RAG Ready](#rag-ready)
- [Category Catalog Snapshots](#category-catalog-snapshots)
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

<a id="quick-routes"></a>

## Beginner Entrypoints / Quick Routes (`meta navigator`)

이 루트 `README`는 저장소 전체의 **meta navigator**다.
여기서 설명을 끝내기보다, 필요한 역할 문서로 한 단계 더 내려 보내는 것이 목적이다.

처음 읽는 junior reader는 "지금 보이는 문서가 입문용인가, follow-up인가"만 먼저 구분하면 된다.
루트에서는 아래 역할 사다리만 기억하고, `incident`, `recovery`, `playbook`, `master note`, `senior`가 보이면 첫 클릭 후보에서 잠깐 뺀다.

| 역할 | 지금 하는 일 | beginner 첫 클릭 여부 |
|---|---|---|
| `survey` | 큰 그림과 학습 순서를 고른다 | yes |
| `category README` | 카테고리 안에서 다음 primer를 고른다 | yes |
| `primer` / `primer bridge` | 개념 축을 세우고 증상 말을 질문 축으로 자른다 | yes |
| `deep dive` | 원인 하나를 깊게 판다 | not first |
| `playbook` / `runbook` / `recovery` / `master note` | 운영 절차, 장애 대응, 종합 정리 | no |

`처음`, `뭐부터`, `헷갈려요`, `what is`, `basics`처럼 broad하게 묻는 상태라면 이 문서에서 바로 incident 문서로 점프하지 않는다.
먼저 `survey -> category README -> primer -> primer bridge`까지로 질문 축을 자르고, `deep dive`와 `playbook/recovery`는 그 다음 단계로 미룬다.

초심자가 가장 먼저 기억할 규칙은 단순하다.
루트에서는 `survey -> category README -> primer -> primer bridge -> deep dive` 순서로 내려가고, `advanced`, `incident`, `cutover`, `recovery`, `case study`가 보이면 첫 클릭이 아니라 follow-up shelf로 본다.

처음 3클릭만 따로 자르면 아래처럼 보면 된다.

| 지금 상태 | 이 루트에서 맡는 역할 | 안전한 다음 클릭 |
|---|---|---|
| "`처음`이라 전체 순서가 필요해요" | `meta navigator -> survey` | [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md) |
| 카테고리는 대충 아는데 primer를 못 고르겠어요 | `meta navigator -> category navigator` | 각 category `README` |
| 검색 결과가 `incident`, `recovery`, `master note`로 시작해요 | follow-up shelf 경고 | 루트에서 `survey`나 category `README`로 한 칸 되돌아가기 |

`README.md`라는 파일명만으로 역할을 판단하지 않는다.
루트 `README`는 `meta navigator`, 카테고리 `README`는 `catalog / navigator`, `rag/*.md`는 `routing helper`에 가깝다.
이 역할 라벨이 헷갈리면 [Navigation Taxonomy](./rag/navigation-taxonomy.md)를 먼저 열어도 된다.

처음 10초 해석만 따로 떼면 아래 표 하나로도 충분하다.

| 보이는 라벨 | 이 뜻으로 읽기 | beginner 첫 클릭 |
|---|---|---|
| `survey` | 큰 그림과 학습 순서 | yes |
| `primer` / `primer bridge` | 첫 개념 설명, 헷갈리는 분기 정리 | yes |
| `deep dive` | 한 원인이나 경계를 깊게 파기 | 기본 축을 잡은 뒤 |
| `playbook` / `runbook` / `recovery` | 운영 절차, 장애 대응, 복구 follow-up | no |

초심자가 가장 자주 헷갈리는 오해도 한 번만 못 박아 둔다.

| 검색 결과에서 먼저 보인 것 | beginner-safe 해석 | 바로 열지 않는 것 |
|---|---|---|
| `Security README` | category `navigator`로 읽고 `기본 primer`나 `증상별 바로 가기`부터 시작 | `운영 / Incident catalog`를 첫 클릭으로 여는 것 |
| `navigation-taxonomy.md` | 역할 표지판을 읽는 `routing helper` | 개념 primer 본문처럼 끝까지 읽으려는 것 |
| `Master Notes`, `Senior Questions` | follow-up synthesis / self-check shelf | broad `what is`, `처음`, `basics` 질문의 첫 답 |

| 지금 필요한 것 | 문서 역할 | 먼저 볼 문서 | 아직 기대하지 말 것 |
|---|---|---|---|
| 저장소 전체에서 어디로 들어갈지 정하기 | `meta navigator` | 이 루트 `README` | `primer`나 `deep dive` 본문 |
| 학습 순서를 잡는 큰 그림 | `survey` | roadmap 문서들 | 세부 장애 대응이나 trade-off 결론 |
| 카테고리 안에서 다음 문서를 고르기 | `catalog / navigator` | 각 카테고리 `README` | 본문 설명 전체 |
| 특정 주제의 개념 축을 세우기 | `primer` | 카테고리 `README`의 primer 구간 | cross-domain synthesis |
| 특정 경계나 failure mode를 깊게 파기 | `deep dive` | 개별 `contents/**` 문서 | 넓은 학습 순서 안내 |
| incident badge를 구분해서 고르기 | `playbook` / `runbook` / `drill` / `incident matrix` | `rag/navigation-taxonomy.md#incident-badge-vocabulary`, incident-heavy 카테고리 `README` | badge 이름이 다 비슷하다고 보고 아무 데나 같은 의미로 붙이기 |
| 여러 카테고리를 엮어 정리하기 | `master note` / `synthesis` | `master-notes/README.md` | 카테고리 전체 catalog |
| README나 navigator 역할이 헷갈리기 | `taxonomy` / `routing helper` | `rag/navigation-taxonomy.md`, `rag/README.md` | 개념 설명 본문 |

beginner 안전 규칙도 한 줄로 고정해 둔다.

- 첫 클릭은 가능하면 `survey`, `primer`, `primer bridge`, `catalog` 중 하나로 시작한다.
- `Advanced Backend Roadmap`, `Master Notes`, `Senior-Level Questions`는 useful하지만 beginner entrypoint는 아니다.
- `playbook`, `runbook`, `drill`, `recovery`는 "지금 장애/운영 순서가 먼저 필요한가?"가 맞을 때만 연다.

처음 보는 주제에서 멈출 shelf를 더 짧게 외우면 아래 셋만 기억해도 된다.

| 질문 모양 | 여기서 멈출 shelf | 바로 다음 한 걸음 | 아직 미루는 것 |
|---|---|---|---|
| `처음`, `뭐예요`, `what is`, `basics` | `survey` 또는 category `README` | category `primer` | `incident`, `recovery`, `master note` |
| `헷갈려요`, `왜 이렇게 나뉘어요`, symptom phrase | category `README`의 `primer bridge` | 관련 `deep dive` 1개 | 여러 deep dive 동시 열기 |
| `지금 장애/운영 순서가 필요해요` | incident-heavy category `README` | `playbook` / `runbook` / `recovery` | broad primer부터 다시 읽기 |

루트에서 자주 섞이는 shelf를 더 짧게 자르면 아래처럼 보면 된다.

| shelf | 역할 | beginner 첫 클릭 여부 | 언제 여나 |
|---|---|---|---|
| [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md) | `survey` | yes | `처음`, `뭐부터`, `큰 그림` |
| 각 category `README` | `catalog / navigator` | yes | 카테고리는 정해졌는데 primer를 고르기 전 |
| category primer / primer bridge | `primer` / `primer bridge` | yes | 기본 개념 축, symptom 분기가 먼저 필요할 때 |
| [Advanced Backend Roadmap](./ADVANCED-BACKEND-ROADMAP.md) | `survey`, advanced | no | 이미 입문 흐름을 지나 심화 주제를 고를 때 |
| [Master Notes](./master-notes/README.md) | `synthesis`, advanced | no | 여러 카테고리를 묶어 이유와 trade-off를 정리할 때 |
| [Senior-Level Questions](./SENIOR-QUESTIONS.md) | `question bank`, advanced | no | 읽은 뒤 self-check를 할 때 |
| incident-heavy README sections | `playbook` / `runbook` / `recovery` | no | 실제 장애 대응 순서가 먼저 필요할 때 |

처음 보는 주제에서 가장 안전한 사다리는 `survey -> category README -> primer -> primer bridge -> deep dive`다.
`advanced`, `incident`, `cutover`, `recovery`, `case study`라는 단어가 먼저 보이면 첫 클릭 후보가 아니라 follow-up 후보로 읽는 편이 junior reader에게 안전하다.

루트에서 시작할 때와 카테고리 안에 이미 들어온 뒤는 안전 사다리를 조금 다르게 보면 덜 헷갈린다.

| 출발 위치 | beginner-safe 사다리 | 처음부터 올리지 않는 것 |
|---|---|---|
| 저장소 루트, 검색 결과에서 `README`만 먼저 보임 | `meta navigator -> survey -> category README -> primer -> primer bridge -> deep dive` | `master note`, `playbook`, `recovery`, `case study` |
| 카테고리 `README`에 이미 들어와 있음 | `category README -> primer -> primer bridge -> deep dive -> playbook/recovery` | category 안의 incident catalog를 primer처럼 읽기 |

혼동이 잦은 역할만 다시 짧게 자르면 아래 표다.

| 질문 모양 | 먼저 고를 역할 | 루트에서 안전한 첫 클릭 | 아직 미루는 것 |
|---|---|---|---|
| `처음`, `뭐부터`, `큰 그림` | `survey` | [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md), [Woowacourse Backend Beginner Ladder](#woowacourse-backend-beginner-ladder) | incident `playbook`, `recovery`, master note |
| `what is`, `헷갈려요`, 개념 첫 설명 | `primer` / `primer bridge` | category `README`, [Auth / Session Beginner Shortcut](#auth--session-beginner-shortcut) | cutover, control-plane deep dive |
| `service 코드인데 map/queue/BFS가 먼저 막혀요` | `cross-category primer bridge` | [Woowacourse Backend Beginner Ladder](#woowacourse-backend-beginner-ladder), [우테코 백엔드 미션 선행 개념 입문](./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md) | system design, weighted shortest path, 운영 queue 문서 |
| 이미 기본 개념은 있고 한 경계만 깊게 봄 | `deep dive` | 각 category `README`의 deep-dive catalog | broad survey 재시작 |
| live incident나 복구 순서가 먼저 필요함 | `playbook` / `runbook` / `recovery` | incident-heavy category `README`의 운영 catalog | beginner primer를 대응 절차로 착각하기 |

- 학습 순서용 `survey`부터 보고 싶다면:
  - [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md)
  - [Advanced Backend Roadmap](./ADVANCED-BACKEND-ROADMAP.md) (`advanced` follow-up)
- 카테고리별 `catalog / navigator`로 바로 들어가려면:
  - 각 카테고리 `contents/*/README.md`
- 교차 도메인 `synthesis / master note`로 바로 들어가려면:
  - [Master Notes](./master-notes/README.md) (`advanced` follow-up)
- 면접형 `question bank`로 점검하려면:
  - [Senior-Level Questions](./SENIOR-QUESTIONS.md) (`advanced` self-check)
- README / navigator 역할이 헷갈리면:
  - [Navigation Taxonomy](./rag/navigation-taxonomy.md)
  - [RAG Design](./rag/README.md)
- auth / session을 category 들어가기 전에 짧게 잡고 싶다면:
  - [Auth / Session Beginner Shortcut](#auth--session-beginner-shortcut)
- 우테코 백엔드 선행 사다리만 먼저 고정하고 싶다면:
  - [Woowacourse Backend Beginner Ladder](#woowacourse-backend-beginner-ladder)
  - [우테코 백엔드 미션 선행 개념 입문](./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md)
- incident 대응 badge 기준이 헷갈리면:
  - [Incident Badge Vocabulary](./rag/navigation-taxonomy.md#incident-badge-vocabulary) (`playbook/runbook/recovery` follow-up helper)
- 검색어가 역할 이름과 섞이면:
  - [Retrieval Anchor Keywords](./rag/retrieval-anchor-keywords.md)
- 문서 역할 구분이나 retrieval 라우팅 규칙이 더 필요하면:
  - [Topic Map](./rag/topic-map.md)
  - [Query Playbook](./rag/query-playbook.md)

### Woowacourse Backend Beginner Ladder

우테코 백엔드 입문에서는 category `README`를 전부 순회하기보다, 아래 ladder를 먼저 고정하는 편이 안전하다.
핵심은 `primer -> primer bridge -> deep dive` 순서를 지키는 것이다.

| 단계 | primer | 안전한 다음 한 걸음 | deep dive는 나중에 |
|---|---|---|---|
| 1. Java basics | [자바 언어의 구조와 기본 문법](./contents/language/java/java-language-basics.md) | [Java 타입, 클래스, 객체, OOP 입문](./contents/language/java/java-types-class-object-oop-basics.md) | [Language README](./contents/language/README.md) 전체 catalog |
| 2. HTTP / web basics | [HTTP 요청-응답 기본 흐름](./contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [HTTP 메서드와 REST 멱등성 입문](./contents/network/http-methods-rest-idempotency-basics.md) | [Network README](./contents/network/README.md) 운영형 deep dive |
| 3. MVC | [Spring 요청 파이프라인과 Bean Container 기초](./contents/spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Spring MVC 컨트롤러 기초](./contents/spring/spring-mvc-controller-basics.md) | [Spring MVC 요청 생명주기](./contents/spring/spring-mvc-request-lifecycle.md) |
| 4. DB handoff / transactions | [Database First-Step Bridge](./contents/database/database-first-step-bridge.md) | "`save()`/SQL 위치가 먼저면" [JDBC · JPA · MyBatis 기초](./contents/database/jdbc-jpa-mybatis-basics.md), "`commit`/`rollback` 범위가 먼저면" [트랜잭션 기초](./contents/database/transaction-basics.md) | [인덱스와 실행 계획](./contents/database/index-and-explain.md), [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md) |
| 5. DI / AOP | [IoC와 DI 기초](./contents/spring/spring-ioc-di-basics.md) | [AOP 기초](./contents/spring/spring-aop-basics.md) -> [@Transactional 기초](./contents/spring/spring-transactional-basics.md) | propagation / rollback-only / self-invocation 심화 |
| 6. System design | [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./contents/system-design/stateless-backend-cache-database-queue-starter-pack.md) | [System Design Foundations](./contents/system-design/system-design-foundations.md) | cutover / control-plane incident 문서 |

- "`처음`이고 `브라우저 -> controller -> save()` 전체 흐름이 헷갈리면" 한 칸씩만 간다:
  [HTTP 요청-응답 기본 흐름](./contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) -> [Spring 요청 파이프라인과 Bean Container 기초](./contents/spring/spring-request-pipeline-bean-container-foundations-primer.md) -> [Database First-Step Bridge](./contents/database/database-first-step-bridge.md) -> [JDBC · JPA · MyBatis 기초](./contents/database/jdbc-jpa-mybatis-basics.md).
  `lock`, `deadlock`, `failover`, `playbook`은 이 4칸 뒤에만 붙인다.
- beginner phrase anchor:

| 지금 떠오른 말 | 여기서 멈출 문서 | 안전한 다음 한 걸음 | 아직 미루는 문서 |
|---|---|---|---|
| "`HTTP 다음에 Spring은 뭐부터 봐요?`" | [HTTP 요청-응답 기본 흐름](./contents/network/http-request-response-basics-url-dns-tcp-tls-keepalive.md) | [Spring 요청 파이프라인과 Bean Container 기초](./contents/spring/spring-request-pipeline-bean-container-foundations-primer.md) | Spring deep dive catalog 전체 |
| "`controller` 다음 `save()`가 보이는데 SQL은 어디서 봐요?" | [Database First-Step Bridge](./contents/database/database-first-step-bridge.md) | [JDBC · JPA · MyBatis 기초](./contents/database/jdbc-jpa-mybatis-basics.md) | 락, failover, replay, cutover 문서 |
| "`왜 같이 rollback돼요?`" | [Database First-Step Bridge](./contents/database/database-first-step-bridge.md) | [트랜잭션 기초](./contents/database/transaction-basics.md) | [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md) |
| "`service` 코드인데 `map/queue`가 먼저 막혀요", "`queue`가 worker handoff인지 BFS인지 헷갈려요" | [우테코 백엔드 미션 선행 개념 입문](./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md) | [Java 컬렉션 프레임워크 입문](./contents/language/java/java-collections-basics.md) -> [Backend Data-Structure Starter Pack](./contents/data-structure/backend-data-structure-starter-pack.md) -> `계산 질문`이면 [Backend Algorithm Starter Pack](./contents/algorithm/backend-algorithm-starter-pack.md), `책임 질문`이면 [Service 계층 기초](./contents/software-engineering/service-layer-basics.md) | weighted shortest path, broker/scheduler, system design 큐 심화 |
| "`map null`이 왜 헷갈리는지", "`TreeMap`이 왜 필요한지", "`floor`/`ceiling`이 왜 어떤 때는 `null`인지" | [Java 컬렉션 프레임워크 입문](./contents/language/java/java-collections-basics.md) | `조회 null 해석`이면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./contents/language/java/map-get-null-containskey-getordefault-primer.md), `구현체별 null 정책`이면 [Map null 허용 여부 구현체 브리지](./contents/language/java/map-null-policy-hashmap-hashtable-concurrenthashmap-mapof-bridge.md), `ordered map 경계`면 [Ordered Map Null-Safe Practice Drill](./contents/language/java/ordered-map-null-safe-practice-drill.md) | comparator deep dive, concurrent map internals, JVM diagnostics |
- MVC에서 JDBC/트랜잭션으로, 다시 DI/AOP로 넘어가며 `controller / service / repository / @Transactional / proxy`가 한 문장에 섞이면 [Spring MVC -> JDBC/트랜잭션 -> DI/AOP 전환 오해 체크리스트](./contents/spring/spring-mvc-jdbc-transaction-di-aop-transition-checklist.md)부터 보고, 그다음 [JDBC · JPA · MyBatis 기초](./contents/database/jdbc-jpa-mybatis-basics.md) -> [트랜잭션 기초](./contents/database/transaction-basics.md) -> [@Transactional 기초](./contents/spring/spring-transactional-basics.md) -> [AOP 기초](./contents/spring/spring-aop-basics.md) 순으로 간다.
- 안전 사다리를 문서 하나로 보고 싶으면 [우테코 백엔드 미션 선행 개념 입문](./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md)으로 바로 간다.
- 이 route를 roadmap 관점으로 다시 보면 [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md#우테코-백엔드-안전-사다리-동기화)에서 같은 순서를 따라갈 수 있다.

### Auth / Session Beginner Shortcut

로그인 문제는 먼저 네 칸으로 자른다. `Location scheme / origin` -> `redirect / navigation memory` -> `cookie transfer` -> `server persistence / session mapping` 순서다. 즉 `login 직후 Location이 public https origin으로 유지되는가` -> `원래 가려던 URL/redirect 기억이 꼬였는가` -> `request Cookie header가 실제로 붙는가` -> `cookie는 왔는데 서버가 session/auth state를 복원하지 못하는가`를 먼저 나눈다. root handoff alias로는 세 번째를 `cookie-not-sent`, 네 번째를 `server-mapping-missing`으로 읽으면 된다.
초보자 첫 클릭 규칙은 더 단순하다. login 직후 `Location`이 `http://...`로 꺾이거나 `https://...`인데 host/origin이 public 값과 다르면 cookie 표보다 먼저 `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md)으로 간다. redirect가 정상일 때만 아래 표의 `redirect / navigation memory`나 `cookie transfer`로 내려간다. 길을 잃으면 [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path)로 돌아온다.
allowed-after-revoke, grant/stale-deny, tenant-membership freshness는 모두 같은 beginner ladder를 쓴다. 먼저 `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md)로 mental model을 맞추고, 그다음 증상별 `[primer bridge]` 하나만 고른 뒤에만 `deep dive`나 `recovery`로 내려간다. `allowed after revoke`처럼 아직 허용되는 tail은 `[primer bridge]` [Claim Freshness After Permission Changes](./contents/security/claim-freshness-after-permission-changes.md)로, `stale deny`처럼 아직 거부되는 tail은 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./contents/security/grant-path-freshness-stale-deny-basics.md)로 먼저 갈라 잡는다.
Spring 경계까지 바로 내려가야 할 때의 direct jump도 하나만 기억하면 된다. `redirect / navigation memory`와 `server persistence / session mapping`을 Spring 쪽 anchor에서 다시 고정하려면 [Spring Security 예외 번역과 세션 경계](./contents/spring/README.md#spring-bridge-security-session-boundary)로 간다.
아래 표만 기억하면 beginner phrase를 route label로 바로 정규화할 수 있다.

| 검색/질문 표현 | 정규화 route label | 먼저 볼 문서 |
|---|---|---|
| `Location`이 `http://...`로 꺾임, `https://...`인데 host/origin이 틀림, proxy/LB 뒤에서만 redirect가 이상함 | `Location scheme / origin` | `1차 질문:` login 직후 `Location`이 public `https` origin인가? 아니면 `http://...`/wrong host인가? -> `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md) |
| `cookie-not-sent`, `stored but not sent`, `Application에는 있는데 request Cookie가 없음` | `cookie transfer` | `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md) |
| `server-mapping-missing`, `sent but anonymous`, `cookie는 갔는데 계속 anonymous` | `server persistence / session mapping` | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md) -> 필요하면 `[spring bridge anchor]` [Spring Security 예외 번역과 세션 경계](./contents/spring/README.md#spring-bridge-security-session-boundary) |
| `OIDC logout tail`, `logout tail`, `revoke tail`, `allowed after revoke` | `allowed-after-revoke / session-tail / revocation propagation` | `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md) |

로그인 루프 검색에서 canonical beginner entry route label은 `[canonical beginner entry route: login-loop]`다. 순서는 `[primer]` Login Redirect / `SavedRequest` -> `[primer bridge]` Browser `401` vs `302`다. HTTP state, Cookie/Session/JWT가 약하면 이 route 전에 해당 primer를 먼저 워밍업으로 본다. Spring `RequestCache`, `SecurityContextRepository`, BFF/session-store 문서는 이 bridge에서 증상을 나눈 뒤에만 deep dive로 내려간다.
cookie-focused shortcut도 같은 규칙을 쓴다. `blocked Set-Cookie`처럼 저장 단계가 먼저 보이면 `[primer]` [Cookie Rejection Reason Primer](./contents/security/cookie-rejection-reason-primer.md) -> `[primer bridge]` [Cookie Failure Three-Way Splitter](./contents/security/cookie-failure-three-way-splitter.md), `Application > Cookies`에는 보이는데 request `Cookie`가 비는 전송 단계면 `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md) -> `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./contents/security/duplicate-cookie-vs-proxy-login-loop-bridge.md) 순서를 먼저 고정한다.
login loop starter는 먼저 `Location` 1차 질문부터 고정한다. login 직후 redirect가 `http://...`로 꺾이거나 `https://...`인데 host/origin이 public 값과 다르면 cookie보다 먼저 `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md)으로 간다. `Location`이 정상일 때만 30초짜리 Network card로 내려가 `Status`/`Location`으로 `redirect 기억`, request `Cookie` header로 `cookie 전송`, cookie를 보냈는데도 익명이면 `server 복원`으로 자른다. 카드는 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md#30초-3-step-체크-카드)에 있다. 그다음 20초 공통 mini decision matrix로 좁힌다. `302 + /login`이면 `기억 / redirect`, `Application`에는 있는데 request `Cookie` header가 비면 `전송 / cookie-not-sent`, request `Cookie` header가 붙었는데도 계속 anonymous면 `조회 / server-anonymous`다. 같은 표는 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md#20초-트리아지-결정표)와 `[primer]` [Browser BFF Session Boundary Primer](./contents/system-design/browser-bff-session-boundary-primer.md#20초-트리아지-결정표)에 같은 wording으로 들어 있다.

redirect mismatch는 beginner가 가장 먼저 헷갈리는 갈래라서, `cookie`보다 앞에 `Location`을 한 번 더 본다. 첫 질문은 "이 `Location`이 `http://...`로 꺾였는가, 아니면 `https://...`인데 host/origin만 틀렸는가"다.

| `Location` 1차 질문 | 이렇게 보이면 | 바로 갈 문서 |
|---|---|---|
| scheme이 틀렸나 | `http://app.example.com/...` | `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md) -> `[primer]` [Secure Cookie Behind Proxy Guide](./contents/security/secure-cookie-behind-proxy-guide.md) |
| host/origin이 틀렸나 | `https://app-internal...`, `https://staging...` | `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md) -> `[primer]` [Absolute Redirect URL Behind Load Balancer Guide](./contents/security/absolute-redirect-url-behind-load-balancer-guide.md) |
| redirect는 정상인가 | `https://public-origin...`인데 다음 요청만 anonymous | 다시 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md)로 돌아가 `cookie transfer`와 `server persistence / session mapping`을 고른다. category entrypoint 복귀는 [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path) |

| 막히는 질문 | 먼저 볼 문서 | 다음 bridge |
|---|---|---|
| `redirect / navigation memory`부터 의심된다. `401`인지 `302`인지 헷갈리고, login loop / `SavedRequest` / hidden `JSESSIONID`가 섞인다 | `[canonical beginner entry route: login-loop]` `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md) | `[spring bridge anchor]` [Spring Security 예외 번역과 세션 경계](./contents/spring/README.md#spring-bridge-security-session-boundary) -> `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](./contents/spring/spring-security-requestcache-savedrequest-boundaries.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./contents/security/browser-bff-token-boundary-session-translation.md). category entrypoint로 돌아가려면 [Browser / Session Beginner Ladder](./contents/security/README.md#browser--session-beginner-ladder) -> [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path) |
| `cookie transfer`부터 의심된다. `cookie 있는데 다시 로그인`, `Application > Cookies`에는 값이 보이는데 request `Cookie` header가 비고, subdomain 이동이나 proxy/LB 뒤에서만 더 잘 깨진다 | `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md) | `[primer bridge]` [Duplicate Cookie vs Proxy Login Loop Bridge](./contents/security/duplicate-cookie-vs-proxy-login-loop-bridge.md)에서 `same-name cookie 중복`과 `wrong-scheme redirect / Secure cookie 미전송`을 먼저 자른다. bridge 뒤 duplicate면 `[primer]` [Duplicate Cookie Name Shadowing](./contents/security/duplicate-cookie-name-shadowing.md), wrong-scheme이면 `[primer]` [Secure Cookie Behind Proxy Guide](./contents/security/secure-cookie-behind-proxy-guide.md), request `Cookie`는 실리는데도 anonymous면 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md)로 한 칸만 더 내려간다. |
| `server persistence / session mapping`부터 의심된다. request `Cookie` header는 보이는데 서버가 계속 anonymous이고 login HTML로 되돌아가거나, `sent but anonymous`처럼 보인다 | `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md) | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md)에서 `sent but anonymous`를 고정한 뒤에만 `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./contents/security/browser-bff-token-boundary-session-translation.md) 순서로 내려간다. `request Cookie`가 실제로 보이는지부터 다시 확인해야 하면 `[primer bridge]` [Cookie Failure Three-Way Splitter](./contents/security/cookie-failure-three-way-splitter.md)로 잠깐 되돌아간다. |
| `왜 로그인 상태가 유지돼요?`, `cookie / session / JWT` 차이부터 다시 잡고 싶다 | `[primer]` [HTTP의 무상태성과 쿠키, 세션, 캐시](./contents/network/http-state-session-cache.md) -> `[primer]` [Cookie / Session / JWT 브라우저 흐름 입문](./contents/network/cookie-session-jwt-browser-flow-primer.md) | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `구글 로그인`, `social login`, `OAuth2냐 OIDC냐`가 먼저 헷갈리고, `auth/app subdomain` handoff 질문으로 바로 뛰기 전에 mental model부터 잡고 싶다 | `[primer]` [OAuth2 vs OIDC Social Login Primer](./contents/security/oauth2-oidc-social-login-primer.md) | social login callback 뒤 `auth.example.com -> app.example.com` handoff가 막히면 `[primer]` [Subdomain Callback Handoff Chooser](./contents/security/subdomain-callback-handoff-chooser.md)로 한 칸만 내려간다. callback의 `code` / `state` / PKCE hardening 자체가 궁금할 때만 `[primer bridge]` [OAuth2 Authorization Code Grant](./contents/security/oauth2-authorization-code-grant.md)로 간다. |
| login 뒤 redirect가 이상한데 `http://...`로 꺾인 건지, `app-internal`/staging 같은 wrong origin인지부터 헷갈린다 | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Wrong-Scheme vs Wrong-Origin Redirect Shortcut](./contents/security/wrong-scheme-vs-wrong-origin-redirect-shortcut.md) | `http://...`면 `[primer]` [Secure Cookie Behind Proxy Guide](./contents/security/secure-cookie-behind-proxy-guide.md), `https://...`인데 host/origin만 틀리면 `[primer]` [Absolute Redirect URL Behind Load Balancer Guide](./contents/security/absolute-redirect-url-behind-load-balancer-guide.md), `X-Forwarded-*` 신뢰 범위까지 헷갈리면 `[primer]` [Forwarded Header Trust Boundary Primer](./contents/security/forwarded-header-trust-boundary-primer.md)로 한 칸만 더 내려간다. |
| `auth.example.com/callback`은 성공했는데 `app.example.com` 첫 요청이 anonymous이고, shared-domain cookie인지 one-time handoff인지부터 헷갈린다 | `[primer]` [OAuth2 vs OIDC Social Login Primer](./contents/security/oauth2-oidc-social-login-primer.md) -> `[primer]` [Subdomain Callback Handoff Chooser](./contents/security/subdomain-callback-handoff-chooser.md) | chooser에서 shared cookie 기대면 `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md), handoff 기대면 `[primer bridge]` [Subdomain Login Callback Boundaries](./contents/security/subdomain-login-callback-boundaries.md)로 한 칸만 내려간다. external IdP/iframe 경유에서만 깨지면 `[primer bridge]` [SameSite Login Callback Primer](./contents/security/samesite-login-callback-primer.md)로 먼저 분기한다. |
| `cookie가 막힌 건지`, `저장만 되고 안 보내는 건지`, `보냈는데 서버가 못 읽는 건지`부터 헷갈린다 | `[primer]` [Cookie Rejection Reason Primer](./contents/security/cookie-rejection-reason-primer.md) | `[primer bridge]` [Cookie Failure Three-Way Splitter](./contents/security/cookie-failure-three-way-splitter.md)에서 `blocked Set-Cookie` / `stored but not sent` / `sent but anonymous`를 먼저 고정한다. root README handoff 이름으로는 `stored but not sent = cookie-not-sent = cookie transfer`, `sent but anonymous = server-mapping-missing = server persistence / session mapping`이다. 그다음 `cookie-not-sent`면 `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md), `server-mapping-missing`이면 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md)로 한 칸씩만 내려간다. |
| `로그아웃했는데 계속 된다`, `role`을 뺐는데 old session이 남는다, `revocation tail`이 의심된다 | `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md) | `[primer bridge]` [Claim Freshness After Permission Changes](./contents/security/claim-freshness-after-permission-changes.md) -> `[deep dive]` [Revocation Propagation Lag / Debugging](./contents/security/revocation-propagation-lag-debugging.md) -> `[recovery]` [Revocation Propagation Status Contract](./contents/security/revocation-propagation-status-contract.md) |
| `권한을 방금 줬는데 still 403`, `stale deny`, `cached 404 after grant`가 남는다 | `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md) | actual `GET`/`POST`의 `403`/`404`인지 먼저 확인한 뒤 stale deny로 읽는다. 그다음 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./contents/security/grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./contents/security/authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./contents/security/authz-cache-inconsistency-runtime-debugging.md) 순서로 내려가고, `OPTIONS`만 실패하거나 `/login` `302`/CORS 오진이면 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./contents/security/auth-failure-response-401-403-404.md)부터 다시 본다. |
| `tenant 이동/추가/제거` 뒤 old workspace가 남거나 새 tenant에서만 `403`이 난다 | `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md) | `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./contents/security/tenant-membership-change-session-scope-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./contents/security/authorization-caching-staleness.md) -> `[deep dive]` [Tenant Isolation / AuthZ Testing](./contents/security/tenant-isolation-authz-testing.md) |

revoke-tail beginner split도 같은 규칙을 쓴다. `allowed after revoke`, `logout still works`, `revoked admin still has access`는 allow tail이므로 `[primer bridge]` [Claim Freshness After Permission Changes](./contents/security/claim-freshness-after-permission-changes.md) 쪽으로 유지하고, `grant했는데 still 403`, `stale deny`, `cached 404 after grant`는 deny tail이므로 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./contents/security/grant-path-freshness-stale-deny-basics.md) 쪽으로 유지한다. 둘을 섞은 채 deep dive부터 열지 않는다.

- 같은 beginner route를 category entrypoint에서 더 넓게 보고 싶으면 [Browser / Session Beginner Ladder](./contents/security/README.md#browser--session-beginner-ladder)에서 먼저 증상 이름을 맞춘 뒤 [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path)로 이어 간다.
- session-store나 large-scale cutover 설계까지 올라가면 [Auth Session Troubleshooting Bridge](./contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge)로 handoff한다.

<a id="symptom-first-quick-routes"></a>

### Symptom-First Primer Bridge Routes

이 소제목의 역할은 "증상 문장을 beginner-safe 첫 문서로 번역하는 `primer bridge` 선반"이다.
아직 `why`, `처음`, `뭐예요`, `basics` 단계라면 아래 bullet에서도 `[primer]`나 `[primer bridge]`부터 먼저 잡고, `[playbook]`, `[recovery]`, `[master note]`, `[system design]`는 follow-up으로 미룬다.

| 지금 검색한 문장 | 여기서 먼저 붙일 역할 | 첫 클릭으로 미루는 것 |
|---|---|---|
| `로그인 됐는데 왜 403`, `cookie 있는데 다시 로그인`, `stale read` | `primer` / `primer bridge` | `recovery`, `cutover`, `master note` |
| `증상은 있는데 어느 카테고리인지 모르겠다` | `catalog` / `cross-category bridge` | 여러 deep dive 동시 열기 |
| `지금 장애 복구 순서가 먼저 필요하다` | `playbook` / `recovery` | broad primer 재시작 |

루트 진입점에서도 자주 들어오는 증상 질의를 바로 route할 수 있게, 아래 route 묶음들은 [Master Notes](./master-notes/README.md), [Query Playbook](./rag/query-playbook.md), [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md), category bridge `README` 기준을 한 번에 붙여 둔다.

junior reader라면 이 구간을 아래 순서로 읽는다.

- 첫 클릭은 가능하면 `[primer]`, `[primer bridge]`, `[catalog]`, `[cross-category bridge]` 중 하나로 잡는다.
- 같은 bullet에 `[master note]`, `[playbook]`, `[recovery]`, `[system design]`가 같이 보여도, 그 링크들은 대개 범위를 넓히거나 incident/설계 단계로 넘어갈 때의 follow-up이다.
- `master note`가 먼저 적혀 있어도 "기초 개념을 처음 잡는 문서"라는 뜻은 아니다. 초보자라면 bullet 안의 beginner-safe starter 문장부터 다시 확인한다.

- `stale read`, `stale-read`, `read-after-write`, `방금 썼는데 조회가 옛값`, `replica lag`부터 떠오르면 beginner-safe first click은 [Read-After-Write Consistency Basics](./contents/system-design/read-after-write-consistency-basics.md) 또는 [Caching vs Read Replica Primer](./contents/system-design/caching-vs-read-replica-primer.md)다. 그다음 `[primer bridge]` [Design Pattern: Read Model Staleness and Read-Your-Writes](./contents/design-pattern/read-model-staleness-read-your-writes.md)로 symptom 언어를 맞추고, 범위를 넓혀야 할 때만 `[master note]` [Replica Freshness Master Note](./master-notes/replica-freshness-master-note.md), `[master note]` [Consistency Boundary Master Note](./master-notes/consistency-boundary-master-note.md)를 붙인다. cutover/verification까지 가야 하면 마지막에 [Incremental Summary Table Refresh and Watermark Discipline](./contents/database/incremental-summary-table-refresh-watermark.md) -> [Dual-Read Comparison / Verification Platform 설계](./contents/system-design/dual-read-comparison-verification-platform-design.md) 순으로 내려간다.
- `dirty read`, `lost update`, `write skew`, `phantom`, `@Transactional`, `왜 안 롤백되지`, `self invocation`, `checked exception commit`, `lock wait`, `deadlock`, `UnexpectedRollbackException`이 같이 나오면 beginner split은 먼저 [트랜잭션 기초](./contents/database/transaction-basics.md) -> [트랜잭션 격리 수준 기초](./contents/database/transaction-isolation-basics.md) -> [@Transactional 기초](./contents/spring/spring-transactional-basics.md)다. 증상을 transaction vs Spring proxy로 먼저 갈라야 할 때만 [DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표](./contents/spring/spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix.md)를 붙이고, 여러 카테고리를 한 번에 묶어 설명해야 할 때만 `[master note]` [Database to Spring Transaction Master Note](./master-notes/database-to-spring-transaction-master-note.md)로 올라간다. core deep dive는 그다음 [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md) -> [@Transactional 깊이 파기](./contents/spring/transactional-deep-dive.md) -> [Spring Service-Layer Transaction Boundary Patterns](./contents/spring/spring-service-layer-transaction-boundary-patterns.md) 순으로 맞춘다.
  - core ladder 뒤 beginner branch는 역할을 `[primer bridge]`로 먼저 고정한 뒤 증상별로 나눈다.
  - `audit는 남고 본 작업은 롤백`, `REQUIRES_NEW`, `partial commit`이면 [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md) -> [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./contents/spring/spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
  - `UnexpectedRollbackException`, `transaction marked rollback-only`, `catch 했는데 마지막에 터짐`이면 [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md) -> [Spring Transaction Debugging Playbook](./contents/spring/spring-transaction-debugging-playbook.md)
  - `readOnly면 안전한가`, `dirty checking`, `flush mode`가 헷갈리면 [Spring Transaction Isolation / ReadOnly Pitfalls](./contents/spring/spring-transaction-isolation-readonly-pitfalls.md)
  - `inner readOnly인데 writer pool`, `reader route가 안 탄다`, `read/write split`이면 [Spring Routing DataSource Read/Write Transaction Boundaries](./contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md)
- `499`, `client disconnect`, `client-disconnect`, `broken pipe`, `cancelled request`, `zombie work`가 섞이면 [Network Failure Handling Master Note](./master-notes/network-failure-handling-master-note.md), [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md)로 hop별 종료 지점과 retry 증폭 여부를 먼저 보고, bridge route는 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) -> [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md) -> [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) 순으로 붙인다.
- `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `upstream reset`이 먼저 보이면 [Edge Request Lifecycle Master Note](./master-notes/edge-request-lifecycle-master-note.md), [Network Failure Handling Master Note](./master-notes/network-failure-handling-master-note.md)로 edge/app 관측 ownership을 먼저 고정하고, bridge route는 [Proxy Local Reply vs Upstream Error Attribution](./contents/network/proxy-local-reply-vs-upstream-error-attribution.md) -> [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md) -> [Service Mesh Local Reply, Timeout, Reset Attribution](./contents/network/service-mesh-local-reply-timeout-reset-attribution.md) 순으로 붙인다.
- `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200`이 보이면 [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md), [Edge Request Lifecycle Master Note](./master-notes/edge-request-lifecycle-master-note.md)로 hop budget과 종료 순서를 먼저 잡고, bridge route는 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) -> [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) -> [Idle Timeout Mismatch: LB / Proxy / App](./contents/network/idle-timeout-mismatch-lb-proxy-app.md) -> [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md) 순으로 붙인다.
- `auth verification outage`, `JWKS outage`, `invalid signature`, `kid miss`, `unable to find JWK`, `stale JWKS cache`가 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)로 auth state와 trust 경계를 먼저 잡고, security route label은 `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust)로 맞춘다. bridge route는 `[playbook]` [JWT Signature Verification Failure Playbook](./contents/security/jwt-signature-verification-failure-playbook.md) -> `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./contents/security/jwt-jwks-outage-recovery-failover-drills.md) -> `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./contents/security/auth-incident-triage-blast-radius-recovery-matrix.md) -> `[system design]` [Security / System-Design Incident Bridge](./contents/system-design/README.md#system-design-security-incident-bridge) -> `[system design]` [Service Discovery / Health Routing 설계](./contents/system-design/service-discovery-health-routing-design.md) 순으로 붙인다.
- `auth-outage`, `auth outage`, `login loop`, `302 login loop`, `hidden session mismatch`, `SavedRequest 때문에 login loop가 난다`, `sid mapping`, `post-login session persistence`, `logout token은 오는데 spring 앱 세션을 못 찾는다`, `cookie drop`, `session store outage`가 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Browser Auth Frontend Backend Master Note](./master-notes/browser-auth-frontend-backend-master-note.md)로 browser/BFF/session state를 먼저 잡고, security route label은 `[catalog]` [Browser / Session Beginner Ladder](./contents/security/README.md#browser--session-beginner-ladder) -> `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path) -> `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay) 순으로 읽는다. beginner canonical entry route는 [Auth / Session Beginner Shortcut](#auth--session-beginner-shortcut)의 `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md) 순서로 고정한다. bridge route는 request `Cookie` header가 비면 `[primer]` [Cookie Scope Mismatch Guide](./contents/security/cookie-scope-mismatch-guide.md), redirect `Location`이나 다음 요청 URL이 `http://...`로 꺾이거나 proxy/LB 뒤에서만 재현되면 `[primer]` [Secure Cookie Behind Proxy Guide](./contents/security/secure-cookie-behind-proxy-guide.md), request `Cookie` header가 실제로 실리면 `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](./contents/spring/spring-security-requestcache-savedrequest-boundaries.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./contents/security/browser-bff-token-boundary-session-translation.md) -> `[recovery]` [BFF Session Store Outage / Degradation Recovery](./contents/security/bff-session-store-outage-degradation-recovery.md) -> `[system design]` [Auth Session Troubleshooting Bridge](./contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge) -> `[system design]` [Session Store Design at Scale](./contents/system-design/session-store-design-at-scale.md) 순으로 붙인다.
- `revoke lag`, `logout still works`, `logout tail`, `allowed after revoke`, `revoked admin still has access`, `revocation tail`이 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Authz and Permission Master Note](./master-notes/authz-and-permission-master-note.md)로 session freshness와 permission fallout을 먼저 묶고, security route label은 `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path) -> `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay)다. bridge route는 `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./contents/security/claim-freshness-after-permission-changes.md) -> `[deep dive]` [Revocation Propagation Lag / Debugging](./contents/security/revocation-propagation-lag-debugging.md) -> `[deep dive]` [Session Revocation at Scale](./contents/security/session-revocation-at-scale.md) -> `[deep dive]` [Revocation Propagation Status Contract](./contents/security/revocation-propagation-status-contract.md) -> `[system design]` [Session Store / Claim-Version Cutover 설계](./contents/system-design/session-store-claim-version-cutover-design.md) -> `[system design]` [Canonical Revocation Plane Across Token Generations](./contents/system-design/canonical-revocation-plane-across-token-generations-design.md) -> `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](./contents/system-design/revocation-bus-regional-lag-recovery-design.md) 순으로 붙인다.
- `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `403 after revoke`, `cached 404 after grant`이 먼저 보이면 [Authz and Permission Master Note](./master-notes/authz-and-permission-master-note.md)로 authz cache와 concealment 경계를 먼저 잡고, security route label은 `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)다. beginner-safe route는 category README와 같은 primer-first handoff를 쓴다. 먼저 `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md)로 mental model을 맞추고, 바로 다음 한 장은 기본값으로 `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./contents/security/grant-path-freshness-stale-deny-basics.md)에서 고른다. 응답 코드 의미부터 흔들릴 때만 그 앞에 `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./contents/security/auth-failure-response-401-403-404.md)를 끼워 넣고, 그다음에만 `[deep dive]` [Authorization Caching / Staleness](./contents/security/authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./contents/security/authz-cache-inconsistency-runtime-debugging.md) 순으로 내려간다. `tenant membership이 바뀐 뒤 특정 workspace만 403`이면 같은 `[primer]` 다음 단계로 `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./contents/security/tenant-membership-change-session-scope-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./contents/security/authorization-caching-staleness.md) -> `[deep dive]` [Tenant Isolation / AuthZ Testing](./contents/security/tenant-isolation-authz-testing.md)으로 갈라진다. `grant했는데 still 403`처럼 freshness symptom이 먼저면 같은 `[primer bridge]`에서 시작해 `[deep dive]` [Authorization Caching / Staleness](./contents/security/authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Negative Cache Failure Case Study](./contents/security/authz-negative-cache-failure-case-study.md)로 이어 붙인다. category symptom table로 돌아가 다시 분기하려면 [Security README: 증상별 바로 가기](./contents/security/README.md#증상별-바로-가기)를 본다.
- `missing-audit-trail`, `audit trail이 없다`, `누가 허용/거부했는지 안 남는다`, `decision log missing`, `auth-signal-gap`, `allow/deny reason code가 안 보인다`, `401/403 spike인데 reason bucket이 없다`가 먼저 보이면 `[master note]` [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), `[master note]` [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)로 auth evidence/telemetry 경계를 먼저 잡고, security route label은 `[catalog]` [운영 / Incident catalog](./contents/security/README.md#운영--incident-catalog) -> `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)다. beginner-safe bridge route는 `[primer bridge]` [Auth Observability Primer Bridge](./contents/security/auth-observability-primer-bridge.md)로 `signal / decision / audit` 3칸을 먼저 고정한 뒤 `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./contents/security/auth-observability-sli-slo-alerting.md) -> `[deep dive]` [AuthZ Decision Logging Design](./contents/security/authz-decision-logging-design.md) -> `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./contents/security/audit-logging-auth-authz-traceability.md) -> `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./contents/security/authorization-runtime-signals-shadow-evaluation.md) 순으로 붙인다.
- `replay store down`, `nonce store down`, `duplicate request after retry`, `replay-safe retry`, `backfill replay`가 섞이면 [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md)를 먼저 보고, 저장소 replay/backfill/repair 축이 더 크면 [Data Pipeline Replay Master Note](./master-notes/data-pipeline-replay-master-note.md), [Eventual Consistency Master Note](./master-notes/eventual-consistency-master-note.md)로 이어진다. security route label은 `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay)로 맞추고, bridge route는 `[recovery]` [Replay Store Outage / Degradation Recovery](./contents/security/replay-store-outage-degradation-recovery.md) -> `[system design]` [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md) -> `[system design]` [Replay / Repair Orchestration Control Plane 설계](./contents/system-design/replay-repair-orchestration-control-plane-design.md) 순으로 붙인다.
- `authority transfer`, `SCIM deprovision`, `SCIM disable은 끝났는데 access shutdown 설명이 안 맞음`, `backfill is green but access tail remains`, `decision parity`, `auth shadow divergence`, `deprovision tail`, `cleanup evidence`, `retirement evidence`, `decision log join key`, `audit evidence bundle`가 보이면 beginner-safe starter를 `[primer]` [Identity Lifecycle / Provisioning Primer](./contents/security/identity-lifecycle-provisioning-primer.md) -> `[primer]` [Role Change and Session Freshness Basics](./contents/security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Claim Freshness After Permission Changes](./contents/security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](./contents/database/README.md#database-bridge-identity-authority) -> `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle) 순으로 먼저 고정한 뒤 `[system design]` [Database / Security Authority Bridge](./contents/system-design/README.md#system-design-database-security-authority-bridge) -> `[system design]` [Verification / Shadowing / Authority Bridge](./contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)로 넘긴다. 한 줄 mental model은 "DB row parity가 green이어도 security runtime access tail은 남을 수 있다"다. bridge에서 owner를 고정한 뒤에만 `[deep dive]` [Online Backfill Verification, Drift Checks, and Cutover Gates](./contents/database/online-backfill-verification-cutover-gates.md) -> `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./contents/security/scim-deprovisioning-session-authz-consistency.md) -> `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./contents/security/authorization-runtime-signals-shadow-evaluation.md) -> `[system design]` [Database / Security Identity Bridge Cutover 설계](./contents/system-design/database-security-identity-bridge-cutover-design.md)를 붙이고, 범위가 커질 때는 `[survey]` [추천 학습 흐름 (category-local survey)](./contents/security/README.md#추천-학습-흐름-category-local-survey)에서 `SCIM / Lifecycle / Drift` branch를 먼저 훑는다. cutover 승격/조직 owner 경계까지 커질 때만 `[master note]` [Migration Cutover Master Note](./master-notes/migration-cutover-master-note.md)와 `[master note]` [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)를 추가한다.
- `acting on behalf of`, `break glass`, `delegated admin`, `support access notification`이 보이면 beginner-safe first click은 `[primer]` [Support Access Alert Router Primer](./contents/security/support-access-alert-router-primer.md) -> `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle)다. `[master note]` [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)는 "지원자 권한 위임, 책임 경계, 신뢰 모델을 한 번에 묶어야 할 때"만 범위 확장용으로 붙인다. 그다음에만 `[deep dive]` [Support Operator / Acting-on-Behalf-Of Controls](./contents/security/support-operator-acting-on-behalf-of-controls.md) -> `[deep dive]` [Customer-Facing Support Access Notifications](./contents/security/customer-facing-support-access-notifications.md) -> `[deep dive]` [Audience Matrix for Support Access Events](./contents/security/audience-matrix-for-support-access-events.md) -> `[deep dive]` [Incident-Close Break-Glass Gate](./contents/security/incident-close-break-glass-gate.md) 순으로 붙인다.
- `trust bundle rollback`, `hardware attestation failure`, `trust bundle recovery`가 보이면 junior first click은 `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust) -> `[catalog]` [Hardware Trust / Recovery deep dive catalog](./contents/security/README.md#hardware-trust--recovery-deep-dive-catalog)다. 여기서 "지금 장애 대응 순서가 먼저 필요한지"와 "hardening / rollout 문서를 읽을지"를 먼저 고른다. 그다음 bridge route로 `[deep dive]` [mTLS Certificate Rotation / Trust Bundle Rollout](./contents/security/mtls-certificate-rotation-trust-bundle-rollout.md) -> `[recovery]` [Hardware Attestation Policy / Failure Recovery](./contents/security/hardware-attestation-policy-failure-recovery.md) -> `[system design]` [Trust-Bundle Rollback During Cell Cutover 설계](./contents/system-design/trust-bundle-rollback-during-cell-cutover-design.md) 순으로 붙이고, 여러 trust/cutover incident를 함께 묶을 때만 `[master note]` [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)와 [Migration Cutover Master Note](./master-notes/migration-cutover-master-note.md)를 추가한다.

## Junior Backend Roadmap (`survey`)

- [신입 백엔드 CS 학습 순서 가이드](./JUNIOR-BACKEND-ROADMAP.md)

이 구간은 beginner-safe entrypoint다. 큰 그림을 먼저 잡고 category `README`나 primer로 내려갈 때 연다.
루트에서 "처음인데 뭐부터 보죠?"라면 기본값으로 여기서 시작하면 된다.

## Advanced Backend Roadmap (`survey`, advanced)

- [백엔드 심화 학습 순서 가이드](./ADVANCED-BACKEND-ROADMAP.md)

이 구간은 심화 survey다. incident, cutover, control-plane, synthesis를 바로 읽고 싶은 junior 이상 독자에게 맞고, 초보자는 먼저 `JUNIOR-BACKEND-ROADMAP`이나 category `README` primer에서 시작하는 편이 안전하다.
즉 `survey` 역할은 같아도, 이 섹션은 beginner 첫 클릭이 아니라 follow-up shelf다.

## Master Notes (`synthesis`, advanced)

- [마스터노트 인덱스](./master-notes/README.md)
- [Master Notes 안내](./MASTER-NOTES.md)

이 구간은 여러 카테고리를 한 번에 묶는 synthesis entrypoint다. beginner의 첫 클릭보다는, primer나 category README를 읽은 뒤 "왜 이게 여러 레이어에 걸리는지"를 묶고 싶을 때 연다.
루트에서 바로 열기보다 `survey -> category README -> primer`를 지난 뒤 범위를 넓힐 때 여는 편이 안전하다.

추천 주제:

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

## Senior-Level Questions (`question bank`, advanced)

- [시니어 레벨 질문 모음](./SENIOR-QUESTIONS.md)

이 구간은 설명 본문이 아니라 self-check용 question bank다. 막히는 질문이 나오면 다시 `primer`나 `deep dive` 본문으로 돌아간다.
첫 클릭으로 쓰기보다, 이미 읽은 내용을 점검하는 follow-up 용도라고 보면 된다.

## RAG Ready (`routing helper`)

이 구간은 개념 primer가 아니라 `routing helper / retrieval helper` entrypoint다.
검색 규칙, 역할 라벨, query 확장 키워드가 필요할 때 열고, 설명 본문은 다시 category `README`나 개별 `primer` / `deep dive`로 내려간다.

즉 `rag/*.md`는 "무엇을 읽을지 고르는 곳"이지, advanced incident 문서를 beginner 첫 클릭으로 올려 주는 shelf가 아니다.

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
| 문서 역할 판별 | `rag/navigation-taxonomy.md` |
| `playbook` / `runbook` / `drill` / `incident matrix` badge 구분 | `rag/navigation-taxonomy.md#incident-badge-vocabulary`, incident-heavy 카테고리 `README.md` |
| 역할이 헷갈리면서 범위도 넓다 | `rag/navigation-taxonomy.md`, `rag/query-playbook.md`, `master-notes/README.md` |
| 카테고리 진입점 찾기 | 루트 `README.md`, 각 카테고리 `README.md` |
| 교차 도메인 맥락 잡기 | `master-notes/README.md`, 대표 master note 문서 |
| 질문 bank로 점검하기 | `SENIOR-QUESTIONS.md` |
| 증상 기반 키워드 확장 | `rag/retrieval-anchor-keywords.md`, `rag/query-playbook.md` |
| 검색 라우팅 잡기 | `rag/topic-map.md`, `rag/query-playbook.md`, `rag/cross-domain-bridge-map.md` |

RAG 문서에서 멈추지 않는 안전 규칙도 같이 둔다.

- `rag/*.md`를 읽고 나면 다음 클릭은 가능하면 category `README`, `primer`, `primer bridge` 중 하나로 잡는다.
- `playbook`, `runbook`, `drill`, `recovery`가 검색 결과에 먼저 보여도, 지금 질문이 beginner `what is` / `처음` / `헷갈려요` 계열이면 entrypoint로 바로 열지 않는다.
- 검색어가 `문서 역할`, `roadmap`, `README 차이`, `primer vs deep dive`, `incident badge`처럼 taxonomy 성격이면 이 구간에 머물고, 개념 질문이면 다시 본문으로 내려간다.

## Category Catalog Snapshots (`catalog snapshot`)

아래 대분류 섹션들은 루트 `README`에 남겨 둔 **catalog snapshot**이다.

- 학습 순서를 고르려면 roadmap 같은 `survey`로 돌아간다.
- 설명 본문이 필요하면 각 카테고리 `README`의 `primer` 또는 개별 `deep dive` 문서로 내려간다.
- 교차 도메인 묶음이 필요하면 `master note`, self-check가 목적이면 `question bank`로 이동한다.
- beginner라면 snapshot에서 고른 다음 첫 문서는 가능하면 각 카테고리 `README`의 `primer`나 `quick start`여야 한다.
- snapshot 안의 `playbook`, `runbook`, `drill`, `recovery`, incident-heavy deep dive는 entrypoint가 아니라 follow-up으로 읽는다.
- 루트 snapshot heading도 generic `정리노트`보다 `카테고리 README` / `category navigator` 같은 역할명이 바로 보이게 유지한다.
- 링크를 연 다음에도 상단 역할 라벨(`primer`, `catalog`, `deep dive`, `question bank`)을 다시 확인한다.
- 역할 이름이 헷갈리면 [Navigation Taxonomy](./rag/navigation-taxonomy.md)에서 `survey / primer / catalog / deep dive` 경계를 다시 확인하고, incident 라벨이 섞이면 [Incident Badge Vocabulary](./rag/navigation-taxonomy.md#incident-badge-vocabulary)를 본다.

처음 보는 주제라면 snapshot을 이렇게 해석하면 안전하다.

| 지금 상태 | snapshot에서 고를 첫 링크 | 아직 미루는 링크 |
|---|---|---|
| `처음`, `뭐예요`, `what is`, `basics` | category `README`, `primer`, `quick start` | incident-heavy `playbook`, `recovery`, 설계 deep dive |
| 증상 이름은 있는데 원인 축이 헷갈림 | `primer bridge`, symptom-first `catalog` | broad `master note`, 운영 절차 문서 |
| 이미 기본 개념은 있고 한 경계를 깊게 파고 싶음 | `deep dive` | unrelated survey 재시작 |

snapshot에서 raw topic 이름만 길게 보이면, 바로 개별 심화 문서로 뛰지 말고 같은 category `README` 안의 `primer` / `첫 분기` / `응용 catalog` anchor를 먼저 고르는 편이 beginner-safe 하다.

## Data Structure (자료구조)

### [📖 자료구조 README](./contents/data-structure/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [처음 15분 읽기 루트](./contents/data-structure/README.md#처음-15분-읽기-루트), [증상별 빠른 길](./contents/data-structure/README.md#증상별-빠른-길) | `map / set / queue / deque / treemap` 첫 분기를 먼저 자른다 |
| `catalog / navigator` | [초급 10초 라우터](./contents/data-structure/README.md#초급-10초-라우터), [기본 primer](./contents/data-structure/README.md#기본-primer) | raw topic 이름보다 "지금 질문 문장" 기준으로 다시 고를 수 있다 |
| `deep dive` follow-up | [응용 catalog](./contents/data-structure/README.md#응용-catalog) | `Trie`, `Heap`, `Union-Find`, `LRU`, `Segment Tree`는 입문 분기 뒤에 필요한 것만 내려간다 |

[🔝 목차로 돌아가기](#table-of-contents)

## 한 줄 정리

루트 `README`는 답 자체를 주는 본문보다 `survey -> primer -> primer bridge -> deep dive` 순서로 안전한 다음 문서를 고르게 만드는 meta navigator로 읽는 것이 가장 안전하다.

## Algorithm (알고리즘)

### [📖 알고리즘 README](./contents/algorithm/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [초보자 첫 분기](./contents/algorithm/README.md#초보자-첫-분기), [처음 15분 읽기 루트](./contents/algorithm/README.md#처음-15분-읽기-루트) | `BFS / binary search / two pointer / brute force` 첫 분기를 먼저 자른다 |
| `primer bridge` | [BFS, Queue, Map 먼저 분리하기](./contents/algorithm/README.md#bfs-queue-map-먼저-분리하기) | `queue가 도구인지`, `BFS가 문제 유형인지` 섞인 질문을 먼저 푼다 |
| `deep dive` follow-up | [심화로 내려가는 기준](./contents/algorithm/README.md#심화로-내려가는-기준), [패턴 / 비교 카탈로그](./contents/algorithm/README.md#패턴--비교-카탈로그) | `MST`, `위상 정렬`, `가중치 shortest path`는 입문 분기 뒤에 필요한 것만 내려간다 |

- `MST`, `minimum spanning tree`, `connect all nodes minimum cost`, `connect all cities minimum cost`, `모든 정점을 최소 비용으로 연결`, `Prim vs Kruskal`처럼 전체 연결 비용 질문은 beginner primer를 지난 뒤 [Minimum Spanning Tree: Prim vs Kruskal](./contents/algorithm/minimum-spanning-tree-prim-vs-kruskal.md)로 내려간다.

[🔝 목차로 돌아가기](#table-of-contents)

## Operating System (운영체제)

### [📖 운영체제 README](./contents/operating-system/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [입문 primer](./contents/operating-system/README.md#입문-primer), [먼저 잡는 멘탈 모델](./contents/operating-system/README.md#먼저-잡는-멘탈-모델) | `프로세스 / 스레드 / 스케줄링 / 가상 메모리` 큰 그림을 먼저 잡고 runtime 용어를 덜 섞게 한다 |
| `catalog / navigator` | [빠른 탐색](./contents/operating-system/README.md#빠른-탐색), [역할별 라우팅 요약](./contents/operating-system/README.md#역할별-라우팅-요약) | `runtime`, `memory`, `container`, `diagnostics` 중 지금 질문 축만 먼저 고를 수 있다 |
| `deep dive` follow-up | [현대 runtime catalog](./contents/operating-system/README.md#현대-runtime-catalog) | `futex`, `off-CPU`, `epoll`, `io_uring`, `cgroup pressure`는 primer 뒤에 필요한 축만 내려간다 |

- `처음`, `스레드가 뭐예요`, `왜 느려요`처럼 broad하면 primer부터 간다.
- 운영체제 README 안의 `[playbook]`과 runtime diagnostics 링크는 entrypoint가 아니라 follow-up shelf다.
- `OOM`, `page cache`, `eBPF`, `perf`, `pressure stall`은 첫 클릭보다 운영/진단 follow-up shelf로 본다.

[🔝 목차로 돌아가기](#table-of-contents)

## Database (데이터베이스)

### [📖 데이터베이스 README](./contents/database/README.md) (`category navigator` snapshot)

- `survey`: [추천 학습 흐름 (category-local survey)](./contents/database/README.md#추천-학습-흐름-category-local-survey)에서 `Transaction / Locking / Invariant`, `Query Plan / Index / Write Path`, `Schema Migration / CDC / Replay`, `Replica / Failover / Freshness`, `Lifecycle / Cleanup / Drift` 순으로 큰 흐름을 잡는다.
- `navigator entrypoint`: [빠른 탐색](./contents/database/README.md#빠른-탐색), [역할별 라우팅 요약](./contents/database/README.md#역할별-라우팅-요약)에서 `survey / primer / catalog / playbook-runbook / taxonomy` 중 어디로 바로 들어갈지 고른다.
- `primer`: [Database First-Step Bridge](./contents/database/database-first-step-bridge.md), [트랜잭션 기초](./contents/database/transaction-basics.md), [JDBC · JPA · MyBatis 기초](./contents/database/jdbc-jpa-mybatis-basics.md)
- `primer follow-up`: 동시성/조회 성능 질문이 붙을 때만 [트랜잭션 격리 수준 기초](./contents/database/transaction-isolation-basics.md), [인덱스 기초](./contents/database/index-basics.md)
- `deep dive catalog`: [현대 catalog](./contents/database/README.md#현대-catalog), [트랜잭션 격리수준과 락](./contents/database/README.md#트랜잭션-격리수준과-락), [Schema Migration, Partitioning, CDC, CQRS](./contents/database/README.md#schema-migration-partitioning-cdc-cqrs), [Authority Transfer / Security Bridge](./contents/database/README.md#authority-transfer--security-bridge), [Replica Lag와 Read-after-Write](./contents/database/README.md#replica-lag와-read-after-write), [Vacuum / Purge Debt](./contents/database/README.md#vacuum--purge-debt)
- `cross-category bridge`: authority-transfer symptom은 [Identity / Authority Transfer 브리지](./contents/database/README.md#database-bridge-identity-authority)에서 row/backfill parity를 먼저 잡고, [Security: Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle), [System Design: Database / Security Authority Bridge](./contents/system-design/README.md#system-design-database-security-authority-bridge), [Verification / Shadowing / Authority Bridge](./contents/system-design/README.md#system-design-verification-shadowing-authority-bridge) 순으로 넘긴다.
- `playbook / runbook`: [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./contents/database/lock-wait-deadlock-latch-triage-playbook.md), [느린 쿼리 분석 플레이북](./contents/database/slow-query-analysis-playbook.md), [Expired-Unreleased Drift Runbook](./contents/database/expired-unreleased-drift-runbook.md), [CDC Replay Verification, Idempotency, and Acceptance Runbook](./contents/database/cdc-replay-verification-idempotency-runbook.md)

[🔝 목차로 돌아가기](#table-of-contents)

## Network (네트워크)

### [📖 네트워크 README](./contents/network/README.md) (`category navigator` snapshot)

- `survey`: [추천 학습 흐름 (category-local survey)](./contents/network/README.md#추천-학습-흐름-category-local-survey)에서 `TCP / HTTP Version Progression`, `Proxy / Mesh / Trust Boundary`, `Timeout / Queueing / Overload`, `Streaming / Disconnect / Cancellation`, `Cache / DNS / Edge Variation` 순으로 큰 흐름을 잡는다.
- `routing summary`: [역할별 라우팅 요약](./contents/network/README.md#역할별-라우팅-요약)에서 `survey / primer / catalog / playbook-runbook / taxonomy` 중 어디로 바로 들어갈지 고른다.
- `primer`: [레거시 primer](./contents/network/README.md#레거시-primer), [보조 primer](./contents/network/README.md#보조-primer)에서 `OSI`, `TCP handshake`, `TCP vs UDP`, `웹 통신의 흐름` 같은 입문 축을 먼저 잡고 primer 내부 anchor로 더 내려간다.
- `deep dive catalog`: [현대 topic catalog](./contents/network/README.md#현대-topic-catalog)에서 `HTTP/2 / gRPC`, `TLS / Proxy / Mesh`, `Timeout / Queueing / Overload`, `Streaming / Disconnect / Cancellation`, `Cache / DNS / Edge Variation` bucket 중 필요한 축을 고른다.
- `playbook / runbook`: [Cache, Vary, Accept-Encoding Edge Case Playbook](./contents/network/cache-vary-accept-encoding-edge-case-playbook.md), [Queue Saturation Attribution, Metrics, Runbook](./contents/network/queue-saturation-attribution-metrics-runbook.md), [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md), [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./contents/network/sse-failure-attribution-http1-http2.md)

[🔝 목차로 돌아가기](#table-of-contents)

## Design Pattern (디자인 패턴)

### [📖 디자인 패턴 README](./contents/design-pattern/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [Beginner 시작 순서](./contents/design-pattern/README.md#beginner-시작-순서), [Beginner primer 모음](./contents/design-pattern/README.md#beginner-primer-모음) | `객체지향 핵심 원리 -> 상속보다 조합 -> 패턴 기초` 사다리를 먼저 고정한다 |
| `primer bridge` | [Template Method beginner route](./contents/design-pattern/README.md#template-method-beginner-route), [선택 기준부터 보는 진입](./contents/design-pattern/README.md#선택-기준부터-보는-진입) | `템플릿 메소드 vs 전략`, `factory vs selector`처럼 이름이 섞인 질문을 먼저 자른다 |
| `deep dive` follow-up | [고전 패턴 primer](./contents/design-pattern/README.md#고전-패턴-primer), [백엔드 / DDD catalog](./contents/design-pattern/README.md#백엔드--ddd-catalog) | `Decorator`, `Observer`, `ACL`, `Projection` 같은 패턴/운영 문서는 primer 뒤에 필요한 것만 확장한다 |

- beginner pattern route map은 `조합 -> 템플릿 메소드 -> 전략 -> 어댑터`다.
- `Projection`, `cutover`, `playbook`, `read model`이 보이면 패턴 입문이 아니라 advanced follow-up shelf로 읽는다.

[🔝 목차로 돌아가기](#table-of-contents)

## Software Engineering (소프트웨어 공학)

### [📖 소프트웨어 공학 README](./contents/software-engineering/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [역할별 시작선](./contents/software-engineering/README.md#역할별-시작선), [Beginner Starter Quick Path](./contents/software-engineering/README.md#beginner-starter-quick-path), [우테코 백엔드 미션 선행 개념 입문](./contents/software-engineering/woowacourse-backend-mission-prerequisite-primer.md) | `레이어 / 테스트 / 객체지향 / 리팩토링` 첫 축을 먼저 맞춘다 |
| `survey` | [기초 survey 입구](./contents/software-engineering/README.md#기초-survey-입구), [Beginner 30-Minute Entry Subset](./contents/software-engineering/README.md#beginner-30-minute-entry-subset) | broad topic을 한 번에 펼치지 않고 `아키텍처 / persistence / API / 테스트` 중 필요한 묶음만 고를 수 있다 |
| `deep dive` follow-up | [deep dive 바로가기](./contents/software-engineering/README.md#deep-dive-바로가기), [거버넌스/운영 deep dive 바로가기 (starter 이후)](./contents/software-engineering/README.md#거버넌스운영-deep-dive-바로가기-starter-이후) | `DDD`, `CQRS`, `cutover`, `거버넌스`는 starter 이후에 필요한 축만 확장한다 |

- `처음`, `리뷰가 헷갈려요`, `테스트를 어디서부터 읽죠` 같은 질문은 primer route가 안전하다.
- `MSA`, `event sourcing`, `cutover`, `governance`는 useful해도 beginner 첫 클릭은 아니다.

[🔝 목차로 돌아가기](#table-of-contents)

## Spring Framework (스프링 프레임워크)

### [📖 스프링 README](./contents/spring/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [처음 20분 루트](./contents/spring/README.md#처음-20분-루트), [처음 10분 라우트](./contents/spring/README.md#처음-10분-라우트), [Beginner 입문 5편](./contents/spring/README.md#beginner-입문-5편) | `요청 흐름 -> Bean/DI -> MVC -> 트랜잭션` 순서를 먼저 잡아 Spring 이름들을 덜 섞게 한다 |
| `primer bridge` | [트랜잭션과 persistence 라우트](./contents/spring/README.md#트랜잭션과-persistence-라우트), [요청 처리와 운영 라우트](./contents/spring/README.md#요청-처리와-운영-라우트), [Cross-domain Security 라우트](./contents/spring/README.md#cross-domain-security-라우트) | `@Transactional`, MVC, Security 증상을 다음 deep dive로 넘기기 전에 질문 축을 먼저 자른다 |
| `deep dive` follow-up | [Spring `@Transactional` 기초](./contents/spring/spring-transactional-basics.md), [Spring MVC 요청 생명주기](./contents/spring/README.md#spring-mvc-요청-생명주기), [Spring Security 아키텍처](./contents/spring/README.md#spring-security-아키텍처) | proxy, async, Security internals는 primer와 bridge 뒤에 필요한 것만 내려간다 |

- `self-invocation`, `SessionCreationPolicy`, `WebFlux`, `disconnect`, `Resilience4j`는 첫 클릭보다 follow-up shelf에 가깝다.
- beginner route에서는 `IoC / DI / MVC / 트랜잭션` 사다리를 먼저 고정한다.

[🔝 목차로 돌아가기](#table-of-contents)

## System Design (시스템 설계)

### [📖 시스템 설계 README](./contents/system-design/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [초심자 1회차 라우트](./contents/system-design/README.md#초심자-1회차-라우트), [Primer Route](./contents/system-design/README.md#primer-route), [Beginner Entrypoints](./contents/system-design/README.md#beginner-entrypoints) | `요구사항 -> 숫자 추정 -> 저장소/캐시/큐` 기본 사고 순서를 먼저 맞춘다 |
| `survey / navigator` | [빠른 탐색](./contents/system-design/README.md#빠른-탐색), [학습 순서 추천](./contents/system-design/README.md#학습-순서-추천) | `면접형 starter`, `consistency`, `session`, `notification` 중 어느 질문 축인지 먼저 고를 수 있다 |
| `advanced follow-up` | [Case Study Entrypoints](./contents/system-design/README.md#case-study-entrypoints), [Replay and Cutover Entrypoints](./contents/system-design/README.md#replay-and-cutover-entrypoints), [Retirement Route](./contents/system-design/README.md#retirement-route) | `cutover`, `shadowing`, `retirement`, incident-heavy bridge는 primer 뒤에 필요한 상황에서만 내려간다 |

- `URL 단축기`, `rate limiter`, `payment`, `workflow` 같은 개별 설계 주제도 primer route 뒤에 고르는 편이 beginner-safe 하다.
- `bridge cluster`는 entrypoint 자체보다 cross-category handoff shelf다. `incident`, `authority`, `cutover`가 보이면 첫 클릭인지 한 번 더 확인한다.

[🔝 목차로 돌아가기](#table-of-contents)

## Security (보안)

### [📖 보안 README](./contents/security/README.md) (`category navigator` snapshot)

- `survey`: [추천 학습 흐름 (category-local survey)](./contents/security/README.md#추천-학습-흐름-category-local-survey)에서 `JWT / Session / Recovery`, `OAuth / Browser / BFF` mainline과 `[primer bridge]` `OAuth PAR / JAR` / `[primer bridge]` `OAuth Device Code` branch point, `Service Trust / Delegation`, `AuthZ / Tenant / Detection`, `Abuse / Replay / PoP`, `SCIM / Lifecycle / Drift` 순으로 큰 흐름을 잡는다.
- `primer`: [인증과 인가의 차이](./contents/security/authentication-vs-authorization.md), [Signed Cookies / Server Sessions / JWT Trade-offs](./contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md), [OAuth2 vs OIDC Social Login Primer](./contents/security/oauth2-oidc-social-login-primer.md), [OAuth2 Authorization Code Grant](./contents/security/oauth2-authorization-code-grant.md)
- `catalog / navigator`: [운영 / Incident catalog](./contents/security/README.md#운영--incident-catalog), [Hardware Trust / Recovery deep dive catalog](./contents/security/README.md#hardware-trust--recovery-deep-dive-catalog), [Session Coherence / Assurance deep dive catalog](./contents/security/README.md#session-coherence--assurance-deep-dive-catalog), [Browser / Session Coherence](./contents/security/README.md#browser--session-coherence), [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path), [Browser / Server Boundary deep dive catalog](./contents/security/README.md#browser--server-boundary-deep-dive-catalog), [Replay / Token Misuse / Session Defense deep dive catalog](./contents/security/README.md#replay--token-misuse--session-defense-deep-dive-catalog), [Identity Lifecycle / Provisioning deep dive catalog](./contents/security/README.md#identity-lifecycle--provisioning-deep-dive-catalog), [Service / Delegation Boundaries deep dive catalog](./contents/security/README.md#service--delegation-boundaries-deep-dive-catalog), [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)
- `route label`: `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust), `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path), `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay), `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle), `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)이 topic map의 security symptom cluster label과 같은 이름으로 맞춰진 root entrypoint다.
- `incident badge snapshot`: security category README와 같은 기준으로 `[playbook]` / `[runbook]` / `[drill]` / `[incident matrix]` / `[recovery]` badge를 읽는다. beginner handoff에서도 `[primer bridge]` / `[deep dive]` / `[cross-category bridge]` / `[system design]` cue를 다시 붙여 다음 handoff를 고른다.
- `[playbook]` [JWT Signature Verification Failure Playbook](./contents/security/jwt-signature-verification-failure-playbook.md), `[runbook]` [Key Rotation Runbook](./contents/security/key-rotation-runbook.md), `[playbook]` [Signing Key Compromise Recovery Playbook](./contents/security/signing-key-compromise-recovery-playbook.md), `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./contents/security/jwt-jwks-outage-recovery-failover-drills.md), `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./contents/security/auth-incident-triage-blast-radius-recovery-matrix.md)
- `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./contents/security/jwks-rotation-cutover-failure-recovery.md), [BFF Session Store Outage / Degradation Recovery](./contents/security/bff-session-store-outage-degradation-recovery.md), [Replay Store Outage / Degradation Recovery](./contents/security/replay-store-outage-degradation-recovery.md), [Hardware Attestation Policy / Failure Recovery](./contents/security/hardware-attestation-policy-failure-recovery.md)
- `primer bridge role cue`: `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md), `[primer bridge]` [Claim Freshness After Permission Changes](./contents/security/claim-freshness-after-permission-changes.md), `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./contents/security/grant-path-freshness-stale-deny-basics.md), `[primer bridge]` [OAuth PAR / JAR Basics](./contents/security/oauth-par-jar-basics.md), `[primer bridge]` [OAuth Device Code Flow / Security Model](./contents/security/oauth-device-code-flow-security.md), `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path), `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust), `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay), `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle), `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./contents/security/jwk-rotation-cache-invalidation-kid-rollover.md), `[deep dive]` [Revocation Propagation Lag / Debugging](./contents/security/revocation-propagation-lag-debugging.md), `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), `[system design]` [System Design: Auth Session Troubleshooting Bridge](./contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Control Plane / Data Plane Separation](./contents/system-design/control-plane-data-plane-separation-design.md), `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](./contents/system-design/database-security-identity-bridge-cutover-design.md)

[🔝 목차로 돌아가기](#table-of-contents)

## Language

### [📖 언어 README](./contents/language/README.md) (`category navigator` snapshot)

| 역할 | snapshot에서 먼저 고를 링크 | 왜 여기서 멈추면 안전한가 |
|---|---|---|
| `primer` | [Java primer](./contents/language/README.md#java-primer), [Java](./contents/language/README.md#java) | `타입 / 객체지향 / 컬렉션 / 메서드` 같은 Java 첫 질문을 먼저 자른다 |
| `deep dive catalog` | [Java deep dive catalog](./contents/language/README.md#java-deep-dive-catalog) | `JVM`, `GC`, `concurrency`, `serialization`, `boundary design`은 primer 뒤에 필요한 축만 확장한다 |
| `cross-category bridge` | [교차 카테고리 브리지](./contents/language/README.md#교차-카테고리-브리지), [C++ primer](./contents/language/README.md#c-primer) | Java basics에서 자료구조/패턴/시스템 질문으로 넘어가거나 언어 자체를 바꿔 읽을 때 길을 잃지 않게 한다 |

- `자바 처음`, `객체지향 처음`, `컬렉션 뭐부터`는 `Java primer`가 첫 클릭이다.
- `map null`, `TreeMap`, `ordered map`, `floor`/`ceiling` broad query는 `Java primer`에서 [Java 컬렉션 프레임워크 입문](./contents/language/java/java-collections-basics.md)으로 먼저 들어간 뒤, `조회 null 해석`이면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./contents/language/java/map-get-null-containskey-getordefault-primer.md), `정렬된 map 경계`면 [Ordered Map Null-Safe Practice Drill](./contents/language/java/ordered-map-null-safe-practice-drill.md)로 한 칸만 더 내려가면 된다.
- `JFR`, `async-profiler`, `virtual threads`, `jcstress`는 입문보다 deep-dive/diagnostics shelf에 가깝다.

[🔝 목차로 돌아가기](#table-of-contents)
