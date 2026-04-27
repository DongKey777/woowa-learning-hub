# Retrieval Anchor Keywords

> 한 줄 요약: 사용자가 문서 제목이 아니라 증상, 에러 문자열, 약어, 운영 용어로 질문할 때 검색을 붙잡아 주는 보조 키워드 규칙이다.

## 왜 필요한가

실제 질문은 문서 제목 그대로 들어오지 않는다.

예를 들면:

- `heap은 괜찮은데 RSS만 올라요`
- `nf_conntrack table full 떠요`
- `retry storm 같아요`
- `mTLS랑 SPIFFE 차이가 뭐예요`

이런 질문은 문서 제목보다 **증상, 에러 문자열, 약어, 도구 이름**으로 들어온다.

특히 beginner용 primer/bridge는 `found 2 -> 선택 규칙 문제`, `rename 문자열 문제`처럼 짧은 분기 문장을 함께 넣어야 첫 검색에서 큰 그림이 더 잘 잡힌다.
그래서 deep dive 문서에는 제목 외에 retrieval anchor를 남겨 두는 편이 RAG 회수율에 유리하다.

## 추천 형식

문서 상단 메타데이터 근처에 한 줄로 남긴다.

```markdown
> retrieval-anchor-keywords: direct buffer, off-heap, native memory, RSS, NMT
```

## 템플릿 삽입 포인트

- deep dive 템플릿: `한 줄 요약` / `난이도` / `관련 문서` 다음, 첫 `##` 제목 바로 전에 둔다.
- `<details>` TOC 템플릿: `</details>` 바로 아래에 두고, 첫 본문 섹션 시작 전에 고정한다.
- `README` / navigator 템플릿: 소개 문단이나 배지 블록 다음, `## 빠른 탐색` 같은 첫 안내 섹션 전에 둔다.
- 새 문서 템플릿에는 placeholder 한 줄을 미리 넣어 두고, 작성 시 comma-separated 값만 채우는 방식으로 유지한다.

### 루트 엔트리포인트 문서 고정 위치

- roadmap 템플릿: 제목 바로 아래 `한 줄 설명` 다음에 두고, `## 목표` 전에 고정한다.
- question bank 템플릿: 제목/요약 다음에 두고, `## 이 문서를 어떻게 써야 하나` 전에 고정한다.
- checklist 템플릿: 제목/요약 다음에 두고, `## 무엇을 먼저 읽나` 또는 첫 체크 섹션 전에 고정한다.
- 배지나 대표 이미지가 있는 루트 `README`는 배지 블록 직후, 첫 `##` 섹션 전에 anchor를 둬서 catalog/navigator alias를 먼저 노출한다.

## 무엇을 넣는가

### 1. 한글 개념 + 영어 원어

- `서비스 간 인증, service-to-service auth`
- `멀티 테넌트, multi-tenant`

### 2. 약어 + 풀네임

- `mTLS, mutual TLS`
- `NMT, Native Memory Tracking`
- `WAL, write-ahead logging`

### 3. 증상과 에러 문자열

- `EADDRNOTAVAIL`
- `Direct buffer memory`
- `table full, dropping packet`
- `client closed request`
- `unable to find JWK`
- `old data after write`

### 4. 운영 도구 이름

- `ss`
- `conntrack`
- `perf`
- `strace`
- `bpftrace`

### 5. 제품/구현체 이름

- `SPIFFE`
- `SPIRE`
- `Resilience4j`
- `HikariCP`

## 좋은 anchor의 특징

- 문서 제목을 그대로 반복하지 않는다.
- 사용자가 실제로 검색할 법한 표현을 넣는다.
- 같은 뜻의 표현을 4~8개 정도로 압축한다.
- 증상, 원인, 도구를 섞되 너무 길게 늘리지 않는다.

beginner primer에서는 아래 기준을 같이 본다.

- anchor 개수는 보통 8~15개 안에서 압축한다.
- anchor는 가능하면 lowercase로 통일하고, 코드 토큰만 예외로 둔다.
- 개념명만 두지 말고 `implements 두 개 했더니 컴파일 에러`, `같은 default method 두 개` 같은 symptom phrase를 2~3개 섞는다.

## 문서 역할 alias도 anchor에 넣는다

증상형 deep dive만 anchor가 필요한 것은 아니다. `README`나 navigator 문서도 사용자가 `survey`, `primer`, `catalog`, `deep dive` 같은 역할 이름으로 찾을 수 있으므로 alias를 같이 두는 편이 안전하다.

- `survey`: `roadmap`, `learning path`, `study order`, `big picture`
- `primer`: `basics`, `intro`, `foundation`, `first principles`, `first-step primer`, `starter`
- `primer bridge`: `follow-up primer`, `handoff primer`, `bridge primer`, `second-step primer`, `primer handoff`
- `catalog / navigator`: `readme`, `index`, `guide`, `entrypoint`
- `deep dive / playbook`: `troubleshooting`, `failure mode`, `trade-off`, `runbook`, `recovery`, `outage`, `incident recovery`
- `question bank`: `interview questions`, `self-check`, `drill`

문서 역할 구분 기준 자체는 [Navigation Taxonomy](./navigation-taxonomy.md)와 함께 맞춰 둔다.

## 패턴 혼동 alias도 anchor에 넣는다

알고리즘 문서는 풀이 이름보다 문제 모양이 헷갈린 채 들어오는 검색이 많다.
`subsequence`, `subarray`, `substring`, `window`, `subwindow`, `contiguous`, `LIS`처럼 서로 섞여 쓰이는 표현은 metadata와 표 라벨 둘 다에 남기는 편이 회수율이 높다.

- subsequence cluster: `LIS`, `longest increasing subsequence`, `증가 부분 수열`, `subsequence`, `skip allowed`, `order preserving`
- contiguous cluster: `subarray`, `substring`, `window`, `subwindow`, `sliding window`, `contiguous only`, `recent k`
- boundary-search cluster: `binary search`, `lower_bound`, `upper_bound`, `first true`, `answer space`, `monotonic predicate`
- confusion bridge: `subsequence vs subarray`, `LIS vs sliding window`, `LIS lower_bound`, `window feasibility + binary search`, `contiguous vs skip allowed`

이 규칙은 [Query Playbook](./query-playbook.md)과 알고리즘 카테고리 navigator를 같이 손볼 때 가장 효과가 크다.

## Topic Map / Bridge 라벨에도 symptom alias와 pattern alias를 드러낸다

metadata anchor만 보강하고 표 라벨이나 섹션 제목은 추상적으로 남겨 두면, symptom query나 pattern query가 category cluster까지 닿는 속도가 느려진다.
특히 topic map, query playbook, cross-domain bridge 같은 routing helper는 표 라벨 자체에도 alias를 함께 적는 편이 좋다.
mixed cross-category bridge라면 symptom alias만이 아니라 `[playbook]`, `[deep dive]`, `[system design]` 같은 role cue도 bullet 앞이나 표 라벨에 드러내서 route shift를 숨기지 않는다.
security beginner route처럼 first-step primer와 handoff primer가 같이 있으면 `[primer]`, `[primer bridge]` cue를 둘 다 드러내서 "맨 처음 여는 문서"와 "그다음 deep dive로 넘기는 문서"를 구분하는 편이 안전하다.
login-loop row와 session-tail row처럼 인접한 beginner troubleshooting shortcut이라면 alias cluster도 따로 둔다. 그래야 `SavedRequest`/`hidden session`류 primer bridge와 `logout tail`/`claim freshness`류 primer bridge가 서로의 deep dive route를 잡아먹지 않는다.
revoke-lag/logout-tail row를 손볼 때도 login-loop와 같은 ladder를 유지한다. 즉 `[primer]`와 `[primer bridge]`를 먼저 고정하고, 그 뒤에 allow tail / stale deny / response contract deep dive를 1개씩만 고르게 둔다.
security README처럼 `incident -> deep dive -> system design -> deep dive`가 한 bullet에 같이 나오면 later link가 앞 badge를 상속한다고 가정하지 말고, 역할이 바뀌는 첫 링크마다 cue를 다시 적어 둔다.

- freshness cluster: `freshness`, `stale read`, `read-after-write`, `projection lag`, `old data after write`, `saved but still old data`
- disconnect cluster: `client disconnect`, `client closed request`, `499`, `broken pipe`, `connection reset`
- edge 502/504 cluster: `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `upstream reset`, `upstream prematurely closed`
- timeout mismatch cluster: `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200`, `first byte timeout`
- auth incident cluster: `JWKS outage`, `kid miss`, `unable to find jwk`, `unable to find JWK`, `auth verification outage`
- revoke lag cluster: `revoke lag`, `revocation tail`, `logout but still works`, `allowed after revoke`, `revoked admin still has access`, `role removed but still allowed`
- login-loop beginner cluster: `login loop beginner route`, `302 login loop primer`, `saved request primer bridge`, `savedrequest primer bridge`, `hidden session beginner route`, `cookie 있는데 다시 로그인 beginner route`, `post-login session persistence beginner`, `cookie-missing beginner split`, `server-anonymous beginner split`
- 401/302 confusion mini-card cluster: `401 302 confusion mini decision card`, `401 302 mini card`, `login loop 30초 체크 카드`, `network 탭 login loop 3 step`, `redirect 기억 cookie 전송 server 복원`, `browser auth 30초 starter card`
- browser/session safe-next-doc cluster: `before spring deep dive`, `spring deep dive 전에 safe next doc`, `safe next doc`, `first safe next doc`, `savedrequest safe next doc`, `cookie 있는데 다시 로그인 safe next doc`, `browser 401 302 safe next doc`, `first spring deep dive after browser guide`
- onceperrequestfilter beginner handoff cluster: `onceperrequestfilter beginner route`, `onceperrequestfilter safe next doc`, `처음 배우는데 onceperrequestfilter`, `onceperrequestfilter 큰 그림`, `onceperrequestfilter 기초 먼저`, `onceperrequestfilter 언제 쓰는지`, `onceperrequestfilter filter interceptor 차이 먼저`, `onceperrequestfilter before async dispatch`, `spring filter example before jwt deep dive`, `spring security filter example beginner handoff`
- security filter chain beginner cluster: `security filter chain beginner`, `처음 배우는데 security filter chain`, `security filter chain 큰 그림`, `security filter chain 기초`, `security filter chain 언제 쓰는지`, `spring security filter chain primer`, `spring security filter chain first-step primer`, `security filter chain 401 403 order`, `security filter chain before deep dive`
- filter-vs-interceptor beginner cluster: `filter vs interceptor beginner`, `servlet filter vs mvc interceptor`, `필터 인터셉터 차이 기초`, `필터 vs 인터셉터 차이부터`, `필터는 언제 쓰고 인터셉터는 언제 쓰나요`, `처음 배우는데 필터 인터셉터 차이`, `request before controller hook`, `controller 앞 공통 처리`, `jwt 전에 filter`, `로그인 체크 interceptor confusion`
- mvc primer beginner cluster: `spring mvc 처음 배우는데`, `spring mvc 큰 그림`, `spring mvc 기초`, `spring mvc는 언제 쓰는지`, `mvc primer before lifecycle`, `spring mvc 생명주기 전에 볼 문서`, `dispatcherservlet 뭐예요`, `컨트롤러는 요청을 어떻게 받나요`
- session-tail beginner cluster: `session tail beginner route`, `session-tail beginner route`, `logout tail primer bridge`, `revocation tail beginner route`, `session freshness primer bridge`, `claim freshness handoff`, `grant freshness handoff`, `tenant membership session scope primer bridge`, `regional revoke lag handoff`
- revoke-lag ladder cluster: `revoke lag primer follow-up deep dive`, `logout tail safe next step`, `primer first revoke lag route`, `role change session freshness basics`, `claim freshness after permission changes`, `logout still works beginner ladder`, `allowed after revoke beginner ladder`, `stale deny beginner ladder`

login-loop ladder처럼 beginner route가 긴 사다리로 이어지는 경우에는 같은 뜻의 철자 변형을 여러 개 반복해서 넣기보다, 사용자 발화 1개와 route label 1개를 남기는 편이 안전하다.
루트 README나 follow-up bridge에서는 legacy alias가 이미 널리 퍼져 있으면 `savedrequest`, `cookie-not-sent`, `server-mapping-missing`처럼 1개씩만 남기고, canonical row wording은 `saved request`, `cookie-missing`, `server-anonymous` 쪽으로 맞춘다.
- delegated-access cleanup cluster: `delegated access cleanup`, `support access cleanup`, `transfer cleanup`, `delegated-access closeout`, `aobo cleanup closeout`, `break-glass cleanup closeout`, `delegated session cleanup`, `cleanup_confirmed beginner route`, `customer timeline closeout`, `support transfer cleanup wording`
- support-access alert beginner cluster: `support access alert 큰 그림`, `support access alert 기초`, `처음 배우는데 support access 알림 큰 그림`, `support access 알림은 누가 받는지`, `지원 접근 알림은 누가 받는지`, `support access 알림은 언제 즉시 보내는지`, `support access 알림은 언제 timeline 쓰는지`, `support access 알림은 무엇 기준으로 나누는지`, `support access audience 먼저`, `support access surface 나중에`, `break glass 알림 누가 언제 받는지`, `mailbox compromise면 무엇 기준으로 surface 고르는지`
- session handoff cue cluster: `auth session troubleshooting bridge`, `hidden session system design handoff`, `session store recovery handoff`, `browser bff session boundary primer`, `system design recovery cue`, `session recovery ladder`
- subdomain callback chooser cluster: `subdomain callback handoff chooser`, `shared-domain cookie vs one-time handoff`, `auth app subdomain chooser`, `callback success but app first request anonymous`, `shared cookie vs handoff chooser`, `auth callback app-local session chooser`
- __Host- migration cluster: `__Host- cookie migration`, `__Host cookie migration`, `shared-domain session to __Host cookie`, `parent-domain cookie to host-only cookie`, `__Host cookie cannot be shared across subdomains`, `old shared cookie cleanup after __Host`, `__Host cookie logout cleanup`, `host-only cutover primer`
- cookie transport split cluster: `cookie-not-sent`, `cookie exists but not sent`, `cookie stored but not sent`, `request cookie header empty`, `application tab cookie but no request cookie`
- authz cache symptom cluster: `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `only one tenant 403`, `403 after revoke`, `403 after role change`, `inconsistent 401 404`, `401 404 flip`, `concealment drift`, `cached 404 after grant`
- bridge role cluster: `playbook`, `deep dive`, `system design`, `incident ladder`, `control-plane handoff`, `cutover handoff`
- primer route cluster: `security beginner route`, `beginner security route`, `security basics route`, `auth basics route`, `auth beginner route`, `primer bridge`, `follow-up primer`, `handoff primer`, `first-step primer`, `starter`
- beginner di question cluster: `처음 배우는데 di가 뭐예요`, `처음 배우는데 의존성 주입이 뭐예요`, `의존성 주입 큰 그림`, `di 큰 그림`, `di 기초`, `의존성 주입 기초`, `언제 di 쓰는지`, `di 왜 쓰는지`, `인터페이스 주입이 뭐예요`, `인터페이스로 주입하는 이유`, `구현 말고 인터페이스를 주입하는 이유`, `new 대신 주입받는 이유`, `객체를 밖에서 넣어주는 이유`, `부모가 아니라 외부가 객체를 넣어준다`, `호출자가 구현을 넣어준다`
- factory beginner creation-selection cluster: `처음 배우는데 factory`, `처음 배우는데 팩토리 패턴`, `factory 큰 그림`, `팩토리 큰 그림`, `factory 기초`, `팩토리 기초`, `factory 언제 쓰는지`, `팩토리 언제 쓰는지`, `creation vs selection`, `생성 vs 선택`, `새로 만들기 vs 고르기`, `factory는 언제 쓰고 selector는 언제 쓰는지`, `factory selector 차이`, `factory selection confusion`, `new 대신 factory`, `정적 팩토리 vs factory 패턴`, `selector is not factory`
- spring router/qualifier beginner cluster: `router 언제 쓰는지`, `qualifier 언제 쓰는지`, `요청마다 구현체 선택`, `앱이 뜰 때 한 번 고르기`, `앱 시작할 때 고르기`, `enum 분기 구현체 선택`, `enum에 따라 구현체 선택`, `주입할 때 고르기`, `실행 중에 고르기`, `고정 wiring vs runtime selection`, `map string bean router`, `처음 배우는데 router qualifier 차이`, `@Primary @Qualifier collection vs runtime router`, `primary qualifier collection vs runtime router`, `처음 배우는데 primary qualifier collection vs runtime router`, `collection vs runtime router`
- language beginner oop route cluster: `처음 배우는데 상속 언제 쓰는지`, `상속 큰 그림`, `상속 기초`, `처음 배우는데 추상 클래스 인터페이스 언제 쓰는지`, `추상 클래스 인터페이스 큰 그림`, `추상 클래스 인터페이스 기초`, `처음 배우는데 상속 vs 조합 언제 쓰는지`, `상속 조합 큰 그림`, `상속 조합 기초`, `객체지향 큰 그림 다음 상속`, `상속 다음 추상 클래스 인터페이스`, `추상 클래스 인터페이스 다음 조합`, `추상 클래스 인터페이스 다음 템플릿 메소드`, `추상 클래스 인터페이스 다음 템플릿 메소드 vs 전략`, `추상 클래스 인터페이스 조합 템플릿 전략 순서`
- oop-to-pattern beginner route cluster: `처음 배우는데 디자인 패턴 어디부터`, `객체지향 큰 그림 다음 디자인 패턴 어디부터`, `상속 다음 디자인 패턴 어디부터`, `상속 다음 조합 패턴 기초`, `상속 다음 템플릿 메소드 전략 순서`, `조합 다음 템플릿 메소드 전략 순서`, `oop to design pattern beginner route`, `design pattern beginner route`, `design pattern route map`
- language beginner inheritance cluster: `처음 배우는데 상속 언제 쓰는지`, `상속은 언제 써요`, `상속 언제 써요`, `상속 언제 써요?`, `상속 언제 쓰나요`, `상속 언제 쓰는지`, `기초 상속 언제 쓰는지`, `상속 vs 조합 언제`, `상속 vs 조합 언제 쓰는지`, `상속 vs 조합 언제 써요`, `처음 배우는데 추상 클래스 인터페이스 차이`, `처음 배우는데 추상 클래스 인터페이스 차이 큰 그림`, `처음 배우는데 추상 클래스 인터페이스 언제 쓰는지`, `추상 클래스 인터페이스 언제`, `추상 클래스 인터페이스 언제 써요`, `추상 클래스 인터페이스 언제 써요?`, `추상 클래스 인터페이스 언제 쓰나요`, `추상 클래스 인터페이스 언제 쓰는지`, `추상 클래스 인터페이스 기초 먼저`, `추상 클래스 인터페이스 입문 먼저`, `추상 클래스 인터페이스 primer first`, `추상 클래스 인터페이스 basics first`, `hook method 언제 쓰는지`, `abstract step 언제 쓰는지`, `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스 인터페이스 -> 상속보다 조합`, `객체지향 큰 그림 다음 상속 언제 쓰는지`, `상속 언제 쓰는지 다음 추상 클래스 인터페이스`, `추상 클래스 인터페이스 다음 상속보다 조합`, `추상 클래스 인터페이스 다음 템플릿 메소드`, `추상 클래스 인터페이스 다음 템플릿 메소드 vs 전략`
- language beginner template-strategy bridge cluster: `처음 배우는데 템플릿 메소드 vs 전략`, `템플릿 메소드 전략 큰 그림`, `템플릿 메소드 전략 기초 비교`, `템플릿 메소드 전략 언제 쓰는지`, `처음 배우는데 템플릿 메소드 전략 언제 쓰는지`, `추상 클래스 다음 템플릿 메소드 vs 전략`, `추상 클래스 문서 다음 템플릿 메소드 vs 전략`, `추상 클래스에서 넘어와서 템플릿 메소드 전략 언제 쓰는지`, `추상 클래스면 템플릿 메소드인가요`, `추상 클래스 다음 뭐 읽지 템플릿 메소드 전략`, `template method vs strategy beginner`, `template method vs strategy return path`, `language readme java primer bridge`, `language readme #java-primer`, `java primer return path`, `패턴 비교하다가 기초로 돌아가기`, `처음 배우는데 객체지향 큰 그림으로 돌아가기`, `처음 배우는데 부모가 흐름을 쥔다 vs 호출자가 전략을 고른다`, `부모가 흐름을 쥔다 vs 호출자가 전략을 고른다`, `부모가 흐름을 쥔다 vs 외부가 구현을 넣어준다`, `부모가 순서를 정한다 vs 외부에서 구현을 넣어준다`, `template method는 부모가 흐름`, `strategy는 호출자가 선택`, `strategy는 외부에서 구현을 넣어준다`, `template method vs strategy di`, `template method vs strategy selector`, `전략 패턴 di로 고르기`, `전략 패턴 selector로 고르기`, `호출자가 구현을 넣어준다 vs 부모가 순서를 고정한다`, `주입으로 구현 고르기 vs 부모 오버라이드`, `selector로 구현 고르기 vs 부모 뼈대`, `template method vs strategy primer first`, `java primer 먼저 보고 template method vs strategy`, `조합 다음 템플릿 메소드`, `템플릿 메소드 다음 전략`, `전략 패턴 다음 템플릿 메소드`, `템플릿 메소드 다음 전략 패턴 기초`, `strategy to template method beginner bridge`, `template method to strategy beginner bridge`, `조합 템플릿 전략 beginner route`
- root/category template-strategy entry cluster: `cs root readme template method vs strategy`, `root readme 처음 배우는데 템플릿 메소드 vs 전략`, `디자인 패턴 readme 템플릿 메소드 vs 전략 입구`, `software engineering readme template method vs strategy`, `카테고리 인덱스 템플릿 메소드 vs 전략`, `처음 배우는데 템플릿 메소드 vs 전략 어디부터`, `처음 배우는데 템플릿 메소드 vs 전략 입문`, `템플릿 메소드 vs 전략 primer entry`, `템플릿 메소드 vs 전략 첫 히트`, `부모가 흐름을 쥔다 호출자가 전략을 고른다 입문`
- template method basics beginner cluster: `처음 배우는데 템플릿 메소드`, `처음 배우는데 템플릿 메소드 큰 그림`, `처음 배우는데 템플릿 메소드 언제 쓰는지`, `템플릿 메소드 큰 그림`, `템플릿 메소드 기초`, `템플릿 메소드 언제 쓰는지`, `template method big picture`, `template method when to use beginner`, `처음 배우는데 hook abstract step 차이`, `abstract step vs hook`, `hook vs abstract step`, `필수 빈칸 선택 빈칸`, `부모가 순서를 고정한다`, `부모가 흐름을 쥔다`
- parent-controls-flow cluster: `부모가 흐름을 쥔다`, `부모가 흐름을 잡고 자식이 일부만 바꾼다`, `상속이 흐름을 쥔다`, `템플릿 메소드 큰 그림`, `템플릿 메소드에서 부모가 흐름을 정한다`, `hook method는 어디서 끼어드나`, `고정 흐름 일부만 바꾸기`, `상속으로 뼈대를 잡는다`, `조합이 아니라 상속으로 흐름 제어`, `전략 말고 부모가 순서를 정한다`
- hook-vs-strategy beginner cluster: `hook vs strategy beginner route`, `hook-vs-strategy beginner route`, `hook method vs strategy pattern`, `template method hook vs strategy`, `처음 배우는데 hook method랑 strategy 차이`, `처음 배우는데 hook vs strategy 큰 그림`, `기초 hook vs strategy 비교`, `hook method 언제 쓰고 strategy 언제 쓰는지`, `언제 hook 쓰고 언제 strategy 쓰는지`, `상속 hook vs 객체 주입 strategy`, `hook 많아지면 strategy 의심`, `템플릿 메서드 다음 strategy`, `strategy pattern 언제 쓰는지`, `hook method 다음 strategy pattern`, `hook method beginner first router`, `template hook smell late stage follow up`, `hook smell은 나중 점검`, `hook method 처음 배우는데 smell 문서 말고 큰 그림 먼저`
- strategy-basics reverse-bridge cluster: `strategy pattern basics`, `strategy pattern beginner`, `전략 패턴 기초`, `처음 배우는데 전략 패턴`, `전략 패턴 큰 그림`, `전략 패턴 언제 쓰는지`, `hook 말고 strategy`, `hook 많아지면 strategy`, `부모가 흐름을 쥔다 vs 호출자가 전략을 고른다`, `외부에서 구현을 넣어준다`, `호출자가 구현을 고른다`, `호출자가 구현을 넣어준다`, `주입으로 구현 고르기`, `di로 전략 선택`, `selector로 전략 선택`
- authority transfer cluster: `authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `SCIM disable했는데 still access`, `SCIM deprovision 뒤에도 권한이 남는다`, `deprovision은 끝났는데 access tail remains`, `backfill is green but access tail remains`, `backfill green access tail`, `access tail remains`, `decision parity`, `data parity vs decision parity`, `shadow read green but auth decision diverges`, `auth shadow divergence`, `deprovision tail`, `SCIM primer first`, `deprovision primer first`, `access tail primer first`, `role change session freshness basics`, `claim freshness after permission changes`, `authority transfer primer bridge`
- authority beginner-path additions: `authority transfer beginner route`, `beginner authority transfer route`, `authority transfer first-step primer`, `identity lifecycle primer route`, `decision parity beginner route`, `auth shadow divergence beginner route`, `verification shadowing authority route`, `authority cleanup evidence ladder`
- cross-readme authority route aliases: security README의 `Identity / Delegation / Lifecycle`, database README의 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design README의 `Database / Security Authority Bridge` / `Verification / Shadowing / Authority Bridge`처럼 sibling label이 갈리면 각 README metadata anchor에 서로의 route name도 같이 남긴다
- algorithm boundary cluster: `LIS`, `subsequence`, `subarray`, `subwindow`, `sliding window`, `binary search`, `lower_bound`, `first true`, `contiguous only`, `skip allowed`
- wildcard-421 trace cluster: `421 trace mini lab`, `wildcard cert 421 walkthrough`, `same cert different backend 421`, `devtools curl proxy log 421`, `wildcard cert coalescing rejected`, `misdirected request mini lab`

이 규칙은 [Topic Map](./topic-map.md), [Query Playbook](./query-playbook.md), [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)를 같이 맞춰 줄 때 가장 효과가 크다.

## 예시

| 문서 | anchor 예시 |
|---|---|
| `nat-conntrack-ephemeral-port-exhaustion.md` | `NAT gateway`, `conntrack`, `TIME_WAIT`, `EADDRNOTAVAIL` |
| `direct-buffer-offheap-memory-troubleshooting.md` | `off-heap`, `RSS`, `Direct buffer memory`, `NMT` |
| `service-to-service-auth-mtls-jwt-spiffe.md` | `mTLS`, `SPIFFE`, `SPIRE`, `workload identity` |
| `strangler-fig-migration-contract-cutover.md` | `shadow traffic`, `dual write`, `cutover`, `rollback` |
| `api-key-hmac-signature-replay-protection.md` | `HMAC`, `nonce`, `timestamp`, `replay attack`, `canonical string` |
| `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md` | `X-Forwarded-For`, `Forwarded`, `X-Real-IP`, `trusted proxy` |
| `monotonic-clock-wall-clock-timeout-deadline.md` | `CLOCK_MONOTONIC`, `wall clock`, `deadline propagation`, `NTP jump` |
| `payment-system-ledger-idempotency-reconciliation-design.md` | `ledger`, `reconciliation`, `auth capture refund`, `double-entry` |

## 관리 규칙

- 새 운영형 문서를 만들면 anchor를 같이 넣는다.
- anchor는 metadata로 올려 query expansion에 쓴다.
- README의 역할 라벨을 바꿨다면 anchor도 함께 맞춰 `roadmap`, `index`, `self-check` 같은 alias가 남아 있는지 본다.
- symptom-first navigator를 고쳤다면 metadata anchor뿐 아니라 table row, section label, related-doc link에도 같은 alias cluster가 드러나는지 본다.
- edge/network routing을 손봤다면 `499`, `502`, `504`, `bad gateway`, `gateway timeout`, `timeout mismatch`가 separate shortcut으로 남아 있는지 본다.
- revoke/authz routing을 손봤다면 `revoke lag`, `allowed after revoke`, `stale authz cache`, `403 after revoke`가 separate shortcut으로 남아 있는지 본다.
- authz cache/debugging 문서를 손봤다면 `stale deny`, `tenant-specific 403`, `401 404 flip` 같은 alias가 deep dive metadata와 security README symptom row에 같이 남는지 본다.
- stale-deny beginner row와 `tenant-specific 403` row가 같은 `[primer bridge]`를 공유한다면, `cached 404 after grant` alias도 같은 row/ladder에 남겨 두고 response-code `[primer]`를 한 번 거치더라도 첫 `[deep dive]` cue는 같은 `Authorization Caching / Staleness`로 다시 수렴하는지 본다.
- cross-category bridge를 손봤다면 `playbook`, `deep dive`, `system design` cue가 metadata anchor, section label, related-doc bullet에 같이 남는지 본다.
- security beginner route를 손봤다면 `security beginner route`, `auth basics route`, `first-step primer`, `primer bridge`, `follow-up primer`, `handoff primer`, `login loop beginner route`, `saved request primer bridge`, `session tail beginner route`, `logout tail primer bridge` alias가 README metadata와 route row 문구에 같이 남는지 본다.
- beginner/junior row를 손봤다면 `[primer] -> [primer bridge]` handoff가 row 문구와 metadata anchor 둘 다에 남아 있는지 본다. `first-step primer`, `second-step handoff`, `safe next step`, `primer bridge` cue 중 하나라도 빠지면 handoff row가 bare deep-dive row처럼 회수될 수 있다. 이 점검은 [Role-Cue Consistency Lint](./role-cue-consistency-lint.md)와 같이 묶는 편이 안전하다.
- login-loop beginner ladder를 손봤다면 primer/follow-up 문서가 `login loop`, `SavedRequest`, `hidden session`, `cookie exists but session missing`, `cookie 있는데 다시 로그인` core alias를 함께 유지하는지 [Auth Ladder Alias Drift Lint](./auth-ladder-alias-drift-lint.md)로 먼저 확인한다.
- browser/session bridge를 손봤다면 `before spring deep dive`, `safe next doc`, `first spring deep dive` phrasing이 primer, follow-up, README route row에 함께 남는지 본다. 그래야 retrieval이 beginner를 곧바로 Spring deep dive로 던지지 않고 한 번 더 안전한 handoff 문서로 세운다.
- revoke/authz beginner ladder를 손봤다면 `revoke lag`, `logout tail`, `allowed after revoke`, `stale deny`, `403 after revoke` alias가 bridge metadata와 README row에 같이 남고, 첫 safe next step이 `[deep dive]` 1개로만 열리는지 확인한다.
- delegated-access cleanup ladder를 손봤다면 `delegated access cleanup`, `support access cleanup`, `transfer cleanup`, `cleanup_confirmed`, `customer timeline closeout` alias가 service-delegation README row와 metadata anchor에 같이 남고, first-step이 generic `revoke lag` incident row가 아니라 `[primer]` -> `[deep dive] Delegated Session Tail Cleanup` starter로 보이는지 확인한다.
- support-access alert primer를 손봤다면 `누가 받는지`, `언제 즉시 보내는지`, `무엇 기준으로 audience를 나누는지`, `support access alert 큰 그림`, `support access alert 기초` 질문형 alias가 primer metadata와 `꼬리질문` 섹션에 같이 남는지 확인한다. beginner first-hit에서는 deep dive 명사보다 `누가/언제/무엇 기준` 재질문 표현이 먼저 회수되어야 한다.
- language primer route를 손봤다면 `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지` 같은 beginner phrasing이 metadata와 README primer bullet에 같이 남는지 확인하고, `처음 배우는데 상속 언제 쓰는지` 류 질의가 [Java 상속과 오버라이딩 기초](../contents/language/java/java-inheritance-overriding-basics.md)로 먼저 수렴하는지 본다.
- OOP primer에서 design-pattern README로 넘기는 bridge를 손봤다면 `처음 배우는데 디자인 패턴 어디부터`, `객체지향 큰 그림 다음 디자인 패턴 어디부터`, `상속 다음 디자인 패턴 어디부터`, `조합 다음 템플릿 메소드 전략 순서` 같은 질문형 alias가 OOP primer metadata와 design-pattern README handoff 문장 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 `GoF` 같은 분류명보다 "어디부터" 질문이 먼저 회수되어야 한다.
- DI/패턴 primer를 손봤다면 `인터페이스 주입`, `new 대신 주입`, `호출자가 구현을 넣어준다`, `부모가 흐름을 쥔다`처럼 초급 질문자가 실제로 말할 표현이 metadata anchor와 primer 첫 요약에 같이 남는지 확인한다. beginner first-hit에서는 정식 용어 `DI`, `template method`보다 질문형 자연어가 먼저 잡혀야 한다.
- template method vs strategy chooser를 손봤다면 `부모가 흐름을 쥔다 vs 호출자가 전략을 고른다` 문장을 `부모가 순서를 고정한다 vs 외부에서 구현을 넣어준다`, `주입으로 구현 고르기`, `selector로 구현 고르기`, `di로 전략 선택` 같은 beginner alias로도 같이 남긴다. beginner first-hit에서는 정식 용어보다 `누가 고르나요`, `밖에서 넣어주나요` 같은 chooser 문장이 먼저 회수되어야 한다.
- service-locator checklist/anti-pattern을 손봤다면 `beanfactory.getbean`, `applicationcontext.getbean`, `objectprovider.getifavailable`, `objectprovider.getobject` 같은 초심자 오검색 변형을 anchor에 같이 남긴다. beginner first-hit에서는 "컨테이너에서 직접 꺼내 쓰는 코드"와 "optional 주입"을 먼저 갈라 주는 문장이 deep dive 제목보다 더 잘 잡힌다.
- factory primer를 손봤다면 `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지` 질문형 alias와 `creation vs selection`, `생성 vs 선택`, `새로 만들기 vs 고르기` 같은 오해 분기 문장이 metadata anchor와 첫 비교 표 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 `factory method`보다 "언제 factory 쓰는지"와 "고르기만 하면 selector인가" 같은 자연어가 먼저 회수되어야 한다.
- interface `static`/utility primer를 손봤다면 `interface static method vs utility class`, `인터페이스 static 메서드 vs 유틸리티 클래스`, `정적 메서드 어디에 두나`, `interface 안에 둘지 utility class로 뺄지`, `언제 utility class` 같은 질문형 alias가 metadata anchor와 첫 비교 표 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 `default/static/private` 분류명보다 "이 정적 메서드 어디에 두죠?" 같은 자연어 갈림길이 먼저 회수되어야 한다.
- factory selector resolver entrypoint를 손봤다면 `selector naming entrypoint`, `selector naming first hit`, `selector 이름 뭐로 지어야 해`, `factory selector 차이`, `처음 배우는데 selector naming` 같은 beginner 검색어가 metadata anchor와 첫 10초 분기 문장 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 `strategy` deep dive보다 "지금 해석/선택/생성 중 무엇인가"를 먼저 보여 주는 entrypoint가 이겨야 한다.
- selector/resolver naming primer를 손봤다면 `raw input 해석 vs 후보 선택`, `문자열 enum 변환 resolver`, `코드값 해석 resolver`, `뜻이 정해진 뒤 selector`, `해석 다음 선택` 같은 증상형 alias가 metadata anchor와 첫 비교 표/증상 카드에 같이 남는지 확인한다. beginner first-hit에서는 `resolver`, `selector` 정의보다 "문자열을 뜻으로 바꾸는 중인가" 같은 증상 문장이 먼저 회수되어야 한다.
- selector/resolver naming bridge를 손봤다면 entrypoint 쪽 `selector naming` alias와 bridge 쪽 `selector naming follow up`, `selector entrypoint follow up`, `selector 이름 뭐로 지어야 해`가 같이 남아 있는지 본다. beginner route에서는 `[entrypoint] -> [bridge] -> [checklist]` handoff가 링크 문구와 metadata anchor 둘 다에서 보여야 `selector` 검색이 바로 deep dive로 새지 않는다.
- map-backed naming checklist를 손봤다면 `이름 뭘로 지어야 해`, `factory로 불러도 돼?`, `새로 안 만드는데 factory`, `lookup만 하는데 registry인가요`, `조건 보고 고르면 selector인가요` 같은 질문형 alias를 metadata anchor와 흔한 혼동 bullet 양쪽에 같이 남긴다. beginner first-hit에서는 정식 패턴명보다 "지금 이 클래스 이름 뭐가 맞아요" 같은 자연어가 먼저 회수되어야 한다.
- strategy map vs registry primer를 손봤다면 `Map<String, Strategy> registry인가요`, `Map<String, Strategy> selector인가요`, `처음 배우는데 strategy map 큰 그림`, `strategy map 언제 쓰는지`, `등록된 것을 찾아온다 vs 어떻게 처리할지 고른다` 같은 beginner alias를 metadata anchor와 첫 비교 표/흔한 오해 bullet 양쪽에 같이 남긴다. beginner first-hit에서는 `strategy collection`보다 "`Map<String, Strategy>` 이거 selector예요 registry예요?" 같은 자연어가 먼저 회수되어야 한다.
- spring DI 후보 선택/strategy primer를 손봤다면 `qualifier가 반복돼요`, `같은 qualifier가 계속 보여요`, `qualifier 반복되면 custom qualifier`, `qualifier 반복되면 언제 router로 가나요`, `언제 router`, `router는 언제 쓰는지` 같은 질문형 alias가 spring `README`, primer metadata, related-doc handoff에 같이 남는지 확인한다. beginner first-hit에서는 `runtime dispatch` 같은 용어보다 "`언제 router`"처럼 짧은 질문형이 먼저 회수되어야 한다.
- spring README beginner entry card를 손봤다면 `@Primary/@Qualifier/collection vs runtime router`, `앱이 뜰 때 한 번 고르기`, `요청마다 구현체 선택`, `같은 qualifier가 계속 보여요` phrasing이 quick-entry row와 metadata anchor에 같이 남는지 확인한다. 처음 배우는데 검색할 때는 deep-dive 제목보다 이 1줄 큰 그림 카드가 먼저 잡혀야 한다.
- spring README runtime router bridge를 손봤다면 `channel -> bean name`, `channel 값으로 bean 이름 찾기`, `채널 -> bean 이름`, `channel bean name confusion`, `처음 배우는데 channel 분기 큰 그림`, `channel registry 언제 쓰는지` 같은 beginner alias가 metadata anchor, quick-entry row, runtime router 섹션의 design-pattern handoff에 같이 남는지 확인한다. beginner first-hit에서는 `strategy dispatch`보다 `channel -> bean name` 같은 증상형 문장이 먼저 회수되어야 한다.
- spring router/qualifier primer를 손봤다면 `router 언제 쓰는지`, `qualifier 언제 쓰는지`, `요청마다 구현체 선택`, `enum 분기 구현체 선택`, `주입할 때 고르기`, `실행 중에 고르기` 같은 질문형 alias가 metadata anchor와 첫 비교 표에 같이 남는지 확인한다. beginner first-hit에서는 `strategy`, `dispatch`보다 질문형 자연어가 먼저 회수되어야 한다.
- spring mvc primer를 손봤다면 `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지`, `mvc primer before lifecycle`, `spring mvc 생명주기 전에 볼 문서` 같은 질문형 alias가 primer metadata와 beginner bridge 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 lifecycle deep dive보다 controller/dispatcher primer가 먼저 잡혀야 한다.
- spring security filter chain 라우트를 손봤다면 `처음 배우는데 security filter chain`, `security filter chain 큰 그림`, `security filter chain 기초`, `security filter chain 언제 쓰는지`, `spring security filter chain primer`, `security filter chain before deep dive` 같은 beginner alias가 primer metadata와 advanced ordering 문서의 입문 브리지 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 ordering deep dive보다 primer가 먼저 잡혀야 한다.
- spring jdbc primer/bridge를 손봤다면 `rowmapper vs resultsetextractor`, `한 행씩 바꾸기`, `결과 전체 조립`, `queryforobject 헷갈림`, `처음 배우는데 rowmapper 뭐예요`, `resultsetextractor 언제 쓰는지` 같은 질문형 alias가 metadata anchor와 첫 비교 표 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 exception translation deep dive보다 콜백 역할 구분 primer가 먼저 잡혀야 한다.
- query playbook의 beginner route를 손봤다면 `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지` 질문형 alias가 query-playbook 표와 primer 문서 metadata anchor 양쪽에 같이 남는지 확인한다. beginner first-hit에서는 deep dive 명사보다 질문형 발화가 먼저 회수되어야 한다.
- OOP primer 3종(`상속 -> 추상 클래스/인터페이스 -> 조합`)을 같이 손봤다면 문서 첫 요약과 metadata anchor가 모두 `처음 배우는데`, `큰 그림`, `기초`, `언제 쓰는지` 질문형을 공유하는지 확인한다. abstract/interface/template handoff까지 같이 손댔다면 `부모가 흐름을 쥔다 vs 계약을 진화시킨다`, `부모 흐름 고정 vs 인터페이스 계약 진화` 같은 beginner 축 문장도 anchor와 첫 비교 표에 같이 남겨 route drift를 더 줄인다. beginner first-hit에서는 설명어보다 질문형과 갈림길 문장이 먼저 잡혀야 한다.
- wrapper-pattern beginner router를 손봤다면 `wrapper pattern confusion`, `처음 배우는데 wrapper`, `큰 그림 wrapper pattern`, `번역 vs 단순화 vs 기능추가`, `adapter냐 facade냐 decorator냐`, `언제 쓰는지 adapter facade decorator` 같은 질문형/갈림길 alias가 metadata anchor와 첫 비교 표에 같이 남는지 확인한다. beginner first-hit에서는 `GoF structural pattern` 같은 분류명보다 "`adapter냐 facade냐 decorator냐`" 같은 자연어 분기 문장이 먼저 회수되어야 한다.
- authority-transfer bridge를 손봤다면 security `Identity / Delegation / Lifecycle`, database `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design `Database / Security Authority Bridge` / `Verification / Shadowing / Authority Bridge`가 서로의 README metadata anchor와 entrypoint 설명에 같이 남아 route-name mismatch를 흡수하는지 본다.
- SCIM/deprovision/access-tail symptom row를 손봤다면 시작 링크가 `[deep dive]`/`[system design]`로 바로 뛰지 않고 `[primer]` -> `[primer bridge]` -> `[cross-category bridge]` starter를 먼저 유지하는지 본다.
- security mixed bridge를 손봤다면 `cross-category bridge`, `deep dive`, `system design` cue가 같은 bullet 안의 role-switch 지점마다 다시 붙는지 본다.
- session troubleshooting handoff를 손봤다면 `saved request primer bridge`, `browser bff session boundary primer`, `bff session store outage`, `auth session troubleshooting bridge`, `session store recovery handoff`, `regional revoke lag handoff` alias가 root/security/system-design README row와 taxonomy example에 같이 남는지 본다.
- cookie/session beginner split을 손봤다면 `cookie-not-sent` alias는 `[primer]` 쪽에, `session store recovery handoff`/`server-mapping-missing` alias는 `[deep dive] -> [recovery]` 쪽에 남아 beginner 첫 분기가 다시 섞이지 않는지 본다.
- mixed incident catalog를 손봤다면 `[playbook]` / `[runbook]` / `[drill]` / `[incident matrix]` / `[recovery]` 옆의 개념 본문에도 `[deep dive]` cue가 붙었는지, `deep dive`, `failure mode`, affected component alias가 같은 섹션 anchor와 링크 문구에 같이 남는지 본다.
- 알고리즘 topic map을 손봤다면 `skip allowed`, `contiguous only`, `lower_bound`, `first true` 같은 경계 alias가 topic map과 query playbook에 같이 남아 있는지 본다.
- spring http client builder/template primer를 손봤다면 `builder vs template`, `resttemplatebuilder vs webclient builder`, `언제 커스터마이징하는지`, `헤더 하나만 추가하고 싶어요`, `공용 baseline vs 전용 client` 같은 beginner alias를 metadata anchor와 첫 비교 표 양쪽에 같이 남긴다. beginner first-hit에서는 실행 모델 deep dive보다 "지금 client를 고르는지, builder를 만지는지"를 먼저 갈라 주는 문장이 이겨야 한다.
- mixed incident catalog에 `[recovery]` 라벨을 붙였다면 `outage`, `degradation`, `recovery`, affected store/component alias도 anchor와 표 라벨에 같이 남긴다.
- anchor가 늘어나면 `query-playbook.md`와 `topic-map.md`도 함께 점검한다.

## 한 줄 정리

Retrieval anchor keyword는 제목 밖 검색어를 붙잡는 장치라서, 운영/장애형 문서일수록 꼭 챙기는 편이 좋다.
