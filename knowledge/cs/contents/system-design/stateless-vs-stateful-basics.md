# Stateless vs Stateful 서비스 기초

> 한 줄 요약: Stateless 서비스는 요청마다 상태를 외부에서 받아 처리하고, Stateful 서비스는 서버 내부에 상태를 저장하며 수평 확장이 어렵다.

**난이도: 🟢 Beginner**

관련 문서:

- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Horizontal vs Vertical Scaling Basics](./horizontal-vs-vertical-scaling-basics.md)
- [HTTP/HTTPS 기초](../network/http-https-basics.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: stateless stateful basics, stateless 서비스 입문, stateful 뭐예요, 세션 서버 상태, jwt stateless, 서버 상태 저장, stateless api 기초, 서버 확장 상태 관리, beginner stateless, 외부 세션 저장, 무상태 서비스, stateless rest api

---

## 핵심 개념

Stateless와 Stateful은 서버가 요청 사이에 상태를 저장하는지 여부를 가리킨다.

- **Stateless**: 서버는 이전 요청에 대한 정보를 기억하지 않는다. 클라이언트가 요청마다 필요한 정보를 모두 포함해서 보낸다.
- **Stateful**: 서버가 클라이언트의 상태를 기억한다. 세션, 연결 상태 등이 서버에 남아있다.

입문자가 자주 헷갈리는 지점은 **왜 현대 웹 서비스가 Stateless를 선호하는가**이다.

서버가 상태를 저장하면 해당 서버에 연결된 클라이언트는 항상 같은 서버로 가야 한다. 서버를 추가하거나 재시작하면 상태가 사라진다.

---

## 한눈에 보기

```text
Stateful
  클라이언트 -> 서버 A (세션 저장됨)
  재시작 후 -> 서버 A (세션 사라짐 -> 로그인 필요)

Stateless
  클라이언트 -> 서버 A (토큰 포함)
  재시작 후 -> 서버 B (토큰 포함) -> 정상 처리
```

비교:

| 기준 | Stateless | Stateful |
|---|---|---|
| 상태 저장 위치 | 클라이언트 또는 외부 저장소 | 서버 내부 |
| 수평 확장 | 쉬움 | 어려움 |
| 서버 재시작 영향 | 없음 | 상태 유실 |
| 예시 | REST API + JWT | WebSocket 세션, TCP 연결 |

---

## 상세 분해

- **HTTP의 무상태성**: HTTP 자체는 Stateless 프로토콜이다. 각 요청은 독립적이고 서버는 이전 요청을 기억하지 않는다. 로그인 상태를 유지하려면 쿠키/세션 또는 토큰을 추가로 써야 한다.
- **세션 기반 인증 (Stateful)**: 서버 메모리에 세션 ID와 사용자 정보를 저장한다. 클라이언트는 세션 ID만 쿠키로 갖는다. 서버를 여러 대 쓰면 세션이 있는 서버로만 요청이 가야 한다(Sticky Session).
- **토큰 기반 인증 (Stateless)**: 사용자 정보를 JWT 같은 토큰에 담아 클라이언트가 보관한다. 서버는 토큰을 검증만 하고 저장하지 않는다. 어느 서버로 요청이 가도 동작한다.
- **Stateful이 필요한 경우**: WebSocket 연결, 실시간 게임 서버, 주문 상태 머신처럼 연결 중에 상태가 이어져야 하는 경우다.

---

## 흔한 오해와 함정

- **"Stateless면 로그인 상태를 유지할 수 없다"**: JWT 같은 토큰을 클라이언트가 들고 다니면 서버는 상태 없이도 인증된 사용자를 처리할 수 있다. 서버가 아닌 클라이언트가 상태를 갖는 것이다.
- **"Stateless REST API는 아무 데이터도 저장하지 않는다"**: Stateless는 요청 간 서버 내부 상태를 저장하지 않는다는 의미다. DB에 데이터를 쓰는 것은 Stateless와 무관하다.
- **"토큰이 있으면 로그아웃이 불가능하다"**: 단기 유효 토큰(Access Token)과 토큰 블랙리스트 또는 Refresh Token 회전 방식으로 로그아웃을 구현할 수 있다. 토큰 기반 인증도 세션 종료가 가능하다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 REST API 서버를 수평 확장하는 경우다.

1. 서버가 2대에서 5대로 늘어난다.
2. 세션 기반이면 기존 사용자의 세션은 서버 1, 2에만 있다. 서버 3, 4, 5로 요청이 가면 로그인이 필요하다.
3. 토큰 기반(JWT)이면 어느 서버에서도 토큰을 검증해 사용자를 인식한다. 확장이 투명하게 동작한다.

만약 세션을 꼭 서버 측에 저장해야 한다면 Redis 같은 외부 세션 저장소를 써서 모든 서버가 같은 세션을 보도록 만들면 Stateless처럼 확장할 수 있다.

---

## 더 깊이 가려면

- [Stateless Sessions Primer](./stateless-sessions-primer.md) — 토큰 기반 세션의 수명 주기, 외부 세션 저장소 구성 실무
- [Horizontal vs Vertical Scaling Basics](./horizontal-vs-vertical-scaling-basics.md) — Stateless가 왜 수평 확장의 전제 조건인지

---

## 면접/시니어 질문 미리보기

> Q: Stateless 서비스와 Stateful 서비스의 차이를 설명해 주세요.
> 의도: 기본 개념 구분 능력 확인
> 핵심: Stateless는 서버가 요청 간 상태를 기억하지 않아 어느 서버에서도 처리 가능하고 수평 확장이 쉽다. Stateful은 서버 내부에 상태가 있어 같은 서버로만 요청이 가야 한다.

> Q: JWT를 쓰면 왜 Stateless가 되는 건가요?
> 의도: 토큰 기반 인증이 서버 상태를 없애는 원리 이해 확인
> 핵심: 사용자 정보가 토큰 안에 담겨 클라이언트가 보관하고, 서버는 서명 검증만 한다. 서버에 세션 데이터를 저장하지 않아 서버를 여러 대 써도 동일하게 동작한다.

> Q: 세션 기반 서버를 수평 확장하려면 어떻게 해야 하나요?
> 의도: Stateful 서버를 Stateless처럼 확장하는 방법 인지 확인
> 핵심: Redis 같은 외부 세션 저장소를 두고 모든 서버가 같은 세션 저장소를 바라보게 하면, 어느 서버로 요청이 가도 동일한 세션을 찾을 수 있다.

---

## 한 줄 정리

Stateless 서비스는 서버 내부에 상태를 두지 않아 수평 확장이 자유롭고, Stateful은 확장이 어렵지만 실시간 연결처럼 상태가 연속성을 가져야 할 때 쓴다.
