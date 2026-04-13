# Security Flashcards

- Q: Bearer와 X-Device-Id를 같이 쓰는 이유는?
  A: 로그인/비로그인 흐름을 모두 지원하기 위해

- Q: 세션을 Redis와 DB에 같이 두는 이유는?
  A: 속도와 복구 가능성을 동시에 확보하기 위해

- Q: token hash를 쓰는 이유는?
  A: 세션 원문을 그대로 저장하지 않기 위해

- Q: AES-GCM을 쓰는 이유는?
  A: 복호화 가능한 민감 토큰을 무결성과 함께 보호하기 위해

- Q: mTLS가 필요한 이유는?
  A: 파트너 API에 대해 상호 인증을 하기 위해
