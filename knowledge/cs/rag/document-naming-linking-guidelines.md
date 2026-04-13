# Document Naming and Linking Guidelines

> 한 줄 요약: 이름과 링크 규칙을 고정해야 RAG도, 사람이 읽는 탐색도 덜 흔들린다.

## Naming Rules

### 파일명

- 파일명은 주제를 짧고 명확하게 나타낸다.
- 공백은 `-`로 연결한다.
- 개념이 비교형이면 비교 대상을 파일명에 드러낸다.
- 운영/장애형이면 `playbook`, `failure`, `traps`, `debugging` 같은 단어를 붙인다.

### 좋은 예

- `jwt-deep-dive.md`
- `spring-transaction-debugging-playbook.md`
- `distributed-cache-design.md`
- `http2-multiplexing-hol-blocking.md`

### 피할 예

- `misc.md`
- `notes-2.md`
- `final-final.md`
- `new-doc.md`

## Linking Rules

### 1. README는 진입점만 담당한다

- 각 카테고리의 `README.md`는 목록과 순서만 보여준다.
- 원리와 예시는 deep dive로 넘긴다.

### 2. deep dive는 인접 문서를 링크한다

좋은 링크는 질문이 다음으로 넘어갈 수 있게 한다.

예:

- `AOP` -> `@Transactional`
- `JWT` -> `OAuth2`
- `gRPC` -> `HTTP/2`
- `cache` -> `database` + `system-design`

### 3. 교차 링크는 시각을 바꿀 수 있어야 한다

같은 주제라도 관점이 다르면 다른 문서로 보낸다.

예:

- `Spring` 관점: 프록시/빈/트랜잭션
- `Java` 관점: 바이트코드/JIT/GC
- `OS` 관점: 스레드/커널/I/O

### 4. 링크는 과하지 않게

- 문장마다 링크를 달지 않는다.
- 문서 끝과 섹션 시작에 집중한다.
- 검색 힌트가 되는 문서만 남긴다.

### 5. Retrieval Anchor Keywords를 남긴다

- 운영/장애형 문서는 `retrieval-anchor-keywords` 줄을 함께 둔다.
- 한글 개념어, 영어 원어, 약어, 에러 문자열, 도구 이름을 같이 남긴다.
- 예: `direct buffer`, `off-heap`, `RSS`, `NMT`, `OutOfMemoryError: Direct buffer memory`

## Recommended Link Topology

```text
README
  -> category README
    -> deep dive
      -> adjacent deep dive
      -> rag/topic-map.md
      -> rag/query-playbook.md
```

## Metadata Hints

링크는 메타데이터의 `linked_paths`에도 남긴다.

- `path`
- `category`
- `doc_type`
- `section`
- `linked_paths`

이 조합이 있어야 검색 결과를 재탐색하기 쉽다.

## Maintenance Rules

- 파일명 변경 시 관련 README를 같이 갱신한다.
- 새 문서를 만들면 topic map에도 반영할지 검토한다.
- 새 운영형 문서를 만들면 retrieval anchor keyword도 같이 검토한다.
- 비슷한 문서가 2개 이상 생기면 `cross-domain-bridge-map.md`에 관계를 적는다.

## 한 줄 정리

문서명은 검색 키워드이고, 링크는 탐색 경로다. 둘을 같이 고정해야 RAG가 덜 흔들린다.
