# Asset Filename Outlier Sweep

> 한 줄 요약: `knowledge/cs/**` 아래 실제 repo-local PDF/image basename만 훑어서 rename이 필요한 filename outlier만 작게 큐잉하는 repo-local QA note다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)

> retrieval-anchor-keywords: asset filename outlier sweep, repo-local pdf image audit, targeted asset cleanup queue, risky filename backlog, extra dot image stem, scanner-safe pdf image basename, reverse-link safe rename, unlinked asset filename audit, repo-local image rename candidates, punctuation-heavy asset sweep, filename cleanup note

## 언제 보나

- markdown link lint가 아니라 `knowledge/cs/**` 실제 자산 basename 전체를 먼저 훑고 싶을 때
- legacy `materials/` / `img/` 묶음에서 공백, 괄호, `&`, extra `.` 같은 outlier가 남았는지 작게 확인할 때
- rename wave를 크게 열지 않고, 실제 cleanup 후보만 queue로 남기고 싶을 때

## 이번 wave 범위

- `knowledge/cs/**` 아래 `.pdf`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`
- markdown에서 실제로 링크되는지와 무관하게 파일명 자체만 본다.
- `code/` 자산과 directory restructure는 이번 wave 범위에 넣지 않는다.

## 판정 기준

- stem은 `한글`, 영문자, 숫자, `_`, `-`만 허용한다.
- `.`은 확장자 앞 한 번만 허용한다.
- 공백, `&`, `#`, `%`, `?`, 괄호, 쉼표, 대문자 확장자는 rename 후보로 본다.
- 한글 basename 자체는 outlier로 보지 않는다.

## 이번 wave 결과

- 총 23개 자산을 확인했다. PDF 11개, image 12개다.
- 공백, 괄호, `&`, `#`, `%`, `?`, 쉼표, 대문자 확장자 outlier는 없었다.
- rename queue에 남길 항목은 `extra dot stem`만 가진 image 3개뿐이다.
- `python docs/asset_filename_lint.py knowledge/cs docs` 결과, punctuation-heavy local asset filename을 직접 가리키는 markdown reference는 현재 없었다.

## targeted cleanup queue

| 현재 path | 위험 이유 | 권장 rename | 현재 link surface |
|---|---|---|---|
| `knowledge/cs/contents/data-structure/img/그래프.001.jpeg` | stem에 extra `.`가 있어 scanner-safe short rule을 벗어난다 | `knowledge/cs/contents/data-structure/img/그래프-001.jpeg` | `knowledge/cs/**/*.md`, `docs/**/*.md`에서 직접 reference 없음 |
| `knowledge/cs/contents/data-structure/img/그래프.002.jpeg` | stem에 extra `.`가 있어 scanner-safe short rule을 벗어난다 | `knowledge/cs/contents/data-structure/img/그래프-002.jpeg` | `knowledge/cs/**/*.md`, `docs/**/*.md`에서 직접 reference 없음 |
| `knowledge/cs/contents/data-structure/img/그래프.003.jpeg` | stem에 extra `.`가 있어 scanner-safe short rule을 벗어난다 | `knowledge/cs/contents/data-structure/img/그래프-003.jpeg` | `knowledge/cs/**/*.md`, `docs/**/*.md`에서 직접 reference 없음 |

## cleanup 순서

1. 위 3개만 rename 후보로 다룬다. 이번 wave에서는 broad rename을 열지 않는다.
2. 실제 rename을 하면 같은 턴에 old basename이 남았는지 `rg`로 다시 확인한다.
3. rename 뒤 missing target inbound reference까지 보고 싶으면 [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)을 이어서 본다.
4. markdown이 새 basename을 직접 가리키기 시작했다면 [Asset Filename Lint](./asset-filename-lint.md)로 link surface를 다시 확인한다.

## 한 줄 정리

이번 repo-local PDF/image sweep에서 실제 cleanup queue로 남길 outlier는 data-structure image 3개의 extra-dot stem뿐이고, 그 외 space/special-char risk는 현재 없다.
