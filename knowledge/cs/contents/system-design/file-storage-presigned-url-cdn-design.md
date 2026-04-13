# File Storage Presigned URL + CDN 설계

> 한 줄 요약: 대용량 파일 업로드/다운로드는 애플리케이션을 통하지 않고 object storage와 CDN으로 직접 흘려보내는 구조가 확장성과 비용 면에서 유리하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [Cache-Control 실전](../network/cache-control-practical.md)
> - [HTTPS / HSTS / MITM](../security/https-hsts-mitm.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)

---

## 핵심 개념

파일 저장 시스템은 "파일을 저장하는 API"가 아니다.  
실제로는 다음을 같이 해결해야 한다.

- 업로드 대역폭을 애플리케이션에서 떼어낸다.
- 접근 제어를 유지한다.
- 파일 크기가 커져도 서버가 죽지 않게 한다.
- 다운로드는 빠르게, 비용은 적게 만든다.
- 썸네일/미리보기/바이러스 검사 같은 후처리를 분리한다.

그래서 보통 구조는 다음과 같다.

- metadata service
- object storage
- presigned URL
- CDN
- async processing pipeline

---

## 깊이 들어가기

### 1. 직접 업로드 vs Presigned URL

| 방식 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 앱 서버 경유 | 제어가 쉽다 | 대역폭/메모리 비용이 크다 | 매우 작은 파일 |
| Presigned URL | 서버 부하가 낮다 | 권한/만료 관리가 필요하다 | 일반적인 파일 업로드 |

Presigned URL의 핵심은 "클라이언트가 storage에 직접 쓰되, 서버가 허용한 짧은 시간만 가능하게 하는 것"이다.

### 2. 업로드 흐름

1. 클라이언트가 업로드 요청을 보낸다.
2. 서버가 권한을 확인한다.
3. 서버가 presigned URL과 object key를 발급한다.
4. 클라이언트가 storage에 직접 업로드한다.
5. 업로드 완료 이벤트로 후처리를 시작한다.

### 3. 다운로드 흐름과 CDN

다운로드는 object storage를 직접 때리면 비용과 지연이 커진다.  
그래서 CDN을 앞에 두고 cache-control과 versioning을 맞춘다.

핵심 포인트:

- public 파일과 private 파일을 분리한다.
- URL에 version 또는 object key를 넣는다.
- 무효화가 필요하면 key를 새로 발급한다.

### 4. 후처리 파이프라인

파일 저장은 업로드 끝이 아니다.

- 바이러스 검사
- 이미지 리사이즈
- thumbnail 생성
- 메타데이터 추출
- 변환 작업(PDF preview 등)

이 작업은 비동기 큐로 분리해야 한다.

### 5. 보안

Presigned URL은 편하지만 남용되기 쉽다.

- 만료 시간을 짧게 잡는다.
- 업로드 가능한 MIME type과 크기를 제한한다.
- object key를 예측 불가능하게 만든다.
- 공개/비공개 버킷을 분리한다.

보안 경계는 [HTTPS / HSTS / MITM](../security/https-hsts-mitm.md)와 [Spring Security 아키텍처](../spring/spring-security-architecture.md) 관점으로 같이 봐야 한다.

### 6. 비용과 성능

가장 큰 비용은 보통 세 가지다.

- egress
- storage
- CDN cache miss

대용량 업로드 시스템은 "서버 CPU"보다 "네트워크와 저장 비용"이 먼저 터지는 경우가 많다.

---

## 실전 시나리오

### 시나리오 1: 프로필 이미지 업로드

요구사항:

- 5MB 이하
- 썸네일 생성 필요
- 인증된 사용자만 업로드 가능

설계:

- presigned URL 발급
- object storage direct upload
- thumbnail worker 비동기 처리
- CDN으로 이미지 서빙

### 시나리오 2: 대용량 동영상 업로드

문제:

- 파일이 너무 커서 재전송 비용이 크다.

대응:

- multipart/resumable upload
- chunk 단위 전송
- 업로드 세션 관리
- 완료 후 merge

### 시나리오 3: 공개 자료 배포

문제:

- 다운로드 트래픽이 폭증할 수 있다.

대응:

- CDN 앞단 배치
- cache-control 최적화
- versioned URL

---

## 코드로 보기

```pseudo
function createUploadSession(userId, fileName, contentType):
    assert authorized(userId)
    objectKey = generateKey(userId, fileName)
    url = storage.presignPut(objectKey, expiresIn=10m, contentType=contentType)
    saveMetadata(objectKey, userId, status="UPLOADING")
    return {objectKey, url}
```

```java
public UploadSession createUploadSession(long userId, String fileName, String contentType) {
    assertAuthorized(userId);
    String objectKey = objectKeyGenerator.generate(userId, fileName);
    URL presigned = objectStorage.presignPut(objectKey, Duration.ofMinutes(10), contentType);
    fileMetadataRepository.save(new FileMetadata(objectKey, userId, UPLOADING));
    return new UploadSession(objectKey, presigned);
}
```

### cache-control 예시

```http
Cache-Control: public, max-age=86400, immutable
```

버전이 바뀌는 파일이라면 URL을 바꾸는 편이 무효화보다 낫다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 앱 서버 경유 | 제어가 쉽다 | 비싸고 느리다 | 작은 파일 |
| Presigned URL | 부하가 낮다 | 권한/만료 설계 필요 | 일반적인 파일 저장 |
| CDN 전면 배치 | 다운로드가 빠르다 | 무효화가 어렵다 | 정적/반정적 파일 |
| Private bucket | 보안이 좋다 | 서빙이 복잡하다 | 민감 자료 |

핵심 기준은 "파일 업로드/다운로드를 앱의 책임으로 둘지, storage/CDN의 책임으로 옮길지"다.

---

## 꼬리질문

> Q: 왜 업로드를 애플리케이션 서버를 거치게 하지 않나요?
> 의도: 병목과 비용 구조를 이해하는지 확인
> 핵심: 서버 대역폭과 메모리를 낭비하고, 대용량 파일에서 확장성이 떨어진다.

> Q: CDN 캐시는 왜 안 맞는 경우가 있나요?
> 의도: cache-control과 key versioning 이해 여부 확인
> 핵심: 무효화와 권한 경계를 잘못 잡으면 stale data 또는 보안 문제가 생긴다.

## 한 줄 정리

파일 저장은 presigned URL로 업로드를 분리하고, CDN으로 다운로드를 분산하며, 후처리와 보안을 비동기로 분리하는 설계다.
