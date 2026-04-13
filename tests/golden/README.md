# Golden Fixtures

개발자용 회귀 검증 fixture.

원칙:

- 학습자는 이 디렉터리를 직접 사용할 필요가 없다.
- `bin/golden` 또는 `python3 -m scripts.workbench golden`으로만 사용한다.
- 전체 답변 문장을 고정하지 말고, intent/topic/focus/reference role 같은 구조적 필드만 검증한다.

주의:

- fixture는 로컬에 해당 repo가 onboarded 되어 있고, 최소한 코칭 세션이 동작할 정도의 데이터가 있을 때 가장 안정적이다.
- 새로운 미션이나 다른 샘플 repo를 기준으로 회귀를 보고 싶다면 이 파일에 case를 추가하면 된다.
