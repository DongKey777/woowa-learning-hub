# CDN Image Transformation Pipeline 설계

> 한 줄 요약: CDN image transformation pipeline은 원본 이미지를 edge 가까이에서 리사이즈, 포맷 변환, 최적화해 빠르고 저렴하게 서빙하는 시스템이다.

retrieval-anchor-keywords: cdn image transformation, resize, format conversion, webp avif, edge compute, image cache, variant key, origin fetch, optimization pipeline, thumbnail

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Storage Presigned URL + CDN 설계](./file-storage-presigned-url-cdn-design.md)
> - [Object Metadata Service 설계](./object-metadata-service-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)
> - [Search 인덱싱 파이프라인 설계](./search-indexing-pipeline-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)

## 핵심 개념

이미지 변환 파이프라인은 단순 썸네일 생성기가 아니다.  
실전에서는 아래를 함께 다룬다.

- resize
- crop
- format conversion
- quality tuning
- cache key versioning
- origin protection
- variant explosion control

즉, CDN 변환은 저장과 배포 사이에서 이미지 파생물을 만드는 edge 최적화 시스템이다.

## 깊이 들어가기

### 1. 왜 변환을 edge에 두는가

원본 서버가 이미지 파생을 직접 처리하면 병목이 생긴다.

- CPU 비용 증가
- 업로드/서빙 경로 혼합
- 캐시 적중률 저하

그래서 변환은 CDN이나 edge worker로 옮긴다.

### 2. Capacity Estimation

예:

- 하루 1,000만 이미지 요청
- 변형 조합 10개
- 평균 이미지 300KB

variant explosion이 핵심 문제다.  
무조건 많은 변형을 만들면 캐시가 깨진다.

봐야 할 숫자:

- variant count
- cache hit ratio
- origin fetch rate
- transform latency
- egress cost

### 3. 변환 키 설계

캐시 키는 파생 파라미터를 포함해야 한다.

```text
image:{objectKey}:w=300:h=300:fit=cover:fmt=webp:q=80
```

키가 부정확하면 잘못된 이미지가 캐시된다.  
너무 세밀하면 variant가 폭발한다.

### 4. 원본 보호

원본 저장소가 CDN 변환의 직접 폭주를 맞지 않도록 해야 한다.

- origin shield
- request collapsing
- signed URL
- rate limit

특히 인기 이미지 하나가 origin을 죽이는 hot object 문제가 자주 생긴다.

### 5. 포맷과 품질

보통 다음을 고려한다.

- JPEG
- PNG
- WebP
- AVIF

채널과 브라우저에 따라 최적 포맷이 다르므로 content negotiation 또는 user-agent rule이 필요하다.

### 6. 캐시 무효화

이미지는 수정되면 무효화가 어렵다.

권장:

- versioned object key
- immutable cache
- new variant path

CDN 캐시를 지우는 것보다 URL을 바꾸는 편이 더 안정적이다.

### 7. 안전한 변환

이미지 변환도 보안 이슈가 있다.

- decompression bomb
- oversized input
- malformed image

그래서 transform worker는 input validation이 필요하다.

## 실전 시나리오

### 시나리오 1: 프로필 이미지 썸네일

문제:

- 다양한 크기의 썸네일이 필요하다

해결:

- width/height 기반 variant
- cacheable path
- immutable URL

### 시나리오 2: 원본 바이럴

문제:

- 하나의 이미지가 폭발적으로 조회된다

해결:

- edge cache hit 우선
- origin shield
- request coalescing

### 시나리오 3: 포맷 최적화

문제:

- 브라우저별 최적 포맷이 다르다

해결:

- WebP/AVIF 우선
- fallback to JPEG

## 코드로 보기

```pseudo
function transform(url, spec):
  key = makeVariantKey(url, spec)
  if cache.exists(key):
    return cache.get(key)
  original = fetchOrigin(url)
  image = resizeAndConvert(original, spec)
  cache.put(key, image)
  return image
```

```java
public ImageVariant serve(String objectKey, TransformSpec spec) {
    return transformCache.getOrLoad(makeKey(objectKey, spec), () -> pipeline.transform(objectKey, spec));
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Origin-side transform | 제어가 쉽다 | CPU/latency 부담 | 작은 서비스 |
| Edge transform | 빠르고 확장성 좋다 | 운영 복잡도 | 대규모 CDN |
| Pre-generated variants | 조회가 매우 빠르다 | 저장 비용 증가 | 인기 콘텐츠 |
| On-demand transform | 저장 효율적이다 | 첫 요청이 느리다 | 긴 꼬리 변형 |
| Immutable URL | 무효화가 쉽다 | 새 URL 관리 필요 | 대부분의 이미지 서빙 |

핵심은 이미지 변환이 단순 미디어 기능이 아니라 **variant 관리와 원본 보호를 포함한 서빙 파이프라인**이라는 점이다.

## 꼬리질문

> Q: 왜 캐시 키에 transform spec을 넣어야 하나요?
> 의도: variant 분리 이해 확인
> 핵심: 서로 다른 크기/포맷 결과를 구분해야 하기 때문이다.

> Q: origin shield는 왜 필요한가요?
> 의도: hot object와 origin 보호 이해 확인
> 핵심: 인기 이미지의 폭주가 원본 저장소를 죽이지 않게 한다.

> Q: 변환을 미리 생성하는 것과 on-demand의 차이는 무엇인가요?
> 의도: 저장과 latency trade-off 이해 확인
> 핵심: 미리 생성은 빠르지만 저장이 늘고, on-demand는 절약되지만 첫 요청이 느리다.

> Q: 이미지 변환에서 보안 문제는 무엇인가요?
> 의도: 비정상 input 방어 이해 확인
> 핵심: malformed file과 압축 폭탄을 막아야 한다.

## 한 줄 정리

CDN image transformation pipeline은 변형 캐시와 원본 보호를 통해 이미지 서빙을 빠르게 하고, 파생물 폭발을 통제하는 시스템이다.

