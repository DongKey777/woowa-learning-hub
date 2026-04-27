# Shared Markdown Link Scanner

> 한 줄 요약: fence/code-span-aware markdown target parsing을 link QA script들이 함께 써서, 처음 링크를 고치는 사람도 check마다 다른 판정을 받지 않게 만드는 repo-local QA note다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Link Regression Fixtures](./link-regression-fixtures.md)
> - [Local Asset Existence Lint](./local-asset-existence-lint.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Fence False-Link Precheck](./fence-false-link-precheck.md)
> - [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)

> retrieval-anchor-keywords: shared markdown link scanner, markdown target parser, fence aware link scan, code span aware link scan, inline link parser, reference style target parser, nested paren markdown target, angle bracket markdown target, qa parser alignment, local asset lint parser, readme reverse link parser, fence false link parser, beginner broken link triage

## 언제 보나

- asset lint, fence precheck, README reverse-link check가 같은 문서를 다르게 읽는 것처럼 보일 때
- target path에 괄호가 들어가거나 `<...>` 감싼 path, reference-style link definition, inline code span이 섞여 naive regex가 흔들릴 때
- broken-link false positive를 줄이면서 "어느 check부터 고쳐야 하나"를 빠르게 정하고 싶을 때

## 공통 scanner가 하는 일

- prose scan과 fenced code block scan을 분리한다.
- prose scan에서는 inline code span을 먼저 가려서 backticked markdown syntax를 실제 link target으로 세지 않는다.
- inline markdown link/image target은 nested parentheses와 angle-bracket target을 같은 방식으로 읽는다.
- reference-style link definition target도 같은 normalization으로 읽는다.
- target 뒤에 붙은 `"title"` / `'title'` suffix는 벗기고 실제 path/anchor만 비교한다.

공유 구현 위치는 `docs/markdown_link_scanner.py`다. link QA rule을 바꿀 때는 각 script에서 regex를 따로 늘리기보다 이 파일을 먼저 맞추는 편이 덜 흔들린다.

## 지금 이 parser를 같이 쓰는 check

| check | 왜 같은 parser를 쓰나 | 다음 step |
|---|---|---|
| [Local Asset Existence Lint](./local-asset-existence-lint.md) | markdown target을 prose/code-span-aware하게 읽고 실제 file 존재 여부만 좁게 본다 | missing target을 바로 복구 |
| [Asset Filename Lint](./asset-filename-lint.md) | 같은 markdown target 집합에서 filename hygiene만 다시 본다 | rename 후보를 작게 큐잉 |
| [Fence False-Link Precheck](./fence-false-link-precheck.md) | fenced block 안 literal markdown 예시를 같은 target parser로 읽어 false positive를 먼저 분리한다 | spacing guard 또는 fence 낮추기 |
| [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md) | 같은 target parser로 category `README.md#...` return path와 stale slug를 본다 | navigator return path 복구 |

## 초보자 기준으로 고치는 순서

1. fenced example이 literal markdown인지 먼저 [Fence False-Link Precheck](./fence-false-link-precheck.md)로 분리한다.
2. 실제 asset path가 없는지 [Local Asset Existence Lint](./local-asset-existence-lint.md)로 확인한다.
3. path는 살아 있는데 이름이 불안하면 [Asset Filename Lint](./asset-filename-lint.md)로 rename cue를 본다.
4. category 문서를 손본 wave라면 [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)로 return path까지 닫는다.

## 어디로 이어서 가나

- literal markdown/HTML example과 balanced-paren target regression fixture를 같이 보려면 [Link Regression Fixtures](./link-regression-fixtures.md)로 간다.
- link label, filename, spacing guard 규칙 자체를 손봐야 하면 [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)로 간다.
- 전체 QA note index로 돌아가려면 [RAG Design](./README.md)를 다시 본다.

## 한 줄 정리

같은 markdown target을 asset/fence/README check가 같은 방식으로 읽어야, beginner도 "이번 줄이 왜 실패했는지"를 한 번에 이해하고 고칠 수 있다.
