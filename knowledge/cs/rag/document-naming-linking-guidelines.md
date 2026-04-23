# Document Naming and Linking Guidelines

> 한 줄 요약: 이름과 링크 규칙을 고정해야 RAG도, 사람이 읽는 탐색도 덜 흔들린다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Navigation Taxonomy](./navigation-taxonomy.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Retrieval Failure Modes](./retrieval-failure-modes.md)
> - [Source Priority and Citation](./source-priority-and-citation.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)
> - [Orphaned Auxiliary Asset Drift Scan](./orphaned-auxiliary-asset-drift-scan.md)
> - [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)
> - [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)
> - [Fence False-Link Precheck](./fence-false-link-precheck.md)
> - [README Quick-Start / Bridge Overlap Check](./readme-bridge-overlap-check.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)

> retrieval-anchor-keywords: document naming, linking guidelines, markdown link hygiene, reverse-link hygiene, readme anchor reverse-link, stale heading slug, same-category readme anchor, materials asset filenames, img asset filenames, code asset filenames, auxiliary asset charset qa, scanner-safe filenames, repo-local pdf filename, repo-local image filename, repo-local code path, java class filename, camelcase code path, lowercase image extension, lowercase pdf extension, mixed-case extension, uppercase png, uppercase pdf, markdown link scanner, asset link guideline, asset filename lint, stale asset reverse link, asset rename sweep, missing local asset target, punctuation-heavy asset filename, ampersand filename, html asset link hygiene, local a href asset link, srcset asset link, literal markdown syntax, code fence false positive, spacing guard, related-doc links, linked paths, retrieval anchor placement, readme labels, navigator links, quick-start overlap lint, bridge overlap check, grouped bridge section

## Naming Rules

### 파일명

- 파일명은 주제를 짧고 명확하게 나타낸다.
- 공백은 `-`로 연결한다.
- 개념이 비교형이면 비교 대상을 파일명에 드러낸다.
- 운영/장애형이면 `playbook`, `failure`, `traps`, `debugging` 같은 단어를 붙인다.

### 좋은 예

- `jwt-deep-dive.md`
- `spring-transaction-debugging-playbook.md`
- `distributed-cache-design.md`
- `http2-multiplexing-hol-blocking.md`

### 피할 예

- `misc.md`
- `notes-2.md`
- `final-final.md`
- `new-doc.md`

### `materials/`, `img/`, `code/` 자산 파일명

`contents/**/materials/`, `contents/**/img/`, `contents/**/code/` 아래 파일은 markdown 본문이 아니어도 local link와 reverse-link QA에서 자주 다시 읽힌다.
Markdown 자체는 더 넓은 문자 집합을 허용하지만, 단순 링크 스캐너나 후처리 스크립트는 보수적인 filename 가정을 두는 경우가 많다.

- 권장 문자셋은 `한글`, 영문자, 숫자, `_`, `-`, `.` 정도로 유지한다.
- `&`, `#`, `%`, `?`, 공백, 괄호처럼 URL/HTML/정규식에서 별도 의미가 강한 문자는 가능하면 피한다.
- 연결 부호가 필요하면 기호 대신 단어로 푼다. 예: `and`, `index`, `guide`
- `code/`는 언어 관례상 `CamelCase` filename이 필요할 수 있으므로 class/file naming convention은 유지하되, directory segment와 나머지 path는 같은 보수 규칙으로 둔다.
- 설명이 더 필요하면 path가 아니라 link label에 싣고, 기존 자산을 정규화했다면 해당 markdown link나 HTML `src` / `href` / `srcset`도 같은 턴에 같이 바꾼다.

예:

- `윤가영_database_&Index.pdf` -> `윤가영_database_index.pdf`
- `img/thread-state-diagram (final).PNG` -> `img/thread-state-diagram.png`
- `code/LinkedList/SinglyLinkedList.java`

#### repo-local PDF/image short rule

markdown에서 직접 가리키는 repo-local PDF/image는 아래 최소 규칙으로 고정한다.

- stem은 `한글`, 영문자, 숫자, `_`, `-`만 쓴다.
- `.`은 확장자 앞 한 번만 쓰고, 확장자는 소문자 (`pdf`, `png`, `jpg`, `jpeg`, `webp`, `gif`, `svg`)로 고정한다.
- 공백, `&`, `#`, `%`, `?`, 괄호, 쉼표처럼 스캐너/URL/정규식에서 의미가 강한 문자는 넣지 않는다.
- 파일명을 바꿨다면 같은 턴에 markdown link를 함께 바꾸고, 이전 basename이 남았는지 `rg`로 한 번 더 확인한다.
- review 전에 markdown이 가리키는 local asset path만 빠르게 훑고 싶으면 repo root에서 `python docs/asset_filename_lint.py`를 먼저 돌린다.
- markdown link와 무관하게 `knowledge/cs/**` 전체 PDF/image basename의 rename queue만 먼저 만들고 싶으면 [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)을 본다.
- rename 뒤 old basename inbound reference까지 같이 훑고 싶으면 `python docs/stale_asset_reverse_link_check.py`를 이어서 돌린다.

일부 markdown link scanner는 image/PDF target을 lowercase extension allowlist로 분류한다.
그래서 `diagram.PNG`, `handout.PdF`처럼 mixed-case extension이 남으면 실제 파일이 열려도 image/PDF bucket에서 빠지거나 reverse-link sweep에서 old/new basename이 따로 잡힐 수 있다.
image/PDF rename target과 markdown link target은 처음부터 소문자 확장자로 통일한다.

짧게 기억하면 `stem=[가-힣A-Za-z0-9_-]+`, `ext=소문자`, `기호/공백 금지`다.

예:

- `윤가영_database_index.pdf`
- `thread-state-diagram.png`
- `queueing-diagram.jpeg`

피할 예:

- `윤가영 database &Index.pdf`
- `thread-state-diagram (final).PNG`
- `queue,state?.jpeg`

#### repo-local code short rule

markdown에서 직접 가리키는 repo-local `code/` path는 아래 최소 규칙으로 고정한다.

- directory segment는 `한글`, 영문자, 숫자, `_`, `-`만 쓴다.
- filename stem은 언어 관례에 맞춰 `CamelCase` 또는 `snake_case`를 쓰되, 공백과 기호는 넣지 않는다.
- `.`은 확장자 앞 한 번만 쓰고, class/function qualifier는 path 대신 link label에 둔다.
- path를 바꿨다면 같은 턴에 markdown link를 함께 바꾸고, 이전 basename/path segment가 남았는지 `rg`로 한 번 더 확인한다.
- markdown가 가리키는 `code/` path만 review 전에 한 번 더 확인하고 싶으면 `python docs/asset_filename_lint.py`를 같이 돌린다.
- rename 뒤 missing target 기준 inbound reference를 묶어 보고 싶으면 `python docs/stale_asset_reverse_link_check.py`도 같이 돌린다.

예:

- `code/LinkedList/SinglyLinkedList.java`
- `code/Queue/ArrayQueue.java`
- `code/two_pointer.cpp`

피할 예:

- `code/LinkedList/Singly Linked List.java`
- `code/Queue/ArrayQueue(final).java`
- `code/two-pointer?.cpp`

## Linking Rules

### 1. README는 진입점만 담당한다

- 각 카테고리의 `README.md`는 목록과 순서만 보여준다.
- 원리와 예시는 deep dive로 넘긴다.

### 2. deep dive는 인접 문서를 링크한다

좋은 링크는 질문이 다음으로 넘어갈 수 있게 한다.

예:

- `AOP` -> `@Transactional`
- `JWT` -> `OAuth2`
- `gRPC` -> `HTTP/2`
- `cache` -> `database` + `system-design`

### 3. 교차 링크는 시각을 바꿀 수 있어야 한다

같은 주제라도 관점이 다르면 다른 문서로 보낸다.

예:

- `Spring` 관점: 프록시/빈/트랜잭션
- `Java` 관점: 바이트코드/JIT/GC
- `OS` 관점: 스레드/커널/I/O

### 4. 링크는 과하지 않게

- 문장마다 링크를 달지 않는다.
- 문서 끝과 섹션 시작에 집중한다.
- 검색 힌트가 되는 문서만 남긴다.

### 5. 코드 펜스 안의 literal markdown에는 spacing guard를 둔다

링크/역링크 QA는 종종 fenced code block 안쪽까지 훑는다.
이때 `]` 바로 뒤에 `(` 또는 `:`가 붙은 literal markdown 예시는 실제 링크나 reference-style link 정의가 아닌데도 false positive로 잡히기 쉽다.

- 설명용 스니펫에서는 `] (` / `] :`처럼 한 칸 띄운 spacing guard를 기본값으로 쓴다.
- guard가 필요한 위치는 code fence, QA note, regex 설명, markdown 문법 예시처럼 "문법을 보여 주는 곳"이다.
- 실제로 동작하는 링크를 만들려는 문단에서만 붙여 쓰고, literal syntax를 보여 주는 예시에서는 spacing guard를 유지한다.
- markdown 문법을 설명하는 게 아니라 `.md` path, catalog metadata, channel handle만 보여 주는 스니펫이면 fence를 `markdown` 대신 `yaml` 또는 `text`로 둔다.

예:

```text
[good-link] (./topic-map.md)
[good-ref] : ./topic-map.md
```

이렇게 두면 사람이 보기에는 충분히 읽히고, 단순 bracket-paren / bracket-colon 패턴 스캔에도 덜 걸린다.

경로만 보여 주는 metadata 예시는 markdown fence보다 아래처럼 쓰는 편이 안전하다.

```yaml
runbook_path: "./runbooks/order-bff.md"
adr_path: "./adr/adr-014-bff-per-client.md"
```

broken-link reporting 전에 repo root에서 `python docs/link_fence_false_link_check.py`를 먼저 돌리면, fenced literal markdown 후보만 따로 모아 볼 수 있다. 실행 순서와 해석은 [Fence False-Link Precheck](./fence-false-link-precheck.md)에 정리한다.

### 6. README quick-start는 bridge entrypoint만 남긴다

category `README`의 `빠른 시작` / `빠른 탐색` / `Quick Routes`는 "어느 묶음으로 들어갈지"만 정하는 entrypoint여야 한다.
later `연결해서 보면 좋은 문서 (cross-category bridge)` 구간은 실제 cross-category bundle을 길게 보관하는 owner다.

- quick-start에서는 later bridge subsection anchor나 route-map anchor를 우선 링크한다.
- 같은 local `.md` 링크가 quick-start와 later grouped bridge section에 2개 이상 같이 남으면 bridge bundle duplication으로 본다.
- symptom entrypoint 설명 때문에 quick-start에 대표 문서 1개를 두는 것은 허용되지만, later bridge bundle 전체를 다시 펼치지는 않는다.
- repo root에서 `python docs/readme_bridge_overlap_check.py`를 돌리면 이 중복 후보를 먼저 모아 볼 수 있다.

### 7. category 문서는 sibling README anchor reverse-link를 남긴다

deep dive / playbook / runbook 문서는 자기 category `README.md`의 relevant heading이나 bridge anchor로 되돌아가는 route를 하나는 남겨 두는 편이 좋다.

- `관련 문서` block이나 "이 문서 다음에 보면 좋은 문서" 같은 후속 라우팅 문장에 same-category `./README.md#...`를 둔다.
- README heading 이름을 바꾸거나 bridge anchor id를 재정리했다면 해당 문서들의 reverse-link slug도 같은 턴에 같이 바꾼다.
- file path는 살아 있어도 heading slug만 죽는 경우가 많으므로, broken-link 확인과 별개로 `python docs/readme_anchor_reverse_link_check.py <touched-path>`를 같이 돌린다.
- cross-category README anchor는 추가로 둘 수 있지만, same-category navigator return link를 대체하지는 않는다.

### 8. Retrieval Anchor Keywords를 남긴다

- 운영/장애형 문서는 `retrieval-anchor-keywords` 줄을 함께 둔다.
- 한글 개념어, 영어 원어, 약어, 에러 문자열, 도구 이름을 같이 남긴다.
- 새 문서는 기본적으로 `제목 -> 한 줄 요약 -> 관련 문서 -> retrieval-anchor-keywords -> (선택) <details>/--- -> 본문` 순서를 따른다.
- 삽입 위치는 가능하면 첫 `##` 전에 고정한다. TOC가 있더라도 anchor 줄을 먼저 두는 편이 누락이 적다.
- 기본 개수는 8~12개 정도로 두고, 대표 개념어 + 영어 alias + 운영 증상/경계 용어를 섞는다.
- 예: `direct buffer`, `off-heap`, `RSS`, `NMT`, `OutOfMemoryError: Direct buffer memory`

## Recommended Link Topology

```text
README
  -> category README
    -> deep dive
      -> adjacent deep dive
      -> rag/topic-map.md
      -> rag/query-playbook.md
```

## Metadata Hints

링크는 메타데이터의 `linked_paths`에도 남긴다.

- `path`
- `category`
- `doc_type`
- `section`
- `linked_paths`

이 조합이 있어야 검색 결과를 재탐색하기 쉽다.

## Maintenance Rules

- 파일명 변경 시 관련 README를 같이 갱신한다.
- `materials/`, `img/`, `code/` 자산 파일명을 바꿨다면 이를 가리키는 markdown link나 HTML `src` / `href` / `srcset`과 간단한 outlier 스캔도 같이 갱신한다.
- review 전에 linked local asset filename만 빠르게 재점검하려면 `python docs/asset_filename_lint.py`를 먼저 돌린다.
- repo-local PDF/image 전체 basename에서 risky rename 후보만 좁게 고르고 싶으면 [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)을 먼저 본다.
- linked asset audit와 별개로 `knowledge/cs/contents/**` 아래 unlinked `img/`·`code/` file drift를 줄이려면 `python docs/orphaned_auxiliary_asset_scan.py`를 같이 돌린다.
- repo-local PDF/image rename 뒤에는 old basename이 `knowledge/cs/`와 `docs/`에 남았는지 한 번 더 확인한다.
- category 문서를 손봤다면 same-category `README.md#...` reverse-link가 빠졌거나 stale slug가 되지 않았는지 `python docs/readme_anchor_reverse_link_check.py <touched-path>`로 확인한다.
- rename 뒤 stale inbound reference를 묶어서 확인하려면 `python docs/stale_asset_reverse_link_check.py`를 함께 돌린다.
- 새 문서를 만들면 topic map에도 반영할지 검토한다.
- 새 운영형 문서를 만들면 retrieval anchor keyword도 같이 검토한다.
- 비슷한 문서가 2개 이상 생기면 `cross-domain-bridge-map.md`에 관계를 적는다.
- link/reverse-link QA가 fenced example 하나 때문에 흔들리면, literal markdown 예시가 `] (` / `] :` guard를 지켰는지 먼저 본다.

## 한 줄 정리

문서명은 검색 키워드이고, 링크는 탐색 경로다. 둘을 같이 고정해야 RAG가 덜 흔들린다.
