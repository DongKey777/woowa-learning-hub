# Alt-Svc To 421 Timeline Bridge


> 한 줄 요약: Alt-Svc To 421 Timeline Bridge는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
> 예전에 배운 `Alt-Svc`나 endpoint discovery 상태가 왜 한참 뒤 `HTTP/3 421 Misdirected Request`로 이어질 수 있는지, 초급자용 한 개 타임라인으로 이어 주는 bridge

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 관련 문서:
> - [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
> - [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
> - [Alt-Svc Cache vs Per-Origin 421 Recovery](./alt-svc-cache-vs-per-origin-421-recovery.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
> - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)

retrieval-anchor-keywords: alt-svc to 421 timeline, stale discovery to 421, stale alt-svc timeline bridge, http/3 421 timeline beginner, old endpoint hint later 421, discovery state to recovery, h3 stale hint retry timeline, alt-svc then 421 then 200, stale endpoint authority timeline, same url 421 recovery bridge, http/3 endpoint discovery stale, h3 wrong path after old alt-svc, beginner alt-svc 421 bridge, stale h3 endpoint learned yesterday, old discovery state fresh path retry

## 먼저 고정할 한 문장

`Alt-Svc`나 HTTPS RR은 "어디로 H3를 시도할지"를 배운 기억이고, `421`은 "방금 그 길은 지금 이 origin에 맞지 않는다"는 나중 교정 신호다.

## 30초 mental model

초급자는 아래 4칸만 먼저 잡으면 된다.

| 칸 | 질문 | 초급자 해석 |
|---|---|---|
| discovery | 브라우저가 H3 endpoint를 어디서 배웠나 | 예전 응답의 `Alt-Svc`, DNS의 HTTPS RR |
| cache / memory | 그 기억이 아직 남아 있나 | `ma` 안이거나 브라우저가 아직 후보를 기억 |
| request | 오늘 요청을 그 기억으로 먼저 보냈나 | 예전 H3 path를 먼저 탔을 수 있음 |
| recovery | 그 길이 틀리면 어떻게 교정되나 | `421` 뒤 fresh path로 다시 감 |

핵심은 이것이다.

- discovery는 "예전에 배운 힌트"
- `421`은 "지금 그 힌트로 탄 path가 틀렸다는 교정"
- 둘은 시간이 떨어져 있어도 같은 이야기일 수 있다

## 왜 이 bridge가 필요한가

입문자는 아래 두 장면을 서로 다른 문제로 따로 본다.

- 오전에 응답 header에서 `Alt-Svc`를 봤다
- 오후에 같은 URL이 `421 -> 200`으로 보인다

하지만 실제로는 하나의 타임라인일 수 있다.

1. 브라우저가 예전에 H3 후보 endpoint를 배운다.
2. 시간이 지난 뒤에도 그 기억을 가지고 첫 시도를 한다.
3. 운영 경로나 authority가 바뀌었으면 그 첫 시도가 `421`로 교정된다.
4. 브라우저가 새 connection 또는 기본 경로로 다시 가며 회복한다.

즉 이 문서는 "`어디서 배웠나`"와 "`왜 나중에 421이 나왔나`"를 한 줄로 이어 주는 용도다.

## 한눈에 보는 전체 타임라인

```text
1. 어제: origin이 Alt-Svc 또는 HTTPS RR로 H3 endpoint 후보를 알려 줌
2. 브라우저: 그 endpoint discovery 상태를 기억
3. 오늘: 같은 origin 또는 관련 요청을 예전 기억으로 먼저 H3 path에 실음
4. 현실 변화: 그 endpoint나 shared connection이 이제 그 origin에 authoritative하지 않음
5. edge/server: 421 Misdirected Request 반환
6. 브라우저: "이 origin을 이 path에 싣는 것은 틀렸구나"를 학습
7. 새 H3 connection, 다른 H3 endpoint, 또는 H2 기본 경로로 재선택
8. 같은 URL이 200 또는 원래 app 응답으로 회복
```

초급자용 한 줄 요약:

- 앞부분은 "배운 단계"
- 가운데는 "낡은 기억으로 첫 시도"
- 뒷부분은 "`421`로 교정 후 fresh path 재시도"

## 단계별로 풀어 읽기

| 단계 | 무슨 일이 있나 | 여기서 바로 단정하면 안 되는 것 |
|---|---|---|
| `Alt-Svc` 또는 HTTPS RR를 배움 | H3 후보 endpoint를 알게 됨 | "이제 모든 요청이 영원히 H3다" |
| 시간이 지나도 기억이 남아 있음 | 브라우저가 다음 새 connection에서 그 후보를 다시 검토 | "예전 힌트가 지금도 반드시 맞다" |
| 오늘 첫 H3 시도 | 브라우저가 예전 path를 먼저 믿어 봄 | "첫 실패면 URL 자체가 틀렸다" |
| `421` 수신 | 방금 사용한 path/connection이 이 origin에 안 맞음을 교정 | "`403/404` 같은 앱 오류다" |
| fresh path 재시도 | 새 connection 또는 기본 경로로 다시 감 | "같은 URL 두 줄이면 프런트 중복 호출이다" |

## 가장 흔한 beginner 타임라인 2개

### 타임라인 A. 예전 `Alt-Svc`가 stale해진 경우

```text
1. 어제 h2 응답에서 Alt-Svc: h3="edge-a.example.net:443"; ma=86400 학습
2. 오늘 브라우저가 admin.example.com 요청을 edge-a 쪽 H3에 먼저 보냄
3. 하지만 admin은 이제 edge-b 또는 기본 경로만 authoritative
4. edge-a가 421 반환
5. 브라우저가 새 path로 다시 보내 200 회복
```

이 장면의 포인트:

- `Alt-Svc`는 틀린 지식이 아니라 "예전에는 맞았던 지식"일 수 있다
- `421`은 그 예전 path가 지금은 안 맞는다는 교정이다

### 타임라인 B. discovery는 맞았지만 shared H3 reuse가 틀린 경우

```text
1. 브라우저는 H3 endpoint discovery 자체는 여전히 갖고 있음
2. 기존 H3 connection을 다른 origin에도 같이 써 봄
3. 그 reuse 조합이 틀려 421 발생
4. 브라우저가 같은 origin 전용 새 H3 connection 또는 H2로 재시도
5. 둘째 요청은 성공
```

이 장면의 포인트:

- discovery가 있었다는 사실과 reuse가 안전하다는 사실은 다르다
- 그래서 discovery가 살아 있어도 `421`이 날 수 있다

## DevTools에서 보이는 흔한 모양

| URL | Status | Protocol | Connection ID | 초급자 1차 해석 |
|---|---:|---|---:|---|
| `https://admin.example.com/api/me` | `421` | `h3` | `42` | 예전 H3 path 또는 wrong shared H3 reuse일 수 있음 |
| `https://admin.example.com/api/me` | `200` | `h3` | `57` | 새 H3 connection으로 fresh path recovery했을 수 있음 |
| `https://admin.example.com/api/me` | `200` | `h2` | `71` | 브라우저가 더 보수적으로 H2 fallback을 골랐을 수 있음 |

여기서 먼저 볼 순서는 아래와 같다.

1. 같은 URL이 `421 -> 200/403/404`로 두 줄 보이는지 본다.
2. `Connection ID`가 바뀌었는지 본다.
3. `Protocol`이 다시 `h3`인지 `h2`인지 본다.
4. 그다음에야 app 문제인지 추가 판독한다.

## 자주 헷갈리는 말 번역표

| 헷갈리는 말 | 더 안전한 해석 |
|---|---|
| "`Alt-Svc`를 봤으니 421은 이상하다" | 이상한 것이 아니라, 예전 discovery 상태가 나중에 교정된 것일 수 있다 |
| "`421`이면 discovery가 틀렸다" | discovery는 맞았지만 그 path 또는 reuse 문맥이 틀렸을 수 있다 |
| "`421 -> 200`이면 프런트가 두 번 호출했다" | 브라우저의 자동 recovery trace일 수도 있다 |
| "`421 -> h2`면 Alt-Svc가 원래 없었다" | 아니다. discovery는 있었어도 recovery에서 H2가 더 안전하다고 판단할 수 있다 |

## 한 번에 설명하는 짧은 비교표

| 질문 | discovery 단계가 답하는 것 | `421` recovery 단계가 답하는 것 |
|---|---|---|
| 무엇을 묻나 | H3 endpoint를 어디서 배웠나 | 방금 쓴 path/connection이 맞았나 |
| 시간 위치 | 요청 이전 또는 예전 응답 시점 | 실제 요청 이후 |
| 흔한 증거 | `Alt-Svc`, HTTPS RR | `421`, 새 `Connection ID`, `h3 -> h3` 또는 `h3 -> h2` 재시도 |
| 초급자 결론 | "시도 근거가 있었다" | "첫 시도 path는 틀려서 교정됐다" |

## 다음에 바로 이어서 볼 문서

- discovery 자체를 더 분리해서 보면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- `ma`, cache scope, `421`을 더 짧게 비교하려면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- stale hint가 `421` 뒤 fresh path로 회복되는 장면을 더 길게 보려면 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- `421` 뒤 새 H3와 H2 fallback이 어떻게 갈리는지 보려면 [Alt-Svc Cache vs Per-Origin 421 Recovery](./alt-svc-cache-vs-per-origin-421-recovery.md)
- DevTools와 로그에서 recovery 증거를 읽으려면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)

## 한 줄 정리

예전에 `Alt-Svc`나 HTTPS RR로 배운 H3 endpoint 기억이 남아 있으면, 브라우저는 나중 요청에서도 그 path를 먼저 시도할 수 있다. 그 path가 더 이상 맞지 않으면 `HTTP/3 421`이 교정 신호로 나오고, 그다음 새 connection 또는 기본 경로의 fresh path로 회복될 수 있다.
