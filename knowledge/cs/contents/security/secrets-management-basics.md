# 시크릿 관리 기초: API 키와 비밀번호를 코드에 넣으면 안 되는 이유

> 한 줄 요약: DB 비밀번호·API 키 같은 시크릿은 소스 코드나 Git에 절대 넣으면 안 되고, 환경변수나 전용 시크릿 스토어를 통해 런타임에 주입해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [비밀번호 저장 기초](./password-hashing-basics.md)
- [API 키 기초](./api-key-basics.md)
- [Spring IoC 컨테이너와 DI](../spring/ioc-di-container.md)
- [Security 카테고리 README](./README.md)

retrieval-anchor-keywords: secrets management basics, api 키 코드에 넣으면, git에 비밀번호, env 환경변수 기초, dotenv 란, application.properties 보안, 시크릿 관리 입문, vault 이란, 민감정보 관리 beginner, credential 노출, 설정 파일 보안, secrets in code danger

## 핵심 개념

처음 백엔드를 개발할 때 흔히 하는 실수가 있다. DB 접속 비밀번호나 외부 API 키를 소스 코드 안에 직접 넣는 것이다.

```java
// 위험한 예시 — 코드에 시크릿을 직접 넣지 않는다
String apiKey = "sk-1234abcd...";
```

이 코드가 GitHub에 올라가는 순간, 세계 누구나 그 키를 볼 수 있다. 실제로 GitHub을 자동 스캔해서 유출된 API 키를 수집하는 봇이 존재한다.

시크릿 관리의 핵심 원칙은 간단하다. **시크릿은 코드 밖에서 관리하고, 실행 시점에 주입한다.**

## 한눈에 보기

| 방법 | 설명 | 적합한 환경 |
|---|---|---|
| 환경변수 | OS 레벨 변수, 코드에서 읽기 | 개발·소규모 서비스 |
| `.env` 파일 | 로컬 개발용 환경변수 파일 | 로컬 개발 전용 |
| Cloud Secrets Manager | AWS Secrets Manager, GCP Secret Manager 등 | 운영 환경 |
| Vault (HashiCorp) | 오픈소스 시크릿 중앙 관리 | 대규모 운영 환경 |

`.env` 파일은 반드시 `.gitignore`에 추가해서 Git에 커밋되지 않게 한다.

## 상세 분해

### 환경변수로 주입하기

가장 기본적인 방법이다. 시크릿을 코드 밖 환경변수로 설정하고 코드에서 읽는다.

Spring Boot에서는 `application.properties`나 `application.yml`에서 환경변수를 참조할 수 있다.

```properties
spring.datasource.password=${DB_PASSWORD}
```

실행 시 `DB_PASSWORD`가 주입되지 않으면 애플리케이션이 시작되지 않으므로, 시크릿이 없는 상태로 실행되는 사고를 방지한다.

### `.env` 파일의 규칙

로컬 개발에서 편의를 위해 `.env` 파일에 시크릿을 모아두는 것은 괜찮다. 단, 반드시 두 가지를 지켜야 한다.

1. `.gitignore`에 `.env`를 추가한다.
2. `.env.example`을 만들어 키 이름만 공유한다 (값은 비워 둠).

### 운영 환경의 시크릿 스토어

운영 환경에서는 환경변수를 직접 서버에 넣기보다 전용 시크릿 스토어를 쓴다. AWS Secrets Manager는 시크릿을 암호화해서 저장하고, 애플리케이션이 IAM 권한으로 런타임에 가져간다. 시크릿 값을 사람이 직접 보거나 수정하는 횟수를 줄이고, 접근 기록을 남긴다.

## 흔한 오해와 함정

### "private 저장소니까 괜찮다"

Private 저장소도 팀원 전체가 볼 수 있고, 실수로 public이 될 수도 있다. 저장소 접근 권한과 시크릿 접근 권한은 별개로 관리해야 한다.

### "application.properties에 넣으면 코드에 넣은 게 아니다"

`application.properties`도 소스 코드 파일이다. Git에 커밋되면 히스토리에 영원히 남는다. `git rm`으로 삭제해도 `git log`에서는 계속 볼 수 있다.

### "한 번 유출된 시크릿을 Git 히스토리에서 지우면 된다"

Git 히스토리 재작성은 복잡하고 팀 협업을 방해한다. 유출이 의심되면 시크릿 자체를 즉시 무효화하고 새 시크릿을 발급하는 것이 더 빠르고 안전하다.

## 실무에서 쓰는 모습

Spring Boot 프로젝트를 GitHub에 올릴 때 흔히 쓰는 패턴이다.

1. `src/main/resources/application.properties`에는 `spring.datasource.password=${DB_PASSWORD}`처럼 환경변수 참조만 넣는다.
2. 로컬 개발을 위해 `.env` 파일에 실제 값을 넣고 `.gitignore`에 추가한다.
3. CI/CD 파이프라인(GitHub Actions 등)에서는 Repository Secrets에 시크릿을 등록하고, 파이프라인 실행 시 환경변수로 주입한다.

프로젝트 시작 시점에 이 구조를 잡아두면, 나중에 유출 사고를 막을 수 있다.

## 더 깊이 가려면

- API 키 발급과 검증 방법: [API 키 기초](./api-key-basics.md)
- 비밀번호 저장 방법: [비밀번호 저장 기초](./password-hashing-basics.md)

## 면접/시니어 질문 미리보기

> Q: DB 비밀번호를 코드에 직접 넣으면 어떤 문제가 생기나요?
> 의도: 시크릿 노출 위험을 이해하는지 확인
> 핵심: Git 커밋 히스토리에 영원히 남고, 저장소가 공개되거나 유출되면 DB 접근 권한이 외부에 노출된다. 환경변수나 시크릿 스토어로 분리해야 한다.

> Q: `.env` 파일을 `.gitignore`에 추가해야 하는 이유는 무엇인가요?
> 의도: 로컬 개발 시 시크릿 관리 기초를 아는지 확인
> 핵심: `.env` 파일에는 실제 시크릿 값이 있으므로 Git에 커밋되면 저장소 접근 권한이 있는 모든 사람이 볼 수 있다.

## 한 줄 정리

시크릿은 코드와 Git 밖에서 관리하고 환경변수나 시크릿 스토어로 런타임에 주입해야 하며, 유출이 의심되면 코드 수정보다 시크릿 교체를 먼저 한다.
