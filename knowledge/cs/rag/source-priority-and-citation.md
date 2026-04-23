# Source Priority and Citation

> 한 줄 요약: 질문 유형마다 먼저 볼 문서와 마지막에 인용할 문서를 나눠야 RAG가 덜 흔들린다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Chunking and Metadata](./chunking-and-metadata.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)

> retrieval-anchor-keywords: source priority, citation guide, citation policy, evidence ranking, primary source, secondary source, tertiary source, asset evidence qa, auxiliary asset filename audit, img asset evidence, code asset evidence, local html asset evidence, reverse-link evidence hygiene

## 우선순위 원칙

이 저장소는 문서 성격이 뚜렷하다. 따라서 검색 우선순위도 문서 타입별로 나눈다.

### 1차 소스

- `README.md`
- `JUNIOR-BACKEND-ROADMAP.md`
- `ADVANCED-BACKEND-ROADMAP.md`
- `SENIOR-QUESTIONS.md`
- `contents/*/README.md`

이들은 "어디를 봐야 하는지"를 알려준다.

### 2차 소스

- `contents/**/deep dive` 문서
- `contents/**/qa` 섹션
- `contents/**/README.md`의 상세 항목

이들은 "무엇이 맞는지"를 설명한다.

### 3차 소스

- `code/`
- `materials/`
- `img/`

이들은 설명 보강용이다. 답변 본문보다 증거로 쓰는 편이 낫다.
`img/`, `code/`, local HTML `src` / `href` / `srcset`를 증거로 붙일 때는 path 자체가 QA에 안전한지 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)으로 먼저 확인해 두면 이후 reverse-link wave에서 덜 흔들린다.

## 질문별 우선순위

### 학습 순서 질문

1. `README.md`
2. `JUNIOR-BACKEND-ROADMAP.md`
3. `ADVANCED-BACKEND-ROADMAP.md`
4. `contents/*/README.md`

### 개념 설명 질문

1. 해당 카테고리 `README.md`
2. 심화 문서
3. 관련 `SENIOR-QUESTIONS.md` 항목
4. 필요 시 코드/자료

### 비교/트레이드오프 질문

1. 비교 대상 문서 둘 다
2. `SENIOR-QUESTIONS.md`
3. `README.md`의 카테고리 개요

### 운영/장애 질문

1. 심화 문서의 `실전 시나리오`
2. `SENIOR-QUESTIONS.md`
3. 관련 `materials/`
4. 관련 `code/`

### 증상/에러 문자열 질문

1. `rag/retrieval-anchor-keywords.md`
2. 해당 카테고리 `README.md`
3. symptom을 직접 다루는 심화 문서
4. 관련 `SENIOR-QUESTIONS.md`

## 인용 규칙

- 답변에는 가능한 한 원문 경로를 붙인다.
- 한 문단에 여러 출처를 섞지 말고, 주장마다 1차 근거를 둔다.
- 문서 간 중복이 있으면 가장 구체적인 문서를 인용한다.
- `README.md`는 요약 근거로, 심화 문서는 설명 근거로, `materials/`는 보조 근거로 쓴다.
- 증상 질의는 anchor keyword로 후보를 넓힌 뒤, 인용은 가장 구체적인 심화 문서에 고정한다.

## 추천 인용 문구 패턴

```markdown
이 부분은 [인덱스와 실행 계획] (../contents/database/index-and-explain.md)와
[쿼리 튜닝 체크리스트] (../contents/database/query-tuning-checklist.md)를 같이 보면 된다.
```

## 실전 기준

- 정의를 말할 때는 index/README를 인용한다.
- 원리와 trade-off를 말할 때는 deep dive를 인용한다.
- 장애와 운영을 말할 때는 실전 시나리오와 `SENIOR-QUESTIONS.md`를 인용한다.
- 코드 조각은 설명보다 짧고 정확해야 한다. 길면 보조 링크로 넘긴다.
- repo-local `img/`·`code/`나 local HTML asset form을 근거로 인용할 때는 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md) 기준으로 target 존재 여부와 filename hygiene를 먼저 고정한다.

## 한 줄 정리

먼저 `README`와 로드맵으로 길을 잡고, 답의 핵심은 심화 문서에서 인용하고, 코드와 자료는 마지막 증거로 쓰는 것이 이 repo의 기본 규칙이다.
