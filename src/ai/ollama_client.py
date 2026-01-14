"""
Ollama client for local text generation.

This client interfaces with a local Ollama server to generate text using
open-source language models like Llama, Mistral, or Granite.
"""

import httpx
from typing import Any, Dict

from src.ai.base_client import BaseAIClient
from src.models.config import OllamaConfig


class OllamaClient(BaseAIClient):
    """
    Client for Ollama text generation service.

    Ollama is a local AI service that runs open-source language models.
    This client handles communication with the Ollama API.
    """

    def __init__(self, config: OllamaConfig):
        """
        Initialize the Ollama client.

        Args:
            config: OllamaConfig with server URL, model name, and timeout
        """
        self.config = config
        self.base_url = config.base_url
        self.model = config.model
        self.timeout = config.timeout

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: The input prompt for text generation
            **kwargs: Additional parameters:
                - temperature (float): Sampling temperature (0.0 to 2.0)
                - max_tokens (int): Maximum tokens to generate
                - top_p (float): Nucleus sampling parameter
                - top_k (int): Top-k sampling parameter
                - repeat_penalty (float): Penalty for repetition

        Returns:
            Generated text as a string

        Raises:
            httpx.HTTPError: If the API request fails
            httpx.ConnectError: If connection to Ollama server fails
            httpx.TimeoutException: If request times out
        """
        # Build request data
        request_data: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False  # We want complete response, not streaming
        }

        # Add optional parameters if provided
        options = {}
        if 'temperature' in kwargs:
            options['temperature'] = kwargs['temperature']
        if 'max_tokens' in kwargs:
            options['num_predict'] = kwargs['max_tokens']
        if 'top_p' in kwargs:
            options['top_p'] = kwargs['top_p']
        if 'top_k' in kwargs:
            options['top_k'] = kwargs['top_k']
        if 'repeat_penalty' in kwargs:
            options['repeat_penalty'] = kwargs['repeat_penalty']

        if options:
            request_data['options'] = options

        # Make API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=request_data
            )

            # Check for errors
            if response.status_code != 200:
                raise httpx.HTTPError(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )

            # Parse response
            response_data = response.json()
            generated_text = response_data.get('response', '')

            return generated_text
