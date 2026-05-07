from scripts.workbench.core.corpus_signal_bridge import detect_corpus_signal_tags


def test_detect_corpus_signal_tags_reuses_signal_rules_vocabulary():
    assert "design-pattern:projection_freshness" in detect_corpus_signal_tags(
        "projection freshness 공부하고 싶어"
    )


def test_detect_corpus_signal_tags_degrades_to_empty_for_plain_study_prompt():
    assert detect_corpus_signal_tags("그냥 공부하고 싶어") == []

