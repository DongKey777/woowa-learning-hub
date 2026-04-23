"""Regression tests for lightweight CS RAG signal detection.

These tests stay dependency-free and focus on the vocabulary that drives
query expansion plus fallback bucket keys. They justify targeted tuning
in ``signal_rules.py`` without requiring the full on-disk index.
"""

from __future__ import annotations

import unittest

from scripts.learning.rag import signal_rules


class CsRagSignalRulesTest(unittest.TestCase):
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

    def test_spring_transaction_terms_surface_spring_before_database(self) -> None:
        prompt = "@Transactional 안에서 bean 이 어떻게 트랜잭션 경계를 만들어?"

        tags = [signal["tag"] for signal in signal_rules.detect_signals(prompt)]
        self.assertIn("spring_framework", tags)
        # spring_framework should score at or above transaction_isolation
        self.assertEqual(tags[0], "spring_framework")

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
