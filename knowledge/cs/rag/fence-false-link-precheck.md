# Fence False-Link Precheck

> 한 줄 요약: broken-link reporting 전에 fenced code block 안의 markdown link-like syntax를 먼저 잡아 false positive를 줄이는 repo-local QA check다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Shared Markdown Link Scanner](./shared-markdown-link-scanner.md)
> - [Source Priority and Citation](./source-priority-and-citation.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: fence false link precheck, broken-link precheck, fenced code link qa, reverse-link false positive, literal markdown guard, spacing guard, repo-local qa check, markdown example hygiene, bracket paren scan, reference-style link guard

## 언제 돌리나

- `knowledge/cs/**/*.md` 또는 `docs/**/*.md`에서 link/reverse-link 정리를 시작하기 전
- broken-link reporting 전에 fenced example이 문제인지 먼저 분리하고 싶을 때
- literal markdown 예시를 여러 개 손본 뒤 회귀를 막고 싶을 때

## 실행

```bash
python docs/link_fence_false_link_check.py
```

특정 경로만 보고 싶으면 path를 넘긴다.

```bash
python docs/link_fence_false_link_check.py knowledge/cs/rag docs
```

## 무엇을 잡나

- fenced code block 안의 inline markdown link/image pattern
- fenced code block 안의 reference-style link definition
- target이 repo 상대경로, 절대경로, anchor, URL처럼 보이는 경우만 본다
- nested parentheses나 angle-bracket target도 asset/readme check와 같은 parser로 읽는다
- `] (` / `] :` spacing guard가 들어간 literal 예시는 통과한다

## 실패했을 때 고치는 순서

1. literal markdown 예시라면 `] (` / `] :` spacing guard로 바꾼다.
2. `.md` path나 metadata만 보여 주는 샘플이면 fence를 `text`나 `yaml`로 낮춘다.
3. 실제로 클릭 가능한 링크를 보여 주려는 문장이라면 fence 밖 prose로 옮긴다.
4. 수정 후 `python docs/link_fence_false_link_check.py`를 다시 돌린 다음 broken-link reporting을 실행한다.

## 출력 해석

```text
knowledge/cs/rag/source-priority-and-citation.md:82: inline-link in fence(markdown)
```

이 출력은 fenced snippet 안에 broken-link reporter가 링크로 오해할 만한 패턴이 남아 있다는 뜻이다.

## 왜 별도 check가 필요한가

- broken-link report가 본문과 fenced example을 같은 수준으로 훑으면 false positive가 섞인다.
- 이 precheck는 "링크가 진짜 깨졌는가"보다 먼저 "이 라인이 애초에 literal example인가"를 분리한다.
- shared parser를 써 두면 asset/readme check가 이해하는 markdown target 범위와 fence precheck 범위가 크게 어긋나지 않는다.
- 그래서 수정 순서를 `fence hygiene -> broken-link validation`으로 고정하기 쉽다.

## 한 줄 정리

broken-link reporting 전에 fence false-link precheck를 먼저 돌리면, literal markdown 예시 때문에 생기는 link/reverse-link noise를 훨씬 빨리 줄일 수 있다.
