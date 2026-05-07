---
schema_version: 3
title: Direct Buffer Off-Heap Memory Troubleshooting
concept_id: language/direct-buffer-offheap-memory-troubleshooting
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- off-heap-memory
- direct-buffer
- rss-debugging
aliases:
- Direct Buffer Off-Heap Memory Troubleshooting
- ByteBuffer.allocateDirect
- Direct buffer memory OOM
- Java off-heap native memory
- NMT direct buffer
- mmap MappedByteBuffer
- RSS heap mismatch
symptoms:
- heap dump와 GC 로그는 깨끗한데 RSS가 계속 증가하거나 container OOM killer가 발생해
- OutOfMemoryError Direct buffer memory가 나는데 -Xmx만 보고 heap 여유를 확인해 원인을 놓쳐
- ByteBuffer.allocateDirect와 FileChannel.map이 native memory, mmap, Cleaner release timing에 의존한다는 점을 고려하지 않아
intents:
- troubleshooting
- deep_dive
prerequisites:
- language/io-nio-serialization
next_docs:
- language/cleaner-vs-finalize-deprecation
- language/oom-heap-dump-playbook
- operating-system/oom-killer-cgroup-memory-pressure
linked_paths:
- contents/language/java/io-nio-serialization.md
- contents/language/java/oom-heap-dump-playbook.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/operating-system/oom-killer-cgroup-memory-pressure.md
- contents/operating-system/mmap-sendfile-splice-zero-copy.md
- contents/language/java/cleaner-vs-finalize-deprecation.md
- contents/language/java/jcmd-diagnostic-command-cheatsheet.md
confusable_with:
- language/oom-heap-dump-playbook
- operating-system/oom-killer-cgroup-memory-pressure
- language/cleaner-vs-finalize-deprecation
forbidden_neighbors: []
expected_queries:
- Java heap은 여유 있는데 RSS가 오르고 Direct buffer memory OOM이 나는 원인을 어떻게 찾지?
- ByteBuffer.allocateDirect가 heap 밖 native memory를 쓰기 때문에 heap dump에 작게 보이는 이유가 뭐야?
- MappedByteBuffer와 mmap memory가 cgroup OOM pressure에 영향을 주는 경로를 설명해줘
- Native Memory Tracking으로 direct buffer off-heap 사용량을 어떻게 확인해?
- direct buffer를 요청마다 할당하면 allocation churn과 Cleaner release delay가 왜 문제가 돼?
contextual_chunk_prefix: |
  이 문서는 Direct Buffer off-heap memory 문제를 ByteBuffer.allocateDirect, native memory, mmap, RSS, NMT, OOM killer, Cleaner release timing 관점으로 진단하는 advanced playbook이다.
  Direct buffer memory OOM, heap clean but RSS high, off-heap, MappedByteBuffer, NMT, container memory 질문이 본 문서에 매핑된다.
---
# Direct Buffer Off-Heap Memory Troubleshooting

> 한 줄 요약: heap은 멀쩡한데 RSS가 계속 오르거나 `OutOfMemoryError: Direct buffer memory`가 난다면, direct buffer와 mmap이 쓰는 native memory 경로를 먼저 의심해야 한다.

**난이도: 🔴 Advanced**

> related-docs:
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [OOM Killer, cgroup Memory Pressure](../../operating-system/oom-killer-cgroup-memory-pressure.md)
> - [mmap, sendfile, splice, zero-copy](../../operating-system/mmap-sendfile-splice-zero-copy.md)

> retrieval-anchor-keywords: direct buffer, off-heap, native memory, ByteBuffer.allocateDirect, NMT, mmap, OOM, RSS

왜 중요한가:

`ByteBuffer.allocateDirect()`는 Java heap 밖, 즉 off-heap native memory를 사용한다.  
그래서 애플리케이션이 "힙은 여유 있는데도" 죽을 수 있다.

실무에서 자주 헷갈리는 지점은 다음이다.

- heap dump가 깨끗한데 프로세스 RSS는 계속 증가한다
- `-Xmx`를 줄였는데도 컨테이너가 죽는다
- GC 로그는 평온한데 `Direct buffer memory` OOM이 난다
- `MappedByteBuffer`를 쓴 뒤 메모리가 잘 안 내려간다

즉 이 주제는 "버퍼 API"가 아니라 **JVM 밖 메모리까지 포함해 프로세스 전체 메모리 생명주기를 읽는 법**이다.

## 핵심 개념

### Direct buffer란 무엇인가

`ByteBuffer`에는 heap buffer와 direct buffer가 있다.

- heap buffer: `byte[]` 위에 올라가며 GC가 직접 관리한다
- direct buffer: heap 밖 native memory를 잡아두고 I/O 경로에서 자주 쓴다

직접 할당 예:

```java
ByteBuffer buffer = ByteBuffer.allocateDirect(64 * 1024);
```

이 buffer는 heap 객체 자체는 작아도, 실제 데이터는 native memory에 잡힌다.  
그래서 `jmap -histo`나 heap dump만 보면 범인이 작게 보일 수 있다.

### 왜 I/O에서 direct buffer를 쓰나

Heap buffer는 보통 다음 경로를 탄다.

1. Java heap에 데이터를 쓴다
2. 네이티브 I/O 계층으로 다시 복사한다

Direct buffer는 이 중간 복사를 줄이기 위해 쓰인다.  
특히 NIO, socket I/O, 파일 전송, TLS 처리 경로에서 자주 등장한다.

다만 여기서 중요한 것은, direct buffer가 곧 zero-copy라는 뜻은 아니라는 점이다.  
복사가 줄어들 수는 있어도, native allocation, page fault, RSS 증가, cgroup pressure 같은 비용은 그대로 남는다.

### off-heap과 native memory

off-heap은 넓은 개념이다.

- direct buffer
- mmap으로 매핑된 파일 페이지
- thread stack
- JNI/native 라이브러리 할당
- metaspace 등 JVM native 영역

즉 "heap이 아니다"만으로는 부족하고, **어떤 native 영역이 얼마를 쓰는지**까지 봐야 한다.

## 깊이 들어가기

### 1. `ByteBuffer.allocateDirect()`가 위험해지는 순간

direct buffer는 GC가 곧바로 해제하는 객체가 아니다.  
보통 Java 객체가 unreachable이 된 뒤 Cleaner 계열 경로로 native memory가 회수된다.

이 말의 실전 의미는 이렇다.

- 버퍼를 너무 자주 만들면 native allocation churn이 커진다
- 참조가 오래 남으면 release도 늦어진다
- 풀링 없이 요청마다 큰 direct buffer를 만들면 RSS가 튄다

특히 큰 payload를 다루는 서버에서 다음 패턴이 위험하다.

```java
public byte[] readFrame(SocketChannel channel, int size) throws IOException {
    ByteBuffer buffer = ByteBuffer.allocateDirect(size);
    channel.read(buffer);
    buffer.flip();

    byte[] result = new byte[buffer.remaining()];
    buffer.get(result);
    return result;
}
```

이 코드는 겉으로는 단순하지만, 요청이 많아지면 direct allocation과 heap copy를 둘 다 만든다.

### 2. `mmap()`은 또 다른 off-heap이다

`FileChannel.map()`은 파일을 메모리처럼 보이게 만든다.

```java
try (FileChannel channel = FileChannel.open(Path.of("/var/log/app.log"), StandardOpenOption.READ)) {
    MappedByteBuffer mapped = channel.map(FileChannel.MapMode.READ_ONLY, 0, channel.size());
    byte first = mapped.get(0);
}
```

이런 매핑은 파일-backed native memory를 사용한다.

주의할 점:

- 매핑된 페이지는 실제로 접근될 때 RSS에 반영된다
- 파일이 크면 page fault와 page cache pressure가 함께 생긴다
- unmap 시점은 JVM과 GC 타이밍에 영향을 받는다

그래서 `mmap()`은 "파일을 읽는 다른 방법"이 아니라, **프로세스 메모리 모델 자체를 바꾸는 도구**다.

### 3. NMT로 봐야 heap과 native를 구분할 수 있다

Native Memory Tracking(NMT)은 JVM native 메모리를 범주별로 보게 해준다.  
이걸 켜지 않으면 heap 외 메모리가 어디서 늘어나는지 감이 잘 안 온다.

JVM 시작 옵션 예:

```bash
java \
  -XX:NativeMemoryTracking=summary \
  -XX:+UnlockDiagnosticVMOptions \
  -Xms2g -Xmx2g \
  -jar app.jar
```

실행 중 점검:

```bash
jcmd <pid> VM.native_memory summary
jcmd <pid> VM.native_memory detail
```

확인 포인트:

- `Java Heap`
- `Class`
- `Thread`
- `Code`
- `GC`
- `Internal`
- `NIO`

`NIO`가 크면 direct buffer나 관련 native path를 의심한다.  
`Thread`가 크면 stack 메모리를, `Internal`이 크면 JVM 내부 native 사용을 본다.

### 4. RSS는 왜 힙과 다르게 보이나

RSS(Resident Set Size)는 프로세스가 실제로 RAM에 올려 둔 페이지의 크기다.  
heap size와 1:1로 같지 않다.

RSS가 heap보다 커지는 흔한 이유:

- direct buffer
- mmap 페이지
- thread stack
- code cache
- metaspace
- libc/JVM native allocation

즉 "heap은 2GB인데 RSS는 4GB"라는 상황은 충분히 자연스럽다.  
문제는 그 2GB 차이가 의도된 것인지, 누수인지 구분하는 것이다.

## 실전 시나리오

### 시나리오 1: heap dump는 멀쩡한데 컨테이너가 OOMKilled 된다

증상:

- `OutOfMemoryError`가 안 났는데 Pod가 재시작된다
- heap 사용률은 제한 안쪽이다
- RSS만 계속 오른다

원인 후보:

- direct buffer 누적
- mmap 파일 증가
- thread 수 증가로 stack 증가
- JNI 라이브러리의 native allocation

점검 순서:

```bash
jcmd <pid> VM.flags
jcmd <pid> VM.native_memory summary
cat /proc/<pid>/status | grep -E 'VmRSS|VmSize|Threads'
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
```

이 상황은 [OOM Killer, cgroup Memory Pressure](../../operating-system/oom-killer-cgroup-memory-pressure.md)와 바로 연결된다.  
heap이 아니라 RSS와 cgroup limit이 먼저 한계에 닿을 수 있기 때문이다.

### 시나리오 2: `OutOfMemoryError: Direct buffer memory`

이 에러는 대개 direct buffer 할당 한도에 도달했음을 뜻한다.  
JVM은 direct memory도 무한정 허용하지 않는다.

점검할 것:

- `-XX:MaxDirectMemorySize`
- 버퍼를 얼마나 자주 만드는지
- 풀을 쓰는지
- 요청 종료 후 참조가 빨리 끊기는지

추가로 확인:

```bash
jcmd <pid> VM.native_memory summary
jcmd <pid> GC.class_histogram
```

heap dump는 보조 증거일 뿐, direct buffer 문제의 주 증거는 아니다.  
이 문맥은 [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)와 역할이 다르다.

### 시나리오 3: `MappedByteBuffer`를 쓴 뒤 메모리가 잘 안 내려간다

증상:

- 파일을 열었다 닫아도 RSS가 쉽게 안 줄어든다
- 대형 파일을 반복 매핑하면 메모리 압박이 커진다
- 로컬에서는 괜찮다가 운영에서만 느려진다

이유:

- page cache와 매핑된 페이지가 남아 있을 수 있다
- unmap 시점이 GC와 Cleaner에 의존할 수 있다
- 파일 접근 패턴이 랜덤이면 page fault 비용이 커진다

이 문제는 [mmap, sendfile, splice, zero-copy](../../operating-system/mmap-sendfile-splice-zero-copy.md)와 함께 봐야 한다.

### 시나리오 4: direct buffer를 너무 많이 만들어 GC도 같이 흔들린다

direct buffer는 native memory를 쓰지만, Java 객체 껍데기는 heap에 있다.  
그래서 버퍼 객체가 너무 많아지면 heap churn도 생긴다.

결과:

- allocation rate 증가
- GC pressure 증가
- native memory 회수 지연

이 경우는 JFR로 allocation burst와 latency spike를 같이 보는 것이 유리하다.  
[JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)와 연결해서 보자.

## 코드로 보기

### 1. direct buffer를 재사용하는 패턴

```java
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;

public final class DirectBufferReader {
    private final ByteBuffer buffer = ByteBuffer.allocateDirect(64 * 1024);

    public int read(SocketChannel channel) throws IOException {
        buffer.clear();
        int read = channel.read(buffer);
        buffer.flip();
        return read;
    }
}
```

핵심은 매 요청마다 새로 만들지 않고, 범위를 제한한 뒤 재사용하는 것이다.

### 2. direct memory 점검을 위한 현장 커맨드

```bash
jcmd <pid> VM.native_memory summary
jcmd <pid> VM.native_memory detail
jcmd <pid> Thread.print
jcmd <pid> GC.class_histogram
```

NMT가 비활성화되어 있으면 summary가 충분히 안 보일 수 있다.  
그래서 운영 재현이 어렵다면 사전에 `-XX:NativeMemoryTracking=summary`를 켜 두는 편이 좋다.

### 3. direct buffer OOM을 재현하는 간단한 예

```java
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;

public class DirectMemoryLeakDemo {
    public static void main(String[] args) {
        List<ByteBuffer> buffers = new ArrayList<>();

        while (true) {
            buffers.add(ByteBuffer.allocateDirect(16 * 1024 * 1024));
        }
    }
}
```

이 코드는 참조를 계속 잡고 있어서 native memory 회수가 늦어진다.  
heap이 아니라 off-heap이 먼저 터질 수 있다는 점을 보여주기 위한 예시다.

### 4. 실행 옵션 예시

```bash
java \
  -Xms1g -Xmx1g \
  -XX:MaxDirectMemorySize=256m \
  -XX:NativeMemoryTracking=summary \
  -XX:+UnlockDiagnosticVMOptions \
  -XX:+HeapDumpOnOutOfMemoryError \
  -jar app.jar
```

이렇게 하면 heap OOM과 native OOM을 함께 관찰하기 쉬워진다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| heap buffer | GC로 관리가 쉽다 | I/O 경로에서 추가 복사가 생길 수 있다 | 단순 로직, 작은 payload |
| direct buffer | I/O 효율이 좋다 | native memory 추적이 어렵다 | 네트워크/파일 I/O 집중 |
| `mmap()` | 대용량 파일에 유리할 수 있다 | RSS와 page fault가 복잡해진다 | 읽기 중심 파일 접근 |
| 버퍼 풀링 | allocation churn을 줄인다 | 풀 관리가 복잡하다 | 고QPS, 큰 버퍼 |
| 요청마다 새 할당 | 구현이 쉽다 | RSS와 GC 압력이 커진다 | 짧은 실험, 비핵심 경로 |

결국 선택 기준은 "빠르냐" 하나가 아니다.

- 메모리 한도 안에서 안정적으로 버티는가
- 장애 시 heap/native를 분리해서 볼 수 있는가
- 운영에서 추적 가능한가
- page fault와 RSS 증가를 감당할 수 있는가

## 꼬리질문

> Q: direct buffer는 왜 heap dump에 잘 안 보이나요?
> 의도: heap과 native memory의 경계를 아는지 확인
> 핵심: 실제 데이터는 heap 밖에 있고, heap dump는 주로 heap 객체 관계를 보여준다.

> Q: `ByteBuffer.allocateDirect()`를 왜 쓰나요?
> 의도: 성능 목적과 비용을 같이 이해하는지 확인
> 핵심: I/O 복사를 줄이기 위해 쓰지만, native memory와 RSS 증가를 같이 관리해야 한다.

> Q: NMT는 왜 필요하나요?
> 의도: heap만으로는 부족하다는 점을 아는지 확인
> 핵심: direct buffer, thread stack, internal native 영역을 범주별로 본다.

> Q: `MappedByteBuffer`와 direct buffer는 같은 건가요?
> 의도: off-heap의 종류를 구분하는지 확인
> 핵심: 둘 다 heap 밖 메모리를 사용하지만, 전자는 파일 매핑 기반이라 page cache와 fault 특성이 다르다.

> Q: heap은 멀쩡한데 RSS가 증가하면 무엇부터 보나요?
> 의도: 운영 진단 우선순위를 확인
> 핵심: `jcmd VM.native_memory summary`, `/proc/<pid>/status`, cgroup memory.current, direct buffer와 mmap 사용량을 본다.

## 한 줄 정리

direct buffer와 mmap은 heap 밖 native memory를 쓰므로, 문제를 볼 때는 heap dump보다 먼저 NMT, RSS, cgroup pressure, `MaxDirectMemorySize`를 같이 확인해야 한다.
