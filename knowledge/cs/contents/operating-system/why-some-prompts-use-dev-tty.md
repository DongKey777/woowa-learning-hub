# Why Some Prompts Use `/dev/tty`

> 한 줄 요약: 어떤 CLI는 비밀번호나 `y/n` 확인을 `stdin`이 아니라 `/dev/tty`에서 직접 읽는다. 그래서 pipe로 값을 넣어도 prompt가 그 값을 무시하고, "실제 터미널에서 사람이 직접 답하라"는 식으로 계속 기다릴 수 있다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md) 다음에 읽는 beginner bridge다. "`echo secret | some-cli`를 했는데 왜 계속 prompt가 뜨지?"를 `stdin`과 `/dev/tty`를 분리해서 설명하고, 안전한 non-interactive 대안을 같이 정리한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
- [PTY Raw Mode and Echo Basics](./pty-raw-mode-echo-basics.md)
- [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
- [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
- [Shell Wrapper Boundary Primer](./shell-wrapper-boundary-primer.md)
- [TTY-Aware Output Capture Patterns](./tty-aware-output-capture-patterns.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: operating-system-00072, why some prompts use dev tty, /dev/tty prompt, dev tty prompt, prompt ignores piped stdin, password prompt ignores stdin, confirmation prompt ignores stdin, why echo pipe does not answer prompt, stdin vs /dev/tty, controlling terminal basics, terminal prompt bypass stdin, password stdin alternative, confirmation non interactive option, yes flag vs tty prompt, askpass basics

## 먼저 잡는 멘탈 모델

먼저 이 둘을 같은 것으로 생각하지 않는 게 핵심이다.

```text
stdin (fd 0)
  -> 지금 프로그램이 기본 입력으로 읽는 통로

/dev/tty
  -> 이 프로세스가 붙어 있는 "실제 터미널" 장치
```

그래서 아래 두 문장은 다를 수 있다.

- "`stdin`으로는 pipe가 들어온다"
- "하지만 이 프로세스는 여전히 터미널을 하나 갖고 있다"

핵심 문장은 이것이다.

> 어떤 프로그램은 "일반 입력 데이터"는 `stdin`에서 읽고, "사람이 직접 답해야 하는 질문"은 `/dev/tty`에서 따로 읽는다.

이 경우 pipe는 batch input으로 소비되고, password prompt나 confirmation prompt는 터미널에서 별도로 기다린다.

## 왜 굳이 `/dev/tty`를 따로 열까

도구 입장에서는 비밀번호나 파괴적 확인 질문을 일반 `stdin`과 섞고 싶지 않을 때가 있다.

| 도구가 걱정하는 것 | `/dev/tty`를 쓰는 이유 |
|---|---|
| 파이프 데이터가 우연히 확인 질문까지 먹어 버림 | "정말 사람 의사인지"를 터미널에서 다시 확인하려고 |
| 비밀번호가 batch input과 섞임 | 비밀 입력을 일반 데이터 통로와 분리하려고 |
| shell pipeline/redirect 환경에서 interactive 여부가 불명확 | 터미널이 있으면 거기서 직접 물어보려고 |
| echo 제어가 필요함 | terminal mode를 써서 echo off 같은 처리를 하려고 |

즉 `/dev/tty`는 "입력을 더 편하게 받는 꼼수"보다, **질문용 채널을 일반 데이터 채널과 분리하려는 선택**에 가깝다.

## `stdin`과 `/dev/tty`를 나란히 보면

| 항목 | `stdin` | `/dev/tty` |
|---|---|---|
| 정체 | fd 0 기본 입력 | controlling terminal 장치 |
| pipe로 바꿀 수 있나 | 쉽다 | 보통 터미널이 있으면 그대로 남아 있다 |
| batch data 전달에 적합한가 | 그렇다 | 보통 아니다 |
| interactive prompt에 적합한가 | 도구마다 다름 | 흔히 그렇다 |
| 비밀번호 echo 제어에 잘 맞나 | pipe 자체로는 아니다 | terminal mode와 함께 쓰기 쉽다 |

초보자 기준으로는 이렇게 기억하면 충분하다.

- `stdin`은 "프로그램 기본 입력선"
- `/dev/tty`는 "사람과 대화하는 실제 터미널선"

둘이 같은 곳을 가리킬 때도 있지만, redirect나 pipe가 들어가면 쉽게 갈라질 수 있다.

## 왜 pipe로 넣었는데도 prompt가 뜨나

가장 흔한 장면은 이렇다.

```text
echo "secret" | some-cli
```

초보자는 보통 이렇게 기대한다.

```text
pipe -> stdin -> some-cli가 secret을 읽음
```

그런데 실제 프로그램이 이렇게 동작할 수 있다.

```text
1. 일반 입력이 필요하면 stdin에서 읽음
2. 비밀번호/확인 질문이 필요하면 /dev/tty를 따로 열어 읽음
3. 그래서 pipe 값은 prompt 답변으로 안 쓰임
```

즉 "pipe가 고장 났다"가 아니라, **프로그램이 그 질문에 대해서는 stdin을 답변 채널로 채택하지 않은 것**이다.

## 간단한 장면 세 개

### 1. 비밀번호 prompt

```text
echo "mypassword" | tool-login
Password:
```

가능한 해석:

- `tool-login`은 password를 `stdin`이 아니라 `/dev/tty`에서 읽는다
- 그래서 pipe의 `"mypassword"`는 password prompt 답이 아니다
- 터미널이 있으면 거기서 직접 타이핑하길 기대한다

### 2. 파괴적 작업 확인 prompt

```text
printf "y\n" | tool-delete
Are you sure? [y/N]
```

가능한 해석:

- 이 도구는 실수 방지를 위해 확인 질문을 `/dev/tty`에서 읽는다
- pipe에 우연히 들어온 `y`가 실제 사용자 의사라고 믿지 않는다

### 3. `stdin` 자체는 이미 다른 용도

```text
cat payload.json | tool-import
Enter API token:
```

이 장면에서는 `stdin`이 이미 payload 데이터 통로다.
도구는 import 데이터는 `stdin`에서 읽고, token 질문은 `/dev/tty`에서 따로 받을 수 있다.

그래서 이런 경우 `/dev/tty` 사용은 더 자연스럽다.

## `stdin`이 pipe여도 터미널은 남아 있을 수 있다

이 부분이 처음엔 가장 낯설다.

```text
shell terminal
  -> 명령 실행
  -> stdin만 pipe로 연결
  -> process는 여전히 같은 terminal 세션 안에 있음
```

즉 프로그램이:

- `fd 0`은 pipe로 보고
- 동시에 `/dev/tty`는 열 수 있는 상태

일 수 있다.

그래서 "`stdin`은 terminal이 아닌데 왜 prompt가 뜨지?"는 모순이 아니다.
프로그램이 `stdin`이 아니라 `/dev/tty`에 붙어 질문했기 때문이다.

## 왜 비밀번호 prompt에서 특히 자주 보이나

[PTY Raw Mode and Echo Basics](./pty-raw-mode-echo-basics.md)에서 본 것처럼, 비밀번호 입력은 보통 echo off 같은 terminal 제어가 필요하다.

| 질문 종류 | 도구가 원하는 성질 |
|---|---|
| 비밀번호 | 화면에 그대로 안 보이기 |
| `y/n` 확인 | 사람이 직접 눌렀다는 감각 |
| line editing 있는 질문 | terminal input 규칙 사용 |

이런 요구는 plain pipe보다 terminal 장치가 더 잘 맞는다.
그래서 password/confirmation prompt에서 `/dev/tty`가 자주 나온다.

## 흔한 오해

### 1. `/dev/tty`를 쓰면 `stdin`을 전혀 안 쓰는 건가요?

아니다. 일반 입력 데이터는 `stdin`, 질문은 `/dev/tty`처럼 역할을 나눌 수 있다.

### 2. pipe로 넣은 값이 완전히 버려진 건가요?

그 질문에 대해서는 무시됐을 수 있지만, 프로그램 다른 입력 경로에서는 소비될 수 있다. 특히 `stdin`이 payload용이면 더 그렇다.

### 3. 이건 shell 버그인가요?

대부분 아니다. shell은 pipe를 연결했을 뿐이고, 어떤 fd나 장치를 실제로 읽을지는 프로그램이 정한다.

### 4. `/dev/tty`를 쓰는 프로그램은 자동화가 불가능한가요?

아니다. 보통은 그 도구가 문서화한 non-interactive 경로를 써야 한다. 핵심은 "pipe로 억지로 답하려 하지 말고, 도구가 준비한 batch 인터페이스를 찾아라"다.

## beginner-safe 비대화형 대안

가장 안전한 기본 규칙은 이렇다.

> prompt를 속이려 하지 말고, 도구가 제공하는 non-interactive 옵션을 먼저 찾는다.

| 상황 | beginner-safe 대안 |
|---|---|
| 확인 질문을 건너뛰고 싶음 | `--yes`, `--force`, `--non-interactive` 같은 공식 옵션 확인 |
| 비밀번호를 표준 입력으로 넣고 싶음 | `--password-stdin` 같은 전용 옵션 확인 |
| 토큰/자격 증명을 넘기고 싶음 | 문서화된 env var, config file, credential helper 사용 |
| GUI/TTY 없는 환경에서 인증 필요 | `ASKPASS` 계열 helper나 서비스 토큰 방식 검토 |

여기서 중요한 건 "가능한 대안"이 아니라 **그 도구가 공식 지원하는 대안**을 쓰는 것이다.

## 비교: 나쁜 기대와 좋은 기대

| 기대 | 왜 흔히 틀리나 | 더 좋은 기대 |
|---|---|---|
| `echo secret | tool`이면 password prompt도 해결될 것이다 | tool이 `/dev/tty`에서 읽을 수 있다 | password 전용 옵션이나 credential path를 찾는다 |
| `printf 'y\n' | tool`이면 확인 질문이 사라질 것이다 | destructive confirm은 terminal만 신뢰할 수 있다 | `--yes` 같은 non-interactive flag를 찾는다 |
| pipe가 연결되면 interactive prompt는 무조건 꺼질 것이다 | 프로그램이 `/dev/tty`를 별도로 열 수 있다 | `stdin`과 terminal 질문 채널을 분리해 생각한다 |

## subprocess나 wrapper 관점에서는

subprocess wrapper를 만드는 쪽에서는 질문을 이렇게 바꿔 보는 편이 좋다.

- child가 `stdin`만 읽는가
- 아니면 `/dev/tty`를 직접 열 수 있는 interactive CLI인가
- 자동화 목표가 batch import인가, 사람-대화형 replay인가

이 판단이 먼저 서야:

- plain pipe만으로 충분한지
- PTY를 붙여야 하는지
- 아니면 아예 non-interactive API/flag를 써야 하는지

를 고를 수 있다.

prompt를 PTY로 억지 재현해야 하는 상황도 있지만, beginner 단계의 기본값은 **가능하면 prompt 자체를 우회하는 공식 비대화형 인터페이스를 찾는 것**이다.

## Self-check (자가 점검 4문항)

1. 왜 어떤 도구는 비밀번호나 확인 질문을 `stdin` 대신 `/dev/tty`에서 읽는지 설명할 수 있는가?
   힌트: 일반 데이터와 "사람 확인" 채널을 분리하려는 경우가 많다.
2. `stdin`이 pipe여도 프로그램이 여전히 터미널 prompt를 띄울 수 있는 이유를 설명할 수 있는가?
   힌트: `fd 0`과 `/dev/tty`는 같은 것이 아니다.
3. `echo secret | tool`이 실패했을 때 shell 버그보다 먼저 무엇을 의심해야 하는가?
   힌트: tool이 실제로 어느 입력 채널을 읽는지다.
4. 자동화가 필요할 때 beginner-safe 기본 대응이 무엇인지 말할 수 있는가?
   힌트: 공식 `--yes`, `--password-stdin`, env/config/helper 경로를 먼저 찾는다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`TTY냐 아니냐`에 따라 color, prompt, progress가 왜 같이 달라지는지"를 먼저 다시 보고 싶다면: [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
> - "password prompt에서 echo off 같은 terminal mode가 왜 필요한지"를 보려면: [PTY Raw Mode and Echo Basics](./pty-raw-mode-echo-basics.md)
> - "`stdin=PIPE`가 실제로 child fd 배선으로는 무엇인지"를 보려면: [popen and Runtime Wrapper Mapping](./popen-runtime-wrapper-mapping.md)
> - "pipe 입력 종료와 prompt 문제를 헷갈린다면" 먼저: [Subprocess Stdin EOF Primer](./subprocess-stdin-eof-primer.md)
> - "사람에게 보이는 terminal replay와 기계용 capture를 나눠 보고 싶다면": [TTY-Aware Output Capture Patterns](./tty-aware-output-capture-patterns.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

어떤 prompt가 pipe `stdin`을 무시하는 것은 입력이 망가져서가 아니라, 그 질문을 일반 데이터 입력이 아니라 `/dev/tty`라는 별도 터미널 채널에서 받도록 프로그램이 설계됐기 때문인 경우가 많다. 자동화가 필요하면 prompt를 속이기보다 그 도구의 공식 non-interactive 경로를 찾는 편이 안전하다.
