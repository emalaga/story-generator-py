# Development Plan - Story Generator

This document tracks the development progress through the test-driven development phases outlined in ARCHITECTURE.md.

**Status Legend:**
- ⬜ Not Started
- 🔄 In Progress
- ✅ Completed
- ⏸️ Blocked/On Hold

---

## Phase 1: Foundation - Data Models (FIRST PRIORITY)

**Goal:** Define and test all core data structures

**Status:** 🔄 In Progress (1/5 tasks completed)

### Tasks

#### 1.1 Configuration Models (`src/models/config.py`) ✅ COMPLETED
- ✅ Create enums (TextProvider, ImageProvider)
- ✅ Create AI config dataclasses (OllamaConfig, OpenAIConfig, ClaudeConfig)
- ✅ Create AIProviderConfig dataclass
- ✅ Create StoryParameters dataclass (from parameters.json)
- ✅ Create DefaultValues dataclass (from defaults.json)
- ✅ Create AppConfig dataclass
- ✅ Write unit tests (`tests/unit/test_models/test_config.py`)
- ✅ Run tests and verify all pass (19/19 tests passed)

**Dependencies:** None (start here!)

**Priority:** HIGH - Foundation for entire app

---

#### 1.2 Story Models (`src/models/story.py`)
- ⬜ Create StoryMetadata dataclass
- ⬜ Create StoryPage dataclass
- ⬜ Create Story dataclass
- ⬜ Write unit tests (`tests/unit/test_models/test_story.py`)
- ⬜ Run tests and verify all pass

**Dependencies:** None

**Priority:** HIGH - Core domain model

---

#### 1.3 Character Models (`src/models/character.py`)
- ⬜ Create Character dataclass
- ⬜ Create CharacterProfile dataclass
- ⬜ Write unit tests (`tests/unit/test_models/test_character.py`)
- ⬜ Run tests and verify all pass

**Dependencies:** None

**Priority:** HIGH - Critical for consistency

---

#### 1.4 Image Prompt Models (`src/models/image_prompt.py`)
- ⬜ Create ImagePrompt dataclass
- ⬜ Write unit tests (`tests/unit/test_models/test_image_prompt.py`)
- ⬜ Run tests and verify all pass

**Dependencies:** Character models (1.3)

**Priority:** HIGH - Core domain model

---

#### 1.5 Project Models (`src/models/project.py`)
- ⬜ Create Project dataclass
- ⬜ Create ProjectStatus enum
- ⬜ Write unit tests (`tests/unit/test_models/test_project.py`)
- ⬜ Run tests and verify all pass

**Dependencies:** Story, Character, ImagePrompt models (1.2, 1.3, 1.4)

**Priority:** MEDIUM - Needed for persistence

---

## Phase 2: Data Persistence - Repositories

**Goal:** Implement data loading/saving with JSON

**Status:** ⬜ Not Started

### Tasks

#### 2.1 Config Repository (`src/repositories/config_repository.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_repositories/test_config_repository.py`)
- ⬜ Implement ConfigRepository class
  - ⬜ `load_app_config()` method
  - ⬜ `save_app_config()` method
  - ⬜ `_load_ai_config()` method
  - ⬜ `_load_parameters()` method
  - ⬜ `_load_defaults()` method
  - ⬜ `_create_default_*()` methods
  - ⬜ `_save_*()` methods
  - ⬜ `update_api_key()` method
  - ⬜ `validate_configuration()` method
- ⬜ Run tests and verify all pass
- ⬜ Test with actual JSON files in `data/config/`

**Dependencies:** Configuration models (1.1)

**Priority:** HIGH - Needed for configuration loading

---

#### 2.2 Project Repository (`src/repositories/project_repository.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_repositories/test_project_repository.py`)
- ⬜ Implement ProjectRepository class
  - ⬜ `save_project()` method
  - ⬜ `load_project()` method
  - ⬜ `list_projects()` method
  - ⬜ `delete_project()` method
- ⬜ Run tests and verify all pass

**Dependencies:** Project models (1.5)

**Priority:** MEDIUM - Needed for saving stories

---

#### 2.3 Image Repository (`src/repositories/image_repository.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_repositories/test_image_repository.py`)
- ⬜ Implement ImageRepository class
  - ⬜ `save_image()` method
  - ⬜ `load_image()` method
  - ⬜ `delete_image()` method
- ⬜ Run tests and verify all pass

**Dependencies:** None

**Priority:** MEDIUM - Needed for image storage

---

## Phase 3: AI Integration - External Services

**Goal:** Integrate with Ollama, OpenAI, Claude

**Status:** ⬜ Not Started

### Tasks

#### 3.1 Base AI Client (`src/ai/base_client.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_ai/test_base_client.py`)
- ⬜ Create AIClient abstract base class
- ⬜ Define interface methods
- ⬜ Run tests and verify all pass

**Dependencies:** Configuration models (1.1)

**Priority:** HIGH - Foundation for AI integration

---

#### 3.2 Ollama Client (`src/ai/ollama_client.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_ai/test_ollama_client.py`)
- ⬜ Implement OllamaClient class
  - ⬜ `generate_text()` method
  - ⬜ Connection handling
  - ⬜ Error handling
- ⬜ Run tests with mocked responses
- ⬜ Test with actual Ollama server (if available)

**Dependencies:** Base AI Client (3.1)

**Priority:** HIGH - Default text provider

---

#### 3.3 OpenAI Client (`src/ai/openai_client.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_ai/test_openai_client.py`)
- ⬜ Implement OpenAIClient class
  - ⬜ `generate_text()` method
  - ⬜ `generate_image()` method
  - ⬜ API key handling
  - ⬜ Error handling
- ⬜ Run tests with mocked responses
- ⬜ Test with actual OpenAI API (optional)

**Dependencies:** Base AI Client (3.1)

**Priority:** HIGH - Default image provider

---

#### 3.4 Claude Client (`src/ai/claude_client.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_ai/test_claude_client.py`)
- ⬜ Implement ClaudeClient class
  - ⬜ `generate_text()` method
  - ⬜ API key handling
  - ⬜ Error handling
- ⬜ Run tests with mocked responses
- ⬜ Test with actual Claude API (optional)

**Dependencies:** Base AI Client (3.1)

**Priority:** MEDIUM - Alternative text provider

---

#### 3.5 AI Client Factory (`src/ai/ai_factory.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_ai/test_ai_factory.py`)
- ⬜ Implement AIClientFactory class
  - ⬜ `create_text_client()` method
  - ⬜ `create_image_client()` method
- ⬜ Run tests and verify all pass

**Dependencies:** All AI clients (3.1, 3.2, 3.3, 3.4)

**Priority:** HIGH - Needed for dependency injection

---

## Phase 4: Domain Logic - Core Business Rules

**Goal:** Implement story generation, character extraction, prompt building

**Status:** ⬜ Not Started

### Tasks

#### 4.1 Character Extractor (`src/domain/character_extractor.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_domain/test_character_extractor.py`)
- ⬜ Implement CharacterExtractor class
  - ⬜ `extract_characters()` method
  - ⬜ `create_character_profile()` method
- ⬜ Run tests and verify all pass

**Dependencies:** Character models (1.3), AI clients (3.x)

**Priority:** HIGH - Critical for consistency

---

#### 4.2 Vocabulary Analyzer (`src/domain/vocabulary_analyzer.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_domain/test_vocabulary_analyzer.py`)
- ⬜ Implement VocabularyAnalyzer class
  - ⬜ `extract_vocabulary()` method
  - ⬜ `calculate_diversity()` method
- ⬜ Run tests and verify all pass

**Dependencies:** Story models (1.2)

**Priority:** MEDIUM - Language learning feature

---

#### 4.3 Prompt Builder (`src/domain/prompt_builder.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_domain/test_prompt_builder.py`)
- ⬜ Implement PromptBuilder class
  - ⬜ `build_story_prompt()` method
  - ⬜ `build_image_prompt()` method
  - ⬜ Template management
- ⬜ Run tests and verify all pass

**Dependencies:** Story, Character, ImagePrompt models (1.2, 1.3, 1.4)

**Priority:** HIGH - Core generation logic

---

## Phase 5: Service Layer - Orchestration

**Goal:** Coordinate domain logic and AI calls

**Status:** ⬜ Not Started

### Tasks

#### 5.1 Story Generator Service (`src/services/story_generator_service.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_services/test_story_generator_service.py`)
- ⬜ Implement StoryGeneratorService class
  - ⬜ `generate_story()` method
  - ⬜ `regenerate_page()` method
  - ⬜ Story validation
- ⬜ Run tests and verify all pass

**Dependencies:** Domain logic (4.1, 4.2, 4.3), AI clients (3.x)

**Priority:** HIGH - Core service

---

#### 5.2 Image Generator Service (`src/services/image_generator_service.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_services/test_image_generator_service.py`)
- ⬜ Implement ImageGeneratorService class
  - ⬜ `generate_image_prompts()` method
  - ⬜ `generate_images()` method
  - ⬜ `regenerate_image()` method
  - ⬜ Consistency enforcement
- ⬜ Run tests and verify all pass

**Dependencies:** Domain logic (4.1, 4.3), AI clients (3.x)

**Priority:** HIGH - Core service

---

#### 5.3 Export Service (`src/services/export_service.py`)
- ⬜ Write unit tests FIRST (`tests/unit/test_services/test_export_service.py`)
- ⬜ Implement ExportService class
  - ⬜ `export_to_pdf()` method
  - ⬜ `export_images_zip()` method
  - ⬜ PDF layout/formatting
- ⬜ Run tests and verify all pass

**Dependencies:** Story models (1.2), Image repository (2.3)

**Priority:** MEDIUM - Output feature

---

## Phase 6: Web Interface - Flask Routes

**Goal:** Build REST API and serve web UI

**Status:** ⬜ Not Started

### Tasks

#### 6.1 Flask Application Setup (`src/app.py`)
- ⬜ Create Flask app instance
- ⬜ Configure CORS
- ⬜ Set up error handlers
- ⬜ Load configuration from JSON
- ⬜ Initialize services with dependency injection
- ⬜ Test basic server startup

**Dependencies:** All services (5.x), Config repository (2.1)

**Priority:** HIGH - Application entry point

---

#### 6.2 Story Routes (`src/routes/story_routes.py`)
- ⬜ Write integration tests FIRST (`tests/integration/test_story_routes.py`)
- ⬜ Implement routes:
  - ⬜ `POST /api/stories` - Create new story
  - ⬜ `GET /api/stories/:id` - Get story
  - ⬜ `PUT /api/stories/:id/pages/:page_num` - Update page
  - ⬜ `POST /api/stories/:id/pages/:page_num/regenerate` - Regenerate page
- ⬜ Run tests and verify all pass

**Dependencies:** Story Generator Service (5.1)

**Priority:** HIGH - Core API

---

#### 6.3 Image Routes (`src/routes/image_routes.py`)
- ⬜ Write integration tests FIRST (`tests/integration/test_image_routes.py`)
- ⬜ Implement routes:
  - ⬜ `POST /api/stories/:id/prompts` - Generate prompts
  - ⬜ `PUT /api/stories/:id/prompts/:page_num` - Update prompt
  - ⬜ `POST /api/stories/:id/images` - Generate images
  - ⬜ `POST /api/stories/:id/images/:page_num/regenerate` - Regenerate image
- ⬜ Run tests and verify all pass

**Dependencies:** Image Generator Service (5.2)

**Priority:** HIGH - Core API

---

#### 6.4 Project Routes (`src/routes/project_routes.py`)
- ⬜ Write integration tests FIRST (`tests/integration/test_project_routes.py`)
- ⬜ Implement routes:
  - ⬜ `GET /api/projects` - List projects
  - ⬜ `POST /api/projects` - Save project
  - ⬜ `GET /api/projects/:id` - Load project
  - ⬜ `DELETE /api/projects/:id` - Delete project
- ⬜ Run tests and verify all pass

**Dependencies:** Project Repository (2.2)

**Priority:** MEDIUM - Persistence API

---

#### 6.5 Config Routes (`src/routes/config_routes.py`)
- ⬜ Write integration tests FIRST (`tests/integration/test_config_routes.py`)
- ⬜ Implement routes:
  - ⬜ `GET /api/config` - Get configuration
  - ⬜ `PUT /api/config/api-keys` - Update API keys
  - ⬜ `GET /api/config/parameters` - Get story parameters
- ⬜ Run tests and verify all pass

**Dependencies:** Config Repository (2.1)

**Priority:** MEDIUM - Configuration API

---

#### 6.6 Static Frontend Files (`src/static/` and `src/templates/`)
- ⬜ Create HTML templates
- ⬜ Create CSS styles
- ⬜ Create JavaScript for UI interactions
- ⬜ Test in browser

**Dependencies:** All API routes (6.2, 6.3, 6.4, 6.5)

**Priority:** MEDIUM - User interface

---

## Phase 7: Integration & Testing

**Goal:** End-to-end testing and refinement

**Status:** ⬜ Not Started

### Tasks

#### 7.1 Integration Tests
- ⬜ Write story generation flow test (`tests/integration/test_story_generation_flow.py`)
- ⬜ Write image generation flow test (`tests/integration/test_image_generation_flow.py`)
- ⬜ Write full workflow test (story → prompts → images → export)
- ⬜ Run all tests and verify pass

**Dependencies:** All previous phases

**Priority:** HIGH - Quality assurance

---

#### 7.2 Manual Testing
- ⬜ Test with real Ollama server
- ⬜ Test with real OpenAI API
- ⬜ Generate complete test story
- ⬜ Test character consistency
- ⬜ Test vocabulary extraction
- ⬜ Test PDF export
- ⬜ Test error handling

**Dependencies:** Complete application (all phases)

**Priority:** HIGH - Real-world validation

---

#### 7.3 Performance Optimization
- ⬜ Profile API response times
- ⬜ Optimize slow operations
- ⬜ Add caching where appropriate
- ⬜ Test batch image generation

**Dependencies:** Working application

**Priority:** LOW - After MVP works

---

#### 7.4 Documentation
- ⬜ Update README with setup instructions
- ⬜ Create API documentation
- ⬜ Add code comments
- ⬜ Create user guide

**Dependencies:** Complete application

**Priority:** MEDIUM - For handoff/maintenance

---

## Current Status Summary

**Overall Progress:** 1% (1/95 tasks completed)

**Completed:**
- ✅ Phase 1.1: Configuration Models (19/19 tests passed)

**Next Immediate Steps:**
1. Start Phase 1.2: Create Story models
2. Write tests for Story models
3. Implement Story models
4. Run tests and verify they pass

**Blockers:** None

**Notes:**
- Virtual environment created ✅
- Dependencies installed ✅
- pytest upgraded to 9.0.2 ✅
- Configuration files created ✅
- Configuration models implemented and tested ✅
- All 19 tests passing ✅

---

**Last Updated:** 2026-01-12
