from scripts.workbench.core.corpus_signal_bridge import (
    detect_corpus_phrase_tags,
    detect_corpus_signal_tags,
)


def test_detect_corpus_signal_tags_reuses_signal_rules_vocabulary():
    assert "design-pattern:projection_freshness" in detect_corpus_signal_tags(
        "projection freshness 공부하고 싶어"
    )


def test_detect_corpus_signal_tags_degrades_to_empty_for_plain_study_prompt():
    assert detect_corpus_signal_tags("그냥 공부하고 싶어") == []


def test_detect_corpus_phrase_tags_uses_frontmatter_aliases():
    assert "database:corpus_phrase" in detect_corpus_phrase_tags("XA 공부하고 싶어")
    assert "database:corpus_phrase" in detect_corpus_signal_tags("2PC 공부하고 싶어")


def test_detect_corpus_phrase_tags_rejects_unrelated_design_prompt():
    assert detect_corpus_phrase_tags("우리 인테리어 설계 공부하고 싶어") == []
