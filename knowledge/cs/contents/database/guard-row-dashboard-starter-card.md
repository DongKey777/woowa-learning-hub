# Guard-Row Dashboard Starter Card

> 한 줄 요약: guard-row 경로의 첫 대시보드는 "얼마나 오래 기다리나", "대기가 몇 개 key에 몰리나", "그 대기 중 deadlock 비중이 얼마나 되나"라는 세 질문만 한 화면에 두면 시작할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Guard-Row Contention Observability Cheatsheet](./guard-row-contention-observability-cheatsheet.md)
- [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)
- [Striped Guard Row Budgeting Primer](./striped-guard-row-budgeting-primer.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Busy: Fail-Fast vs One Short Retry Card](./busy-fail-fast-vs-one-short-retry-card.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: guard row dashboard starter, guard-row dashboard starter card, guard row 3 panel dashboard, guard row wait panel, hot key concentration panel, deadlock share panel, guard row observability thresholds, beginner guard row dashboard, guard row p95 wait threshold, top1 key concentration threshold, deadlock share threshold, room_type_day dashboard card, campaign guard dashboard, same key concentration dashboard, guard row dashboard starter card basics

## 먼저 멘탈모델

guard row dashboard는 "락이 많다"를 보는 화면이 아니라 **한 줄 queue가 얼마나 길어지고, 얼마나 한 key에 몰리고, 그 queue가 순환 대기로 깨졌는지**를 보는 화면이다.

초보자 기준으로는 아래 세 패널이면 충분하다.

1. wait time: 줄이 얼마나 길어졌나
2. hot-key concentration: 그 줄이 한두 개 key에 몰렸나
3. deadlock share: 단순 대기인지, 순환 대기로 바뀌었나

## 3패널 스타터 구성

| 패널 | 질문 | 추천 지표 | starter threshold |
|---|---|---|---|
| Wait Time | "지금 줄이 길어졌나?" | `guard_row_wait_p95_ms` | green `< 30ms`, yellow `30-100ms`, red `> 100ms` |
| Hot-Key Concentration | "문제가 몇 개 key에 몰리나?" | `top1_guard_key_wait_share` | green `< 20%`, yellow `20-50%`, red `> 50%` |
| Deadlock Share | "단순 대기가 아니라 순환 대기로 깨졌나?" | `deadlock_share_on_guard_path` | green `< 1%`, yellow `1-5%`, red `> 5%` |

이 숫자는 universal truth가 아니라 **첫 화면 starter band**다.
서비스마다 절대값은 달라도, 초반에는 이 세 칸만으로 "hot row인지", "ordering 문제인지", "그냥 바쁜 정도인지"를 빠르게 가를 수 있다.

## 패널별 뜻

### 1. Wait Time 패널

가장 먼저 보는 값은 보통 평균이 아니라 `p95`다.

- 평균은 짧은 요청이 섞이면 문제를 가릴 수 있다
- `p95`는 "상위 느린 tail이 실제로 길어졌는가"를 먼저 보여 준다

starter 해석:

| 구간 | 초보자 해석 | 첫 액션 |
|---|---|---|
| `< 30ms` | queue는 보이지만 아직 짧다 | hot key가 한쪽으로 몰리는지만 같이 본다 |
| `30-100ms` | 사용자 tail latency로 번질 수 있다 | top key와 retry 증가를 같이 본다 |
| `> 100ms` | guard row가 체감 지연의 주인공일 가능성이 높다 | blocker path, 트랜잭션 길이, same-key 집중도를 바로 본다 |

### 2. Hot-Key Concentration 패널

이 패널은 "전체 wait가 커졌다"보다 더 설명력이 좋다.
핵심은 **상위 1개 key가 전체 대기의 몇 %를 차지하는가**다.

예:

- `room_type:17:2026-05-05`
- `campaign:coupon-2026-spring`
- `tenant:42`

starter 해석:

| 구간 | 초보자 해석 | 첫 액션 |
|---|---|---|
| `< 20%` | 특정 한 key보다 wider write pressure에 가깝다 | pool, SQL shape, broader contention도 함께 본다 |
| `20-50%` | hot key 후보가 선명해진다 | 상위 key 3개와 해당 path를 묶어 본다 |
| `> 50%` | 한 key queue가 거의 incident를 지배한다 | striping, narrower surface, fail-fast를 우선 검토한다 |

### 3. Deadlock Share 패널

deadlock share는 "guard-row 관련 lock conflict 중 deadlock이 차지하는 비중"으로 보면 된다.

가장 단순한 시작식:

```text
deadlock_share_on_guard_path
  = deadlock_total
    / (deadlock_total + lock_wait_timeout_total)
```

starter 해석:

| 구간 | 초보자 해석 | 첫 액션 |
|---|---|---|
| `< 1%` | 주로 한 줄 대기다 | hot key와 긴 트랜잭션을 먼저 본다 |
| `1-5%` | 일부 path에서 잠금 순서가 흔들릴 수 있다 | create/cancel/expire/admin path의 ordering을 비교한다 |
| `> 5%` | 단순 혼잡보다 protocol 불일치가 더 의심된다 | canonical ordering 회귀, 다중 row touch 순서, retry 폭증을 같이 본다 |

중요한 점:

## 패널별 뜻 (계속 2)

- wait time이 높아도 deadlock share가 낮으면, 문제 중심은 보통 **긴 queue**다
- wait time이 중간이어도 deadlock share가 높으면, 문제 중심은 보통 **ordering drift**다

## 지표 정의를 아주 작게 고정하기

초기 버전에서는 panel 정의를 복잡하게 만들지 않는 편이 낫다.

| 지표 | 초보자용 정의 |
|---|---|
| `guard_row_wait_p95_ms` | guard row를 잡으려다 기다린 시간의 p95 |
| `top1_guard_key_wait_share` | 최근 window wait 이벤트 중 가장 뜨거운 key 1개의 비중 |
| `deadlock_share_on_guard_path` | guard-row path의 `deadlock / (deadlock + timeout)` |

window는 보통 `5분` 또는 `10분`으로 시작하면 충분하다.
너무 짧으면 흔들리고, 너무 길면 incident 순간 집중이 흐려진다.

## 한 화면에서 이렇게 읽는다

| Wait Time | Hot-Key Concentration | Deadlock Share | 첫 결론 |
|---|---|---|---|
| red | red | green | classic single hot guard row 가능성이 높다 |
| yellow | red | red | 한 key도 뜨겁고 ordering도 흔들린다 |
| red | green | green | guard row 자체보다 wider transaction 길이 또는 다른 병목도 의심해야 한다 |
| yellow | green | red | 대기 길이보다 protocol drift를 먼저 본다 |

## 아주 작은 예시

```text
guard_row_wait_p95_ms = 128
top1_guard_key_wait_share = 67%
deadlock_share_on_guard_path = 0.4%
top1_guard_key = room_type:17:2026-05-05
```

초보자 첫 해석:

- 줄은 이미 길다
- incident가 사실상 한 key에 몰렸다
- deadlock 비중은 낮으므로 ordering보다 hot row queue가 중심이다

이 경우 첫 질문은 "`room_type:17:2026-05-05`를 더 좁게 나누거나 더 빨리 패배시키는 방법이 있는가?"다.

반대로:

```text
guard_row_wait_p95_ms = 42
top1_guard_key_wait_share = 28%
deadlock_share_on_guard_path = 8%
```

이 장면은 "매우 뜨거운 한 key"보다 **몇 개 path가 잠금 순서를 다르게 밟고 있다** 쪽에 더 가깝다.

## 자주 하는 오해

- wait time만 높으면 무조건 deadlock 문제다
  - 아니다. deadlock share가 낮으면 그냥 한 줄 queue일 수 있다.
- top1 share가 높으면 전체 트래픽도 그 key 하나뿐이다
  - 아니다. "문제가 된 wait 이벤트"가 그 key에 몰렸다는 뜻이다.
- deadlock share가 0이면 safe하다
  - 아니다. timeout과 긴 tail latency만으로도 사용자 영향은 충분히 클 수 있다.
- starter threshold를 SLA처럼 고정해야 한다
  - 아니다. 이 문서의 숫자는 첫 triage band다. 서비스 특성에 맞춰 나중에 조정하면 된다.

## 바로 이어서 볼 문서

- wait/duplicate/deadlock/slow query를 먼저 구분하고 싶다면 → [Guard-Row Contention Observability Cheatsheet](./guard-row-contention-observability-cheatsheet.md)
- "이 key가 너무 뜨거운가?"를 구조적으로 읽고 싶다면 → [Guard Row Hot-Row Symptoms Primer](./guard-row-hot-row-symptoms-primer.md)
- single hot row를 stripe로 쪼갤 때의 첫 규칙을 보고 싶다면 → [Striped Guard Row Budgeting Primer](./striped-guard-row-budgeting-primer.md)

## 한 줄 정리

guard-row 경로의 첫 대시보드는 "얼마나 오래 기다리나", "대기가 몇 개 key에 몰리나", "그 대기 중 deadlock 비중이 얼마나 되나"라는 세 질문만 한 화면에 두면 시작할 수 있다.
