---
schema_version: 3
title: '디스크가 찼는데 파일이 안 보임 — deleted-open fd 드릴'
concept_id: operating-system/fd-space-leak-log-rotation-drill
canonical: false
category: operating-system
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 72
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- deleted-open-file
- log-rotation
- fd-space-leak
aliases:
- deleted open file drill
- 디스크 찼는데 파일 안 보임
- 로그 삭제했는데 공간 안 줄어듦
- lsof deleted fd
- log rotation space leak
symptoms:
- df에서는 디스크가 가득 찼는데 du로 큰 파일이 보이지 않는다
- 로그 파일을 삭제했는데 사용량이 줄지 않는다
- 프로세스 재시작 후에야 디스크 공간이 회수된다
intents:
- drill
- troubleshooting
prerequisites:
- operating-system/file-descriptor-basics
- operating-system/deleted-open-file-space-leak-log-rotation
next_docs:
- operating-system/fd-exhaustion-ulimit-diagnostics
- operating-system/proc-pid-fdinfo-epoll-runtime-debugging
linked_paths:
- contents/operating-system/file-descriptor-basics.md
- contents/operating-system/deleted-open-file-space-leak-log-rotation.md
- contents/operating-system/fd-exhaustion-ulimit-diagnostics.md
- contents/operating-system/proc-pid-fdinfo-epoll-runtime-debugging.md
- contents/operating-system/open-file-description-dup-fork-shared-offsets.md
- contents/operating-system/subprocess-fd-hygiene-basics.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- df는 꽉 찼는데 du로 큰 파일이 안 보이면 deleted open file인지 확인하고 싶어
- 로그 삭제했는데 디스크 공간이 안 줄어드는 이유를 드릴로 풀어줘
- lsof deleted 결과를 보고 어떤 프로세스를 재시작해야 하는지 알고 싶어
- log rotation에서 copytruncate와 reopen이 왜 중요한지 예제로 확인해줘
contextual_chunk_prefix: |
  이 문서는 df는 가득 찼는데 du에는 큰 파일이 보이지 않는 상황을 deleted-open
  file descriptor와 log rotation 문제로 판별하는 operating-system drill이다.
  lsof deleted, 로그 삭제했는데 공간 안 줄어듦, 프로세스가 fd를 붙잡음,
  copytruncate/reopen 같은 질의를 파일 디스크립터 수명 진단으로 연결한다.
---
# 디스크가 찼는데 파일이 안 보임 — deleted-open fd 드릴

> 한 줄 요약: 파일을 삭제해도 프로세스가 fd를 열고 있으면 디스크 블록은 바로 회수되지 않는다. `df`와 `du`가 크게 다르면 deleted-open file을 의심한다.

**난이도: 🟡 Intermediate**

## 문제 1

상황:

```text
df -h  -> /var 100%
du -sh /var/log/* -> 큰 파일 없음
```

질문: 무엇을 의심할까?

답: 삭제됐지만 프로세스가 여전히 열고 있는 파일이다.

확인:

```text
lsof +L1
lsof | grep deleted
```

## 문제 2

상황:

```text
app.log를 rm으로 지웠다.
애플리케이션은 계속 같은 fd에 로그를 쓰고 있다.
```

질문: 왜 공간이 안 줄까?

답: directory entry는 사라졌지만 open file description은 살아 있다. 마지막 fd가 닫힐 때까지 블록이 회수되지 않는다.

## 문제 3

상황:

```text
logrotate 후에도 old log fd를 계속 잡는다.
```

해결 후보:

- 프로세스에 reopen signal을 보낸다
- 애플리케이션 logging framework가 rotate 후 파일을 다시 열게 한다
- 임시로 프로세스를 재시작한다
- `copytruncate`를 쓰는 경우 유실/중복 위험을 이해한다

## 빠른 판단표

| 관측 | 의미 |
|---|---|
| `df`만 높고 `du`는 낮다 | deleted-open file 가능성 |
| `lsof +L1`에 큰 파일이 보인다 | 해당 process가 공간을 붙잡음 |
| restart 후 공간 회수 | fd가 닫히면서 블록 회수 |
| rotate 후에도 같은 inode에 write | reopen 실패 가능성 |

## 한 줄 정리

`df`와 `du`가 다르고 로그 삭제 후 공간이 안 줄면 파일 이름이 아니라 열린 fd를 추적해야 한다.
