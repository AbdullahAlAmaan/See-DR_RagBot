from __future__ import annotations
import asyncio
import os
import time
from typing import Dict

import google.generativeai as genai
from google.api_core import exceptions

from ..config import AppConfig


class GeminiClient:
	"""Client for Google Gemini API integration."""
	
	def __init__(self, cfg: AppConfig) -> None:
		"""Initialize Gemini client with API key from environment.
		
		Args:
			cfg: Application configuration.
			
		Raises:
			ValueError: If GEMINI_API_KEY is not set in environment.
		"""
		api_key = os.getenv("GEMINI_API_KEY")
		if not api_key:
			raise ValueError("GEMINI_API_KEY environment variable is required")
		genai.configure(api_key=api_key)
		self.model = cfg.models.llm_model
		# Ensure model name has 'models/' prefix if not already present
		model_name = self.model if self.model.startswith("models/") else f"models/{self.model}"
		
		# Initialize the model (using default safety settings which work fine for medical content)
		try:
			self.client = genai.GenerativeModel(model_name)
		except Exception as e:
			raise ValueError(f"Failed to initialize Gemini model '{model_name}': {e}")
	
	async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int | None = None) -> str:
		"""Generate text using Gemini API.
		
		Args:
			prompt: The input prompt for generation.
			temperature: Sampling temperature (0.0-1.0). Lower values are more deterministic.
			max_tokens: Maximum number of tokens to generate. If None, uses model default.
			
		Returns:
			Generated text response.
		"""
		generation_config: Dict = {
			"temperature": temperature,
		}
		if max_tokens is not None:
			generation_config["max_output_tokens"] = max_tokens
		
		def _generate_sync() -> str:
			"""Synchronous wrapper for Gemini API call with retry logic."""
			max_retries = 3
			base_delay = 1.0
			
			for attempt in range(max_retries):
				try:
					response = self.client.generate_content(
						prompt,
						generation_config=generation_config
					)
					# Simple approach: use response.text directly (works for normal cases)
					if hasattr(response, 'text') and response.text:
						return response.text
					# Fallback: extract from candidates if text property not available
					if response.candidates and len(response.candidates) > 0:
						candidate = response.candidates[0]
						if candidate.content and candidate.content.parts:
							text_parts = []
							for part in candidate.content.parts:
								if hasattr(part, 'text') and part.text:
									text_parts.append(part.text)
							if text_parts:
								return ''.join(text_parts)
					raise RuntimeError("Gemini API returned an empty response")
				except exceptions.ResourceExhausted as e:
					# Rate limit error - wait and retry
					if attempt < max_retries - 1:
						# Extract retry delay from error if available, otherwise use exponential backoff
						delay = base_delay * (2 ** attempt)
						if "retry_delay" in str(e):
							# Try to extract seconds from error message
							import re
							match = re.search(r'seconds:\s*(\d+)', str(e))
							if match:
								delay = float(match.group(1)) + 1
						time.sleep(delay)
						continue
					else:
						raise RuntimeError(f"Gemini API rate limit exceeded after {max_retries} attempts: {e}")
				except Exception as e:
					raise RuntimeError(f"Gemini API error: {e}")
			
			# Should not reach here, but just in case
			raise RuntimeError("Failed to generate content after retries")
		
		# Run synchronous API call in thread pool to avoid blocking
		return await asyncio.to_thread(_generate_sync)

