# Master Notes

> 개별 문서를 많이 읽는 대신, 여러 분야를 한 번에 엮어 학습하고 회수하기 위한 상위 요약 노트 모음

> retrieval-anchor-keywords: master notes guide, master note overview, synthesis guide, cross-domain reading, symptom-first navigator, broad question routing, master note role, retrieval escalation

## 이 문서의 목적

`contents/` 아래의 문서는 주제별 깊이를 담당한다.  
`master-notes/` 아래의 문서는 그 개별 문서들을 묶어서:

- 증상 기반으로 빠르게 찾고
- 여러 분야를 함께 연결하고
- 실전 의사결정 단위로 압축하고
- RAG가 넓은 질문에도 안정적으로 회수할 수 있게

만드는 상위 노트다.

즉 `master-notes`는 카테고리 README의 대체물이 아니라, **교차 관점 학습용 상위 레이어**다.
대표 노트 목록은 [Master Notes Index](./master-notes/README.md), 문서 역할 기준은 [Navigation Taxonomy](./rag/navigation-taxonomy.md)에서 함께 본다.

## 어떤 상황에서 보는가

- “지금 느린데 네트워크인지 DB인지 JVM인지 모르겠다”
- “트랜잭션, 이벤트, outbox, 재시도를 한 번에 엮어서 이해하고 싶다”
- “JWT, 세션, 쿠키, OIDC, BFF를 인증 흐름 관점에서 정리하고 싶다”
- “마이그레이션, cutover, dual write, rollback을 점진 전환 관점에서 보고 싶다”
- “미션을 하다가 지금 필요한 CS만 큰 그림으로 먼저 잡고 싶다”

## 구성 원칙

- 각 노트는 하나의 실전 주제나 증상을 중심으로 여러 카테고리를 묶는다.
- 각 노트는 `EXPERT-TEAM`의 문서 구조를 그대로 따른다.
- 각 노트는 최소 5개 이상의 개별 문서로 교차 링크한다.
- 각 노트는 retrieval anchor keyword를 충분히 포함한다.
- 각 노트는 “무엇을 먼저 볼지”가 아니라 “어떻게 연결해서 판단할지”를 다룬다.

## 현재 초점

이번 확장 사이클에서는 아래 축을 우선 채운다.

- latency / timeout / retry / backpressure
- transaction / consistency / idempotency / outbox
- auth / session / token / proxy / trust boundary
- JVM / OS / native memory / performance
- migration / strangler / branch by abstraction / rollout
- cache / invalidation / stampede / hot key

## 사용 순서

1. 먼저 [README.md](./README.md) 또는 각 카테고리 README로 주제 위치를 잡는다.
2. 그다음 `master-notes/`에서 증상이나 의사결정 단위의 상위 노트를 읽는다.
3. 필요할 때 세부 문서로 내려간다.
4. 질문을 더 쪼개야 하면 [query-playbook.md](./rag/query-playbook.md)와 [cross-domain-bridge-map.md](./rag/cross-domain-bridge-map.md)를 함께 본다.

## 관련 문서

- [Master Notes Index](./master-notes/README.md)
- [Navigation Taxonomy](./rag/navigation-taxonomy.md)
- [RAG Ready Checklist](./RAG-READY.md)
- [Advanced Backend Roadmap](./ADVANCED-BACKEND-ROADMAP.md)
- [Senior-Level Questions](./SENIOR-QUESTIONS.md)
- [Topic Map](./rag/topic-map.md)
- [Query Playbook](./rag/query-playbook.md)
- [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md)
