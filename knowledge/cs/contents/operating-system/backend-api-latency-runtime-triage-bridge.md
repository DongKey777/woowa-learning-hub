---
schema_version: 3
title: Backend API Latency Runtime Triage Bridge
concept_id: operating-system/backend-api-latency-runtime-triage-bridge
canonical: false
category: operating-system
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: mixed
source_priority: 76
mission_ids:
- missions/roomescape
- missions/spring-roomescape
- missions/shopping-cart
- missions/payment
review_feedback_tags:
- runtime-triage
- api-latency
- cpu-memory-io
- backend-observability
aliases:
- backend api latency runtime triage
- API 느림 OS triage bridge
- 서버가 느린데 CPU memory IO 구분
- roomescape shopping-cart runtime latency
- top vmstat iostat backend bridge
symptoms:
- API가 느린데 애플리케이션 로그만 보고 CPU, 메모리, I/O를 나누지 못한다
- checkout이나 reservation API가 가끔 느려질 때 DB 문제인지 OS 문제인지 바로 단정한다
- container CPU throttling, memory pressure, iowait 같은 런타임 신호를 코칭 질문으로 연결하지 못한다
intents:
- mission_bridge
- troubleshooting
- drill
prerequisites:
- operating-system/cpu-memory-io-first-triage-command-drill
- operating-system/runtime-symptom-to-os-signal-router-beginner
next_docs:
- operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait
- operating-system/fd-space-leak-log-rotation-drill
- operating-system/blocking-io-thread-pool-backpressure-primer
linked_paths:
- contents/operating-system/cpu-memory-io-first-triage-command-drill.md
- contents/operating-system/runtime-symptom-to-os-signal-router-beginner.md
- contents/operating-system/load-average-triage-cpu-saturation-cgroup-throttling-io-wait.md
- contents/operating-system/blocking-io-thread-pool-backpressure-primer.md
- contents/operating-system/fd-space-leak-log-rotation-drill.md
- contents/database/connection-pool-starvation-symptom-router.md
confusable_with:
- operating-system/runtime-symptom-to-os-signal-router-beginner
- operating-system/cpu-memory-io-first-triage-command-drill
- database/connection-pool-starvation-symptom-router
forbidden_neighbors:
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
expected_queries:
- API가 느릴 때 OS 관점 CPU memory IO를 어떻게 먼저 나눠?
- roomescape reservation API latency를 runtime triage로 연결해줘
- shopping-cart checkout timeout이 DB인지 OS인지 첫 신호를 어떻게 봐?
- top vmstat iostat를 백엔드 미션 리뷰 질문으로 어떻게 써?
contextual_chunk_prefix: |
  이 문서는 backend API latency runtime triage mission_bridge다. API slow,
  checkout timeout, reservation latency, CPU saturation, memory pressure,
  iowait, fd leak, container throttling 같은 미션 증상을 OS first triage
  질문으로 매핑한다.
---
# Backend API Latency Runtime Triage Bridge

> 한 줄 요약: API가 느릴 때 바로 코드나 DB 탓으로 단정하지 말고 CPU, memory, I/O, limit hit를 먼저 나눠야 한다.

**난이도: Beginner**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "API가 느린데 코드 문제인지 DB 문제인지 OS 문제인지 모르겠어요" | 예약 목록, checkout, 결제 승인 API latency triage | 애플리케이션 로그만 보지 말고 CPU, memory, I/O, limit hit를 먼저 나눈다 |
| "가끔만 timeout이 나서 쿼리부터 튜닝해야 할지 모르겠어요" | 특정 시간대 장바구니/예약 요청 지연 | DB wait, thread blocking, iowait, throttling 신호를 분리한다 |
| "컨테이너에서만 느린데 로컬에서는 빨라요" | 배포 환경에서만 재현되는 미션 장애 | host 전체 부하와 cgroup CPU/memory 제한을 따로 본다 |

## CS concept 매핑

| 미션 장면 | OS/runtime 질문 |
|---|---|
| reservation 목록 API가 갑자기 느림 | CPU saturation인지 I/O wait인지 |
| checkout 요청이 timeout | DB wait, thread pool wait, external I/O wait 분리 |
| 로그 파일 삭제 후 디스크가 안 비워짐 | deleted-open-file / fd leak |
| container에서만 느림 | cgroup CPU throttling / memory pressure |
| connection pool timeout | DB 문제인지 thread blocking인지 first split |

## 리뷰 신호

- "API가 느려요"만으로 쿼리 튜닝부터 시작하면 관측 축이 부족하다.
- "load average가 높으니 CPU 문제"라고 바로 말하면 I/O wait를 놓칠 수 있다.
- "로그를 삭제했는데 용량이 그대로"는 애플리케이션 로그 설정보다 open fd를 봐야 한다.
- "container만 느립니다"는 host 전체가 아니라 cgroup 제한을 확인해야 한다.

## 판단 순서

1. `top`/`vmstat`으로 CPU runnable과 iowait를 나눈다.
2. `free`/memory events로 memory pressure와 OOM을 확인한다.
3. `iostat`이나 DB wait를 보며 I/O와 lock wait를 분리한다.
4. fd, thread, connection pool 같은 limit hit를 확인한다.

이 bridge는 운영 명령 자체를 외우게 하려는 문서가 아니라, 코칭 답변이 "느림"을 한 덩어리로 설명하지 않도록 첫 분기 언어를 제공한다.
