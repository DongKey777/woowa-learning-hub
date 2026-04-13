# PR Learning Pipeline

## 목적

이 문서는 미션 PR 학습을 앞으로 하나의 방식으로 운영하기 위한 기준 문서다.

앞으로 PR 학습은 반드시 아래 순서로 진행한다.

1. 수집
2. 분석
3. 해석
4. 학습

핵심은 자동으로 정답을 뽑는 것이 아니라, 내가 읽고 비교하고 설명하기 좋은 재료를 먼저 구조화하는 것이다.

---

## 적용 범위

이 문서는 아래 상황에 공통으로 적용한다.

- 다른 크루 PR를 읽으며 설계 차이를 비교할 때
- 리뷰어 피드백 패턴을 학습할 때
- 특정 주제(예: Repository, Transaction, DAO)를 가로로 비교할 때
- 내 PR과 다른 PR을 함께 놓고 해석할 때

---

## 한 줄 기준

- 수집은 전체를 먼저 본다.
- 분석은 packet을 만든다.
- 해석은 사람이 한다.
- 학습은 반드시 내 코드와 연결한다.

---

## 단계별 운영 기준

### 1. 수집

목적:
- 특정 미션의 PR 전체를 학습 가능한 형태로 로컬 DB에 저장한다.

입력:
- GitHub PR 목록
- PR 본문
- 변경 파일
- patch
- review
- review comment
- issue comment

산출물:
- `catalog/pr-datasets/*.sqlite3`

도구:
- `scripts/pr_archive/collect_prs.py`
- `scripts/pr_archive/schema.sql`
- `scripts/pr_archive/github_client.py`
- `scripts/pr_archive/db.py`

기본 원칙:
- 샘플 PR 몇 개를 먼저 읽지 않는다.
- 전체 미션 PR를 먼저 수집한다.
- patch와 review comment는 반드시 같이 저장한다.
- 이미지, DB 파일, 빌드 산출물 같은 바이너리 자산은 저장하지 않는다.

기본 명령:

```bash
python3 -m scripts.pr_archive.collect_prs \
  --owner woowacourse \
  --repo java-janggi \
  --track java \
  --mission java-janggi \
  --title-contains "사이클2" \
  --mode full \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3
```

세션 시작 전 동기화:

```bash
python3 -m scripts.pr_archive.collect_prs \
  --owner woowacourse \
  --repo java-janggi \
  --track java \
  --mission java-janggi \
  --title-contains "사이클2" \
  --mode incremental \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3
```

완료 기준:
- 분석하려는 미션 PR 전체가 DB에 들어 있다.
- 최근 변경이 있으면 incremental sync까지 끝났다.

---

### 2. 분석

목적:
- 자동 결론을 내기보다, 해석 가능한 자료 묶음(packet)을 만든다.

입력:
- 수집된 PR 데이터셋
- 내가 보고 싶은 주제 또는 비교 대상

산출물:
- topic packet
- reviewer packet
- compare packet

도구:
- `scripts/pr_archive/search_prs.py`
- `scripts/pr_archive/analyze_prs.py`
- `scripts/pr_archive/topic_packet.py`
- `scripts/pr_archive/reviewer_packet.py`
- `scripts/pr_archive/compare_prs.py`

기본 원칙:
- 키워드 검색만 하고 끝내지 않는다.
- packet에는 comment, path, diff hunk가 같이 있어야 한다.
- packet은 결론이 아니라 읽을 재료다.

기본 명령:

```bash
python3 -m scripts.pr_archive.topic_packet \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --topic Repository \
  --query Repository
```

```bash
python3 -m scripts.pr_archive.reviewer_packet \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --reviewer syoun602
```

```bash
python3 -m scripts.pr_archive.compare_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --prs 346 338 277
```

완료 기준:
- 지금 질문에 맞는 packet이 최소 1개 이상 만들어졌다.
- packet에서 코멘트와 코드 문맥을 같이 볼 수 있다.

---

### 3. 해석

목적:
- packet을 읽고 설계적 의미를 사람이 해석한다.

입력:
- packet 출력
- 필요하면 원본 PR 본문
- 필요하면 내 코드와 관련된 현재 구현 문맥

산출물:
- 짧은 해석 메모 또는 학습 노트 초안

기본 질문:
- 리뷰어는 정확히 무엇을 문제라고 본 것인가?
- 그 문제는 책임 경계 문제인가, 네이밍 문제인가, 구조 과잉 문제인가?
- 여러 PR을 비교했을 때 공통 패턴은 무엇인가?
- 예외처럼 보이는 PR은 왜 예외인가?
- 이 포인트가 내 코드에도 그대로 적용되는가?

기본 원칙:
- 해석은 자동화하지 않는다.
- packet 문장만 읽고 결론 내리지 않는다.
- 필요하면 원본 PR과 diff를 다시 연다.
- 해석은 반드시 근거와 같이 적는다.

권장 출력 형식:
- 관찰
- 해석
- 내 코드와의 연결
- 다음 질문

완료 기준:
- “무슨 말을 했는가”가 아니라 “왜 그 말을 했는가”를 설명할 수 있다.
- 내 코드에 적용할지 말지 근거를 말할 수 있다.

---

### 4. 학습

목적:
- 해석 결과를 현재 내 코드, 내 설계, 다음 구현 질문으로 연결한다.

입력:
- 해석 결과
- 내 현재 코드/PR

산출물:
- `knowledge/learning/from-missions/` 하위 노트 또는 `journal/` 하위 미션 문서
- 다음 구현 질문 또는 리팩터링 기준

좋은 결과의 형태:
- “Repository는 상태 저장까지만 알아야 하나, 마지막 이동 명령도 알아야 하나?”
- “트랜잭션 경계는 지금 Application에 두는 게 맞나, Service가 필요한 시점인가?”
- “궁성 규칙은 Piece 책임인가 Palace 책임인가?”

기본 원칙:
- 남의 코드 감상으로 끝내지 않는다.
- 반드시 현재 내 코드와 연결한다.
- 마지막에는 다음 질문 또는 다음 수정 기준이 남아야 한다.

완료 기준:
- 배운 점이 내 코드의 설계 판단 기준으로 바뀌었다.
- 다음에 같은 주제가 나오면 더 빠르게 판단할 수 있다.

---

## 표준 세션 절차

한 번의 PR 학습 세션은 아래 순서를 기본으로 한다.

1. 오늘 볼 주제를 한 문장으로 정한다.
2. 해당 미션 DB가 최신인지 incremental sync로 확인한다.
3. 주제에 맞는 packet을 만든다.
4. packet에서 반복 패턴과 예외 패턴을 읽는다.
5. 필요하면 대표 PR 2~3개를 원문까지 다시 본다.
6. 해석을 문장으로 남긴다.
7. 내 코드/내 PR에 연결한다.
8. 다음 구현 질문이나 학습 질문 1~2개를 남긴다.

주제가 정해지지 않았다면 세션을 시작하지 않는다.

---

## packet 선택 기준

### Topic Packet

언제 쓰나:
- 특정 개념을 넓게 비교할 때

예:
- `Repository`
- `Transaction`
- `Entity`
- `Service`

### Reviewer Packet

언제 쓰나:
- 특정 리뷰어가 반복해서 보는 포인트를 학습할 때

예:
- `syoun602`
- `donghoony`

### Compare Packet

언제 쓰나:
- 내 PR과 다른 PR 2~3개를 직접 비교할 때
- 구조 차이가 큰 구현들을 나란히 볼 때

예:
- `346 vs 338 vs 277`

---

## 산출물 저장 기준

- 원본 수집 DB: `catalog/pr-datasets/`
- 세션 중간 메모: `journal/<track>/<repo>/reviews/`
- 재사용할 학습 노트: `knowledge/learning/from-missions/<track>/<repo>/`
- 운영 기준 문서: `playbooks/`

임시 터미널 출력만 보고 끝내지 않는다.

---

## 표준 해석 템플릿

packet을 읽은 뒤 기록은 `playbooks/pr-learning-note-template.md` 형식을 기본으로 사용한다.

최소한 아래 네 줄은 남긴다.

- 무엇을 봤는가
- 무엇이 반복됐는가
- 내 코드와 어떻게 연결되는가
- 다음 질문이 무엇인가

---

## 금지 사항

- 전체 수집 없이 샘플 몇 개만 보고 결론 내리기
- 검색 결과 몇 줄만 보고 구조를 단정하기
- packet 출력만 보고 바로 정답 구조라고 말하기
- 내 코드와 연결하지 않고 남의 코드만 구경하기
- 학습 포인트 없이 단순 PR 요약만 남기기

---

## 성공 기준

이 파이프라인이 잘 작동한다고 볼 수 있는 기준은 아래와 같다.

- 주제를 정하면 필요한 packet을 바로 만들 수 있다.
- packet에서 코멘트와 코드 문맥을 함께 읽을 수 있다.
- 해석 결과를 내 코드와 연결해 설명할 수 있다.
- 다음 설계 질문이나 구현 질문으로 자연스럽게 이어진다.

---

## 현재 운영 규칙

앞으로 PR 학습은 `수집 -> 분석 -> 해석 -> 학습` 순서로 통일한다.

그리고 분석의 목적은 자동 결론이 아니라, 내가 더 잘 읽고 비교하고 해석할 수 있도록 자료를 구조화하는 것이다.
