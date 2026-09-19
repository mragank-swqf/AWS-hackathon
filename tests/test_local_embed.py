from app.services.local_ai import local_embed


def test_local_embed_is_1024_and_stable():
    first = local_embed("RBI payment aggregator shall maintain a grievance officer")
    second = local_embed("RBI payment aggregator shall maintain a grievance officer")
    assert len(first) == 1024
    assert first == second
    other = local_embed("totally unrelated kitchen recipe")
    assert first != other
