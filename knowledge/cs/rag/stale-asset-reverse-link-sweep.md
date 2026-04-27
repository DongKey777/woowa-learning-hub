# Stale Asset Reverse-Link Sweep

> 한 줄 요약: non-Markdown asset rename 뒤 예전 basename을 가리키는 inbound local markdown/HTML link가 남았는지 묶어서 보여 주는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [RAG Design: QA Check Order Matrix](./README.md#qa-check-order-matrix)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Local Asset Existence Lint](./local-asset-existence-lint.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)
> - [Fence False-Link Precheck](./fence-false-link-precheck.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: stale asset reverse-link sweep, stale reverse link, renamed asset orphan reference, asset rename inbound link, missing local asset target, reverse-link sweep, old basename scan, stale basename grep, old basename grep, post-rename grep, rg old basename, repo-local asset rename qa, inbound markdown asset reference, asset rename regression check, orphaned asset link, reverse-link hygiene, html asset stale link, local a href stale link, srcset stale target, poster stale target, video poster stale link, audio src stale link, track src stale link, local asset existence lint

## 언제 돌리나

- `materials/`, `img/`, `code/` 자산 이름을 바꾸거나 위치를 옮긴 직후
- asset basename은 바꿨는데 README, deep dive, HTML `src`/`href`/`poster`/`srcset` 중 어디가 아직 old path를 들고 있는지 빠르게 보고 싶을 때
- rename 직후 old basename이 `knowledge/cs/`와 `docs/` markdown에 남았는지 한 줄 grep으로 바로 확인하고 싶을 때
- review 전에 "파일은 이미 rename됐는데 inbound link가 일부만 따라왔는가"를 별도 확인하고 싶을 때

## rename 직후 한 줄 grep

가장 빠른 1차 확인은 old basename 그대로 grep하는 것이다.

```bash
rg -n --glob '*.md' -F '<old-basename.ext>' knowledge/cs docs
```

- `<old-basename.ext>`를 rename 전 basename으로 바꾼다. 예: `CS_(Agile).pdf`, `윤가영_database_&Index.pdf`
- 출력이 남으면 그 문서들이 아직 pre-rename basename을 들고 있으므로 broken reverse-link 후보를 같은 턴에 바로 고친다.
- 출력이 없으면 obvious한 stale-basename reference는 일단 비운 상태다. 이어서 아래 sweep을 돌리면 missing target 기준으로 inbound reference를 다시 묶어 볼 수 있다.
- basename뿐 아니라 old path segment도 같이 바뀌었다면 같은 명령에서 basename 대신 old relative path를 넣어 한 번 더 확인한다.

## 실행

```bash
python docs/stale_asset_reverse_link_check.py
```

특정 경로만 보고 싶으면 path를 넘긴다.

```bash
python docs/stale_asset_reverse_link_check.py knowledge/cs/contents/database knowledge/cs/contents/software-engineering
```

## 무엇을 잡나

- prose 영역의 markdown inline link / image target
- prose 영역의 reference-style link target
- markdown 안 HTML `src` / `href` / `poster`가 가리키는 repo-local asset path
- HTML `srcset`의 candidate URL (`1x`, `2x`, `800w` descriptor는 떼고 URL만 검사)
- `<video>`, `<audio>`, `<track>` 같은 media tag의 local asset target도 same missing-target 묶음으로 본다
- 실제 파일이 더는 존재하지 않는 non-Markdown local target만 본다
- 결과는 missing target별로 묶어서 "어느 문서들이 아직 old basename을 들고 있나"를 reverse-link 형태로 보여 준다

다음은 범위에서 뺀다.

- local `.md` 문서 링크와 `#anchor`
- `http://`, `https://`, `mailto:`, `data:` 같은 외부 target
- fenced code block 안의 literal markdown 예시

## 실패했을 때 고치는 순서

1. 실제 rename된 현재 asset path를 확인한다.
2. 같은 턴에 markdown link, image link, HTML `src` / `href` / `poster` / `srcset`을 모두 새 path로 바꾼다.
3. old basename이 `knowledge/cs/`와 `docs/`에 남았는지 `rg -n --glob '*.md' -F '<old-basename.ext>' knowledge/cs docs`로 한 번 더 확인한다.
4. `python docs/stale_asset_reverse_link_check.py`를 다시 돌린다.
5. path 자체의 문자셋도 함께 점검하려면 [Asset Filename Lint](./asset-filename-lint.md)를 이어서 돌린다.

## 출력 해석

```text
Missing local asset targets still have inbound markdown references.
knowledge/cs/contents/software-engineering/materials/CS_(Agile).pdf -> 2 inbound reference(s)
  knowledge/cs/contents/software-engineering/README.md:811: inline-link -> ./materials/CS_(Agile).pdf
  knowledge/cs/contents/software-engineering/eXtremeProgramming.md:9: inline-link -> ./materials/CS_(Agile).pdf
```

이 출력은 asset이 이미 `CS_Agile.pdf` 같은 새 이름으로 옮겨졌거나 삭제됐는데, inbound markdown 두 곳이 아직 old basename을 잡고 있다는 뜻이다.

## 이번 wave 메모

- rename 사례 기준으로 `윤가영_database_&Index.pdf -> 윤가영_database_index.pdf`, `CS_(Agile).pdf -> CS_Agile.pdf`를 stale reverse-link 후보로 다시 확인했다.
- 현재 sweep에서는 old basename을 가리키는 inbound local asset link가 남지 않았다.
- 이번 wave의 핵심 수정은 "missing target을 target별로 묶어 보여 주는 sweep"을 추가해 다음 rename에서 orphaned reference를 더 빨리 잡게 한 것이다.

## 왜 별도 check가 필요한가

- [Local Asset Existence Lint](./local-asset-existence-lint.md)는 unresolved local asset target을 generic gate로 실패시키고, 이 문서는 rename 직후 old basename grep과 missing target 묶음까지 포함하는 rename-focused triage다.
- [Asset Filename Lint](./asset-filename-lint.md)는 "현재 link된 path의 filename이 scanner-safe한가"를 본다.
- [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)는 "현재 link된 `img/`·`code/` 자산이 존재하고 보수 규칙을 지키는가"를 본다.
- rename이 이미 끝난 뒤에는 old basename이 missing target이 되므로, 이번 check처럼 inbound reference를 missing target 기준으로 다시 묶어 보는 편이 더 빠르다.

## 다음 단계와 돌아가기

- check 시작점이 헷갈리면 [RAG Design: QA Check Order Matrix](./README.md#qa-check-order-matrix)에서 filename hygiene 선행 여부와 README return-path 후속 여부를 먼저 고른다.
- rename wave에서 아직 fenced literal markdown도 같이 손볼 예정이면 [Fence False-Link Precheck](./fence-false-link-precheck.md)부터 다시 보고 false positive 후보를 먼저 비운다.
- stale target을 다 비운 뒤 새 asset path 이름까지 다시 점검하려면 [Asset Filename Lint](./asset-filename-lint.md)로 이어 간다.
- QA note index로 돌아가려면 [RAG Design](./README.md)를 다시 본다.

## 한 줄 정리

asset rename 뒤에는 old basename `rg` 확인과 stale asset reverse-link sweep을 함께 돌려야 broken reverse-link를 가장 빨리 잡는다.
