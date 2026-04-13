# Real-time Collaboration Backend 설계

> 한 줄 요약: 실시간 협업 백엔드는 여러 사용자의 동시 편집, 충돌 해결, presence, 오프라인 복구를 함께 처리하는 동기화 시스템이다.

retrieval-anchor-keywords: real-time collaboration, concurrent editing, presence, operational transform, crdt, cursor sync, offline sync, conflict resolution, awareness, document room

**난이도: 🔴 Advanced**

> 관련 문서:
> - [채팅 시스템 설계](./chat-system-design.md)
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Distributed Lock 설계](./distributed-lock-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)

## 핵심 개념

실시간 협업은 단순히 텍스트를 주고받는 채팅이 아니다.  
실전에서는 다음을 함께 다뤄야 한다.

- 동시 편집
- 충돌 해결
- presence / cursor awareness
- offline sync
- version history
- comment / suggestion mode

즉, 협업 백엔드는 "문서 상태를 공유하는 분산 동기화 엔진"이다.

## 깊이 들어가기

### 1. 편집 모델

대표적으로 두 접근이 있다.

| 방식 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| OT | 문서 중심 직관적 | 구현이 복잡하다 | 전통적 협업 편집 |
| CRDT | 분산 합성이 쉽다 | 상태 크기가 커질 수 있다 | 오프라인/분산 우선 |

협업 편집은 단순 CRUD가 아니므로, 변경 연산을 어떻게 합칠지가 핵심이다.

### 2. Capacity Estimation

예:

- 1만 동시 문서 세션
- 세션당 5명 동시 접속
- 초당 수십 편집 연산

이 경우 read보다 write sync와 presence broadcast가 더 중요한 병목이 된다.

봐야 할 숫자:

- concurrent sessions
- ops/sec
- propagation delay
- reconnect rate
- merge conflict rate

### 3. 아키텍처

```text
Client
  -> Realtime Gateway
  -> Document Session Service
  -> Sync Engine
  -> Presence Service
  -> Persistence / Snapshot Store
  -> Event Queue
```

gateway는 연결을 유지하고, sync engine은 연산을 정규화하고, storage는 상태를 보관한다.

### 4. Session ownership

문서 세션은 한 노드가 owner 역할을 하는 편이 안정적이다.

- room/document 단위 partition
- primary session owner
- heartbeat 기반 failover

이게 없으면 동시에 두 노드가 문서를 처리하며 충돌이 늘어난다.

### 5. Conflict resolution

동시 편집 충돌은 다음을 통해 줄인다.

- OT transform
- CRDT merge
- optimistic local apply
- server ack ordering

중요한 것은 "충돌을 없애는 것"이 아니라 **사용자 경험을 깨지 않는 방식으로 충돌을 수용하는 것**이다.

### 6. Presence와 awareness

실시간 협업은 누가 보고 있는지, 어디에 커서가 있는지가 중요하다.

- user join/leave
- cursor position
- selection range
- typing indicator

이 정보는 강한 영속성이 필요하지 않지만, 늦으면 UX가 급격히 나빠진다.

### 7. Offline sync

오프라인 동안 편집한 내용을 나중에 합쳐야 한다.

필요한 것:

- client operation log
- version vector
- reconnect handshake
- conflict retry

이 부분은 [채팅 시스템 설계](./chat-system-design.md)에서 다루는 메시지/오프라인 복구와 비슷하지만, 문서 병합이 훨씬 어렵다.

## 실전 시나리오

### 시나리오 1: 동시에 같은 문단 수정

문제:

- 두 사용자가 같은 부분을 고쳤다

해결:

- OT 또는 CRDT로 merge
- 서버는 순서와 version을 관리

### 시나리오 2: 네트워크가 끊겼다가 재접속

문제:

- 클라이언트가 오래 오프라인이었다

해결:

- 로컬 op log를 보낸다
- 서버 version과 대조한다
- 충돌을 rebase한다

### 시나리오 3: 대형 문서 room 폭주

문제:

- 수백 명이 한 문서를 본다

해결:

- presence와 edit path를 분리한다
- broadcast를 계층화한다
- session owner를 shard한다

## 코드로 보기

```pseudo
function applyOp(docId, op, clientVersion):
  state = load(docId)
  transformed = transformIfNeeded(state, op, clientVersion)
  newState = apply(state, transformed)
  save(docId, newState)
  broadcast(docId, transformed)
```

```java
public void onEdit(DocumentOp op) {
    syncEngine.apply(op);
    presenceService.broadcast(op.documentId());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| OT | 문서 협업에 익숙하다 | 구현이 까다롭다 | 전통적인 편집기 |
| CRDT | 분산/오프라인에 강하다 | 상태가 커질 수 있다 | 모바일/오프라인 우선 |
| Central session owner | 일관성이 쉽다 | failover가 필요하다 | 대부분의 서비스 |
| Fully peer sync | 탈중앙화 | 운영이 어렵다 | 특수한 협업 |
| Snapshot + op log | 복구가 쉽다 | 저장이 늘어난다 | 실서비스 기본형 |

핵심은 협업 백엔드가 단순한 실시간 채팅이 아니라 **동시성, 병합, 상태 복구를 포함한 문서 동기화 시스템**이라는 점이다.

## 꼬리질문

> Q: 채팅 시스템과 협업 백엔드는 어떻게 다른가요?
> 의도: 메시징과 상태 동기화 구분 확인
> 핵심: 채팅은 메시지 전달, 협업은 공유 상태 병합이 중심이다.

> Q: OT와 CRDT의 차이는 무엇인가요?
> 의도: 동시 편집 알고리즘 이해 확인
> 핵심: OT는 변환 중심, CRDT는 합성 중심이다.

> Q: presence는 왜 별도 서비스로 두나요?
> 의도: 실시간 awareness와 영속 상태 구분 확인
> 핵심: 자주 변하고 영속성이 낮아 별도 경로가 적합하다.

> Q: 오프라인 편집은 어떻게 합치나요?
> 의도: 재접속과 버전 동기화 이해 확인
> 핵심: client op log와 server version을 대조해 rebase한다.

## 한 줄 정리

Real-time collaboration backend는 다중 사용자의 동시 편집과 병합, presence, 오프라인 복구를 다루는 문서 동기화 인프라다.

