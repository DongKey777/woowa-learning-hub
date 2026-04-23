# Cache-Control 실전

**난이도: 🔴 Advanced**

> 캐시를 "빠르게 만드는 기능"이 아니라 "정확하게 통제해야 하는 계약"으로 보는 정리

> 관련 문서:
> - [CDN 캐시 키와 무효화 전략](./cdn-cache-key-invalidation.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
> - [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
> - [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)

retrieval-anchor-keywords: Cache-Control, max-age, no-store, no-cache, stale-while-revalidate, immutable, shared cache, browser cache, CDN cache, HTTP caching

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [Cache-Control의 역할](#cache-control의-역할)
- [자주 쓰는 지시어](#자주-쓰는-지시어)
- [실전 패턴](#실전-패턴)
- [자주 하는 실수](#자주-하는-실수)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

캐시는 응답 속도를 높이고 서버 부하를 줄인다.

하지만 실무에서는 단순히 "캐시를 켠다"로 끝나지 않는다.

- 누가 캐시하는가
- 어디서 캐시하는가
- 얼마나 오래 캐시하는가
- stale 데이터를 얼마나 허용하는가

를 명확히 정해야 한다.

### Retrieval Anchors

- `Cache-Control`
- `max-age`
- `no-store`
- `no-cache`
- `stale-while-revalidate`
- `immutable`
- `shared cache`
- `HTTP caching`

---

## Cache-Control의 역할

`Cache-Control`은 HTTP 응답이나 요청에서
**캐시 동작 방식을 지정하는 핵심 헤더**다.

브라우저, CDN, 리버스 프록시가 이 값을 보고 캐시 여부와 유효 시간을 결정한다.

대표적으로 다음을 제어한다.

- 캐시 가능 여부
- 저장 위치별 정책
- 최대 보관 시간
- 재검증 여부
- stale 허용 여부

---

## 자주 쓰는 지시어

### `no-store`

- 저장 자체를 하지 않는다
- 민감한 정보나 매번 최신이어야 하는 응답에 쓴다

### `no-cache`

- 저장은 할 수 있지만, 쓰기 전에 서버 검증을 거쳐야 한다
- 이름 때문에 "캐시 금지"로 오해하기 쉽다

### `max-age`

- 응답을 얼마 동안 신선한 상태로 볼지 정한다
- 초 단위로 지정한다

### `public`

- 공유 캐시(CDN, 프록시)가 저장해도 된다

### `private`

- 브라우저 같은 개인 캐시에만 저장하는 편이 안전하다

### `must-revalidate`

- 만료되면 반드시 재검증해야 한다

### `stale-while-revalidate`

- 일단 오래된 응답을 주고, 뒤에서 새 값을 갱신할 수 있다

### `immutable`

- 유효 시간 동안은 바뀌지 않는 리소스에 유용하다

---

## 실전 패턴

### 정적 리소스

JS, CSS, 이미지처럼 파일명이 해시로 바뀌는 정적 리소스는 길게 캐시해도 된다.

예:

```http
Cache-Control: public, max-age=31536000, immutable
```

파일명이 바뀌면 URL도 바뀌므로 오래 캐시해도 안전하다.

### API 응답

API는 데이터 성격에 따라 다르다.

- 자주 바뀌는 목록: 짧은 `max-age`
- 로그인 사용자별 응답: `private` 또는 `no-store`
- 덜 민감한 조회 API: `no-cache` + 재검증

### CDN 앞단

CDN에 태울 응답은 보통 `public`과 함께 설계한다.

- 같은 응답을 여러 사용자가 볼 수 있는가
- 국가/언어/권한별로 응답이 달라지는가

를 먼저 봐야 한다.

---

## 자주 하는 실수

- `no-cache`를 저장 금지로 오해하기
- 사용자별 응답을 `public`으로 두기
- `max-age`만 길게 두고 배포 전략을 생각하지 않기
- 캐시 무효화 없이 API 값을 바꾸기
- 쿼리 문자열만 보고 캐시 여부를 단순 판단하기

캐시는 편하지만, 잘못 쓰면 **오래된 데이터가 정답처럼 보이는 문제**를 만든다.

---

## 면접에서 자주 나오는 질문

### Q. `no-cache`와 `no-store` 차이는 무엇인가요?

- `no-store`는 저장 자체를 금지하고, `no-cache`는 저장은 가능하지만 사용 전에 재검증을 요구한다.

### Q. 정적 파일을 왜 길게 캐시해도 되나요?

- 파일명이 해시 기반으로 바뀌면 URL이 바뀌므로, 새 파일과 옛 파일이 충돌하지 않기 때문이다.

### Q. 개인화 API에 `public` 캐시를 쓰면 왜 위험한가요?

- 다른 사용자가 같은 응답을 받아 정보가 섞일 수 있기 때문이다.

### Q. `Cache-Control`만으로 충분한가요?

- 아니다. `ETag`, `Last-Modified`, CDN 정책, 프록시 설정과 함께 봐야 실제 동작을 정확히 통제할 수 있다.
