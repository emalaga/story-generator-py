# Configuration Files

This directory contains JSON configuration files for the Children's Story Generator application.

## Files

### `config.json` - AI Provider Configuration
Contains settings for AI text and image generation providers.

**Fields:**
- `text_provider`: Which provider to use for text generation (`ollama`, `openai`, `claude`)
- `image_provider`: Which provider to use for image generation (`dall-e-3`, `dall-e-2`, `stable-diffusion`)
- `ollama`: Ollama server configuration (base URL, model name, timeout)
- `openai`: OpenAI API configuration (API key, models, timeout)
- `claude`: Anthropic Claude configuration (API key, model, timeout)

**Note:** API keys should be kept secure. Consider using environment variables for sensitive data.

### `parameters.json` - Story Parameters
Defines available options for story generation that will appear in the UI.

**Fields:**
- `languages`: List of languages available for story generation
- `complexities`: Story complexity levels (beginner, intermediate, advanced)
- `vocabulary_levels`: Vocabulary diversity options (low, medium, high)
- `age_groups`: Target age groups for stories
- `page_counts`: Available story length options (number of pages)
- `genres`: Story genre/theme options
- `art_styles`: Available illustration styles

**Customization:**
You can add or remove options from any of these lists to customize your story generator.

### `defaults.json` - Default Values
Sets the default selections when creating a new story.

**Fields:**
- `language`: Default language (must be in `parameters.json` languages list)
- `complexity`: Default complexity level
- `vocabulary_diversity`: Default vocabulary level
- `age_group`: Default target age group
- `num_pages`: Default number of pages
- `genre`: Default story genre
- `art_style`: Default illustration style

**Note:** All default values should correspond to options defined in `parameters.json`.

## Modifying Configuration

1. **To add a new language:**
   - Edit `parameters.json` and add the language to the `languages` array
   - Optionally update `defaults.json` if you want it as the default

2. **To change AI providers:**
   - Edit `config.json` and set `text_provider` or `image_provider` to your preferred option
   - Ensure the corresponding provider configuration is filled in

3. **To add custom story genres:**
   - Edit `parameters.json` and add genres to the `genres` array

4. **To set API keys:**
   - Edit `config.json` and fill in the `api_key` field for the provider you're using
   - Alternatively, use environment variables for better security

## Validation

The application will validate these configuration files on startup and create default versions if they don't exist or are invalid.

## Backup

It's recommended to backup these configuration files, especially if you've customized them or added API keys.
