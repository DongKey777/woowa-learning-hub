# CDN 기초 (CDN Basics)

> 한 줄 요약: CDN은 정적 파일과 자주 요청되는 콘텐츠를 원본 서버 대신 전 세계 가까운 서버에서 전달해 응답 속도를 높이고 원본 부하를 줄인다.

**난이도: 🟢 Beginner**

관련 문서:

- [CDN 이미지 변환 파이프라인 설계](./cdn-image-transformation-pipeline-design.md)
- [Cache-Control 실전](../network/cache-control-practical.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: cdn basics, cdn 뭐예요, content delivery network 입문, cdn 동작 원리, edge server 개념, cdn 캐시, origin server cdn, cdn hit miss, 정적 파일 cdn, cdn invalidation 기초, 글로벌 배포 입문, beginner cdn, cdn 왜 쓰나요, cdn basics basics, cdn basics beginner

---

## 핵심 개념

CDN(Content Delivery Network)은 "원본 서버의 콘텐츠를 전 세계 여러 Edge 서버에 복사해 두고, 사용자에게 가장 가까운 서버에서 전달하는 네트워크"다.

입문자가 자주 헷갈리는 지점은 **CDN이 캐시인지 서버인지**이다.

CDN Edge 서버는 원본 서버의 응답을 캐시해 두고 재사용한다. 사용자 요청이 Edge에서 처리되면 원본까지 갈 필요가 없다.

CDN이 특히 효과적인 콘텐츠:
- 이미지, CSS, JavaScript, 폰트 같은 정적 파일
- 자주 바뀌지 않는 API 응답
- 동영상 스트리밍

---

## 한눈에 보기

```text
사용자 (서울)
  -> CDN Edge (서울)
       [캐시 HIT]  -> 바로 응답 (빠름)
       [캐시 MISS] -> Origin 서버 (미국) 조회 -> Edge 캐시 저장 -> 응답

사용자 (뉴욕)
  -> CDN Edge (뉴욕)
       [캐시 HIT]  -> 바로 응답 (빠름)
```

CDN 없이 서울 사용자가 미국 원본 서버에 직접 요청하면 왕복 지연(RTT)이 크다. CDN Edge가 서울에 있으면 그 지연이 대폭 줄어든다.

---

## 상세 분해

### CDN 캐시 HIT/MISS

- **Cache HIT**: Edge에 이미 저장된 파일이 있다. 빠르고 Origin 부하가 없다.
- **Cache MISS**: Edge에 없다. Origin에서 가져와 Edge에 저장하고 응답한다.

첫 요청은 항상 MISS이고 이후 같은 파일은 HIT가 된다. TTL이 지나면 다시 MISS로 돌아간다.

### Cache-Control과 TTL

Origin 서버가 응답 헤더에 `Cache-Control: max-age=86400`을 설정하면 Edge는 24시간 동안 원본에 묻지 않고 응답한다.

- TTL을 길게 주면 Edge 적중률이 높아지지만, 파일 변경이 늦게 반영된다.
- TTL을 짧게 주면 최신성이 보장되지만 Origin 부하가 늘어난다.

### Cache Invalidation

CDN 캐시를 강제로 지우는 작업이다. 파일을 바꿨는데 Edge에 예전 버전이 남아 있으면 invalidation으로 제거한다.

빠른 배포를 위해 파일명에 해시를 붙이는 방법(`main.abc123.js`)도 흔히 쓴다. 파일 내용이 바뀌면 URL도 바뀌므로 별도 invalidation 없이 새 파일이 바로 서비스된다.

---

## 흔한 오해와 함정

- **"CDN을 쓰면 Origin 서버가 필요 없다"**: CDN은 Origin의 캐시다. 원본이 없으면 CDN도 채울 수 없다. Origin은 반드시 있어야 한다.
- **"CDN은 정적 파일에만 쓴다"**: API 응답도 캐시할 수 있다. 다만 개인화된 응답(사용자별로 다른 데이터)은 CDN 캐시와 맞지 않는 경우가 많다.
- **"캐시를 지우면 즉시 반영된다"**: Invalidation 전파에 수십 초~수 분이 걸릴 수 있다. 전 세계 Edge에 동시에 반영되지 않는다.

---

## 실무에서 쓰는 모습

가장 흔한 사용 방식은 정적 파일 서빙이다.

1. 배포 시 빌드 결과물(JS, CSS, 이미지)을 S3나 Object Storage에 업로드한다.
2. CloudFront, CloudFlare 같은 CDN이 그 앞에 붙어 Edge에서 서빙한다.
3. 사용자가 `main.abc123.js`를 요청하면 가장 가까운 Edge에서 응답한다.
4. 파일 내용이 바뀌면 해시가 달라져 새 URL로 요청되고 자동으로 새 파일이 캐시된다.

---

## 더 깊이 가려면

- [CDN 이미지 변환 파이프라인 설계](./cdn-image-transformation-pipeline-design.md) — CDN을 활용한 동적 이미지 최적화
- [Cache-Control 실전](../network/cache-control-practical.md) — 브라우저·CDN 캐시 헤더 설정의 실전 포인트

---

## 면접/시니어 질문 미리보기

> Q: CDN Cache MISS가 많이 발생하면 어떤 문제가 생기나요?
> 의도: CDN HIT율과 Origin 부하 관계 이해 확인
> 핵심: MISS마다 Origin 요청이 발생해 Origin에 부하가 집중되고, CDN의 이점이 사라진다.

> Q: 개인화된 API 응답을 CDN에 캐시하면 왜 문제가 되나요?
> 의도: CDN 캐시와 개인화 데이터의 충돌 이해 확인
> 핵심: 사용자 A의 응답이 캐시되어 사용자 B에게 전달될 수 있다. 개인화 데이터는 CDN 캐시를 사용자 식별자 기준으로 분리하거나 CDN을 쓰지 않아야 한다.

> Q: CDN을 쓰는 주된 이유 두 가지를 말해 보세요.
> 의도: CDN 도입 동기를 명확히 설명할 수 있는지 확인
> 핵심: 첫째, 사용자와 가까운 Edge에서 응답해 지연을 줄인다. 둘째, Origin 서버의 트래픽 부하를 줄인다.

---

## 한 줄 정리

CDN은 원본 서버의 콘텐츠를 전 세계 가까운 Edge에 캐시해 사용자 지연을 줄이고, Cache-Control TTL과 Invalidation으로 최신성과 적중률 사이의 균형을 맞춘다.
