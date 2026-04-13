# PR Archive Scripts

## 목적

이 디렉터리는 GitHub PR 데이터를 학습용 SQLite 데이터베이스로 수집하는 스크립트를 둔다.

이 디렉터리가 담당하는 범위는 `수집`과 `분석`까지다.
그 이후 `해석`과 `학습` 운영 기준은 `playbooks/pr-learning-pipeline.md`를 따른다.

현재 구성:
- `schema.sql`: PR archive DB 초기화 스키마
- `github_client.py`: `gh api` 래퍼
- `db.py`: SQLite upsert / history 저장 헬퍼
- `collect_prs.py`: full / incremental 수집 엔트리
- `search_prs.py`: 저장된 PR 데이터 검색 도구
- `analyze_prs.py`: 저장된 PR 데이터 요약/분석 도구
- `topic_packet.py`: 주제별 학습 자료 묶음 생성 도구
- `reviewer_packet.py`: 리뷰어 관점 학습 자료 묶음 생성 도구
- `compare_prs.py`: 여러 PR 구조를 비교하는 비교 패킷 생성 도구

## 기본 실행 예시

```bash
python3 -m scripts.pr_archive.collect_prs \
  --owner woowacourse \
  --repo java-janggi \
  --track java \
  --mission java-janggi \
  --title-contains "사이클2" \
  --mode full
```

incremental 예시:

```bash
python3 -m scripts.pr_archive.collect_prs \
  --owner woowacourse \
  --repo java-janggi \
  --title-contains "사이클2" \
  --mode incremental \
  --since 2026-04-01T00:00:00+00:00
```

## 주의

- 실행 전 `gh api user`가 성공하는지 확인한다.
- 검색 API보다 `gh api repos/...` endpoint를 우선 사용한다.
- 이미지, DB 파일, 빌드 산출물은 저장 대상이 아니다.
- packet 출력은 최종 결론이 아니라 해석용 재료다.

## 권장 사용 순서

1. `collect_prs.py`로 전체 미션 PR를 수집한다.
2. 필요하면 incremental sync로 최신 상태를 맞춘다.
3. `topic_packet.py`, `reviewer_packet.py`, `compare_prs.py`로 자료 묶음을 만든다.
4. 결과는 `playbooks/pr-learning-pipeline.md` 기준으로 해석하고 학습 노트로 연결한다.

## 검색 예시

리뷰 코멘트 검색:

```bash
python3 -m scripts.pr_archive.search_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --scope comments \
  --query 'Repository'
```

patch 검색:

```bash
python3 -m scripts.pr_archive.search_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --scope patches \
  --query 'commit'
```

## 분석 예시

리뷰어별 리뷰 요약:

```bash
python3 -m scripts.pr_archive.analyze_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  reviewer-summary
```

리뷰 코멘트가 많이 달린 파일:

```bash
python3 -m scripts.pr_archive.analyze_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  path-hotspots
```

키워드 리포트:

```bash
python3 -m scripts.pr_archive.analyze_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  keyword-report --query Repository
```

특정 PR 상세 리포트:

```bash
python3 -m scripts.pr_archive.analyze_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  pr-report --number 270
```

주제 패킷 생성:

```bash
python3 -m scripts.pr_archive.topic_packet \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --topic "Repository" \
  --query Repository
```

리뷰어 패킷 생성:

```bash
python3 -m scripts.pr_archive.reviewer_packet \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --reviewer donghoony
```

PR 비교 패킷 생성:

```bash
python3 -m scripts.pr_archive.compare_prs \
  --db-path catalog/pr-datasets/github-prs-cycle2.sqlite3 \
  --prs 270 346
```
