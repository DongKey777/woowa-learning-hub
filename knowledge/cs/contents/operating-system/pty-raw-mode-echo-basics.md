---
schema_version: 3
title: PTY Raw Mode Echo Basics
concept_id: operating-system/pty-raw-mode-echo-basics
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 73
review_feedback_tags:
- pty-raw-mode
- echo
- canonical-non-canonical
- terminal-mode
aliases:
- PTY raw mode echo
- canonical non-canonical terminal mode
- echo off
- interactive CLI PTY
- terminal line discipline
- pseudo tty raw mode
intents:
- definition
- troubleshooting
linked_paths:
- contents/operating-system/pseudo-tty-vs-pipe-behavior.md
- contents/operating-system/tty-aware-output-capture-patterns.md
- contents/operating-system/stdio-buffering-after-redirect.md
- contents/operating-system/ci-log-merge-behavior-primer.md
- contents/operating-system/subprocess-pipe-backpressure-primer.md
expected_queries:
- PTY에서 raw mode와 canonical mode, echo는 무엇을 결정해?
- interactive CLI는 왜 pipe보다 PTY에서 다르게 동작해?
- vim이나 shell line editor가 raw/non-canonical echo off를 쓰는 이유는?
- PTY면 interactive하다는 말을 terminal mode와 line discipline으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 PTY에서 terminal mode가 문자를 언제 program에 넘길지와 입력을 화면에 다시 echo할지
  결정한다는 점을 설명한다. canonical mode, raw/non-canonical mode, echo on/off를 초급자에게
  연결한다.
---
# PTY Raw Mode and Echo Basics

> 한 줄 요약: PTY에서는 "문자를 언제 프로그램에 넘길지"와 "내가 친 글자를 화면에 다시 보여 줄지"를 terminal mode가 결정한다. simple line-oriented CLI는 보통 canonical mode + echo 위에서 동작하고, shell의 line editor나 `vim` 같은 full-screen app은 raw/non-canonical + echo off 쪽으로 바꿔서 동작한다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md) 다음에 읽는 beginner bridge다. "`PTY면 interactive하다`는 말이 정확히 무슨 뜻이야?"를 canonical mode, raw mode, echo 세 축으로 풀어 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
- [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)
- [Session vs Process Group Primer](./session-vs-process-group-primer.md)
- [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
- [operating-system 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: operating-system-00070, pty raw mode echo basics, pty raw mode, tty raw mode basics, terminal canonical mode basics, canonical mode vs raw mode, cooked mode vs raw mode, line discipline beginner, tty echo basics, echo off password prompt, shell raw mode, vim raw mode, full screen app tty mode, line oriented cli tty mode, enter key canonical mode

## 먼저 잡는 멘탈 모델

PTY를 "키보드와 화면 사이에 있는 작은 비서"처럼 생각하면 쉽다.

- canonical mode: 비서가 한 줄을 모아 두었다가 Enter를 누르면 프로그램에 넘긴다
- raw mode: 비서가 거의 가공하지 않고 키 입력을 바로바로 넘긴다
- echo on/off: 비서가 사용자가 친 글자를 화면에 다시 찍어 줄지 말지를 정한다

핵심은 이것이다.

> PTY는 단순한 byte 통로가 아니라, 입력을 바로 줄지 한 줄로 모을지, 입력 문자를 화면에 다시 보일지 같은 "terminal 규칙"을 같이 갖는다.

그래서 같은 PTY를 써도 프로그램 종류에 따라 체감이 달라진다.

| 프로그램 종류 | 흔한 terminal mode | 사용자가 느끼는 모습 |
|---|---|---|
| simple line-oriented CLI | canonical + echo on | 글자를 치면 보이고, Enter를 눌러야 프로그램이 입력을 받는다 |
| shell line editor | raw/non-canonical 계열 + echo off 또는 직접 redraw | 화살표, history, 한 글자씩 편집이 즉시 반응한다 |
| `vim`, `top`, `less` 같은 full-screen app | raw/non-canonical + echo off | 화면 전체를 다시 그리며 키 하나마다 바로 반응한다 |

## canonical mode는 무엇인가

canonical mode는 "한 줄 단위로 입력을 모아서 전달하는 모드"라고 보면 된다.

사용자가 이런 순서로 입력한다고 하자.

```text
h e l l o Backspace o Enter
```

canonical mode에서는 terminal 쪽이 먼저 이를 처리한다.

- `Backspace`로 줄 안의 글자를 지울 수 있다
- `Enter`를 누르기 전까지 프로그램은 보통 전체 줄을 받지 못한다
- 프로그램은 대개 `"hello\n"` 같은 완성된 줄을 받는다

그래서 단순한 REPL이나 line-oriented CLI는 canonical mode에서 다루기 편하다.

```text
사용자 타이핑 -> terminal이 줄 편집 -> Enter -> 프로그램 read()
```

초보자 관점에서는 "프로그램이 한 글자씩 읽는 것처럼 보이지 않네"라고 느껴질 수 있는데, 그 이유가 바로 canonical mode다.

## raw mode는 무엇인가

raw mode는 "terminal이 중간 가공을 거의 하지 않고 키 입력을 바로 넘기는 쪽"이라고 보면 된다.

이 모드에서는 보통:

- Enter를 기다리지 않고 키 하나마다 반응할 수 있다
- 화살표, `Ctrl-R`, `Esc` 같은 키를 앱이 직접 해석할 수 있다
- 화면 redraw를 앱이 직접 책임진다

그래서 shell의 line editor나 full-screen app이 raw/non-canonical 계열을 좋아한다.

| 하고 싶은 일 | canonical mode만으로는 불편한 이유 | raw/non-canonical을 쓰는 이유 |
|---|---|---|
| 화살표로 커서 이동 | Enter 전까지 앱이 키를 바로 못 받기 쉽다 | 키 이벤트를 즉시 받아 직접 커서를 옮길 수 있다 |
| history 검색 | 줄 완성 뒤가 아니라 타이핑 중간에 반응해야 한다 | 한 글자마다 입력을 받아 검색을 갱신한다 |
| `vim` 화면 편집 | terminal이 줄 단위 입력을 대신 처리하면 안 맞다 | 앱이 키와 화면을 직접 관리한다 |
| `top`/`htop` 단축키 | `q`, 화살표, `PgUp`에 즉시 반응해야 한다 | 키 입력을 바로 받아 화면을 다시 그린다 |

여기서 beginner가 기억할 안전한 표현은 이것이다.

> shell과 full-screen app은 PTY를 쓰기만 하는 것이 아니라, 그 PTY의 terminal mode도 자주 바꾼다.

## echo는 무엇인가

echo는 "내가 친 문자를 terminal이 화면에 다시 보여 주는가"를 뜻한다.

- echo on: `abc`를 치면 화면에도 `abc`가 보인다
- echo off: `abc`를 쳐도 화면에는 그대로 보이지 않는다

이 기능은 프로그램 출력과 다르다.
내가 친 문자를 **terminal이 대신 복사해서 보여 주는 것**에 가깝다.

초보자가 자주 헷갈리는 예:

- 비밀번호 입력에서 글자가 안 보인다 -> 보통 echo off
- `vim`에서 글자를 쳤는데 화면은 앱 규칙대로만 바뀐다 -> terminal echo 대신 앱이 화면을 직접 관리
- raw mode인데 화면이 정상적으로 보인다 -> terminal echo가 아니라 앱이 직접 redraw 중일 수 있다

## 세 가지를 한 장면으로 보면

| 질문 | canonical mode | raw/non-canonical mode |
|---|---|---|
| 입력 전달 단위 | 보통 한 줄 | 보통 한 키 또는 작은 byte 조각 |
| Backspace 처리 | terminal이 먼저 처리 | 앱이 직접 처리하기 쉽다 |
| Enter 전 read() | 대개 줄이 안 모이면 기다림 | 키가 오면 바로 깨어날 수 있다 |
| echo on일 때 | 내가 친 글자가 보임 | 보일 수도 있지만 보통 interactive app은 echo를 끄고 직접 그림 |
| 어울리는 프로그램 | 단순 line CLI | shell line editor, `vim`, `less`, `top` |

즉 raw mode와 echo off는 같은 개념이 아니다.

- raw mode는 "입력을 언제 어떻게 넘길까"
- echo는 "입력 문자를 화면에 다시 찍을까"

둘은 자주 같이 바뀌지만, 서로 다른 스위치다.

## 왜 shell은 simple CLI와 다르게 느껴지나

여기서 초보자가 가장 궁금해하는 장면을 풀어 보자.

### 1. 단순 line-oriented CLI

예를 들어 아주 단순한 입력 프로그램은 이런 기대를 갖는다.

- 사용자가 한 줄을 입력한다
- Enter를 누른다
- 그다음 줄 전체를 읽는다

이 경우 canonical mode + echo on이면 자연스럽다.

```text
사용자: hello
화면  : hello
프로그램: Enter 후 "hello\n"를 한 번에 읽음
```

### 2. interactive shell

shell prompt에서 화살표, history, `Ctrl-A`, `Ctrl-E`가 즉시 먹히는 이유는 보통 shell의 line editor가 terminal을 raw/non-canonical 쪽으로 바꿔 한 글자씩 받기 때문이다.

즉 shell은 단순히 "줄을 읽는 프로그램"이 아니라:

- 키 하나마다 반응하고
- 커서를 움직이고
- 현재 줄을 다시 그리는 작은 UI 프로그램에 가깝다

그래서 같은 PTY 위에서도 shell은 simple CLI와 다르게 느껴진다.

### 3. full-screen app

`vim`, `less`, `top` 같은 앱은 더 나아가 화면 전체를 직접 다룬다.

- 화살표를 누르면 바로 스크롤/이동
- `q`를 누르면 즉시 종료
- 화면 일부만 다시 그리거나 전체를 refresh

이 동작은 canonical mode로는 불편하므로 raw/non-canonical + echo off 조합이 흔하다.

## PTY에서만 더 두드러져 보이는 이유

[Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)에서 봤듯이, PTY를 받으면 프로그램은 "나는 terminal과 대화 중"이라고 느낀다.

그러면 프로그램은 단순 출력만 바꾸는 것이 아니라:

- terminal mode를 바꿀 수 있고
- prompt를 띄우고
- echo를 끄고
- 키 하나마다 반응하는 UI로 들어갈 수 있다

반대로 plain pipe에서는 이런 전제가 약해진다.

- interactive mode를 아예 끄거나
- line editor를 비활성화하거나
- password prompt를 거부하거나
- progress redraw를 plain log로 바꿀 수 있다

즉 "PTY라서 갑자기 shell스럽고 화면 앱스럽게 보인다"는 말은, 단순히 통로가 바뀐 것이 아니라 **TTY detection + terminal mode 전환**이 같이 일어났기 때문이다.

## 자주 헷갈리는 포인트

- "raw mode면 자동으로 echo도 꺼지나요?" -> 자주 같이 바꾸지만 개념상 별도다.
- "echo off면 프로그램이 입력을 못 받는 건가요?" -> 아니다. 입력은 받되 화면에 그대로 복사하지 않을 뿐이다.
- "canonical mode면 `Ctrl-C`가 앱에 문자로 들어가나요?" -> 보통 terminal 규칙이 먼저 관여한다. full-screen app은 raw/non-canonical 쪽으로 바꿔 이런 키를 더 직접 다루려 한다.
- "shell은 항상 canonical mode인가요?" -> 단순히 줄만 받는 순간도 있지만, interactive line editing 중에는 raw/non-canonical 계열로 바꾸는 경우가 흔하다.
- "PTY만 있으면 무조건 `vim`처럼 동작하나요?" -> 아니다. PTY는 그런 동작이 가능하게 할 뿐이고, 실제로 mode를 바꾸는 것은 프로그램이다.

## Self-check (자가 점검 4문항)

1. canonical mode를 "한 줄 입력을 모아 주는 모드"로 말할 수 있는가?
   힌트: Enter 전까지 terminal이 입력 편집을 먼저 맡는 그림을 떠올리면 된다.
2. raw/non-canonical mode가 shell line editor나 `vim`에 잘 맞는 이유를 설명할 수 있는가?
   힌트: 키 하나마다 즉시 반응하고 화면을 앱이 직접 관리해야 한다.
3. echo와 raw mode가 서로 다른 스위치라는 점을 말할 수 있는가?
   힌트: 하나는 입력 전달 방식, 다른 하나는 화면에 다시 보여 줄지 여부다.
4. PTY가 simple CLI와 full-screen app의 행동 차이를 왜 키우는지 설명할 수 있는가?
   힌트: PTY가 terminal mode 변경과 TTY-aware interactive 경로를 가능하게 만든다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`PTY라서 interactive해진다`는 큰 그림부터 다시 고정하고 싶다면": [Pseudo-TTY vs Pipe Behavior](./pseudo-tty-vs-pipe-behavior.md)
> - "`Ctrl-C`, foreground job, controlling terminal까지 이어서 보고 싶다면": [Session vs Process Group Primer](./session-vs-process-group-primer.md)
> - "shell이 foreground/background와 terminal ownership을 어떻게 다루는지 보고 싶다면": [Shell Job-Control Command Bridge](./shell-job-control-command-bridge.md)
> - "subprocess에서 PTY 대신 pipe를 썼을 때 어떤 차이가 생기는지 보고 싶다면": [Subprocess FD Hygiene Basics](./subprocess-fd-hygiene-basics.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

canonical mode는 "한 줄로 모아 주는 입력 모드", raw/non-canonical mode는 "키를 바로 넘기는 입력 모드", echo는 "친 글자를 화면에 다시 보여 줄지"다. shell과 full-screen app이 PTY에서 다르게 느껴지는 이유는 이 세 스위치를 앱이 적극적으로 바꾸기 때문이다.
