# CS Authoring Guide — Beginner/Junior 문서 작성 계약

이 문서는 `knowledge/cs/contents/<category>/` 아래에 새로 추가하는 **🟢 Beginner / 🟡 Intermediate** 난이도 CS 노트의 단일 source-of-truth다. 11개 카테고리 워커가 동시에 글을 추가할 때 톤·구조·retrieval anchor 품질이 갈라지지 않도록 강제한다.

대상 독자:
- woowa-learning-hub의 카테고리별 입문/주니어 문서를 추가하는 AI 워커
- 기존 Advanced 문서를 입문층 진입 문서로 짝지을 때 참고가 필요한 사람

이 가이드는 **Beginner 문서를 추가하는 작업에만** 적용된다. Advanced/Expert 문서는 별도 컨벤션이 누적된 상태이며, 본 사이클의 비목표다.

---

## 0. 왜 컨벤션이 필요한가

- CS RAG 파이프라인은 `corpus_loader.py`가 본문 구조를 파싱해 청크를 만들고, `searcher.py`가 FTS5 + dense + RRF + category boost로 랭킹한다. 본문 H2 블록 하나가 `MAX_CHARS_PER_CHUNK = 1600` 자를 넘으면 hard split이 발생해서 retrieval 단위가 갈라지고, 학습자가 받는 결과가 단편화된다.
- `retrieval-anchor-keywords:` 라인은 `corpus_loader._extract_retrieval_anchors`가 추출해서 모든 청크 본문 끝에 `[retrieval anchors] ...` 접미사로 붙인다. 즉 anchor 품질이 곧 학습자가 자연어로 검색했을 때의 recall 품질이다.
- `**난이도: 🟢 Beginner**` 라벨은 `corpus_loader._extract_difficulty`가 추출해 청크 메타데이터로 저장하고, `searcher._apply_difficulty_boost`가 학습자의 `experience_level`에 맞춰 tie-breaker boost를 준다. 라벨 표기가 다르면 boost가 적용되지 않는다.

규칙을 어기면 글 자체는 살아남지만 **검색 노출이 새고**, 학습자가 같은 카테고리의 Advanced 함정 문서를 먼저 받게 된다.

---

## 1. 필수 7요소 (이 중 하나라도 빠지면 lint 실패)

문서 상단부터 순서대로:

1. **H1 — `# {문서 제목}`** (한국어 또는 한영 혼용, 1줄)
2. **한 줄 요약 블록쿼트 — `> 한 줄 요약: ...`**
3. **난이도 라벨 — `**난이도: 🟢 Beginner**`** (정확히 이 형식, 이모지 포함)
4. **관련 문서 섹션 — `관련 문서:` + 빈 줄 + 불릿 ≥ 3개**
5. **retrieval anchor 라인 — `retrieval-anchor-keywords: ...`** (한 줄, 쉼표 구분, ≥ 8개)
6. **본문 H2 섹션 ≥ 5개** (표준 시퀀스는 §3)
7. **마지막 H2 = `## 한 줄 정리`**

샘플 헤더:

```markdown
# 트랜잭션 기초 (Transaction Basics)

> 한 줄 요약: 트랜잭션은 commit/rollback으로 묶인 작업 단위이고, ACID 4글자가 그 단위의 안전 보장을 다섯 가지 다른 각도에서 설명한다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
- [Isolation Anomaly Cheat Sheet](./isolation-anomaly-cheat-sheet.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: transaction basics, acid intro, commit rollback intro, atomicity for beginners, durability beginner, isolation beginner, transaction unit of work, what is transaction, savepoint basics, beginner db transaction
```

라벨 변형 금지: `**난이도: 🟢 BEGINNER**`, `**난이도:🟢 Beginner**`(공백 빠짐), `**Difficulty: Beginner**`는 모두 lint 실패다.

---

## 2. 필수 체크리스트 (작성 후 본인이 lint 실행 전 자가 확인)

1. 위 7요소가 모두 있는가
2. `retrieval-anchor-keywords:`가 lowercase 8~15개인가 (영문/한영 혼용 OK, 쉼표 구분)
3. anchor 중 증상 키워드(`뭐예요`, `basics`, `intro`, `처음` 등)가 ≥ 2개인가
4. `관련 문서:` 아래 불릿이 ≥ 3개이고 실재하는 경로인가
5. `관련 문서:` 중 cross-category bridge(`../` 링크)가 ≥ 1개인가
6. `## 한눈에 보기`에서 코드 블록이 전체 줄 수의 60%를 넘기지 않는가
7. 각 H2 본문이 ≤ 1600자인가 (한글 1자 = 1자로 셈)

자가 확인 후:

```bash
python3 scripts/lint_cs_authoring.py knowledge/cs/contents/<category>/<file>.md
```

exit 0이면 머지 가능. 실패 메시지를 보고 수정.

---

## 3. 표준 H2 시퀀스

기존 106개 Beginner 문서에서 추출한 공통 패턴이다. 항목 자체는 가변이지만 **순서와 의도를 따른다**:

1. `## 핵심 개념` — 한 단락 정의 + 왜 입문자가 헷갈리는지
2. `## 한눈에 보기` — 표, ascii 다이어그램, 또는 5~7줄 매트릭스. **코드 블록(` ``` `)은 이 섹션에서 전체 줄 수의 60%를 넘기지 않는다.** 실제 코드 예시는 `## 실무에서 쓰는 모습`에 배치. 코드 펜스 밖의 표/텍스트 다이어그램은 상관없다.
3. `## 상세 분해` — 3~5개 sub-bullet 또는 H3 (개념을 부분으로 쪼갬)
4. `## 흔한 오해와 함정` — 입문자가 자주 틀리는 표현 + 더 맞는 첫 대응
5. `## 실무에서 쓰는 모습` — 가장 흔한 1~2개 시나리오 (코드 dump 금지, 시퀀스 설명)
6. `## 더 깊이 가려면` — 같은 카테고리 advanced peer 1~2개 링크 + cross-category 1개
7. `## 면접/시니어 질문 미리보기` — 2~3개 꼬리 질문 (의도 + 핵심 답변)
8. `## 한 줄 정리` — 한 문장. 이 문서를 들고 나가는 사람이 외울 한 줄

5개 이상이면 OK. 8개를 강요하지 않는다 — 짧은 토픽은 §3, §5, §7을 합쳐도 된다. 단 §1, §4, §8은 빠질 수 없다.

---

## 4. retrieval-anchor-keywords 작성 규칙

학습자가 자연어로 검색할 때 이 글이 발견되도록 만드는 키워드 목록이다.

- **lowercase** — `Transaction Basics` 아니라 `transaction basics`
- **8~15개** — 너무 적으면 recall이 새고, 너무 많으면 다른 글의 키워드를 잠식함
- **canonical 표현 + 동의어/약어** — `acid`, `acid 4글자`, `atomicity consistency isolation durability`
- **증상 키워드 ≥ 2개 필수** — 학습자가 실제로 치는 표현. 예: `트랜잭션이 뭐예요`, `commit 언제 써`, `정규화 처음 배우는데`. anchor 목록에 canonical 용어만 있고 증상 문구가 없으면 recall이 새서 학습자의 자연어 질문이 이 문서를 못 찾는다. 한국어 증상(`뭐예요`, `왜`, `처음`, `헷갈`, `기초`, `입문`) 또는 영문 증상(`beginner`, `intro`, `basics`, `what is`, `why`, `how to`) 중 2개 이상 포함해야 lint WARN을 피한다.
- **카테고리 prefix 권장** — `beginner transaction`, `db basics commit`
- **다른 글이 이미 점유한 키워드는 피하기** — 같은 카테고리 안에서 anchor 충돌이 나면 RAG가 두 글을 동시에 내보내며 학습자가 혼란

좋은 예 (10개):
```
transaction basics, acid intro, commit rollback intro, atomicity for beginners, durability beginner, isolation beginner, transaction unit of work, what is transaction, savepoint basics, beginner db transaction
```

나쁜 예:
```
Transaction, ACID, Commit, Rollback   # 4개뿐, 대문자, 너무 일반적
```

---

## 5. 관련 문서 링크 규칙

3개 이상의 불릿. **cross-category bridge ≥ 1개 필수:**

- **같은 카테고리 advanced peer 1~2개** — 학습자가 읽고 나서 다음 단계로 갈 advanced 문서
- **cross-category bridge ≥ 1개 (필수)** — 다른 카테고리의 관련 문서. 예: database 입문 글 → `../spring/spring-transaction-basics.md`, algorithm 입문 글 → `../data-structure/array-basics.md`. `../` 경로가 1개도 없으면 lint WARN이 발생한다. 사이클 1-2 spot-check에서 80%의 문서가 자기 카테고리에만 링크하는 문제가 발견됐다 — 카테고리 간 연결고리가 없으면 학습자가 관련 개념을 놓친다.
- **카테고리 README 1개** — `./README.md`로 navigator 복귀 경로

링크는 **상대 경로**로 작성. 절대 경로나 GitHub URL 금지(repo가 옮겨가면 깨짐).

---

## 6. 본문 작성 톤

- **한국어 산문**. 영문 dump 금지.
- **단락 1개는 짧게**. 입문자에게 한 문단 7줄을 넘기면 읽기 손실이 큼.
- **추상적 결론만 적지 말기**. "트랜잭션은 중요합니다" 같은 문장은 0점이다. 한 줄이라도 예시로 내려와야 함.
- **코드 블록은 최소화**. 전체 SQL/Java dump는 advanced 문서의 영역이다. Beginner 글은 SQL 한두 줄 + 그 줄의 의미 설명.
- **다른 문서 내용을 베끼지 않기**. 입문 글은 같은 토픽을 advanced 글과 다른 각도(정의/혼동 해소)로 다루는 것이지 advanced 글을 압축하는 것이 아니다.

---

## 7. 금지 사항 (자동 또는 수동으로 reject)

- H2 본문 1600자 초과 (자동)
- 7요소 누락 (자동)
- 난이도 라벨 변형 (자동)
- retrieval-anchor-keywords < 8 (자동)
- 관련 문서 < 3 (자동)
- 코드 dump (수동 spot-check) — 한 H2에 코드 블록 50줄 이상이면 advanced 문서로 분리하라는 신호
- 다른 문서 내용 복제 (수동) — 같은 카테고리 다른 글의 본문을 80%+ 동일하게 옮기면 reject

---

## 8. 워커 워크플로우 요약

각 카테고리 워커는 단일 호출 안에서:

1. **갭 분석 (read-only)** — `knowledge/cs/contents/<category>/README.md` + 기존 Beginner 파일 3개 + `JUNIOR-BACKEND-ROADMAP.md`의 해당 stage + 본 가이드
2. **5장 토픽 결정** — 로드맵이 가리키지만 입문 진입 문서가 없는 토픽 5개. 선정 근거를 한 단락으로 기록
3. **작성 + lint** — 5장을 표준 시퀀스로 작성, commit 전에 본인이 `python3 scripts/lint_cs_authoring.py <path>` 실행
4. **README 등록** — 카테고리 README의 "빠른 탐색" 또는 인덱스 섹션에 새 5편 링크 추가

워커는 `knowledge/cs/contents/<자기카테고리>/` 외의 파일을 수정하지 않는다(README 1곳 제외).

---

## 9. 체크리스트 한 장

```
[ ] H1 1줄
[ ] > 한 줄 요약: 블록쿼트
[ ] **난이도: 🟢 Beginner** (정확히)
[ ] 관련 문서: + 불릿 ≥ 3 (cross-category bridge ≥ 1 포함)
[ ] retrieval-anchor-keywords: 8~15 lowercase (증상 키워드 ≥ 2)
[ ] ## 한눈에 보기 코드 블록 < 60%
[ ] H2 ≥ 5개, 각 본문 ≤ 1600자
[ ] ## 한 줄 정리 마지막 H2
[ ] python3 scripts/lint_cs_authoring.py 통과 (FAIL 없음)
[ ] python3 scripts/lint_cs_authoring.py --strict 통과 (WARN 없음)
[ ] 카테고리 README 등록
```

이 체크리스트가 끝나면 머지 가능. 의심스러운 부분은 `knowledge/cs/contents/database/transaction-basics.md`(본 가이드와 함께 머지된 살아있는 reference) 를 보고 비교한다.
