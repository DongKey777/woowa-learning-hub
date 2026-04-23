# README Quick-Start / Bridge Overlap Check

> 한 줄 요약: category `README`의 quick-start나 `역할별 라우팅 요약` bridge row가 later grouped bridge section의 긴 문서 묶음을 다시 복제했는지 잡는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Navigation Taxonomy](./navigation-taxonomy.md)
> - [Fence False-Link Precheck](./fence-false-link-precheck.md)

> retrieval-anchor-keywords: readme quick start overlap, readme quick-start overlap, quick-start overlap lint, quick routes overlap lint, bridge overlap check, grouped bridge section, cross-category bridge section, bridge entrypoint hygiene, duplicate bridge bundle, readme link dedupe, reverse-link qa, anchor-first cleanup, anchor-first quick-start, bridge subsection anchor, quick-start before after, role summary noise audit, role-summary noise audit, role summary bridge row, role-summary bridge row, routing summary bridge noise, bridge-owned link, bridge owner anchor

## 언제 돌리나

- `contents/*/README.md`의 `빠른 시작`, `빠른 탐색`, `Quick Routes`를 손본 뒤
- `역할별 라우팅 요약` table에서 `bridge` 역할 row를 손본 뒤
- later `연결해서 보면 좋은 문서 (cross-category bridge)` 구간으로 link bundle을 재정리한 뒤
- quick-start나 role-summary row에는 entrypoint만 남기고, 세부 cross-category link는 아래 bridge section이 owner인지 확인하고 싶을 때

## 실행

```bash
python docs/readme_bridge_overlap_check.py
```

특정 README만 보고 싶으면 file path를 넘긴다.

```bash
python docs/readme_bridge_overlap_check.py knowledge/cs/contents/network/README.md
```

기본 기준은 "같은 local `.md` 링크가 2개 이상 겹치면 실패"다. 필요하면 threshold를 조정한다.

```bash
python docs/readme_bridge_overlap_check.py --min-overlap 3
```

현재 스크립트는 quick-start vs later bridge overlap만 자동으로 본다.
`역할별 라우팅 요약` bridge row noise는 아래 최소 규칙으로 수동 QA한다.

## 무엇을 잡나

- `빠른 시작`, `빠른 탐색`, `Quick Routes` 같은 quick-start section
- `역할별 라우팅 요약`에서 `문서 역할` 칸에 `bridge`가 들어가는 row
- 그보다 뒤에 나오는 `연결해서 보면 좋은 문서 (cross-category bridge)`류 grouped bridge section
- 두 구간에 모두 등장하는 local `.md` 링크
- internal `#anchor` link는 무시한다. quick-start에서 subsection anchor를 entrypoint로 남기는 패턴은 허용하기 위해서다.
- role-summary row는 subsection anchor나 route-map anchor를 남기고, later bridge section이 owner인 direct `.md` bundle은 다시 적지 않는 것을 기본 규칙으로 본다.

## 실패했을 때 고치는 순서

1. quick-start에는 later bridge subsection anchor나 route-map entrypoint만 남긴다.
2. `역할별 라우팅 요약`의 `bridge` row도 같은 anchor-first 규칙을 따른다. 같은 bundle이 later bridge section에 있으면 table row는 subsection anchor나 route-map entrypoint로 줄인다.
3. cross-category 문서 묶음은 later grouped bridge section 쪽에서만 길게 유지한다.
4. quick-start나 role-summary row에 대표 문서 1개가 꼭 필요하면, later bridge section에 없는 symptom entrypoint 1개만 둔다.
5. quick-start 중복은 `python docs/readme_bridge_overlap_check.py`로 다시 확인하고, role-summary row는 diff로 수동 확인한다.

## 역할별 라우팅 요약 최소 규칙

- `문서 역할` 칸에 `bridge`가 들어가면 그 row는 bundle owner가 아니라 navigator entrypoint다.
- 그런 row의 `먼저 갈 곳`은 같은 README 안의 bridge subsection anchor나 `rag/cross-domain-bridge-map.md#...` route anchor를 우선 쓴다.
- later `연결해서 보면 좋은 문서 (cross-category bridge)` 구간이 이미 owner인 direct `.md` 링크 묶음은 role-summary table에서 다시 나열하지 않는다.
- direct `.md` 링크를 role-summary table에 남겨도 되는 경우는, later bridge section에 다시 나오지 않는 단일 대표 entrypoint일 때뿐이다.

## Anchor-First Before/After 예시

quick-start 정리 때는 "대표 bundle anchor를 먼저 남기고, direct `.md` 링크는 bridge section owner 쪽으로 내린다"를 기본 패턴으로 삼는다.

```markdown
<!-- before -->
## 빠른 탐색
- disconnect / timeout bundle:
  - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
  - [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
  - [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)

## 연결해서 보면 좋은 문서 (cross-category bridge)
### Request Lifecycle Upload Disconnect
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
```

```markdown
<!-- after -->
## 빠른 탐색
- disconnect / timeout bundle은 [Request Lifecycle Upload Disconnect](#request-lifecycle-upload-disconnect) anchor에서 이어 본다.
- 대표 symptom entrypoint 1개만 남기고 싶으면 [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)만 둔다.

## 연결해서 보면 좋은 문서 (cross-category bridge)
### Request Lifecycle Upload Disconnect
- [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
- [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
- [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
```

실제 category README 패턴은 [Network README: 빠른 탐색](../contents/network/README.md#빠른-탐색)과 [Network README: 연결해서 보면 좋은 문서 (cross-category bridge)](../contents/network/README.md#연결해서-보면-좋은-문서-cross-category-bridge)에서 같이 볼 수 있다.

## Role-Summary Before/After 예시

network README의 auth bridge row처럼, role-summary table도 later bridge owner를 다시 복제하지 않고 anchor-first로 줄인다.

```markdown
<!-- before -->
| 브라우저가 cookie를 저장/전송하고 session/JWT가 request에 어디 실리는지 이해 | `primer / auth bridge` | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md), [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md), [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) |
```

```markdown
<!-- after -->
| 브라우저가 cookie를 저장/전송하고 session/JWT가 request에 어디 실리는지 이해 | `primer / auth bridge` | [Browser Session Spring Auth](#browser-session-spring-auth), [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) |
```

이 패턴이면 role-summary table은 local bridge subsection을 가리키는 navigator로 남고, 실제 primer/deep-dive bundle owner는 later bridge section이 맡는다.

## 출력 해석

```text
knowledge/cs/contents/network/README.md: quick '빠른 탐색' (line 91) vs bridge '연결해서 보면 좋은 문서 (cross-category bridge)' (line 165) -> 5 overlap(s)
  quick line 120 / bridge line 167: ./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md
```

이 출력은 quick-start가 "어디로 들어갈지 정하는 entrypoint" 역할을 넘어서, later bridge bundle의 실제 문서 리스트를 다시 펼치기 시작했다는 뜻이다.

## 왜 별도 check가 필요한가

- README quick-start는 navigator entrypoint여야 하고, later grouped bridge section은 cross-category bundle owner여야 한다.
- `역할별 라우팅 요약`의 bridge row도 같은 navigator entrypoint여야 하고, later bridge section owner와 경쟁하면 안 된다.
- 둘이 동시에 같은 긴 doc list를 들고 있으면 link/reverse-link 관리가 한 번 더 흔들린다.
- 작은 rename이나 bridge re-balance가 생길 때 quick-start와 bridge section을 둘 다 고쳐야 해서 drift가 빨리 생긴다.

## 한 줄 정리

quick-start와 role-summary bridge row는 entrypoint, later grouped bridge section은 detailed bundle owner로 분리하고, overlap check + 수동 QA rule로 그 경계를 감시한다.
