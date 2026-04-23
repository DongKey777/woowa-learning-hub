# Session Pinning vs Version-Gated Strict Reads

> 한 줄 요약: `expectedVersion`이나 watermark gate는 "이 화면의 projection이 충분히 따라왔는가"를 증명하는 규칙이고, session pinning은 "이 사용자의 짧은 strict window 동안 다음 여러 화면이 뒤로 가지 않게 어느 read world에 묶을 것인가"를 정하는 규칙이다. 화면 하나의 freshness 증명보다 cross-screen routing 일관성이 더 중요할 때 session pinning이 더 적합하다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Read Model Staleness and Read-Your-Writes](./read-model-staleness-read-your-writes.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Fallback Capacity and Headroom Contracts](./fallback-capacity-and-headroom-contracts.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Database: Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
> - [Database: Client Consistency Tokens](../database/client-consistency-tokens.md)
> - [Database: Read Snapshot Pinning](../database/read-snapshot-pinning.md)
> - [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)

retrieval-anchor-keywords: session pinning strict read, session pinning vs version gated, expected version strict read, watermark gated strict read, cross screen read your writes, strict screen routing window, actor scoped pinning, pinned read chain, session strict window, consistency token strict screen, projection version gate, projection watermark gate, multi screen strict flow, strict route token

---

## 핵심 개념

많은 팀이 `session pinning`과 `expectedVersion` 또는 watermark gate를 같은 자리의 대안처럼 비교한다.  
하지만 실제로는 서로 다른 질문에 답한다.

| 전략 | 실제로 답하는 질문 | 보통 맞는 범위 |
|---|---|---|
| Session pinning | "이 actor의 짧은 strict window 동안 다음 strict screen들을 어느 read route/snapshot에 묶을 것인가?" | 여러 strict screen, workflow step, list/detail 혼합 경로 |
| `expectedVersion` gate | "이 aggregate/detail projection이 방금 성공한 command version까지 따라왔는가?" | 단건 상세, 단일 aggregate read |
| Watermark gate | "이 projection/shard/list read가 필요한 replay 지점까지 따라왔는가?" | 목록, 검색, 카운트, fan-out read |

즉 `expectedVersion`과 watermark는 **freshness 증거**이고, session pinning은 **routing 기억**이다.

문제는 사용자가 이 둘을 따로 느끼지 않는다는 점이다.  
사용자는 "저장 직후 상세는 맞는데 목록은 옛값"처럼 **화면 간 모순**을 기억한다.

그래서 strict read 설계에서는 먼저 질문을 분리해야 한다.

- 이 화면이 스스로 freshness를 증명할 수 있는가
- 여러 strict screen이 같은 recent-write window를 공유하는가
- 그 window 동안 read route가 바뀌면 사용자가 모순을 느끼는가

### Retrieval Anchors

- `session pinning strict read`
- `session pinning vs version gated`
- `expected version strict read`
- `watermark gated strict read`
- `cross screen read your writes`
- `strict screen routing window`
- `actor scoped pinning`
- `pinned read chain`
- `session strict window`
- `projection version gate`
- `projection watermark gate`

---

## 깊이 들어가기

### 1. 세 전략은 같은 층위의 선택지가 아니다

`expectedVersion`이나 watermark gate는 "이 read model이 충분히 최신인가"를 판정한다.  
반면 session pinning은 "이번 사용자 흐름에서 read path가 뒤로 가지 않게 묶어야 하는가"를 판정한다.

이 차이를 놓치면 흔히 두 가지 실수가 나온다.

- 모든 strict 문제를 session pinning으로 덮어서 primary/old path를 오래 태운다
- 반대로 모든 화면에 version/watermark를 억지로 전파해 cross-screen 흐름을 지나치게 복잡하게 만든다

실전에서는 둘 중 하나를 고르는 게 아니라, **증거 규칙과 라우팅 규칙을 분리**하는 편이 맞다.

### 2. `expectedVersion`이 가장 좋은 기본값은 단건 상세다

다음 조건이면 session pinning보다 `expectedVersion` gate가 먼저다.

- command 응답이 aggregate version을 돌려준다
- read model이 같은 aggregate의 applied version을 갖고 있다
- strict 약속이 사실상 단일 상세 화면에 가깝다
- stale 여부를 actor/session이 아니라 entity 단위로 판단하는 편이 더 정확하다

예를 들어 주문 생성 직후 `order-detail` 화면은 보통 이 방식이 가장 깔끔하다.

- command는 `orderId`, `aggregateVersion`을 반환한다
- detail projection은 `lastAppliedVersion(orderId)`를 노출한다
- `projectionVersion >= expectedVersion`이면 canonical projection으로 읽는다
- 아니면 write query port 또는 pending UX로 내려간다

이 경우 session pinning까지 걸면 보호 범위가 너무 넓어질 수 있다.  
문제는 "이 주문 상세가 최신인가"이지, "세션 전체를 어디에 묶을 것인가"가 아니기 때문이다.

### 3. watermark gate가 더 자연스러운 기본값은 목록, 검색, 카운트다

다음 화면들은 단일 `expectedVersion`으로 설명하기 어렵다.

- `내 주문` 목록 첫 페이지
- 검색 결과
- 집계 카드와 badge count
- 여러 aggregate를 fan-out해서 조합한 read model

여기서는 entity별 version보다 projection/shard watermark가 더 의미 있다.

- 어떤 consumer offset까지 반영됐는가
- 어떤 shard watermark까지 catch-up했는가
- 어떤 snapshot watermark 이후 데이터는 아직 덜 들어왔는가

즉 watermark gate는 "이 read cohort를 canonical path로 보여 줄 수 있는가"를 묻는 규칙이다.  
목록/검색 strict read는 보통 이 질문이 더 맞다.

그래서 session pinning만으로는 부족한 경우가 많다.

- pinned route도 여전히 덜 채워진 projection일 수 있다
- list/search는 page depth와 cursor world까지 같이 맞아야 한다
- count badge는 detail과 다른 projection을 볼 수 있다

이 경우에는 [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)처럼 page-depth와 cursor verdict까지 같이 고정해야 한다.

### 4. session pinning이 더 적합한 순간은 "화면 하나"가 아니라 "짧은 strict window"다

session pinning이 더 좋은 선택이 되는 조건은 다음과 같다.

- 같은 actor가 최근 write 직후 여러 strict screen을 연달아 볼 가능성이 높다
- 그 화면들이 서로 다른 projection, cache, replica, old path를 사용한다
- 화면마다 `expectedVersion`이나 watermark를 따로 증명하게 두면 route가 들쑥날쑥해질 수 있다
- 사용자가 느끼는 약속은 "몇 초 동안은 방금 한 작업이 어디서든 뒤로 가지 않아야 한다"에 가깝다

대표적인 예시는 이런 흐름이다.

- 프로필 수정 -> 설정 상세 -> 헤더 아바타 카드 -> 사용자 검색 shortcut
- 주문 생성 -> 주문 상세 -> 내 주문 page 1 -> confirmation badge
- 상담사가 상태 변경 -> case detail -> queue list -> side summary card

이때 화면별 gate만 따로 두면 이런 모순이 생긴다.

- detail은 write fallback이라 최신
- list는 projection watermark 미달이라 옛값
- badge는 cache hit라 더 옛값

사용자 입장에서는 "일부만 맞고 일부는 틀린 시스템"으로 보인다.  
이럴 때 session pinning은 세션 전체를 무조건 primary에 태우는 기술이 아니라, **strict registry에 포함된 화면들을 짧은 actor-scoped window 동안 같은 read world로 묶는 계약**이다.

### 5. session pinning을 쓰려면 scope와 exit rule이 먼저 있어야 한다

session pinning은 강한 도구라서, 아래 조건이 없으면 쉽게 과해진다.

| 항목 | 꼭 정해야 하는 질문 | 안전한 기본값 |
|---|---|---|
| Actor scope | 누구를 pinning할 것인가 | write를 만든 actor 본인 |
| Screen scope | 어떤 strict screen에만 적용할 것인가 | registry에 등록된 detail/list/badge만 |
| Strict window | 얼마나 오래 유지할 것인가 | 3~10초의 짧은 TTL |
| Pinned route | 어디에 묶을 것인가 | write query port, primary, old projection, pinned snapshot 중 하나 |
| Exit rule | 언제 canonical path로 돌아갈 것인가 | TTL 만료 또는 local gate 통과 |

핵심은 "recent write가 있었다"가 아니라 **"어떤 recent write가 어떤 strict screen 묶음에 대해 얼마 동안 어느 route를 강제하는가"**다.

### 6. 가장 실전적인 조합은 "gate로 풀고, pinning으로 묶는다"다

대부분의 시스템에서 가장 안정적인 패턴은 아래 순서다.

1. 화면이 스스로 freshness를 증명할 수 있으면 `expectedVersion` 또는 watermark gate를 먼저 본다.
2. 그 증거가 아직 부족하지만 actor가 strict window 안에 있으면 session pinning으로 같은 read world를 유지한다.
3. 둘 다 만족하지 못하면 pending UX, retry-after, page1-only fallback 같은 degrade로 내려간다.

이 패턴의 장점은 분명하다.

- local gate가 가능한 화면은 정밀하게 canonical path로 빨리 복귀한다
- cross-screen strict window는 pinning으로 모순을 줄인다
- pinning이 영구 경로가 아니라 "증거가 생길 때까지의 짧은 우산"이 된다

즉 session pinning은 `expectedVersion`/watermark의 경쟁자가 아니라, **여러 strict screen을 한 recent-write window로 묶는 외곽 계약**에 가깝다.

### 7. session pinning이 더 낫다는 신호

다음 체크리스트가 많이 맞으면 session pinning을 우선 검토할 가치가 크다.

- strict 화면이 2개 이상이고, detail/list/badge처럼 projection 종류가 섞여 있다
- 사용자 약속이 "이 화면"보다 "이 여정" 단위로 정의돼 있다
- client나 gateway가 consistency token/session token을 다음 요청에 안정적으로 실을 수 있다
- pinned route의 capacity reserve와 breaker가 이미 문서화돼 있다
- local version/watermark gate가 있더라도 화면마다 결과가 엇갈릴 위험이 크다

반대로 아래면 session pinning보다 local gate가 먼저다.

- strict 화면이 사실상 단건 상세 한 곳뿐이다
- aggregate version을 정확히 비교할 수 있다
- list/search strict가 아니거나, page1-only로 충분하다
- primary/old path reserve가 약하다
- anonymous/global traffic이라 actor-scoped pinning이 어렵다

### 8. 하지 말아야 할 것

- 모든 write 세션을 30초 이상 primary에 묶지 말 것
- 단건 상세 문제를 session pinning으로만 해결하지 말 것
- list/search에 단일 `expectedVersion`을 억지로 끼워 넣지 말 것
- page 1만 pinned route로 읽고 page 2는 다른 cursor world로 조용히 넘기지 말 것
- pinning을 "latest 보장 증거"처럼 설명하지 말 것

session pinning은 어디까지나 **route non-regression**에 가깝다.  
해당 route가 진짜 충분히 최신인지는 local gate나 pending/degrade 규칙이 따로 보완해야 한다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 후 바로 상세만 보는 흐름

- strict scope: `order-detail`
- signal: `aggregateVersion`
- 더 나은 선택: `expectedVersion` gate

이 경우 strict 약속이 거의 한 화면에 닫혀 있다.  
session pinning까지 쓰면 범위만 넓어지고 정밀도는 오히려 떨어질 수 있다.

### 시나리오 2: 프로필 수정 후 여러 자기 화면이 연달아 보이는 흐름

- strict scope: 설정 상세, 헤더 아바타, 요약 카드
- screen마다 projection/cache가 다름
- 더 나은 선택: 짧은 session pinning + 가능하면 각 화면의 local gate

이 흐름은 "사용자 본인이 방금 바꾼 프로필이 당분간 어디서나 뒤로 가지 않아야 한다"가 핵심이다.  
이때는 화면별 freshness 증거보다 cross-screen route 안정성이 더 중요하다.

### 시나리오 3: 거래 완료 후 거래내역 first page와 running balance

- strict scope: actor-owned first page, balance card
- signal: projection watermark
- 더 나은 선택: watermark gate, 필요하면 page1-only fallback

여기서는 단건 version보다 list/balance projection의 catch-up 정도가 중요하다.  
session pinning만으로는 page depth, watermark, badge 동기화를 설명하기 어렵다.

### 시나리오 4: 주문 생성 후 상세와 내 주문 page 1을 모두 엄격히 맞추고 싶은 흐름

- detail은 `expectedVersion`으로 충분
- `my-orders` page 1은 watermark/cursor policy가 필요
- 둘 사이 route 모순을 줄이려면 actor-scoped short session pinning을 outer contract로 둔다

이 조합이 가장 흔하다.  
즉 "detail은 version gate, list는 watermark gate, 둘을 묶는 것은 session pinning"이 실전 default가 되기 쉽다.

---

## 코드로 보기

### strict token

```java
public record StrictReadToken(
    String actorId,
    Instant strictWindowUntil,
    Long expectedVersion,
    String requiredWatermark,
    ReadRoute pinnedRoute
) {
    boolean strictWindowActive(Instant now) {
        return strictWindowUntil != null && now.isBefore(strictWindowUntil);
    }
}
```

### route decision

```java
public final class StrictReadRouter {
    public ReadRoute choose(
        ScreenPolicy screen,
        StrictReadToken token,
        ProjectionStatus status,
        Instant now
    ) {
        if (screen.usesExpectedVersion()
            && token.expectedVersion() != null
            && status.version() >= token.expectedVersion()) {
            return ReadRoute.CANONICAL_PROJECTION;
        }

        if (screen.usesWatermark()
            && token.requiredWatermark() != null
            && status.watermarkAtOrAfter(token.requiredWatermark())) {
            return ReadRoute.CANONICAL_PROJECTION;
        }

        if (screen.strictScreen() && token.strictWindowActive(now)) {
            return token.pinnedRoute();
        }

        return screen.degradedRoute();
    }
}
```

이 코드는 session pinning을 "증거 대신 무조건 우회"가 아니라,  
**local gate가 아직 안 풀린 동안 strict screen들을 같은 route에 묶는 규칙**으로 두는 감각을 보여 준다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 우선하는가 |
|---|---|---|---|
| Session pinning | 여러 strict screen의 체감 일관성을 맞추기 쉽다 | route state, TTL, capacity reserve, breaker가 필요하다 | actor-scoped recent-write window가 핵심일 때 |
| `expectedVersion` gate | 단건 상세에서 가장 정밀하고 싸다 | list/search/count에는 잘 안 맞는다 | aggregate detail strict read |
| Watermark gate | projection/list/fan-out read에 자연스럽다 | coarse하고 watermark 계측이 필요하다 | 목록, 검색, 카운트, badge |
| Pending/degraded UX | correctness를 솔직하게 드러낸다 | UX 설계가 필요하다 | local gate도 pinning도 안전하지 않을 때 |

판단 기준은 다음 순서가 좋다.

- strict 약속이 화면 단위인지, 여정 단위인지 먼저 구분한다
- 단건 상세면 `expectedVersion`부터 검토한다
- 목록/검색/카운트면 watermark gate부터 검토한다
- 여러 strict screen이 한 recent-write window를 공유하면 session pinning을 outer contract로 둔다
- pinning을 열기 전에 capacity reserve와 cursor/session exit rule을 고정한다

---

## 꼬리질문

> Q: session pinning만 있으면 read-your-writes가 해결된 것 아닌가요?
> 의도: route 안정성과 freshness 증거를 구분하는지 본다.
> 핵심: 아니다. pinning은 route non-regression에 가깝고, 그 route가 충분히 최신인지까지 자동으로 증명하지는 않는다.

> Q: 왜 모든 strict screen에 `expectedVersion`을 넘기면 안 되나요?
> 의도: entity-local version과 projection cohort read를 구분하는지 본다.
> 핵심: list/search/count는 단일 aggregate version으로 설명되지 않는 경우가 많고, cross-screen 전파 비용도 커진다.

> Q: session pinning과 strict pagination fallback은 어떤 관계인가요?
> 의도: page 1 strict와 pinned chain을 구분하는지 본다.
> 핵심: page 1 strict를 살릴 때도 page 2 이후 cursor verdict를 따로 정해야 한다. pinning이 있다고 해서 pagination continuity가 자동 보장되지는 않는다.

## 한 줄 정리

단건 strict read는 `expectedVersion`이나 watermark gate가 먼저고, 여러 strict screen이 같은 recent-write window를 공유해 route가 엇갈리면 session pinning을 outer contract로 두는 편이 더 안전하다.
