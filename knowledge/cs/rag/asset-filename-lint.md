# Asset Filename Lint

> 한 줄 요약: review 전에 markdown과 inline HTML이 가리키는 repo-local asset path만 훑어서 punctuation-heavy filename과 mixed-case extension을 먼저 잡는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Local Asset Existence Lint](./local-asset-existence-lint.md)
> - [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)
> - [Fence False-Link Precheck](./fence-false-link-precheck.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: asset filename lint, punctuation-heavy asset filename, local asset path qa, markdown asset link lint, scanner-safe asset path, repo-local asset filename check, image filename lint, pdf filename lint, lowercase image extension, lowercase pdf extension, mixed-case extension, uppercase png, uppercase pdf, markdown link scanner, code path lint, markdown review precheck, reverse-link asset hygiene, html asset link lint, local a href lint, srcset asset lint, local asset existence lint, missing local asset target

## 언제 돌리나

- `knowledge/cs/**/*.md`나 `docs/**/*.md`에서 local asset link/image를 추가하거나 rename한 뒤
- broken-link보다 먼저 "path 자체가 scanner-safe한가"를 빠르게 가르고 싶을 때
- review 전에 `materials/`, `img/`, `code/` 링크가 공백, 괄호, `&`, extra dot stem, mixed-case extension 같은 outlier를 다시 끌고 들어왔는지 확인하고 싶을 때

## 실행

```bash
python docs/asset_filename_lint.py
```

특정 문서나 디렉터리만 보고 싶으면 path를 넘긴다.

```bash
python docs/asset_filename_lint.py knowledge/cs/contents/network/README.md docs
```

## 무엇을 잡나

- prose 영역의 markdown inline link / image target
- prose 영역의 reference-style link target
- markdown 안 HTML `src` / `href`가 가리키는 repo-local asset path
- HTML `srcset`의 candidate URL (`1x`, `2x`, `800w` descriptor는 떼고 URL만 검사)
- directory segment의 공백, 괄호, `&`, `#`, `%`, `?`, 쉼표 같은 scanner-hostile 문자
- filename stem의 extra `.`와 image/PDF 확장자의 대문자·mixed-case 사용

다음은 범위에서 뺀다.

- local `.md` 문서 링크와 `#anchor`
- `http://`, `https://`, `mailto:`, `data:` 같은 외부 target
- fenced code block 안의 예시 스니펫
- 실제 파일이 없는 unresolved local asset target 자체는 [Local Asset Existence Lint](./local-asset-existence-lint.md) 범위다.
- markdown link 유무와 무관한 repo-local PDF/image 전체 basename sweep은 [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md) 범위다.

즉, 현재 lint는 local asset 기준으로 `<img src>`, `<a href>`, `<source src>`, `srcset` candidate URL까지 한 번에 훑는다. 외부 URL과 `#anchor`는 계속 범위 밖이다.

## 실패했을 때 고치는 순서

1. asset basename이나 directory segment를 scanner-safe 형태로 바꾼다.
2. 같은 턴에 markdown link나 HTML `src` / `href` / `srcset`도 함께 갱신한다.
3. rename 뒤에는 `python docs/asset_filename_lint.py`를 다시 돌린다.
4. target 자체가 missing인지도 `python docs/local_asset_existence_lint.py`로 함께 확인한다.
5. linked asset 전체 존재 여부와 broader path 묶음은 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md) 기준으로 한 번 더 본다.

## 출력 해석

```text
knowledge/cs/contents/network/README.md:236: html-asset -> img/thread-state-diagram (final).PNG [filename stem `thread-state-diagram (final)` has scanner-hostile chars: space, (, ); extension `PNG` should be lowercase]
```

이 출력은 markdown가 실제로 가리키는 local asset path에 review 전에 정리해야 할 filename 문제가 남아 있다는 뜻이다.

## mixed-case extension note

일부 markdown link scanner는 `.png`, `.jpg`, `.jpeg`, `.pdf` 같은 lowercase allowlist로 asset type을 분류한다.
그래서 `img/diagram.PNG`, `materials/guide.PdF`는 파일이 존재해도 image/PDF link로 일관되게 집계되지 않거나 stale basename sweep에서 두 이름처럼 보일 수 있다.
이 lint에서는 이런 mixed-case extension도 조기 rename cue로 본다.

## 왜 별도 check가 필요한가

- [Local Asset Existence Lint](./local-asset-existence-lint.md)는 "path가 실제로 존재하느냐"를 보고, 이 lint는 "존재하는 path 이름이 scanner-safe하냐"를 본다.
- broken-link report는 "존재하느냐"를 말하지만, filename이 scanner-safe한지는 따로 말해 주지 않는다.
- manual audit note만 두면 review 직전에 빠르게 회귀를 막기 어렵다.
- 이 lint는 "링크는 살아 있어도 path가 QA에 불리한가"를 먼저 걸러서 rename wave를 더 작게 만든다.

## 한 줄 정리

asset 존재 여부는 [Local Asset Existence Lint](./local-asset-existence-lint.md)로, path hygiene는 이 lint로 나눠서 고정해 두는 편이 안전하다.
