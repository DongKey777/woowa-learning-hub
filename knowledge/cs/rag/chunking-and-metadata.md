# Chunking and Metadata

> 한 줄 요약: `CS-study`는 파일 단위가 아니라, 제목과 섹션 단위로 잘라야 검색 품질이 안정적이다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Source Priority and Citation](./source-priority-and-citation.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)
> - [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)

> retrieval-anchor-keywords: chunking metadata, section chunking, retrieval metadata guide, linked_paths metadata, asset qa linked paths, auxiliary asset filename audit, html asset path metadata, reverse-link maintenance route

## 기본 원칙

이 저장소의 문서는 대체로 다음 구조를 따른다.

- 제목
- 한 줄 요약
- 핵심 개념
- 깊이 들어가기
- 실전 시나리오
- 코드로 보기
- 트레이드오프
- 꼬리질문
- 한 줄 정리

RAG에서는 이 구조를 그대로 활용하는 편이 좋다.

### 자르는 기준

- `H1`는 문서 정체성이다. 문서 전체의 상위 메타데이터로 남긴다.
- `H2`는 기본 chunk 경계다. 대부분의 문서는 `H2` 단위로 자른다.
- `H3`는 길이가 길 때만 보조 chunk 경계로 쓴다.
- 표, 코드블록, SQL, 명령어는 중간에 끊지 않는다.
- `README.md`와 로드맵은 짧아도 통째로 유지하는 편이 낫다.

### 예외

- `materials/*.pdf` 추출본은 문단이 깨질 수 있으니, 문단 기준으로 다시 재분할한다.
- `code/` 아래 예시는 파일 경로를 메타데이터에 남기고, 설명 텍스트와 분리한다.
- 표가 핵심인 문서는 표를 분리 chunk로 유지한다.

## 권장 메타데이터

각 chunk에는 최소한 아래 메타데이터를 붙인다.

```json
{
  "path": "contents/database/index-and-explain.md",
  "title": "인덱스와 실행 계획",
  "category": "database",
  "doc_type": "deep_dive",
  "level": "advanced",
  "chunk_type": "section",
  "section": "실전 시나리오",
  "language": "ko",
  "contains_code": true,
  "contains_table": true,
  "retrieval_anchor_keywords": [
    "redo log",
    "checkpoint",
    "crash recovery"
  ],
  "linked_paths": [
    "contents/database/transaction-isolation-locking.md",
    "contents/database/mvcc-replication-sharding.md"
  ],
  "source_priority": 80
}
```

### 추천 필드

- `path`: 원본 파일 절대 경로 또는 repo-relative path
- `title`: 문서 제목
- `category`: `database`, `network`, `spring` 같은 상위 분류
- `doc_type`: `root`, `roadmap`, `index`, `deep_dive`, `qa`, `material`, `code`
- `level`: `basic`, `intermediate`, `advanced`
- `section`: chunk의 섹션명
- `language`: `ko`, `en`, `mixed`
- `contains_code`: 코드/쿼리 포함 여부
- `contains_table`: 표 포함 여부
- `retrieval_anchor_keywords`: 동의어, 약어, 증상, 에러 문자열, 도구 이름
- `linked_paths`: 같은 질문에서 자주 같이 읽는 파일. repo-local `img/`·`code/`나 local HTML asset form이 들어간 chunk라면 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)도 같이 남겨 후속 filename/reverse-link QA route를 보존한다.
- `source_priority`: 검색 우선순위 점수

## RAG에 맞는 청크 우선순위

1. root/roadmap 질문이면 `README.md`, `JUNIOR-BACKEND-ROADMAP.md`, `ADVANCED-BACKEND-ROADMAP.md`, `SENIOR-QUESTIONS.md`
2. 개념 질문이면 `contents/*/README.md`
3. 구현/실전 질문이면 `contents/**/deep dive` 문서
4. 예시 코드 질문이면 `code/` 또는 문서 내 `코드로 보기`
5. 마지막 보강으로 `materials/`

## 실전 팁

- chunk 크기는 "토큰 수"만 보지 말고, 섹션 의미가 끊기는지 먼저 본다.
- 같은 개념이 여러 문서에 반복되면, 인용할 원문은 하나만 남기고 나머지는 링크 관계로 처리한다.
- 문서 내부 링크는 chunk metadata의 `linked_paths`에 넣어 재탐색 힌트로 쓴다.
- `retrieval-anchor-keywords` 줄이 있으면 metadata에 그대로 올려서 alias 확장에 쓴다.
- repo-local `img/`·`code/` path나 local HTML asset form을 설명하는 chunk는 `linked_paths`에서 [Auxiliary Asset Filename Audit](./auxiliary-asset-filename-audit.md)로 한 번 더 이어 두면 다음 link-maintenance wave가 adjacent QA note를 놓치지 않는다.
- README는 개념의 정의보다 위치 안내 역할을 하므로 짧은 chunk로 유지한다.

## 한 줄 정리

`CS-study`는 "파일"이 아니라 "섹션"을 검색 단위로 봐야 하고, 메타데이터는 `path`, `category`, `doc_type`, `level`, `section`, `linked_paths`가 핵심이다.
