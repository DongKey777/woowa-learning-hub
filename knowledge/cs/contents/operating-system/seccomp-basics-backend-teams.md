# Seccomp Basics, Backend Teams

> 한 줄 요약: seccomp는 허용된 syscall만 남기는 필터라서, 백엔드 팀이 컨테이너와 런타임의 공격면을 줄일 때 가장 직접적인 커널 레벨 안전장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)
> - [container, cgroup, namespace](./container-cgroup-namespace.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)
> - [FD Exhaustion, ulimit, Diagnostics](./fd-exhaustion-ulimit-diagnostics.md)
> - [signals, process supervision](./signals-process-supervision.md)

> retrieval-anchor-keywords: seccomp, syscall filter, no_new_privs, PR_SET_NO_NEW_PRIVS, BPF filter, container security, syscall allowlist, backend hardening

## 핵심 개념

seccomp는 프로세스가 호출할 수 있는 syscall을 제한하는 리눅스 보안 메커니즘이다. 백엔드에서는 보안뿐 아니라 런타임 안정성과 오류 격리에도 영향을 준다.

- `seccomp`: syscall 필터링 메커니즘이다
- `no_new_privs`: 더 강한 권한 상승을 막는 플래그다
- `allowlist`: 허용할 syscall만 명시하는 방식이다

왜 중요한가:

- 컨테이너 공격면을 줄일 수 있다
- 런타임이 예상하는 syscall만 남겨 장애 범위를 줄일 수 있다
- 잘못 넣으면 정상 기능이 바로 깨질 수 있다

이 문서는 [시스템 콜과 User-Kernel Boundary](./syscall-user-kernel-boundary.md)와 [container, cgroup, namespace](./container-cgroup-namespace.md)를 보안 관점으로 잇는다.

## 깊이 들어가기

### 1. seccomp는 syscall 수준의 경계다

앱이 커널로 내려가는 경로를 필터링한다.

- `openat`, `read`, `write`, `futex` 같은 기본 syscall이 중요하다
- 특정 기능이 있으면 추가 syscall이 필요할 수 있다
- 차단되면 `EPERM`이나 프로세스 종료로 이어질 수 있다

### 2. allowlist는 단순하지만 강하다

허용한 syscall만 두는 방식은 공격면을 줄인다.

- 불필요한 syscall 제거
- 컨테이너/샌드박스 경화
- 예상 못한 런타임 의존성 드러남

### 3. backend 팀은 기능과 필터를 같이 봐야 한다

- DNS lookup
- file I/O
- networking
- thread synchronization

이런 경로가 어떤 syscall을 요구하는지 파악해야 한다.

### 4. 관측 없이 seccomp를 걸면 위험하다

운영에서는 먼저 trace로 syscall 사용량을 확인하고, 그 다음 필터를 좁혀야 한다.

## 실전 시나리오

### 시나리오 1: 컨테이너에 seccomp를 넣었더니 시작이 실패한다

가능한 원인:

- 필요한 syscall을 막았다
- JVM/native library가 추가 syscall을 쓴다
- 런타임이 숨겨진 syscalls를 호출한다

진단:

```bash
strace -f -ttT -e trace=%file,%process,%network,%signal -p <pid>
```

### 시나리오 2: 서비스는 뜨는데 특정 기능만 실패한다

가능한 원인:

- 해당 기능이 드문 syscall을 쓴다
- seccomp 프로필이 너무 좁다
- 운영자도 예상 못 한 런타임 경로다

### 시나리오 3: 보안을 강화했는데 관측이 어려워졌다

가능한 원인:

- 필터가 너무 엄격하다
- 디버깅 syscall까지 막았다
- rollout 전에 충분히 검증하지 않았다

## 코드로 보기

### 기본 방어 생각

```text
allow only required syscalls
  -> block unexpected kernel transitions
  -> reduce attack surface
```

### 운영 확인 감각

```bash
strace -f -e trace=%file,%network,%process <command>
```

### `no_new_privs` 개념 확인

```c
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 강한 allowlist | 공격면을 크게 줄인다 | 호환성 문제가 생길 수 있다 | 컨테이너 경화 |
| 넓은 허용 | 기능 호환성이 높다 | 방어력이 약해진다 | 일반 개발 환경 |
| 단계적 rollout | 장애를 줄인다 | 운영 절차가 늘어난다 | 프로덕션 |

## 꼬리질문

> Q: seccomp는 무엇을 막나요?
> 핵심: 프로세스가 호출할 수 있는 syscall을 제한한다.

> Q: backend 팀이 seccomp를 왜 신경 써야 하나요?
> 핵심: 보안뿐 아니라 런타임 호환성과 장애 격리에 직접 영향이 있기 때문이다.

> Q: allowlist가 왜 좋은가요?
> 핵심: 필요한 syscall만 남겨 공격면을 줄일 수 있기 때문이다.

## 한 줄 정리

seccomp는 syscall allowlist로 런타임 공격면을 줄이는 강력한 경계지만, backend 기능이 요구하는 syscall을 먼저 관측하고 설계해야 한다.
