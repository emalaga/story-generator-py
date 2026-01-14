# Quick Start Guide

Get the Story Generator up and running in 5 minutes!

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- One of the following AI providers:
  - **Ollama** (free, local) - Recommended for testing
  - **OpenAI API** (paid)
  - **Anthropic Claude API** (paid)

## Installation

1. **Clone or navigate to the repository**:
   ```bash
   cd story-generator-py
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your API keys (if using OpenAI or Claude).

## Configuration

The application uses a `.env` file to load environment variables. This file is already created for you, but you need to add your API keys.

### Option 1: Ollama (Recommended for Testing)

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)

2. **Pull a model**:
   ```bash
   ollama pull llama2
   ```

3. **Verify Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. **Update `.env` file** (optional - defaults are already set):
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

5. **Configuration is already set** - The default `config.json` uses Ollama

### Option 2: OpenAI

1. **Get API key** from [platform.openai.com](https://platform.openai.com)

2. **Add API key to `.env` file**:
   ```bash
   # Edit .env and update this line:
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

   **Note**: The API key is automatically loaded from the `.env` file. No need to export it manually!

3. **Update `config.json`**:
   ```json
   {
     "ai_providers": {
       "text_provider": "openai",
       "openai": {
         "model": "gpt-3.5-turbo",
         "api_key_env": "OPENAI_API_KEY"
       }
     }
   }
   ```

### Option 3: Anthropic Claude

1. **Get API key** from [console.anthropic.com](https://console.anthropic.com)

2. **Add API key to `.env` file**:
   ```bash
   # Edit .env and update this line:
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

   **Note**: The API key is automatically loaded from the `.env` file!

3. **Update `config.json`**:
   ```json
   {
     "ai_providers": {
       "text_provider": "claude",
       "claude": {
         "model": "claude-3-haiku-20240307",
         "api_key_env": "ANTHROPIC_API_KEY"
       }
     }
   }
   ```

## Image Generation Setup (Optional)

By default, the application uses a stub image client that returns placeholder images. To enable real AI-generated images with GPT-Image 3:

### Enable GPT-Image 3:

1. **Ensure OpenAI API key is set** in `.env` file (same key used for text generation)

2. **The image provider is already configured** - `config.json` is already set to use GPT-Image 3

3. **Verify the configuration**:
   ```bash
   # Check that config.json has:
   cat data/config/config.json
   ```
   Should show:
   ```json
   {
     "image_provider": "gpt-image-1",
     "openai": {
       "api_key": "",
       ...
     }
   }
   ```

4. **That's it!** The application will automatically use GPT-Image 3 if:
   - `OPENAI_API_KEY` is set in `.env`
   - `image_provider` is set to `"gpt-image-1"` in `config.json`

5. **Use the web interface**:
   - Generate a story
   - Click "Generate Image" on any page
   - Wait 10-20 seconds for GPT-Image 3 to create the illustration
   - The image will appear on the page

**Note**: GPT-Image 3 image generation costs approximately $0.04-$0.08 per image depending on quality and size settings.

## Running the Application

1. **Start the server**:
   ```bash
   python -m src.app
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5001
   ```

3. **Generate your first story**:
   - Enter a title (e.g., "The Brave Little Mouse")
   - Select parameters (or use defaults)
   - Click "Generate Story"
   - Wait 10-30 seconds for the story to be created

## Quick API Test

Once the server is running, try this in another terminal:

```bash
# Generate a simple 3-page story
curl -X POST http://localhost:5001/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Brave Little Mouse",
    "num_pages": 3
  }'
```

## Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src
```

## Automated Testing Scripts

### Test with Ollama:
```bash
# Make sure Ollama is running and the app is running
./scripts/test_ollama.sh
```

### Test with OpenAI:
```bash
# Make sure OPENAI_API_KEY is in .env file and the app is running
./scripts/test_openai.sh
```

**Note**: API keys are now automatically loaded from the `.env` file, so you don't need to pass them as environment variables!

## Common Issues

### Issue: "Missing .env file"
**Solution**: Copy the example file and add your API keys:
```bash
cp .env.example .env
# Then edit .env and add your API keys
```

### Issue: "Ollama not running"
**Solution**: Start Ollama app or run `ollama serve`

### Issue: "AI service unavailable"
**Solution**:
- Check that your AI provider is configured correctly in `config.json`
- Verify API keys are set in the `.env` file (for OpenAI/Claude)
- Make sure the `.env` file is in the project root directory
- Check logs for detailed error messages

### Issue: "Module not found"
**Solution**: Make sure you're in the project root and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Stories are empty or low quality
**Solution**:
- For Ollama: Try a larger model (`ollama pull mistral`)
- For OpenAI: Use GPT-4 instead of GPT-3.5-turbo
- Increase timeout in config if stories are being cut off

## Next Steps

- Read the [Manual Testing Guide](MANUAL_TESTING_GUIDE.md) for comprehensive testing
- Check the [Architecture](ARCHITECTURE.md) for system design details
- See the [Development Plan](DEVELOPMENT_PLAN.md) for implementation progress

## Web Interface Features

Once the app is running at http://localhost:5001, you can:

1. **Generate Stories**:
   - Fill in the story parameters form
   - Click "Generate Story"
   - View the generated story with pages and characters

2. **Generate Images**:
   - After generating a story, click "Generate Image" on any page
   - Wait for GPT-Image 3 to create the illustration (10-20 seconds)
   - View the AI-generated image on the page
   - Click "Regenerate Image" if you want a different version

3. **Save Projects**:
   - After generating a story, click "Save Project"
   - Project is saved to `data/projects/`

4. **Load Projects**:
   - Click on any project in the projects list
   - Story displays with all its details

5. **Delete Projects**:
   - Click the delete button next to any project
   - Confirm deletion in the dialog

## API Endpoints

The application provides these REST API endpoints:

- `GET /health` - Health check
- `GET /api/config` - Get configuration
- `POST /api/stories` - Generate a new story
- `GET /api/stories/:id` - Get story metadata
- `POST /api/images/stories/:id/pages/:num` - Generate single page image
- `GET /api/projects` - List all projects
- `POST /api/projects` - Save a project
- `GET /api/projects/:id` - Get a project
- `DELETE /api/projects/:id` - Delete a project

## Example API Requests

### Generate a themed story:
```bash
curl -X POST http://localhost:5001/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Friends Forever",
    "num_pages": 3,
    "theme": "friendship and kindness",
    "age_group": "3-5",
    "complexity": "simple"
  }'
```

### Generate with custom prompt:
```bash
curl -X POST http://localhost:5001/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Reading Dragon",
    "num_pages": 5,
    "custom_prompt": "A dragon who discovers the joy of reading"
  }'
```

### Generate an image for a page:
```bash
curl -X POST http://localhost:5001/api/images/stories/STORY_ID/pages/1 \
  -H "Content-Type: application/json" \
  -d '{
    "scene_description": "A brave mouse in a colorful garden",
    "art_style": "cartoon"
  }'
```

## Support

For detailed documentation:
- **Manual Testing**: See [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Development**: See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

For issues and contributions:
- Create an issue in the repository
- Follow the existing code style and test patterns
