"""
Unit tests for Ollama Client.
Write these tests BEFORE implementing the client (TDD approach).

These tests use mocked HTTP responses to avoid requiring a running Ollama server.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestOllamaClient:
    """Test OllamaClient for text generation"""

    @pytest.fixture
    def ollama_config(self):
        """Create OllamaConfig for testing"""
        from src.models.config import OllamaConfig
        return OllamaConfig(
            base_url="http://localhost:11434",
            model="granite4:small-h",
            timeout=120
        )

    @pytest.fixture
    def ollama_client(self, ollama_config):
        """Create OllamaClient instance for testing"""
        from src.ai.ollama_client import OllamaClient
        return OllamaClient(ollama_config)

    def test_ollama_client_initialization(self, ollama_config):
        """Test creating OllamaClient with config"""
        from src.ai.ollama_client import OllamaClient

        client = OllamaClient(ollama_config)

        assert client.config == ollama_config
        assert client.base_url == "http://localhost:11434"
        assert client.model == "granite4:small-h"
        assert client.timeout == 120

    def test_ollama_client_inherits_base_client(self, ollama_client):
        """Test that OllamaClient inherits from BaseAIClient"""
        from src.ai.base_client import BaseAIClient

        assert isinstance(ollama_client, BaseAIClient)

    @pytest.mark.asyncio
    async def test_generate_text_success(self, ollama_client):
        """Test successful text generation"""
        mock_response_data = {
            "model": "granite4:small-h",
            "created_at": "2024-01-01T00:00:00Z",
            "response": "Once upon a time in a magical forest...",
            "done": True
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await ollama_client.generate_text("Write a story")

            assert result == "Once upon a time in a magical forest..."
            assert isinstance(result, str)
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_with_kwargs(self, ollama_client):
        """Test text generation with additional parameters"""
        mock_response_data = {
            "response": "Generated with custom params",
            "done": True
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await ollama_client.generate_text(
                "Test prompt",
                temperature=0.9,
                max_tokens=500
            )

            assert result == "Generated with custom params"

            # Verify kwargs were passed to the API
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            assert 'options' in request_data
            assert 'temperature' in request_data['options']
            assert request_data['options']['temperature'] == 0.9

    @pytest.mark.asyncio
    async def test_generate_text_request_format(self, ollama_client):
        """Test that request is formatted correctly for Ollama API"""
        mock_response_data = {"response": "test", "done": True}

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await ollama_client.generate_text("Test prompt")

            # Verify request structure
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']

            assert 'model' in request_data
            assert request_data['model'] == "granite4:small-h"
            assert 'prompt' in request_data
            assert request_data['prompt'] == "Test prompt"
            assert 'stream' in request_data
            assert request_data['stream'] is False

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, ollama_client):
        """Test handling of API errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.text = "Internal Server Error"
            mock_post.return_value = mock_resp

            with pytest.raises(httpx.HTTPError):
                await ollama_client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_text_connection_error(self, ollama_client):
        """Test handling of connection errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(httpx.ConnectError):
                await ollama_client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_text_timeout(self, ollama_client):
        """Test handling of timeout errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(httpx.TimeoutException):
                await ollama_client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_text_empty_response(self, ollama_client):
        """Test handling of empty response from API"""
        mock_response_data = {
            "response": "",
            "done": True
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await ollama_client.generate_text("Test prompt")

            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_text_uses_configured_model(self):
        """Test that client uses the model specified in config"""
        from src.ai.ollama_client import OllamaClient
        from src.models.config import OllamaConfig

        config = OllamaConfig(
            base_url="http://localhost:11434",
            model="custom-model:latest",
            timeout=60
        )
        client = OllamaClient(config)

        mock_response_data = {"response": "test", "done": True}

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await client.generate_text("Test")

            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            assert request_data['model'] == "custom-model:latest"

    @pytest.mark.asyncio
    async def test_generate_text_uses_configured_url(self):
        """Test that client uses the base URL from config"""
        from src.ai.ollama_client import OllamaClient
        from src.models.config import OllamaConfig

        config = OllamaConfig(
            base_url="http://custom-server:8080",
            model="test-model",
            timeout=60
        )
        client = OllamaClient(config)

        mock_response_data = {"response": "test", "done": True}

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await client.generate_text("Test")

            call_args = mock_post.call_args[0]
            url = call_args[0]
            assert "custom-server:8080" in url

    @pytest.mark.asyncio
    async def test_generate_text_respects_timeout(self):
        """Test that client uses timeout from config"""
        from src.ai.ollama_client import OllamaClient
        from src.models.config import OllamaConfig

        config = OllamaConfig(
            base_url="http://localhost:11434",
            model="test-model",
            timeout=30
        )
        client = OllamaClient(config)

        mock_response_data = {"response": "test", "done": True}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            await client.generate_text("Test")

            # Verify AsyncClient was created with timeout
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] == 30

    @pytest.mark.asyncio
    async def test_generate_text_long_response(self, ollama_client):
        """Test handling of long text responses"""
        long_text = "A" * 10000  # 10k character response
        mock_response_data = {
            "response": long_text,
            "done": True
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await ollama_client.generate_text("Test prompt")

            assert len(result) == 10000
            assert result == long_text

    @pytest.mark.asyncio
    async def test_generate_text_special_characters(self, ollama_client):
        """Test handling of special characters in prompt and response"""
        prompt = "Tell me about 'quotes', \"double quotes\", and émojis 🎉"
        response_text = "Here's text with special chars: ñ, ü, 中文, 🌟"

        mock_response_data = {
            "response": response_text,
            "done": True
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await ollama_client.generate_text(prompt)

            assert result == response_text
            assert "🌟" in result

    @pytest.mark.asyncio
    async def test_multiple_sequential_requests(self, ollama_client):
        """Test making multiple requests in sequence"""
        responses = [
            {"response": "First response", "done": True},
            {"response": "Second response", "done": True},
            {"response": "Third response", "done": True}
        ]

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resps = []
            for resp_data in responses:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = resp_data
                mock_resps.append(mock_resp)

            mock_post.side_effect = mock_resps

            result1 = await ollama_client.generate_text("Prompt 1")
            result2 = await ollama_client.generate_text("Prompt 2")
            result3 = await ollama_client.generate_text("Prompt 3")

            assert result1 == "First response"
            assert result2 == "Second response"
            assert result3 == "Third response"
            assert mock_post.call_count == 3
