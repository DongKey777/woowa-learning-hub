---
schema_version: 3
title: Object Metadata Service 설계
concept_id: system-design/object-metadata-service-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- object metadata service
- bucket
- object key
- versioning
aliases:
- object metadata service
- bucket
- object key
- versioning
- checksum
- lifecycle
- multipart upload
- presigned url
- replication
- metadata partition
- Object Metadata Service 설계
- object metadata service design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/system-design/file-storage-presigned-url-cdn-design.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/search-indexing-pipeline-design.md
- contents/system-design/search-system-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Object Metadata Service 설계 설계 핵심을 설명해줘
- object metadata service가 왜 필요한지 알려줘
- Object Metadata Service 설계 실무 트레이드오프는 뭐야?
- object metadata service 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Object Metadata Service 설계를 다루는 deep_dive 문서다. object metadata service는 대용량 파일의 위치, 버전, 권한, 무결성 정보를 중앙에서 관리하는 스토리지 제어 평면이다. 검색 질의가 object metadata service, bucket, object key, versioning처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Object Metadata Service 설계

> 한 줄 요약: object metadata service는 대용량 파일의 위치, 버전, 권한, 무결성 정보를 중앙에서 관리하는 스토리지 제어 평면이다.

retrieval-anchor-keywords: object metadata service, bucket, object key, versioning, checksum, lifecycle, multipart upload, presigned url, replication, metadata partition

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [File Storage, Presigned URL, CDN 설계](./file-storage-presigned-url-cdn-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)

## 핵심 개념

오브젝트 저장은 바이너리만 저장한다고 끝나지 않는다.  
실전에서는 metadata가 더 중요할 때가 많다.

- object key
- version
- owner
- checksum
- content type
- lifecycle state
- encryption metadata
- replication status

즉, metadata service는 파일 스토리지의 진짜 뇌다.

## 깊이 들어가기

### 1. Metadata와 blob storage를 분리한다

대용량 파일은 object storage에 두고, 메타데이터는 별도 DB에 둔다.

이유:

- 조회 패턴이 다르다
- 권한/버전/상태가 중요하다
- blob 전체를 읽지 않아도 된다

### 2. Capacity Estimation

예:

- 10억 objects
- object당 metadata 1 KB

메타데이터만으로도 엄청난 규모가 된다.  
여기서 중요한 건 단순 저장량보다 인덱스, partition, lookup latency다.

봐야 할 숫자:

- metadata lookup QPS
- upload commit latency
- version count
- replication lag
- lifecycle job backlog

### 3. 데이터 모델

핵심 필드:

- bucket_id
- object_key
- version_id
- size
- checksum
- storage_class
- created_at
- deleted_at
- owner_id
- encryption_key_id

버전이 있으면 삭제도 보통 soft delete나 tombstone으로 처리한다.

### 4. 업로드 흐름

일반적인 흐름:

1. client가 upload intent를 만든다
2. metadata service가 presigned URL 또는 upload session을 발급한다
3. client가 blob store에 업로드한다
4. commit 시 metadata를 최종 확정한다

이 흐름이 없으면 업로드 중단/재시도에서 상태가 꼬인다.

### 5. 일관성

object metadata는 강한 일관성이 필요한 경로와 eventual consistency가 가능한 경로가 섞인다.

- 새 object 생성: 강한 일관성 선호
- replication status: eventual consistency 허용
- listing: 약간의 지연 허용
- delete marker: 정책에 따라 다름

### 6. Lifecycle와 TTL

오브젝트는 영원히 보관되지 않는다.

- temporary upload
- archive transition
- expired delete
- legal hold

지연 job으로 lifecycle을 관리하면 오브젝트 수명이 시스템 정책과 맞는다.

### 7. 검색과 메타데이터

사용자는 종종 파일 이름, owner, tag로 찾고 싶어 한다.

그 경우:

- metadata index
- full-text search
- tag index

를 분리한다.

이 부분은 [Search 시스템 설계](./search-system-design.md)와 [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)와 연결된다.

## 실전 시나리오

### 시나리오 1: presigned upload

문제:

- 클라이언트가 직접 대용량 파일을 올려야 한다

해결:

- metadata service가 upload session 발급
- blob store에 직접 업로드
- commit 시 metadata 확정

### 시나리오 2: 버전 복구

문제:

- 실수로 잘못된 버전을 덮었다

해결:

- version history를 유지
- 이전 버전으로 restore

### 시나리오 3: 대량 listing

문제:

- bucket에 object가 너무 많아 listing이 느리다

해결:

- partitioned metadata store
- prefix index
- pagination cursor

## 코드로 보기

```pseudo
function createUpload(bucket, key, user):
  version = newVersionId()
  session = createUploadSession(bucket, key, version, user)
  return presignedUrl(session)

function commitUpload(session, checksum):
  validate(session, checksum)
  metadataStore.save(session.object, checksum, state="READY")
```

```java
public ObjectMetadata commit(UploadSession session, String checksum) {
    validateChecksum(session, checksum);
    return metadataRepository.save(session.toMetadata(checksum));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Metadata DB + blob store | 분리가 명확하다 | 시스템이 둘로 나뉜다 | 대부분의 object storage |
| Inline metadata in blob store | 단순하다 | 조회/검색이 약하다 | 작은 시스템 |
| Versioned metadata | 복구가 쉽다 | 저장이 늘어난다 | 실서비스 |
| Eventual listing | 확장성이 좋다 | 최신성 지연 | 대규모 bucket |
| Strong commit confirmation | 안전하다 | latency 증가 | 중요 파일 업로드 |

핵심은 오브젝트 스토리지가 단순 파일 저장이 아니라 **버전, 정책, 검색, 복구를 담는 데이터 시스템**이라는 점이다.

## 꼬리질문

> Q: 왜 blob와 metadata를 분리하나요?
> 의도: 저장 구조 분리 이유 이해 확인
> 핵심: 조회, 권한, 버전, lifecycle이 blob보다 metadata에 더 가깝기 때문이다.

> Q: listing이 왜 어려운가요?
> 의도: 대규모 prefix 탐색 이해 확인
> 핵심: object 수가 많으면 prefix 탐색과 pagination이 비용이 커진다.

> Q: versioning이 왜 중요한가요?
> 의도: 복구와 감사 이해 확인
> 핵심: 실수 overwrite와 삭제 후 복구를 가능하게 한다.

> Q: presigned URL은 왜 쓰나요?
> 의도: 대용량 업로드 경로 이해 확인
> 핵심: 서버를 경유하지 않고 직접 업로드해 확장성을 확보한다.

## 한 줄 정리

Object metadata service는 blob storage의 위치, 버전, 정책, 검색 가능성을 관리해 대용량 파일 시스템의 제어 평면 역할을 한다.

