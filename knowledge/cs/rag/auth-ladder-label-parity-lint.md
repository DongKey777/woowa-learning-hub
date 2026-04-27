# Auth Ladder Label Parity Lint

> 한 줄 요약: `login-loop` beginner route가 root README, security README, RAG routing docs에서 같은 label과 같은 다음 단계 순서를 유지하는지 잡는 repo-local QA check다.
>
> 관련 문서:
> - [CS Root README: Auth / Session Beginner Shortcut](../README.md#auth--session-beginner-shortcut)
> - [Security README: Browser / Session Beginner Ladder](../contents/security/README.md#browser--session-beginner-ladder)
> - [RAG Design](./README.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#spring--security)
>
> retrieval-anchor-keywords: auth ladder label parity lint, login-loop route parity lint, root security rag ladder parity, login-loop canonical beginner entry route qa, cookie-missing server-anonymous parity, beginner auth label drift check, primer bridge order parity, security readme return-path parity

## 무엇을 고정하나

이 lint는 beginner가 가장 많이 타는 auth ladder에서 아래 네 가지를 같이 본다.

1. root README와 RAG routing docs가 canonical route label `[canonical beginner entry route: login-loop]`를 같이 유지하는가
2. security README ladder도 같은 primer -> primer bridge 순서 `Login Redirect, Hidden JSESSIONID, SavedRequest 입문` -> `Browser 401 vs 302 Login Redirect Guide`를 유지하는가
3. child label이 `cookie-missing` / `server-anonymous`로 정규화돼 있는가
4. RAG routing docs가 security README 복귀 경로를 여전히 가리키는가

## 언제 돌리나

- root/security README에서 login-loop row wording을 손봤을 때
- RAG routing docs에서 auth/session symptom alias를 조정했을 때
- retrieval alias는 남기되 beginner-facing label은 한 문장으로 맞췄는지 확인하고 싶을 때

## 실행

```bash
python docs/auth_ladder_label_parity_lint.py
```

## 통과 기준

- `knowledge/cs/README.md`
- `knowledge/cs/contents/security/README.md`
- `knowledge/cs/rag/README.md`
- `knowledge/cs/rag/cross-domain-bridge-map.md`

위 네 문서가 모두 canonical label, primer/bridge 순서, normalized child label, security README return-path wording을 함께 가진다.

## 실패 예시

- security README row에서 primer -> primer bridge 순서가 깨지고 spring deep dive가 먼저 옴
- RAG README summary row는 `login-loop`를 말하지만 `cookie-missing` / `server-anonymous` child label을 잃음
- cross-domain bridge map이 primer/bridge 순서를 건너뛰고 spring deep dive만 남김

## 한 줄 정리

login-loop ladder를 손봤다면 beginner가 같은 이름으로 다시 찾을 수 있게 root/security/RAG 네 문서의 route label과 safe next step을 같이 lint로 고정한다.
