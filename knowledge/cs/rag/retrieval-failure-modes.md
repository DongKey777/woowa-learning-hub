# Retrieval Failure Modes

> 한 줄 요약: RAG가 틀리는 방식부터 알아야 검색 품질을 복구할 수 있다.

## 왜 필요한가

검색 시스템은 보통 "찾는 것"보다 "잘못 찾는 것"이 더 문제다.
이 저장소는 같은 개념이 여러 폴더에 반복되기 때문에, 잘못된 문서를 고르는 순간 답변이 흔들린다.

## 대표 실패 모드

### 1. 개념은 맞는데 층이 틀림

예:

- `Spring` 질문인데 `Java` runtime 문서만 잡는 경우
- `DB` 질문인데 `System Design`의 개략 설계만 잡는 경우

대응:

- 먼저 `contents/*/README.md`를 찾는다.
- 다음에 deep dive를 붙인다.

### 2. README만 잡고 실전 문서를 놓침

README는 길 안내다.
정답이 필요한 질문에서 README만 보면 정의는 맞아도 운영 포인트가 빠진다.

대응:

- 정의 질문: README
- 장애/운영 질문: deep dive
- 비교 질문: deep dive 2개

### 3. 여러 문서에서 같은 말을 반복하는데 서로 다른 시각임

예:

- `cache`는 `network`, `database`, `system-design`, `software-engineering`에 다 나온다.

대응:

- 문서의 시각을 메타데이터에 남긴다.
- 답변에는 시각을 섞지 않는다.

### 4. chunk가 너무 크거나 너무 작음

- 너무 크면 검색은 되는데 답변이 둔해진다.
- 너무 작으면 문맥이 사라진다.

대응:

- 기본은 `H2`
- 표/코드/SQL은 분리
- README는 짧게 유지

### 5. 파일명은 맞는데 링크가 끊김

이 repo는 상대 링크가 많아서 구조가 조금만 어긋나도 검색이 깨진다.

대응:

- 경로 기반 검증을 한다.
- 파일명 변경 시 관련 README와 rag 문서도 같이 본다.

### 6. 질문 분해가 안 됨

예:

`Spring에서 왜 느리죠?`

이 질문은 너무 넓다.

대응:

- `Spring MVC`인지 `WebFlux`인지
- `transaction`인지 `test slice`인지
- `cache`인지 `AOP`인지

로 다시 쪼갠다.

## 복구 전략

1. 질문을 `domain`과 `intent`로 쪼갠다.
2. `README`와 `RAG-READY.md`를 먼저 찾는다.
3. `topic-map.md`로 교차 도메인을 고른다.
4. `source-priority-and-citation.md` 순서대로 인용한다.
5. 답변이 애매하면 `question-decomposition-examples.md` 패턴으로 다시 분해한다.

## 한 줄 정리

RAG의 품질은 "무엇을 찾았는가"보다 "무엇을 잘못 찾는가"를 얼마나 빨리 복구하느냐에 달려 있다.
