# GitHub CLI Guide

## 목적

이 문서는 `gh`를 미션 진행, PR 리뷰 확인, API 탐색, 메타데이터 수집에 안정적으로 사용하는 기준을 정리한다.

핵심 원칙:
- PR 하나를 읽을 때는 `gh pr view`를 먼저 쓴다.
- PR 목록이나 필터링은 `gh pr list`를 먼저 쓴다.
- raw endpoint, pagination, 리뷰 코멘트, rate limit 확인은 `gh api`를 쓴다.
- 검색 API는 비싸므로 마지막 수단으로만 사용한다.

---

## 공식 문서

- GitHub CLI manual: <https://cli.github.com/manual>
- `gh api`: <https://cli.github.com/manual/gh_api>
- `gh pr view`: <https://cli.github.com/manual/gh_pr_view>
- `gh pr list`: <https://cli.github.com/manual/gh_pr_list>
- `gh auth status`: <https://cli.github.com/manual/gh_auth_status>
- formatting (`--json`, `--jq`, `--template`): <https://cli.github.com/manual/gh_help_formatting>

---

## 인증 기준

### 1. 저장된 로그인 상태 확인

```bash
gh auth status
```

- `gh`가 저장하고 있는 계정 상태를 본다.
- invalid가 뜨면 다시 로그인한다.

```bash
gh auth login -h github.com -p https -w
```

### 2. 실제 인증 요청이 되는지 확인

```bash
gh api user
```

- 이 요청이 성공하면 실제 API 호출은 가능한 상태로 본다.
- `gh auth status`와 `gh api user` 결과가 다를 수 있으므로, 실무적으로는 둘 다 확인하는 것이 좋다.

---

## 명령 선택 기준

### PR 하나 읽기

```bash
gh pr view 346 --json number,title,body,files,reviews,comments
```

이럴 때 사용:
- 특정 PR의 제목/본문/파일/리뷰를 보고 싶을 때
- 현재 브랜치와 연결된 PR을 보고 싶을 때

특징:
- 인자 없이 실행하면 현재 브랜치 PR을 본다.
- `--comments`는 빠르게 댓글을 plain text로 볼 때 유용하다.

### PR 목록 보기

```bash
gh pr list --state all --json number,title,author,state
```

이럴 때 사용:
- 전체 PR 목록 보기
- author, state, base, head 기준으로 필터링

### 리뷰 코멘트 / raw endpoint / pagination

```bash
gh api repos/woowacourse/java-janggi/pulls/346/comments --paginate
gh api repos/woowacourse/java-janggi/pulls/346/reviews
gh api repos/woowacourse/java-janggi/pulls/346
```

이럴 때 사용:
- review comment 원문 보기
- issue comment와 review comment를 구분해서 보기
- raw REST 응답 구조를 직접 확인하고 싶을 때
- `--paginate`가 필요한 endpoint일 때

---

## 출력 가공 규칙

### `gh pr view`, `gh pr list`

이 두 명령은 `--jq`를 쓰려면 `--json`이 먼저 필요하다.

```bash
gh pr view 346 --json comments --jq '.comments[].body'
gh pr list --state all --json number,title --jq '.[] | [.number, .title]'
```

### `gh api`

`gh api`는 응답이 바로 JSON이므로 `--json` 없이 `--jq`를 붙일 수 있다.

```bash
gh api repos/woowacourse/java-janggi/pulls/346/comments --jq '.[].body'
```

### `--template`

사람이 읽기 좋게 테이블 형태로 출력할 때 쓴다.

```bash
gh pr list --state all \
  --json number,title,author,updatedAt \
  --template '{{range .}}{{tablerow (printf "#%v" .number) .title .author.login (timeago .updatedAt)}}{{end}}{{tablerender}}'
```

---

## Search 사용 원칙

### 먼저 쓰지 말 것

- `gh search code`
- `search/issues`

이유:
- 별도 rate limit 버킷이 작다.
- `code_search`는 특히 금방 소진된다.
- 반복 루프에서 여러 repo에 연달아 쏘면 쉽게 막힌다.

### 우선순위

1. `gh pr view`
2. `gh pr list`
3. `gh api repos/...`
4. 정말 필요할 때만 `gh search ...`

---

## Rate Limit 해석

확인 명령:

```bash
gh api rate_limit
gh api rate_limit | jq '{core: .resources.core, search: .resources.search, graphql: .resources.graphql, code_search: .resources.code_search}'
```

중요한 버킷:
- `core`: 일반 REST 조회
- `search`: 검색 API
- `code_search`: 코드 검색
- `graphql`: GraphQL

실무 해석:
- `core`는 여유가 큰 편이라 일반 PR/리뷰/이슈 조회는 여기로 해결하는 것이 좋다.
- `search`, `code_search`는 작으므로 아껴 써야 한다.

---

## 현재 미션에서 자주 쓰는 예시

### 현재 브랜치 PR 보기

```bash
gh pr view --comments
```

### 특정 PR의 리뷰/코멘트까지 구조적으로 보기

```bash
gh pr view 346 --json number,title,body,files,reviews,comments
```

### 리뷰 코멘트만 따로 보기

```bash
gh api repos/woowacourse/java-janggi/pulls/346/comments --paginate
```

### 리뷰 이벤트 보기

```bash
gh api repos/woowacourse/java-janggi/pulls/346/reviews
```

### 내 브랜치 PR 찾기

```bash
gh api 'repos/woowacourse/java-janggi/pulls?state=all&head=DongKey777:step2'
```

### 사이클2 PR 개수 세기

```bash
gh api 'repos/woowacourse/java-janggi/pulls?state=all&per_page=100&page=1' \
| jq '[.[] | select(.title | contains("사이클2"))] | length'
```

---

## 장애 대응 메모

### `invalid character '<' looking for beginning of value`

의미:
- JSON 대신 HTML 에러 페이지가 왔다.

주요 원인:
- search API 에러
- rate limit
- 인증/호스트 문제

대응:
- `gh api rate_limit` 확인
- search 대신 `repos/.../pulls` endpoint로 우회

### `token is invalid`

대응:

```bash
gh auth login -h github.com -p https -w
gh auth status
gh api user
```

### `error connecting to api.github.com`

의미:
- 네트워크 제한, DNS, 프록시, sandbox 문제 가능성

대응:
- 로컬 터미널에서 재시도
- 네트워크 제한 환경인지 확인

---

## 현재 사용 기준 요약

- PR 하나 읽기: `gh pr view`
- PR 목록 보기: `gh pr list`
- raw endpoint / 리뷰 코멘트 / pagination: `gh api`
- 출력 정리: `--json` + `--jq`
- 검색 API는 마지막 수단
- 인증 상태는 `gh auth status`와 `gh api user`를 같이 본다
