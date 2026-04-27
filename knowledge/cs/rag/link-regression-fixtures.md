# Link Regression Fixtures

> 한 줄 요약: punctuation-heavy asset 이름, inline-code HTML 예시, `srcset` candidate, `poster`/media `src`, local HTML `<a href>`가 다시 빠지거나 false positive로 흔들리지 않게 잡아 두는 QA fixture note다.
>
> 관련 문서:
> - [RAG Design](./README.md)
> - [Shared Markdown Link Scanner](./shared-markdown-link-scanner.md)
> - [Local Asset Existence Lint](./local-asset-existence-lint.md)
> - [Asset Filename Lint](./asset-filename-lint.md)

> retrieval-anchor-keywords: link regression fixture, punctuation-heavy asset example, inline code html example, balanced paren markdown link, markdown scanner regression, false positive fixture, local asset lint regression, asset filename lint regression, beginner link qa fixture, html srcset regression, local html href regression, poster attr regression, source src regression, track src regression

## 언제 보나

- link QA script를 손본 뒤 "예시 문장인데 왜 실제 broken link처럼 잡히지?"가 다시 나오지 않는지 빠르게 확인하고 싶을 때
- 초보자가 문서 예시와 실제 링크를 구분하지 못해 잘못된 rename이나 delete를 시작하기 전에 안전한 fixture를 보고 싶을 때

## fixture 묶음

- punctuation-heavy asset literal은 inline code로 고정한다: `` `![diagram](./img/release(qa)-v1.2.png)` ``, `` `[download](./code/retry&rollback.v2.pdf)` ``
- inline HTML literal도 inline code로 고정한다: `` `<img src="./img/release(qa)-v1.2.png" alt="qa">` ``, `` `<source srcset="./img/release(qa)-v1.2.png 1x, ./img/release(qa)-v2.0.png 2x">` ``
- 실제 HTML `srcset` candidate는 descriptor를 떼고 각각 따로 본다: `<source srcset="./img/release-safe.png 1x, ./img/release(qa).PNG 2x">`
- local HTML `<a href>`도 외부 링크처럼 넘기지 않고 repo-local target로 본다: `<a href="./fixtures/release-guide.html">safe local html</a>`, `<a href="./fixtures/release-guide(v2).html">missing local html</a>`
- `<video poster>`, `<source src>`, `<track src>`도 같은 local asset lint family로 본다: `<video poster="./media/preview(qa).PNG" src="./media/teaser.mp4"></video>`, `<source src="./media/release-safe.webm" type="video/webm">`, `<track src="./captions/release(ko).VTT" kind="captions">`
- balanced-paren target은 parser가 끝 괄호를 잃지 않아야 한다: `[scanner note](./guides/link-fixture(v2).md#balanced-(paren)-target "Fixture Title")`

이 문서의 첫 두 줄은 "실제 자산 링크"가 아니라 literal example이라서, code span masking이 깨지면 `local_asset_existence_lint`와 `asset_filename_lint`가 바로 흔들린다. 그다음 두 줄은 beginner가 자주 헷갈리는 "HTML 속 local path도 repo-local QA 범위인가?"를 고정하는 fixture다. media attr 줄은 `poster`와 추가 media `src`가 `src`/`href`/`srcset` 뒤에 빠지지 않는지 확인하는 회귀 핀이다. 마지막 줄은 nested parenthesis가 들어간 target을 scanner가 끝까지 읽는지 확인하는 parser fixture다.

## 어디로 이어서 가나

- parser 동작 범위를 다시 확인하려면 [Shared Markdown Link Scanner](./shared-markdown-link-scanner.md)를 본다.
- lint 실행 순서까지 정리하려면 [Document Naming and Linking Guidelines](./document-naming-linking-guidelines.md)를 본다.
- QA note index로 돌아가려면 [RAG Design](./README.md)를 다시 본다.
