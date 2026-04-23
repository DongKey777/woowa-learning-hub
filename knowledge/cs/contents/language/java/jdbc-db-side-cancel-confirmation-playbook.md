# DB-Side Cancel Confirmation Playbook

> 한 줄 요약: `SQLTimeoutException`, `Statement.cancel()`, request timeout 로그는 cancel 의도만 보여 준다. 실제 전파를 확인하려면 같은 JDBC session을 PostgreSQL, MySQL, SQL Server의 서버-side 관측 화면에 매칭해서 "현재 statement가 멈췄는지"와 "transaction/lock cleanup이 남았는지"를 따로 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [Spring JDBC Timeout Propagation Boundaries](./spring-jdbc-timeout-propagation-boundaries.md)
> - [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](./jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)
> - [JDBC Cursor Cleanup on Download Abort](./jdbc-cursor-cleanup-download-abort.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../../database/lock-wait-deadlock-latch-triage-playbook.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

> retrieval-anchor-keywords: DB-side cancel confirmation playbook, JDBC cancel confirmation, cancel propagation evidence, query cancel verification, virtual thread JDBC cancel observability, PostgreSQL cancel confirmation, PostgreSQL `pg_stat_activity` cancel, PostgreSQL `pg_backend_pid`, PostgreSQL `query_canceled` `57014`, PostgreSQL `idle in transaction (aborted)`, PostgreSQL statement timeout verification, MySQL cancel confirmation, MySQL `connection_id()`, MySQL `KILL QUERY`, MySQL `performance_schema.processlist`, MySQL `events_statements_current`, MySQL `events_statements_history_long`, MySQL `ER_QUERY_INTERRUPTED` `1317`, MySQL `ER_QUERY_TIMEOUT` `3024`, SQL Server cancel confirmation, SQL Server `@@SPID`, SQL Server `attention` event, SQL Server query timeout attention, SQL Server `sys.dm_exec_requests`, SQL Server rollback progress, DB session correlation key, statement stopped but transaction open, query cancel vs connection abort

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [먼저 잡을 상관관계 키](#먼저-잡을-상관관계-키)
- [증거 강도 매트릭스](#증거-강도-매트릭스)
- [PostgreSQL](#postgresql)
- [MySQL](#mysql)
- [SQL Server](#sql-server)
- [공통 함정](#공통-함정)
- [운영 체크리스트](#운영-체크리스트)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

cancel 진단에서 가장 흔한 실수는 "애플리케이션이 timeout/cancel을 기록했다"와 "DB 서버가 그 statement를 멈췄다"를 같은 뜻으로 읽는 것이다.

실제로는 세 질문을 따로 확인해야 한다.

- 같은 DB session을 정확히 찾았는가
- 그 session의 **현재 statement** 가 실제로 멈췄는가
- statement는 멈췄더라도 transaction/lock cleanup이 남아 있지는 않은가

virtual thread 환경에서는 이 구분이 더 중요하다.

- request virtual thread는 먼저 끝날 수 있다
- JDBC driver는 cancel request를 보냈다고 말할 수 있다
- 하지만 DB 서버에서는 query가 잠깐 더 돌거나 rollback이 길게 남을 수 있다

그래서 "cancel propagated"라고 말하려면 보통 아래 둘이 함께 필요하다.

- DB의 current-request 화면에서 원래 statement가 더는 실행 중이 아님
- engine-specific cancel/timeout 흔적 또는 rollback/aborted 상태가 확인됨

## 먼저 잡을 상관관계 키

애플리케이션 로그만 보지 말고, 재현 전에 **DB session id**를 먼저 잡아 두는 편이 가장 빠르다.

| 엔진 | 먼저 캡처할 값 | 서버-side 관측 위치 | 왜 중요한가 |
|---|---|---|---|
| PostgreSQL | `select pg_backend_pid();` | `pg_stat_activity.pid` | query cancel 후에도 backend 자체는 살아 있을 수 있어서 `pid`가 가장 안정적이다 |
| MySQL | `select connection_id();` | `performance_schema.processlist.id`, `threads.processlist_id` | `KILL QUERY`는 statement만 끊고 connection은 유지한다 |
| SQL Server | `select @@SPID;` | `sys.dm_exec_requests.session_id`, `sys.dm_exec_sessions.session_id` | client cancel 뒤 같은 session이 `rollback`이나 `sleeping`으로 남을 수 있다 |

가능하면 아래 보조 키도 같이 남기면 좋다.

- JDBC `applicationName` / datasource name
- `host_name` / `client_addr`
- 짧은 SQL comment (`/* traceId=... */`)

핵심은 SQL text만으로 찾지 않는 것이다.  
비슷한 쿼리가 동시에 많이 돌면 cancel 확인도 흔들린다.

## 증거 강도 매트릭스

| 강도 | 무엇을 봤는가 | 이걸로 결론 내려도 되는가 |
|---|---|---|
| 약함 | app timeout, `Future.cancel(true)`, `SQLTimeoutException` | 아니다. cancel 의도만 봤다 |
| 중간 | driver/pool/app이 "cancel sent"를 기록 | 아직 부족하다. dispatch와 effect는 다르다 |
| 강함 | DB current-request 뷰에서 원래 statement가 사라지거나 `rollback`/`aborted` 상태로 전이 | 현재 statement stop은 확인했다 |
| 가장 강함 | 강한 증거 + lock/transaction aftermath까지 확인 | "statement는 멈췄고 cleanup 상태도 이해했다"까지 말할 수 있다 |

실무에서는 마지막 줄까지 봐야 "orphan query가 없다"는 설명이 안전하다.

## PostgreSQL

### 1. 먼저 `pg_stat_activity`에서 같은 backend를 본다

```sql
select pid,
       application_name,
       client_addr,
       state,
       wait_event_type,
       wait_event,
       xact_start,
       query_start,
       state_change,
       left(query, 200) as query
from pg_stat_activity
where pid = :backend_pid;
```

이 화면에서 가장 중요한 컬럼은 다음이다.

- `state`: 지금 `active`인지, `idle`인지, `idle in transaction (aborted)`인지
- `query_start`: 현재 active query 시작 시각, 또는 마지막 query 시작 시각
- `state_change`: 상태가 마지막으로 바뀐 시각

PostgreSQL에서 current activity는 `track_activities`가 켜져 있으면 up-to-date다.  
다만 통계 화면을 트랜잭션 안에서 반복 조회하면 snapshot이 고정될 수 있으니, psql에서는 autocommit 상태로 보거나 필요하면 `pg_stat_clear_snapshot()` 후 다시 보는 편이 안전하다.

### 2. cancel 성공은 "같은 `pid`가 더는 원래 SQL을 실행하지 않는다"로 읽는다

다음이 보이면 current statement cancel은 대체로 성공한 쪽이다.

- 같은 `pid`가 `active`에서 `idle`로 바뀐다
- 같은 `pid`가 `idle in transaction (aborted)`로 바뀐다
- `state_change`가 cancel 시점과 가깝게 갱신된다

특히 `idle in transaction (aborted)`는 중요한 신호다.  
현재 statement는 멈췄지만, explicit transaction 안에서 에러가 났기 때문에 세션이 여전히 `ROLLBACK`을 기다린다는 뜻이다.

추가로 맞춰 볼 수 있는 증거도 있다.

- PostgreSQL의 query cancel 계열 에러 코드는 `57014` (`query_canceled`)다
- `statement_timeout`이 원인이었다면 `log_min_error_statement <= ERROR` 설정에서 timed-out statement가 서버 로그에 남을 수 있다

즉 PostgreSQL에서는 "backend는 살아 있지만 current statement는 중단됨"이 정상적인 cancel 성공 모양일 수 있다.

### 3. dispatch 성공과 effect 성공을 구분한다

PostgreSQL cancel은 별도 cancel connection을 통해 요청이 전달될 수 있다.  
그래서 driver가 "cancel request dispatched"를 성공으로 봐도, 서버가 이미 query를 끝냈거나 너무 늦게 받으면 visible effect가 없을 수 있다.

다음이면 아직 cancel 효과를 못 봤다고 읽는 편이 맞다.

- 같은 `pid`가 계속 `active`
- `query_start`가 그대로고 원래 SQL이 계속 보임
- blocker/waiter 관계가 그대로 남아 있음

lock이 문제였던 쿼리라면 `pg_locks`나 waiter chain도 같이 본다.  
query text만 사라졌다고 바로 "영향 없음"으로 결론 내리면 위험하다.

### 4. backend 자체가 사라졌다면 query cancel보다 connection abort에 가깝다

`Statement.cancel()`이나 statement timeout은 보통 query만 끊고 세션은 남길 수 있다.  
반대로 `pid` 자체가 `pg_stat_activity`에서 사라졌다면 보통은 connection close, network fail-safe, session termination 쪽을 먼저 의심한다.

즉 PostgreSQL에서는 "same pid survives, query no longer active"가 query-level cancel의 전형적인 성공 패턴이다.

## MySQL

### 1. `processlist_id`와 `thread_id`를 같이 매칭한다

```sql
select t.thread_id,
       t.processlist_id,
       p.command,
       p.time,
       p.state,
       left(p.info, 200) as current_sql,
       esc.event_name,
       esc.timer_wait,
       esc.mysql_errno,
       esc.returned_sqlstate,
       esc.message_text
from performance_schema.threads t
join performance_schema.processlist p
  on p.id = t.processlist_id
left join performance_schema.events_statements_current esc
  on esc.thread_id = t.thread_id
where t.processlist_id = :connection_id;
```

여기서 읽을 포인트는 다음이다.

- `processlist_id`: `CONNECTION_ID()`와 매칭되는 connection key
- `command`, `state`, `time`: 지금 statement가 아직 실행 중인지
- `events_statements_current`: 현재 statement 한 건의 SQL text와 경과 정보

이력 확인이 가능하면 아래도 바로 이어서 본다.

```sql
select event_id,
       event_name,
       sql_text,
       mysql_errno,
       returned_sqlstate,
       message_text
from performance_schema.events_statements_history_long
where thread_id = :thread_id
order by event_id desc
limit 5;
```

`events_statements_current`는 현재 statement, `events_statements_history_long`은 끝난 statement 이력 확인에 유용하다.

### 2. MySQL에서 query cancel 성공은 "statement 종료 + connection 생존"이 흔하다

MySQL `KILL QUERY`는 현재 statement만 끊고 connection은 남긴다.  
JDBC cancel/timeout이 driver 내부에서 query kill로 번역되는 경우도 이 패턴으로 관측된다.

보통 아래 조합이면 current statement cancel은 성공 쪽이다.

- 같은 `processlist_id`는 살아 있다
- `COMMAND='Query'` + 원래 SQL이 더는 보이지 않는다
- 다음 poll에서 `COMMAND='Sleep'` 또는 다른 새 command가 보인다
- statement history에 `MYSQL_ERRNO=1317`, `RETURNED_SQLSTATE='70100'`, `MESSAGE_TEXT='Query execution was interrupted'`가 남는다

server-side `MAX_EXECUTION_TIME` 계열 timeout이면 이력의 error code가 `3024`로 남을 수 있다.  
즉 MySQL은 "interrupt/cancel"과 "server-side execution timeout"의 error code를 구분해서 보는 편이 좋다.

### 3. `KILL QUERY`는 즉시 확인 신호가 아니라 kill flag 설정이다

MySQL은 `KILL QUERY`가 확인 응답을 기다리지 않고 반환되고, 실제 abort는 kill flag를 체크하는 지점에서 일어난다.  
그래서 cancel 직후 잠깐은 같은 statement가 여전히 보일 수 있다.

이 구간에서는 아래처럼 읽는다.

- 같은 `processlist_id`가 잠깐 더 보이는 것은 가능하다
- 하지만 `TIME`이 계속 늘고 원래 SQL이 오래 유지되면 cancel 효과가 약하거나 늦은 것이다
- "KILL 쳤다"만 보고 끝내지 말고 current statement disappearance까지 polling해야 한다

### 4. query cancel과 connection kill을 섞지 않는다

MySQL에서는 아래 둘이 완전히 다르다.

- `KILL QUERY`: statement만 종료
- `KILL CONNECTION`: connection 자체 종료

server-side 화면에서도 차이가 난다.

- query cancel이면 `processlist_id`는 그대로 남을 수 있다
- connection kill이나 network fail-safe면 `processlist_id` row 자체가 사라진다

또 한 가지 주의할 점이 있다.  
문서상 `UPDATE`/`DELETE`를 kill했을 때 transactional storage engine이 아닌 경우에는 rollback을 기대하면 안 된다.

즉 MySQL에서는 "statement가 중단됨"과 "변경이 모두 되돌려짐"을 같은 뜻으로 읽지 않는 편이 안전하다.

lock이 문제였던 경우라면 `performance_schema.data_locks`, `data_lock_waits`, 또는 `innodb_trx` 관측까지 이어서 blocker 해제가 되었는지 확인한다.

## SQL Server

### 1. 먼저 `@@SPID` 기준으로 request와 session을 함께 본다

```sql
select s.session_id,
       s.status as session_status,
       s.open_transaction_count,
       s.host_name,
       s.program_name,
       r.request_id,
       r.status as request_status,
       r.command,
       r.wait_type,
       r.blocking_session_id,
       r.percent_complete,
       r.total_elapsed_time,
       t.text as sql_text
from sys.dm_exec_sessions s
left join sys.dm_exec_requests r
  on r.session_id = s.session_id
outer apply sys.dm_exec_sql_text(r.sql_handle) t
where s.session_id = :spid;
```

이때 핵심은 `session`과 `request`를 분리해서 읽는 것이다.

- `sys.dm_exec_requests`: 현재 실행 중인 request가 있는지
- `sys.dm_exec_sessions`: request는 끝났어도 session이 sleeping/open transaction으로 남았는지

### 2. SQL Server에서는 `attention`이 client-side cancel의 핵심 서버 흔적이다

SQL Server 문서 기준으로 query timeout/cancel은 서버에서 `Attention` 이벤트로 관측된다.  
즉 app timeout 로그만이 아니라, 같은 `session_id`에서 `attention`이 잡혔는지를 보면 "서버가 cancel 신호를 봤다"는 근거가 생긴다.

실전에서는 Extended Events에서 아래를 같이 묶어 보는 편이 가장 선명하다.

- `attention`
- `sql_batch_completed`
- `rpc_completed`

같은 `session_id`에서 completed event duration이 app timeout과 거의 맞물리고 직후 `attention`이 보이면, cancel propagation이 실제로 서버에 도달했다고 읽을 수 있다.

### 3. rollback 상태는 cancel 실패가 아니라 cleanup 진행일 수 있다

SQL Server에서 data modification이 cancel되면 request가 바로 사라지는 대신 rollback으로 들어갈 수 있다.

다음이면 cancel은 이미 서버에 반영됐고, 지금은 undo를 하는 중이라고 읽는 편이 맞다.

- `sys.dm_exec_requests.status = 'rollback'`
- `command = 'ROLLBACK'`
- `percent_complete`가 보인다

즉 request가 안 사라졌다고 바로 "cancel 실패"라고 말하면 안 된다.  
오히려 rollback progress가 보이면 current statement stop은 이미 성공했고 cleanup만 남은 것이다.

필요하면 server-side 수동 정리에서도 `KILL <spid> WITH STATUSONLY`로 rollback progress를 읽을 수 있다.

### 4. request는 멈췄는데 transaction은 열려 있을 수 있다

SQL Server 문서에서 특히 중요한 함정은 이것이다.

- query timeout/cancel은 current query와 batch를 끝낼 수 있다
- 하지만 explicit transaction을 자동으로 rollback하지는 않는다

그래서 다음 패턴이 나올 수 있다.

- `sys.dm_exec_requests`에서는 현재 request가 사라짐
- `sys.dm_exec_sessions`에서는 같은 session이 `sleeping`
- `open_transaction_count > 0`
- 락이 계속 남아 blocker가 유지됨

이 경우는 "cancel이 서버에 전파되지 않았다"가 아니라, "statement는 멈췄지만 application이 transaction cleanup을 안 했다"가 더 정확하다.

### 5. 아직 실행 중인 원래 request가 남아 있으면 미전파 쪽이다

반대로 아래면 cancel 성공을 말하기 어렵다.

- 같은 `session_id`의 request가 여전히 `running`/`runnable`/`suspended`
- `total_elapsed_time`가 계속 증가
- 같은 SQL text가 계속 current request로 보임
- `attention` 흔적도 없다

즉 SQL Server에서는 `attention`, request disappearance, rollback progress, open transaction 상태를 한 묶음으로 봐야 한다.

## 공통 함정

### 1. "request가 끝났다"와 "transaction이 정리됐다"를 섞지 않는다

세 엔진 모두에서 current statement stop과 transaction cleanup은 별개일 수 있다.

- PostgreSQL: `idle in transaction (aborted)`
- MySQL: connection은 남고 lock/transaction 정리가 별도로 남을 수 있음
- SQL Server: `sleeping` + open transaction count

### 2. query-level cancel과 connection-level abort를 구분한다

서버 화면에서 session 자체가 사라졌다면 보통 query cancel보다 connection close, network timeout, abort, kill connection 쪽에 가깝다.

즉 "DB에서 안 보인다"만으로는 query-level cancel 성공이라고 단정하면 안 된다.

### 3. current 화면과 history 화면을 섞어 읽는다

cancel 성공 직후에는 current request가 사라져도, 나중에 원인을 설명하려면 history/error/event가 필요하다.

- PostgreSQL: `pg_stat_activity` + `57014`/server log
- MySQL: `events_statements_current` + `events_statements_history_long`
- SQL Server: DMV + Extended Events `attention`

### 4. 관측 기능이 꺼져 있으면 "증거 없음"이지 "cancel 없음"이 아니다

다음이 빠져 있으면 해석력이 급격히 떨어진다.

- PostgreSQL `track_activities`
- MySQL Performance Schema statement consumers/history
- SQL Server Extended Events session

운영에서 자주 놓치는 부분은 "cancel은 됐는데 관측이 비어 있다"가 아니라 "관측이 비어서 cancel도 없었다고 착각한다"는 점이다.

## 운영 체크리스트

1. 재현 전에 DB session key를 캡처한다.  
   PostgreSQL `pg_backend_pid()`, MySQL `connection_id()`, SQL Server `@@SPID`.
2. current request 화면에서 실제로 그 statement가 돌고 있는지 먼저 확인한다.
3. timeout / `Statement.cancel()` / client disconnect를 발생시킨다.
4. app 로그 대신 DB 화면을 poll한다.  
   current statement disappearance, `rollback`, `aborted`, `attention`, history error code를 본다.
5. current statement가 멈춘 뒤에도 transaction/lock cleanup이 남았는지 확인한다.
6. session이 살아남은 경우는 실패로 단정하지 말고, query-level cancel인지 connection-level abort인지 구분한다.

## 꼬리질문

> Q: `SQLTimeoutException`만 봤으면 cancel propagated라고 말해도 되나요?
> 핵심: 아니다. DB에서 같은 session의 current statement가 멈췄는지까지 확인해야 한다.

> Q: cancel 성공인데 session이 아직 살아 있으면 이상한가요?
> 핵심: 아니다. PostgreSQL backend, MySQL connection, SQL Server session은 query cancel 후에도 남을 수 있다.

> Q: rollback progress가 보이면 cancel 실패인가요?
> 핵심: 보통 반대다. current statement는 이미 중단됐고, 서버가 undo를 진행 중인 것이다.

> Q: 왜 lock/transaction cleanup까지 봐야 하나요?
> 핵심: statement만 멈추고 transaction이 열린 채 남으면 blocker와 orphan work가 계속 남을 수 있기 때문이다.

## 한 줄 정리

cancel 진단은 "app이 포기했다"가 아니라 "같은 DB session에서 원래 statement가 멈췄고, 그 뒤의 rollback/lock 상태까지 설명된다"까지 확인해야 끝난다.
