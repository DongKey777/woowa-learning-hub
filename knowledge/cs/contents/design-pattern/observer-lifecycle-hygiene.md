---
schema_version: 3
title: Observer Lifecycle Hygiene
concept_id: design-pattern/observer-lifecycle-hygiene
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- observer-lifecycle
- unsubscribe-contract
- duplicate-listener-guard
aliases:
- observer lifecycle hygiene
- unsubscribe pattern
- duplicate listener registration
- listener cleanup
- event listener leak
- UI listener lifecycle
- plugin listener lifecycle
- long lived process observer leak
- event emitter cleanup
- register once unsubscribe always
symptoms:
- 화면 remount, plugin re-enable, reconnect 이후 같은 이벤트가 두 번씩 처리되어 중복 요청이나 중복 알림이 발생한다
- subscribe API는 있는데 unsubscribe handle이나 owner lifecycle이 없어 stale listener가 오래 살아남는다
- 중복 등록 방지를 호출자 습관에 맡겨 retry, reload, reconnect 경로에서 listener가 계속 누적된다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/observer
- design-pattern/observer-pubsub-application-events
- design-pattern/mediator-vs-observer-vs-pubsub
next_docs:
- design-pattern/plugin-architecture-pattern-language
- design-pattern/spring-eventlistener-vs-transactionaleventlistener-timing
- software-engineering/cache-message-observability
linked_paths:
- contents/design-pattern/observer.md
- contents/design-pattern/observer-pubsub-application-events.md
- contents/design-pattern/mediator-vs-observer-vs-pubsub.md
- contents/design-pattern/plugin-architecture-pattern-language.md
- contents/design-pattern/spring-eventlistener-vs-transactionaleventlistener-timing.md
- contents/software-engineering/cache-message-observability.md
confusable_with:
- design-pattern/observer
- design-pattern/observer-pubsub-application-events
- design-pattern/plugin-architecture-pattern-language
- design-pattern/mediator-vs-observer-vs-pubsub
forbidden_neighbors: []
expected_queries:
- Observer에서 unsubscribe를 빼먹으면 왜 메모리 누수보다 중복 실행이 먼저 보일 수 있어?
- UI remount나 plugin re-enable 때 duplicate listener registration을 막으려면 API가 어떤 계약을 가져야 해?
- subscribe가 Disposable이나 unsubscribe handle을 반환해야 하는 이유가 뭐야?
- listener lifecycle을 owner lifecycle과 맞추지 않으면 stale closure와 hidden side effect가 생기는 이유가 뭐야?
- long lived process에서 active listener count와 teardown test를 왜 운영 지표로 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Observer Lifecycle Hygiene playbook으로, UI, plugin, daemon, long-lived
  session에서 observer listener가 중복 등록되거나 해제되지 않아 duplicate effect, stale closure,
  memory leak가 생기는 문제를 unsubscribe handle, owner-scoped registry, duplicate guard,
  deterministic teardown으로 막는 방법을 설명한다.
---
# Observer Lifecycle Hygiene

> 한 줄 요약: 옵저버는 등록보다 해제가 어렵다. UI, plugin, long-lived process에서는 `unsubscribe`, 중복 등록 방지, listener 소유권을 코드 계약으로 고정해야 누수와 중복 실행을 막을 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Observer(옵저버) 디자인 패턴](./observer.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Mediator vs Observer vs Pub/Sub](./mediator-vs-observer-vs-pubsub.md)
> - [Plugin Architecture: 기능을 꽂아 넣는 패턴 언어](./plugin-architecture-pattern-language.md)
> - [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](./spring-eventlistener-vs-transactionaleventlistener-timing.md)

retrieval-anchor-keywords: observer lifecycle hygiene, unsubscribe pattern, duplicate listener registration, listener cleanup, event listener leak, UI listener lifecycle, plugin listener lifecycle, long-lived process observer leak, event emitter cleanup, register once unsubscribe always, stale listener closure, disable unload teardown

---

## 이 문서는 언제 읽으면 좋은가

- 화면을 다시 열거나 plugin을 다시 enable할 때 같은 이벤트가 두 번씩 처리될 때
- WebSocket session, worker, daemon, IDE plugin처럼 프로세스가 오래 살아 listener가 누적될 수 있을 때
- 옵저버는 느슨한 결합이라 안전하다고 생각했는데 메모리 누수와 hidden side effect가 먼저 보일 때

## 핵심 개념

옵저버 패턴에서 실전 난이도는 "알림 구조"보다 "수명주기 소유권"에서 나온다.

- 누가 subscribe 하는가
- 언제 unsubscribe 하는가
- 같은 owner가 같은 listener를 두 번 붙이지 않게 어디서 막는가
- host가 내려갈 때 stale listener를 누가 정리하는가

짧게 말하면:

**subscribe는 생성/활성화 경계에서, unsubscribe는 종료/비활성화 경계에서, duplicate guard는 registration API 자체에서 강제해야 한다.**

이 규칙은 단순 코드 스타일이 아니라 운영 안전장치다. listener가 남아 있으면 메모리보다 먼저 중복 실행, 오래된 session context, 닫힌 화면 state 접근 같은 기능 이상으로 드러난다.

## 왜 UI, plugin, long-lived process에서 더 위험한가

짧게 살아나는 request-scope 객체라면 프로세스 종료와 함께 listener도 사라진다.  
하지만 아래 구조는 다르다.

- SPA 화면 shell
- plugin host
- 장시간 유지되는 세션 매니저
- 설정 reload가 가능한 worker / daemon

이런 구조에서는 registration path가 여러 번 실행되는데 host 자체는 계속 살아 있다.  
그래서 문제가 쌓인다.

- 예전 listener가 이전 state/closure를 계속 붙잡는다
- enable, remount, reconnect마다 listener가 하나씩 더 늘어난다
- 사용자는 "한 번 눌렀는데 두 번 실행된다"로 체감한다
- 운영자는 나중에 heap growth와 오래된 참조로 문제를 본다

## 1. `unsubscribe`는 옵션이 아니라 대칭 계약이다

옵저버 API가 `subscribe()`만 있고 해제 경로가 흐릿하면 거의 항상 누수가 난다.

- 등록 API는 가능하면 `Disposable`, `Subscription`, `unsubscribe()` 같은 해제 handle을 반환해야 한다
- 등록 시점과 해제 시점을 같은 owner가 들고 있어야 한다
- 익명 함수를 즉석에서 등록하고 나중에 다른 참조로 `off()`를 부르면 해제가 실패한다

나쁜 예:

```ts
class CheckoutPanel {
  mount() {
    bus.on("couponChanged", () => this.recalculate());
  }

  unmount() {
    // 해제할 참조가 없다
  }
}
```

좋은 예:

```ts
class CheckoutPanel {
  private unsubscribe?: () => void;

  mount() {
    this.unsubscribe = bus.subscribe("couponChanged", () => {
      this.recalculate();
    });
  }

  unmount() {
    this.unsubscribe?.();
    this.unsubscribe = undefined;
  }
}
```

핵심은 "listener를 등록했다"가 아니라 "owner가 나갈 때 반드시 정리된다"다.

## 2. 중복 등록 방지는 호출자 습관이 아니라 API 책임이다

`if (!alreadyRegistered)` 같은 호출자 측 규칙에만 기대면 결국 한 군데서 빠진다.  
중복 등록 방지는 host나 registry 레이어에서 강제하는 편이 안전하다.

실전 규칙:

- owner ID와 event key를 기준으로 `Set` / `Map`을 둔다
- 이미 등록된 owner면 no-op 하거나 기존 subscription을 먼저 dispose한다
- `render()`, `retry loop`, `reconnect handler` 안에서 무심코 다시 등록하지 않는다
- plugin 재활성화는 새 등록 전에 이전 등록을 해제하는 흐름으로 고정한다

예:

```ts
class PluginHost {
  private subscriptions = new Map<string, () => void>();

  enable(plugin: EditorPlugin) {
    if (this.subscriptions.has(plugin.id)) {
      return;
    }

    const unsubscribe = bus.subscribe("documentSaved", (event) => {
      plugin.onDocumentSaved(event);
    });

    this.subscriptions.set(plugin.id, unsubscribe);
  }

  disable(pluginId: string) {
    this.subscriptions.get(pluginId)?.();
    this.subscriptions.delete(pluginId);
  }
}
```

이 구조의 의미는 "조심해서 한 번만 등록하자"가 아니라,  
**한 번만 등록되는 구조를 host가 보장한다**는 데 있다.

## 3. listener 수명은 owner 수명과 같이 가야 한다

옵저버를 글로벌 emitter에 붙이면 편해 보이지만, 실제로는 owner lifecycle과 분리되기 쉽다.  
수명이 어긋나면 stale callback과 메모리 누수가 동시에 생긴다.

| 맥락 | 등록 시점 | 해제 시점 | 흔한 실수 |
|---|---|---|---|
| UI component | mount / effect start | unmount / cleanup | render마다 재등록 |
| plugin | enable / load | disable / unload | disable 경로가 비어 있음 |
| WebSocket session | connect | close / error / timeout | 끊긴 세션 listener가 남음 |
| worker / daemon | start / boot | shutdown / reload | reload 때 기존 listener를 안 걷음 |

기준은 단순하다.

- component가 소유하면 component lifecycle에 묶는다
- plugin이 소유하면 enable/disable에 묶는다
- session이 소유하면 connect/disconnect에 묶는다
- process singleton이 소유하면 shutdown/reconfigure에 묶는다

owner를 명시하지 못하면 나중에 누가 정리해야 하는지 항상 흐려진다.

## 4. "메모리 누수"보다 먼저 나타나는 신호를 읽어야 한다

listener leak는 heap dump 전에 기능 이상으로 먼저 보인다.

- 클릭 한 번에 같은 요청이 여러 번 나간다
- 토스트, 알림, 로그가 중복 출력된다
- 이미 닫힌 화면의 state를 만지는 callback 예외가 난다
- reconnect 후 예전 session context로 처리되는 로그가 남는다

즉 "duplicate effect"는 대개 lifecycle bug의 첫 증상이다.  
문제를 기능 버그로만 보지 말고 registration path를 같이 봐야 한다.

## 5. weak reference나 GC에 기대면 늦다

가끔 "어차피 owner가 GC되면 괜찮지 않나?"라고 생각하기 쉽다.  
하지만 observer cleanup을 GC에 맡기면 안 된다.

- 해제 시점이 비결정적이다
- 중복 등록 자체는 막지 못한다
- stale listener가 살아 있는 동안은 잘못된 동작이 계속된다

weak reference는 보조 안전장치일 수는 있어도, deterministic teardown을 대신하지 못한다.

## 6. 테스트와 운영에서 확인해야 할 것

수명주기 위생은 문서로만 유지되지 않는다. 테스트와 계측이 필요하다.

- mount -> unmount -> remount 뒤에도 이벤트가 한 번만 처리되는지 테스트한다
- plugin enable -> disable -> enable 시 active subscription 수가 1로 유지되는지 확인한다
- reconnect / reload 시 이전 owner의 cleanup이 호출됐는지 로그나 metric으로 본다
- 가능하면 event별 active listener count를 노출한다

짧은 체크리스트:

- 등록 함수가 해제 handle을 반환하는가
- 해제 경로가 성공/실패/timeout까지 포함하는가
- owner key 없이 무명 listener만 쌓이고 있지 않은가
- 중복 등록이 호출자 규칙이 아니라 host 계약으로 막히는가

## 흔한 smell

| smell | 왜 문제인가 | 더 안전한 방향 |
|---|---|---|
| `subscribe()`만 있고 `unsubscribe()`가 없다 | 해제 책임이 사라진다 | disposable handle 반환 |
| 익명 함수 등록 후 다른 참조로 해제 시도 | 실제 해제가 안 된다 | 동일 참조 또는 returned handle 사용 |
| `render()` / `onResume()` / `retry()` 안에서 재등록 | 호출 횟수만큼 중복된다 | lifecycle hook 한 군데로 고정 |
| plugin `enable()`은 있는데 `disable()`이 비어 있다 | 장시간 누적된다 | enable/disable 대칭 보장 |
| global emitter가 component/service를 오래 잡고 있다 | stale state와 메모리 누수 동시 발생 | owner-scoped subscription registry |

## 어디까지가 Observer이고, 언제 다른 구조를 보나

이 문서는 observer 자체를 버리라는 뜻이 아니다.  
오히려 옵저버를 계속 쓸 거라면 lifecycle hygiene를 설계에 포함하라는 뜻이다.

- 같은 프로세스 안에서 상태 변화 fan-out이 필요하면 observer는 여전히 유용하다
- 순서, 실패 격리, 재시도, durable delivery가 중요해지면 Pub/Sub나 queue 경계를 다시 본다
- 객체 간 상호작용 자체를 중앙에서 조율해야 하면 Mediator가 더 맞을 수 있다

즉 lifecycle hygiene는 observer를 대체하는 패턴이 아니라,  
**observer를 오래 살아있는 시스템에 안전하게 쓰기 위한 운영 규칙**이다.

## 꼬리질문

> Q: `unsubscribe`를 빼먹으면 왜 "메모리"보다 "중복 실행"이 먼저 보이나요?
> 의도: leak의 초기 증상을 lifecycle 관점에서 읽는지 확인한다.
> 핵심: stale listener가 살아 있는 동안 이벤트 fan-out 수가 먼저 증가한다.

> Q: 중복 등록 방지를 호출자에게 맡기면 왜 금방 깨지나요?
> 의도: discipline과 contract를 구분하는지 확인한다.
> 핵심: remount, reconnect, retry 같은 재진입 경로가 늘수록 한 군데 예외가 생긴다.

> Q: plugin host에서 listener를 plugin 내부가 아니라 host registry가 관리해야 하는 이유는 무엇인가요?
> 의도: ownership boundary를 이해하는지 확인한다.
> 핵심: enable/disable 수명주기를 host가 알고 있으므로 cleanup을 가장 확실하게 강제할 수 있다.

## 한 줄 정리

옵저버는 느슨한 결합만으로 안전해지지 않는다. 오래 살아 있는 시스템에서는 `unsubscribe`, 중복 등록 방지, owner-aligned teardown까지 포함한 lifecycle 계약이 있어야 안전하다.
