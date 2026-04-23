# 캐시 기초 (Caching Basics)

> 한 줄 요약: 캐시는 자주 조회되는 데이터를 빠른 저장소에 미리 올려두어 반복 연산이나 DB 조회를 줄이는 성능 최적화 기법이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [데이터베이스 인덱스 기초](../database/index-basics.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: caching basics, 캐시 입문, cache 뭐예요, cache hit miss 기초, redis 기초, ttl 캐시, 캐시 무효화 입문, read through cache aside, 캐시 레이어 기초, beginner caching, 데이터베이스 캐시, 캐시 전략 입문, 성능 최적화 캐시

---

## 핵심 개념

캐시는 "자주 쓰는 데이터를 가까운 곳에 복사해두는 것"이다.
입문자가 자주 헷갈리는 지점은 **캐시가 왜 필요하고, 언제 문제가 생기는가**이다.

DB 조회에는 디스크 I/O, 네트워크 왕복, 쿼리 파싱 비용이 든다. 같은 데이터를 수백 번 요청해도 매번 DB를 거치면 응답이 느리고 DB에 부담이 간다.

캐시를 두면:

- 첫 조회는 DB에서 가져와 캐시에 저장한다 (Cache Miss).
- 이후 조회는 캐시에서 바로 반환한다 (Cache Hit).
- DB 부하가 줄고 응답이 빨라진다.

---

## 한눈에 보기

```text
요청 -> 캐시 확인
          |-- 데이터 있음 (Hit) --> 바로 반환
          |-- 데이터 없음 (Miss) -> DB 조회 -> 캐시 저장 -> 반환
```

핵심 용어:

| 용어 | 의미 |
|---|---|
| Cache Hit | 캐시에 데이터가 있어 DB를 거치지 않음 |
| Cache Miss | 캐시에 없어 DB 조회 후 저장 |
| TTL (Time To Live) | 캐시 항목이 만료되는 시간 |
| Eviction | TTL 만료 또는 메모리 부족 시 항목 제거 |

---

## 상세 분해

- **Cache-Aside 패턴**: 애플리케이션이 직접 캐시를 확인하고, Miss이면 DB에서 가져와 캐시에 저장한다. 가장 흔하게 쓰이는 패턴이다.
- **Write-Through 패턴**: 데이터를 쓸 때 캐시와 DB에 동시에 저장한다. 캐시와 DB가 항상 동기화되지만, 쓰기 지연이 생긴다.
- **TTL 설정**: 캐시 데이터가 너무 오래 살아있으면 DB 원본과 불일치가 발생한다. TTL을 짧게 두면 Cache Miss가 잦아지고, 길게 두면 오래된 데이터가 서비스된다.
- **캐시 레이어 위치**: 로컬 인메모리(JVM Heap), 원격 캐시(Redis, Memcached), CDN 캐시(정적 리소스) 등 여러 레이어에 쓰인다.

---

## 흔한 오해와 함정

- **"캐시를 쓰면 항상 최신 데이터가 나온다"**: 캐시는 복사본이라 원본이 바뀌어도 TTL이 지나기 전까지 오래된 값이 반환될 수 있다. 이를 Stale Read라고 한다.
- **"캐시가 크면 클수록 좋다"**: 캐시 메모리는 비용이 크다. 자주 쓰이는 데이터만 캐시하고, 잘 쓰이지 않는 데이터를 올리면 Hit Rate이 낮아져 의미가 없다.
- **"캐시는 일관성 없어도 된다"**: 결제 잔액, 재고 수량처럼 정확성이 중요한 데이터는 캐시 없이 항상 DB에서 읽거나 캐시 무효화를 즉시 해줘야 한다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 상품 상세 페이지 조회다.

1. 사용자가 상품 페이지를 요청한다.
2. Redis에서 `product:{id}` 키를 조회한다.
3. Hit이면 Redis 값을 반환한다 (DB 조회 없음).
4. Miss이면 DB에서 조회하고 Redis에 TTL 10분으로 저장한다.
5. 상품 정보가 변경되면 Redis 캐시 키를 삭제(invalidate)해 다음 요청에서 DB를 새로 읽는다.

Spring에서는 `@Cacheable`과 `@CacheEvict` 어노테이션으로 캐시 전략을 선언적으로 적용할 수 있다.

---

## 더 깊이 가려면

- [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md) — 캐시 무효화 전략, Stale Read, 동시 갱신 경쟁 조건
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md) — 캐시와 DB Read Replica의 차이와 선택 기준

---

## 면접/시니어 질문 미리보기

> Q: Cache Hit Rate이 낮으면 어떤 문제가 생기나요?
> 의도: 캐시 효과와 DB 부하의 관계 이해 확인
> 핵심: Miss가 많으면 DB 조회가 늘어나 캐시를 안 쓰는 것과 비슷해지고, 캐시 조회 비용만 추가된다. 키 설계와 TTL을 재검토해야 한다.

> Q: Cache-Aside와 Write-Through의 차이는 무엇인가요?
> 의도: 캐시 쓰기 전략 구분 능력 확인
> 핵심: Cache-Aside는 읽기 시 캐시를 채우고 쓰기는 DB만 업데이트한다. Write-Through는 쓰기 시 캐시와 DB를 동시에 업데이트한다.

> Q: 결제 잔액 조회에 캐시를 쓰면 안 되는 이유는 무엇인가요?
> 의도: 캐시 일관성 한계 인식 확인
> 핵심: 캐시는 복사본이라 즉시 갱신되지 않는다. 잔액이 변해도 TTL 안에는 이전 값이 반환될 수 있어 과다 인출 등 심각한 데이터 불일치가 발생한다.

---

## 한 줄 정리

캐시는 자주 조회되는 데이터를 빠른 저장소에 복사해두어 DB 부하를 줄이지만, Stale Read와 캐시 무효화를 항상 함께 고려해야 한다.
