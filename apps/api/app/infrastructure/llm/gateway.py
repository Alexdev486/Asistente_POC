import logging

from app.application.ports.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class LLMGateway:
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            return self.primary.complete(prompt=prompt, system_prompt=system_prompt)
        except Exception as exc:
            logger.warning("LLM primary failed, switching to fallback", exc_info=True, extra={"error": str(exc)})
            return self.fallback.complete(prompt=prompt, system_prompt=system_prompt)

