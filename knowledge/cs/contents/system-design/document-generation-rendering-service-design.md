---
schema_version: 3
title: Document Generation / Rendering Service 설계
concept_id: system-design/document-generation-rendering-service-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- document generation
- rendering service
- pdf generation
- docx
aliases:
- document generation
- rendering service
- pdf generation
- docx
- template rendering
- html to pdf
- async render
- page break
- watermark
- snapshot
- queue
- Document Generation / Rendering Service 설계
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/file-storage-presigned-url-cdn-design.md
- contents/system-design/object-metadata-service-design.md
- contents/system-design/job-queue-design.md
- contents/system-design/cdn-image-transformation-pipeline-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/config-distribution-system-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Document Generation / Rendering Service 설계 설계 핵심을 설명해줘
- document generation가 왜 필요한지 알려줘
- Document Generation / Rendering Service 설계 실무 트레이드오프는 뭐야?
- document generation 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Document Generation / Rendering Service 설계를 다루는 deep_dive 문서다. document generation and rendering service는 템플릿과 데이터를 받아 PDF, DOCX, 이미지, HTML 같은 문서를 안정적으로 생성하는 비동기 렌더링 시스템이다. 검색 질의가 document generation, rendering service, pdf generation, docx처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Document Generation / Rendering Service 설계

> 한 줄 요약: document generation and rendering service는 템플릿과 데이터를 받아 PDF, DOCX, 이미지, HTML 같은 문서를 안정적으로 생성하는 비동기 렌더링 시스템이다.

retrieval-anchor-keywords: document generation, rendering service, pdf generation, docx, template rendering, html to pdf, async render, page break, watermark, snapshot, queue

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Storage Presigned URL + CDN 설계](./file-storage-presigned-url-cdn-design.md)
> - [Object Metadata Service 설계](./object-metadata-service-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [CDN Image Transformation Pipeline 설계](./cdn-image-transformation-pipeline-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Config Distribution System 설계](./config-distribution-system-design.md)

## 핵심 개념

문서 생성은 단순 문자열 치환이 아니다.  
실전에서는 아래를 동시에 만족해야 한다.

- 템플릿 버전 관리
- 데이터 바인딩
- PDF/DOCX rendering
- 페이지 나눔과 레이아웃
- 비동기 생성과 재시도
- 다운로드/보관 경로 분리

즉, document service는 템플릿과 데이터를 안정적으로 결합해 출력물을 만드는 렌더링 파이프라인이다.

## 깊이 들어가기

### 1. 어떤 문서를 생성하는가

대표 대상:

- invoice
- contract
- report
- certificate
- shipping label
- letter/pdf export

문서 유형에 따라 정확도, 레이아웃, 속도가 다르다.

### 2. Capacity Estimation

예:

- 일 100만 문서
- 평균 생성 3초
- 피크 batch 1만 건

실시간과 배치가 섞이면 rendering pool과 queue 설계가 중요하다.

봐야 할 숫자:

- render latency
- queue depth
- 실패율
- output size
- retry count

### 3. 파이프라인

```text
Template
  + Data
  -> Validate
  -> Render
  -> Post-process
  -> Store
  -> Deliver
```

### 4. template versioning

문서 출력은 재현 가능해야 한다.

- 템플릿 버전
- 데이터 스냅샷
- 렌더 엔진 버전
- locale/format version

계약서와 invoice는 나중에 동일하게 재생성 가능해야 한다.

### 5. Layout and pagination

문서 렌더링의 어려움은 페이지다.

- page break
- orphan/widow line
- table overflow
- font fallback

HTML to PDF는 편하지만 레이아웃이 예상과 다를 수 있다.

### 6. Asynchronous rendering

무거운 렌더는 요청 경로에서 분리한다.

- job queue
- worker pool
- status callback
- download URL

이 부분은 [Job Queue 설계](./job-queue-design.md)와 연결된다.

### 7. Storage and delivery

생성된 문서는 object storage에 저장하는 편이 일반적이다.

- private bucket
- signed download URL
- retention policy
- audit trail

이 부분은 [File Storage Presigned URL + CDN 설계](./file-storage-presigned-url-cdn-design.md)와 [Object Metadata Service 설계](./object-metadata-service-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: invoice PDF

문제:

- 월말 invoice를 대량 생성해야 한다

해결:

- batch job
- template snapshot
- object storage 저장

### 시나리오 2: 계약서 생성

문제:

- 템플릿 버전이 바뀌면 재현이 어려워진다

해결:

- template version pinning
- data snapshot 저장

### 시나리오 3: 한국어/영문 혼합 보고서

문제:

- 폰트와 줄바꿈이 깨진다

해결:

- locale-aware font bundle
- rendering engine fixed version

## 코드로 보기

```pseudo
function renderDocument(templateId, data):
  template = templateRepo.loadVersioned(templateId)
  validate(data, template.schema)
  output = renderer.render(template, data)
  objectKey = storage.put(output)
  return objectKey
```

```java
public DocumentJob submit(DocumentRequest req) {
    return jobQueue.enqueue(req);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Sync render | 단순하다 | 느리다 | 작은 문서 |
| Async render | 요청이 빠르다 | 상태 추적 필요 | 대부분의 실서비스 |
| HTML to PDF | 구현이 빠르다 | 레이아웃 이슈 | 일반 보고서 |
| Native PDF engine | 제어가 좋다 | 운영 난이도 | 정교한 출력 |
| Versioned templates | 재현 가능하다 | 관리가 늘어난다 | 계약/청구 문서 |

핵심은 문서 생성이 단순 출력이 아니라 **템플릿, 렌더링, 보관, 재현성을 함께 관리하는 파이프라인**이라는 점이다.

## 꼬리질문

> Q: 왜 템플릿 버전이 중요한가요?
> 의도: 재현성과 감사 이해 확인
> 핵심: 나중에 같은 문서를 다시 만들어야 할 수 있기 때문이다.

> Q: HTML to PDF가 항상 좋은가요?
> 의도: 렌더링 엔진 trade-off 이해 확인
> 핵심: 빠르지만 페이지 레이아웃이 깨질 수 있다.

> Q: 문서 생성이 느리면 어떻게 하나요?
> 의도: 비동기 처리 이해 확인
> 핵심: queue와 worker pool로 요청 path와 분리한다.

> Q: 생성 결과는 어디에 저장하나요?
> 의도: 보관과 배포 분리 이해 확인
> 핵심: object storage와 signed URL이 일반적이다.

## 한 줄 정리

Document generation / rendering service는 템플릿과 데이터를 버전화해 렌더링하고, 생성된 산출물을 안전하게 저장·배포하는 시스템이다.

