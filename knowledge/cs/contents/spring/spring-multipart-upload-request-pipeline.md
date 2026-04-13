# Spring Multipart Upload Request Pipeline

> 한 줄 요약: multipart upload는 단순 파일 전송이 아니라 boundary parsing, part binding, size limits, and temp storage가 이어지는 요청 파이프라인이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)
> - [Spring Content Negotiation Pitfalls](./spring-content-negotiation-pitfalls.md)
> - [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)

retrieval-anchor-keywords: multipart, file upload, boundary parsing, MultipartResolver, MultipartFile, temp file, max file size, request body parsing, upload pipeline

## 핵심 개념

multipart 요청은 여러 파트를 가진 HTTP 요청이다.

- 파일
- 메타데이터
- 폼 필드

Spring은 이를 `MultipartResolver`를 통해 파싱한다.

즉, 업로드는 단순히 파일 하나 받는 것이 아니라 **요청 본문을 여러 파트로 분해하는 과정**이다.

## 깊이 들어가기

### 1. multipart boundary를 파싱해야 한다

요청 본문은 boundary로 구분된다.

### 2. `MultipartResolver`가 파트로 나눈다

Spring MVC는 이를 해석해 `MultipartFile`로 만들 수 있다.

### 3. 파일은 메모리나 임시 디스크에 저장될 수 있다

작으면 메모리, 크면 temp file로 넘어갈 수 있다.

### 4. size limit이 중요하다

작업이 시작되기 전에 큰 파일을 차단해야 한다.

- max file size
- max request size
- memory threshold

### 5. validation과 binding은 업로드 후에 이어진다

메타데이터와 파일명을 검증해야 한다.

## 실전 시나리오

### 시나리오 1: 파일은 올라왔는데 컨트롤러에서 null이다

multipart resolver 설정이나 요청 content type을 봐야 한다.

### 시나리오 2: 큰 파일이 올라오자마자 413이 난다

size limit이 너무 작거나 reverse proxy가 먼저 막았을 수 있다.

### 시나리오 3: 업로드는 됐는데 파일명이 깨진다

encoding과 content disposition을 확인해야 한다.

### 시나리오 4: temp file이 쌓인다

cleanup policy를 점검해야 한다.

## 코드로 보기

### multipart controller

```java
@PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public void upload(@RequestPart("file") MultipartFile file) {
    ...
}
```

### multipart config

```yaml
spring:
  servlet:
    multipart:
      max-file-size: 10MB
      max-request-size: 20MB
```

### metadata + file

```java
@PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public void upload(@RequestPart("file") MultipartFile file,
                   @RequestPart("meta") UploadMeta meta) {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| multipart upload | 브라우저와 잘 맞는다 | 파싱/임시저장 비용이 있다 | 일반 파일 업로드 |
| signed URL / presigned upload | 서버 부하를 줄인다 | 클라이언트 흐름이 복잡하다 | 대용량 파일 |
| streaming upload | 메모리 효율이 좋다 | 구현이 까다롭다 | 큰 파일/백업 |

핵심은 업로드를 "파일 전송"이 아니라 **요청 파싱과 저장 정책의 문제**로 보는 것이다.

## 꼬리질문

> Q: multipart 요청은 일반 JSON 요청과 무엇이 다른가?
> 의도: body parsing 이해 확인
> 핵심: boundary로 여러 part를 파싱해야 한다.

> Q: `MultipartResolver`는 무엇을 하는가?
> 의도: 파이프라인 이해 확인
> 핵심: multipart 본문을 파트로 분해한다.

> Q: 파일 size limit은 왜 중요한가?
> 의도: 운영 안정성 이해 확인
> 핵심: 메모리와 디스크를 보호하기 위해서다.

> Q: temp file이 왜 생기는가?
> 의도: 업로드 저장 경로 이해 확인
> 핵심: 큰 파일은 임시 디스크에 저장될 수 있다.

## 한 줄 정리

Multipart upload는 boundary parsing과 size control, temp storage가 연결된 요청 파이프라인이다.
