# Protocol Version Skew / Compatibility 설계

> 한 줄 요약: protocol version skew와 compatibility 설계는 old/new producer, consumer, client, server가 동시에 존재하는 기간에도 요청과 이벤트가 안전하게 해석되도록 버전 호환 규칙과 deprecation 경계를 운영하는 설계다.

retrieval-anchor-keywords: protocol version skew, compatibility, mixed version fleet, client server skew, event schema compatibility, backward compatible protocol, forward compatible protocol, deprecation window, unknown field handling, version negotiation, capability negotiation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Mesh Control Plane 설계](./service-mesh-control-plane-design.md)
> - [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
> - [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Config Rollback Safety 설계](./config-rollback-safety-design.md)
> - [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)

## 핵심 개념

배포 중에는 세상이 한 버전으로 통일되어 있지 않다.

- old client / new server
- new client / old server
- old producer / new consumer
- new producer / old consumer

이 기간을 version skew라고 본다.
좋은 시스템은 skew를 없애려 하지 않고 **skew를 견딜 수 있는 compatibility envelope를 설계**한다.

## 깊이 들어가기

### 1. 왜 skew가 생기는가

대표 원인:

- 점진 배포
- mobile / edge client 지연 업그레이드
- async consumer 장기 생존
- replay / backfill 중 과거 payload 재처리
- partial rollback

즉, mixed-version window는 예외가 아니라 정상 상태에 가깝다.

### 2. Capacity Estimation

예:

- 서버 배포 30분
- mobile client upgrade 반영 수일
- consumer mixed-version 기간 수시간
- event retention 수주

이때 봐야 할 숫자:

- oldest supported version
- skew window length
- incompatible request ratio
- unknown field parse failure
- deprecation lag

protocol compatibility는 QPS보다 "얼마나 오래 구버전을 떠안아야 하는가"가 더 중요하다.

### 3. Compatibility 규칙

대표 규칙:

- unknown field ignore
- additive field only
- enum extension safe handling
- required field 도입 시 default / fallback 제공
- semantic meaning 변경 금지

즉, field 추가보다 field 의미 변경이 더 위험할 때가 많다.

### 4. API protocol vs event protocol

둘은 비슷해 보이지만 다르다.

- API protocol: request/response 협상과 status semantics가 중요
- event protocol: long retention과 replay가 있어 과거 payload 호환이 중요

이벤트는 retention 동안 과거 버전을 계속 읽을 수 있어야 하므로 deprecation 창이 더 길어지는 경우가 많다.

### 5. Version negotiation and envelope

선택지:

- explicit version header
- content-type / schema version
- route versioning
- feature capability bit

핵심은 버전 숫자보다도 "상대가 어떤 기능을 이해하는지"를 명확히 아는 것이다.

### 6. Deprecation과 point-of-removal

호환성을 영원히 유지할 수는 없다.
그래서 다음을 정해야 한다.

- deprecation announce 시점
- new use 금지 시점
- old traffic 임계치
- replay / archive 영향
- removal point

특히 이벤트 프로토콜은 "현재 live traffic이 없음"만으로 지워선 안 된다.

### 7. Observability

운영자는 다음을 봐야 한다.

- 버전별 traffic 비율
- skew window가 얼마나 남았는가
- parse fallback 발생률
- deprecated version 아직 사용 중인 caller
- rollback 시 어떤 skew 조합이 생기는가

이 데이터가 있어야 deprecation도 안전하게 할 수 있다.

## 실전 시나리오

### 시나리오 1: mobile client와 server API 진화

문제:

- 오래된 앱 버전이 며칠간 남아 있다

해결:

- additive response field만 먼저 도입한다
- required semantic 변경은 capability gating으로 감싼다
- old client traffic이 충분히 줄어든 뒤 제거한다

### 시나리오 2: event schema field 추가

문제:

- producer가 새 필드를 보내지만 일부 consumer는 아직 old version이다

해결:

- unknown field ignore를 기본으로 한다
- semantic default를 둔다
- replay consumer까지 포함해 compatibility를 검증한다

### 시나리오 3: protocol rollback

문제:

- 새 binary를 되돌렸는데 새 protocol payload가 이미 일부 발생했다

해결:

- old binary가 new field를 무시 가능한지 확인한다
- 불가능하면 full rollback 대신 forward-fix 또는 protocol adapter를 둔다
- removal cleanup 전까지만 true rollback을 허용한다

## 코드로 보기

```pseudo
function handleRequest(req):
  version = negotiator.resolve(req)
  if !compatibility.supports(version):
    return error("unsupported_version")
  normalized = adapter.normalize(req, version)
  return handler.process(normalized)

function consume(event):
  schema = registry.lookup(event.version)
  decoded = decoder.decodeIgnoringUnknown(event, schema)
  process(decoded)
```

```java
public DecodedEvent decode(EventPayload payload) {
    return decoder.decode(payload, CompatibilityMode.IGNORE_UNKNOWN_FIELDS);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Strict single-version | 단순하다 | 점진 배포와 rollback이 어렵다 | 내부 low-latency control path |
| Additive compatibility | 안전하다 | schema discipline이 필요하다 | 대부분의 API/event protocol |
| Long deprecation window | 안전한 제거가 쉽다 | 운영 부담이 남는다 | mobile / retained events |
| Fast removal | 복잡도가 줄어든다 | skew incident risk가 크다 | internal short-lived protocol |

핵심은 protocol version skew 설계가 버전 번호 논의가 아니라 **mixed-version 기간을 정상 상태로 보고 그 안에서 안전하게 해석되는 규칙을 설계하는 것**이라는 점이다.

## 꼬리질문

> Q: additive field면 항상 안전한가요?
> 의도: syntactic vs semantic compatibility 구분 확인
> 핵심: 구문상 추가는 안전할 수 있어도 의미 변경이나 required behavior 변화는 여전히 위험하다.

> Q: live traffic에 old version이 없으면 protocol 제거해도 되나요?
> 의도: replay / retained payload 고려 확인
> 핵심: 이벤트나 archive, delayed consumer가 남아 있으면 아직 제거하면 안 될 수 있다.

> Q: version header만 있으면 해결되나요?
> 의도: negotiation의 한계 이해 확인
> 핵심: 헤더는 식별 수단일 뿐이고, 실제 안전성은 unknown field 처리, default semantics, deprecation policy에 달려 있다.

> Q: rollback 때 protocol skew가 왜 더 심해지나요?
> 의도: partial rollback 사고방식 확인
> 핵심: 일부는 new payload를 이미 만들었는데 처리자는 old binary로 돌아가면 지원 조합이 더 복잡해지기 때문이다.

## 한 줄 정리

Protocol version skew / compatibility 설계는 old/new producer, consumer, client, server가 동시에 존재하는 기간을 전제로, mixed-version 해석 규칙과 deprecation 경계를 명시하는 운영 설계다.
