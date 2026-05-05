---
schema_version: 3
title: 'roomescape 관리자 예약 생성 POST 뒤 목록 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지'
concept_id: spring/roomescape-admin-reservation-post-redirect-get-bridge
canonical: false
category: spring
difficulty: beginner
doc_role: mission_bridge
level: beginner
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- redirect-after-post
- refresh-resubmit-boundary
- prg-vs-read-after-write
aliases:
- roomescape PRG
- roomescape 관리자 예약 redirect after post
- roomescape 예약 생성 뒤 redirect
- roomescape 관리자 예약 새로고침 재전송
- roomescape admin reservations PRG
symptoms:
- roomescape 관리자 예약을 추가한 뒤 목록 화면에서 F5를 누르면 같은 요청이 다시 나갈까 불안해요
- 예약 생성 POST 응답에서 바로 HTML을 그렸더니 브라우저가 양식 재전송을 묻는 이유를 모르겠어요
- 리뷰에서 redirect after post를 하라는데 roomescape에서는 왜 필요한지 감이 안 와요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- spring/mvc-controller-basics
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- network/post-redirect-get-prg-beginner-primer
next_docs:
- network/post-redirect-get-prg-beginner-primer
- database/roomescape-reservation-create-read-after-write-bridge
- database/idempotency-key-and-deduplication
- software-engineering/roomescape-reservation-flow-service-layer-bridge
linked_paths:
- contents/network/post-redirect-get-prg-beginner-primer.md
- contents/database/roomescape-reservation-create-read-after-write-bridge.md
- contents/database/idempotency-key-and-deduplication.md
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/spring/roomescape-reservation-request-validation-binding-bridge.md
confusable_with:
- database/roomescape-reservation-create-read-after-write-bridge
- database/idempotency-key-and-deduplication
- spring/roomescape-reservation-request-validation-binding-bridge
forbidden_neighbors: []
expected_queries:
- roomescape 관리자 예약 생성 후 결과를 바로 렌더하지 말고 목록 GET으로 redirect 하라는 리뷰는 무슨 뜻이야?
- roomescape에서 예약 추가 성공 화면을 POST 응답으로 바로 보여 주면 새로고침 때 왜 같은 요청 재전송이 문제돼?
- 관리자 예약 생성 뒤 `redirect:/admin/reservations` 같은 흐름이 왜 브라우저 계약을 더 안정적으로 만들어?
- roomescape에서 PRG와 방금 저장한 예약이 바로 보이는 문제는 서로 어떻게 다른 축이야?
- 예약 생성 뒤 목록으로 보내는 redirect와 DB 중복 제출 방어는 각각 무엇을 맡아?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 생성 POST를 처리한 뒤
  결과를 바로 렌더하지 않고 `/admin/reservations` 같은 조회 GET으로 redirect해
  다시 여는 PRG(Post/Redirect/Get) 경계를 설명하는 mission_bridge다. roomescape
  관리자 예약 새로고침 재전송, redirect after post, 목록 GET 복귀, PRG와
  read-after-write 및 중복 제출 방어의 역할 차이 같은 학습자 표현을
  브라우저-서버 계약과 연결한다.
---

# roomescape 관리자 예약 생성 POST 뒤 목록 새로고침 ↔ Spring PRG(Post/Redirect/Get) 브릿지

## 한 줄 요약

> roomescape에서 관리자 예약 생성이 상태를 바꾸는 POST라면, 완료 화면은 그 응답에서 바로 끝내기보다 redirect 뒤 목록 GET으로 다시 열어야 브라우저 새로고침이 같은 생성 요청을 다시 재생하는 혼란을 줄일 수 있다.

## 미션 시나리오

roomescape 관리자 화면을 만들 때 처음에는 `POST /admin/reservations`를 처리한
controller가 성공 메시지와 예약 목록 모델을 채워 곧바로 HTML을 렌더하기 쉽다.
화면은 바로 보이지만, 학습자가 F5를 누르거나 브라우저가 "양식 재전송"을 묻는
순간 "방금 예약 생성 POST를 또 보내도 되나?"라는 어색한 상태가 드러난다.

PR에서 "`POST` 뒤에는 redirect로 끊어 주세요", "완료 후에는 다시 열 수 있는 GET
주소를 가지게 하세요"라는 코멘트가 붙는 자리가 여기다. roomescape에서는 예약
추가 직후 다시 목록으로 돌아가 확인하는 흐름이 흔하므로, 결과 화면의 주소가 POST
응답에 묶여 있으면 브라우저 새로고침의 책임과 서버의 상태 변경 책임이 섞인다.

## CS concept 매핑

여기서 닿는 개념은 PRG(Post/Redirect/Get)다. 상태 변경은 POST가 맡고, 사용자가
다시 보게 될 결과 화면은 redirect 이후 GET이 맡는다. 예를 들어
`POST /admin/reservations`가 성공하면 `303 See Other` 또는 redirect 응답으로
`GET /admin/reservations`를 다시 열게 해서, 목록 화면의 새로고침 대상이 "같은
예약 생성 POST"가 아니라 "이미 반영된 목록 조회 GET"이 되게 만든다.

다만 PRG는 브라우저 새로고침 경계를 정리할 뿐, 같은 생성 요청이 두 번 들어오는
문제 자체를 끝내 주지는 않는다. 더블클릭이나 timeout 뒤 재시도는 redirect 전에
이미 두 POST가 서버에 도착할 수 있다. 또 redirect 뒤 목록에 방금 예약이 바로
안 보인다면 그것은 PRG보다 read-after-write 축에 가깝다. 즉 roomescape에서는
PRG, 중복 제출 방어, 직후 조회 freshness를 서로 다른 질문으로 나눠 읽어야 한다.

| roomescape 장면 | 더 가까운 개념 | 왜 그 개념으로 읽나 |
| --- | --- | --- |
| 예약 생성 성공 뒤 목록 화면 새로고침이 불안함 | PRG, redirect after post | 브라우저가 다시 열 주소를 POST가 아니라 GET으로 바꿔야 하기 때문이다 |
| 더블클릭으로 같은 생성 요청이 두 번 들어옴 | idempotency, dedup | redirect 전에 이미 중복 POST가 들어온 문제라 저장소 계약이 필요하다 |
| redirect 뒤 첫 목록 조회에 방금 예약이 안 보임 | read-after-write | 주소 전환은 됐지만 직후 조회 freshness가 약한 것이다 |
| controller가 생성과 목록 조회를 한 응답에서 모두 끝냄 | HTTP flow separation | 상태 변경과 조회 화면 재오픈 책임이 한 응답에 섞인다 |

## 미션 PR 코멘트 패턴

- "`POST` 성공 응답에서 바로 목록 HTML을 렌더하면 새로고침 대상이 생성 요청으로 남습니다."라는 코멘트는 결과 화면을 GET 주소로 분리하라는 뜻이다.
- "`redirect:/admin/reservations`로 넘겨서 브라우저가 다시 열 주소를 바꿔 보세요."라는 코멘트는 roomescape 관리자 목록을 조회 화면으로 재정의하라는 뜻이다.
- "redirect를 넣어도 중복 생성 방어가 끝난 건 아닙니다."라는 코멘트는 PRG와 멱등성/중복 제출 방어를 다른 축으로 설명하라는 뜻이다.
- "redirect 뒤 첫 조회가 비면 PRG보다 read-after-write 문제를 먼저 의심하세요."라는 코멘트는 화면 전환과 freshness 문제를 분리하라는 뜻이다.

## 다음 학습

- PRG 자체를 HTTP 왕복 기준으로 다시 정리하려면 [Post/Redirect/Get(PRG) 패턴 입문](../network/post-redirect-get-prg-beginner-primer.md)을 읽는다.
- redirect는 했는데 방금 만든 예약이 목록에 바로 안 보이면 [roomescape 예약 생성 직후 재조회 ↔ Read-After-Write 브릿지](../database/roomescape-reservation-create-read-after-write-bridge.md)로 이어진다.
- 같은 생성 요청을 저장소에서 한 번만 인정하는 계약을 보려면 [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)를 본다.
- 예약 생성 유스케이스 순서를 controller가 아니라 service에 두는 이유를 다시 묶으려면 [roomescape 관리자 예약 생성 흐름 ↔ Service 계층 브릿지](../software-engineering/roomescape-reservation-flow-service-layer-bridge.md)를 함께 본다.
