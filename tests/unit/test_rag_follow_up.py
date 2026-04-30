from scripts.learning.rag.follow_up import is_follow_up


def test_korean_anaphora_short_prompt_is_follow_up():
    assert is_follow_up("그럼 왜 그래?")
    assert is_follow_up("이건 어떻게 해?")


def test_english_anaphora_short_prompt_is_follow_up():
    assert is_follow_up("then why?")
    assert is_follow_up("what about DI?")


def test_long_or_standalone_prompt_is_not_follow_up():
    assert not is_follow_up("트랜잭션 격리수준이 왜 필요한지 처음부터 설명해줘")
    assert not is_follow_up("Spring Bean이 뭐야?")
