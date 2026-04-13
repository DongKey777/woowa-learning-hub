# RAG Ready Checklist

> 한 줄 요약: 이 저장소를 RAG에 넣을 때는 문서 구조, chunk 기준, 우선순위, citation 규칙이 이미 고정돼 있어야 한다.

## 무엇을 먼저 읽나

- [RAG README](./rag/README.md)
- [Chunking and Metadata](./rag/chunking-and-metadata.md)
- [Source Priority and Citation](./rag/source-priority-and-citation.md)
- [Topic Map](./rag/topic-map.md)
- [Query Playbook](./rag/query-playbook.md)
- [Retrieval Anchor Keywords](./rag/retrieval-anchor-keywords.md)
- [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md)
- [Retrieval Failure Modes](./rag/retrieval-failure-modes.md)
- [Master Notes](./MASTER-NOTES.md)

## 운영 규칙

1. 질문이 들어오면 카테고리를 먼저 고른다.
2. 넓거나 교차 도메인 질문이면 `master-notes/`를 먼저 붙인다.
3. `README`와 로드맵으로 범위를 정한다.
4. `topic-map`과 `cross-domain-bridge-map`으로 교차 영역을 확인한다.
5. 심화 문서의 `H2` 섹션을 우선 검색한다.
6. 증상/에러 문자열 질문이면 `retrieval-anchor-keywords`로 alias를 먼저 확장한다.
7. 코드와 `materials/`는 보강용으로만 쓴다.
8. 답변에는 원문 경로를 붙인다.
9. direct question은 `definition / mechanism / policy / troubleshooting / design`으로 먼저 분해한다.
10. `rag/*`, `RAG-READY.md`, 루트 가이드 같은 메타 문서는 기본 검색에서 우선 제외하고, RAG 자체를 묻는 질문일 때만 다시 포함한다.

## 금지

- 문서 전체를 무작정 같은 가중치로 검색하지 않는다.
- `materials/`를 심화 문서보다 먼저 인용하지 않는다.
- `README`의 요약과 깊이 문서의 세부 원리를 섞어 말하지 않는다.
- 동일한 개념을 여러 문서에서 중복 인용하지 않는다.
- 에러 문자열이나 운영 증상을 일반 개념어 하나로 뭉개서 검색하지 않는다.

## 체크 포인트

- 문서 제목이 검색 가능한가
- H2 기준 chunk가 의미 단위인가
- alias/증상 문서를 위한 `retrieval-anchor-keywords`가 들어 있는가
- linked paths가 남아 있는가
- code/materials가 보조 소스인지 구분되는가
- root guide에서 카테고리로 잘 내려갈 수 있는가
- 넓은 질문을 받아줄 `master-notes/` 상위 레이어가 있는가

## RAG 적용 대상

- 학습 경로 추천
- 개념 설명
- 비교 질문
- 장애/운영 질문
- 코드 예시가 필요한 질문

## 한 줄 정리

이 저장소의 RAG는 `README -> category README -> master-notes(필요 시) -> deep dive -> code/materials` 순으로 내려가고, chunk는 `H2` 중심, 인용은 가장 구체적인 원문 중심으로 해야 한다.
