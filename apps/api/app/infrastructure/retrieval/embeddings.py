import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_TIMEOUT = 30


class EmbeddingService:
    """
    Generates embeddings via OpenRouter's /v1/embeddings endpoint.

    Falls back to SHA-256 placeholder if the API key is not configured,
    so the pipeline can still run end-to-end during development.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_embedding_model
        self._url = "https://openrouter.ai/api/v1/embeddings"

    def embed(self, text: str) -> list[float]:
        if not self._api_key:
            return self._placeholder_embed(text)

        try:
            return self._embed_via_api(text)
        except Exception as exc:
            logger.warning("Embedding API call failed, falling back to placeholder", exc_info=exc)
            return self._placeholder_embed(text)

    def _embed_via_api(self, text: str) -> list[float]:
        payload = {
            "model": self._model,
            "input": text,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=EMBEDDING_TIMEOUT) as client:
            response = client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["data"][0]["embedding"]

    @staticmethod
    def _placeholder_embed(text: str) -> list[float]:
        """Deterministic SHA-256 placeholder (1024d) for offline/dev use."""
        import hashlib

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[idx % len(digest)] / 255.0 for idx in range(1024)]

