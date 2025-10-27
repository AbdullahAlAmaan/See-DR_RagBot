from typing import List, Dict
import httpx

from ..config import AppConfig


class OllamaClient:
	def __init__(self, cfg: AppConfig) -> None:
		self.base_url = cfg.environment.ollama_base_url.rstrip("/")
		self.model = cfg.models.llm_model

	async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int | None = None) -> str:
		url = f"{self.base_url}/api/generate"
		payload: Dict = {
			"model": self.model,
			"prompt": prompt,
			"stream": False,
			"options": {"temperature": temperature},
		}
		if max_tokens is not None:
			payload["options"]["num_predict"] = max_tokens
		async with httpx.AsyncClient(timeout=120) as client:
			resp = await client.post(url, json=payload)
			resp.raise_for_status()
			data = resp.json()
			return data.get("response", "")
