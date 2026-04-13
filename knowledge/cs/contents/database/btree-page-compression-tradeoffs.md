# B-Tree Page Compression Trade-offs

> 한 줄 요약: page compression은 저장 공간과 I/O를 줄일 수 있지만, 압축과 재압축 비용이 B-Tree의 split/merge path에 추가 세금을 붙인다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: page compression, row_format compressed, key_block_size, compression level, compression failure threshold, B-Tree compression, compressed pages, write amplification

## 핵심 개념

- 관련 문서:
  - [Page Split, Merge, and Fill Factor](./page-split-merge-fill-factor.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Redo Log Write Amplification](./redo-log-write-amplification.md)
  - [Clustered Index Locality](./clustered-index-locality.md)

B-Tree page compression은 데이터를 더 작은 페이지로 압축해 저장하는 방식이다.  
MySQL InnoDB에서는 `ROW_FORMAT=COMPRESSED`와 `KEY_BLOCK_SIZE` 같은 설정이 관련된다.

핵심은 다음이다.

- 디스크 공간과 I/O를 줄일 수 있다
- 대신 CPU와 페이지 재구성 비용이 늘어난다
- split/merge와 함께 쓰기 증폭이 커질 수 있다

## 깊이 들어가기

### 1. 왜 압축이 도움이 되나

압축은 디스크에 저장되는 데이터량을 줄일 수 있다.  
특히 읽기 중심이거나 오래 보관하는 테이블에서는 저장 공간 절감 효과가 크다.

장점:

- 스토리지 비용 절감
- I/O량 감소 가능성
- 더 많은 페이지를 같은 공간에 넣을 수 있음

### 2. 왜 CPU 비용이 늘어나나

압축은 읽을 때 해제하고, 쓸 때 다시 압축해야 한다.  
즉 데이터를 저장하는 순간마다 추가 계산이 들어간다.

- read path에서 decompress
- write path에서 recompress
- split/merge 시 재압축

### 3. split/merge와 압축은 궁합이 까다롭다

page split이 일어날 때 두 페이지를 다시 압축해야 할 수 있다.  
page merge도 마찬가지다.

그래서 압축 테이블은:

- 쓰기 경합이 높을수록 부담이 커지고
- 랜덤 insert가 많을수록 재압축 비용이 두드러질 수 있다

### 4. 어떤 워크로드에 맞나

- 보관 비중이 큰 데이터
- 읽기 비중이 높고 쓰기 비중이 낮은 테이블
- 디스크 비용 절감이 중요한 경우

반대로:

- write-heavy OLTP
- page split이 잦은 테이블
- latency p99가 매우 민감한 경로

에서는 조심해야 한다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `page compression`
- `row_format compressed`
- `key_block_size`
- `compression level`
- `compression failure threshold`
- `B-Tree compression`

## 실전 시나리오

### 시나리오 1. 오래된 로그 테이블을 압축해서 저장 비용을 줄이고 싶다

읽기보다 보관이 더 중요하고, 쓰기가 많지 않다면 압축이 이득일 수 있다.  
압축 비율과 응답 시간을 같이 봐야 한다.

### 시나리오 2. 압축을 켰더니 CPU가 올라갔다

압축은 저장 공간 대신 CPU를 쓰는 선택이다.  
특히 page split/merge가 많으면 재압축 비용이 눈에 띌 수 있다.

### 시나리오 3. 랜덤 insert 테이블에는 별로였다

page compression이 모든 OLTP 테이블에 맞는 것은 아니다.  
쓰기 패턴이 거칠면 압축과 재압축이 병목이 된다.

## 코드로 보기

### 압축 테이블 예시

```sql
CREATE TABLE logs (
  id BIGINT PRIMARY KEY,
  created_at DATETIME NOT NULL,
  level VARCHAR(20) NOT NULL,
  message TEXT NOT NULL
) ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;
```

### 관련 변수 확인

```sql
SHOW VARIABLES LIKE 'innodb_compression_level';
SHOW VARIABLES LIKE 'innodb_compression_pad_pct_max';
SHOW VARIABLES LIKE 'innodb_compression_failure_threshold_pct';
```

### 상태 점검

```sql
SHOW ENGINE INNODB STATUS\G
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| page compression | 저장 공간과 I/O를 줄일 수 있다 | CPU와 재압축 비용이 있다 | 보관/읽기 중심 |
| 비압축 page | CPU 부담이 적다 | 저장 공간과 I/O가 더 든다 | write-heavy OLTP |
| 더 작은 KEY_BLOCK_SIZE | 압축 효율을 높일 수 있다 | 압축/재압축 비용이 커질 수 있다 | 공간 절감이 중요할 때 |

핵심은 압축을 "무조건 좋은 최적화"로 보지 말고, **B-Tree의 split/merge path에 추가되는 비용**으로 보는 것이다.

## 꼬리질문

> Q: page compression은 왜 CPU를 더 쓰나요?
> 의도: 압축/해제의 기본 비용을 이해하는지 확인
> 핵심: 읽고 쓸 때마다 재압축 단계가 있기 때문이다

> Q: 압축 테이블이 write-heavy에 불리한 이유는 무엇인가요?
> 의도: split/merge와 재압축 비용을 아는지 확인
> 핵심: page 재구성이 잦을수록 비용이 커진다

> Q: 언제 압축을 고려하나요?
> 의도: 워크로드 적합성을 보는지 확인
> 핵심: 보관 중심, 읽기 중심, 저장 비용 절감이 중요할 때다

## 한 줄 정리

B-Tree page compression은 공간과 I/O를 줄이지만, 그만큼 CPU와 split/merge 재압축 비용을 받아들여야 하는 trade-off다.
