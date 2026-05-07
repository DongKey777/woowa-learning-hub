---
schema_version: 3
title: Backend Runtime Resource Symptom Mission Bridge
concept_id: operating-system/backend-runtime-resource-symptom-mission-bridge
canonical: false
category: operating-system
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 78
mission_ids:
- missions/payment
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- runtime-triage
- cpu-scheduling
- fd-pressure
- cgroup-throttling
aliases:
- backend runtime resource symptom bridge
- backend OS triage mission bridge
- CPU fd cgroup latency bridge
- p99 latency runtime resource bridge
- 백엔드 런타임 리소스 브리지
symptoms:
- API p99가 튀는데 CPU 평균만 보고 애플리케이션 로직 문제로 단정한다
- too many open files, cgroup throttling, accept backlog를 backend 장애와 연결하지 못한다
- 컨테이너 안 지표와 host 지표의 범위 차이를 설명하지 못한다
intents:
- mission_bridge
- troubleshooting
- design
prerequisites:
- operating-system/beginner-symptom-to-doc-map
- operating-system/cpu-scheduling-basics
next_docs:
- operating-system/backend-api-latency-runtime-triage-bridge
- operating-system/container-fd-pressure-emfile-enfile-bridge
- operating-system/cgroup-cpu-throttling-quota-runtime-debugging
linked_paths:
- contents/operating-system/beginner-symptom-to-doc-map.md
- contents/operating-system/backend-api-latency-runtime-triage-bridge.md
- contents/operating-system/cpu-scheduling-basics.md
- contents/operating-system/container-fd-pressure-emfile-enfile-bridge.md
- contents/operating-system/cgroup-cpu-throttling-quota-runtime-debugging.md
- contents/operating-system/accept-overload-observability-playbook.md
confusable_with:
- operating-system/backend-api-latency-runtime-triage-bridge
- operating-system/beginner-symptom-to-doc-map
- operating-system/cpu-scheduling-basics
forbidden_neighbors:
- contents/software-engineering/backend-service-refactor-first-test-mission-bridge.md
expected_queries:
- backend API p99 latency를 OS resource 관점 mission bridge로 설명해줘
- CPU 평균은 낮은데 응답이 느릴 때 scheduler cgroup fd를 어떻게 봐?
- too many open files가 미션 API 장애와 어떻게 연결되는지 알려줘
- 컨테이너 안에서는 정상인데 host resource 문제일 수 있는 장면을 정리해줘
- payment backend runtime triage를 운영체제 문서로 연결해줘
contextual_chunk_prefix: |
  이 문서는 backend runtime resource symptom mission_bridge다. API p99 latency,
  CPU average low, run queue, cgroup throttling, EMFILE/ENFILE, accept backlog,
  container vs host metrics 같은 미션 증상을 operating-system triage 개념으로
  매핑한다.
---
# Backend Runtime Resource Symptom Mission Bridge

> 한 줄 요약: backend API 지연은 항상 service 코드 문제만이 아니라, runnable 대기, cgroup quota, fd 한도, accept backlog 같은 runtime resource 증상일 수 있다.

**난이도: Beginner**

## 미션 진입 증상

| backend 증상 | OS 질문 |
|---|---|
| 평균 CPU는 낮은데 p99가 튄다 | runnable/run queue 대기가 있는가 |
| container CPU는 남아 보인다 | cgroup quota throttling이 있는가 |
| 간헐적으로 connection accept가 늦다 | listen backlog/accept queue가 차는가 |
| too many open files | process fd 한도인가 host file table인가 |
| 재시작 후 잠깐 좋아진다 | 누수/누적 resource인지 확인했는가 |

## 리뷰 신호

- "로직은 빠른데 배포 환경에서만 느려요"는 runtime 지표를 같이 보라는 신호다.
- "CPU가 낮으니 OS 문제는 아니죠?"는 CPU usage와 scheduler wait를 구분하라는 말이다.
- "`ulimit`만 올리면 되나요?"는 EMFILE/ENFILE과 누수 원인을 같이 보라는 뜻이다.
- "컨테이너에서는 정상인데 노드에서만 이상해요"는 host/container 관측 범위를 분리하라는 신호다.

## 판단 순서

1. API latency가 CPU, IO, network, lock, pool wait 중 어디에 붙는지 1차 분기한다.
2. CPU 평균보다 runnable/run queue와 throttled counter를 본다.
3. fd/socket 오류는 process 한도와 host file table을 나눠 본다.
4. accept 지연은 app handler보다 listen/accept queue 증거를 먼저 확인할 수 있다.

이 bridge는 학습자가 backend 장애를 application stack 안에서만 보지 않고 OS 관찰 신호로 연결하게 만든다.
