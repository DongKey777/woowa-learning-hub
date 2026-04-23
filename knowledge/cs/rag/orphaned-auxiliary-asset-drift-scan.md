# Orphaned Auxiliary Asset Drift Scan

> 한 줄 요약: `knowledge/cs/contents/**` 아래 실제 `img/`·`code/` 파일 중 contents 문서에서 더는 직접 링크하지 않는 file-level orphan을 묶어 보는 repo-local QA note다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)
> - [Asset Filename Lint](./asset-filename-lint.md)
> - [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)
> - [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: orphaned auxiliary asset drift scan, orphaned img file audit, orphaned code file audit, unlinked img code sweep, unreferenced auxiliary asset, contents doc inbound asset scan, file-level asset drift, stale asset reentry, support file link gap, retrieval path cleanup queue

## 언제 보나

- deep dive나 README에서 예전 `img/`·`code/` link를 걷어낸 뒤, 실제 파일이 retrieval path에 그대로 남았는지 확인할 때
- linked asset QA는 통과했는데 legacy example bundle이 `contents/**` 밑에 계속 남아 있는지 별도로 보고 싶을 때
- broad rename wave를 열기 전에 "지금은 안 쓰는 자산"과 "여전히 링크 중인 자산"을 분리하고 싶을 때
- stale filename이 다시 링크 surface로 들어오기 전에 orphan queue부터 먼저 정리하고 싶을 때

## 실행

```bash
python docs/orphaned_auxiliary_asset_scan.py
```

특정 카테고리만 좁히고 싶으면 경로를 넘긴다.

```bash
python docs/orphaned_auxiliary_asset_scan.py knowledge/cs/contents/design-pattern knowledge/cs/contents/data-structure
```

## 무엇을 잡나

- `knowledge/cs/contents/**/*.md`의 markdown inline link / image, reference-style link target
- markdown 안 local HTML `<img src>`, `<a href>`, `<source src>`, `srcset` candidate
- 실제로 존재하는 `knowledge/cs/contents/**/img/**`, `knowledge/cs/contents/**/code/**` file-level asset
- inbound link가 하나도 없는 orphan file과, 그 orphan path 자체의 filename risk

다음은 범위에서 뺀다.

- `materials/` asset
- missing target은 [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md) 범위
- markdown이 이미 링크 중인 asset의 charset/path hygiene는 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)와 [Asset Filename Lint](./asset-filename-lint.md) 범위
- fenced code block 안의 literal markdown 예시

## 이번 wave 결과

- `python docs/orphaned_auxiliary_asset_scan.py` 기준으로 `knowledge/cs/contents/**/*.md` 1427개와 `img/`·`code/` asset 50개를 확인했다.
- 이 중 20개는 현재 contents 문서에서 직접 링크되고 있고, 30개는 file-level orphan으로 남아 있다.
- orphan group은 `design-pattern/code` 16개, `algorithm/code` 7개, `data-structure/code` 4개, `data-structure/img` 3개다.
- filename risk가 실제로 남은 orphan은 `data-structure/img`의 extra-dot image 3개뿐이다.

| orphan group | count | 현재 관찰 | follow-up cue |
|---|---:|---|---|
| `algorithm/code` | 7 | `KMPTest.java`, `LDS_bs.cpp`, `MergeSort.java`, `QuickSort.java`, `lis_brute.cpp`, `lis_bs.cpp`, `lis_dp.cpp`가 현재 어떤 contents 문서에서도 직접 링크되지 않는다 | 관련 deep dive에서 다시 쓸 예정이면 explicit link를 추가하고, 아니면 retrieval path 밖으로 이동할지 결정 |
| `data-structure/code` | 4 | `ILinkedList.java`, `IQueue.java`, `IStack.java`, `TrieExample.java`는 support file이지만 file-level inbound link는 없다 | implementation만 링크할지, bundle entry link를 둘지, support file을 별도 surface에서 뺄지 정한다 |
| `data-structure/img` | 3 | `그래프.001.jpeg`, `그래프.002.jpeg`, `그래프.003.jpeg`는 현재 unlinked이면서 stem extra `.` risk도 있다 | relink 전에 rename 우선. 필요 없으면 retrieval path 밖으로 이동 |
| `design-pattern/code` | 16 | `FactoryJava`, `ObserverJava`, `SingletonJava`, `SingletonPython`, `MVCPython` 예제 묶음 전체가 현재 contents 문서에서 직접 링크되지 않는다 | category 문서에 code bundle entry를 만들지, archive/quarantine 할지 먼저 결정 |

## 판정 메모

- 이 scan은 "파일 단위로 contents 문서가 다시 찾아갈 수 있는가"만 본다.
- 그래서 linked implementation 옆에 있는 interface/support file도 직접 링크가 없으면 orphan으로 남는다.
- 이 판정은 false positive를 줄이기보다 retrieval path drift를 작게 유지하는 쪽에 맞춘다.
- 즉, support file을 계속 `contents/**` 아래 둘 거라면 bundle entry link든 file-level link든 하나는 남겨 두는 편이 안전하다.

## filename-risk orphan queue

| 현재 path | 위험 이유 | 권장 rename |
|---|---|---|
| `knowledge/cs/contents/data-structure/img/그래프.001.jpeg` | stem extra `.` | `knowledge/cs/contents/data-structure/img/그래프-001.jpeg` |
| `knowledge/cs/contents/data-structure/img/그래프.002.jpeg` | stem extra `.` | `knowledge/cs/contents/data-structure/img/그래프-002.jpeg` |
| `knowledge/cs/contents/data-structure/img/그래프.003.jpeg` | stem extra `.` | `knowledge/cs/contents/data-structure/img/그래프-003.jpeg` |

## 정리 순서

1. orphan이지만 다시 쓸 asset인지 먼저 분류한다.
2. 다시 쓸 asset이면 contents 문서에 explicit link를 추가하기 전에 filename을 보수 규칙으로 정규화한다.
3. 더는 안 쓸 asset이면 `contents/**` retrieval path 밖으로 이동하거나 archive location으로 분리한다.
4. rename이나 relink 뒤에는 `python docs/orphaned_auxiliary_asset_scan.py`와 [Asset Filename Lint](./asset-filename-lint.md)를 다시 돌린다.
5. basename을 바꿨다면 [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)으로 old path inbound link도 같이 확인한다.

## 왜 별도 check가 필요한가

- [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)는 "현재 링크된 자산"만 본다.
- [Asset Filename Outlier Sweep](./asset-filename-outlier-sweep.md)는 PDF/image basename만 보고 `code/` orphan은 잡지 않는다.
- [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md)는 rename 뒤 broken inbound link를 찾지만, 조용히 남아 있는 orphan file은 찾지 못한다.

## 한 줄 정리

linked asset QA가 깨끗해도 `contents/**` 아래 unlinked `img/`·`code/` file이 남아 있으면 retrieval path drift는 계속 쌓이므로, orphan scan을 별도로 고정해 두는 편이 안전하다.
