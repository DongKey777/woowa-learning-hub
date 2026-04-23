# Auxiliary Asset Filename Audit

> 한 줄 요약: `knowledge/cs/contents/**`에서 markdown과 inline HTML이 실제로 가리키는 보조 자산(`img/`·`code/`와 local-asset HTML form)에도 `materials/`와 같은 보수적인 filename charset 규칙을 적용해 link/reverse-link noise를 줄이는 repo-local QA note다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)
> - [Orphaned Auxiliary Asset Drift Scan](./orphaned-auxiliary-asset-drift-scan.md)
> - [Source Priority and Citation](./source-priority-and-citation.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: auxiliary asset filename audit, auxiliary asset charset qa, img asset filename qa, code asset filename qa, reverse-link asset hygiene, scanner-safe image path, scanner-safe code path, repo-local asset audit, linked asset filename check, java class filename audit, html img src audit, html asset link audit, local a href asset audit, srcset asset audit, picture source srcset hygiene

## 언제 보나

- `contents/**` 문서에서 `./img/...`, `img/...`, `./code/...` 링크를 추가하거나 수정한 뒤
- 같은 문서에서 local asset을 markdown 대신 HTML `<img src>`, `<a href>`, `<source src>`, `srcset`으로 연결했을 때
- review 전에 punctuation-heavy linked asset filename만 먼저 걸러야 하면 [Asset Filename Lint](./asset-filename-lint.md)를 먼저 돌리고, 그 다음 이 문서 기준으로 broader audit을 이어 간다.
- `materials/` filename 정리는 끝났지만 `img/`·`code/` link target은 아직 같은 기준으로 훑지 않았을 때
- broken-link보다는 asset basename/dir segment 문자셋 때문에 reverse-link noise가 생기는지 먼저 분리하고 싶을 때

## 이번 wave 범위

- `knowledge/cs/contents/**/*.md` 안의 markdown inline link/image, HTML `<img src>`, local-asset `<a href>`, `<source src>`, `srcset` candidate URL을 본다.
- `srcset`은 `1x`, `2x`, `800w` 같은 descriptor를 떼고 candidate URL 각각을 따로 본다.
- 외부 URL과 `#anchor`는 이번 wave 범위에 넣지 않는다.
- local HTML `<a href>`가 `materials/` PDF를 가리키면 filename 규칙은 [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)의 repo-local PDF/image short rule을 그대로 따른다.
- link target이 실제 파일로 resolve되는지와, path segment가 보수 규칙을 넘지 않는지만 확인한다.
- 실제 file은 남아 있지만 contents 문서에서 더는 링크하지 않는 `img/`·`code/` orphan queue는 이번 문서 범위 밖이며 [Orphaned Auxiliary Asset Drift Scan](./orphaned-auxiliary-asset-drift-scan.md)에서 따로 본다.

## HTML-linked form coverage

| form | local asset일 때 보는 것 | 이번 repo 관찰 |
|---|---|---|
| `<img src="img/foo.png">` | `img/` path 존재 여부, basename/dir segment 문자셋, lowercase extension | `knowledge/cs/contents/network/README.md`에서 local image 4개를 이 형태로 사용 중 |
| `<a href="./materials/foo.pdf">` | local asset이면 markdown inline link와 같은 filename 규칙 + rename 후 stale path 확인 | 현재 `knowledge/cs/contents/**`의 HTML `<a href>`는 `design-pattern/mvc-python.md`의 외부 URL만 확인됐고 local asset anchor는 없었다 |
| `<source src="img/foo.webp">` | `src` target을 일반 HTML asset처럼 본다 | 이번 wave에서 관찰되지 않았다 |
| `<img srcset="img/foo.png 1x, img/foo@2x.png 2x">`, `<source srcset="...">` | candidate URL 각각을 따로 본다 | 이번 wave에서 `knowledge/cs/contents/**`에 `srcset`은 없었다 |

직접 확인이 필요할 때는 아래 한 줄로 HTML-linked asset form만 먼저 좁힌다.

```bash
rg -n --glob '*.md' '<a\\b[^>]*href=|<img\\b[^>]*src=|<source\\b[^>]*src=|srcset=' knowledge/cs/contents
```

## 보수 규칙

### `img/`

- stem과 directory segment는 `한글`, 영문자, 숫자, `_`, `-`만 유지한다.
- 확장자는 소문자 image 확장자(`png`, `jpg`, `jpeg`, `webp`, `gif`, `svg`)로 고정한다.
- 공백, `&`, `#`, `%`, `?`, 괄호, 쉼표처럼 URL/HTML/정규식에서 의미가 강한 문자는 넣지 않는다.

### `code/`

- directory segment도 같은 보수 문자셋으로 유지한다.
- 언어 관례상 필요한 `CamelCase` filename은 허용하되, 기호 대신 link label에 설명을 싣는다.
- `.`은 확장자 앞에서만 쓰고, 경로를 설명하려고 `+`, `&`, 공백, 괄호를 path에 넣지 않는다.

## 현재 확인된 linked asset 묶음

- algorithm: `code/BellmanFordTest.java`, `code/DijkstraTest.java`, `code/FloydWarshallTest.java`, `code/KruskalTest.java`, `code/two_pointer.cpp`, `img/chess_board_1.png`
- data-structure: `code/LinkedList/SinglyLinkedList.java`, `code/LinkedList/DoublyLinkedList.java`, `code/LinkedList/LinkedListExample.java`, `code/Stack/ArrayStack.java`, `code/Stack/LinkedStack.java`, `code/Stack/StackExample.java`, `code/Queue/ArrayQueue.java`, `code/Queue/LinkedQueue.java`, `code/Queue/QueueExample.java`, `code/Tree/Tree.ts`
- network: `img/osi-and-tcp-ip.png`, `img/osi-7-layer.png`, `img/3-way-handshake.png`, `img/4-way-handshake.png`
- HTML local-asset form 관찰: `network/README.md`의 `<img src>` 4건
- HTML external form 관찰: `design-pattern/mvc-python.md`의 `<a href="https://...">` 1건
- HTML `srcset`: 현재 `knowledge/cs/contents/**`에서는 관찰되지 않음

## 이번 wave 결과

- 현재 `knowledge/cs/contents/**`에서 실제로 링크된 `img/`·`code/` 자산은 모두 존재한다.
- 현재 `knowledge/cs/contents/**`에서 local HTML asset form은 `network/README.md`의 `<img src>`뿐이었고 모두 존재한다.
- HTML `<a href>`는 현재 외부 URL만 확인됐으므로 local asset hygiene debt는 남지 않았다.
- `srcset`은 아직 쓰이지 않지만, 이후 도입되면 candidate URL 각각을 같은 규칙으로 audit해야 한다.
- 공백, `&`, `#`, `%`, `?`, 괄호 같은 outlier는 이번 범위에서 발견되지 않았다.
- rename이 필요한 asset은 없었고, 보수 규칙을 문서화하는 쪽이 이번 wave의 가장 작은 고가치 수정이다.
- linked asset audit가 깨끗해도 unlinked orphan file은 별도 debt로 남을 수 있으므로 file-level drift는 [Orphaned Auxiliary Asset Drift Scan](./orphaned-auxiliary-asset-drift-scan.md)으로 분리해 본다.

## 다시 흔들릴 때 고치는 순서

1. asset basename/dir segment를 scanner-safe 형태로 먼저 정규화한다.
2. 같은 턴에 markdown link와 HTML `src` / `href` / `srcset` candidate를 함께 갱신한다.
3. 이전 basename이 `knowledge/cs/`와 `docs/`에 남았는지 `rg`로 한 번 더 확인한다.
4. code example의 class/function 설명이 더 필요하면 path가 아니라 link label에 넣는다.

## 한 줄 정리

`img/`·`code/`뿐 아니라 local HTML `<a href>` / `srcset` candidate도 같은 보수 규칙으로 묶어 관리하면 link/reverse-link QA가 덜 흔들린다.
