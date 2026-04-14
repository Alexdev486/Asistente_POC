from app.application.ports.llm_provider import LLMProvider


class LLMGateway:
    def __init__(self, primary: LLMProvider, fallback: LLMProvider):
        self.primary = primary
        self.fallback = fallback

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            return self.primary.complete(prompt=prompt, system_prompt=system_prompt)
        except Exception:
            return self.fallback.complete(prompt=prompt, system_prompt=system_prompt)

