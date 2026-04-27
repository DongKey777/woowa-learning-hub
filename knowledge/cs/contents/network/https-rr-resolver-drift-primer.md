# HTTPS RR Resolver Drift Primer: browser DoH, OS resolver, `dig`가 왜 다르게 보이나

> 브라우저 DoH, OS resolver, terminal `dig`가 같은 host의 `HTTPS` RR/SVCB를 서로 다르게 보여 줄 때, 먼저 "`누가 누구에게 물었는가`"부터 분리하게 만드는 beginner primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [DNS over HTTPS Operational Trade-offs](./dns-over-https-operational-tradeoffs.md)
> - [DNS Split-Horizon Behavior](./dns-split-horizon-behavior.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [DNS 기초](./dns-basics.md)

retrieval-anchor-keywords: HTTPS RR resolver drift, browser DoH vs dig, OS resolver vs browser resolver, HTTPS RR SVCB mismatch, browser secure DNS answer differs, dig HTTPS different from browser, why dig and browser disagree, resolver path drift, DoH resolver drift, HTTPS RR cache drift, SVCB different answer, browser DoH OS dig primer, same host different HTTPS RR, split horizon HTTPS RR, HTTPS RR TTL drift, resolver comparison checklist, dig bypasses browser cache, dig bypasses OS cache, browser secure DNS mismatch, H3 DNS hint disagreement

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [세 주체를 한 줄로 구분하기](#세-주체를-한-줄로-구분하기)
- [왜 같은 host인데 답이 달라지나](#왜-같은-host인데-답이-달라지나)
- [가장 흔한 4가지 원인](#가장-흔한-4가지-원인)
- [짧은 예시: browser는 `h3`, `dig HTTPS`는 비어 있는 경우](#짧은-예시-browser는-h3-dig-https는-비어-있는-경우)
- [30초 체크리스트: 비교를 공정하게 만드는 방법](#30초-체크리스트-비교를-공정하게-만드는-방법)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡는 mental model

같은 질문처럼 보여도 실제로는 **서로 다른 사람에게 묻고 있을 수 있다**.

- browser는 자체 DoH resolver에 물을 수 있다
- OS는 회사 DNS나 집 공유기 DNS에 물을 수 있다
- terminal `dig`는 `/etc/resolv.conf`의 nameserver나 사용자가 지정한 `@resolver`에 직접 물을 수 있다

그래서 "`같은 host를 조회했다`"보다 먼저 봐야 할 것은 이것이다.

> `누가`, `어떤 resolver에게`, `언제`, `어떤 cache 상태로` 물었는가

이 네 가지가 다르면 `HTTPS` RR/SVCB answer가 달라져도 이상한 일이 아니다.

### Retrieval Anchors

- `HTTPS RR resolver drift`
- `browser DoH vs dig`
- `OS resolver vs browser resolver`
- `resolver path drift`
- `same host different HTTPS RR`

---

## 세 주체를 한 줄로 구분하기

입문자는 아래 표만 먼저 고정하면 된다.

| 보는 대상 | 보통 누구에게 묻나 | 초급자 메모 |
|---|---|---|
| browser | browser 자체 DoH provider 또는 browser가 선택한 system path | browser는 OS와 다른 resolver를 쓸 수 있다 |
| OS resolver | 시스템 DNS 설정, 로컬 stub, 회사 VPN DNS | 앱이 OS API를 쓰면 이 답을 볼 가능성이 높다 |
| terminal `dig` | `resolv.conf`의 nameserver 또는 `@8.8.8.8`처럼 사용자가 직접 지정한 resolver | `dig`는 비교 대상 resolver를 내가 고를 수 있다 |

핵심은 "`browser가 본 DNS`"와 "`내 terminal에서 본 DNS`"가 자동으로 같지 않다는 점이다.

## 왜 같은 host인데 답이 달라지나

`HTTPS` RR/SVCB는 특히 아래 차이에 민감하다.

| 축 | browser DoH | OS resolver | `dig` |
|---|---|---|---|
| resolver 자체 | browser 설정에 따라 public DoH일 수 있다 | 사내 DNS, 공유기 DNS, VPN DNS일 수 있다 | 기본 nameserver 또는 `@resolver` 직접 지정 |
| cache 위치 | browser 내부 cache | OS/stub cache | 보통 직접 질의 결과를 바로 봄 |
| 정책/뷰 | browser policy, Secure DNS mode | split-horizon, VPN, enterprise policy | 내가 고른 resolver의 정책을 그대로 봄 |
| 시점 | 몇 초 전 browser가 캐시했을 수 있다 | TTL이 OS 쪽에 남아 있을 수 있다 | 지금 이 순간의 해당 resolver answer |

그래서 아래 조합은 모두 가능하다.

- browser는 `alpn="h3"`가 있는 `HTTPS` RR을 봤다
- OS는 아직 예전 answer를 캐시하고 있다
- `dig @1.1.1.1`는 public resolver 기준의 다른 answer를 보여 준다

이건 "`누가 틀렸다`"보다 "`관측 지점이 다르다`"에 가깝다.

## 가장 흔한 4가지 원인

### 1. resolver가 다르다

가장 흔한 이유다.

- browser Secure DNS는 public DoH를 쓴다
- OS는 회사 DNS를 쓴다
- `dig`는 내가 `@8.8.8.8`을 붙여 public resolver에 직접 묻는다

이 경우 같은 이름이어도 답이 달라질 수 있다.

- 회사 DNS는 internal view를 준다
- public DoH는 external view를 준다
- 특정 resolver는 `HTTPS` RR을 다르게 정규화하거나 더 최신 zone을 보고 있을 수 있다

### 2. cache 시점이 다르다

`HTTPS` RR도 TTL과 cache 영향을 받는다.

- browser는 조금 전 answer를 들고 있을 수 있다
- OS stub cache는 다른 만료 시점을 가질 수 있다
- `dig`는 비교적 지금 시점의 answer를 새로 가져오기 쉽다

즉 "`방금 `dig`는 바뀌었는데 browser는 안 바뀐다`"는 장면은 cache 차이로 자주 생긴다.

### 3. split-horizon 또는 VPN view가 다르다

사내망, VPN, private zone이 있으면 같은 이름이 다른 힌트를 줄 수 있다.

- 사내 resolver는 internal endpoint용 `HTTPS` RR을 준다
- public resolver는 외부 edge용 `HTTPS` RR을 준다
- browser DoH가 외부 public resolver로 나가면 내부 view를 못 볼 수 있다

그래서 enterprise 환경에서는 "`browser는 외부를 보고, 앱은 내부를 본다`" 같은 드리프트가 생긴다.

### 4. 비교 대상이 사실 다르다

초급자가 의외로 자주 놓치는 부분이다.

- browser는 `www.example.com`을 봤다
- terminal에서는 `example.com`을 조회했다
- browser는 재시도 중 다른 origin이나 alt-authority를 따라갔다

host가 한 글자라도 다르면 `HTTPS` RR/SVCB는 완전히 다른 레코드일 수 있다.

## 짧은 예시: browser는 `h3`, `dig HTTPS`는 비어 있는 경우

이 장면을 바로 "`browser가 거짓말한다`"로 읽으면 안 된다.

먼저 가능한 해석은 이렇다.

| 관찰 | 바로 내릴 초급 결론 |
|---|---|
| browser는 `h3`로 붙는다 | browser는 어딘가에서 H3 discovery 힌트를 얻었다 |
| terminal `dig HTTPS example.com`은 비어 있다 | **내가 방금 본 resolver**는 그 host에 `HTTPS` RR 힌트를 주지 않았다 |
| 둘이 다르다 | browser와 `dig`가 같은 resolver path를 본다고 아직 증명되지 않았다 |

이때 흔한 실제 원인은 두 가지다.

- browser는 DoH 또는 이전 cache로 HTTPS RR/SVCB 힌트를 봤다
- `dig`는 system resolver 또는 다른 public resolver를 보고 있다

추가로 이 경우에는 DNS HTTPS RR이 아니라 `Alt-Svc`로 H3를 배웠을 가능성도 남아 있다.
그래서 "`browser는 `h3`, `dig HTTPS`는 비어 있음`"은 곧바로 DNS 문제 확정이 아니라, **resolver path 비교 단계로 들어가야 한다는 신호**다.

## 30초 체크리스트: 비교를 공정하게 만드는 방법

다음 4개를 맞추면 해석이 훨씬 쉬워진다.

| 체크 | 왜 필요한가 | 초급자 행동 |
|---|---|---|
| 같은 host를 비교했는가 | `www`/apex 차이만으로도 완전히 달라진다 | browser 주소와 `dig` 대상 문자열을 똑같이 맞춘다 |
| 같은 resolver를 비교했는가 | 서로 다른 DNS view를 보고 있을 수 있다 | `dig @resolver host HTTPS`처럼 resolver를 명시한다 |
| cache 시점을 맞췄는가 | stale answer가 섞이면 원인 판단이 흐려진다 | browser repeat visit과 fresh `dig`를 같은 뜻으로 읽지 않는다 |
| browser가 DNS 힌트가 아니라 `Alt-Svc`로 배웠을 가능성을 봤는가 | `h3` 자체가 HTTPS RR의 증거는 아니다 | DevTools에서 response `Alt-Svc`도 같이 확인한다 |

`dig` 쪽은 아래처럼 비교 resolver를 고정하는 습관이 안전하다.

```bash
DOMAIN=www.example.com

dig +noall +answer "$DOMAIN" HTTPS
dig +noall +answer @"8.8.8.8" "$DOMAIN" HTTPS
dig +noall +answer @"1.1.1.1" "$DOMAIN" HTTPS
```

이 3줄은 "`system path와 public resolver가 같은 answer를 주는가`"를 보는 가장 짧은 비교 카드다.

## 자주 헷갈리는 포인트

- "`dig`가 정답이고 browser가 예외다"라고 읽으면 안 된다.
  - `dig`도 결국 **어느 resolver에 물었는지**에 따라 answer가 달라진다.
- browser가 `h3`면 반드시 `HTTPS` RR이 있었다고 단정하면 안 된다.
  - `Alt-Svc`로 배웠을 수도 있다.
- `HTTPS` RR이 다르면 authoritative zone이 깨졌다고 바로 단정하면 안 된다.
  - resolver 차이, cache 차이, split-horizon 차이가 더 흔하다.
- OS에서 안 보이는 answer가 browser에 보인다고 해서 browser가 DNS 규칙을 무시한 것은 아니다.
  - browser가 **다른 resolver path**를 택했을 가능성이 더 높다.

## 다음에 이어서 볼 문서

- browser가 실제로 H3를 어디서 배웠는지 더 직접 추적하려면 [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)
- `Alt-Svc`와 HTTPS RR이 discovery에서 어떻게 역할이 갈리는지 먼저 묶어 보려면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- 사내망/VPN/내부 zone 때문에 답이 갈리는 이유를 더 보려면 [DNS Split-Horizon Behavior](./dns-split-horizon-behavior.md)
- cache와 TTL 시간차 때문에 답이 흔들리는 이유를 더 보려면 [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)

## 한 줄 정리

browser DoH, OS resolver, terminal `dig`가 `HTTPS` RR/SVCB에서 다르게 보일 때는 "`DNS가 틀렸다`"보다 먼저 "`서로 같은 resolver와 같은 cache 시점을 보고 있었는가`"를 확인해야 한다.
