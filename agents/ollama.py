import httpx

from backend.config import settings


class OllamaClient:
    def generate(self, prompt: str) -> str:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_predict": 96, "num_ctx": 2048},
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]
