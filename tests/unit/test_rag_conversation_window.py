from scripts.learning.rag.conversation_window import recent_rag_ask_context


def test_recent_rag_ask_context_prefers_concepts_and_latest_events():
    history = [
        {"event_type": "rag_ask", "prompt": "old", "concept_ids": ["concept:old"]},
        {"event_type": "coach_run", "prompt": "skip"},
        {"event_type": "rag_ask", "prompt": "tx", "concept_ids": ["concept:tx"]},
        {
            "event_type": "rag_ask",
            "prompt": "spring",
            "concept_ids": ["concept:spring/bean", "concept:spring/di"],
        },
    ]

    assert recent_rag_ask_context(limit=2, history=history) == [
        "concepts=concept:spring/bean,concept:spring/di",
        "concepts=concept:tx",
    ]


def test_recent_rag_ask_context_falls_back_to_paths_categories_and_prompt():
    history = [
        {"event_type": "rag_ask", "prompt": "plain prompt"},
        {"event_type": "rag_ask", "top_paths": ["a.md", "b.md", "c.md"]},
        {"event_type": "rag_ask", "category_hits": ["database", "spring"]},
    ]

    assert recent_rag_ask_context(limit=3, history=history) == [
        "categories=database,spring",
        "paths=a.md,b.md",
        "plain prompt",
    ]
