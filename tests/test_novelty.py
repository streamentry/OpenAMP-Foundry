from openamp_foundry.scoring.novelty import normalized_similarity


def test_similarity_exact():
    assert normalized_similarity("ABC", "ABC") == 1.0


def test_similarity_lower_for_different_sequences():
    assert normalized_similarity("AAAA", "DDDD") < 0.5
