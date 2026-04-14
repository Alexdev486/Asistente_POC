from app.infrastructure.llm.gateway import LLMGateway


class EmbeddingService:
    """
    Placeholder para el generador de embeddings.
    Puede conectarse a OpenRouter/Groq si se habilita un modelo de embedding compatible.
    """

    def __init__(self, _: LLMGateway | None = None) -> None:
        pass

    def embed(self, text: str) -> list[float]:
        # Placeholder determinista para poder avanzar con estructura y pruebas.
        return [float(len(text) % 10)] * 8

