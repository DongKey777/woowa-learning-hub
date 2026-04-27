"""Regression tests for lightweight CS RAG signal detection.

These tests mostly stay dependency-free and focus on the vocabulary that
drives query expansion plus fallback bucket keys. A small cheap-mode
search fixture also locks beginner colloquial shortforms to their primer
docs so ranking regressions surface here, not only in broader search
suites.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer, searcher, signal_rules


def _chunk(
    doc_id: str,
    path: str,
    title: str,
    category: str,
    section_title: str,
    body: str,
) -> corpus_loader.CorpusChunk:
    return corpus_loader.CorpusChunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}#0",
        path=path,
        title=title,
        category=category,
        section_title=section_title,
        section_path=[title, section_title],
        body=body,
        char_len=len(body),
    )


_COLLOQUIAL_SHORTFORM_SEARCH_FIXTURES = [
    _chunk(
        "query-model-primer",
        "contents/software-engineering/query-model-separation-read-heavy-apis.md",
        "Query Model Separation for Read-Heavy APIs",
        "software-engineering",
        "List search filter sort beginner guide",
        (
            "query model separation beginner primer explains list search filter sort "
            "query conditions, browser filter state, local sort state, and why list "
            "behavior can change before blaming stale read paths."
        ),
    ),
    _chunk(
        "read-model-stale",
        "contents/design-pattern/read-model-staleness-read-your-writes.md",
        "Read Model Staleness and Read-Your-Writes",
        "design-pattern",
        "Stale read beginner symptom map",
        (
            "read model staleness explains stale read, projection lag, read your "
            "writes, replica lag, and saved but still old data after write."
        ),
    ),
    _chunk(
        "read-after-write-primer",
        "contents/database/replica-lag-read-after-write-strategies.md",
        "Replica Lag and Read-After-Write Strategies",
        "database",
        "Cache vs replica beginner primer",
        (
            "read-after-write beginner primer explains cache vs replica lag, how to "
            "tell application cache vs read replica delay after a save, read-after-write "
            "strategies, and when primary fallback helps just-saved-but-old-data symptoms."
        ),
    ),
    _chunk(
        "spring-primer",
        "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
        "Spring Request Pipeline and Bean Container Foundations Primer",
        "spring",
        "DispatcherServlet big picture",
        (
            "dispatcherservlet beginner primer explains dispatcher servlet, request pipeline, "
            "bean container foundation, controller service repository roles, and front "
            "controller basics for first-time Spring learners."
        ),
    ),
    _chunk(
        "spring-deep",
        "contents/spring/spring-mvc-handlerexecutionchain-interceptor-ordering.md",
        "Spring MVC HandlerExecutionChain and Interceptor Ordering",
        "spring",
        "Advanced interceptor ordering",
        (
            "dispatcherservlet advanced deep dive covers handlerexecutionchain, interceptor "
            "ordering, adapter resolution, async dispatch, and mvc execution ordering."
        ),
    ),
    _chunk(
        "tx-primer",
        "contents/spring/spring-transactional-basics.md",
        "Spring Transactional Basics",
        "spring",
        "Transactional annotation basics",
        (
            "spring transactional basics covers transactional annotation basics, spring proxy "
            "transaction, unchecked exception rollback, checked exception rollback, and self "
            "invocation transactional behavior for beginners."
        ),
    ),
    _chunk(
        "tx-deep",
        "contents/spring/spring-transaction-propagation-deep-dive.md",
        "Spring Transaction Propagation Deep Dive",
        "spring",
        "Propagation edge cases",
        (
            "transactional deep dive covers propagation, isolation, requires new, nested "
            "transactions, remote call boundaries, and advanced rollback coordination."
        ),
    ),
    _chunk(
        "ioc-primer",
        "contents/spring/spring-ioc-di-basics.md",
        "Spring IoC and DI Basics",
        "spring",
        "IoC vs DI beginner guide",
        (
            "spring ioc di basics explains di vs ioc, dependency injection, inversion of "
            "control, bean wiring, and object graph ownership in simple beginner terms."
        ),
    ),
    _chunk(
        "ioc-deep",
        "contents/spring/spring-bean-definition-overriding-semantics.md",
        "Spring Bean Definition Overriding Semantics",
        "spring",
        "Override semantics",
        (
            "bean definition overriding semantics covers override conflicts, bean name "
            "collisions, context merge rules, and configuration precedence."
        ),
    ),
    _chunk(
        "keepalive-primer",
        "contents/network/keepalive-connection-reuse-basics.md",
        "Keep-Alive and Connection Reuse Basics",
        "network",
        "HTTP keep-alive basics",
        (
            "keepalive connection reuse basics explains http keep-alive, persistent "
            "connection, connection reuse, idle timeout, and why TCP connections are reused."
        ),
    ),
    _chunk(
        "keepalive-deep",
        "contents/network/http2-http3-connection-reuse-coalescing.md",
        "HTTP/2 HTTP/3 Connection Reuse and Coalescing",
        "network",
        "Coalescing deep dive",
        (
            "http2 http3 connection reuse coalescing covers authority coalescing, origin "
            "frame, alt-svc, 421 retry, and cross-origin pooling policy."
        ),
    ),
    _chunk(
        "pool-primer",
        "contents/database/connection-pool-basics.md",
        "Connection Pool Basics",
        "database",
        "Why connection pools exist",
        (
            "connection pool basics explains db connection pool beginner concepts, db "
            "connection reuse, hikari cp beginner, pool size basics, and pool exhaustion."
        ),
    ),
    _chunk(
        "pool-deep",
        "contents/database/transaction-locking-connection-pool-primer.md",
        "Transaction Locking and Connection Pool Primer",
        "database",
        "Operational lock and pool interplay",
        (
            "transaction locking connection pool primer covers long transaction, lock wait "
            "timeout, pool starvation, retry storm, connection leak triage, and operational "
            "recovery."
        ),
    ),
    _chunk(
        "tx-isolation-primer",
        "contents/database/transaction-isolation-basics.md",
        "Transaction Isolation Basics",
        "database",
        "MVCC isolation beginner guide",
        (
            "transaction isolation basics beginner primer explains mvcc, isolation level, "
            "read committed, repeatable read, phantom read, optimistic lock, "
            "pessimistic lock, and a simple mental model before internals."
        ),
    ),
    _chunk(
        "tx-mvcc-internals-deep",
        "contents/database/mvcc-read-view-undo-chain-internals.md",
        "MVCC Read View and Undo Chain Internals",
        "database",
        "MVCC internals deep dive",
        (
            "mvcc deep dive covers read view, undo chain, undo log, history list, "
            "version chain, purge lag, and storage-engine internals."
        ),
    ),
    _chunk(
        "auth-primer",
        "contents/security/authentication-authorization-session-foundations.md",
        "Authentication Authorization Session Foundations",
        "security",
        "Authentication and authorization foundations",
        (
            "authentication authorization session foundations explains login flow, "
            "authentication, authorization, session vs jwt, and stateful session vs "
            "stateless token differences for beginners."
        ),
    ),
    _chunk(
        "session-cookie-jwt-primer",
        "contents/security/session-cookie-jwt-basics.md",
        "세션 쿠키 JWT 기초",
        "security",
        "Session cookie JWT basics",
        (
            "session cookie jwt basics explains cookie session jwt browser flow, http "
            "stateless login state, jsessionid, server session vs jwt, login state "
            "persistence, why login stays, stay signed in, browser remembers my login, "
            "keep me signed in, and token based authentication for beginners."
        ),
    ),
    _chunk(
        "http-state-session-cache-primer",
        "contents/network/http-state-session-cache.md",
        "HTTP State Session Cache Primer",
        "network",
        "HTTP stateless basics",
        (
            "http state session cache primer explains http stateless request response, "
            "cookie, session, cache, browser cache, server cache, and why http itself "
            "does not remember prior requests."
        ),
    ),
    _chunk(
        "auth-deep",
        "contents/security/jwt-deep-dive.md",
        "JWT Deep Dive",
        "security",
        "JWT validation details",
        (
            "jwt deep dive covers signature verification, kid lookup, issuer audience "
            "validation, jwks rotation, and token validation edge cases."
        ),
    ),
    _chunk(
        "cf-cancel-primer",
        "knowledge/cs/contents/language/java/completablefuture-cancellation-semantics.md",
        "CompletableFuture Cancellation Semantics",
        "language",
        "Cancellation basics",
        (
            "completablefuture cancellation semantics explains cancel, cancellationexception, "
            "cancel does not stop work, mayinterruptifrunning expectation, interrupt vs "
            "cancellation, cooperative cancellation, dependent stage propagation, and "
            "timeout vs cancel basics for learners."
        ),
    ),
    _chunk(
        "cf-pool-deep",
        "knowledge/cs/contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
        "CompletableFuture Execution Model and Common Pool Pitfalls",
        "language",
        "Common pool hazards",
        (
            "completablefuture execution model covers common pool, default executor, "
            "forkjoinpool, async stage, blocking stage, thread hopping, work stealing, "
            "and starvation hazards."
        ),
    ),
]


class CsRagSignalRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmpdir.name)
        sqlite_path, dense_path, manifest_path = indexer._paths(cls.tmp)
        conn = indexer._open_sqlite(sqlite_path)
        try:
            indexer._insert_chunks(conn, _COLLOQUIAL_SHORTFORM_SEARCH_FIXTURES)
        finally:
            conn.close()
        manifest_path.write_text(
            json.dumps(
                {
                    "index_version": indexer.INDEX_VERSION,
                    "embed_model": "fixture",
                    "embed_dim": 0,
                    "row_count": len(_COLLOQUIAL_SHORTFORM_SEARCH_FIXTURES),
                    "corpus_hash": "fixture",
                    "corpus_root": "fixture",
                }
            ),
            encoding="utf-8",
        )
        dense_path.touch()
        os.environ["WOOWA_RAG_NO_RERANK"] = "1"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()
        os.environ.pop("WOOWA_RAG_NO_RERANK", None)

    def _search(self, prompt: str, *, top_k: int = 4) -> list[dict]:
        return searcher.search(
            prompt,
            learning_points=[],
            mode="cheap",
            index_root=self.tmp,
            top_k=top_k,
        )

    def assert_path_rank_at_most(
        self,
        hits: list[dict],
        path: str,
        max_rank: int,
    ) -> None:
        paths = [hit["path"] for hit in hits]
        self.assertIn(path, paths, f"expected {path} in hits {paths}")
        rank = paths.index(path) + 1
        self.assertLessEqual(
            rank,
            max_rank,
            f"expected {path} within top-{max_rank}, got rank #{rank} in {paths}",
        )

    def assert_ranks_ahead(
        self,
        hits: list[dict],
        winner: str,
        loser: str,
    ) -> None:
        paths = [hit["path"] for hit in hits]
        self.assertIn(winner, paths, f"missing winner {winner} in {paths}")
        self.assertIn(loser, paths, f"missing loser {loser} in {paths}")
        self.assertLess(paths.index(winner), paths.index(loser), paths)

    def test_java_basics_terms_map_to_language_signal(self) -> None:
        prompt = "자바 기본 문법, 데이터 타입, 바이트코드/JVM 실행 흐름을 정리해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_language_runtime",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java language", expanded)
        self.assertIn("bytecode", expanded)
        self.assertIn("jvm", expanded)

    def test_java_concurrency_terms_map_to_language_signal(self) -> None:
        prompt = "Java ExecutorService Future CompletableFuture CountDownLatch 정리"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_concurrency_utilities",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java concurrency utilities", expanded)
        self.assertIn("executorservice", expanded)
        self.assertIn("completablefuture", expanded)

    def test_introductory_java_runtime_query_adds_primer_vocabulary(self) -> None:
        prompt = "자바 런타임을 처음 배우는데 classloader JIT GC JMM 차이를 큰 그림으로 먼저 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_language_runtime",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java runtime overview", expanded)
        self.assertIn("bytecode execution flow", expanded)
        self.assertIn("heap stack metaspace", expanded)

    def test_introductory_jvm_thread_stack_query_suppresses_generic_concurrency_noise(self) -> None:
        prompt = "Java runtime 입문인데 JVM thread stack heap 차이를 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_language_runtime",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_language_runtime", tags)
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("jvm", expanded)

    def test_java_runtime_overview_query_suppresses_generic_network_and_resource_noise(
        self,
    ) -> None:
        prompt = "Java NIO socket close timeout 같은 OS/network 말고 JVM runtime 큰 그림 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_language_runtime",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_language_runtime", tags)
        self.assertNotIn("network_and_reliability", tags)
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java runtime overview", expanded)
        self.assertIn("jvm", expanded)

    def test_introductory_java_concurrency_query_suppresses_executorservice_false_positives(self) -> None:
        prompt = (
            "Java 동시성을 처음 배우는데 queue rejection policy 같은 튜닝보다 ExecutorService "
            "Future CompletableFuture CountDownLatch 를 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_concurrency_utilities",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_concurrency_utilities", tags)
        self.assertNotIn("concurrency", tags)
        self.assertNotIn("java_language_runtime", tags)
        self.assertNotIn("layer_responsibility", tags)
        self.assertNotIn("db_modeling", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java concurrency overview", expanded)
        self.assertIn("thread pool basics", expanded)
        self.assertIn("coordination primitives", expanded)
        self.assertNotIn("jvm", expanded)
        self.assertNotIn("service layer", expanded)
        self.assertNotIn("schema design", expanded)

    def test_beginner_future_completablefuture_query_stays_overview_even_with_common_pool_hint(
        self,
    ) -> None:
        prompt = (
            "Future CompletableFuture 를 처음 배우는데 common pool 위험 얘기 전에 큰 그림부터 "
            "설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_concurrency_utilities",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_concurrency_utilities", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java concurrency overview", expanded)
        self.assertIn("future composition basics", expanded)
        self.assertNotIn("default executor", expanded)
        self.assertNotIn("forkjoinpool", expanded)
        self.assertNotIn("blocking stage", expanded)

    def test_fixture_java_future_intro_prompt_adds_overview_bridge_terms(self) -> None:
        prompt = (
            "Java 동시성을 처음 배우는데 Future CompletableFuture 와 ExecutorService "
            "Callable CountDownLatch 관계를 큰 그림부터 정리해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_concurrency_utilities",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("java concurrency utilities overview", expanded)
        self.assertIn("executorservice callable future overview", expanded)
        self.assertIn("future vs completablefuture basics", expanded)
        self.assertIn("countdownlatch coordination basics", expanded)

    def test_completablefuture_common_pool_query_adds_execution_model_vocabulary(self) -> None:
        prompt = (
            "CompletableFuture common pool default executor blocking stage thread hopping "
            "starvation 을 어떻게 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_concurrency_utilities",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_concurrency_utilities", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("common pool", expanded)
        self.assertIn("default executor", expanded)
        self.assertIn("forkjoinpool", expanded)
        self.assertIn("blocking stage", expanded)
        self.assertIn("thread hopping", expanded)

    def test_completablefuture_cancellation_prompt_routes_to_explicit_cancellation_signal(
        self,
    ) -> None:
        prompt = (
            "CompletableFuture cancellation semantics 를 처음 배우는데 cancel(true) "
            "mayInterruptIfRunning CancellationException interrupt 차이를 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_completablefuture_cancellation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_completablefuture_cancellation", tags)
        self.assertNotIn("java_concurrency_utilities", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("completablefuture cancellation basics", expanded)
        self.assertIn("cancel does not stop work", expanded)
        self.assertIn("interrupt vs cancellation", expanded)
        self.assertNotIn("common pool", expanded)
        self.assertNotIn("forkjoinpool", expanded)
        self.assertNotIn("blocking stage", expanded)

    def test_completablefuture_cancellation_and_common_pool_prompts_split_search_ranking(
        self,
    ) -> None:
        cancellation_prompt = (
            "CompletableFuture cancellation semantics 를 처음 배우는데 cancel(true) "
            "mayInterruptIfRunning CancellationException interrupt 차이를 큰 그림부터 설명해줘"
        )
        common_pool_prompt = (
            "CompletableFuture common pool default executor blocking stage thread hopping "
            "starvation 을 어떻게 이해해야 해?"
        )

        cancellation_hits = self._search(cancellation_prompt)
        self.assert_path_rank_at_most(
            cancellation_hits,
            "knowledge/cs/contents/language/java/completablefuture-cancellation-semantics.md",
            1,
        )
        self.assert_ranks_ahead(
            cancellation_hits,
            "knowledge/cs/contents/language/java/completablefuture-cancellation-semantics.md",
            "knowledge/cs/contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
        )

        common_pool_hits = self._search(common_pool_prompt)
        self.assert_path_rank_at_most(
            common_pool_hits,
            "knowledge/cs/contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
            1,
        )
        self.assert_ranks_ahead(
            common_pool_hits,
            "knowledge/cs/contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
            "knowledge/cs/contents/language/java/completablefuture-cancellation-semantics.md",
        )

    def test_executor_tuning_query_stays_in_java_concurrency_family(self) -> None:
        prompt = "executor sizing queue capacity rejection policy worker saturation thread pool tuning 을 어떻게 잡아?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_concurrency_utilities",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_concurrency_utilities", tags)
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("executor sizing", expanded)
        self.assertIn("queue capacity", expanded)
        self.assertIn("thread pool tuning", expanded)
        self.assertNotIn("connection pool", expanded)

    def test_projection_symptom_only_list_refresh_lag_query_maps_to_primer_signal(self) -> None:
        prompt = (
            "저장했는데 목록 새로고침이 느리고 이전 화면 상태가 한동안 남아 있어. "
            "왜 이런지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("list refresh lag after write", expanded)
        self.assertIn("old screen state after save", expanded)

    def test_projection_symptom_only_old_screen_state_query_adds_primer_vocabulary(self) -> None:
        prompt = (
            "처음 배우는 사람 기준으로 저장 직후 list refresh lag 때문에 old screen state 가 "
            "남아 보여. 운영 문서 전에 어떤 기초 개념부터 보면 돼?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertIn("list refresh lag after write", expanded)
        self.assertIn("old screen state after save", expanded)

    def test_fully_korean_projection_guardrail_compare_prompt_adds_primer_and_cutover_terms(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 최신성을 처음 배우는데 예전 값이 보여서 헷갈려. 방금 쓴 값 읽기 보장 "
            "설명이랑 전환 안전 구간 안내를 같이 비교해서 보고 싶어. 입문자는 운영 안전 "
            "규칙 전에 어떤 기초 설명부터 봐야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("freshness guardrail", expanded)

    def test_fully_korean_projection_rollback_distinguish_prompt_keeps_projection_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 최신성을 처음 배우는데 롤백 윈도우랑 트랜잭션 롤백을 어떻게 구분해야 "
            "해? 왜 예전 값이 보이고 방금 쓴 값 읽기 보장이 흔들리는지 큰 그림부터 "
            "설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertNotIn("cqrs survey routing", expanded)

    def test_projection_symptom_only_no_jargon_list_stuck_query_maps_to_primer_signal(self) -> None:
        prompt = "저장하고 나서 목록이 바로 안 바뀌고 예전 화면이 잠깐 보여. 왜 이런지 큰 그림부터 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertIn("old screen state after save", expanded)

    def test_projection_symptom_only_no_jargon_delayed_screen_query_adds_primer_vocabulary(
        self,
    ) -> None:
        prompt = (
            "수정 저장했는데 새로고침 전까지 이전 상태가 보이고 화면 반영이 한참 늦어. "
            "입문자 기준으로 무슨 개념부터 보면 돼?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("list refresh lag after write", expanded)
        self.assertIn("old screen state after save", expanded)

    def test_projection_cached_screen_after_save_query_keeps_primer_signal_and_strips_cache_noise(
        self,
    ) -> None:
        prompt = (
            "저장했는데 화면이 캐시된 것처럼 안 바뀌어. 처음 배우는 사람 기준으로 왜 "
            "이런지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertIn("old screen state after save", expanded)
        self.assertNotIn("cache", expanded)
        self.assertNotIn("캐시", expanded)

    def test_projection_mobile_screen_delay_query_maps_to_primer_signal(self) -> None:
        prompt = (
            "모바일에서 수정 저장했는데 화면 반영이 늦고 예전 목록이 한동안 남아 있어. "
            "처음 배우는 사람 기준으로 왜 이런지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("list refresh lag after write", expanded)
        self.assertIn("old screen state after save", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_swipe_refresh_lag_query_maps_to_primer_signal(self) -> None:
        prompt = (
            "모바일에서 저장은 됐는데 당겨서 새로고침해야 새 값이 보여. "
            "swipe refresh 없이는 리스트가 늦게 갱신돼. 입문자 기준으로 먼저 어떤 개념을 보면 돼?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read-after-write", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_app_screen_delay_variant_maps_to_primer_signal(self) -> None:
        prompt = "앱에서 수정했는데 화면이 늦게 바뀌고 예전 목록이 남아 있어. 왜 이래?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old screen state after save", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_screen_update_delay_symptom_only_variant_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = "모바일에서 화면 업데이트가 늦고 목록이 한참 뒤에 바뀌어. 왜 이런 거야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old screen state after save", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_screen_update_delay_jiyeon_variant_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = "모바일에서 저장했는데 화면 업데이트 지연 때문에 예전 목록이 남아 있어. 왜 이래?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old screen state after save", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_pull_to_refresh_value_variant_maps_to_primer_signal(self) -> None:
        prompt = "앱에서 pull to refresh 해야 바뀐 값이 보여. 리스트 갱신이 늦어."

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_swipe_refresh_once_variant_maps_to_primer_signal(self) -> None:
        prompt = "앱에서 당겨서 새로고침 한 번 해야 최신 화면으로 바뀌어. 왜 이렇게 늦어?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_swipe_refresh_lag_symptom_only_variant_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = "앱에서 스와이프 새로고침해야 목록이 갱신돼. 왜 바로 안 보여?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_swipe_refresh_transliterated_variant_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = "모바일에서 스와이프 리프레시 해야 화면이 따라와. 왜 바로 반영 안 돼?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_swipe_refresh_after_gesture_variant_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = "앱에서 스와이프 새로고침하고 나서야 바뀐 값이 보여. 왜 바로 안 보여?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_mobile_swipe_refresh_pull_down_variant_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = "앱에서 새로고침 쓸어내리고 나서야 새 값이 떠. 왜 바로 반영 안 돼?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("swipe refresh needed to see new value", expanded)
        self.assertIn("mobile screen update delay after save", expanded)

    def test_projection_detail_updated_but_list_card_stale_query_maps_to_primer_signal(
        self,
    ) -> None:
        prompt = (
            "상세는 바뀌었는데 목록 카드만 예전 값이 보여. 처음 배우는 사람 기준으로 왜 "
            "이런지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("cache", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("list refresh lag after write", expanded)
        self.assertIn("detail view updated but list stale", expanded)
        self.assertIn("상세는 바뀌었는데 목록 카드만 예전 값", expanded)

    def test_projection_detail_screen_updated_but_list_card_old_value_variant_keeps_primer_first(
        self,
    ) -> None:
        prompt = (
            "상세 화면은 바뀌었는데 리스트 카드만 이전 값이 남아 있어. 저장 직후 왜 "
            "이런지 입문자 기준으로 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("cache", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertIn("detail page changed but list card stale", expanded)

    def test_projection_detail_updated_but_list_old_value_variant_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "상세는 바뀌었는데 목록은 예전 값이야. 처음 배우는 사람 기준으로 왜 이런지 "
            "큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("cache", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertIn("detail view updated but list stale", expanded)
        self.assertIn("상세는 바뀌었는데 목록 카드만 예전 값", expanded)

    def test_projection_delete_visibility_list_prompt_maps_to_primer_signal(self) -> None:
        prompt = (
            "삭제는 성공했는데 목록에 계속 남아 보여. 처음 배우는 사람 기준으로 왜 이런지 "
            "큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertIn("deleted item still visible after delete", expanded)
        self.assertIn("deleted item still appears in list results", expanded)

    def test_projection_delete_visibility_search_prompt_adds_beginner_freshness_vocabulary(
        self,
    ) -> None:
        prompt = (
            "삭제했는데 검색 결과나 목록에 아직 남아 있어. 입문자 기준으로 왜 이럴 수 "
            "있는지 먼저 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("deleted item still visible after delete", expanded)
        self.assertIn("deleted item still appears in search results", expanded)

    def test_introductory_virtual_thread_query_prefers_loom_primer_signal(self) -> None:
        prompt = (
            "Project Loom virtual threads 를 처음 배우는데 blocking I/O, carrier thread, "
            "pinning 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_virtual_threads_loom",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_virtual_threads_loom", tags)
        self.assertNotIn("concurrency", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("virtual threads basics", expanded)
        self.assertIn("loom overview", expanded)
        self.assertIn("blocking i/o with virtual threads", expanded)
        self.assertIn("thread per request with loom", expanded)
        self.assertNotIn("lock", expanded)
        self.assertNotIn("jvm", expanded)

    def test_introductory_virtual_thread_contrast_prompt_suppresses_generic_network_noise(
        self,
    ) -> None:
        prompt = (
            "자바 virtual thread 를 처음 배우는데 thread pool timeout connection budget 말고 "
            "개념만 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_virtual_threads_loom",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_virtual_threads_loom", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("virtual threads basics", expanded)
        self.assertIn("loom overview", expanded)

    def test_java_labeled_virtual_thread_intro_query_suppresses_runtime_noise(self) -> None:
        prompt = "Java 21 virtual threads / Project Loom 입문 설명 부탁해"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_virtual_threads_loom",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_virtual_threads_loom", tags)
        self.assertNotIn("java_language_runtime", tags)
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("project loom", expanded)
        self.assertIn("virtual threads basics", expanded)
        self.assertNotIn("bytecode", expanded)
        self.assertNotIn("jvm", expanded)

    def test_virtual_thread_migration_query_adds_operational_terms_without_primer_bias(self) -> None:
        prompt = "virtual thread migration 에서 pinning ThreadLocal pool boundary 를 어떻게 점검해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_virtual_threads_loom",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("virtual thread migration", expanded)
        self.assertIn("threadlocal migration", expanded)
        self.assertIn("pool boundary strategy", expanded)
        self.assertNotIn("loom overview", expanded)
        self.assertNotIn("virtual threads basics", expanded)

    def test_classloader_leak_query_routes_to_java_runtime_signal(self) -> None:
        prompt = (
            "metaspace leak thread context class loader static cache pinning hot redeploy "
            "leak triage 를 어떻게 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_language_runtime",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("java_language_runtime", tags)
        self.assertNotIn("concurrency", tags)
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("classloader", expanded)
        self.assertIn("metaspace leak", expanded)
        self.assertIn("thread context class loader", expanded)

    def test_jit_warmup_query_routes_to_java_runtime_signal(self) -> None:
        prompt = (
            "tiered compilation inlining code cache profile pollution deopt trigger 를 "
            "JIT warmup 관점에서 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_language_runtime",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("jit warmup", expanded)
        self.assertIn("tiered compilation", expanded)
        self.assertIn("deoptimization", expanded)

    def test_applied_data_structures_terms_map_to_data_structure_signal(self) -> None:
        prompt = "ring buffer bloom filter hyperloglog trie 같은 응용 자료 구조"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "applied_data_structures",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("applied data structures", expanded)
        self.assertIn("data structure overview", expanded)

    def test_jwks_rotation_terms_map_to_rotation_signal(self) -> None:
        prompt = "JWKS key rotation 때 kid rollover 와 cache invalidation 을 어떻게 안전하게 운영해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_key_rotation_rollover",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("key rotation", expanded)
        self.assertIn("kid rollover", expanded)
        self.assertIn("cache invalidation", expanded)

    def test_hyphenated_jwks_rotation_terms_still_map_to_rotation_signal(self) -> None:
        prompt = (
            "JWKS key-rotation 때 kid-rollover 와 cache-invalidation 을 어떻게 안전하게 운영해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_key_rotation_rollover",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("key rotation", expanded)
        self.assertIn("kid rollover", expanded)
        self.assertIn("cache invalidation", expanded)

    def test_key_rotation_runbook_terms_map_to_runbook_signal(self) -> None:
        prompt = "key rotation runbook 에서 dual validation grace window revoke old key 순서를 어떻게 잡아?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_key_rotation_runbook",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("rotation runbook", expanded)
        self.assertIn("dual validation", expanded)
        self.assertIn("revoke old key", expanded)

    def test_hyphenated_key_rotation_runbook_terms_still_map_to_runbook_signal(self) -> None:
        prompt = (
            "key-rotation runbook 에서 dual-validation grace-window revoke-old-key 순서를 "
            "어떻게 잡아?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_key_rotation_runbook",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("rotation runbook", expanded)
        self.assertIn("dual validation", expanded)
        self.assertIn("revoke old key", expanded)

    def test_key_rotation_rollback_terms_promote_runbook_signal(self) -> None:
        prompt = "key rotation rollback plan 을 runbook 기준으로 어떻게 잡아야 해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_key_rotation_runbook",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("security_key_rotation_runbook", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("rotation runbook", expanded)
        self.assertIn("key rotation rollback", expanded)
        self.assertIn("rollback plan", expanded)

    def test_jwks_recovery_terms_map_to_recovery_signal(self) -> None:
        prompt = "kid miss storm, stale-if-error, fail-closed 로 JWKS recovery ladder 를 어떻게 운영해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_jwks_recovery",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("fail-open", expanded)
        self.assertIn("jwks outage recovery", expanded)
        self.assertIn("stale-if-error", expanded)
        self.assertIn("recovery ladder", expanded)
        self.assertNotIn("connection pool", expanded)
        self.assertNotIn("close", expanded)

    def test_jwks_fail_closed_terms_do_not_activate_resource_lifecycle_signal(self) -> None:
        prompt = "JWKS endpoint outage 나면 stale cache fail-open fail-closed 를 어떻게 결정해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_jwks_recovery",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("fail-open", expanded)
        self.assertIn("fail-closed", expanded)
        self.assertIn("jwks outage recovery", expanded)
        self.assertNotIn("connection pool", expanded)
        self.assertNotIn("close", expanded)

    def test_introductory_jwt_validation_query_prefers_authentication_primer_signal(self) -> None:
        prompt = "JWT 를 처음 배우는데 kid issuer audience signature validation 순서를 입문자 기준으로 먼저 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_authentication",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("security_authentication", tags)
        self.assertNotIn("security_token_validation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("token payload structure", expanded)
        self.assertIn("claims", expanded)
        self.assertIn("exp", expanded)

    def test_timeout_attribution_terms_map_to_network_signal(self) -> None:
        prompt = "timeout attribution 을 할 때 local reply 랑 upstream error 를 어떻게 구분해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "network_error_attribution",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("proxy local reply", expanded)
        self.assertIn("upstream error attribution", expanded)

    def test_anycast_failover_terms_map_to_network_signal(self) -> None:
        prompt = "anycast edge failover tradeoff 랑 route convergence 차이를 알고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "network_edge_failover",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("anycast", expanded)
        self.assertIn("edge failover", expanded)
        self.assertIn("route convergence", expanded)

    def test_os_locking_terms_map_to_locking_signal(self) -> None:
        prompt = "futex off-CPU lock contention 과 perf lock 을 같이 보고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "os_locking_debugging",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("futex", expanded)
        self.assertIn("off-cpu", expanded)
        self.assertNotIn("race condition", expanded)

    def test_mysql_gap_lock_terms_map_to_database_locking_signal(self) -> None:
        prompt = "MySQL gap lock next-key lock 어떻게 동작해"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "mysql_gap_locking",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("gap lock", expanded)
        self.assertIn("next-key lock", expanded)
        self.assertIn("innodb gap locking", expanded)
        self.assertNotIn("race condition", expanded)

    def test_overlap_enforcement_gap_lock_prompt_maps_to_database_lock_family(self) -> None:
        prompt = "예약 겹침 검사에서 select for update 했는데 insert blocked 되는 이유가 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "mysql_gap_locking",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("mysql_gap_locking", tags)
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("gap lock", expanded)
        self.assertIn("next-key lock", expanded)
        self.assertIn("insert intention wait", expanded)

    def test_engine_fallback_overlap_terms_stay_in_gap_lock_family(self) -> None:
        prompt = "engine fallback overlap enforcement 로 예약 겹침 검사를 처리할 때 gap lock 대신 어떤 제약이 생겨?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "mysql_gap_locking",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("mysql_gap_locking", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("overlap enforcement fallback", expanded)
        self.assertIn("engine fallback overlap enforcement", expanded)
        self.assertIn("gap lock", expanded)
        self.assertNotIn("receiver warmup", expanded)

    def test_next_key_lock_wait_terms_stay_out_of_generic_concurrency(self) -> None:
        prompt = "next-key lock lock wait timeout 은 왜 생겨?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "mysql_gap_locking",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("concurrency", tags)
        self.assertNotIn("transaction_anomaly_patterns", tags)
        self.assertNotIn("transaction_deadlock_case_study", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("insert intention wait", expanded)
        self.assertIn("range lock", expanded)
        self.assertNotIn("deadlock case study", expanded)

    def test_innodb_lock_wait_timeout_stays_out_of_generic_network_timeout(self) -> None:
        prompt = "InnoDB lock wait timeout 이 나는 이유가 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "mysql_gap_locking",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("network_and_reliability", tags)
        self.assertNotIn("transaction_anomaly_patterns", tags)
        self.assertNotIn("transaction_deadlock_case_study", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("gap lock", expanded)
        self.assertNotIn("deadlock case study", expanded)
        self.assertNotIn("retry budget", expanded)
        self.assertNotIn("circuit breaker", expanded)

    def test_lock_wait_timeout_with_retry_backoff_keeps_network_signal(self) -> None:
        prompt = "InnoDB lock wait timeout 이후 retry backoff 를 어떻게 잡아?"

        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("mysql_gap_locking", tags)
        self.assertIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("retry budget", expanded)
        self.assertIn("circuit breaker", expanded)

    def test_beginner_deadlock_vs_timeout_primer_suppresses_gap_lock_siblings(self) -> None:
        prompt = "deadlock 이랑 lock wait timeout 차이가 뭐야? 처음 배우는 입장에서 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_deadlock_case_study",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_deadlock_case_study", tags)
        self.assertNotIn("mysql_gap_locking", tags)
        self.assertNotIn("transaction_anomaly_patterns", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("deadlock vs lock wait timeout", expanded)
        self.assertIn("circular wait vs long wait", expanded)
        self.assertNotIn("gap lock", expanded)
        self.assertNotIn("range lock", expanded)

    def test_os_async_io_overview_terms_map_to_overview_signal(self) -> None:
        prompt = "epoll kqueue io_uring 차이와 readiness model 을 개념적으로 보고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "os_async_io_overview",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("epoll", expanded)
        self.assertIn("kqueue", expanded)
        self.assertIn("readiness model", expanded)

    def test_io_uring_queue_terms_map_to_deep_dive_signal(self) -> None:
        prompt = "io_uring 의 SQ CQ submission queue completion queue batching 을 알고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "os_io_uring_queues",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("io_uring", expanded)
        self.assertIn("submission queue", expanded)
        self.assertIn("cqe", expanded)

    def test_introductory_io_uring_queue_query_prefers_overview_signal(self) -> None:
        prompt = "io_uring 을 처음 배우는데 SQ CQ 보다 epoll kqueue 랑 차이를 먼저 개념적으로 알고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "os_async_io_overview",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("os_async_io_overview", tags)
        self.assertNotIn("os_io_uring_queues", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("epoll kqueue io_uring overview", expanded)
        self.assertIn("edge triggered", expanded)

    def test_io_uring_hazards_terms_map_to_operational_signal(self) -> None:
        prompt = "io_uring registered buffers, fixed files, SQPOLL 같은 operational hazards 는 어디서 봐야 해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "os_io_uring_operational_hazards",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("io_uring operational hazards", expanded)
        self.assertIn("registered buffers", expanded)
        self.assertIn("cq overflow", expanded)

    def test_bigdecimal_terms_map_to_language_value_signal(self) -> None:
        prompt = "BigDecimal equals compareTo rounding 직렬화 함정이 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_numeric_value_semantics",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("bigdecimal", expanded)
        self.assertIn("compareto", expanded)
        self.assertIn("json serialization", expanded)

    def test_value_object_canonicalization_terms_map_to_language_signal(self) -> None:
        prompt = "value object canonicalization 으로 scale normalization 을 강제해야 하나?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "java_value_canonicalization",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("value object", expanded)
        self.assertIn("canonicalization", expanded)
        self.assertIn("scale normalization", expanded)

    def test_failover_cutover_terms_map_to_control_plane_signal(self) -> None:
        prompt = "regional evacuation 이랑 weighted region routing 을 하는 global traffic failover control plane 을 어떻게 설계해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "global_failover_control_plane",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("global traffic failover", expanded)
        self.assertIn("regional evacuation", expanded)

    def test_stateful_failover_terms_map_to_placement_signal(self) -> None:
        prompt = "stateful workload placement failover control plane 에서 evacuation 과 placement budget 을 어떻게 잡아?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "stateful_failover_placement",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("stateful workload placement", expanded)
        self.assertIn("leader placement", expanded)

    def test_failover_verification_terms_map_to_database_signal(self) -> None:
        prompt = "commit horizon after failover verification 을 어떻게 해야 하지?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "failover_verification",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("commit horizon after failover", expanded)
        self.assertIn("loss boundary", expanded)

    def test_progressive_cutover_terms_map_to_cutover_signal(self) -> None:
        prompt = "shadow traffic mirrored requests route guardrail 로 progressive cutover 를 운영하고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "progressive_cutover_control_plane",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("progressive cutover", expanded)
        self.assertIn("traffic shadowing", expanded)

    def test_strangler_verification_terms_map_to_cutover_signal(self) -> None:
        prompt = "strangler verification, shadow traffic metrics, diffing 으로 cutover 전 검증하고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "progressive_cutover_control_plane",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("response diff", expanded)
        self.assertIn("shadow traffic", expanded)

    def test_failover_visibility_terms_map_to_visibility_signal(self) -> None:
        prompt = "failover visibility window 동안 stale primary 와 topology cache divergence 를 어떻게 줄이지?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "failover_visibility",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("failover visibility window", expanded)
        self.assertIn("topology cache invalidation", expanded)

    def test_post_promotion_visibility_terms_stay_out_of_key_rotation_family(self) -> None:
        prompt = "post-promotion stale reads 와 topology cache invalidation visibility window 를 알고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "failover_visibility",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("post-promotion stale reads", expanded)
        self.assertIn("topology cache invalidation", expanded)
        self.assertNotIn("stale key", expanded)

    def test_failover_visibility_alias_without_window_maps_to_visibility_signal(self) -> None:
        prompt = "failover visibility 때문에 stale primary 랑 topology cache divergence 가 왜 생기는지 알고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "failover_visibility",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("failover visibility window", expanded)
        self.assertIn("topology cache invalidation", expanded)

    def test_failover_divergence_beginner_aliases_stay_out_of_visibility_playbook_terms(self) -> None:
        cases = {
            "stale primary 가 뭐야? failover 뒤에 왜 예전 primary 를 읽어?": "stale primary",
            "old primary read 가 왜 생겨? failover 뒤 읽기가 갈라지는 이유를 초보자 기준으로 설명해줘": (
                "old primary still serving reads"
            ),
            "promotion read divergence 가 뭐야? failover 후 왜 어떤 요청은 옛값을 읽어?": (
                "read divergence"
            ),
        }

        for prompt, anchor in cases.items():
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "failover_read_divergence",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("failover_read_divergence", tags)
                self.assertNotIn("failover_visibility", tags)
                self.assertNotIn("global_failover_control_plane", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn(anchor, expanded)
                self.assertIn("read divergence", expanded)
                self.assertNotIn("failover visibility window", expanded)
                self.assertNotIn("global traffic failover", expanded)

    def test_introductory_projection_vs_failover_visibility_alias_mixed_prompt_keeps_beginner_first(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 projection freshness 랑 failover visibility 차이를 같이 "
            "보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_visibility", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_visibility"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("failover", expanded)
        self.assertIn("visibility", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("stale primary", expanded)

    def test_projection_freshness_terms_map_to_projection_signal(self) -> None:
        prompt = "projection freshness budget 이랑 read-your-writes 는 어떻게 설명해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("persistence_boundary", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("projection lag budget", expanded)
        self.assertIn("projection freshness slo", expanded)
        self.assertNotIn("repository pattern", expanded)

    def test_cdc_schema_evolution_terms_map_to_storage_contract_signal(self) -> None:
        prompt = "CDC schema evolution 에서 expand-contract migration 순서를 어떻게 잡아?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "storage_contract_evolution",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("db_modeling", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("cdc schema evolution", expanded)
        self.assertIn("expand contract migration", expanded)
        self.assertIn("forward compatible consumer", expanded)
        self.assertNotIn("cross-service schema evolution", expanded)
        self.assertNotIn("schema design", expanded)
        self.assertNotIn("dual write", expanded)

    def test_debezium_contract_phase_terms_stay_in_storage_contract_family(self) -> None:
        prompt = "debezium schema change 때 versioned payload 랑 contract phase 를 어떻게 운영해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "storage_contract_evolution",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("debezium schema change", expanded)
        self.assertIn("versioned payload", expanded)
        self.assertIn("contract-safe rollout", expanded)
        self.assertNotIn("normalization", expanded)

    def test_contract_remove_phase_cleanup_terms_expand_to_retirement_keywords(self) -> None:
        prompt = (
            "expand-contract rollout 이 contract/remove phase 에 들어갔는데 "
            "destructive schema cleanup 전에 old field shadow read 제거, "
            "retention/replay window, drop column safety 를 어떻게 확인해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "storage_contract_evolution",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("db_modeling", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("contract phase", expanded)
        self.assertIn("destructive schema cleanup", expanded)
        self.assertIn("drop column safety", expanded)
        self.assertIn("field removal runbook", expanded)
        self.assertNotIn("backward compatible payload", expanded)
        self.assertNotIn("consumer tolerance", expanded)

    def test_column_retirement_terms_stay_in_late_phase_storage_contract_family(self) -> None:
        prompt = (
            "column retirement 에서 read-off -> write-off -> drop 순서와 "
            "field removal runbook 을 어떻게 잡아?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "storage_contract_evolution",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("db_modeling", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("column retirement", expanded)
        self.assertIn("contract phase", expanded)
        self.assertIn("schema cleanup", expanded)
        self.assertIn("drop column safety", expanded)
        self.assertNotIn("cdc schema evolution", expanded)
        self.assertNotIn("backward compatible payload", expanded)

    def test_event_upcaster_terms_map_to_dedicated_signal(self) -> None:
        prompt = "event schema evolution 이 있을 때 upcaster compatibility layer 를 어떻게 설계해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "event_upcaster_compatibility",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("storage_contract_evolution", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("event upcaster", expanded)
        self.assertIn("event compatibility layer", expanded)
        self.assertIn("event schema evolution", expanded)
        self.assertNotIn("schema design", expanded)
        self.assertNotIn("layered architecture", expanded)

    def test_api_schema_evolution_compatibility_layer_terms_do_not_activate_upcaster_signal(
        self,
    ) -> None:
        prompt = "REST API versioning 과 schema evolution 에서 compatibility layer 를 어디까지 둬야 해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "api_boundary",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("event_upcaster_compatibility", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("rest api", expanded)
        self.assertNotIn("event upcaster", expanded)
        self.assertNotIn("event schema evolution", expanded)

    def test_cross_service_schema_evolution_terms_do_not_activate_upcaster_signal(self) -> None:
        prompt = "cross-service schema evolution 에서 backward compatible payload 와 consumer tolerance 를 어떻게 설계해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "storage_contract_evolution",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("event_upcaster_compatibility", tags)
        self.assertNotIn("layer_responsibility", tags)
        self.assertNotIn("db_modeling", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("cross-service schema evolution", expanded)
        self.assertIn("backward compatible payload", expanded)
        self.assertIn("consumer tolerance", expanded)
        self.assertNotIn("cdc schema evolution", expanded)
        self.assertNotIn("debezium schema change", expanded)
        self.assertNotIn("event upcaster", expanded)
        self.assertNotIn("legacy event replay", expanded)
        self.assertNotIn("layered architecture", expanded)

    def test_legacy_event_replay_terms_stay_in_upcaster_family(self) -> None:
        prompt = "legacy event replay 에서 upcast chain 과 tolerant reader 를 어떻게 설계해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "event_upcaster_compatibility",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("legacy event replay", expanded)
        self.assertIn("upcast chain", expanded)
        self.assertIn("tolerant reader", expanded)
        self.assertNotIn("migration", expanded)

    def test_legacy_fixture_replay_terms_keep_upcaster_signal_ahead_of_siblings(self) -> None:
        prompt = "event upcaster 로 legacy fixture replay 와 semantic versioned event upcast chain 을 어떻게 테스트해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "event_upcaster_compatibility",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("event upcaster", expanded)
        self.assertIn("semantic versioned event", expanded)
        self.assertIn("upcast chain", expanded)
        self.assertIn("legacy", expanded)
        self.assertNotIn("forward compatible consumer", expanded)

    def test_snapshot_mixed_replay_terms_stay_in_upcaster_family(self) -> None:
        prompt = "snapshot 이전/이후 혼합 replay 에서 event upcaster compatibility policy 로 legacy event 를 current model 로 끌어올리는 기준이 궁금해"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "event_upcaster_compatibility",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("snapshot", expanded)
        self.assertIn("event upcaster", expanded)
        self.assertIn("legacy event replay", expanded)
        self.assertIn("upcast chain", expanded)
        self.assertNotIn("repair", expanded)

    def test_receiver_warmup_terms_map_to_cutover_signal(self) -> None:
        prompt = "receiver warmup, cache prefill, write freeze 로 cutover blast radius 를 줄이고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "migration_repair_cutover",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("receiver warmup", expanded)
        self.assertIn("cutover", expanded)

    def test_projection_cutover_guardrail_terms_map_to_projection_signal(self) -> None:
        prompt = "read model cutover guardrails, dual read parity, rollback window, freshness guardrail 을 같이 보고 싶어"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("projection freshness slo", expanded)

    def test_introductory_projection_freshness_query_prefers_primer_terms_over_cutover_playbook_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 read model cutover guardrails 나 "
            "projection rebuild backfill cutover playbook 전에 stale read 랑 "
            "read-your-writes 큰 그림부터 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("old data after write", expanded)
        self.assertIn("eventual consistency ux", expanded)

    def test_introductory_session_pinning_vs_expected_version_prompt_keeps_strict_read_primer_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 session pinning 이랑 expectedVersion strict "
            "read 차이가 뭐야? strict read fallback contract 나 read model cutover "
            "guardrails 전에 큰 그림부터 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("session pinning strict read", expanded)
        self.assertIn("session pinning vs version gated", expanded)
        self.assertIn("expected version strict read", expanded)
        self.assertIn("actor scoped pinning", expanded)
        self.assertNotIn("dual write", expanded)

    def test_introductory_session_pinning_vs_watermark_gate_prompt_keeps_strict_read_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 최신성을 처음 배우는데 세션 피닝이랑 watermark gated strict read 차이를 "
            "알고 싶어. strict read fallback contract 나 read model cutover guardrails 같은 "
            "운영 문서 전에 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("session pinning strict read", expanded)
        self.assertIn("watermark gated strict read", expanded)
        self.assertIn("cross screen read your writes", expanded)
        self.assertNotIn("receiver warmup", expanded)

    def test_introductory_session_pinning_vs_version_gated_prompts_keep_strict_read_primer_signal_without_authentication_drift(
        self,
    ) -> None:
        cases = (
            (
                "session pinning 이랑 version-gated strict read 차이가 뭐야? strict read "
                "fallback contract 나 read model cutover guardrails 같은 운영 playbook 전에 "
                "입문 그림부터 먼저 보고 싶어"
            ),
            (
                "세션 피닝이랑 version gated strict read 는 뭐가 달라? fallback contract 나 "
                "cutover guardrails 전에 먼저 이해하고 싶어"
            ),
        )

        for prompt in cases:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                self.assertNotIn("migration_repair_cutover", tags)
                self.assertNotIn("security_authentication", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("session pinning strict read", expanded)
                self.assertIn("session pinning vs version gated", expanded)
                self.assertIn("expected version strict read", expanded)
                self.assertIn("watermark gated strict read", expanded)
                self.assertIn("cross screen read your writes", expanded)
                self.assertNotIn("session cookie jwt basics", expanded)

    def test_introductory_projection_primer_vs_guardrail_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, "
            "read model cutover guardrails 를 같이 비교해서 보고 싶어. 입문자는 "
            "guardrail 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("read model cutover guardrails", expanded)

    def test_introductory_projection_primer_vs_rebuild_playbook_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, "
            "projection rebuild backfill cutover playbook 를 같이 비교해서 보고 싶어. "
            "입문자는 운영 playbook 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("stale read", expanded)
        self.assertNotIn("backfill", expanded)
        self.assertNotIn("rebuild", expanded)

    def test_introductory_projection_primer_vs_guardrail_and_rebuild_triad_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, "
            "read model cutover guardrails, projection rebuild backfill cutover playbook 를 "
            "같이 비교해서 보고 싶어. 입문자는 운영 문서 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertEqual(tags, ["projection_freshness"])
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertNotIn("backfill", expanded)
        self.assertNotIn("rebuild", expanded)

    def test_projection_beginner_navigator_bridge_prompt_prefers_primer_neighbors_over_cqrs_survey(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 개요 문서랑 주변 형제 "
            "문서를 같이 보고 싶어. CQRS 전체 survey 말고 projection 큰 그림부터 보고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read model staleness and read-your-writes", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("projection lag budgeting pattern", expanded)
        self.assertIn("projection lag budget", expanded)
        self.assertNotIn("cqrs survey routing", expanded)

    def test_projection_beginner_navigator_bridge_prompt_accepts_cqrs_overview_rejection_wording(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 개요 문서랑 옆 형제 "
            "문서를 같이 보고 싶어. CQRS 전체 개요 말고 projection 큰 그림부터 보고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertEqual(tags, ["projection_freshness"])
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read model staleness and read-your-writes", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("projection lag budgeting pattern", expanded)
        self.assertIn("projection lag budget", expanded)

    def test_projection_beginner_navigator_bridge_prompt_accepts_staleness_overview_and_nearby_docs_wording(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 projection 을 처음 배우는데 stale read 때문에 예전 값이 왜 보이는지 "
            "staleness overview doc 이랑 nearby docs 를 같이 보고 싶어. CQRS 전체 "
            "overview 말고 projection 큰 그림부터 보고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertEqual(tags, ["projection_freshness"])
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read model staleness and read-your-writes", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("projection lag budgeting pattern", expanded)
        self.assertIn("projection lag budget", expanded)
        self.assertNotIn("cqrs survey routing", expanded)
        self.assertNotIn("cqrs survey routing", expanded)

    def test_projection_beginner_navigator_bridge_prompt_accepts_overview_docs_and_sibling_docs_route_rejection(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 overview docs 랑 "
            "nearby sibling docs 를 같이 보고 싶어. broad CQRS survey routes 말고 "
            "projection 큰 그림부터 보고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertEqual(tags, ["projection_freshness"])
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read model staleness overview", expanded)
        self.assertIn("read model staleness and read-your-writes", expanded)
        self.assertIn("projection primer sibling docs", expanded)
        self.assertIn("nearby sibling docs", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("projection lag budgeting pattern", expanded)
        self.assertNotIn("cqrs survey routing", expanded)

    def test_projection_beginner_navigator_bridge_prompt_accepts_entrypoint_primer_and_route_rejection_wording(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 entrypoint primer "
            "랑 bridge docs, linked sibling docs 를 같이 보고 싶어. broad CQRS "
            "survey routes 말고 projection 큰 그림부터 보고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertEqual(tags, ["projection_freshness"])
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read model staleness overview", expanded)
        self.assertIn("projection primer sibling docs", expanded)
        self.assertIn("nearby sibling docs", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertIn("projection lag budgeting pattern", expanded)
        self.assertNotIn("cqrs survey routing", expanded)

    def test_introductory_projection_primer_vs_rebuild_playbook_compare_keeps_stateful_companion_anchor_tokens(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, "
            "projection rebuild backfill cutover playbook 이랑 stateful failover placement "
            "문서를 같이 비교하고 싶어. 입문자는 운영 문서 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stateful", expanded)
        self.assertIn("failover", expanded)
        self.assertIn("placement", expanded)
        self.assertNotIn("rebuild", expanded)
        self.assertNotIn("backfill", expanded)

    def test_introductory_projection_primer_vs_rebuild_playbook_compare_keeps_failover_verification_anchor_tokens(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, "
            "projection rebuild backfill cutover playbook 이랑 failover verification 문서를 "
            "같이 비교하고 싶어. 입문자는 운영 문서 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("failover", expanded)
        self.assertIn("verification", expanded)
        self.assertNotIn("commit horizon after failover", expanded)
        self.assertNotIn("rebuild", expanded)
        self.assertNotIn("backfill", expanded)

    def test_introductory_projection_korean_only_primer_vs_rebuild_backfill_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 저장했는데도 예전 값이 보여서 헷갈려. "
            "쓴 직후 읽기 보장 설명이랑 프로젝션 재빌드 백필 컷오버 안내를 같이 "
            "비교해서 보고 싶어. 입문자는 운영 복구 문서 전에 어떤 기초 설명부터 "
            "봐야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("stale read", expanded)
        self.assertNotIn("rebuild", expanded)
        self.assertNotIn("backfill", expanded)

    def test_introductory_projection_korean_only_primer_vs_guardrail_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 예전 값이 보여서 헷갈려. 쓴 직후 읽기 보장과 "
            "전환 안전 구간 문서를 같이 비교해서 보고 싶어. 입문자는 운영 안전 규칙 전에 "
            "뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("old data after write", expanded)
        self.assertIn("read model cutover guardrails", expanded)

    def test_introductory_projection_korean_phrase_only_primer_vs_guardrail_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 방금 저장했는데도 예전 값이 보여서 헷갈려. "
            "쓴 직후 읽기 보장 설명이랑 전환 안전 구간 안내를 같이 비교해서 보고 싶어. "
            "입문자는 운영 문서 전에 어떤 기초 설명부터 봐야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("old data after write", expanded)
        self.assertIn("read model cutover guardrails", expanded)

    def test_projection_cutover_safety_shortform_question_maps_to_primer_signal(self) -> None:
        prompt = "컷오버 안전 구간 뭐야"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertEqual(tags[0], "projection_freshness")
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("cutover safety window", expanded)
        self.assertNotIn("read model cutover guardrails", expanded)

    def test_introductory_projection_primer_vs_slo_lag_budget_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer를 "
            "먼저 보고, projection freshness SLO 문서랑 projection lag budget 문서를 "
            "같이 비교하고 싶어. 입문자는 SLO 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("projection freshness slo", expanded)
        self.assertIn("projection lag budget", expanded)

    def test_introductory_projection_korean_only_primer_vs_slo_lag_budget_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 예전 값이 보여서 헷갈려. 예전 값이 보이는 기초 "
            "설명이랑 최신성 SLO, 지연 예산 문서를 같이 비교해서 보고 싶어. 입문자는 "
            "운영 목표 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("projection freshness slo", expanded)
        self.assertIn("projection lag budget", expanded)
        self.assertNotIn("slo", expanded)
        self.assertNotIn("지연", expanded)
        self.assertNotIn("예산", expanded)
        self.assertNotIn("read model cutover guardrails", expanded)

    def test_introductory_projection_fully_korean_primer_vs_slo_lag_budget_compare_prompt_keeps_primer_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 예전 값이 보여서 헷갈려. 예전 값이 보이는 기초 "
            "설명이랑 최신성 서비스 수준 목표, 반영 지연 허용 범위 문서를 같이 비교해서 "
            "보고 싶어. 입문자는 운영 목표 전에 뭐부터 이해해야 해?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("migration_repair_cutover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("projection freshness slo", expanded)
        self.assertIn("projection lag budget", expanded)
        self.assertNotIn("최신성", expanded)
        self.assertNotIn("지연", expanded)
        self.assertNotIn("범위", expanded)
        self.assertNotIn("read model cutover guardrails", expanded)

    def test_advanced_projection_slo_tuning_query_avoids_primer_first_bias_without_beginner_cues(
        self,
    ) -> None:
        prompt = (
            "projection freshness SLO tuning 에서 freshness SLI, lag breach policy, "
            "consumer backlog budget, projection watermark gap, read-your-writes "
            "exception budget 를 어떻게 묶어?"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("projection freshness slo", expanded)
        self.assertIn("projection lag budget", expanded)
        self.assertIn("lag breach policy", expanded)
        self.assertIn("consumer backlog budget", expanded)
        self.assertIn("projection watermark", expanded)
        self.assertIn("watermark gap", expanded)
        self.assertIn("read your writes", expanded)
        self.assertNotIn("read model staleness", expanded)
        self.assertNotIn("old data after write", expanded)
        self.assertNotIn("saved but still old data", expanded)
        self.assertNotIn("old screen state after save", expanded)

    def test_introductory_projection_vs_stateful_failover_placement_compare_prompt_keeps_primer_signal_with_stateful_companion(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 projection freshness 랑 "
            "stateful failover placement 차이를 같이 보고 싶어. stale read 랑 "
            "read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertIn("stateful_failover_placement", tags)
        self.assertLess(tags.index("projection_freshness"), tags.index("stateful_failover_placement"))
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stateful workload placement", expanded)
        self.assertIn("placement budget", expanded)

    def test_korean_only_projection_vs_stateful_failover_placement_compare_prompts_keep_primer_signal(
        self,
    ) -> None:
        prompts = {
            "workload_placement": (
                "읽기 모델 최신성을 처음 배우는데 투영 최신성이랑 상태 저장 워크로드 "
                "장애 전환 배치가 어떻게 다른지 같이 알고 싶어. 왜 저장 직후엔 예전 값이 "
                "남고 상태 저장 서비스는 장애 때 어느 복제본을 올릴지 따로 고민하는지 큰 "
                "그림부터 설명해줘"
            ),
            "leader_placement": (
                "입문자 기준으로 읽기 모델 최신성이랑 상태 저장 서비스 리더 배치, 배치 "
                "예산 판단이 뭐가 다른지 비교해줘. 저장 직후 예전 값이 보이는 문제와 장애 "
                "전환 때 리더를 어디에 둘지 고민하는 문제를 큰 그림부터 알고 싶어"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                self.assertIn("stateful_failover_placement", tags)
                self.assertLess(
                    tags.index("projection_freshness"),
                    tags.index("stateful_failover_placement"),
                )
                self.assertNotIn("global_failover_control_plane", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("stateful workload placement", expanded)
                self.assertIn("placement budget", expanded)
                self.assertNotIn("global traffic failover", expanded)

    def test_introductory_projection_rollback_window_query_suppresses_transaction_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 rollback window 때문에 stale read 랑 "
            "read-your-writes 큰 그림이 더 헷갈려"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("mvcc", expanded)
        self.assertNotIn("read committed", expanded)

    def test_projection_rollback_window_suppression_toggles_only_with_beginner_freshness_cue(
        self,
    ) -> None:
        prompts = {
            "freshness cue on": (
                "rollback window 랑 transaction rollback 을 처음 배우는데 read model "
                "freshness 큰 그림부터 설명해줘"
            ),
            "freshness cue off": (
                "rollback window 랑 transaction rollback 을 처음 배우는데 큰 그림부터 "
                "설명해줘"
            ),
        }

        expected_presence = {
            "freshness cue on": False,
            "freshness cue off": True,
        }

        for label, prompt in prompts.items():
            with self.subTest(case=label):
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                if expected_presence[label]:
                    self.assertIn("transaction_isolation", tags)
                else:
                    self.assertNotIn("transaction_isolation", tags)

    def test_database_focused_transaction_rollback_query_keeps_transaction_signal_without_projection_primer(
        self,
    ) -> None:
        prompt = (
            "트랜잭션 롤백이 왜 필요한지와 isolation level 에서 dirty read, "
            "phantom read 를 어떻게 막는지 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_isolation", tags)
        self.assertNotIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("transaction", expanded)
        self.assertIn("isolation level", expanded)
        self.assertIn("rollback", expanded)
        self.assertNotIn("read model staleness", expanded)
        self.assertNotIn("read your writes", expanded)

    def test_database_transaction_incident_primer_strips_generic_operational_noise(self) -> None:
        prompt = "transaction rollback incident primer 를 beginner 관점에서 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("transaction", expanded)
        self.assertIn("rollback", expanded)
        self.assertIn("mvcc", expanded)
        self.assertNotIn("incident", expanded)
        self.assertNotIn("primer", expanded)

    def test_commit_failure_rollback_incident_primer_strips_generic_commit_failure_noise(
        self,
    ) -> None:
        prompt = "commit failure rollback incident primer 를 beginner 관점에서 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_isolation", tags)
        self.assertNotIn("spring_framework", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("transaction", expanded)
        self.assertIn("rollback", expanded)
        self.assertIn("mvcc", expanded)
        self.assertNotIn("commit", expanded)
        self.assertNotIn("failure", expanded)
        self.assertNotIn("incident", expanded)
        self.assertNotIn("primer", expanded)

    def test_dirty_read_incident_primer_keeps_database_anomaly_vocabulary_without_spring_noise(
        self,
    ) -> None:
        prompt = "dirty read incident primer 를 beginner 관점에서 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_anomaly_patterns",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_anomaly_patterns", tags)
        self.assertNotIn("spring_framework", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("anomaly overview", expanded)
        self.assertIn("isolation level", expanded)
        self.assertIn("mvcc", expanded)
        self.assertNotIn("deadlock", expanded)
        self.assertNotIn("mysql deadlock", expanded)
        self.assertNotIn("incident", expanded)
        self.assertNotIn("primer", expanded)

    def test_explicit_spring_rollback_incident_prompt_keeps_spring_cues(self) -> None:
        prompt = "Spring rollbackOnly incident primer 를 beginner 관점에서 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring", expanded)
        self.assertIn("incident", expanded)
        self.assertIn("primer", expanded)

    def test_english_transactional_propagation_prompt_keeps_advanced_spring_signal_without_beginner_bias(
        self,
    ) -> None:
        prompt = "What does propagation mean in @Transactional?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        self.assertNotIn("java_completablefuture_cancellation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("transaction propagation", expanded)
        self.assertIn("required", expanded)
        self.assertIn("requires_new", expanded)
        self.assertIn("nested transaction", expanded)
        self.assertNotIn("transactional annotation basics", expanded)

    def test_mixed_rollback_window_and_korean_transaction_rollback_without_primer_cue_stays_db_first(
        self,
    ) -> None:
        prompt = "rollback window 랑 트랜잭션 롤백 차이가 뭐야"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_isolation", tags)
        self.assertIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("transaction", expanded)
        self.assertIn("isolation level", expanded)
        self.assertIn("rollback window", expanded)
        self.assertNotIn("read model staleness", expanded)
        self.assertNotIn("read your writes", expanded)

    def test_introductory_projection_rollback_window_vs_transaction_rollback_query_keeps_contrast_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 rollback window 랑 transaction rollback "
            "차이를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 "
            "설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("transaction_isolation", tags)
        self.assertLess(tags.index("projection_freshness"), tags.index("transaction_isolation"))
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertNotIn("rollback window", expanded)
        self.assertNotIn("transaction rollback", expanded)

    def test_introductory_projection_rollback_window_vs_korean_transaction_rollback_query_keeps_contrast_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 rollback window 랑 트랜잭션 롤백 "
            "차이를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 "
            "설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("transaction_isolation", tags)
        self.assertLess(tags.index("projection_freshness"), tags.index("transaction_isolation"))
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)

    def test_introductory_projection_korean_rollback_window_vs_korean_transaction_rollback_query_keeps_contrast_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 "
            "차이를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 "
            "설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("transaction_isolation", tags)
        self.assertLess(tags.index("projection_freshness"), tags.index("transaction_isolation"))
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)

    def test_introductory_projection_full_korean_rollback_window_vs_transaction_rollback_query_keeps_contrast_signal(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 최신성을 처음 배우는데 롤백 윈도우랑 트랜잭션 롤백 차이를 같이 비교해서 "
            "보고 싶어. 왜 예전 값이 보이고 방금 쓴 값 읽기가 흔들리는지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("transaction_isolation", tags)
        self.assertLess(tags.index("projection_freshness"), tags.index("transaction_isolation"))
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertNotIn("rollback window", expanded)
        self.assertNotIn("transaction rollback", expanded)

    def test_introductory_projection_rollback_contrast_synonyms_keep_comparison_signal(
        self,
    ) -> None:
        prompts = {
            "구분": (
                "read model freshness 를 처음 배우는데 rollback window 랑 transaction rollback 을 "
                "어떻게 구분해야 해? stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "헷갈림": (
                "read model freshness 를 처음 배우는데 rollback window 랑 transaction rollback "
                "헷갈림이 있어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "vs": (
                "read model freshness 를 처음 배우는데 rollback window vs transaction rollback 이 "
                "뭐가 다른지 모르겠어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                signals = signal_rules.detect_signals(prompt)
                tags = [signal["tag"] for signal in signals]
                self.assertIn("projection_freshness", tags)
                self.assertIn("transaction_isolation", tags)
                self.assertLess(
                    tags.index("projection_freshness"),
                    tags.index("transaction_isolation"),
                )
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("stale read", expanded)

    def test_introductory_projection_korean_rollback_contrast_synonyms_keep_comparison_signal(
        self,
    ) -> None:
        prompts = {
            "비교": (
                "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 을 "
                "같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "구분": (
                "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 을 "
                "어떻게 구분해야 해? stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "헷갈림": (
                "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 "
                "헷갈림이 있어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                signals = signal_rules.detect_signals(prompt)
                tags = [signal["tag"] for signal in signals]
                self.assertIn("projection_freshness", tags)
                self.assertIn("transaction_isolation", tags)
                self.assertLess(
                    tags.index("projection_freshness"),
                    tags.index("transaction_isolation"),
                )
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("stale read", expanded)
                self.assertIn("mvcc", expanded)
                self.assertIn("read committed", expanded)
                self.assertIn("mvcc", expanded)
                self.assertIn("read committed", expanded)

    def test_introductory_projection_vs_failover_queries_keep_both_signals_with_compact_failover_terms(
        self,
    ) -> None:
        prompts = {
            "compare": (
                "read model freshness 를 처음 배우는데 projection freshness 랑 "
                "failover 차이를 같이 비교해서 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
            "different": (
                "read model freshness 를 처음 배우는데 projection freshness 랑 "
                "failover 가 어떻게 다른지 같이 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                signals = signal_rules.detect_signals(prompt)
                tags = [signal["tag"] for signal in signals]
                self.assertIn("projection_freshness", tags)
                self.assertIn("global_failover_control_plane", tags)
                self.assertLess(
                    tags.index("projection_freshness"),
                    tags.index("global_failover_control_plane"),
                )
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("stale read", expanded)
                self.assertIn("global traffic failover", expanded)
                self.assertIn("control plane", expanded)
                self.assertNotIn("regional evacuation", expanded)
                self.assertNotIn("weighted region routing", expanded)
                self.assertNotIn("health signal aggregation", expanded)

    def test_introductory_projection_vs_failover_visibility_queries_keep_visibility_signal_without_operational_dump(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 projection freshness 랑 "
            "failover visibility window 차이를 같이 보고 싶어. stale read 랑 "
            "read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_visibility", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_visibility"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("failover", expanded)
        self.assertIn("visibility", expanded)
        self.assertIn("window", expanded)
        self.assertNotIn("post-promotion stale reads", expanded)
        self.assertNotIn("topology cache invalidation", expanded)
        self.assertNotIn("stale primary", expanded)

    def test_introductory_projection_vs_failover_verification_query_stays_beginner_first_without_jwt_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 projection freshness 랑 "
            "failover verification 차이를 같이 보고 싶어. stale read 랑 "
            "read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_verification", tags)
        self.assertNotIn("security_token_validation", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_verification"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("commit horizon after failover", expanded)
        self.assertNotIn("loss boundary", expanded)
        self.assertNotIn("jwt", expanded)
        self.assertNotIn("signature verification", expanded)

    def test_introductory_projection_failover_visibility_vs_write_loss_verification_query_keeps_both_failover_signals_without_jwt_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 failover visibility window 에서 "
            "stale read 가 보일 수 있다는 말이랑 write loss audit 로 verify 해야 "
            "한다는 말을 같이 들었어. 뭐가 다른지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_visibility", tags)
        self.assertIn("failover_verification", tags)
        self.assertNotIn("security_token_validation", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_visibility"),
        )
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_verification"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("failover visibility window", expanded)
        self.assertIn("commit horizon after failover", expanded)
        self.assertNotIn("verify", expanded)
        self.assertNotIn("jwt", expanded)
        self.assertNotIn("signature verification", expanded)

    def test_introductory_projection_cutover_safety_window_suppresses_failover_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 cutover safety window 동안 stale read 랑 "
            "read-your-writes 를 어떻게 이해해야 해? failover rollback 같은 운영 얘기 "
            "전에 큰 그림부터 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("failover", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_cutover_safety_vs_failover_visibility_queries_keep_both_signals(
        self,
    ) -> None:
        prompts = {
            "compare": (
                "read model freshness 를 처음 배우는데 cutover safety window 랑 failover "
                "visibility window 차이를 같이 비교해서 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
            "different": (
                "read model freshness 를 처음 배우는데 cutover safety window 랑 failover "
                "visibility window 가 어떻게 다른지 같이 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
            "distinguish": (
                "read model freshness 를 처음 배우는데 cutover safety window 랑 failover "
                "visibility window 를 구별해서 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                signals = signal_rules.detect_signals(prompt)
                tags = [signal["tag"] for signal in signals]
                self.assertIn("projection_freshness", tags)
                self.assertIn("failover_visibility", tags)
                self.assertLess(
                    tags.index("projection_freshness"),
                    tags.index("failover_visibility"),
                )
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("stale read", expanded)
                self.assertIn("failover visibility window", expanded)
                self.assertNotIn("global traffic failover", expanded)
                self.assertNotIn("stale primary", expanded)

    def test_mixed_language_projection_cutover_safety_vs_failover_visibility_query_keeps_beginner_first_signals(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 cutover safety window vs failover visibility window 를 "
            "같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_visibility", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_visibility"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertIn("failover visibility window", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("stale primary", expanded)

    def test_full_korean_projection_cutover_safety_vs_failover_visibility_query_keeps_visibility_companion_visible(
        self,
    ) -> None:
        prompt = (
            "읽기 모델 최신성을 처음 배우는데 전환 안전 윈도우 랑 failover visibility "
            "window 차이를 같이 보고 싶어. 왜 예전 값이 보이고 방금 쓴 값 읽기 보장이 "
            "흔들리는지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        signals = signal_rules.detect_signals(prompt)
        tags = [signal["tag"] for signal in signals]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_visibility", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("failover_visibility"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertIn("failover visibility window", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("stale primary", expanded)

    def test_introductory_projection_cutover_safety_vs_failover_rollback_keeps_compare_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 cutover safety window 랑 failover rollback "
            "은 뭐가 다른지 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 "
            "그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertIn("global_failover_control_plane", tags)
        self.assertNotIn("transaction_isolation", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("global_failover_control_plane"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("failover rollback", expanded)
        self.assertIn("failover", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_cutover_safety_vs_key_rotation_rollback_keeps_compare_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 cutover safety window 랑 key rotation "
            "rollback 은 뭐가 다른지 같이 비교해서 보고 싶어. stale read 랑 "
            "read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertIn("security_key_rotation_runbook", tags)
        self.assertNotIn("transaction_isolation", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("security_key_rotation_runbook"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("key rotation rollback", expanded)
        self.assertIn("key rotation", expanded)
        self.assertNotIn("kid rollover", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_cutover_safety_vs_hyphenated_key_rotation_rollback_keeps_compare_signal(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 cutover safety window 랑 key-rotation "
            "rollback 은 뭐가 다른지 같이 비교해서 보고 싶어. stale read 랑 "
            "read-your-writes 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertIn("security_key_rotation_runbook", tags)
        self.assertNotIn("transaction_isolation", tags)
        self.assertLess(
            tags.index("projection_freshness"),
            tags.index("security_key_rotation_runbook"),
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("key rotation rollback", expanded)
        self.assertIn("key rotation", expanded)
        self.assertNotIn("kid rollover", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_cutover_safety_window_suppresses_key_rotation_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 cutover safety window 와 rollback window "
            "때문에 stale read 가 왜 생기는지 알고 싶어. key rotation rollback 같은 "
            "운영 얘기는 잠깐 빼고"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertNotIn("key", expanded)
        self.assertNotIn("rotation", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("key rotation", expanded)

    def test_introductory_projection_cutover_safety_window_suppresses_hyphenated_key_rotation_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 cutover safety window 와 rollback window "
            "때문에 stale read 가 왜 생기는지 알고 싶어. key-rotation rollback 같은 "
            "운영 얘기는 잠깐 빼고"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertNotIn("key", expanded)
        self.assertNotIn("rotation", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("key rotation", expanded)

    def test_introductory_projection_mixed_cutover_safety_window_suppresses_failover_and_key_rotation_noise(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 cutover safety window 동안 stale reads 가 보이고 "
            "쓴 직후 읽기 보장이 왜 깨지는지 알고 싶어. failover rollback 이나 key "
            "rotation rollback 같은 운영 키워드는 잠깐 빼고 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertNotIn("failover", expanded)
        self.assertNotIn("key rotation", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_korean_cutover_safety_window_suppresses_failover_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 전환 안전 구간 동안 stale read 랑 "
            "read-your-writes 를 어떻게 이해해야 해? failover rollback 같은 운영 얘기 "
            "전에 큰 그림부터 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("failover", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_mixed_korean_english_cutover_safety_window_with_stale_reads_suppresses_failover_noise(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 cutover safety window 동안 stale reads 가 보이고 "
            "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 알고 싶어. failover rollback 같은 "
            "운영 얘기는 잠깐 빼고"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("failover", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_korean_cutover_safety_window_suppresses_key_rotation_noise(
        self,
    ) -> None:
        prompt = (
            "read model freshness 를 처음 배우는데 전환 안전 윈도우 와 rollback window "
            "때문에 stale read 가 왜 생기는지 알고 싶어. key rotation rollback 같은 "
            "운영 얘기는 잠깐 빼고"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("stale read", expanded)
        self.assertNotIn("key", expanded)
        self.assertNotIn("rotation", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("key rotation", expanded)

    def test_introductory_projection_korean_rollback_window_vs_cutover_safety_query_stays_beginner_first(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 롤백 윈도우 랑 전환 안전 구간이 뭐가 다른지 "
            "헷갈려. stale read 랑 쓴 직후 읽기 보장이랑 같이 큰 그림으로 비교해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("rollback window", expanded)
        self.assertIn("cutover safety window", expanded)
        self.assertIn("롤백 윈도우", expanded)
        self.assertIn("전환 안전 구간", expanded)
        self.assertIn("freshness guardrail", expanded)
        self.assertIn("dual read parity", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_korean_cutover_safety_vs_rollback_window_comparison_strips_transaction_noise(
        self,
    ) -> None:
        prompt = (
            "CQRS 읽기 모델을 처음 배우는데 전환 안전 윈도우 vs 롤백 윈도우 를 구분해서 "
            "보고 싶어. 저장 직후 예전 값이 보여서 왜 그런지 입문자 기준으로 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("transaction_isolation", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("rollback window", expanded)
        self.assertIn("cutover safety window", expanded)
        self.assertIn("read model cutover guardrails", expanded)
        self.assertNotIn("failover", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_korean_cutover_safety_window_with_key_rotation_noise_stays_primer_first(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 전환 안전 윈도우 동안 예전 값이 보이고 쓴 직후 읽기 "
            "보장이 왜 흔들리는지 알고 싶어. key rotation rollback 같은 운영 얘기는 "
            "잠깐 빼고 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("key rotation", expanded)
        self.assertNotIn("jwks", expanded)

    def test_introductory_projection_transliterated_cutover_safety_zone_suppresses_failover_noise(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 컷오버 안전 구간 동안 예전 값이 보이고 쓴 직후 읽기 "
            "보장이 왜 깨지는지 알고 싶어. failover rollback 같은 운영 얘기 전에 큰 "
            "그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("failover", expanded)
        self.assertNotIn("global traffic failover", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_introductory_projection_spaced_transliterated_cutover_safety_window_suppresses_key_rotation_noise(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 컷 오버 안전 윈도우 동안 예전 값이 보이고 쓴 직후 "
            "읽기 보장이 왜 흔들리는지 알고 싶어. key rotation rollback 같은 운영 "
            "얘기는 잠깐 빼고 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("old data after write", expanded)
        self.assertNotIn("key rotation", expanded)
        self.assertNotIn("jwks", expanded)

    def test_beginner_transliterated_cutover_vs_failover_visibility_prompt_keeps_primer_first(
        self,
    ) -> None:
        prompt = (
            "컷오버 안전 구간 vs failover visibility window 를 입문자 기준으로 비교해줘. "
            "저장 직후 예전 값이 왜 보이는지 큰 그림부터 알고 싶어"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertIn("failover_visibility", tags)
        self.assertNotIn("global_failover_control_plane", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("cutover safety window", expanded)
        self.assertIn("failover visibility window", expanded)
        self.assertNotIn("global traffic failover", expanded)

    def test_korean_projection_freshness_synonyms_map_to_primer_signal(self) -> None:
        prompts = {
            "old_value_visible": (
                "CQRS 읽기 모델을 처음 배우는데 롤백 윈도우 때문에 예전 값이 보임. "
                "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘"
            ),
            "saved_not_visible": (
                "읽기 모델을 처음 배우는데 방금 저장했는데 안 보여. "
                "왜 옛값이 보여? 큰 그림부터 설명해줘"
            ),
            "saved_value_not_visible": (
                "CQRS를 처음 배우는데 저장한 값이 안 보이고 옛값이 보여. "
                "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                self.assertNotIn("persistence_boundary", tags)
                self.assertNotIn("transaction_isolation", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("read your writes", expanded)
                self.assertIn("old data after write", expanded)
                self.assertIn("saved but still old data", expanded)
                self.assertIn("cqrs survey routing", expanded)
                self.assertIn("쓴 직후 읽기 보장", expanded)
                self.assertIn("저장 직후 예전 값이 보임", expanded)
                self.assertNotIn("projection lag budget", expanded)
                self.assertNotIn("read model cutover guardrails", expanded)

    def test_korean_projection_freshness_minimal_symptom_queries_route_to_primer_signal(
        self,
    ) -> None:
        prompts = {
            "saved_not_visible": "방금 저장했는데 안 보여",
            "old_value_visible": "옛값이 보여",
            "old_value_only_visible": "옛값만 보여",
            "saved_not_visible_compact": "저장했는데 안 보임",
            "saved_but_old_value_visible": "저장했는데 옛값이 보인다",
            "list_not_changed_compact": "목록이 안 바뀜",
            "just_written_value_not_visible": "방금 쓴 값이 안 보임",
            "write_read_mismatch": "저장은 됐는데 조회가 달라",
            "updated_but_list_stale": "수정했는데 목록은 그대로야",
            "detail_updated_but_list_old_value": "상세는 바뀌었는데 목록은 예전 값이야",
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("read your writes", expanded)
                self.assertIn("read-after-write", expanded)
                self.assertIn("replica lag", expanded)
                self.assertIn("read replica delay", expanded)
                self.assertIn("primary fallback", expanded)
                self.assertNotIn("projection lag budget", expanded)
                self.assertNotIn("projection freshness slo", expanded)
                self.assertNotIn("read model cutover guardrails", expanded)

    def test_projection_freshness_plural_symptom_variants_keep_shared_canonical_tokens(
        self,
    ) -> None:
        prompts = {
            "stale_read": "처음 배우는데 stale read 가 보여. 왜 그런지 큰 그림부터 설명해줘",
            "stale_reads": "처음 배우는데 stale reads 가 보여. 왜 그런지 큰 그림부터 설명해줘",
            "old_values": "처음 배우는데 old values 가 보여. 왜 그런지 큰 그림부터 설명해줘",
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("read your writes", expanded)
                self.assertIn("stale read", expanded)
                self.assertIn("old data after write", expanded)
                self.assertIn("saved but still old data", expanded)
                self.assertIn("cqrs survey routing", expanded)
                self.assertIn("read-after-write", expanded)
                self.assertIn("replica lag", expanded)
                self.assertIn("read replica delay", expanded)
                self.assertIn("primary fallback", expanded)

    def test_korean_projection_freshness_fixture_anchor_queries_route_to_primer_signal(
        self,
    ) -> None:
        prompts = {
            "saved_but_old_value_visible": "저장했는데 옛값이 보인다",
            "query_old_data": "저장 직후 조회하면 예전 데이터가 보임",
            "list_not_refreshing": "저장 직후 목록 최신화가 안 됨",
            "list_still_same": "저장했는데 목록이 그대로",
            "old_list_on_screen": "수정했는데 화면엔 예전 목록이 보여",
            "screen_update_late": "저장한 뒤 화면 반영이 늦음",
            "cached_screen_after_save": "저장 후 화면이 캐시된 것처럼 보여",
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("read your writes", expanded)
                self.assertIn("old data after write", expanded)
                self.assertIn("saved but still old data", expanded)

    def test_korean_projection_freshness_rollback_symptom_variants_keep_primer_signal(
        self,
    ) -> None:
        prompts = {
            "old_value_visible_with_rollback_terms": (
                "읽기 모델 최신성을 처음 배우는데 롤백 윈도우랑 트랜잭션 롤백이 헷갈려. "
                "예전 값이 보여. 왜 이런지 큰 그림부터 설명해줘"
            ),
            "saved_not_visible_with_rollback_terms": (
                "읽기 모델 최신성을 처음 배우는데 롤백 윈도우랑 트랜잭션 롤백이 헷갈려. "
                "방금 저장했는데 안 보여. 왜 이런지 큰 그림부터 설명해줘"
            ),
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("read your writes", expanded)
                self.assertIn("saved but still old data", expanded)
                self.assertIn("쓴 직후 읽기 보장", expanded)
                self.assertIn("저장 직후 예전 값이 보임", expanded)
                self.assertNotIn("projection freshness slo", expanded)
                self.assertNotIn("projection lag budget", expanded)
                self.assertNotIn("read model cutover guardrails", expanded)

    def test_beginner_projection_cache_confusion_query_keeps_primer_terms_and_strips_cache_token(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 방금 저장했는데도 예전 값이 보여. 캐시 때문인가요? "
            "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertNotIn("캐시", expanded)
        self.assertNotIn("cache", expanded)

    def test_no_jargon_cached_screen_after_save_query_keeps_projection_primer_signal(
        self,
    ) -> None:
        prompts = (
            "저장하고 나서 화면이 캐시된 것처럼 보여. 왜 이런지 초보자 기준으로 먼저 알고 싶어",
            "저장했는데 화면이 계속 그대로라 캐시된 것처럼 보여",
            "저장 후 화면이 캐시된 것처럼 보여",
        )

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "projection_freshness",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("projection_freshness", tags)
                self.assertNotIn("security_key_rotation_rollover", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("read model staleness", expanded)
                self.assertIn("read your writes", expanded)
                self.assertIn("saved but still old data", expanded)
                self.assertIn("old screen state after save", expanded)
                self.assertNotIn("캐시", expanded)
                self.assertNotIn("cache", expanded)

    def test_beginner_cache_vs_replica_confusion_query_routes_to_read_after_write_primer(
        self,
    ) -> None:
        prompt = "방금 저장했는데 캐시인지 리플리카인지 모르겠음. 입문자 기준으로 어디부터 구분해서 봐야 해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        hits = self._search(prompt)
        self.assert_path_rank_at_most(
            hits,
            "contents/database/replica-lag-read-after-write-strategies.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/database/replica-lag-read-after-write-strategies.md",
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("replica lag", expanded)
        self.assertIn("read replica delay", expanded)
        self.assertIn("primary fallback", expanded)
        self.assertIn("application cache vs read replica", expanded)
        self.assertIn("리플리카인지", expanded)
        self.assertIn("cache vs replica lag", expanded)

    def test_beginner_projection_mixed_korean_english_cache_confusion_query_keeps_primer_bias(
        self,
    ) -> None:
        prompt = (
            "읽기 모델을 처음 배우는데 saved but old data, is it cache? "
            "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)
        self.assertIn("saved but still old data", expanded)
        self.assertNotIn("cache", expanded)

    def test_beginner_projection_vs_application_cache_invalidation_query_keeps_cache_docs(
        self,
    ) -> None:
        prompt = (
            "projection lag 이랑 real application cache invalidation 은 뭐가 달라? "
            "입문자 기준으로 read model 반영 지연과 실제 캐시 무효화를 비교 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("projection_freshness", tags)
        self.assertNotIn("security_key_rotation_rollover", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("cache", expanded)
        self.assertIn("cache invalidation", expanded)
        self.assertIn("application cache invalidation", expanded)
        self.assertIn("cache eviction after write", expanded)
        self.assertIn("projection lag vs cache invalidation", expanded)
        self.assertIn("read model staleness", expanded)
        self.assertNotIn("jwks", expanded)
        self.assertNotIn("stale key", expanded)

    def test_beginner_filter_sort_state_confusion_does_not_route_to_projection_freshness(
        self,
    ) -> None:
        prompt = (
            "처음 배우는데 수정했는데 목록은 그대로야. 혹시 브라우저 필터나 정렬 상태 때문일 수도 있어? "
            "목록 검색 조건과 sort state 큰 그림부터 설명해줘"
        )

        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("projection_freshness", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertNotIn("read model staleness", expanded)
        self.assertNotIn("read your writes", expanded)
        self.assertNotIn("saved but still old data", expanded)

    def test_beginner_filter_sort_state_confusion_search_prefers_query_model_primer(
        self,
    ) -> None:
        prompt = (
            "처음 배우는데 수정했는데 목록은 그대로야. 브라우저 필터나 정렬 상태가 더 흔한지 헷갈려. "
            "목록 검색 조건과 sort state 큰 그림부터 보고 싶어"
        )

        hits = self._search(prompt, top_k=4)

        self.assert_path_rank_at_most(
            hits,
            "contents/software-engineering/query-model-separation-read-heavy-apis.md",
            1,
        )
        paths = [hit["path"] for hit in hits]
        self.assertNotIn(
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
            paths[:2],
        )

    def test_explicit_read_model_lag_prompt_keeps_projection_freshness_signal(
        self,
    ) -> None:
        prompt = (
            "입문자 기준으로 read model projection lag 때문에 저장했는데 목록은 그대로인 상황을 "
            "read-your-writes 관점에서 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("read your writes", expanded)

    def test_generic_crud_questions_do_not_overmatch_projection_freshness(self) -> None:
        prompts = {
            "api_difference": "회원 수정 API와 조회 API 차이가 뭐야",
            "delete_api_difference": "회원 삭제 API와 조회 API 차이가 뭐야",
            "delete_status_code": "REST DELETE API는 언제 200 말고 204를 써?",
            "update_failing": "목록 조회는 되는데 수정이 안 돼",
            "generic_crud": "CRUD에서 조회랑 수정은 각각 언제 써?",
            "generic_delete_crud": "CRUD에서 delete는 언제 hard delete 대신 soft delete를 써?",
            "generic_ui_sync": "상세 디자인은 바뀌었는데 목록 카드 레이아웃만 예전 버전이야",
        }

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertNotIn("projection_freshness", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertNotIn("read model staleness", expanded)
                self.assertNotIn("read your writes", expanded)
                self.assertNotIn("projection lag budget", expanded)

        update_failing_expanded = signal_rules.expand_query(prompts["update_failing"])
        self.assertIn("service layer transaction boundary patterns", update_failing_expanded)
        self.assertIn("transactional annotation basics", update_failing_expanded)

        api_difference_expanded = signal_rules.expand_query(prompts["api_difference"])
        self.assertIn("controller service repository roles", api_difference_expanded)
        self.assertIn("spring request pipeline beginner", api_difference_expanded)

    def test_projection_watermark_terms_map_to_projection_signal(self) -> None:
        prompt = "read model cutover 에서 dual projection run 이랑 projection watermark 를 어떻게 써?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "projection_freshness",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("read model staleness", expanded)
        self.assertIn("projection freshness slo", expanded)
        self.assertIn("read model cutover guardrails", expanded)

    def test_idempotency_terms_map_to_family_signal(self) -> None:
        prompt = "POST 요청 중복 방지하려면 idempotency key 어떻게 설계해"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "idempotency_dedup_family",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("idempotency key", expanded)
        self.assertIn("payment ledger", expanded)
        self.assertIn("dedup window", expanded)

    def test_payment_ledger_idempotency_terms_stay_in_same_family(self) -> None:
        prompt = "payment ledger 에서 double charge 막으려면 idempotency 와 reconciliation 을 어떻게 같이 보지?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "idempotency_dedup_family",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("payment ledger", expanded)
        self.assertIn("double charge prevention", expanded)
        self.assertIn("reconciliation", expanded)
        self.assertIn("replay safe retry", expanded)

    def test_hyphenated_key_store_terms_stay_out_of_retry_and_migration_families(self) -> None:
        prompt = "idempotency key store 에서 dedup-window 와 replay-safe-retry 를 어떻게 같이 설계해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "idempotency_dedup_family",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("migration_repair_cutover", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("dedup window", expanded)
        self.assertIn("replay safe retry", expanded)
        self.assertNotIn("retry budget", expanded)
        self.assertNotIn("receiver warmup", expanded)

    def test_dedup_window_lease_terms_expand_to_key_store_specific_keywords(self) -> None:
        prompt = "idempotency key store 에서 dedup-window TTL 이랑 processing lease 를 어떻게 같이 설계해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "idempotency_dedup_family",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("migration_repair_cutover", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("dedup window", expanded)
        self.assertIn("processing lease", expanded)
        self.assertIn("payload hash", expanded)
        self.assertNotIn("retry budget", expanded)

    def test_request_log_retention_ttl_terms_stay_in_idempotency_family(self) -> None:
        prompt = "idempotency key store 에서 request-log retention TTL 이랑 key TTL 을 어떻게 같이 잡아야 해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "idempotency_dedup_family",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("security_key_rotation_rollover", tags)
        self.assertNotIn("security_jwks_recovery", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("dedup window", expanded)
        self.assertIn("processing lease", expanded)
        self.assertIn("replay safe retry", expanded)

    def test_jwks_validation_terms_map_to_security_signal(self) -> None:
        prompt = "JWKS kid issuer audience signature validation 순서를 어떻게 보지?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_token_validation",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("jwt", expanded)
        self.assertIn("jwks", expanded)
        self.assertIn("token validation", expanded)

    def test_locking_strategy_terms_map_to_transaction_signal(self) -> None:
        prompt = "optimistic pessimistic lock 과 select for update 는 언제 고르지?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("locking strategy", expanded)
        self.assertIn("optimistic lock", expanded)
        self.assertIn("pessimistic lock", expanded)

    def test_transaction_anomaly_terms_expand_anomaly_vocabulary(self) -> None:
        prompt = "트랜잭션 격리 수준에 따라 어떤 이상 현상이 생겨?"

        expanded = signal_rules.expand_query(prompt)
        self.assertIn("transaction anomaly", expanded)
        self.assertIn("dirty read", expanded)
        self.assertIn("phantom read", expanded)

    def test_introductory_transaction_overview_query_adds_primer_vocabulary(self) -> None:
        prompt = "트랜잭션 격리 수준과 락을 처음 배우는데 큰 그림부터 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertIn("repeatable read", expanded)

    def test_introductory_mvcc_query_uses_transaction_primer_signal(self) -> None:
        prompt = "MVCC 를 처음 배우는데 read view, undo chain 같은 내부 용어 전에 큰 그림부터 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertIn("repeatable read", expanded)
        self.assertIn("phantom read", expanded)

    def test_shortform_mvcc_query_uses_transaction_primer_signal(self) -> None:
        prompt = "MVCC가 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertIn("repeatable read", expanded)
        self.assertIn("phantom read", expanded)

    def test_shortform_mvcc_query_ranks_transaction_primer_ahead_of_internals_deep_dive(
        self,
    ) -> None:
        prompt = "MVCC가 뭐야?"

        hits = self._search(prompt)
        self.assert_path_rank_at_most(
            hits,
            "contents/database/transaction-isolation-basics.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/database/transaction-isolation-basics.md",
            "contents/database/mvcc-read-view-undo-chain-internals.md",
        )

    def test_introductory_lock_only_query_stays_in_transaction_primer_family(self) -> None:
        prompt = "optimistic/pessimistic lock 을 처음 배우는데 언제 쓰는지 말고 큰 그림부터 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_isolation",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_isolation", tags)
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("optimistic lock", expanded)
        self.assertIn("pessimistic lock", expanded)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertIn("repeatable read", expanded)
        self.assertNotIn("race condition", expanded)

    def test_introductory_transaction_query_prefers_anomaly_primer_signal(self) -> None:
        prompt = (
            "트랜잭션 격리 수준이랑 locking 을 처음 배우는데 optimistic pessimistic lock 전에 "
            "read committed repeatable read phantom read 큰 그림부터 설명해줘"
        )

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_anomaly_patterns",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("transaction_anomaly_patterns", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("mvcc", expanded)
        self.assertIn("read committed", expanded)
        self.assertIn("repeatable read", expanded)
        self.assertNotIn("locking strategy", expanded)

    def test_mysql_deadlock_terms_avoid_io_uring_false_positive(self) -> None:
        prompt = "MySQL 데드락이 왜 생기는 거야"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_deadlock_case_study",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("deadlock case study", expanded)
        self.assertIn("deadlock", expanded)
        self.assertIn("lock ordering", expanded)
        self.assertNotIn("io_uring", expanded)

    def test_mysql_deadlock_english_terms_prefer_deadlock_case_signal(self) -> None:
        prompt = "MySQL deadlock log 보고 lock ordering 을 어떻게 고쳐?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_deadlock_case_study",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("transaction_anomaly_patterns", tags)
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("deadlock case study", expanded)
        self.assertIn("wait graph", expanded)
        self.assertNotIn("phantom read", expanded)
        self.assertNotIn("race condition", expanded)

    def test_fixture_mysql_deadlock_lock_ordering_prompt_adds_case_study_terms(self) -> None:
        prompt = "MySQL deadlock log 에서 wait graph 보고 lock ordering 을 어떻게 고쳐?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "transaction_deadlock_case_study",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("transaction_anomaly_patterns", tags)
        self.assertNotIn("concurrency", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("wait graph", expanded)
        self.assertIn("row lock acquisition order", expanded)
        self.assertIn("consistent lock ordering", expanded)
        self.assertIn("deadlock victim retry", expanded)

    def test_backpressure_terms_map_to_reliability_signal(self) -> None:
        prompt = "backpressure load shedding overload queueing 을 어떻게 다루지?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "network_and_reliability",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("retry budget", expanded)
        self.assertIn("backpressure", expanded)
        self.assertIn("load shedding", expanded)

    def test_beginner_keepalive_query_prefers_keepalive_primer_signal(self) -> None:
        prompt = "HTTP keep-alive 가 뭐야? 처음 배우는데 connection reuse 큰 그림부터 알려줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "network_keepalive_basics",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("network_keepalive_basics", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("keepalive connection reuse basics", expanded)
        self.assertIn("http keep-alive", expanded)
        self.assertNotIn("retry budget", expanded)

    def test_keep_alive_spacing_shortform_query_prefers_keepalive_primer_signal(self) -> None:
        prompt = "HTTP keep alive 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "network_keepalive_basics",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("network_keepalive_basics", tags)
        self.assertNotIn("network_and_reliability", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("keepalive connection reuse basics", expanded)
        self.assertIn("http keep-alive", expanded)
        self.assertNotIn("retry budget", expanded)

    def test_colloquial_shortform_queries_keep_beginner_primer_bias_for_foundation_topics(
        self,
    ) -> None:
        cases = (
            {
                "prompt": "DispatcherServlet 뭔데?",
                "top_tag": "spring_framework",
                "must_include": {"spring request pipeline beginner", "bean container foundation"},
                "must_exclude": {"rest api"},
            },
            {
                "prompt": "@Transactional 뭔데?",
                "top_tag": "spring_framework",
                "must_include": {
                    "spring transactional basics",
                    "transactional annotation basics",
                },
                "must_exclude": {"transactional deep dive", "mvcc"},
            },
            {
                "prompt": "DI vs IoC 차이가 뭔데?",
                "top_tag": "spring_framework",
                "must_include": {
                    "spring ioc di basics",
                    "dependency injection",
                    "inversion of control",
                },
                "must_exclude": set(),
            },
            {
                "prompt": "HTTP keep-alive 뭔데?",
                "top_tag": "network_keepalive_basics",
                "must_include": {"keepalive connection reuse basics", "http keep-alive"},
                "must_exclude": {"retry budget"},
            },
            {
                "prompt": "connection pool 뭔데?",
                "top_tag": "connection_pool_basics",
                "must_include": {"connection pool basics", "hikari cp"},
                "must_exclude": {"resource lifecycle", "close", "leak"},
            },
            {
                "prompt": "세션이랑 JWT 차이가 뭔데?",
                "top_tag": "security_authentication",
                "must_include": {"session vs jwt", "session cookie jwt basics"},
                "must_exclude": {"signature verification"},
            },
            {
                "prompt": "세션이 뭐야?",
                "top_tag": "security_authentication",
                "must_include": {"session vs jwt", "session cookie jwt basics"},
                "must_exclude": {"signature verification"},
            },
            {
                "prompt": "JWT랑 쿠키 둘 다 로그인 유지에 쓰는 거야?",
                "top_tag": "security_authentication",
                "must_include": {"session vs jwt", "session cookie jwt basics"},
                "must_exclude": {"signature verification"},
            },
            {
                "prompt": "브라우저가 로그인 기억하는 건 세션이야 JWT야?",
                "top_tag": "security_authentication",
                "must_include": {"session vs jwt", "session cookie jwt basics"},
                "must_exclude": {"signature verification"},
            },
        )

        for case in cases:
            with self.subTest(prompt=case["prompt"]):
                self.assertEqual(
                    signal_rules.top_signal_tag(case["prompt"]),
                    case["top_tag"],
                )
                expanded = signal_rules.expand_query(case["prompt"])
                for token in case["must_include"]:
                    self.assertIn(token, expanded)
                for token in case["must_exclude"]:
                    self.assertNotIn(token, expanded)

    def test_colloquial_shortform_queries_rank_beginner_primers_first_in_cheap_search(
        self,
    ) -> None:
        cases = (
            {
                "prompt": "DispatcherServlet 뭔데?",
                "primer_doc": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
                "deep_dive_doc": "contents/spring/spring-mvc-handlerexecutionchain-interceptor-ordering.md",
            },
            {
                "prompt": "Spring bean 이 뭐야?",
                "primer_doc": "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
                "deep_dive_doc": "contents/spring/spring-bean-definition-overriding-semantics.md",
            },
            {
                "prompt": "@Transactional 뭔데?",
                "primer_doc": "contents/spring/spring-transactional-basics.md",
                "deep_dive_doc": "contents/spring/spring-transaction-propagation-deep-dive.md",
            },
            {
                "prompt": "DI vs IoC 차이가 뭔데?",
                "primer_doc": "contents/spring/spring-ioc-di-basics.md",
                "deep_dive_doc": "contents/spring/spring-bean-definition-overriding-semantics.md",
            },
            {
                "prompt": "HTTP keep-alive 뭔데?",
                "primer_doc": "contents/network/keepalive-connection-reuse-basics.md",
                "deep_dive_doc": "contents/network/http2-http3-connection-reuse-coalescing.md",
            },
            {
                "prompt": "connection pool 뭔데?",
                "primer_doc": "contents/database/connection-pool-basics.md",
                "deep_dive_doc": "contents/database/transaction-locking-connection-pool-primer.md",
            },
            {
                "prompt": "세션이랑 JWT 차이가 뭔데?",
                "primer_doc": "contents/security/session-cookie-jwt-basics.md",
                "deep_dive_doc": "contents/security/authentication-authorization-session-foundations.md",
            },
            {
                "prompt": "세션이 뭐야?",
                "primer_doc": "contents/security/session-cookie-jwt-basics.md",
                "deep_dive_doc": "contents/security/authentication-authorization-session-foundations.md",
            },
            {
                "prompt": "JWT랑 쿠키 둘 다 로그인 유지에 쓰는 거야?",
                "primer_doc": "contents/security/session-cookie-jwt-basics.md",
                "deep_dive_doc": "contents/security/authentication-authorization-session-foundations.md",
            },
            {
                "prompt": "브라우저가 로그인 기억하는 건 세션이야 JWT야?",
                "primer_doc": "contents/security/session-cookie-jwt-basics.md",
                "deep_dive_doc": "contents/security/authentication-authorization-session-foundations.md",
            },
        )

        for case in cases:
            with self.subTest(prompt=case["prompt"]):
                hits = self._search(case["prompt"])
                self.assert_path_rank_at_most(hits, case["primer_doc"], 1)
                self.assert_ranks_ahead(hits, case["primer_doc"], case["deep_dive_doc"])

    def test_beginner_connection_pool_query_prefers_connection_pool_primer_signal(self) -> None:
        prompt = "connection pool 이 뭐야? 처음 배우는데 왜 필요한지 알려줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "connection_pool_basics",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("connection_pool_basics", tags)
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("connection pool basics", expanded)
        self.assertIn("hikari cp", expanded)
        self.assertNotIn("resource lifecycle", expanded)
        self.assertNotIn("close", expanded)
        self.assertNotIn("leak", expanded)

    def test_connection_pooling_shortform_query_prefers_connection_pool_primer_signal(self) -> None:
        prompt = "connection pooling 이 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "connection_pool_basics",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("connection_pool_basics", tags)
        self.assertNotIn("resource_lifecycle", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("connection pool basics", expanded)
        self.assertIn("hikari cp", expanded)
        self.assertNotIn("resource lifecycle", expanded)

    def test_spring_dispatcher_terms_map_to_spring_signal(self) -> None:
        prompt = "Spring 의 dispatcherServlet 이 어떻게 동작하고 bean lifecycle 과 어디서 엮여?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        signals = signal_rules.detect_signals(prompt)
        self.assertEqual(signals[0]["category"], "spring")
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring", expanded)
        self.assertIn("dispatcher servlet", expanded)
        self.assertIn("bean lifecycle", expanded)

    def test_beginner_dispatcherservlet_query_prefers_request_pipeline_primer(self) -> None:
        prompt = "DispatcherServlet 이 뭐야? 처음 배우는데 요청 흐름이랑 bean 컨테이너 큰 그림부터 알려줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("api_boundary", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring request pipeline beginner", expanded)
        self.assertIn("bean container foundation", expanded)
        self.assertIn("controller service repository roles", expanded)

    def test_beginner_spring_bean_query_prefers_foundation_primer(self) -> None:
        prompt = "Spring bean 이 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring bean basics", expanded)
        self.assertIn("bean container foundation", expanded)
        self.assertIn("applicationcontext basics", expanded)

    def test_dispatcher_servlet_spacing_and_casing_variants_keep_beginner_primer_bias(self) -> None:
        prompts = [
            "Dispatcher Servlet 이 뭐야?",
            "dispatcher servlet 이 뭐야?",
            "Dispatcher  Servlet 이 뭐야?",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "spring_framework",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("spring_framework", tags)
                self.assertNotIn("api_boundary", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("dispatcher servlet", expanded)
                self.assertIn("spring request pipeline beginner", expanded)
                self.assertIn("bean container foundation", expanded)

    def test_spring_transaction_terms_surface_spring_before_database(self) -> None:
        prompt = "@Transactional 안에서 bean 이 어떻게 트랜잭션 경계를 만들어?"

        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        # spring_framework should score at or above transaction_isolation
        self.assertEqual(tags[0], "spring_framework")

    def test_beginner_transactional_query_prefers_transactional_basics(self) -> None:
        prompt = "@Transactional 이 뭐야? 처음 배우는데 동작 원리 큰 그림부터 설명해줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertIn("spring proxy transaction", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_shortform_transactional_what_is_query_still_prefers_transactional_basics(self) -> None:
        prompt = "@Transactional 이 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_shortform_transactional_query_still_prefers_transactional_basics(self) -> None:
        prompt = "What is @Transactional?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_plain_transactional_query_without_at_sign_keeps_beginner_primer_bias(
        self,
    ) -> None:
        prompt = "What is transactional in Spring?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("@transactional", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_plain_transactional_meaning_query_without_at_sign_keeps_beginner_primer_bias(
        self,
    ) -> None:
        prompt = "What does transactional mean in Spring?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_transactional_spring_shortform_without_question_words_keeps_beginner_primer_bias(
        self,
    ) -> None:
        prompt = "transactional in spring"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_transactional_spring_token_pair_keeps_beginner_primer_bias(self) -> None:
        prompt = "spring transactional"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_contracted_transactional_query_keeps_beginner_primer_bias(self) -> None:
        prompt = "What's @Transactional?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_english_why_use_transactional_query_keeps_beginner_primer_bias(self) -> None:
        prompt = "Why use @Transactional?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        self.assertNotIn("transaction_isolation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring transactional basics", expanded)
        self.assertIn("transactional annotation basics", expanded)
        self.assertNotIn("transactional deep dive", expanded)
        self.assertNotIn("mvcc", expanded)

    def test_beginner_di_vs_ioc_query_adds_ioc_primer_vocabulary(self) -> None:
        prompt = "DI vs IoC 차이가 뭐야? 처음 배우는데 스프링 기준으로 알려줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring ioc di basics", expanded)
        self.assertIn("dependency injection", expanded)
        self.assertIn("inversion of control", expanded)

    def test_di_and_ioc_shortform_query_adds_ioc_primer_vocabulary(self) -> None:
        prompt = "DI와 IoC 차이가 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "spring_framework",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("spring ioc di basics", expanded)
        self.assertIn("dependency injection", expanded)
        self.assertIn("inversion of control", expanded)

    def test_beginner_session_vs_jwt_query_stays_on_authentication_primer(self) -> None:
        prompt = "세션이랑 JWT 차이가 뭐야? 처음 배우는데 로그인 흐름 관점으로 알려줘"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_authentication",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertNotIn("security_token_validation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("authentication", expanded)
        self.assertIn("session", expanded)
        self.assertNotIn("signature verification", expanded)

    def test_beginner_session_only_query_stays_on_authentication_primer(self) -> None:
        prompt = "세션이 뭐야?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_authentication",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("session vs jwt", expanded)
        self.assertIn("session cookie jwt basics", expanded)
        self.assertNotIn("signature verification", expanded)

    def test_fixture_jwt_basics_prompt_adds_session_cookie_primer_vocabulary(self) -> None:
        prompt = "JWT 토큰이 뭐고 세션 쿠키로 로그인 상태를 유지하는 거랑 뭐가 달라?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_authentication",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("security_authentication", tags)
        self.assertNotIn("security_token_validation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("session vs jwt", expanded)
        self.assertIn("session cookie jwt basics", expanded)
        self.assertIn("cookie session jwt browser flow", expanded)
        self.assertIn("http stateless login state", expanded)
        self.assertIn("jsessionid", expanded)
        self.assertIn("server session vs jwt", expanded)
        self.assertIn("login state persistence", expanded)
        self.assertIn("why login stays", expanded)
        self.assertNotIn("signature verification", expanded)

    def test_colloquial_cookie_login_state_prompt_adds_session_cookie_primer_vocabulary(self) -> None:
        prompts = (
            "JWT랑 쿠키 둘 다 로그인 유지에 쓰는 거야?",
            "If JWT exists, why do I still stay logged in with cookies?",
            "왜 쿠키 있으면 로그인 안 풀려?",
            "Why do cookies keep me signed in?",
            "브라우저가 로그인 기억하는 건 세션이야 JWT야?",
            "Why am I still logged in when the browser remembers my cookie?",
        )

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertEqual(
                    signal_rules.top_signal_tag(prompt),
                    "security_authentication",
                )
                tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
                self.assertIn("security_authentication", tags)
                self.assertNotIn("security_token_validation", tags)
                expanded = signal_rules.expand_query(prompt)
                self.assertIn("session vs jwt", expanded)
                self.assertIn("session cookie jwt basics", expanded)
                self.assertIn("cookie session jwt browser flow", expanded)
                self.assertIn("http stateless login state", expanded)
                self.assertIn("login state persistence", expanded)
                self.assertIn("why login stays", expanded)
                self.assertNotIn("signature verification", expanded)

    def test_session_vs_jwt_english_shortform_stays_on_authentication_primer(self) -> None:
        prompt = "session vs JWT what is the difference?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "security_authentication",
        )
        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("security_authentication", tags)
        self.assertNotIn("security_token_validation", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("authentication", expanded)
        self.assertIn("session", expanded)
        self.assertNotIn("signature verification", expanded)

    def test_jpa_terms_route_to_spring_category(self) -> None:
        prompt = "JPA dirty checking 이 어떻게 hibernate 에서 동작해?"

        signals = signal_rules.detect_signals(prompt)
        self.assertTrue(signals)
        self.assertEqual(signals[0]["tag"], "spring_framework")

    def test_kotlin_coroutine_routes_to_language_general(self) -> None:
        prompt = "kotlin 의 coroutine 과 go 의 goroutine 차이가 뭐야?"

        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("language_runtime_general", tags)
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("coroutine", expanded)
        self.assertIn("goroutine", expanded)

    def test_rust_ownership_routes_to_language_general(self) -> None:
        prompt = "rust 의 ownership 과 borrow checker 가 왜 필요해?"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "language_runtime_general",
        )

    def test_migration_replay_cutover_terms_map_to_new_signal(self) -> None:
        prompt = "backfill replay repair reconciliation cutover guardrail"

        self.assertEqual(
            signal_rules.top_signal_tag(prompt),
            "migration_repair_cutover",
        )
        expanded = signal_rules.expand_query(prompt)
        self.assertIn("migration", expanded)
        self.assertIn("dual write", expanded)
        self.assertIn("reconciliation", expanded)


if __name__ == "__main__":
    unittest.main()
