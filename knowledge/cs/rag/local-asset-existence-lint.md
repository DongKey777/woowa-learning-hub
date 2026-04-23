# Local Asset Existence Lint

> 한 줄 요약: markdown과 inline HTML이 가리키는 repo-local asset path 중 실제 파일이 없는 target을 review 전에 바로 실패시키는 companion QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Shared Markdown Link Scanner](./shared-markdown-link-scanner.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)
> - [Fence False-Link Precheck](./fence-false-link-precheck.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: local asset existence lint, unresolved local asset target, missing local asset target lint, repo-local asset existence check, markdown asset existence lint, html asset existence lint, broken asset path qa, missing image target, missing pdf target, missing code path target, local a href existence lint, srcset existence lint, reverse-link existence check, stale asset target lint

## 언제 돌리나

- 새 `materials/`, `img/`, `code/` link를 추가했는데 실제 경로가 살아 있는지 review 전에 바로 실패시키고 싶을 때
- asset rename, move, delete 뒤 markdown/HTML reference가 새 path를 따라왔는지 generic gate로 확인하고 싶을 때
- filename은 scanner-safe해 보여도 link target 자체가 missing인지 빠르게 분리하고 싶을 때
- broader broken-link report 전에 repo-local asset target만 좁게 확인하고 싶을 때

## 실행

```bash
python docs/local_asset_existence_lint.py
```

특정 문서나 디렉터리만 보고 싶으면 path를 넘긴다.

```bash
python docs/local_asset_existence_lint.py knowledge/cs/contents/database docs
```

## 무엇을 잡나

- prose 영역의 markdown inline link / image target
- prose 영역의 reference-style link target
- markdown 안 HTML `src` / `href`가 가리키는 repo-local asset path
- HTML `srcset`의 candidate URL (`1x`, `2x`, `800w` descriptor는 떼고 URL만 검사)
- nested parentheses와 angle-bracket target도 shared markdown parser 기준으로 읽는다
- 실제 파일이 존재하지 않는 non-Markdown local target

다음은 범위에서 뺀다.

- local `.md` 문서 링크와 `#anchor`
- `http://`, `https://`, `mailto:`, `data:` 같은 외부 target
- fenced code block 안의 literal markdown 예시
- path는 존재하지만 filename stem, directory segment, mixed-case extension이 risky한 경우는 [Asset Filename Lint](./asset-filename-lint.md) 범위다.

## 실패했을 때 고치는 순서

1. 실제로 살아 있어야 하는 asset path가 무엇인지 먼저 확인한다.
2. asset이 옮겨졌다면 markdown link, image link, HTML `src` / `href` / `srcset`을 같은 턴에 모두 새 path로 갱신한다.
3. asset이 지워진 것이 맞다면 reference 자체를 삭제하거나 대체 근거로 바꾼다.
4. `python docs/local_asset_existence_lint.py`를 다시 돌린다.
5. path는 살아 있지만 문자셋이나 확장자 규칙이 불안하면 [Asset Filename Lint](./asset-filename-lint.md)를 이어서 돌린다.
6. rename 직후 old basename grep과 missing target 묶음이 더 필요하면 [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)을 이어서 본다.

## 출력 해석

```text
Markdown/HTML references still point at unresolved repo-local asset targets.
knowledge/cs/contents/software-engineering/materials/CS_(Agile).pdf -> 2 inbound reference(s)
  knowledge/cs/contents/software-engineering/README.md:811: inline-link -> ./materials/CS_(Agile).pdf
  knowledge/cs/contents/software-engineering/eXtremeProgramming.md:9: inline-link -> ./materials/CS_(Agile).pdf
Restore the asset or update every inbound reference, then rerun this lint.
```

이 출력은 markdown나 inline HTML이 어떤 local asset path를 가리키고 있지만, 그 path에 실제 파일이 없다는 뜻이다.

## 왜 별도 check가 필요한가

- [Asset Filename Lint](./asset-filename-lint.md)는 "현재 target path 문자열이 scanner-safe한가"를 보고, 이 check는 "그 target이 실제로 존재하는가"를 본다.
- broader broken-link report는 문서 link, anchor, fenced example noise까지 한 번에 섞이기 쉬운데, 이 check는 repo-local asset target만 좁게 실패시킨다.
- [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)는 rename triage와 old basename grep 흐름까지 같이 설명하는 rename-focused 문서이고, 여기서는 generic pre-review gate로 바로 돌릴 수 있게 이름을 분리했다.
- shared parser를 [Fence False-Link Precheck](./fence-false-link-precheck.md), [README Anchor Reverse-Link Check](./readme-anchor-reverse-link-check.md)와 같이 쓰므로 "어떤 markdown target을 읽었는가"는 맞추고, 여기서는 existence만 따로 본다.

## 한 줄 정리

filename hygiene와 별개로, markdown/HTML이 가리키는 repo-local asset target이 실제로 존재하는지도 lint로 따로 고정해 두는 편이 안전하다.
