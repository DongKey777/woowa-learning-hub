# Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기

> 한 줄 요약: 브라우저 Network 탭 waterfall은 "요청 전체 시간" 한 덩어리가 아니라 `dns -> connect -> ssl -> request sent -> waiting -> content download`로 잘라 읽는 시간표이며, 각 칸이 답하는 질문을 먼저 분리해야 병목을 잘못 찍지 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)

retrieval-anchor-keywords: browser devtools waterfall, devtools timing breakdown, dns connect ssl waiting content download, request sent waiting ttfb, network tab waterfall primer, waterfall basics, dns connect ssl 안 보여요, keep-alive 재사용 timing, waiting이 길어요, waiting ttfb 차이, waterfall vs 304, waterfall vs memory cache, first request vs repeat request waterfall, 같은 origin 반복 요청 waterfall, 처음 배우는데 waterfall 뭐예요

> [!TIP]
> waterfall은 `304`/`memory cache`/`disk cache`를 대체하는 화면이 아니다.
>
> - cache 신호 질문: "body를 어디서 썼나, 서버에 다시 물어봤나"
> - waterfall 질문: "네트워크 시간이 있었다면 어디에 썼나"
>
> 즉 `304`면 먼저 재검증 장면으로 묶고, 그 다음 waterfall에서 `waiting`이 있었는지 본다.
> `from memory cache`/`from disk cache`면 waterfall이 짧거나 비어 보여도 이상한 것이 아니라 local reuse 신호일 수 있다.

## 핵심 개념

Waterfall은 "브라우저가 이 요청에서 시간을 어디에 썼는가"를 줄 단위로 보여 주는 시간표다. 초급자는 각 칸을 서버 내부 단계로 바로 번역하려다 자주 틀린다. 먼저 `dns/connect/ssl`은 요청을 보내기 전 연결 준비, `request sent`는 보내는 순간, `waiting`은 첫 바이트를 기다리는 구간, `content download`는 body를 받는 구간으로만 나눠 두면 된다.

가장 중요한 한 줄은 이것이다. `waiting`이 길다고 해서 곧바로 "서버 코드가 느리다"는 뜻은 아니고, `dns/connect/ssl`이 안 보인다고 해서 계측이 깨진 것도 아니다. 재사용된 연결에서는 앞 구간이 짧거나 아예 사라질 수 있다.

## HTTP 흐름 다음에 붙이는 브리지

[HTTP 요청-응답 기본 흐름](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)을 막 읽었다면, waterfall은 그 흐름을 **시간 칸으로 다시 보는 화면**이라고 생각하면 된다.

- URL과 DNS를 찾는 과정은 `dns`로 보인다
- TCP/TLS로 길을 여는 과정은 `connect`, `ssl`로 보인다
- HTTP 요청을 보낸 뒤 첫 응답이 시작될 때까지는 `waiting`으로 보인다
- 응답 body를 끝까지 받는 과정은 `content download`로 보인다

즉 "브라우저가 무슨 순서로 움직이나"를 배웠다면, 이제는 "그 순서 중 어디서 시간이 많이 쓰였나"를 읽는 단계다.

## 왜 `dns`, `connect`, `ssl`이 갑자기 안 보일까

초급자가 가장 많이 헷갈리는 장면은 첫 요청에서는 `dns -> connect -> ssl`이 보였는데, 다음 요청에서는 그 칸들이 비거나 `0ms`처럼 보이는 경우다. 이때 가장 먼저 떠올릴 기본 해석은 "브라우저가 이미 열어 둔 연결을 다시 썼다"다.

즉 브라우저가 단계를 건너뛴 것이 아니라, **앞선 요청에서 이미 끝낸 연결 준비를 이번 요청이 재사용**한 것이다. HTTPS가 꺼진 것도 아니고 계측이 망가진 것도 아니다. keep-alive나 HTTP/2 연결 재사용 위에서는 자연스러운 모습이다.

| 장면 | 초급자 눈에 보이는 모습 | 먼저 붙일 해석 |
|---|---|---|
| 첫 요청 | `dns`, `connect`, `ssl`이 각각 보임 | 새 연결을 열면서 준비 비용을 냈다 |
| 같은 origin의 다음 요청 | 앞 3칸이 짧거나 없음 | 기존 keep-alive 연결을 재사용했을 수 있다 |
| `waiting`만 상대적으로 큼 | "왜 앞칸이 없지?"보다 "첫 바이트 전 대기만 남았나?"를 본다 | 연결 준비가 아니라 응답 시작 전 대기가 남은 장면일 수 있다 |

이 표를 기억하면 "`dns/connect/ssl`이 사라졌으니 네트워크 분석이 불가능하다"라는 오해를 많이 줄일 수 있다.

### Waterfall에서 재사용 단서 읽는 순서

1. 같은 origin 요청인지 본다. 다른 서버면 새 연결일 가능성이 더 높다.
2. `dns/connect/ssl`이 비었거나 매우 짧으면 "reuse 후보"로 먼저 적는다.
3. 그다음 남아 있는 큰 구간이 `waiting`인지 `content download`인지 본다.
4. 필요하면 `Protocol`, `Connection ID`, `Remote Address`를 같이 봐서 정말 같은 연결 맥락인지 확인한다.

핵심은 waterfall을 "빈칸이 이상한 화면"이 아니라 "이미 치른 연결 준비 비용이 이번 줄에서는 안 보이는 화면"으로 읽는 것이다.

## 같은 origin 첫 요청 vs 반복 요청 비교

같은 브라우저 탭에서 `https://shop.example.com/api/orders`를 두 번 눌렀다고 가정해 보자. 첫 번째는 새 연결을 여는 장면이고, 두 번째는 조금 전 연결을 그대로 재사용한 장면이다.

| 항목 | 첫 요청 | 반복 요청 |
|---|---|---|
| 상황 | 탭을 열고 처음 호출 | 같은 origin에 바로 이어서 다시 호출 |
| `dns` | 보일 수 있음 | 보통 0ms 또는 없음 |
| `connect` | 보일 수 있음 | 보통 0ms 또는 없음 |
| `ssl` | 보일 수 있음 | 보통 0ms 또는 없음 |
| `waiting` | 응답이 느리면 길 수 있음 | 응답이 느리면 여전히 길 수 있음 |
| 먼저 붙일 해석 | 새 연결 비용까지 포함된 요청 | keep-alive 재사용 위의 요청 |

```text
첫 요청
[dns][connect][ssl][request sent][........ waiting ........][download]

반복 요청
                           [request sent][.... waiting ....][download]
```

여기서 중요한 점은 반복 요청의 `waiting`이 짧아진다고 자동으로 보장되지 않는다는 것이다. keep-alive 재사용이 줄여 주는 것은 주로 `dns/connect/ssl` 같은 연결 준비 비용이고, 서버가 첫 바이트를 늦게 주면 반복 요청에서도 `waiting`은 길 수 있다.

초급자용으로 한 줄만 외우면 이렇다. "`같은 origin인데 앞칸만 사라지고 뒤칸은 남아 있으면` 브라우저가 이상한 게 아니라 **이미 열린 연결을 다시 쓴 것**일 가능성을 먼저 본다."

## 한눈에 보기

| Waterfall 구간 | 브라우저가 실제로 하는 일 | 초급자 첫 질문 | 자주 나오는 첫 해석 |
|---|---|---|---|
| `dns` | 도메인을 IP로 찾음 | 이름 찾기가 느린가 | DNS cache miss, resolver 지연 |
| `connect` | TCP 연결을 엶 | 서버까지 붙는 길이 느린가 | 새 연결 비용, 네트워크 경로 지연 |
| `ssl` | TLS handshake 수행 | HTTPS 자물쇠 준비가 느린가 | 새 TLS handshake, 인증서 교환 |
| `request sent` | request header/body를 밀어 넣음 | 보내는 쪽이 막혔나 | 보통 매우 짧음, 큰 upload면 늘 수 있음 |
| `waiting` | 첫 바이트를 기다림 | 응답이 왜 늦게 시작됐나 | TTFB 구간, queue/app/upstream 포함 가능 |
| `content download` | 응답 body를 내려받음 | body 전송이 느린가 | 큰 payload, 느린 클라이언트, buffering |

짧게 외우면 아래 한 줄이다.

```text
연결 준비(dns/connect/ssl) -> 보내기(request sent) -> 첫 바이트 대기(waiting) -> 내려받기(content download)
```

초급자용으로 더 짧게 붙이면 아래처럼 된다.

```text
HTTP 흐름 문서가 "무슨 일이 일어나나"였다면
waterfall 문서는 "어디서 오래 걸렸나"다
```

## cache 신호와 섞지 않는 30초 분리표

이 문서는 timing primer라서, cache 질문은 먼저 짧게 잘라 두는 편이 안전하다.

| 보이는 신호 | 이 문서에서 먼저 읽는 법 | cache 문서로 넘길 질문 |
|---|---|---|
| `from memory cache` | waterfall보다 local reuse 가능성을 먼저 적는다 | 왜 메모리에서 바로 썼는가 |
| `from disk cache` | waterfall이 거의 없어도 자연스럽다고 본다 | 왜 디스크 사본을 재사용했는가 |
| `304` | 재검증 round trip이 있었다고 보고 `waiting` 유무를 본다 | validator, `ETag`, `Last-Modified`를 어떻게 읽는가 |
| `200` + 긴 `waiting` | 첫 바이트 전 대기 장면으로 본다 | cache miss인지 resource 변경인지 |
| `200` + 긴 `content download` | body 다운로드 장면으로 본다 | payload가 왜 큰가, streaming인가 |

한 줄 규칙:

- cache 신호는 "body 출처/재검증 여부"를 설명한다.
- waterfall은 "네트워크 시간이 있었다면 그 시간이 어디에 있었나"를 설명한다.

`304`/`memory cache`/`disk cache`를 실제 row로 분리해서 연습하려면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)를 바로 이어서 보면 된다.

## 상세 분해

### `dns`, `connect`, `ssl`

이 세 칸은 "아직 HTTP 응답이 시작되기 전" 준비 구간이다.

- `dns`가 길면 앱 코드보다 앞에서 이미 시간이 탄다
- `connect`가 길면 새 TCP 연결 비용이나 경로 문제가 먼저 의심된다
- `ssl`이 길면 HTTPS handshake 비용이 들어간다

같은 origin에 이미 살아 있는 연결을 재사용하면 이 구간이 매우 짧거나 보이지 않을 수 있다. 그래서 "이번 줄에 `ssl`이 없네, HTTPS가 아닌가?"라고 읽으면 틀린다.

### `request sent`, `waiting`, `content download`

- `request sent`는 보통 짧고, 큰 업로드나 느린 송신일 때만 눈에 띈다
- `waiting`은 request를 보낸 뒤 첫 바이트를 받을 때까지의 대기다
- `content download`는 응답 body가 실제로 내려오는 시간이다

초급자에게 가장 중요한 구분은 `waiting`과 `content download`다. `waiting`은 응답 시작이 늦은 이유를, `content download`는 응답이 시작된 뒤 끝까지 받는 데 걸린 시간을 보여 준다.

### 처음 볼 때 바로 쓰는 1차 판독

| 눈에 먼저 띄는 구간 | 초급자 1차 해석 | 바로 다음에 붙일 질문 |
|---|---|---|
| `dns`만 유독 길다 | 요청이 서버에 가기 전 이름 찾기부터 늦다 | 첫 요청인가, DNS cache miss인가 |
| `connect`나 `ssl`이 길다 | 새 연결 준비 비용이 크다 | 새 connection인가, HTTPS handshake가 매번 새로 났나 |
| `waiting`이 대부분이다 | 응답 시작 전 대기가 크다 | app compute 말고 queue/proxy/upstream도 같이 후보인가 |
| `content download`가 대부분이다 | 응답 시작은 빨랐고 body 전송이 길다 | 큰 payload인가, streaming인가, 느린 download인가 |

이 표의 목적은 원인 확정이 아니라 **첫 분기 실수 줄이기**다.

## 흔한 오해와 함정

- `waiting`을 서버 코드 실행 시간과 같은 말로 둔다. 실제로는 proxy queue, upstream wait, auth, DB 대기까지 섞일 수 있다.
- `content download`가 길면 서버가 느리다고 단정한다. 큰 파일, 압축, 느린 클라이언트 다운로드도 원인이다.
- `dns/connect/ssl`이 없으면 네트워크 문제가 없다고 생각한다. 재사용된 keep-alive 연결이면 앞 구간이 숨는 것이 자연스럽다.
- `dns/connect/ssl`이 없으면 HTTPS가 꺼졌다고 오해한다. 실제로는 앞선 handshake를 재사용한 것일 수 있다.
- `request sent`가 거의 0ms라서 중요하지 않다고 본다. 업로드 API나 큰 body에서는 여기가 의미를 가질 수 있다.
- Waterfall 한 줄만 보고 전체 incident를 결론 낸다. `Status`, `Protocol`, cache 표기와 같이 봐야 한다.

### 이런 문장으로 보이면 이렇게 고친다

- "`dns`가 길어요, 서버가 느린가 봐요"보다 "`dns` 단계가 길어서 서버 도착 전 지연부터 의심한다"가 더 정확하다.
- "`ssl`이 길어요, 앱 응답이 느리네요"보다 "HTTPS handshake 준비 비용이 길다"가 더 정확하다.
- "`waiting`이 길어요, 컨트롤러가 느려요"보다 "첫 바이트 전 대기라서 proxy/app/upstream을 같이 본다"가 더 정확하다.
- "`content download`가 길어요, DB가 느리네요"보다 "응답 시작 뒤 body 전송이 길다"가 더 정확하다.

## 실무에서 쓰는 모습

예를 들어 `GET /api/orders` 한 줄이 아래처럼 보였다고 하자.

| 구간 | 시간 |
|---|---:|
| `dns` | 2ms |
| `connect` | 8ms |
| `ssl` | 18ms |
| `request sent` | 1ms |
| `waiting` | 420ms |
| `content download` | 12ms |

초급자 첫 판독은 "응답 시작 전 대기(`waiting`)가 대부분"이다. 즉 큰 body 다운로드보다, 첫 바이트가 늦게 나온 이유를 먼저 본다. 여기서 바로 "컨트롤러 코드가 420ms"라고 말하지 말고, proxy queue나 upstream 호출도 함께 후보에 둬야 한다.

반대로 아래처럼 보이면 읽는 축이 달라진다.

| 구간 | 시간 |
|---|---:|
| `dns` | 0ms |
| `connect` | 0ms |
| `ssl` | 0ms |
| `request sent` | 1ms |
| `waiting` | 35ms |
| `content download` | 780ms |

이 줄은 재사용 연결 위에서 body download가 길게 보이는 장면에 가깝다. 응답 시작은 빨랐고, 큰 JSON/파일/streaming 때문에 끝까지 받는 시간이 길 수 있다.

## 더 깊이 가려면

- URL부터 요청 흐름 전체를 다시 잡으려면 [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- Waterfall을 보기 전 Network 탭 첫 판독 순서를 먼저 고정하려면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- `dns/connect/ssl`이 빠진 줄을 keep-alive 재사용 관점으로 다시 묶으려면 [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- cache hit, `304`, `from memory cache`가 waterfall을 어떻게 비워 보이게 하는지 보려면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- DevTools 구간을 curl/운영 지표의 `TTFB`, `TTLB`와 연결하려면 [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- timeout 이름을 `connect`와 `read` 관점으로 다시 붙이려면 [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
- `Protocol`/`Connection ID`/`Remote Address`를 재사용 단서로 함께 읽으려면 [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md)
- Spring 코드 시간과 네트워크 시간을 섞지 않으려면 [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)

## 면접/시니어 질문 미리보기

**Q. DevTools `waiting`은 서버 처리 시간과 같은가요?**  
아니다. 첫 바이트 전까지의 대기이므로 app compute뿐 아니라 queue, proxy, upstream wait도 포함될 수 있다.

**Q. 어떤 요청은 `dns/connect/ssl`이 안 보이는데 왜 그런가요?**  
이미 열린 keep-alive 연결이나 재사용된 세션 위로 요청이 올라가면 새 준비 구간이 거의 없을 수 있다.

**Q. `content download`만 길면 어디부터 의심하나요?**  
큰 응답 body, 느린 다운로드, buffering, streaming cadence를 먼저 본다.

## 한 줄 정리

Browser DevTools waterfall은 `연결 준비 -> 보내기 -> 첫 바이트 대기 -> body 다운로드`의 시간표로 읽고, 특히 `waiting`과 `content download`를 분리해서 봐야 브라우저 지연을 서버 코드 시간과 헷갈리지 않는다.
