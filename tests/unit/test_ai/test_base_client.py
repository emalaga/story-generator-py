"""
Unit tests for Base AI Client.
Write these tests BEFORE implementing the base client (TDD approach).
"""

import pytest
from abc import ABC


class TestBaseAIClient:
    """Test BaseAIClient abstract base class"""

    def test_base_client_is_abstract(self):
        """Test that BaseAIClient is an abstract base class"""
        from src.ai.base_client import BaseAIClient

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            BaseAIClient()

    def test_base_client_has_generate_text_method(self):
        """Test that BaseAIClient defines generate_text as abstract"""
        from src.ai.base_client import BaseAIClient

        # Check that the method exists and is abstract
        assert hasattr(BaseAIClient, 'generate_text')
        assert BaseAIClient.generate_text.__isabstractmethod__

    def test_base_client_subclass_must_implement_generate_text(self):
        """Test that subclasses must implement generate_text"""
        from src.ai.base_client import BaseAIClient

        # Create incomplete subclass
        class IncompleteClient(BaseAIClient):
            pass

        # Should not be able to instantiate without implementing abstract method
        with pytest.raises(TypeError):
            IncompleteClient()

    def test_base_client_subclass_with_generate_text_can_instantiate(self):
        """Test that subclass with generate_text can be instantiated"""
        from src.ai.base_client import BaseAIClient

        # Create complete subclass
        class CompleteClient(BaseAIClient):
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return "generated text"

        # Should be able to instantiate
        client = CompleteClient()
        assert client is not None
        assert isinstance(client, BaseAIClient)

    def test_generate_text_is_async(self):
        """Test that generate_text is defined as async"""
        from src.ai.base_client import BaseAIClient
        import inspect

        # Create a valid subclass to check the signature
        class TestClient(BaseAIClient):
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return "test"

        client = TestClient()
        assert inspect.iscoroutinefunction(client.generate_text)

    def test_generate_text_signature(self):
        """Test that generate_text has correct signature"""
        from src.ai.base_client import BaseAIClient
        import inspect

        # Create a valid subclass
        class TestClient(BaseAIClient):
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return "test"

        client = TestClient()
        sig = inspect.signature(client.generate_text)

        # Check parameters
        params = list(sig.parameters.keys())
        assert 'prompt' in params
        assert 'kwargs' in params

        # Check return annotation
        assert sig.return_annotation == str


class TestBaseImageClient:
    """Test BaseImageClient abstract base class"""

    def test_base_image_client_is_abstract(self):
        """Test that BaseImageClient is an abstract base class"""
        from src.ai.base_client import BaseImageClient

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            BaseImageClient()

    def test_base_image_client_has_generate_image_method(self):
        """Test that BaseImageClient defines generate_image as abstract"""
        from src.ai.base_client import BaseImageClient

        # Check that the method exists and is abstract
        assert hasattr(BaseImageClient, 'generate_image')
        assert BaseImageClient.generate_image.__isabstractmethod__

    def test_base_image_client_subclass_must_implement_generate_image(self):
        """Test that subclasses must implement generate_image"""
        from src.ai.base_client import BaseImageClient

        # Create incomplete subclass
        class IncompleteImageClient(BaseImageClient):
            pass

        # Should not be able to instantiate without implementing abstract method
        with pytest.raises(TypeError):
            IncompleteImageClient()

    def test_base_image_client_subclass_with_generate_image_can_instantiate(self):
        """Test that subclass with generate_image can be instantiated"""
        from src.ai.base_client import BaseImageClient

        # Create complete subclass
        class CompleteImageClient(BaseImageClient):
            async def generate_image(self, prompt: str, **kwargs) -> bytes:
                return b"fake image data"

        # Should be able to instantiate
        client = CompleteImageClient()
        assert client is not None
        assert isinstance(client, BaseImageClient)

    def test_generate_image_is_async(self):
        """Test that generate_image is defined as async"""
        from src.ai.base_client import BaseImageClient
        import inspect

        # Create a valid subclass to check the signature
        class TestImageClient(BaseImageClient):
            async def generate_image(self, prompt: str, **kwargs) -> bytes:
                return b"test"

        client = TestImageClient()
        assert inspect.iscoroutinefunction(client.generate_image)

    def test_generate_image_signature(self):
        """Test that generate_image has correct signature"""
        from src.ai.base_client import BaseImageClient
        import inspect

        # Create a valid subclass
        class TestImageClient(BaseImageClient):
            async def generate_image(self, prompt: str, **kwargs) -> bytes:
                return b"test"

        client = TestImageClient()
        sig = inspect.signature(client.generate_image)

        # Check parameters
        params = list(sig.parameters.keys())
        assert 'prompt' in params
        assert 'kwargs' in params

        # Check return annotation
        assert sig.return_annotation == bytes

    def test_base_client_and_image_client_are_independent(self):
        """Test that BaseAIClient and BaseImageClient are separate interfaces"""
        from src.ai.base_client import BaseAIClient, BaseImageClient

        # They should be different classes
        assert BaseAIClient is not BaseImageClient

        # They should both be abstract
        assert ABC in BaseAIClient.__bases__
        assert ABC in BaseImageClient.__bases__


class TestClientIntegration:
    """Test that clients can be used together"""

    @pytest.mark.asyncio
    async def test_text_client_generates_text(self):
        """Test that a concrete text client can generate text"""
        from src.ai.base_client import BaseAIClient

        class MockTextClient(BaseAIClient):
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return f"Response to: {prompt}"

        client = MockTextClient()
        result = await client.generate_text("Hello")

        assert result == "Response to: Hello"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_image_client_generates_image(self):
        """Test that a concrete image client can generate image"""
        from src.ai.base_client import BaseImageClient

        class MockImageClient(BaseImageClient):
            async def generate_image(self, prompt: str, **kwargs) -> bytes:
                return b"image data for: " + prompt.encode()

        client = MockImageClient()
        result = await client.generate_image("cat picture")

        assert result == b"image data for: cat picture"
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_clients_accept_kwargs(self):
        """Test that clients can accept additional keyword arguments"""
        from src.ai.base_client import BaseAIClient, BaseImageClient

        class MockTextClient(BaseAIClient):
            async def generate_text(self, prompt: str, **kwargs) -> str:
                max_tokens = kwargs.get('max_tokens', 100)
                temperature = kwargs.get('temperature', 0.7)
                return f"Generated with max_tokens={max_tokens}, temp={temperature}"

        class MockImageClient(BaseImageClient):
            async def generate_image(self, prompt: str, **kwargs) -> bytes:
                size = kwargs.get('size', '1024x1024')
                return f"Image {size}".encode()

        text_client = MockTextClient()
        text_result = await text_client.generate_text(
            "test",
            max_tokens=500,
            temperature=0.9
        )
        assert "max_tokens=500" in text_result
        assert "temp=0.9" in text_result

        image_client = MockImageClient()
        image_result = await image_client.generate_image(
            "test",
            size='512x512'
        )
        assert b"512x512" in image_result
