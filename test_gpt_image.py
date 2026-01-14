"""
Quick test script to validate GPT-Image integration.

This script tests:
1. Loading the OpenAI API key from .env
2. Creating a GPT-Image client
3. Generating a simple test image
"""

import asyncio
import os
from dotenv import load_dotenv
from src.ai.gpt_image_client import GPTImageClient
from src.models.config import OpenAIConfig

async def test_gpt_image():
    """Test GPT-Image client with a simple prompt."""

    print("=" * 60)
    print("GPT-Image Integration Test")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ FAILED: OPENAI_API_KEY not found in .env file")
        return False

    print(f"✓ API key loaded: {api_key[:15]}...{api_key[-4:]}")

    # Create OpenAI config
    config = OpenAIConfig(
        api_key=api_key,
        text_model="gpt-4",
        image_model="gpt-image-1",
        timeout=120
    )

    # Create GPT-Image client
    print("\n✓ Creating GPT-Image client with model: gpt-image-1")
    client = GPTImageClient(config, model="gpt-image-1")

    # Test prompt - simple and child-friendly
    test_prompt = "A cartoon style children's book illustration: A happy brown teddy bear sitting under a tree reading a book. Vibrant colors, child-friendly, professional illustration."

    print(f"\n✓ Test prompt ({len(test_prompt)} chars):")
    print(f"  {test_prompt[:100]}...")

    # Generate image
    print("\n⏳ Generating image... (this may take 10-20 seconds)")

    try:
        image_url = await client.generate_image(test_prompt)

        print("\n" + "=" * 60)
        print("✅ SUCCESS! Image generated successfully")
        print("=" * 60)
        print(f"\nImage URL: {image_url}")
        print("\nYou can open this URL in your browser to view the generated image.")
        print("Note: OpenAI image URLs expire after 1 hour.")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ FAILED! Image generation error")
        print("=" * 60)
        print(f"\nError type: {type(e).__name__}")
        print(f"Error message: {str(e)}")

        # Provide helpful debugging info
        print("\n" + "-" * 60)
        print("Debugging Information:")
        print("-" * 60)

        if "401" in str(e) or "authentication" in str(e).lower():
            print("• Authentication failed - check your API key")
            print("• Make sure OPENAI_API_KEY is set correctly in .env")
        elif "400" in str(e):
            print("• Bad request - the API rejected the prompt")
            print("• This might be a content policy issue")
        elif "500" in str(e):
            print("• OpenAI server error - this is temporary")
            print("• The retry logic should handle this automatically")
            print("• Try running the test again in a few moments")
        elif "timeout" in str(e).lower():
            print("• Request timed out")
            print("• Try increasing the timeout or check your connection")
        else:
            print("• Unexpected error - see error message above")

        return False

if __name__ == "__main__":
    print("\nStarting GPT-Image validation test...\n")

    # Run the async test
    success = asyncio.run(test_gpt_image())

    print("\n" + "=" * 60)
    if success:
        print("Test Result: ✅ PASSED")
        print("\nThe GPT-Image integration is working correctly!")
        print("You can now use the web interface to generate images.")
    else:
        print("Test Result: ❌ FAILED")
        print("\nPlease fix the issues above and try again.")
    print("=" * 60 + "\n")
