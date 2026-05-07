---
schema_version: 3
title: Roaring Instrumentation Schema Examples
concept_id: data-structure/roaring-instrumentation-schema-examples
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- roaring-instrumentation-schema
- bitmap-observability-contract
- transition-event-schema
aliases:
- Roaring instrumentation schema
- Roaring metrics hook
- Roaring dashboard schema
- container transition event schema
- repairAfterLazy instrumentation
- runOptimize instrumentation
- high key transition log
symptoms:
- Java RoaringBitmap과 CRoaring 계측이 서로 다른 metric name/tag를 써서 대시보드에서 같은 현상을 합쳐 읽지 못한다
- high_key나 bitmap_id 같은 고카디널리티 label을 항상 켜 시계열 cardinality 폭발을 만든다
- phase, op, owner, before/after type, repair_kind를 고정하지 않아 ingest churn과 query repair churn이 섞인다
intents:
- design
- troubleshooting
prerequisites:
- data-structure/roaring-production-profiling-checklist
- data-structure/roaring-run-churn-observability-guide
next_docs:
- data-structure/roaring-intermediate-repair-path-guide
- data-structure/roaring-run-optimize-timing-guide
- data-structure/roaring-run-formation-and-row-ordering
linked_paths:
- contents/data-structure/roaring-bitmap.md
- contents/data-structure/roaring-container-transition-heuristics.md
- contents/data-structure/roaring-intermediate-repair-path-guide.md
- contents/data-structure/roaring-run-optimize-timing-guide.md
- contents/data-structure/roaring-production-profiling-checklist.md
- contents/data-structure/roaring-run-churn-observability-guide.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
confusable_with:
- data-structure/roaring-production-profiling-checklist
- data-structure/roaring-run-churn-observability-guide
- data-structure/roaring-intermediate-repair-path-guide
- data-structure/roaring-container-transition-heuristics
forbidden_neighbors: []
expected_queries:
- Roaring Bitmap 운영 계측에서 phase op high_key before_type after_type 같은 event schema를 어떻게 잡아?
- Java RoaringBitmap과 CRoaring을 같은 dashboard에서 비교하려면 metric contract를 어떻게 맞춰?
- high_key를 시계열 label로 올리지 않고 sampled hotspot event로 남겨야 하는 이유는?
- repairAfterLazy runOptimize container transition을 관측하는 schema 예시를 보여줘
- Roaring observability에서 low-cardinality rollup과 sampled transition event를 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 Roaring Bitmap observability를 위한 instrumentation schema
  playbook이다. phase, op, owner, high_key, before/after type, repair_kind,
  sample_rate를 공통 event contract로 고정하고 Java/CRoaring 계측과 dashboard
  cardinality를 관리한다.
---
# Roaring Instrumentation Schema Examples

> 한 줄 요약: Roaring 운영 계측은 라이브러리별 metric 이름보다 `phase`, `op`, `owner`, `high_key`, `before/after` 같은 공통 스키마를 먼저 고정하고, Java `RoaringBitmap`과 CRoaring에서 같은 snapshot/diff emitter를 두는 편이 가장 안정적이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Intermediate Repair Path Guide](./roaring-intermediate-repair-path-guide.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)

> retrieval-anchor-keywords: roaring instrumentation schema, roaring java metrics hook, roaring croaring metrics hook, roaring chunk event schema, roaring transition event schema, roaring dashboard schema, roaring run metrics, repairAfterLazy instrumentation, runOptimize instrumentation, roaring sampled hotspot event, roaring observability emitter, high key transition log, container snapshot schema, low cardinality roaring metrics, roaring metrics bridge, roaring prometheus metrics, roaring opentelemetry metrics, roaring otel meter, roaring exemplar sampling, roaring metric naming examples

## 핵심 개념

Roaring observability에서 가장 먼저 고정해야 하는 것은 metric backend가 아니라 **데이터 계약**이다.

같은 `array -> bitmap` churn을 보더라도:

- Java 쪽은 `highLowContainer` snapshot 기반으로 잡고
- CRoaring 쪽은 `high_low_container`와 `typecodes` 기반으로 잡고
- 대시보드는 `phase`, `op`, `before_type`, `after_type`, `runs`, `cpu_ns`로 해석한다

처럼 층이 나뉜다.

이때 schema를 먼저 고정하지 않으면:

- Java는 `runOptimize` bytes delta만 남기고
- C는 container count만 남기고
- 대시보드는 서로 다른 tag 조합 때문에 합쳐지지 않는다

즉 구현 언어가 달라도 아래 세 종류의 artifact는 같게 가져가는 편이 좋다.

| artifact | 목적 | cardinality 원칙 |
|---|---|---|
| chunk rollup | 대시보드용 저카디널리티 집계 | `bitmap_family`, `phase`, `op`, band 수준까지만 |
| sampled transition event | hot chunk drill-down | `bitmap_id_hash`, `segment_id`, `high_key`까지 허용 |
| dashboard schema | 패널/alert 의미 고정 | metric 이름보다 panel meaning을 먼저 고정 |

## 1. 먼저 고정할 canonical event 필드

실전에서는 "무슨 metric을 만들지"보다 "이 이벤트가 어떤 의미를 갖는지"를 먼저 맞추는 편이 덜 흔들린다.

| 필드 | 예시 | 왜 필요한가 |
|---|---|---|
| `bitmap_family` | `segment_membership` | 사용자 세그먼트, warehouse bitmap, query cache 결과를 분리한다 |
| `bitmap_id_hash` | `sha256:6f3d...` | sampled event drill-down 키로 쓰되 raw label 폭발을 막는다 |
| `segment_id` | `seg-0421` | shard/segment hotspot을 찾는다 |
| `phase` | `build`, `update`, `query_result`, `repair`, `optimize` | ingest와 query churn을 분리한다 |
| `owner` | `persisted`, `intermediate` | 저장 bitmap과 request-scoped 결과를 분리한다 |
| `op` | `add`, `remove`, `or`, `xor`, `runOptimize` | 같은 transition도 원인 연산이 다르다 |
| `high_key` | `183` | hotspot chunk 식별자다 |
| `before_type`, `after_type` | `array`, `bitmap`, `run` | transition 해석의 핵심이다 |
| `cardinality_before`, `cardinality_after` | `4091`, `4122` | `4096` 경계 압력을 본다 |
| `runs_before`, `runs_after` | `11`, `143` | run fragmentation을 본다 |
| `bytes_before`, `bytes_after` | `38`, `8192` | transition당 rewrite 크기를 본다 |
| `repair_kind` | `none`, `repairAfterLazy`, `toEfficientContainer`, `runOptimize` | finalize/repair 경로를 구분한다 |
| `cpu_ns` | `23100` | transition count와 비용을 분리한다 |
| `sample_rate` | `0.02` | sampled event 해석 오차를 관리한다 |

sampled transition event 예시는 아래 정도면 충분하다.

```json
{
  "event_name": "roaring.container.transition.v1",
  "ts_unix_ms": 1776133812488,
  "service": "audience-api",
  "bitmap_family": "segment_membership",
  "bitmap_id_hash": "sha256:6f3d9c8a",
  "segment_id": "seg-0421",
  "phase": "repair",
  "owner": "intermediate",
  "op": "or",
  "high_key": 183,
  "before_type": "run",
  "after_type": "bitmap",
  "cardinality_before": 4112,
  "cardinality_after": 4188,
  "runs_before": 9,
  "runs_after": 137,
  "bytes_before": 38,
  "bytes_after": 8192,
  "repair_kind": "repairAfterLazy",
  "cpu_ns": 23100,
  "sample_rate": 0.02
}
```

핵심은 `최종 타입`만 남기지 않고 **`before/after`를 함께 남기는 것**이다.
여기서 `cpu_ns`는 sampled chunk event를 생성한 **operation 전체 시간**으로 두고, 합계는 rollup metric에서만 계산하는 편이 안전하다.

## 2. Java `RoaringBitmap` hook 예시

Java 쪽은 bitmap-wide timing만 보면 public API로도 충분하지만,  
**chunk-local snapshot과 repair hook**은 작은 bridge가 필요하다.

실전 감각은 아래처럼 잡으면 된다.

- `checkedAdd`, `checkedRemove`, `runOptimize`, `serializedSizeInBytes`, `getCardinality`는 public 경계라 wrapper가 쉽다
- `highLowContainer`, `Container.numberOfRuns()`, `repairAfterLazy()`는 package/protected 범위라 `org.roaringbitmap` 안쪽 bridge나 shaded fork가 있어야 한다
- 그래서 Java에서는 "계측 bridge를 같은 package에 둔다"가 가장 현실적인 해법이다

아래 예시는 `org.roaringbitmap` 패키지 안에 두는 bridge다.

```java
package org.roaringbitmap;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class RoaringMetricsBridge {
  public interface TransitionSink {
    void emitRollup(String name, long value, Map<String, String> tags);
    void emitTransition(TransitionEvent event);
  }

  public record ChunkSnapshot(
      int highKey,
      String type,
      int cardinality,
      int runs,
      int serializedBytes) {}

  public record TransitionEvent(
      String bitmapFamily,
      String bitmapIdHash,
      String phase,
      String op,
      int highKey,
      ChunkSnapshot before,
      ChunkSnapshot after,
      String repairKind,
      long cpuNs) {}

  public static boolean checkedAddWithMetrics(
      String bitmapFamily,
      String bitmapIdHash,
      RoaringBitmap bitmap,
      int value,
      TransitionSink sink) {
    int highKey = value >>> 16;
    ChunkSnapshot before = snapshotOne(bitmap, highKey);
    long startNs = System.nanoTime();
    boolean changed = bitmap.checkedAdd(value);
    long cpuNs = System.nanoTime() - startNs;
    if (changed) {
      emitSingleKeyDiff(
          bitmapFamily,
          bitmapIdHash,
          "update",
          "add",
          "none",
          highKey,
          before,
          snapshotOne(bitmap, highKey),
          cpuNs,
          sink);
    }
    return changed;
  }

  public static boolean runOptimizeWithMetrics(
      String bitmapFamily,
      String bitmapIdHash,
      String phase,
      String op,
      RoaringBitmap bitmap,
      TransitionSink sink) {
    List<ChunkSnapshot> before = snapshotAll(bitmap);
    int bytesBefore = bitmap.serializedSizeInBytes();
    long startNs = System.nanoTime();
    boolean changed = bitmap.runOptimize();
    long cpuNs = System.nanoTime() - startNs;
    List<ChunkSnapshot> after = snapshotAll(bitmap);
    emitDiff(bitmapFamily, bitmapIdHash, phase, op, "runOptimize", before, after, cpuNs, sink);
    sink.emitRollup(
        "roaring_run_optimize_bytes_delta",
        bytesBefore - bitmap.serializedSizeInBytes(),
        Map.of("bitmap_family", bitmapFamily, "phase", phase, "op", op));
    return changed;
  }

  public static void repairAfterLazyWithMetrics(
      String bitmapFamily,
      String bitmapIdHash,
      String op,
      RoaringBitmap bitmap,
      TransitionSink sink) {
    List<ChunkSnapshot> before = snapshotAll(bitmap);
    long startNs = System.nanoTime();
    bitmap.repairAfterLazy();
    long cpuNs = System.nanoTime() - startNs;
    emitDiff(bitmapFamily, bitmapIdHash, "repair", op, "repairAfterLazy", before, snapshotAll(bitmap), cpuNs, sink);
  }

  private static List<ChunkSnapshot> snapshotAll(RoaringBitmap bitmap) {
    ArrayList<ChunkSnapshot> out = new ArrayList<>(bitmap.highLowContainer.size());
    for (int i = 0; i < bitmap.highLowContainer.size(); i++) {
      out.add(snapshotAt(bitmap, i));
    }
    return out;
  }

  private static ChunkSnapshot snapshotOne(RoaringBitmap bitmap, int highKey) {
    for (int i = 0; i < bitmap.highLowContainer.size(); i++) {
      if ((bitmap.highLowContainer.getKeyAtIndex(i) & 0xFFFF) == highKey) {
        return snapshotAt(bitmap, i);
      }
    }
    return null;
  }

  private static ChunkSnapshot snapshotAt(RoaringBitmap bitmap, int index) {
    Container c = bitmap.highLowContainer.getContainerAtIndex(index);
    return new ChunkSnapshot(
        bitmap.highLowContainer.getKeyAtIndex(index) & 0xFFFF,
        typeOf(c),
        c.getCardinality(),
        c.numberOfRuns(),
        c.serializedSizeInBytes());
  }

  private static void emitDiff(
      String bitmapFamily,
      String bitmapIdHash,
      String phase,
      String op,
      String repairKind,
      List<ChunkSnapshot> before,
      List<ChunkSnapshot> after,
      long cpuNs,
      TransitionSink sink) {
    Map<Integer, ChunkSnapshot> beforeByKey = new HashMap<>();
    for (ChunkSnapshot snapshot : before) {
      beforeByKey.put(snapshot.highKey(), snapshot);
    }
    for (ChunkSnapshot current : after) {
      ChunkSnapshot previous = beforeByKey.remove(current.highKey());
      if (previous == null || !previous.equals(current)) {
        emitSingleKeyDiff(
            bitmapFamily,
            bitmapIdHash,
            phase,
            op,
            repairKind,
            current.highKey(),
            previous,
            current,
            cpuNs,
            sink);
      }
    }
    for (ChunkSnapshot removed : beforeByKey.values()) {
      emitSingleKeyDiff(
          bitmapFamily,
          bitmapIdHash,
          phase,
          op,
          repairKind,
          removed.highKey(),
          removed,
          null,
          cpuNs,
          sink);
    }
  }

  private static void emitSingleKeyDiff(
      String bitmapFamily,
      String bitmapIdHash,
      String phase,
      String op,
      String repairKind,
      int highKey,
      ChunkSnapshot before,
      ChunkSnapshot after,
      long cpuNs,
      TransitionSink sink) {
    ChunkSnapshot effective = after != null ? after : before;
    sink.emitRollup(
        "roaring_chunk_runs_bucket",
        effective == null ? 0 : effective.runs(),
        Map.of(
            "bitmap_family", bitmapFamily,
            "phase", phase,
            "op", op,
            "type", effective == null ? "none" : effective.type()));
    sink.emitTransition(
        new TransitionEvent(
            bitmapFamily,
            bitmapIdHash,
            phase,
            op,
            highKey,
            before,
            after,
            repairKind,
            cpuNs));
  }

  private static String typeOf(Container c) {
    if (c instanceof ArrayContainer) return "array";
    if (c instanceof BitmapContainer) return "bitmap";
    if (c instanceof RunContainer) return "run";
    return "unknown";
  }
}
```

이 bridge가 주는 운영상 장점은 단순하다.

- `checkedAdd`/`checkedRemove`는 **한 개 `high_key`만 diff**하면 되므로 sampled transition event를 매우 싸게 만들 수 있다
- `runOptimize()`와 `repairAfterLazy()`는 **before/after 전체 snapshot**을 한 번 비교해 transition CPU와 bytes delta를 함께 남길 수 있다
- 대시보드용 rollup과 hotspot event를 같은 sink에서 분기할 수 있다

주의할 점도 있다.

- Java public API만으로는 `repairAfterLazy()`와 container-level run count를 직접 보기 어렵다
- bridge를 둘 수 없다면 bitmap-wide `getCardinality()`, `serializedSizeInBytes()`, `runOptimize()` timing만 남기고 chunk event는 sampled log로만 보내는 편이 낫다

## 3. CRoaring hook 예시

CRoaring은 `roaring_bitmap_t` 안에 `high_low_container`가 직접 들어 있어 **chunk-local snapshot 접근은 더 쉽다**.  
대신 per-container run 수와 byte size는 `containers/` 헤더를 함께 써야 하므로, 이 경로는 public surface보다 한 단계 더 내부 지향적이다.

아래 예시는 update와 optimize 경계를 계측하는 wrapper다.

```c
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <roaring/roaring.h>
#include <roaring/containers/array.h>
#include <roaring/containers/bitset.h>
#include <roaring/containers/containers.h>
#include <roaring/containers/run.h>

typedef struct {
  uint16_t high_key;
  uint8_t typecode;
  uint32_t cardinality;
  uint32_t runs;
  uint32_t bytes;
} chunk_snapshot_t;

typedef struct metrics_sink_s metrics_sink_t;
void sink_transition(metrics_sink_t *sink, const char *phase, const char *op,
                     uint16_t high_key, const chunk_snapshot_t *before,
                     const chunk_snapshot_t *after, const char *repair_kind,
                     uint64_t cpu_ns);
void sink_rollup(metrics_sink_t *sink, const char *name, uint64_t value,
                 const char *phase, const char *op, const char *type);
uint64_t now_ns(void);

static uint32_t container_runs(container_t *c, uint8_t typecode) {
  switch (typecode) {
    case ARRAY_CONTAINER_TYPE:
      return (uint32_t)array_container_number_of_runs((const array_container_t *)c);
    case BITSET_CONTAINER_TYPE:
      return (uint32_t)bitset_container_number_of_runs((bitset_container_t *)c);
    case RUN_CONTAINER_TYPE:
      return (uint32_t)((const run_container_t *)c)->n_runs;
    default:
      return 0;
  }
}

static bool snapshot_one(const roaring_bitmap_t *bitmap, uint16_t high_key,
                         chunk_snapshot_t *out) {
  const roaring_array_t *ra = &bitmap->high_low_container;
  for (int32_t i = 0; i < ra->size; ++i) {
    if (ra->keys[i] != high_key) {
      continue;
    }
    container_t *container = ra->containers[i];
    uint8_t typecode = ra->typecodes[i];
    *out = (chunk_snapshot_t) {
        .high_key = high_key,
        .typecode = typecode,
        .cardinality = (uint32_t)container_get_cardinality(container, typecode),
        .runs = container_runs(container, typecode),
        .bytes = (uint32_t)container_size_in_bytes(container, typecode),
    };
    return true;
  }
  memset(out, 0, sizeof(*out));
  out->high_key = high_key;
  return false;
}

static const char *type_name(uint8_t typecode) {
  switch (typecode) {
    case ARRAY_CONTAINER_TYPE: return "array";
    case BITSET_CONTAINER_TYPE: return "bitmap";
    case RUN_CONTAINER_TYPE: return "run";
    default: return "unknown";
  }
}

bool roaring_add_checked_with_metrics(roaring_bitmap_t *bitmap, uint32_t value,
                                      metrics_sink_t *sink) {
  uint16_t high_key = (uint16_t)(value >> 16);
  chunk_snapshot_t before;
  chunk_snapshot_t after;
  snapshot_one(bitmap, high_key, &before);
  uint64_t start_ns = now_ns();
  bool changed = roaring_bitmap_add_checked(bitmap, value);
  uint64_t cpu_ns = now_ns() - start_ns;
  if (!changed) {
    return false;
  }
  snapshot_one(bitmap, high_key, &after);
  sink_transition(sink, "update", "add", high_key, &before, &after, "none", cpu_ns);
  sink_rollup(sink, "roaring_chunk_runs_bucket", after.runs, "update", "add", type_name(after.typecode));
  return true;
}

bool roaring_run_optimize_with_metrics(roaring_bitmap_t *bitmap,
                                       metrics_sink_t *sink) {
  roaring_statistics_t before_stats = {0};
  roaring_statistics_t after_stats = {0};
  roaring_bitmap_statistics(bitmap, &before_stats);
  size_t bytes_before = roaring_bitmap_portable_size_in_bytes(bitmap);
  uint64_t start_ns = now_ns();
  bool changed = roaring_bitmap_run_optimize(bitmap);
  uint64_t cpu_ns = now_ns() - start_ns;
  roaring_bitmap_statistics(bitmap, &after_stats);

  sink_rollup(sink, "roaring_run_optimize_cpu_ns_total", cpu_ns, "optimize", "runOptimize", "bitmap");
  sink_rollup(
      sink,
      "roaring_run_optimize_bytes_delta",
      bytes_before - roaring_bitmap_portable_size_in_bytes(bitmap),
      "optimize",
      "runOptimize",
      "bitmap");
  sink_rollup(
      sink,
      "roaring_run_container_delta",
      (uint64_t)after_stats.n_run_containers - (uint64_t)before_stats.n_run_containers,
      "optimize",
      "runOptimize",
      "run");
  return changed;
}
```

CRoaring 쪽 해석 포인트는 아래 셋이다.

- point update는 touched `high_key` 하나만 보면 되므로 transition event를 싸게 만든다
- wide `OR`/`XOR` 결과는 `roaring_bitmap_statistics()`로 먼저 chunk/run mix를 보고, 문제가 생길 때만 sampled chunk snapshot을 붙인다
- `roaring_bitmap_portable_size_in_bytes()` delta를 같이 남기면 runOptimize가 실제로 이득을 줬는지 바로 보인다

즉 CRoaring은 Java보다 bridge는 덜 필요하지만,  
**`containers/*.h`를 쓰는 만큼 버전 업그레이드 시 내부 타입 의존성을 같이 점검해야 한다**.

## 4. 항상 켜둘 rollup schema 예시

대시보드가 받아야 하는 데이터는 sampled event 원문이 아니라, 아래 같은 **저카디널리티 rollup row**가 더 안정적이다.

```json
{
  "event_name": "roaring.chunk.rollup.v1",
  "ts_unix_ms": 1776133812488,
  "service": "audience-api",
  "bitmap_family": "segment_membership",
  "phase": "update",
  "op": "add",
  "owner": "persisted",
  "container_type": "bitmap",
  "cardinality_band": "4097_4608",
  "run_band": "129_256",
  "chunk_count": 14,
  "cpu_ns_total": 105000,
  "bytes_delta_total": 32768,
  "sample_rate": 1.0
}
```

여기서 중요한 규칙은 아래와 같다.

- `bitmap_id_hash`, `high_key`는 rollup에 올리지 않는다
- boundary pressure panel에는 `cardinality_band`만 올린다
- run fragmentation panel에는 `run_band`와 `container_type`만 올린다
- transition panel에는 `before_type`, `after_type` 집계만 올리고 개별 key는 sampled event로 보낸다

추천 metric family는 아래 정도면 충분하다.

| metric | type | label 예시 | 의미 |
|---|---|---|---|
| `roaring_chunk_cardinality_bucket` | counter or histogram | `bitmap_family`, `phase`, `op`, `cardinality_band` | `4096` 경계 압력 |
| `roaring_chunk_runs_bucket` | counter or histogram | `bitmap_family`, `phase`, `op`, `run_band`, `type` | run fragmentation tail |
| `roaring_container_transition_total` | counter | `phase`, `op`, `before_type`, `after_type`, `repair_kind` | transition 횟수 |
| `roaring_container_transition_cpu_ns_total` | counter | `phase`, `op`, `before_type`, `after_type` | transition 비용 |
| `roaring_run_optimize_bytes_delta` | counter | `phase="optimize"`, `op="runOptimize"` | optimize payoff |
| `roaring_intermediate_result_type_total` | counter | `phase`, `op`, `type` | query result shape |

이 표는 **backend-neutral logical schema**로 보면 된다.

- Prometheus처럼 monotonic counter 위주 backend는 `bytes_delta`를 그대로 누적하지 말고 `saved`/`expanded` 두 방향으로 쪼개는 편이 안전하다
- OpenTelemetry는 histogram / `UpDownCounter`로 numeric 분포를 더 자연스럽게 들고 갈 수 있다
- sampled hotspot event와 trace/span은 raw `high_key`, signed delta, `sample_rate`를 남기되 rollup metric label에는 올리지 않는다

### Prometheus metric naming 예시

Prometheus 쪽은 `snake_case` 이름에 `*_total` 규칙을 맞추고, semantic band는 **label 값**으로 고정하는 편이 운영자가 읽기 쉽다.

| 관측 질문 | Prometheus metric | type | 권장 label |
|---|---|---|---|
| 어떤 transition이 얼마나 자주 일어나는가 | `roaring_container_transition_total` | counter | `bitmap_family`, `phase`, `op`, `owner`, `before_type`, `after_type`, `repair_kind` |
| transition rewrite CPU를 얼마나 먹는가 | `roaring_container_transition_cpu_ns_total` | counter | `bitmap_family`, `phase`, `op`, `owner`, `before_type`, `after_type`, `repair_kind` |
| `4096` 근처 boundary pressure가 올라오는가 | `roaring_chunk_cardinality_band_total` | counter | `bitmap_family`, `phase`, `op`, `owner`, `cardinality_band` |
| run fragmentation tail이 두꺼워지는가 | `roaring_chunk_runs_band_total` | counter | `bitmap_family`, `phase`, `op`, `owner`, `container_type`, `run_band` |
| `runOptimize()`가 실제로 byte를 줄였는가 | `roaring_run_optimize_bytes_saved_total` | counter | `bitmap_family`, `phase="optimize"`, `op="runOptimize"`, `owner` |
| `runOptimize()`가 오히려 byte를 늘렸는가 | `roaring_run_optimize_bytes_expanded_total` | counter | `bitmap_family`, `phase="optimize"`, `op="runOptimize"`, `owner` |
| query 결과 shape가 어느 타입으로 귀결되는가 | `roaring_intermediate_result_type_total` | counter | `bitmap_family`, `phase`, `op`, `owner`, `type` |

Prometheus에서 특히 중요한 제약은 아래 셋이다.

- `segment_id`, `bitmap_id_hash`, `high_key`는 **metric label 금지**고 sampled event/log/trace에서만 쓴다
- `service`, `job`, `instance`는 scrape 계층이 붙이게 두고 instrumentation label로 중복하지 않는다
- `bytes_delta`는 signed 값이므로 counter 하나로 밀어 넣지 않는다

sample exposition은 아래 정도면 충분하다.

```text
# TYPE roaring_container_transition_total counter
roaring_container_transition_total{bitmap_family="segment_membership",phase="repair",op="or",owner="intermediate",before_type="run",after_type="bitmap",repair_kind="repairAfterLazy"} 128

# TYPE roaring_container_transition_cpu_ns_total counter
roaring_container_transition_cpu_ns_total{bitmap_family="segment_membership",phase="repair",op="or",owner="intermediate",before_type="run",after_type="bitmap",repair_kind="repairAfterLazy"} 347281000

# TYPE roaring_chunk_cardinality_band_total counter
roaring_chunk_cardinality_band_total{bitmap_family="segment_membership",phase="update",op="add",owner="persisted",cardinality_band="4097_4608"} 1423

# TYPE roaring_run_optimize_bytes_saved_total counter
roaring_run_optimize_bytes_saved_total{bitmap_family="segment_membership",phase="optimize",op="runOptimize",owner="persisted"} 7340032
```

대시보드/alert query도 band label을 그대로 쓴다.

```promql
sum by (bitmap_family, phase) (
  rate(roaring_chunk_cardinality_band_total{cardinality_band="4097_4608"}[5m])
)
/
clamp_min(
  sum by (bitmap_family, phase) (
    rate(roaring_chunk_cardinality_band_total[5m])
  ),
  1
)
```

이런 식이면 `4096` 경계 근처 chunk 비중이 갑자기 튀는 시점을 바로 잡을 수 있다.

### OpenTelemetry instrument naming 예시

OpenTelemetry는 metric 이름과 unit metadata를 분리하므로, instrument는 dotted name으로 logical schema를 드러내고 exporter/view에서 Prometheus alias를 맞추는 편이 가장 덜 흔들린다.

| OTel instrument | instrument kind | unit | low-cardinality attribute 예시 | bucket / aggregation 예시 |
|---|---|---|---|---|
| `roaring.container.transition` | Counter | `{transition}` | `bitmap.family`, `phase`, `op`, `owner`, `before.type`, `after.type`, `repair.kind` | sum |
| `roaring.container.transition.cpu` | Counter | `ns` | `bitmap.family`, `phase`, `op`, `owner`, `before.type`, `after.type`, `repair.kind` | sum |
| `roaring.chunk.cardinality` | Histogram | `{entry}` | `bitmap.family`, `phase`, `op`, `owner` | explicit buckets `64,256,1024,2048,3584,4096,4608,8192,16384,32768,65536` |
| `roaring.chunk.runs` | Histogram | `{run}` | `bitmap.family`, `phase`, `op`, `owner`, `container.type` | explicit buckets `1,2,4,8,16,32,64,128,256,512` |
| `roaring.run.optimize.bytes.delta` | UpDownCounter | `By` | `bitmap.family`, `phase`, `op`, `owner` | signed sum |
| `roaring.intermediate.result` | Counter | `{result}` | `bitmap.family`, `phase`, `op`, `owner`, `type` | sum |

개념상 meter wiring은 아래처럼 둔다.

```java
LongCounter transitions =
    meter.counterBuilder("roaring.container.transition")
        .setUnit("{transition}")
        .build();

LongHistogram chunkCardinality =
    meter.histogramBuilder("roaring.chunk.cardinality")
        .ofLongs()
        .setUnit("{entry}")
        .build();

LongUpDownCounter runOptimizeBytesDelta =
    meter.upDownCounterBuilder("roaring.run.optimize.bytes.delta")
        .setUnit("By")
        .build();
```

OpenTelemetry를 쓸 때도 raw hotspot key는 metric attribute가 아니라 **sampled span event**나 log record로 보내는 편이 맞다.

```json
{
  "span_name": "roaring.container.transition",
  "attributes": {
    "roaring.bitmap_family": "segment_membership",
    "roaring.phase": "repair",
    "roaring.op": "or",
    "roaring.owner": "intermediate",
    "roaring.high_key": 183,
    "roaring.before_type": "run",
    "roaring.after_type": "bitmap",
    "roaring.repair_kind": "repairAfterLazy",
    "roaring.sample_rate": 0.25,
    "roaring.sampling_reason": "boundary_band+repair_hotspot"
  }
}
```

이렇게 두면 Prometheus 쪽 panel은 low-cardinality 시계열로 유지되고, exemplar나 trace pivot으로만 `high_key` drill-down을 여는 구성이 가능하다.

### Sampling policy 예시

운영 패턴은 `rollup metric = 100%`, `sampled transition event/span = adaptive deterministic`, `full snapshot dump = manual` 세 층으로 고정하는 편이 가장 안전하다.

| 계층 | 기본 sample rate | 언제 rate를 올리나 | 남기는 필드 |
|---|---|---|---|
| rollup metric | `1.0` | 올리지 않음 | `bitmap_family`, `phase`, `op`, `owner`, `band/type` |
| transition event / span | `0.02` | `3584..4608` boundary band, `runs_after >= 128`, `repair_kind != none`, `cpu_ns >= 20000` | `high_key`, `before/after`, `bytes_*`, `sample_rate`, `sampling_reason` |
| full snapshot dump | `0` by default | manual debug flag나 incident capture 때만 `1.0` | container array 전체 |

deterministic sampler 예시는 아래처럼 잡으면 재현성이 좋다.

```text
sample_rate = 0.02
if 3584 <= cardinality_after && cardinality_after <= 4608:
  sample_rate = max(sample_rate, 0.25)
if runs_after >= 128:
  sample_rate = max(sample_rate, 0.50)
if repair_kind != "none" && cpu_ns >= 20000:
  sample_rate = 1.0

sample_key = bitmap_id_hash + "|" + high_key + "|" + phase + "|" + op + "|" + minute_bucket
emit_transition_event = xxhash64(sample_key) < sample_rate * UINT64_MAX
```

이 규칙이 좋은 이유는 아래와 같다.

- 같은 `bitmap_id_hash/high_key/op` 조합은 같은 minute bucket 안에서 **같이 잡히거나 같이 빠지므로** hotspot 추세가 덜 흔들린다
- `4096` 경계 근처, run tail 악화, repair hotspot만 sample rate를 올리면 전체 비용은 낮게 유지하면서 문제 chunk는 거의 놓치지 않는다
- sampled event는 항상 `sample_rate`를 싣고, rollup metric은 별도 100% emit이므로 나중에 둘을 섞어 해석해도 bias가 적다

## 5. 대시보드 schema 예시

대시보드도 "패널 이름"보다 **어떤 metric 조합을 어떤 질문에 쓰는가**를 문서화해 두는 편이 좋다.

```json
{
  "dashboard_id": "roaring-churn-v1",
  "filters": ["service", "bitmap_family", "phase", "op", "segment_id"],
  "panels": [
    {
      "id": "boundary-pressure",
      "title": "4096 Boundary Pressure",
      "kind": "stacked-area",
      "metrics": ["roaring_chunk_cardinality_bucket"],
      "where": {"cardinality_band": ["3584_4096", "4097_4608"]},
      "group_by": ["phase", "cardinality_band"]
    },
    {
      "id": "transition-cpu-share",
      "title": "Transition CPU Share",
      "kind": "timeseries",
      "metrics": [
        "roaring_container_transition_cpu_ns_total",
        "roaring_total_cpu_ns"
      ],
      "formula": "sum(roaring_container_transition_cpu_ns_total) / sum(roaring_total_cpu_ns)",
      "group_by": ["phase", "op", "before_type", "after_type"]
    },
    {
      "id": "run-fragmentation-tail",
      "title": "Run Fragmentation Tail",
      "kind": "heatmap",
      "metrics": ["roaring_chunk_runs_bucket"],
      "group_by": ["run_band", "type"]
    },
    {
      "id": "sampled-hotspots",
      "title": "Sampled Hotspot Events",
      "kind": "table",
      "source": "roaring.container.transition.v1",
      "columns": [
        "ts_unix_ms",
        "phase",
        "op",
        "high_key",
        "before_type",
        "after_type",
        "runs_before",
        "runs_after",
        "cpu_ns"
      ]
    }
  ]
}
```

이 schema를 써두면 언어별 구현이 달라도 대시보드 질문은 고정된다.

- boundary panel: `4096` 경계 churn이 올라오는가
- transition CPU panel: container 재작성 자체가 latency를 먹는가
- run tail panel: fragmentation이 진행 중인가
- hotspot table: 어느 `high_key`가 실제 사건을 만들었는가

## 6. 운영 적용 순서

한 번에 다 넣으려 하지 말고 아래 순서로 쪼개는 편이 실패가 적다.

1. bitmap-wide timing과 bytes delta부터 넣는다
2. touched `high_key` 하나만 바뀌는 update path에 sampled transition event를 붙인다
3. `runOptimize`, `repairAfterLazy`, cache publish 같은 finalize 경계에 전체 snapshot diff를 붙인다
4. 마지막에 dashboard schema와 alert rule을 고정한다

특히 `wide OR/XOR` 같은 query 결과는 처음부터 모든 chunk를 log로 남기지 않는 편이 좋다.

- 항상 켜둘 것은 rollup
- 사건이 터질 때만 sampled event
- deep debug 때만 full snapshot dump

이 세 단계를 섞지 않아야 시계열 cardinality가 버틴다.

## 꼬리질문

> Q: Java와 CRoaring이 다른 API를 가지는데 왜 schema를 먼저 맞추나요?
> 의도: 구현 surface와 관측 contract를 분리하는지 확인
> 핵심: 대시보드는 `phase/op/high_key/before-after`를 해석하지 라이브러리 메서드 이름을 해석하지 않기 때문이다.

> Q: raw `bitmap_id`, `high_key`를 metric label로 그냥 올리면 더 정확하지 않나요?
> 의도: observability cardinality cost를 아는지 확인
> 핵심: sampled event에는 괜찮지만 rollup metric label로 올리면 시계열 수가 먼저 터진다.

> Q: 왜 `runOptimize`와 `repairAfterLazy`를 따로 봐야 하나요?
> 의도: correctness 경계와 compression 경계를 구분하는지 확인
> 핵심: `repairAfterLazy`는 lazy 결과 정규화이고, `runOptimize`는 stable shape를 다시 run으로 압축하는 cold-path finalize다.

## 한 줄 정리

Roaring instrumentation은 "Java에선 어떤 메서드, C에선 어떤 함수"보다, **공통 `transition event + chunk rollup + dashboard schema`를 먼저 고정하고 각 구현에서 snapshot/diff bridge를 맞추는 방식**이 가장 오래 버틴다.
