# RAG Design for `CS-study`

> 한 줄 요약: 이 저장소를 검색 가능한 학습 지식베이스로 만들기 위한 chunking, metadata, citation 기준을 정리한다.

## 이 폴더의 역할

`CS-study`는 단일 문서 모음이 아니라, 아래 네 층으로 나뉜다.

1. 진입점 문서: `README.md`, `JUNIOR-BACKEND-ROADMAP.md`, `ADVANCED-BACKEND-ROADMAP.md`, `SENIOR-QUESTIONS.md`
2. 카테고리 인덱스: `contents/*/README.md`
3. 심화 문서: `contents/**/**/*.md`
4. 보조 자산: `materials/`, `code/`, `img/`

RAG에서는 이 네 층을 같은 무게로 보지 않는다.  
질문 유형에 따라 먼저 찾을 문서와, 보조 근거로 붙일 문서를 분리해야 한다.

## 권장 흐름

1. 질문 분류
2. 카테고리 선택
3. 인덱스 문서 우선 탐색
4. 심화 문서 검색
5. 필요하면 코드/재료로 보강
6. 인용은 가장 가까운 원문으로 고정

## 바로 읽을 문서

- [Chunking and Metadata](./chunking-and-metadata.md)
- [Source Priority and Citation](./source-priority-and-citation.md)
- [Topic Map](./topic-map.md)
- [Query Playbook](./query-playbook.md)
- [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
- [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
- [Question Decomposition Examples](./question-decomposition-examples.md)
- [Retrieval Failure Modes](./retrieval-failure-modes.md)
- [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
- [RAG Ready Checklist](../RAG-READY.md)
