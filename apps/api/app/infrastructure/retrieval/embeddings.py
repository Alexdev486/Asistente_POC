from app.infrastructure.llm.gateway import LLMGateway
import hashlib


class EmbeddingService:
    """
    Placeholder para el generador de embeddings.
    Puede conectarse a OpenRouter/Groq si se habilita un modelo de embedding compatible.
    """

    def __init__(self, _: LLMGateway | None = None) -> None:
        pass

    def embed(self, text: str) -> list[float]:
        # Embedding determinista de 1024 dimensiones para pipeline end-to-end.
        # Se reemplazara por proveedor real en la fase de hardening.
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for idx in range(1024):
            byte_val = digest[idx % len(digest)]
            values.append(byte_val / 255.0)
        return values
