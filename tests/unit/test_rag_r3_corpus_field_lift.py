from __future__ import annotations

import json

from scripts.learning.rag.r3.eval.corpus_field_lift import (
    corpus_v2_documents,
    main,
    run_corpus_field_lift,
)


def _write_doc(path, *, concept_id, aliases, expected_queries, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "schema_version: 2\n"
        f'title: "{concept_id}"\n'
        f"concept_id: {concept_id}\n"
        "difficulty: beginner\n"
        "doc_role: primer\n"
        "level: beginner\n"
        "aliases:\n"
        + "".join(f"  - {alias}\n" for alias in aliases)
        + "expected_queries:\n"
        + "".join(f"  - {query}\n" for query in expected_queries)
        + "---\n\n"
        + body
        + "\n",
        encoding="utf-8",
    )


def test_corpus_v2_documents_enable_only_selected_fields(tmp_path):
    corpus = tmp_path / "contents"
    _write_doc(
        corpus / "spring" / "di.md",
        concept_id="spring/di",
        aliases=["DI", "의존성 주입"],
        expected_queries=["DI가 뭐야?"],
        body="객체가 직접 만들지 않고 외부에서 협력 객체를 받는다.",
    )

    body_only = corpus_v2_documents(corpus, fields=("body",))
    alias_only = corpus_v2_documents(corpus, fields=("aliases",))

    assert body_only[0].path == "contents/spring/di.md"
    assert body_only[0].body.startswith("객체가 직접")
    assert body_only[0].aliases == ()
    assert alias_only[0].body == ""
    assert alias_only[0].aliases == ("DI", "의존성 주입")


def test_corpus_field_lift_shows_alias_recall_lift(tmp_path):
    corpus = tmp_path / "contents"
    _write_doc(
        corpus / "spring" / "di.md",
        concept_id="spring/di",
        aliases=["DI", "의존성 주입"],
        expected_queries=["DI가 뭐야?"],
        body="객체가 직접 생성하지 않고 외부에서 협력 객체를 받는 방식.",
    )
    _write_doc(
        corpus / "spring" / "ioc.md",
        concept_id="spring/ioc",
        aliases=["IoC"],
        expected_queries=["IoC가 뭐야?"],
        body="제어 흐름을 프레임워크가 가져가는 방식.",
    )

    report = run_corpus_field_lift(
        corpus,
        windows=(1,),
        field_runs={
            "body_only": ("body",),
            "body_aliases": ("body", "aliases"),
        },
    )

    body_rate = report["field_runs"]["body_only"]["summary"]["overall"][
        "candidate_recall_primary"
    ]["1"]
    alias_rate = report["field_runs"]["body_aliases"]["summary"]["overall"][
        "candidate_recall_primary"
    ]["1"]
    assert body_rate == 0.0
    assert alias_rate == 1.0
    assert report["query_count"] == 2


def test_corpus_field_lift_cli_writes_report(tmp_path):
    corpus = tmp_path / "contents"
    _write_doc(
        corpus / "network" / "latency.md",
        concept_id="network/latency",
        aliases=["latency"],
        expected_queries=["latency가 뭐야?"],
        body="지연 시간 설명.",
    )
    out = tmp_path / "reports" / "field-lift.json"

    rc = main(["--corpus-root", str(corpus), "--out", str(out), "--window", "1"])

    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["query_count"] == 1
