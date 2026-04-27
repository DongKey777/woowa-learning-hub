# Primer Scope Manifest: beginner primer와 bridge/checklist를 이름 대신 분류로 가르기

> 한 줄 요약: beginner 문서가 많아지면 파일명만 보고 primer를 찾기 어렵다. 그래서 lint가 "진짜 첫 진입 primer"만 정확히 집을 수 있도록, 이 manifest에서 문서 역할을 명시적으로 고정한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [Beginner Primer 작성 템플릿: 30초 비교표 + 1분 예시 박스 스켈레톤](./beginner-primer-template.md)
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> - [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: primer scope manifest, beginner primer manifest, primer vs bridge vs checklist, beginner lint manifest, primer scope marker, true beginner primer list, beginner entrypoint manifest, design pattern primer manifest, first read primer manifest, primer scope taxonomy, beginner primer lint, filename heuristic replacement, primer classification manifest, 초보자 프라이머 매니페스트, primer scope 구분

---

## 먼저 잡을 멘탈 모델

문서가 beginner라고 해서 모두 같은 역할은 아니다.
처음 읽는 사람 기준으로는 보통 아래 셋이 섞여 보인다.

| 문서 종류 | 가장 짧은 멘탈 모델 | lint에서 어떻게 다뤄야 하나 |
|---|---|---|
| `true-beginner-primer` | 처음 들어오는 정문 | primer 앵커 검사 대상 |
| `beginner-bridge` | 두 갈래 길에서 방향을 잡는 연결판 | primer 앵커 강제 대상 아님 |
| `beginner-checklist` | 코드 리뷰나 빠른 판별용 체크 카드 | primer 앵커 강제 대상 아님 |

핵심은 단순하다.

**첫 독해 리듬을 제공하는 문서만 primer로 잡고, 비교/라우팅/체크용 문서는 따로 뺀다.**

## 왜 파일명 휴리스틱만으로는 부족한가

파일명에 `beginner`, `primer`, `basics`, `checklist`가 들어가도 실제 역할은 다를 수 있다.

- `*-basics.md`라도 첫 진입 primer일 수 있다.
- `*-beginner.md`라도 질문 라우터나 bridge일 수 있다.
- `*checklist.md`는 beginner 친화적이어도 primer shape를 강제하면 오히려 부자연스럽다.

예를 들어 아래 둘은 둘 다 beginner 문서지만 역할이 다르다.

| 문서 | 실제 역할 | primer 앵커 강제 여부 |
|---|---|---|
| [전략 패턴 기초](./strategy-pattern-basics.md) | 처음 배우는 사람이 큰 그림과 예시를 잡는 primer | 강제 |
| [Factory Misnaming Checklist](./factory-misnaming-checklist.md) | 리뷰에서 빠르게 가르는 checklist | 비강제 |

그래서 lint는 이름이 아니라 **명시적 분류표**를 봐야 한다.

## lint가 읽을 분류 계약

아래 manifest block을 우선 기준으로 쓴다.
새 beginner 문서를 추가할 때도 먼저 이 표에 넣으면, lint가 filename heuristic 없이 분류할 수 있다.

## lint가 읽을 분류 계약 (계속 2)

```yaml
primer-scope-manifest:
  version: 1
  doc_classes:
    true-beginner-primer: "첫 진입용 primer. 10초 질문, 30초 비교표, Quick-Check, 1분 예시 같은 primer 리듬을 기대한다."
    beginner-entrypoint-router: "질문을 받아 다음 primer나 bridge로 보내는 entrypoint. primer처럼 보일 수 있지만 full primer 앵커를 강제하지 않는다."
    beginner-bridge: "가까운 개념 둘 이상을 비교하거나 학습 단계를 연결하는 문서."
    beginner-checklist: "리뷰/점검/빠른 판별용 문서."
    support-template: "template, manifest, QA 가이드처럼 분류 기준을 설명하는 지원 문서."
  lint_policy:
    primer_anchor_lint_targets:
      - true-beginner-primer
    excluded_from_primer_anchor_lint:
      - beginner-entrypoint-router
      - beginner-bridge
      - beginner-checklist
      - support-template
  files:
    object-oriented-design-pattern-basics.md: true-beginner-primer
    adapter-basics.md: true-beginner-primer
    composition-over-inheritance-basics.md: true-beginner-primer
    strategy-pattern-basics.md: true-beginner-primer
    factory-basics.md: true-beginner-primer
    builder-pattern-basics.md: true-beginner-primer
    observer-basics.md: true-beginner-primer
    template-method-basics.md: true-beginner-primer
    command-pattern-basics.md: true-beginner-primer
    decorator-proxy-basics.md: true-beginner-primer
    singleton-basics.md: true-beginner-primer
    factory-selector-resolver-beginner-entrypoint.md: beginner-entrypoint-router
    template-method-query-router-beginner.md: beginner-entrypoint-router
    policy-object-vs-strategy-map-beginner-bridge.md: beginner-bridge

## lint가 읽을 분류 계약 (계속 3)

observer-vs-command-beginner-bridge.md: beginner-bridge
    abstract-class-vs-interface-injection-bridge.md: beginner-bridge
    request-object-creation-vs-di-container.md: beginner-bridge
    request-scope-vs-plain-request-objects.md: beginner-bridge
    record-vs-builder-request-model-chooser.md: beginner-bridge
    strategy-map-vs-registry-primer.md: beginner-bridge
    strategy-policy-selector-naming.md: beginner-bridge
    policy-object-naming-primer.md: beginner-bridge
    registry-primer-lookup-table-resolver-router-service-locator.md: beginner-entrypoint-router
    factory-misnaming-checklist.md: beginner-checklist
    injected-registry-vs-service-locator-checklist.md: beginner-checklist
    map-backed-selector-resolver-registry-factory-naming-checklist.md: beginner-checklist
    beginner-primer-template.md: support-template
    primer-scope-manifest.md: support-template
```

## 문서를 어디에 넣을지 30초 판단표

새 문서를 추가할 때는 이름보다 먼저 아래 질문으로 자른다.

| 질문 | `예`면 더 가까운 분류 |
|---|---|
| 이 문서 하나만 읽어도 초보자가 큰 그림과 첫 예시를 잡을 수 있는가 | `true-beginner-primer` |
| 이 문서의 주역할이 "이쪽이냐 저쪽이냐"를 연결하는 것인가 | `beginner-bridge` 또는 `beginner-entrypoint-router` |
| 이 문서가 review/triage/check 용도인가 | `beginner-checklist` |
| 이 문서가 작성 규칙이나 분류 계약을 설명하는가 | `support-template` |

짧게 외우면 이렇다.

- **정문**이면 primer
- **갈림길 표지판**이면 bridge/router
- **점검 카드**면 checklist

## 작게 붙일 수 있는 doc-level marker

지금은 manifest만으로도 lint를 돌릴 수 있다.
다만 새 문서는 본문 위쪽에 아래 한 줄을 함께 붙이면 사람이 읽을 때도 더 빨리 분류된다.

```md
> Primer Scope: `true-beginner-primer`
```

다른 값 예시는 아래처럼 맞춘다.

```md
> Primer Scope: `beginner-entrypoint-router`
> Primer Scope: `beginner-bridge`
> Primer Scope: `beginner-checklist`
```

이 marker는 사람이 빠르게 읽는 용도이고, lint 기준의 정답표는 현재 manifest를 우선한다.

## 공통 혼동 3개

- "`Beginner`면 다 primer 아닌가요?" -> 아니다. beginner는 독자 난이도이고, primer는 문서 역할이다.
- "`entrypoint`면 무조건 primer 아닌가요?" -> 아니다. 질문 라우터형 entrypoint는 primer로 보내는 표지판일 수 있다.
- "`primer`라는 단어가 파일명에 있으면 primer 아닌가요?" -> 아니다. manifest 분류를 우선한다.

## 다음에 문서를 추가할 때

1. 먼저 이 manifest에서 분류를 정한다.
2. `true-beginner-primer`면 [Beginner Primer 작성 템플릿](./beginner-primer-template.md) 리듬을 따른다.
3. `bridge`나 `checklist`면 primer 앵커를 억지로 맞추지 말고, 비교/판별 역할을 더 선명하게 쓴다.

## 한 줄 정리

이 manifest의 목적은 "beginner 문서"를 한 덩어리로 보지 않고, **첫 진입 primer만 lint 타깃으로 정확히 고정하는 것**이다.
