# woowa-learning-hub

우아한테크코스 미션을 풀면서 옆에서 코칭해주는 한국어 AI 워크벤치입니다.
PR 리뷰 같이 봐주고, 막히는 CS 개념을 자료에서 찾아서 설명해주고, 학습 테스트
채점도 같이 하는, 그런 도구예요.

학습자는 한국어로 의도만 던지면 되고, 명령어는 AI가 알아서 칩니다.

## 빨리 시작

```bash
git clone https://github.com/DongKey777/woowa-learning-hub.git
cd woowa-learning-hub
```

이 폴더에서 AI CLI를 엽니다. 매번 y/n 안 묻게 자동 승인 모드로 시작하면 편해요.

| AI | 명령 |
|---|---|
| Claude Code | `claude --dangerously-skip-permissions` |
| Codex (OpenAI) | `codex --full-auto` |
| Gemini CLI | `gemini --yolo` |

> 자동 승인은 신뢰하는 저장소에서만 쓰세요. 이 워크벤치는 자기 폴더 안에서만
> 동작하지만, 의심되면 옵션 빼고 시작해도 됩니다.

그리고 한국어로 한 줄.

> *"이 저장소로 학습 시작하자. spring-core-1부터."*

처음에는 의존성 설치, 모델 캐시, RAG 인덱스 다운로드까지 5~10분 정도 걸립니다.
그 뒤로는 질문 한 번에 1~2초.

## 뭘 해주나요

**peer PR 코칭.** 자기 미션 저장소를 알려주면 upstream `woowacourse/<repo>`에
다른 크루들이 올린 PR이랑 멘토 리뷰를 모아둡니다. *"다른 사람들은 Repository
경계를 어떻게 잡았어?"* 같은 질문에 같은 단계 PR 기준으로 답해줍니다.

**CS 개념 질문.** *"Bean이 뭐야?"* 같은 질문이 들어오면 `knowledge/cs/` 안에서
관련 문서를 찾아서 한국어로 설명합니다. 정의/비교/깊이에 따라 답이 자동으로
얕아지거나 깊어져요. 코퍼스에 없는 주제는 일반 지식으로 답하되 그 사실을
명시합니다.

**학습 테스트.** `spring-learning-test` 모듈을 자동으로 클론하고, 코드 짜고
*"테스트 통과했어"* 하면 JUnit XML을 파싱해 모듈별 통과율로 누적합니다.

**Drill 채점.** *"DI drill 풀어볼래"* 하면 4문장 답변 요구 질문이 나오고,
정확도/깊이/실전성/완결성 4축으로 채점합니다. 8점 ×2 + 테스트 통과면 mastered.

**기억합니다.** 같은 개념을 7일 안에 ≥3번 물어보면 다음 답이 자동으로
깊어지고, mastered된 개념은 기본 정의를 생략합니다. 다른 미션에서 본 패턴까지
같이 봐요.

## 학습자 노트북 배치

```
woowa-learning-hub/                  ← 직접 클론한 한 곳
├─ bin/, scripts/, knowledge/        ← 도구 + CS 자료
├─ state/                            ← 런타임 상태 (gitignore, 노트북 안에만)
└─ missions/                         ← AI가 자동 클론
   ├─ spring-learning-test/
   └─ <자기 미션 fork>/              ← upstream은 woowacourse/<repo>
```

이미 다른 폴더에 미션 저장소를 클론해뒀으면 위치만 알려주면 됩니다 —
*"내 미션 저장소는 `~/code/java-janggi`에 있어."*

## 미리 깔아두면 좋은 것

- Python 3.10 이상, `git`, `gh` CLI (`gh auth login` 한 번)
- AI CLI 한 종류 (Claude Code / Codex / Gemini 중 아무거나)

운영체제는 macOS, Linux, WSL2, Windows native 다 됩니다. AI가 OS 감지해서
`bin/*` (Unix)나 `.\bin\*.ps1` (Windows native)을 골라 씁니다. 의존성 설치,
모델 캐시, gh 인증까지 첫 세션에 알아서 해요.

## 명령어

학습자가 직접 칠 일은 거의 없습니다. AI가 호출하니까요. 환경이 깨졌을 때만:

```bash
bin/doctor                          # 환경 점검
bin/cs-index-build                  # 인덱스 다시 받기
bin/learner-profile clear --yes     # 학습 데이터 초기화
```

## AI 시작 파일

저장소 루트에서 AI를 띄우면 자기에게 맞는 시작 파일을 자동으로 읽습니다.

| AI | 시작 파일 |
|---|---|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) |
| Codex | [`AGENTS.md`](AGENTS.md) |
| Gemini | [`GEMINI.md`](GEMINI.md) |

권장 모델이랑 첫 응답에서 모델 확인하는 규약은 각 파일 안에 적혀 있어요.

## 더 읽기

- [`docs/onboarding.md`](docs/onboarding.md) — 학습 흐름 7단계
- [`docs/rag-runtime.md`](docs/rag-runtime.md) — Tier 분류 + RAG 런타임
- [`docs/agent-operating-contract.md`](docs/agent-operating-contract.md) — Response Contract, First-Run Protocol
- [`docs/architecture.md`](docs/architecture.md) — 파이프라인 구조

## 라이선스

[MIT](LICENSE). 우테코 학습 도구라 자유 사용/포크/변경/재배포 OK.

피드백/버그는 이슈로 부탁드려요. 아직 다듬을 부분이 많습니다.
