# Private / Prelaunch 네트워크 흐름

## 개념

사주다방은 local, private, prelaunch, production을 구분한다.

이건 단순 환경변수 차이가 아니라, **네트워크 의미가 다르다**는 뜻이다.

## 현재 기준

- private 프론트 번들
- prelaunch Java backend
- 도메인: `api-prelaunch.saju-dabang.com`

## 흐름

```text
Toss App (private link)
  -> app bundle
  -> HTTPS call to api-prelaunch.saju-dabang.com
  -> Route53
  -> EC2 single-box
  -> Caddy
  -> Java API / worker / postgres / redis
```

## 왜 production과 분리하나

- 미완성 기능 검증
- 실기기 테스트
- 운영 데이터와 분리
- 잘못된 배포 영향 최소화

## 면접 포인트

“개발 환경, 검증 환경, 운영 환경을 분리하는 건 소프트웨어 품질과 장애 격리를 위해 중요하다. 사주다방은 prelaunch 도메인을 별도로 두고 private 테스트에 사용했다.”
