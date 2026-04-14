from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        ...

