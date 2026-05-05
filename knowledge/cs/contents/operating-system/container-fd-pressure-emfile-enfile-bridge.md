---
schema_version: 3
title: 'Container FD Pressure Bridge: `EMFILE`, `ENFILE`, Host vs Container'
concept_id: operating-system/container-fd-pressure-emfile-enfile-bridge
canonical: false
category: operating-system
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- emfile-vs-enfile
- host-vs-container-resource-scope
aliases:
- qa-content-operating-system-00039
- container fd pressure bridge
- container fd limit confusion
- emfile vs enfile container
- host vs container fd pressure
- container too many open files host looks fine
- host file-nr container fd
- file-max in container setup
- rlimit_nofile container beginner
- file-nr beginner bridge
- pod fd looks normal but host file table full
- per-process fd limit vs host file table
- 처음 fd 에러 뭐부터 봐요
- 왜 컨테이너만 멀쩡해 보여요
- container fd visibility confusion
symptoms:
- 컨테이너 안 fd 수는 낮은데 too many open files가 나요
- pod에서는 멀쩡해 보이는데 노드 전체 fd가 찼다는 말이 헷갈려요
- EMFILE랑 ENFILE을 언제 다르게 의심해야 하나요
intents:
- comparison
prerequisites:
- operating-system/file-descriptor-basics
next_docs:
- operating-system/fd-exhaustion-ulimit-diagnostics
- operating-system/rlimit-nofile-nproc-governance
linked_paths:
- contents/operating-system/file-descriptor-basics.md
- contents/operating-system/beginner-triage-quick-check-snippet-pack.md
- contents/operating-system/fd-exhaustion-ulimit-diagnostics.md
- contents/operating-system/rlimit-nofile-nproc-governance.md
- contents/operating-system/container-cgroup-namespace.md
confusable_with:
- operating-system/fd-exhaustion-ulimit-diagnostics
- operating-system/container-cgroup-namespace
forbidden_neighbors:
- contents/operating-system/container-cgroup-namespace.md
- contents/operating-system/file-descriptor-basics.md
expected_queries:
- 컨테이너에서 too many open files가 뜨는데 호스트 fd랑 같이 봐야 해?
- 내 프로세스 fd는 적은데 ENFILE이 나는 상황을 처음 설명해줘
- pod 안에서는 괜찮아 보이는데 node file-nr이 높으면 무슨 뜻이야?
- EMFILE과 ENFILE을 컨테이너 환경에서 어떻게 구분해?
- 컨테이너 fd 문제를 볼 때 ulimit이랑 file-max 중 뭐부터 봐?
contextual_chunk_prefix: |
  이 문서는 운영체제 입문자가 컨테이너 안 숫자는 괜찮아 보이는데 왜 too many open files가 나는지, 프로세스 로컬 한도와 호스트 전역 fd pressure를 연결해 처음 혼동을 줄이는 bridge다. pod 안 fd는 적은데 실패, 노드 전체 file-nr 압박, 내 ulimit은 남았는데 에러, EMFILE과 ENFILE 구분, 컨테이너만 보면 안 보이는 전역 한도 같은 자연어 paraphrase가 본 문서의 판단 축에 매핑된다.
---
# Container FD Pressure Bridge: `EMFILE`, `ENFILE`, Host vs Container

> 한 줄 요약: 컨테이너 안 숫자가 멀쩡해 보여도, fd는 일부가 프로세스 로컬 한도이고 일부는 호스트 공유 풀이어서 `EMFILE`과 `ENFILE`를 다른 층으로 봐야 덜 헷갈린다.
>
> 문서 역할: 이 문서는 operating-system `primer`에서 [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)와 [container, cgroup, namespace](./container-cgroup-namespace.md) 사이를 잇는 beginner bridge다. "컨테이너는 멀쩡해 보이는데 왜 host fd pressure가 터지지?"라는 첫 혼동을 줄이는 데 초점을 둔다.

**난이도: 🟢 Beginner**

관련 문서:

- [파일 디스크립터 기초](./file-descriptor-basics.md)
- [Beginner Triage Quick-Check Snippet Pack](./beginner-triage-quick-check-snippet-pack.md)
- [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)
- [RLIMIT NOFILE, NPROC Governance](./rlimit-nofile-nproc-governance.md)
- [container, cgroup, namespace](./container-cgroup-namespace.md)
- [operating-system 카테고리 인덱스](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: qa-content-operating-system-00039, container fd pressure bridge, container fd limit confusion, emfile vs enfile container, host vs container fd pressure, container too many open files host looks fine, host file-nr container fd, file-max in container setup, rlimit_nofile container beginner, file-nr beginner bridge, pod fd looks normal but host file table full, per-process fd limit vs host file table, 처음 fd 에러 뭐부터 봐요, 왜 컨테이너만 멀쩡해 보여요, container fd visibility confusion

## 먼저 잡는 멘탈 모델

컨테이너 fd 문제는 "내 방의 서랍"과 "건물 공용 창고"를 같이 보는 그림으로 잡으면 쉽다.

- 프로세스마다 자기 서랍이 있다: `RLIMIT_NOFILE`, `ulimit -n`
- 호스트 전체가 같이 쓰는 공용 창고도 있다: `fs.file-max`, `file-nr`
- 컨테이너는 방을 나눠 보여 줄 뿐, 공용 창고까지 새로 만드는 것은 아니다

그래서 컨테이너 안 앱이 보는 첫 질문은 항상 둘 중 하나다.

1. 내 프로세스 서랍이 찼나? -> `EMFILE`
2. 호스트 공용 창고가 찼나? -> `ENFILE`

## 컨테이너가 보여 주는 것 vs 숨기는 것

초보자 혼동은 보통 여기서 시작한다. 컨테이너는 "아예 다른 커널"이 아니라, 같은 호스트 커널 위에 올린 격리된 실행 공간에 가깝다.

| 구분 | 컨테이너 안에서 보기 쉬운가 | 첫 해석 |
|---|---|---|
| 내 프로세스의 fd 개수 (`/proc/<pid>/fd`) | 쉽다 | "이 프로세스가 자기 서랍을 얼마나 썼나?" |
| 내 프로세스의 `Max open files` (`/proc/<pid>/limits`) | 쉽다 | "이 프로세스가 어디서 `EMFILE`에 닿나?" |
| 호스트 전체 fd 사용량 (`file-nr`) | 놓치기 쉽다 | "같은 노드의 다른 컨테이너까지 합친 공용 풀이 얼마나 찼나?" |
| 호스트 전체 상한 (`fs.file-max`) | 놓치기 쉽다 | "노드 전체가 `ENFILE` 위험 구간인가?" |

핵심은 이것이다.

- 컨테이너는 "내 프로세스 상태"를 보기 쉽게 해 준다
- 하지만 "노드 전체 공용 fd pressure"는 컨테이너 안 숫자만 보면 놓치기 쉽다

여기서 "컨테이너는 내 방" 비유는 입문용이다. 실제 Linux 컨테이너는 보통 같은 호스트 커널을 공유하므로, fd 한도도 "프로세스 로컬"과 "호스트 전역"이 섞여 보인다. 다른 가상화 방식이나 운영 환경 세부는 별도 문서에서 다시 확인하면 된다.

## 한눈에 보는 비교표

| 지금 보는 값 | 뜻 | 먼저 떠올릴 에러 | 왜 헷갈리나 |
|---|---|---|---|
| `ls /proc/<pid>/fd | wc -l` 이 `Max open files`에 가까움 | 이 프로세스 서랍이 찼다 | `EMFILE` | 컨테이너 안 숫자만 봐도 보이는 문제라 원인이 단순해 보인다 |
| `/proc/<pid>/fd`는 여유 있는데 `file-nr`이 `fs.file-max`에 가까움 | 호스트 공용 창고가 찼다 | `ENFILE` | 앱 입장에서는 "내 fd는 많지 않은데 왜 실패하지?"가 된다 |
| 둘 다 높음 | 프로세스 로컬 pressure와 호스트 전체 pressure가 같이 있다 | 둘 다 가능 | 한쪽만 보고 원인을 단정하면 틀리기 쉽다 |

짧게 줄이면:

- `EMFILE`은 "내 컨테이너 안 이 프로세스 상자" 쪽 질문이다
- `ENFILE`은 "같은 노드의 다른 컨테이너까지 합친 전체 상자" 쪽 질문이다

## 아주 작은 예시

같은 호스트에 컨테이너가 20개 떠 있다고 하자.

- 내 앱 컨테이너의 `Max open files`는 `65535`
- 내 앱의 현재 fd 개수는 `12000`
- 그런데 호스트의 `file-nr`은 `1,980,000`
- 호스트 `fs.file-max`는 `2,000,000`

이때 내 컨테이너만 보면 "아직 한참 남았네"처럼 보일 수 있다.
하지만 노드 전체는 공용 풀 끝자락이라, 새 fd를 만들 때 `ENFILE` 쪽 실패가 날 수 있다.

반대로:

- 호스트 `file-nr`은 여유가 많다
- 내 앱 컨테이너의 `Max open files`는 `1024`
- 내 앱 fd 개수는 `1018 -> 1023 -> 1024`

이 그림이면 호스트는 멀쩡해도 내 프로세스가 먼저 `EMFILE`에 닿는다.

## 첫 읽기 순서: 3개 질문만 먼저

로그에 `Too many open files`가 보였을 때 초보자 기준 첫 분기는 이 순서면 충분하다.

1. "내 프로세스 fd 수가 `Max open files`에 붙었나?"
2. "아니면 호스트 `file-nr`이 `fs.file-max`에 붙었나?"
3. "내가 지금 컨테이너 안 숫자만 보고 있나?"

짧게 매칭하면:

| 먼저 보이는 그림 | 첫 판단 |
|---|---|
| 프로세스 fd 수가 자기 limit에 거의 닿음 | `EMFILE` 쪽부터 본다 |
| 프로세스 fd 수는 낮은데 호스트 `file-nr`이 높음 | `ENFILE` 쪽부터 본다 |
| 둘 다 애매함 | 둘 다 같이 본다. 한쪽만 보고 결론 내리지 않는다 |

## 30초 분기: 무엇을 같이 봐야 하나

| 질문 | 어디서 보나 | 초보자용 해석 |
|---|---|---|
| "내 프로세스가 꽉 찼나?" | `cat /proc/<pid>/limits`, `ls /proc/<pid>/fd | wc -l` | 프로세스 로컬 한도를 본다 |
| "노드 전체가 꽉 찼나?" | `cat /proc/sys/fs/file-nr`, `cat /proc/sys/fs/file-max` | 호스트 공유 풀을 본다 |
| "컨테이너만 보고 있는가?" | 관찰 위치 확인 | 컨테이너 안 `/proc/<pid>/fd`만 보면 호스트 전체 pressure는 놓칠 수 있다 |

자주 쓰는 최소 체크:

```bash
cat /proc/<pid>/limits | grep -i "open files"
ls /proc/<pid>/fd | wc -l
cat /proc/sys/fs/file-nr
cat /proc/sys/fs/file-max
```

초보자 기준 해석은 이 정도면 충분하다.

- 앞의 두 줄은 "내 프로세스 상자"
- 뒤의 두 줄은 "노드 공용 상자"

## 자주 헷갈리는 포인트

- "컨테이너마다 `file-max`도 따로 있다" -> 보통 그렇게 생각하면 틀리기 쉽다. `RLIMIT_NOFILE`은 프로세스별이지만 `fs.file-max`는 호스트 전역 관찰값이다.
- "컨테이너 안 fd 개수가 낮으면 `Too many open files`는 아닐 것이다" -> 아니다. 호스트 전체 pressure 때문에 `ENFILE`이 날 수 있다.
- "호스트가 멀쩡하면 컨테이너도 멀쩡하다" -> 아니다. 내 프로세스 `ulimit -n`이 낮으면 호스트가 널널해도 `EMFILE`이 먼저 난다.
- "`EMFILE`과 `ENFILE`은 그냥 같은 말이다" -> 아니다. 어디 한도에 걸렸는지 다르다. 그래서 다음 확인 위치도 달라진다.
- "컨테이너 restart를 했는데 잠깐 괜찮아졌으니 내 앱만의 문제다" -> 꼭 그렇지는 않다. 재시작으로 일시적으로 내 fd 수가 줄어도, 노드 전체 pressure가 남아 있으면 같은 혼동이 다시 나온다.
- "컨테이너별 `ulimit -n`만 올리면 끝난다" -> `EMFILE`에는 도움이 될 수 있지만, 호스트 공용 풀이 문제면 `ENFILE` 쪽 관찰이 먼저다.

소켓도 fd라는 점을 잊기 쉽다. 그래서 "파일을 많이 안 열었는데 왜 fd가 차지?"라는 질문은 네트워크 연결 누수, keep-alive 과다, subprocess pipe 미정리까지 같이 보라는 신호다.

## 여기까지 이해했으면 다음 deep-dive

> **Beginner handoff box**
>
> - "`EMFILE`과 `ENFILE`을 숫자와 명령으로 더 또렷하게 가르고 싶으면": [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)
> - "컨테이너가 무엇을 분리하고 무엇을 공유하는지 다시 묶고 싶으면": [container, cgroup, namespace](./container-cgroup-namespace.md)
> - "`nofile`을 어디서 어떻게 거는지 운영 관점으로 보고 싶으면": [RLIMIT NOFILE, NPROC Governance](./rlimit-nofile-nproc-governance.md)
> - "네트워크 연결과 socket fd가 왜 같이 묶이는지"를 보려면: [Keepalive, Connection Reuse Basics](../network/keepalive-connection-reuse-basics.md)
> - 이 카테고리 안에서 다시 고르려면: [operating-system 카테고리 인덱스](./README.md)

## 한 줄 정리

컨테이너 fd 혼동은 "프로세스 로컬 한도(`EMFILE`)와 호스트 공유 풀 한도(`ENFILE`)를 같은 층으로 본 것"에서 시작하므로, `/proc/<pid>/fd`와 `file-nr`을 같이 봐야 첫 판단이 틀리지 않는다.
