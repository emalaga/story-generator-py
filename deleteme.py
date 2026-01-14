import os
import base64
from openai import OpenAI

# Create client (automatically reads OPENAI_API_KEY)
client = OpenAI()

prompt = """
A soft pastel isometric illustration of an AI agent organizing documents
in floating windows, modern clean style, LinkedIn professional aesthetic,
light background, minimal, friendly
"""

# Call the Images API (DALL·E-3 backend)
result = client.images.generate(
    model="gpt-image-1",
    prompt=prompt,
    size="1024x1024",
    quality="high"
)

# Decode base64 → PNG
image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

# Save file
output_file = "ai_agent.png"
with open(output_file, "wb") as f:
    f.write(image_bytes)

print(f"Image saved as {output_file}")
