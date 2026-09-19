from app.config import get_settings
from app.services.openai_client import OpenAIUnavailableError, embed_openai, invoke_openai_chat


def test_openai_requires_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    try:
        try:
            invoke_openai_chat("hello")
        except OpenAIUnavailableError as exc:
            assert "OPENAI_API_KEY" in str(exc)
        else:
            raise AssertionError("expected missing key")
    finally:
        get_settings.cache_clear()


def test_openai_embed_returns_1024(monkeypatch, respx_mock):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()
    respx_mock.post("https://api.openai.com/v1/embeddings").respond(
        json={"data": [{"embedding": [0.1] * 1024}]}
    )
    try:
        vector = embed_openai("hello")
        assert len(vector) == 1024
    finally:
        get_settings.cache_clear()
