import httpx

from app.core.config import get_settings


class OpenRouterProvider:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model
        self._timeout = settings.request_timeout_seconds
        self._url = "https://openrouter.ai/api/v1/chat/completions"

    def complete(self, prompt: str, system_prompt: str | None = None) -> str:
        if not self._api_key:
            raise RuntimeError("OPENROUTER_API_KEY no configurada")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self._model, "messages": messages, "temperature": 0}
        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

