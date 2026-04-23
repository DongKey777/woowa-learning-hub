# 정규화와 반정규화 트레이드오프

> 한 줄 요약: 정규화는 무결성을 지키고, 반정규화는 읽기를 빠르게 한다. 둘은 정답이 아니라 비용 선택이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Schema Migration, Partitioning, CDC, CQRS](./schema-migration-partitioning-cdc-cqrs.md)
> - [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
> - [B+Tree vs LSM-Tree](./bptree-vs-lsm-tree.md)
> - [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
> - [Incremental Summary Table Refresh and Watermark Discipline](./incremental-summary-table-refresh-watermark.md)
> - [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)

retrieval-anchor-keywords: normalization, denormalization, summary table, read model, data duplication, incremental refresh, source of truth, backend tradeoff

---

## 핵심 개념

정규화는 데이터 중복을 줄여서 이상(anomaly)을 막는 설계다. 반정규화는 읽기 성능이나 조회 단순화를 위해 의도적으로 중복을 허용하는 설계다.

이 둘은 대립이 아니라 선택이다.

- 정규화는 쓰기 정합성을 지킨다
- 반정규화는 읽기 성능과 조회 단순성을 얻는다

문제는 “항상 정규화”도, “조회 편하라고 다 펼치기”도 정답이 아니라는 점이다.

---

## 깊이 들어가기

### 1. 정규화가 해결하는 문제

정규화는 다음 문제를 줄인다.

- 삽입 이상
- 갱신 이상
- 삭제 이상

예를 들어 `orders`에 고객 정보까지 넣으면 고객 이름이 여러 주문에 반복된다. 고객 이름이 바뀔 때 모든 row를 수정해야 한다.

### 2. 반정규화가 필요한 이유

조회가 많은 서비스에서는 정규화된 조인이 너무 비싸질 수 있다.

예:

- 주문 목록에서 고객명, 배송상태, 최근 결제 상태를 항상 보여줘야 함
- 매번 여러 테이블 join을 하면 p99가 흔들림
- admin dashboard 같은 조회성 화면은 write보다 read가 훨씬 많음

이때는 read model이나 summary table을 두는 편이 낫다.

### 3. 핵심 기준은 읽기/쓰기 비율이다

정규화와 반정규화를 결정할 때 보통 다음을 본다.

- 조회가 얼마나 잦은가
- 데이터 변경 빈도가 얼마나 높은가
- 정합성이 즉시 필요한가
- 조인 비용이 병목인가
- 중복 동기화를 감당할 수 있는가

### 4. 반정규화는 결국 동기화 비용을 만든다

반정규화는 무료가 아니다.

- write amplification이 생긴다
- 중복 데이터 동기화가 필요하다
- 소스 오브 트루스가 어디인지 명확해야 한다

이걸 모르면, 조회는 빨라졌는데 운영은 더 어려워진다.

특히 summary table을 오래 운영하려면 refresh watermark, replay, late correction 전략이 같이 필요하다.

---

## 실전 시나리오

### 시나리오 1: 주문 목록이 너무 느림

정규화된 구조:

```sql
SELECT o.id, o.status, c.name, p.method
FROM orders o
JOIN customers c ON c.id = o.customer_id
LEFT JOIN payments p ON p.order_id = o.id
WHERE o.user_id = ?
ORDER BY o.created_at DESC
LIMIT 20;
```

데이터가 커지면 join 비용과 인덱스 조합 때문에 목록 조회가 느려질 수 있다.

해결책:

- 주문 summary table을 만든다
- 필요한 필드를 미리 집계한다
- 변경은 이벤트나 배치로 반영한다

### 시나리오 2: 고객 이름 변경이 여러 화면에 퍼짐

반정규화를 과하게 하면 고객 이름이 여러 테이블에 복제된다. 이때 이름 변경 이벤트가 누락되면 화면마다 다른 이름이 보일 수 있다.

교훈:

- 반정규화는 읽기 최적화와 일관성 관리 비용을 동시에 가져온다
- 쓰기 경로를 단순화할 수 없다면 중복은 위험하다

### 시나리오 3: 운영 중 조인 폭발

`order_items`, `payments`, `shipments`, `coupons`를 매번 조인하는 admin report가 있다고 하자.  
이런 보고용 조회는 write model을 그대로 쓰기보다, 별도 조회 테이블로 분리하는 것이 현실적이다.

---

## 코드로 보기

### 정규화된 모델

```sql
CREATE TABLE customers (
  id BIGINT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(200) NOT NULL UNIQUE
);

CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  INDEX idx_orders_customer_created (customer_id, created_at)
);
```

### 반정규화된 조회 테이블

```sql
CREATE TABLE order_summary (
  order_id BIGINT PRIMARY KEY,
  customer_id BIGINT NOT NULL,
  customer_name VARCHAR(100) NOT NULL,
  order_status VARCHAR(20) NOT NULL,
  last_payment_method VARCHAR(20) NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  INDEX idx_order_summary_customer_created (customer_id, created_at)
);
```

이 테이블은 조회가 빠르지만, 원본 데이터가 바뀌면 다시 써야 한다.

### 동기화 예시

```java
public void onOrderPaid(OrderPaidEvent event) {
    orderSummaryRepository.updatePaymentMethod(
        event.orderId(),
        event.paymentMethod()
    );
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 정규화 | 정합성이 좋다 | 조인이 늘어난다 | write-heavy, 정합성 우선 |
| 반정규화 | 조회가 빠르다 | 중복/동기화 비용이 생긴다 | read-heavy, 조회 SLA 우선 |
| summary table | 목록/리포트가 단순해진다 | 소스 오브 트루스 관리 필요 | 반복 조회가 많은 화면 |
| CQRS read model | 쓰기와 읽기를 분리한다 | 시스템 복잡도가 올라간다 | 조회 패턴이 복잡할 때 |

핵심 기준은 “정답”이 아니라 **어떤 실패를 감당할 것인가**다.

---

## 꼬리질문

> Q: 정규화를 강하게 할수록 무조건 좋은가요?
> 의도: 정합성과 성능의 균형 이해 여부 확인
> 핵심: 무결성은 좋아지지만 조인 비용과 운영 복잡도가 늘 수 있다

> Q: 반정규화를 하면 어디서 위험해지나요?
> 의도: 중복 동기화 비용 인식 확인
> 핵심: 쓰기 경로와 이벤트 누락, 소스 오브 트루스 불명확성이 위험하다

> Q: read model과 반정규화는 같은 건가요?
> 의도: 용어 구분 능력 확인
> 핵심: 겹치지만 같지는 않다. read model은 조회 전용 모델링까지 포함한다

---

## 한 줄 정리

정규화는 무결성, 반정규화는 조회 성능을 얻는 선택이다. 중요한 건 어떤 데이터를 어떤 비용으로 중복할지 명확히 아는 것이다.
