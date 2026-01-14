"""
Unit tests for OpenAI Client.
Write these tests BEFORE implementing the client (TDD approach).

These tests use mocked API responses to avoid requiring an OpenAI API key.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestOpenAIClient:
    """Test OpenAIClient for text generation"""

    @pytest.fixture
    def openai_config(self):
        """Create OpenAIConfig for testing"""
        from src.models.config import OpenAIConfig
        return OpenAIConfig(
            api_key="test-api-key-123",
            text_model="gpt-4o-mini",
            timeout=60
        )

    @pytest.fixture
    def openai_client(self, openai_config):
        """Create OpenAIClient instance for testing"""
        from src.ai.openai_client import OpenAIClient
        return OpenAIClient(openai_config)

    def test_openai_client_initialization(self, openai_config):
        """Test creating OpenAIClient with config"""
        from src.ai.openai_client import OpenAIClient

        client = OpenAIClient(openai_config)

        assert client.config == openai_config
        assert client.api_key == "test-api-key-123"
        assert client.text_model == "gpt-4o-mini"
        assert client.timeout == 60

    def test_openai_client_inherits_base_client(self, openai_client):
        """Test that OpenAIClient inherits from BaseAIClient"""
        from src.ai.base_client import BaseAIClient

        assert isinstance(openai_client, BaseAIClient)

    @pytest.mark.asyncio
    async def test_generate_text_success(self, openai_client):
        """Test successful text generation"""
        mock_response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-4o-mini",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Once upon a time in a magical forest..."
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await openai_client.generate_text("Write a story")

            assert result == "Once upon a time in a magical forest..."
            assert isinstance(result, str)
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_with_kwargs(self, openai_client):
        """Test text generation with additional parameters"""
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": "Generated with custom params"
                }
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await openai_client.generate_text(
                "Test prompt",
                temperature=0.9,
                max_tokens=500
            )

            assert result == "Generated with custom params"

            # Verify kwargs were passed to the API
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            assert request_data['temperature'] == 0.9
            assert request_data['max_tokens'] == 500

    @pytest.mark.asyncio
    async def test_generate_text_request_format(self, openai_client):
        """Test that request is formatted correctly for OpenAI API"""
        mock_response_data = {
            "choices": [{
                "message": {"content": "test"}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await openai_client.generate_text("Test prompt")

            # Verify request structure
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']

            assert 'model' in request_data
            assert request_data['model'] == "gpt-4o-mini"
            assert 'messages' in request_data
            assert len(request_data['messages']) == 1
            assert request_data['messages'][0]['role'] == 'user'
            assert request_data['messages'][0]['content'] == "Test prompt"

    @pytest.mark.asyncio
    async def test_generate_text_includes_auth_header(self, openai_client):
        """Test that API key is included in Authorization header"""
        mock_response_data = {
            "choices": [{
                "message": {"content": "test"}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await openai_client.generate_text("Test prompt")

            # Verify Authorization header
            call_kwargs = mock_post.call_args[1]
            headers = call_kwargs['headers']
            assert 'Authorization' in headers
            assert headers['Authorization'] == "Bearer test-api-key-123"

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, openai_client):
        """Test handling of API errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.text = "Invalid API key"
            mock_post.return_value = mock_resp

            with pytest.raises(httpx.HTTPError):
                await openai_client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_text_connection_error(self, openai_client):
        """Test handling of connection errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(httpx.ConnectError):
                await openai_client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_text_timeout(self, openai_client):
        """Test handling of timeout errors"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(httpx.TimeoutException):
                await openai_client.generate_text("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_text_empty_response(self, openai_client):
        """Test handling of empty response from API"""
        mock_response_data = {
            "choices": [{
                "message": {"content": ""}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await openai_client.generate_text("Test prompt")

            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_text_uses_configured_model(self):
        """Test that client uses the model specified in config"""
        from src.ai.openai_client import OpenAIClient
        from src.models.config import OpenAIConfig

        config = OpenAIConfig(
            api_key="test-key",
            text_model="gpt-4o",
            timeout=60
        )
        client = OpenAIClient(config)

        mock_response_data = {
            "choices": [{
                "message": {"content": "test"}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await client.generate_text("Test")

            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            assert request_data['model'] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_generate_text_respects_timeout(self):
        """Test that client uses timeout from config"""
        from src.ai.openai_client import OpenAIClient
        from src.models.config import OpenAIConfig

        config = OpenAIConfig(
            api_key="test-key",
            text_model="gpt-4o-mini",
            timeout=30
        )
        client = OpenAIClient(config)

        mock_response_data = {
            "choices": [{
                "message": {"content": "test"}
            }]
        }

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
    async def test_generate_text_long_response(self, openai_client):
        """Test handling of long text responses"""
        long_text = "A" * 10000  # 10k character response
        mock_response_data = {
            "choices": [{
                "message": {"content": long_text}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await openai_client.generate_text("Test prompt")

            assert len(result) == 10000
            assert result == long_text

    @pytest.mark.asyncio
    async def test_generate_text_special_characters(self, openai_client):
        """Test handling of special characters in prompt and response"""
        prompt = "Tell me about 'quotes', \"double quotes\", and émojis 🎉"
        response_text = "Here's text with special chars: ñ, ü, 中文, 🌟"

        mock_response_data = {
            "choices": [{
                "message": {"content": response_text}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await openai_client.generate_text(prompt)

            assert result == response_text
            assert "🌟" in result

    @pytest.mark.asyncio
    async def test_multiple_sequential_requests(self, openai_client):
        """Test making multiple requests in sequence"""
        responses = [
            {"choices": [{"message": {"content": "First response"}}]},
            {"choices": [{"message": {"content": "Second response"}}]},
            {"choices": [{"message": {"content": "Third response"}}]}
        ]

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resps = []
            for resp_data in responses:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = resp_data
                mock_resps.append(mock_resp)

            mock_post.side_effect = mock_resps

            result1 = await openai_client.generate_text("Prompt 1")
            result2 = await openai_client.generate_text("Prompt 2")
            result3 = await openai_client.generate_text("Prompt 3")

            assert result1 == "First response"
            assert result2 == "Second response"
            assert result3 == "Third response"
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_text_with_system_message(self, openai_client):
        """Test text generation with system message parameter"""
        mock_response_data = {
            "choices": [{
                "message": {"content": "Response with system context"}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = await openai_client.generate_text(
                "Test prompt",
                system_message="You are a helpful assistant."
            )

            assert result == "Response with system context"

            # Verify system message was included
            call_kwargs = mock_post.call_args[1]
            request_data = call_kwargs['json']
            assert len(request_data['messages']) == 2
            assert request_data['messages'][0]['role'] == 'system'
            assert request_data['messages'][0]['content'] == "You are a helpful assistant."
            assert request_data['messages'][1]['role'] == 'user'
            assert request_data['messages'][1]['content'] == "Test prompt"

    @pytest.mark.asyncio
    async def test_api_endpoint_url(self, openai_client):
        """Test that correct OpenAI API endpoint is used"""
        mock_response_data = {
            "choices": [{
                "message": {"content": "test"}
            }]
        }

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            await openai_client.generate_text("Test")

            # Verify correct endpoint URL
            call_args = mock_post.call_args[0]
            url = call_args[0]
            assert "https://api.openai.com/v1/chat/completions" in url
