---
schema_version: 3
title: Open File Description dup fork Shared Offsets
concept_id: operating-system/open-file-description-dup-fork-shared-offsets
canonical: true
category: operating-system
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- open-file-description
- dup-fork-shared
- offsets
- shared-offset
aliases:
- open file description shared offset
- dup fork fd shared offsets
- O_APPEND shared file status
- nonblocking shared status flags
- subprocess IO shared offset
- file descriptor vs open file description
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/o-cloexec-fd-inheritance-exec-leaks.md
- contents/operating-system/fork-exec-copy-on-write-behavior.md
- contents/operating-system/pipe-socketpair-eventfd-memfd-ipc-selection.md
- contents/operating-system/deleted-open-file-space-leak-log-rotation.md
expected_queries:
- file descriptor 번호가 달라도 같은 open file description을 공유하면 무엇이 함께 움직여?
- dup와 fork 후 shared offset 때문에 로그 쓰기나 subprocess I/O가 예상과 다를 수 있어?
- O_APPEND, nonblocking 같은 file status flag는 fd마다 독립이야?
- file descriptor와 open file description 차이를 운영 문제로 설명해줘
contextual_chunk_prefix: |
  이 문서는 file descriptor number와 open file description을 구분한다. dup나 fork로 다른 fd가
  같은 open file description을 공유하면 offset, append mode, nonblocking status가 함께 움직여
  subprocess I/O와 logging에서 예상과 다른 동작이 나올 수 있다.
---
# Open File Description, dup, fork, Shared Offsets

> 한 줄 요약: file descriptor 숫자는 각각 달라도 같은 open file description을 공유하면 offset, append mode, nonblocking 상태가 함께 움직일 수 있어 로그 쓰기, 파이프라인, 서브프로세스 I/O에서 예상과 다른 동작이 나온다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)
> - [Fork, Exec, Copy-on-Write Behavior](./fork-exec-copy-on-write-behavior.md)
> - [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
> - [deleted-but-open files, log rotation, space leak debugging](./deleted-open-file-space-leak-log-rotation.md)

> retrieval-anchor-keywords: open file description, dup, dup2, dup3, fork fd sharing, shared offset, O_APPEND, O_NONBLOCK, file status flags, per-fd flags, shared file position

## 핵심 개념

백엔드 개발자가 자주 보는 것은 `int fd`지만, 커널이 실제로 추적하는 중요한 단위는 open file description이다. `dup()`이나 `fork()`로 만들어진 여러 fd가 같은 open file description을 가리키면, 이들은 같은 file offset과 일부 file status를 공유한다.

- `file descriptor`: 프로세스 로컬의 정수 핸들이다
- `open file description`: 열린 파일 객체에 대한 커널 쪽 실제 참조다
- `dup*()`: 새로운 fd 번호를 만들지만, 보통 같은 open file description을 공유한다
- `fork()`: 자식이 부모의 열린 참조를 이어받는다

왜 중요한가:

- `read()`/`write()`/`lseek()`가 서로 다른 fd에서도 같은 offset을 움직일 수 있다
- `O_APPEND`, `O_NONBLOCK` 같은 상태가 shared behavior를 만든다
- "별도 fd니까 독립적이겠지"라는 가정이 로그/파이프/소켓 경로에서 틀릴 수 있다

## 깊이 들어가기

### 1. `dup()`은 새 open이 아니라 새 참조다

`dup`, `dup2`, `dup3`는 파일을 다시 여는 것이 아니라, 기존 열린 객체를 가리키는 새 번호를 만든다.

- file offset을 공유한다
- append/nonblocking 같은 status도 공유될 수 있다
- close-on-exec 같은 descriptor flag는 공유되지 않을 수 있다

즉 숫자는 둘이지만 실제 열린 객체는 하나일 수 있다.

### 2. `fork()` 뒤 parent/child도 같은 열린 객체를 볼 수 있다

자식 프로세스는 부모의 fd table을 이어받고, 많은 경우 그 참조는 같은 open file description을 본다.

- parent가 읽으면 child의 다음 offset도 달라질 수 있다
- child가 nonblocking으로 바꾸면 parent도 영향을 받을 수 있다
- pipe/socket에서 half-close/EOF 감각이 꼬일 수 있다

그래서 subprocess I/O 설계는 "누가 어떤 번호를 갖는가"보다 "누가 같은 열린 객체를 공유하는가"를 먼저 봐야 한다.

### 3. 독립 offset이 필요하면 추가 `open()`이 필요하다

동일한 path를 다시 `open()`하면 보통 별도 open file description을 얻는다.

- 같은 경로라도 offset이 독립적이다
- `dup()`과 다르게 status/state 공유가 줄어든다
- read cursor를 분리하고 싶을 때 유용하다

즉 "새 번호가 필요하다"와 "새 열린 객체가 필요하다"는 다른 요구다.

### 4. 이 차이는 서버에서 생각보다 자주 문제를 만든다

- subprocess stdout/stderr redirect
- logger fd reuse
- parent/child pipeline
- 같은 file을 여러 reader가 읽는 유틸리티

문제는 보통 race처럼 보이지만, 실제로는 shared offset/shared status semantics다.

## 실전 시나리오

### 시나리오 1: 두 워커가 같은 파일을 읽는데 cursor가 꼬인다

가능한 원인:

- `dup()`한 fd를 각 워커가 나눠 들고 있다
- 같은 open file description을 공유한다
- 한쪽의 `read()`가 다른 쪽의 offset을 움직인다

대응 감각:

- 독립 cursor가 필요하면 각자 `open()`한다
- `dup()`은 새 번호이지 새 cursor가 아니라는 점을 문서화한다

### 시나리오 2: child에 넘긴 fd 설정 변경이 parent에도 영향을 준다

가능한 원인:

- `O_NONBLOCK` 변경이 shared status로 전파된다
- parent/child가 같은 열린 객체를 보고 있다
- close-on-exec와 file status flag를 혼동했다

이 경우는 per-fd flag와 shared file status를 구분해야 한다.

### 시나리오 3: append logger가 예상과 다른 순서로 섞인다

가능한 원인:

- 여러 참조가 같은 open description을 공유한다
- `O_APPEND`와 write atomicity 기대가 뒤섞인다
- rotation/reopen 시점과 old/new fd 수명이 겹친다

이 경우는 append semantics와 deleted-open/rotation 문제를 같이 봐야 한다.

## 코드로 보기

### 같은 열린 객체를 공유하는 경우

```c
int fd1 = open("data.log", O_WRONLY | O_APPEND);
int fd2 = dup(fd1);
```

### 독립 열린 객체가 필요한 경우

```c
int fd1 = open("data.log", O_WRONLY | O_APPEND);
int fd2 = open("data.log", O_WRONLY | O_APPEND);
```

### mental model

```text
dup(fd)
  -> new number
  -> same underlying open description

open(path)
  -> usually new number
  -> new underlying open description
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `dup()` 공유 | handoff가 단순하다 | offset/status sharing이 숨은 coupling이 된다 | redirect, inherited I/O |
| 별도 `open()` | 독립 cursor와 state를 갖기 쉽다 | open 비용과 lifecycle 관리가 늘어난다 | independent readers/writers |
| `fork()` 후 공유 유지 | 표준 유닉스 동작과 잘 맞는다 | parent/child side effect가 생긴다 | 단순 pipeline |
| `exec()` 전 재구성 | 수명 경계를 명확히 나눌 수 있다 | setup 코드가 늘어난다 | supervisor/subprocess hygiene |

## 꼬리질문

> Q: `dup()`한 fd 둘은 완전히 독립적인가요?
> 핵심: 아니다. 번호는 달라도 같은 open file description을 공유하면 offset과 일부 status가 함께 움직일 수 있다.

> Q: 독립 file offset이 필요하면 어떻게 하나요?
> 핵심: 보통 같은 path를 다시 `open()`해 별도 open file description을 얻어야 한다.

> Q: `FD_CLOEXEC`와 `O_NONBLOCK`는 같은 층의 설정인가요?
> 핵심: 아니다. close-on-exec는 descriptor flag이고, nonblocking은 shared file status 쪽이라 영향 범위가 다르다.

## 한 줄 정리

backend에서 fd 버그를 줄이려면 "숫자 fd"보다 "같은 open file description을 공유하고 있는가"를 먼저 생각하는 습관이 중요하다.
