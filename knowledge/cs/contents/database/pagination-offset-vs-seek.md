# Pagination: Offset vs Seek

> 한 줄 요약: 페이지네이션은 UI 문제처럼 보이지만, 대용량 DB에서는 정렬과 인덱스 접근 비용을 바꾸는 쿼리 설계 문제다.

**난이도: 🟡 Intermediate**

> 관련 문서: [인덱스와 실행 계획](./index-and-explain.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md), [SQL 조인과 쿼리 실행 순서](./sql-joins-and-query-order.md)

> retrieval-anchor-keywords:
> - pagination
> - offset pagination
> - seek pagination
> - keyset pagination
> - cursor pagination
> - LIMIT OFFSET
> - deep pagination
> - 스크롤 페이지네이션

## 핵심 개념

`offset pagination`은 `LIMIT x OFFSET y` 방식이다.  
`seek pagination`은 마지막으로 본 키를 기준으로 다음 페이지를 찾는 방식이다.

왜 중요한가:

- offset은 뒤로 갈수록 느려질 수 있다
- seek는 성능이 좋지만 "임의 페이지 점프"가 어렵다
- 정렬 키와 인덱스 설계가 함께 맞아야 한다

## 깊이 들어가기

### 1. offset이 느려지는 이유

DB는 offset 만큼 결과를 건너뛰어야 하므로, 뒤 페이지로 갈수록 버려지는 row가 늘어난다.

### 2. seek 방식

예:

```sql
SELECT *
FROM posts
WHERE (created_at, id) < (?, ?)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

seek는 인덱스를 타고 다음 지점을 바로 찾는다.

### 3. 실전 선택 기준

- 끝없는 스크롤, 피드, 로그 조회: seek
- 관리 페이지의 특정 페이지 점프: offset

## 실전 시나리오

### 시나리오 1: 페이지 1은 빠른데 10000페이지는 느리다

offset pagination의 전형적인 증상이다.

### 시나리오 2: "다음 페이지"만 필요하다

seek가 훨씬 적합하다.  
cursor token을 전달하면 된다.

## 코드로 보기

```sql
-- offset
SELECT * FROM articles ORDER BY id DESC LIMIT 20 OFFSET 100000;

-- seek
SELECT * FROM articles WHERE id < 100000 ORDER BY id DESC LIMIT 20;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Offset | 구현 단순 | 뒤 페이지 느림 | 관리 UI |
| Seek | 성능 좋음 | 임의 점프 어려움 | 피드/로그 |

## 꼬리질문

> Q: offset pagination이 왜 느려지는가?
> 의도: DB가 row를 버리는 비용 이해 여부 확인
> 핵심: 뒤로 갈수록 무시해야 할 row가 늘어난다.

> Q: seek pagination을 쓰면 무엇이 불편해지는가?
> 의도: UX와 성능 trade-off 이해 여부 확인
> 핵심: 페이지 번호 기반 점프가 어려워진다.

## 한 줄 정리

offset은 편하지만 뒤로 갈수록 비싸고, seek는 빠르지만 cursor 설계를 같이 해야 한다.
