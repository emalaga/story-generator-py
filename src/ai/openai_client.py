"""
OpenAI client for text generation using GPT models.

This client interfaces with OpenAI's API to generate text using
models like GPT-4o, GPT-4o-mini, and other GPT variants.
"""

import os
import httpx
from typing import Any, Dict, List

from src.ai.base_client import BaseAIClient
from src.models.config import OpenAIConfig


class OpenAIClient(BaseAIClient):
    """
    Client for OpenAI text generation service.

    OpenAI provides state-of-the-art language models through their API.
    This client handles communication with the OpenAI Chat Completions API.
    """

    # OpenAI API endpoint
    API_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, config: OpenAIConfig):
        """
        Initialize the OpenAI client.

        Args:
            config: OpenAIConfig with API key, model name, and timeout
        """
        self.config = config
        # Get API key from config or environment variable
        self.api_key = config.api_key or os.getenv('OPENAI_API_KEY', '')
        self.text_model = config.text_model
        self.timeout = config.timeout

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI.

        Args:
            prompt: The input prompt for text generation
            **kwargs: Additional parameters:
                - temperature (float): Sampling temperature (0.0 to 2.0)
                - max_tokens (int): Maximum tokens to generate
                - top_p (float): Nucleus sampling parameter
                - presence_penalty (float): Presence penalty (-2.0 to 2.0)
                - frequency_penalty (float): Frequency penalty (-2.0 to 2.0)
                - system_message (str): Optional system message to guide behavior

        Returns:
            Generated text as a string

        Raises:
            ValueError: If API key is not configured
            httpx.HTTPError: If the API request fails
            httpx.ConnectError: If connection to OpenAI API fails
            httpx.TimeoutException: If request times out
        """
        # Validate API key
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in your .env file"
            )

        # Build messages array
        messages: List[Dict[str, str]] = []

        # Add system message if provided
        if 'system_message' in kwargs:
            messages.append({
                "role": "system",
                "content": kwargs.pop('system_message')
            })

        # Add user prompt
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Build request data
        request_data: Dict[str, Any] = {
            "model": self.text_model,
            "messages": messages
        }

        # Add optional parameters if provided
        if 'temperature' in kwargs:
            request_data['temperature'] = kwargs['temperature']
        if 'max_tokens' in kwargs:
            request_data['max_tokens'] = kwargs['max_tokens']
        if 'top_p' in kwargs:
            request_data['top_p'] = kwargs['top_p']
        if 'presence_penalty' in kwargs:
            request_data['presence_penalty'] = kwargs['presence_penalty']
        if 'frequency_penalty' in kwargs:
            request_data['frequency_penalty'] = kwargs['frequency_penalty']

        # Prepare headers with API key
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Make API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.API_BASE_URL}/chat/completions",
                json=request_data,
                headers=headers
            )

            # Check for errors
            if response.status_code != 200:
                raise httpx.HTTPError(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )

            # Parse response
            response_data = response.json()
            generated_text = response_data['choices'][0]['message']['content']

            return generated_text
