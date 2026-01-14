# Manual Testing Guide

This guide provides step-by-step instructions for manually testing the Story Generator application with real AI services.

## Prerequisites

Before testing, ensure you have:

1. **Python Environment**: Python 3.12+ installed
2. **Dependencies**: All packages installed (`pip install -r requirements.txt`)
3. **Environment Variables**: Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```
4. **AI Service Access**: At least one of the following:
   - Ollama server running locally (recommended for testing)
   - OpenAI API key (add to `.env` file)
   - Anthropic Claude API key (add to `.env` file)

## Configuration Setup

### Option 1: Test with Ollama (Recommended)

Ollama is free and runs locally, making it ideal for testing.

1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)

2. **Pull a model**:
   ```bash
   ollama pull llama2  # or mistral, phi, etc.
   ```

3. **Verify Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

4. **Update configuration** (`config.json`):
   ```json
   {
     "ai_providers": {
       "text_provider": "ollama",
       "image_provider": "gpt-image-1",
       "ollama": {
         "base_url": "http://localhost:11434",
         "model": "llama2",
         "timeout": 120
       }
     }
   }
   ```

### Option 2: Test with OpenAI

1. **Get API Key**: Sign up at [platform.openai.com](https://platform.openai.com)

2. **Add API key to `.env` file**:
   ```bash
   # Edit .env and update this line:
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

   **Note**: The API key is automatically loaded from `.env` when the app starts!

3. **Update configuration** (`config.json`):
   ```json
   {
     "ai_providers": {
       "text_provider": "openai",
       "image_provider": "gpt-image-1",
       "openai": {
         "model": "gpt-3.5-turbo",
         "api_key_env": "OPENAI_API_KEY",
         "timeout": 60
       }
     }
   }
   ```

### Option 3: Test with Anthropic Claude

1. **Get API Key**: Sign up at [console.anthropic.com](https://console.anthropic.com)

2. **Add API key to `.env` file**:
   ```bash
   # Edit .env and update this line:
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ```

   **Note**: The API key is automatically loaded from `.env` when the app starts!

3. **Update configuration** (`config.json`):
   ```json
   {
     "ai_providers": {
       "text_provider": "claude",
       "image_provider": "gpt-image-1",
       "claude": {
         "model": "claude-3-haiku-20240307",
         "api_key_env": "ANTHROPIC_API_KEY",
         "timeout": 60
       }
     }
   }
   ```

## Test Scenarios

### Test 1: Health Check

**Purpose**: Verify the application starts correctly

```bash
# Start the server
python -m src.app

# In another terminal, test health endpoint
curl http://localhost:5000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "ai_provider": "ollama",  # or openai, claude
  "version": "1.0.0"
}
```

### Test 2: Configuration Endpoint

**Purpose**: Verify configuration is loaded correctly

```bash
curl http://localhost:5000/api/config
```

**Expected Response**: JSON with parameters, defaults, and AI providers

**Validation**:
- `ai_providers.text_provider` matches your config
- `parameters` includes languages, complexities, etc.
- `defaults` has all default values
- API keys are NOT exposed in response

### Test 3: Simple Story Generation

**Purpose**: Test basic story generation with minimal parameters

```bash
curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Brave Little Mouse",
    "num_pages": 3
  }'
```

**Expected Response**:
- Status: 201 Created
- Story object with:
  - `id` (UUID)
  - `metadata.title` = "The Brave Little Mouse"
  - `pages` array with 3 pages
  - `pages[0].page_number` = 1
  - `pages[0].text` contains story content
  - `characters` array (may be empty or contain extracted characters)
  - `vocabulary` array
  - `created_at` and `updated_at` timestamps

**Validation Checklist**:
- [ ] Story has exactly 3 pages
- [ ] Each page has unique content
- [ ] Page numbers are sequential (1, 2, 3)
- [ ] Story is coherent and child-appropriate
- [ ] Response time is reasonable (< 30 seconds)

### Test 4: Story with Theme

**Purpose**: Test thematic story generation

```bash
curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Friends Forever",
    "num_pages": 3,
    "theme": "friendship and kindness",
    "age_group": "3-5",
    "complexity": "simple"
  }'
```

**Validation**:
- [ ] Story incorporates the theme of friendship/kindness
- [ ] Language is appropriate for ages 3-5
- [ ] Complexity is simple (short sentences, basic vocabulary)

### Test 5: Story with Custom Prompt

**Purpose**: Test custom story ideas

```bash
curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Dragon Who Learned to Read",
    "num_pages": 5,
    "custom_prompt": "A story about a young dragon who discovers the joy of reading books",
    "genre": "fantasy"
  }'
```

**Validation**:
- [ ] Story follows the custom prompt
- [ ] Dragon is the main character
- [ ] Reading/books are central to the plot
- [ ] Fantasy genre elements are present

### Test 6: Character Extraction

**Purpose**: Verify character extraction and profiling

```bash
curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Forest Adventure",
    "num_pages": 3,
    "theme": "exploration"
  }'
```

**Validation**:
- [ ] `characters` array is populated
- [ ] Each character has:
  - `name`
  - `species` (or null)
  - `physical_description`
  - `personality_traits`
- [ ] Character descriptions are consistent with story
- [ ] Multiple characters are extracted if story has multiple characters

### Test 7: Single Page Image Generation

**Purpose**: Test image generation for one page

```bash
# First, get the response from Test 3 and extract the story ID
STORY_ID="<story-id-from-previous-test>"

curl -X POST "http://localhost:5000/api/images/stories/${STORY_ID}/pages/1" \
  -H "Content-Type: application/json" \
  -d '{
    "scene_description": "A brave little mouse exploring a colorful garden",
    "art_style": "cartoon"
  }'
```

**Expected Response** (with StubImageClient):
```json
{
  "image_url": "https://via.placeholder.com/512x512?text=A+brave+little",
  "page_number": 1
}
```

**Expected Response** (with real image client):
```json
{
  "image_url": "https://...",  # Real image URL
  "page_number": 1
}
```

**Validation**:
- [ ] Image URL is returned
- [ ] Page number matches request
- [ ] Image URL is accessible (if using real client)

### Test 8: Project Creation and Retrieval

**Purpose**: Test project save/load workflow

**Step 1: Create a story**
```bash
RESPONSE=$(curl -s -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Project Story",
    "num_pages": 2
  }')

echo $RESPONSE | jq '.'
STORY_ID=$(echo $RESPONSE | jq -r '.id')
```

**Step 2: Save as project**
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${STORY_ID}\",
    \"name\": \"My Test Project\",
    \"story\": ${RESPONSE},
    \"status\": \"completed\",
    \"character_profiles\": [],
    \"image_prompts\": []
  }"
```

**Step 3: List projects**
```bash
curl http://localhost:5000/api/projects
```

**Step 4: Retrieve project**
```bash
curl "http://localhost:5000/api/projects/${STORY_ID}"
```

**Step 5: Delete project**
```bash
curl -X DELETE "http://localhost:5000/api/projects/${STORY_ID}"
```

**Validation**:
- [ ] Project is created successfully
- [ ] Project appears in list
- [ ] Retrieved project matches created project
- [ ] Project is deleted successfully
- [ ] Project no longer appears in list after deletion

### Test 9: Error Handling

**Purpose**: Verify proper error handling

**Test 9a: Missing required field**
```bash
curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "num_pages": 3
  }'
```

**Expected**: 400 Bad Request with error message about missing title

**Test 9b: Invalid JSON**
```bash
curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d 'not valid json'
```

**Expected**: 400 Bad Request with JSON parsing error

**Test 9c: Non-existent story**
```bash
curl http://localhost:5000/api/stories/nonexistent-id-12345
```

**Expected**: 404 Not Found

**Validation**:
- [ ] All errors return proper HTTP status codes
- [ ] Error messages are clear and helpful
- [ ] Application doesn't crash on errors

### Test 10: Web Interface

**Purpose**: Test the frontend UI

1. **Open browser**: Navigate to `http://localhost:5000`

2. **Test form population**:
   - [ ] All dropdowns are populated from config
   - [ ] Default values are pre-selected

3. **Generate a story**:
   - [ ] Fill in title: "Web Test Story"
   - [ ] Select parameters
   - [ ] Click "Generate Story"
   - [ ] Loading indicator appears
   - [ ] Story displays after generation
   - [ ] Pages are shown
   - [ ] Characters are shown (if extracted)

4. **Save project**:
   - [ ] Click "Save Project"
   - [ ] Success message appears
   - [ ] Project appears in projects list

5. **Load project**:
   - [ ] Click on project in list
   - [ ] Story displays correctly

6. **Delete project**:
   - [ ] Click delete button
   - [ ] Confirmation dialog appears
   - [ ] Project is removed from list

7. **Create new story**:
   - [ ] Click "New Story" button
   - [ ] Form resets
   - [ ] Can generate another story

## Performance Testing

### Response Time Benchmarks

Test with different story lengths and record response times:

```bash
# 3-page story
time curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{"title": "Short Story", "num_pages": 3}'

# 5-page story
time curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{"title": "Medium Story", "num_pages": 5}'

# 8-page story
time curl -X POST http://localhost:5000/api/stories \
  -H "Content-Type: application/json" \
  -d '{"title": "Long Story", "num_pages": 8}'
```

**Expected Response Times** (with Ollama + llama2):
- 3 pages: 10-20 seconds
- 5 pages: 15-30 seconds
- 8 pages: 25-45 seconds

**Note**: Response times vary based on:
- AI provider (Ollama is slower than OpenAI)
- Model size (larger models are slower but better quality)
- Hardware (CPU vs GPU for Ollama)
- Network speed (for cloud APIs)

## Troubleshooting

### Issue: "AI service unavailable"

**Symptoms**: 500 error when generating stories

**Solutions**:
1. **Ollama**: Check if Ollama is running: `curl http://localhost:11434/api/tags`
2. **OpenAI**: Verify API key is set: `echo $OPENAI_API_KEY`
3. **Check logs**: Look at application logs for detailed error messages

### Issue: "Connection timeout"

**Symptoms**: Request times out before completion

**Solutions**:
1. Increase timeout in config (e.g., 120 seconds for Ollama)
2. Use a smaller model for Ollama
3. Reduce number of pages

### Issue: Characters not extracted

**Symptoms**: `characters` array is empty

**Solutions**:
1. This is normal if AI doesn't detect clear characters
2. Try a story with more explicit character introductions
3. Check if character extraction is enabled in config

### Issue: Poor story quality

**Symptoms**: Incoherent story, repeated content, inappropriate language

**Solutions**:
1. **Ollama**: Try a larger model (mistral instead of llama2)
2. **OpenAI**: Use gpt-4 instead of gpt-3.5-turbo
3. Adjust temperature in prompt builder (lower for more focused, higher for creative)
4. Provide more specific theme or custom prompt

## Test Results Template

Use this template to record your manual testing results:

```markdown
## Manual Test Results - [Date]

**Configuration**:
- AI Provider: [ollama/openai/claude]
- Model: [llama2/gpt-3.5-turbo/etc]
- Test Duration: [time]

**Test Results**:

| Test | Status | Notes |
|------|--------|-------|
| Health Check | ✅/❌ | |
| Configuration | ✅/❌ | |
| Simple Story | ✅/❌ | Response time: X seconds |
| Story with Theme | ✅/❌ | |
| Custom Prompt | ✅/❌ | |
| Character Extraction | ✅/❌ | X characters extracted |
| Image Generation | ✅/❌ | |
| Project CRUD | ✅/❌ | |
| Error Handling | ✅/❌ | |
| Web Interface | ✅/❌ | |

**Issues Found**:
1. [Description of any issues]
2. [Description of any issues]

**Overall Assessment**: [Pass/Fail/Pass with issues]

**Recommendations**:
- [Any recommendations for improvements]
```

## Next Steps

After completing manual testing:

1. **Document Issues**: Record any bugs or unexpected behavior
2. **Update Tests**: Add automated tests for any issues found
3. **Performance Tuning**: Optimize slow operations
4. **Production Readiness**: Replace StubImageClient with real image client if needed
