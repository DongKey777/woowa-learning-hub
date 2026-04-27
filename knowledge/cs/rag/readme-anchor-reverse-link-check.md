# README Anchor Reverse-Link Check

> 한 줄 요약: category 문서가 자기 category `README.md#...`로 돌아가는 reverse-link를 잃었거나 stale heading slug를 잡고 있지 않은지 확인하는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [RAG Design: QA Check Order Matrix](./README.md#qa-check-order-matrix)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Navigation Taxonomy](./navigation-taxonomy.md)
> - [Shared Markdown Link Scanner](./shared-markdown-link-scanner.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [README Quick-Start / Bridge Overlap Check](./readme-bridge-overlap-check.md)

> retrieval-anchor-keywords: readme anchor reverse-link check, readme reverse-link check, category readme anchor qa, same-category readme anchor, stale heading slug, stale readme slug, missing reverse-link, README.md anchor drift, navigator return link, category doc readme backlink, related docs anchor hygiene, reverse-link slug check

## 언제 돌리나

- `contents/*/*.md`의 `관련 문서`나 후속 라우팅 문장을 손본 뒤
- category `README.md`에서 heading 이름이나 custom anchor id를 바꾼 뒤
- deep dive 문서가 자기 category navigator bucket으로 제대로 되돌아가는지 빠르게 확인하고 싶을 때

repo 전체에 legacy backlog가 많을 수 있으므로, 보통은 **이번 wave에서 손댄 category나 문서 path만** 넘겨서 돌리는 편이 낫다.

## 실행

```bash
python docs/readme_anchor_reverse_link_check.py knowledge/cs/contents/security
```

단일 문서만 보고 싶으면 file path를 넘긴다.

```bash
python docs/readme_anchor_reverse_link_check.py \
  knowledge/cs/contents/security/oauth2-authorization-code-grant.md
```

path를 주지 않으면 기본값으로 `knowledge/cs/contents` 전체를 스캔한다.

## 무엇을 잡나

- sibling category `README.md#...` reverse-link가 아예 없는 문서
- 같은 category `README.md`를 가리키지만 anchor slug가 더는 heading/custom id와 맞지 않는 문서
- inline link와 reference-style link definition target을 같은 parser로 읽는다
- heading slug와 explicit `<a id="..."></a>` 둘 다 유효 target로 인정한다
- fenced code block 안 예시 링크와 cross-category README anchor link는 범위에서 뺀다

## 실패했을 때 고치는 순서

1. 문서의 `관련 문서` 또는 후속 라우팅 문장에 same-category `./README.md#...` reverse-link를 넣는다.
2. README heading을 바꿨다면 문서의 old slug를 새 slug나 explicit id로 같이 바꾼다.
3. README bridge entrypoint를 custom anchor로 고정해 두었다면 그 id가 여전히 살아 있는지 확인한다.
4. 수정 후 `python docs/readme_anchor_reverse_link_check.py <touched-path>`를 다시 돌린다.

## 출력 해석

```text
knowledge/cs/contents/security/example.md -> knowledge/cs/contents/security/README.md
  stale same-category README anchor reverse-link(s):
    line 18: ./README.md#session-coherence-catalog
      suggestion: ./README.md#session-coherence--assurance-deep-dive-catalog
```

이 출력은 문서가 여전히 자기 category README로 되돌아가려 하긴 하지만, slug drift 때문에 실제 heading/custom id를 더는 못 찾는다는 뜻이다.

missing 케이스는 아래처럼 나온다.

```text
knowledge/cs/contents/security/example.md -> knowledge/cs/contents/security/README.md
  missing: add a same-category README anchor reverse-link such as `./README.md#...`.
```

## 왜 별도 check가 필요한가

- 일반 broken-link 확인은 `README.md` 파일이 존재하는지만 보고 anchor drift를 놓치기 쉽다.
- README restructure 뒤에도 sibling markdown 파일 자체는 그대로 있으므로, stale slug가 review에서 늦게 드러난다.
- quick-start/bridge overlap lint는 README 내부 ownership을 보지만, 이번 check는 개별 문서가 category navigator로 **되돌아가는 path**를 본다.
- shared parser를 asset/fence check와 같이 쓰므로, 여기서는 "같은 markdown target을 읽되 README anchor drift만 따로 본다"는 경계가 더 분명해진다.

## 다음 단계와 돌아가기

- check 시작점이 헷갈리면 [RAG Design: QA Check Order Matrix](./README.md#qa-check-order-matrix)에서 category return-path 우선인지 asset rename 후속인지 먼저 고른다.
- beginner primer가 category return path와 다음 안전한 follow-up을 둘 다 보여 주는지까지 묶어 보려면 [Primer Link Contract Lint](./primer-link-contract-lint.md)로 이어 간다.
- 같은 wave에서 local asset rename도 함께 있었다면 새 path hygiene는 [Asset Filename Lint](./asset-filename-lint.md), old basename 잔존 link는 [Stale Asset Reverse-Link Sweep](./stale-asset-reverse-link-sweep.md) 순서로 이어 간다.
- QA note index로 돌아가려면 [RAG Design](./README.md)를 다시 본다.

## 한 줄 정리

category 문서를 손봤다면 file 존재 여부만 보지 말고 `README.md#...` reverse-link가 아직 살아 있는지도 같이 확인해야 한다.
