# Children's Story Generator - Application Specifications

## 1. Project Overview

### 1.1 Purpose
An AI-powered application that generates illustrated children's stories in multiple languages to help children learn new languages through engaging, fun stories. The application uses a structured 3-step process, ensuring quality control and character consistency across all generated illustrations.

### 1.2 Core Value Proposition
- **Language Learning Tool**: Create engaging stories in target languages to help children learn
- Automated creation of complete illustrated children's stories
- **Customizable Difficulty**: Adjust story complexity and vocabulary diversity for different learning levels
- User control through approval steps
- Character consistency maintained throughout the story
- Simple, guided workflow for non-technical users

---

## 2. User Workflow

### 2.1 Step 1: Story Text Generation
**Input:**
- Story prompt/theme from user
- Optional parameters:
  - Age group/reading level
  - Story length (number of pages/scenes)
  - Genre/theme preferences
  - Character details (names, traits)
  - **Language** (English, Spanish, French, etc.) - Target language for learning
  - **Story Complexity** (Beginner, Intermediate, Advanced)
    - Sentence structure complexity
    - Grammar difficulty level
    - Use of tenses and verb conjugations
  - **Vocabulary Diversity** (Low, Medium, High)
    - Range of vocabulary used
    - Introduction of new words
    - Repetition frequency for learning reinforcement

**Process:**
1. AI generates complete story text broken into pages
2. User reviews story page by page or all at once
3. User can edit text for any individual page
4. User approves pages:
   - **Option A:** Approve all pages at once (bulk approval)
   - **Option B:** Approve pages individually (one-by-one)
5. Regenerate option available for individual pages if needed

**Output:**
- Complete story text broken into scenes/pages
- Editable text for each page
- User approval required before proceeding to Step 2

### 2.2 Step 2: Image Prompt Generation
**Input:**
- Approved story text from Step 1
- Character descriptions extracted from story

**Process:**
1. AI extracts character information from story:
   - Character names, physical descriptions, clothing
   - Creates master character reference for consistency
2. AI generates detailed image prompts for each page:
   - Scene description based on page text
   - **Character appearance (consistent across ALL prompts)**
   - Setting and background details
   - Art style specifications
   - Composition and framing
3. User reviews prompts page by page or all at once
4. User can edit/modify prompts for any individual page
5. User approves prompts:
   - **Option A:** Approve all prompts at once (bulk approval)
   - **Option B:** Approve prompts individually (one-by-one)
6. Regenerate option available for individual prompts if needed

**Output:**
- Set of image generation prompts (one per page)
- Editable prompts for each page
- Character consistency markers embedded in all prompts
- User approval required before proceeding to Step 3

### 2.3 Step 3: Image Generation
**Input:**
- Approved image prompts from Step 2
- Character consistency reference data

**Process:**
1. User selects generation mode:
   - **Option A:** Generate all images at once (batch generation)
   - **Option B:** Generate images one-by-one (sequential)
2. AI generates images for each page with consistency enforcement:
   - **Character consistency** maintained through:
     - Consistent character descriptions embedded in every prompt
     - Reference style/seed management (if supported by image API)
     - Unified art style parameters across all images
   - **Context consistency** maintained through:
     - Consistent art style (same illustration technique)
     - Color palette consistency
     - Visual storytelling continuity
3. User reviews generated images
4. User can regenerate individual images if:
   - Character appearance is inconsistent
   - Image quality is poor
   - Scene doesn't match the story
5. Consistency validation:
   - Visual review by user
   - Option to regenerate specific images
   - Side-by-side comparison view of all images

**Output:**
- Complete illustrated story with one image per page
- **Character consistency across all illustrations**
- **Visual context consistency** (style, colors, mood)
- Export options for final story

---

## 3. Functional Requirements

### 3.1 Story Generation Features
- [ ] User input form for story parameters
- [ ] **AI provider configuration** (select between Ollama/OpenAI/Claude for text)
- [ ] Language selection with preview
- [ ] Story complexity level selector (Beginner/Intermediate/Advanced)
- [ ] Vocabulary diversity control (Low/Medium/High)
- [ ] AI text generation integration with language-specific prompts
- [ ] **Ollama integration** (default - granite4:small-h model)
- [ ] **Fallback to cloud LLMs** if configured
- [ ] **Per-page text display** (paginated view of story)
- [ ] **Story text editing capability** (edit any individual page)
- [ ] **Bulk approval** (approve all pages at once)
- [ ] **Individual page approval** (approve pages one-by-one)
- [ ] **Page regeneration** (regenerate text for specific pages)
- [ ] Scene/page breakdown management
- [ ] Page navigation (next/previous, jump to page)
- [ ] Vocabulary list generation (new words introduced in the story)

### 3.2 Image Prompt Features
- [ ] **Automatic character extraction** from story text
- [ ] **Master character profile creation** (for consistency)
- [ ] Automatic prompt generation from story text (one per page)
- [ ] **Character consistency tracking** across all prompts
- [ ] **Per-page prompt display** (view prompts individually)
- [ ] **Prompt editing interface** (modify any individual prompt)
- [ ] **Bulk approval** (approve all prompts at once)
- [ ] **Individual prompt approval** (approve prompts one-by-one)
- [ ] **Prompt regeneration** (regenerate specific prompts)
- [ ] Preview/review system for prompts
- [ ] Character reference display (show master character descriptions)

### 3.3 Image Generation Features
- [ ] **DALL-E 3 integration** (default image provider)
- [ ] **Image provider configuration** (DALL-E 2/3, Stable Diffusion options)
- [ ] **Generation mode selection**:
  - [ ] Batch generation (all images at once)
  - [ ] Sequential generation (one-by-one)
- [ ] **Character consistency enforcement**:
  - [ ] Embed character descriptions in all prompts
  - [ ] Visual style consistency parameters
  - [ ] Color palette management
- [ ] **Image regeneration capability** (regenerate individual images)
- [ ] **Side-by-side image comparison** (view all images together)
- [ ] **Individual image preview** (view each page's image)
- [ ] Image quality validation
- [ ] Consistency check alerts (warn about visual inconsistencies)
- [ ] API key management for OpenAI
- [ ] Progress tracking for batch generation

### 3.4 Export and Output Features
- [ ] Complete story compilation
- [ ] Multiple export formats (PDF, image sets, etc.)
- [ ] Print-ready formatting options
- [ ] **Vocabulary list export** (glossary of new words with translations)
- [ ] **Bilingual export option** (side-by-side or interleaved with native language)
- [ ] Save/load project capability
- [ ] Story library/history with language tags

---

## 4. Technical Requirements

### 4.1 AI Integration
**Text Generation:**
- **Default:** Ollama local server running `granite4:small-h` model
  - Free, privacy-focused (no data sent to cloud)
  - Fast local inference
  - Good multilingual support
- **Configurable alternatives:** OpenAI GPT, Anthropic Claude, other Ollama models
- **Multilingual support** with language-specific prompts
- **Complexity control** through prompt engineering
  - Beginner: Simple sentences, present tense, common words
  - Intermediate: Varied sentence structure, multiple tenses, broader vocabulary
  - Advanced: Complex sentences, idiomatic expressions, rich vocabulary
- **Vocabulary diversity control**
  - Low: High repetition of key words (learning reinforcement)
  - Medium: Balanced new words with familiar patterns
  - High: Rich vocabulary with contextual learning
- Age-appropriate content filtering
- Vocabulary extraction and translation capabilities

**Image Generation:**
- **Default:** OpenAI DALL-E 3 API
- **Configurable alternatives:** DALL-E 2, Stable Diffusion (via API or local), Midjourney
- Character consistency techniques (LoRA, IP-Adapter, or prompt engineering)
- Art style presets

### 4.2 Application Architecture
**Frontend:**
- User interface for 3-step workflow
- Form inputs and text editors
- Image gallery/preview
- Progress tracking

**Backend:**
- API request handling
- State management across steps
- Data persistence
- Queue management for generation tasks

**Data Storage:**
- **Local file system** or SQLite database
- User projects/stories stored locally
- Generated content (text and images) saved to local directories
- Character profiles and consistency data
- **Configuration files (JSON)**:
  - `config.json` - AI provider settings, API keys, server URLs
  - `parameters.json` - Story parameters (languages, complexities, age groups, page counts)
  - `defaults.json` - Default values for story generation
  - All parameters configurable without code changes

### 4.3 Technology Stack Considerations
**Platform:**
- **Local web application** (runs on localhost)
- Browser-based interface for better UX
- No cloud hosting required
- All processing happens locally

**Programming Language/Framework:**
- **Python** (excellent AI library support, simple local server)
- **Backend:** Flask or FastAPI (lightweight local server)
- **Frontend:** HTML/CSS/JavaScript or React (served locally)
- **Alternative:** Electron (Python backend + web frontend packaged as desktop app)

**Key Dependencies:**
- `ollama` Python library for local LLM integration
- `openai` Python library for DALL-E API
- HTTP client for API requests
- Image processing library (PIL/Pillow)
- PDF generation library (ReportLab or similar)

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Story generation: < 30 seconds
- Image prompt generation: < 10 seconds per scene
- Image generation: < 60 seconds per image (API dependent)
- Responsive UI with loading states

### 5.2 Usability
- Simple, intuitive interface
- Clear progress indicators
- Easy navigation between steps
- Helpful error messages and guidance

### 5.3 Reliability
- Error handling for API failures
- Retry mechanisms
- Draft auto-save functionality (to local storage)
- Data backup/recovery (local backups)
- Graceful handling of network issues (API calls)

### 5.4 Security
- API key management (secure local storage, environment variables)
- User data privacy (all data stays local)
- Content filtering (child-safe output)
- Rate limiting to prevent accidental API overuse

---

## 6. Character Consistency Strategy

### 6.1 Approaches
**Option A: Detailed Prompt Engineering**
- Create comprehensive character descriptions
- Include in every image prompt
- Maintain consistent descriptors (age, hair, clothing, features)

**Option B: Reference Image + LoRA/Fine-tuning**
- Generate initial character reference
- Use as basis for subsequent generations
- Train custom model or use IP-Adapter

**Option C: Seed-based Consistency**
- Use consistent seeds across generations
- Combine with detailed character descriptions
- Platform-dependent (Stable Diffusion)

### 6.2 Implementation Plan
1. **Extract character information** from approved story text:
   - Character names and roles
   - Physical descriptions mentioned in story
   - Clothing, accessories, distinctive features
2. **Generate master character profile** for each character:
   - Comprehensive physical appearance description
   - Age, height, build
   - Hair color, style, eye color
   - Clothing style and colors
   - Distinctive features or accessories
3. **Create character reference** (optional):
   - Generate initial character reference image
   - Use as visual baseline for subsequent images
4. **Embed character descriptions** in ALL image prompts:
   - Include full character profile in every prompt
   - Ensure consistent wording across all prompts
   - Add style consistency parameters (art style, colors, technique)
5. **Generate images** with consistency enforcement:
   - Use same base prompt structure for all images
   - Maintain character descriptions verbatim
   - Apply consistent art style parameters
6. **Validate consistency** across generated images:
   - Side-by-side visual comparison
   - User review and approval
   - Allow manual regeneration of inconsistent images
7. **Iterative refinement**:
   - User can regenerate individual images
   - Maintain character consistency in regenerations
   - Track which images have been approved

---

## 7. User Stories

### 7.1 Primary User Stories
1. **As a parent**, I want to create fun stories in Spanish for my child, so they can learn Spanish through engaging content
2. **As a language teacher**, I want to generate stories at different difficulty levels, so I can match my students' proficiency
3. **As a bilingual educator**, I want to control vocabulary diversity, so I can introduce new words at the right pace
4. **As a homeschool parent**, I want stories with vocabulary lists, so my child can review new words after reading

### 7.2 User Journey Example
1. User enters story idea: "A brave girl named Luna explores a magical forest"
2. User selects parameters:
   - Language: Spanish
   - Complexity: Beginner
   - Vocabulary Diversity: Medium
   - Length: 5 pages
3. **Step 1: Story Text Generation**
   - System generates complete story in Spanish with 5 pages
   - User reviews pages 1-5 (can navigate between pages)
   - User edits page 3 to simplify a sentence
   - User clicks "Approve All Pages"
   - Vocabulary list shows 15 new Spanish words with English translations
4. **Step 2: Image Prompt Generation**
   - System extracts character: Luna (8 years old, brown hair in braids, green dress, brown boots)
   - System generates 5 image prompts, each including Luna's description
   - User reviews prompts (can navigate between prompts)
   - User edits prompt for page 2 to add more forest detail
   - User clicks "Approve All Prompts"
5. **Step 3: Image Generation**
   - User selects "Generate All Images" (batch mode)
   - System generates 5 illustrations with Luna appearing consistent
   - User reviews images in side-by-side view
   - User notices page 4 image has Luna with different hair color
   - User clicks "Regenerate" for page 4 only
   - New image 4 shows Luna correctly
   - User approves all images
6. User downloads complete illustrated storybook as PDF with vocabulary list at the end

---

## 8. Future Enhancements (Post-MVP)

### 8.1 Advanced Features
- [ ] Multiple illustration styles (watercolor, digital, cartoon)
- [ ] **Audio narration in target language** (pronunciation practice)
- [ ] **Interactive vocabulary quizzes** after story completion
- [ ] **Translation toggle** (show/hide native language translation)
- [ ] **Word highlighting** (click words to see translations)
- [ ] Animation of illustrations
- [ ] Interactive story choices (branching narratives)
- [ ] **Progress tracking** (vocabulary learned, stories completed)
- [ ] **Difficulty progression** (adaptive complexity based on user progress)
- [ ] Template library (common story structures)
- [ ] **Cultural context notes** (explain cultural references in stories)

### 8.2 Platform Expansion
- [ ] Mobile app version
- [ ] Print-on-demand integration
- [ ] Social sharing features
- [ ] Story marketplace/community

---

## 9. Success Metrics

### 9.1 Quality Metrics
- Story text coherence and age-appropriateness
- **Language accuracy** (grammar, vocabulary usage)
- **Appropriate complexity level** for selected difficulty
- Character consistency score across images
- User approval rate per step
- Time from start to completed story
- **Vocabulary diversity match** to selected level

### 9.2 User Metrics
- Story completion rate
- User retention
- Stories generated per user
- User satisfaction scores

---

## 10. Constraints and Assumptions

### 10.1 Constraints
- API costs for text and image generation
- API rate limits
- Image generation time (user patience)
- Storage requirements for images

### 10.2 Assumptions
- Users have internet connection
- Users understand basic story elements
- AI-generated content meets quality standards
- Character consistency is achievable with chosen tools

---

## 10. User Interface Mockup

### 10.1 Main Screen - Story Setup
```
┌─────────────────────────────────────────────────────────────────┐
│  🎨 Children's Story Generator - Language Learning Edition      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Create New Story                                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Story Idea / Prompt:                                        │ │
│  │ ┌────────────────────────────────────────────────────────┐ │ │
│  │ │ A brave girl named Luna explores a magical forest     │ │ │
│  │ └────────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  │ Target Language: [Spanish ▼]                                │ │
│  │ Story Length:    [5 pages ▼]                                │ │
│  │ Age Group:       [4-7 years ▼]                              │ │
│  │ Complexity:      ○ Beginner  ◉ Intermediate  ○ Advanced    │ │
│  │ Vocabulary:      ○ Low       ◉ Medium        ○ High        │ │
│  │                                                             │ │
│  │         [Generate Story]                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Recent Stories:                                                 │
│  • Luna's Forest Adventure (Spanish) - 2026-01-10              │
│  • El Gato Valiente (Spanish) - 2026-01-08                     │
│                                                                  │
│  Settings: [⚙️ Configure AI Providers]                          │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Step 1 - Story Text Review & Editing
```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1 of 3: Review Story Text                   [✓ Approved]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Luna's Forest Adventure (Spanish - Beginner)                   │
│                                                                  │
│  ┌─ Pages ──────────────────────────────────────────────────┐  │
│  │  [1] [2] [3] [4] [5]                    Page 1 of 5       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Page 1 Content ─────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Luna era una niña valiente. Un día, ella decidió        │  │
│  │  explorar el bosque mágico cerca de su casa. El bosque   │  │
│  │  estaba lleno de árboles grandes y flores bonitas.        │  │
│  │                                                            │  │
│  │  [✏️ Edit Page]  [🔄 Regenerate Page]  [✓ Approve Page]   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Vocabulary (15 new words) ──────────────────────────────┐  │
│  │  • valiente (brave)        • decidió (decided)            │  │
│  │  • explorar (to explore)   • bosque (forest)              │  │
│  │  • cerca (near)            • lleno (full)                 │  │
│  │  • árboles (trees)         • flores (flowers)             │  │
│  │  [Show all...]                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [< Back]  [Approve All Pages]  [Next: Image Prompts >]        │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Step 2 - Image Prompt Review & Editing
```
┌─────────────────────────────────────────────────────────────────┐
│  Step 2 of 3: Review Image Prompts                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Character Reference ─────────────────────────────────────┐ │
│  │  Luna: 8 years old, brown hair in two braids, big brown   │ │
│  │  eyes, green dress with yellow flowers, brown boots,      │ │
│  │  cheerful expression, adventurous personality             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ Prompts ────────────────────────────────────────────────┐  │
│  │  [1] [2] [3] [4] [5]                    Prompt 1 of 5     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Page 1 Image Prompt ────────────────────────────────────┐  │
│  │                                                            │  │
│  │  A children's book illustration in watercolor style       │  │
│  │  showing Luna, an 8-year-old girl with brown hair in two  │  │
│  │  braids, wearing a green dress with yellow flowers and    │  │
│  │  brown boots, standing at the edge of a magical forest.   │  │
│  │  The forest has large trees and colorful flowers. Bright, │  │
│  │  cheerful atmosphere. Luna looks excited and brave.       │  │
│  │                                                            │  │
│  │  [✏️ Edit Prompt]  [🔄 Regenerate]  [✓ Approve Prompt]    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [< Back to Text]  [Approve All Prompts]  [Next: Generate >]   │
└─────────────────────────────────────────────────────────────────┘
```

### 10.4 Step 3 - Image Generation & Review
```
┌─────────────────────────────────────────────────────────────────┐
│  Step 3 of 3: Generate Images                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Generation Mode:  ◉ Generate All  ○ One-by-One                │
│                                                                  │
│  [🎨 Generate All Images]                                       │
│                                                                  │
│  ┌─ Generated Images ───────────────────────────────────────┐  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │  │
│  │  │ [1]  │ │ [2]  │ │ [3]  │ │ [4]  │ │ [5]  │            │  │
│  │  │      │ │      │ │      │ │ ⚠️   │ │      │            │  │
│  │  │Luna  │ │Forest│ │Creek │ │Cave  │ │Home  │            │  │
│  │  │ ✓    │ │ ✓    │ │ ✓    │ │      │ │ ✓    │            │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │  │
│  │                                                             │  │
│  │  Click image to view full size                             │  │
│  │  ⚠️ Page 4: Character appearance may be inconsistent       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Current Image: Page 4 ──────────────────────────────────┐  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────┐                     │  │
│  │  │                                   │                     │  │
│  │  │        [Image Preview]            │                     │  │
│  │  │   Luna entering dark cave         │                     │  │
│  │  │                                   │                     │  │
│  │  └──────────────────────────────────┘                     │  │
│  │                                                            │  │
│  │  [🔄 Regenerate This Image]  [✓ Approve]                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [< Back to Prompts]  [View Side-by-Side]  [Export Story >]    │
└─────────────────────────────────────────────────────────────────┘
```

### 10.5 Side-by-Side Comparison View
```
┌─────────────────────────────────────────────────────────────────┐
│  Character Consistency Review - Side by Side                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │ Page 1 │  │ Page 2 │  │ Page 3 │  │ Page 4 │  │ Page 5 │   │
│  │        │  │        │  │        │  │        │  │        │   │
│  │ [img]  │  │ [img]  │  │ [img]  │  │ [img]  │  │ [img]  │   │
│  │        │  │        │  │        │  │  ⚠️    │  │        │   │
│  │  ✓     │  │  ✓     │  │  ✓     │  │        │  │  ✓     │   │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │
│                                                                  │
│  Consistency Check:                                             │
│  • Hair color: ✓ Consistent across all images                  │
│  • Clothing: ⚠️  Page 4 shows different dress color            │
│  • Art style: ✓ Consistent watercolor style                    │
│                                                                  │
│  [🔄 Regenerate Flagged Images]  [✓ Approve All]  [Close]      │
└─────────────────────────────────────────────────────────────────┘
```

### 10.6 Final Export Screen
```
┌─────────────────────────────────────────────────────────────────┐
│  Export Story                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Luna's Forest Adventure                                        │
│  Language: Spanish | Pages: 5 | Vocabulary: 15 words           │
│                                                                  │
│  ┌─ Export Options ──────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Format:                                                    │ │
│  │  ☑ PDF (with vocabulary list)                              │ │
│  │  ☐ Images only (ZIP)                                       │ │
│  │  ☐ Bilingual PDF (Spanish + English)                       │ │
│  │                                                             │ │
│  │  Options:                                                   │ │
│  │  ☑ Include vocabulary list at end                          │ │
│  │  ☑ Print-ready format (8.5x11")                            │ │
│  │  ☐ Include pronunciation guide                             │ │
│  │                                                             │ │
│  │  Output Folder:                                             │ │
│  │  /Users/you/Stories/Luna-Forest-Adventure/                 │ │
│  │  [Browse...]                                                │ │
│  │                                                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [< Back]  [Save Project]  [Export Story]                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.7 Settings / Configuration Screen
```
┌─────────────────────────────────────────────────────────────────┐
│  Settings                                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ AI Provider Configuration ───────────────────────────────┐ │
│  │                                                             │ │
│  │  Text Generation Provider:                                 │ │
│  │  ◉ Ollama (Local)    ○ OpenAI    ○ Anthropic Claude       │ │
│  │                                                             │ │
│  │  Ollama Settings:                                           │ │
│  │  Server URL: [http://localhost:11434        ]              │ │
│  │  Model:      [granite4:small-h ▼]                          │ │
│  │  [Test Connection]                                          │ │
│  │                                                             │ │
│  │  Image Generation Provider:                                 │ │
│  │  ◉ DALL-E 3    ○ DALL-E 2    ○ Stable Diffusion           │ │
│  │                                                             │ │
│  │  OpenAI Settings:                                           │ │
│  │  API Key: [sk-...************************] [Show] [Test]   │ │
│  │  Model:   [dall-e-3 ▼]                                     │ │
│  │                                                             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ Default Settings ────────────────────────────────────────┐ │
│  │  Default Language:    [Spanish ▼]                          │ │
│  │  Default Complexity:  [Beginner ▼]                         │ │
│  │  Default Story Length: [5 pages ▼]                         │ │
│  │  Auto-save:           [✓] Every 2 minutes                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Cancel]  [Save Settings]                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 10.8 UI/UX Design Notes

**Navigation Flow:**
1. Main Setup → Step 1 (Text) → Step 2 (Prompts) → Step 3 (Images) → Export
2. User can go back at any step without losing progress
3. Auto-save functionality preserves work at each step

**Key UX Principles:**
- **Progressive Disclosure**: Show only relevant options at each step
- **Clear Status Indicators**: Visual feedback on approval status (✓, ⚠️)
- **Flexible Workflow**: Support both bulk and individual operations
- **Visual Consistency Validation**: Side-by-side view for character consistency
- **Page-by-Page Control**: Navigate, edit, and approve individual pages/prompts
- **Responsive Feedback**: Loading states, progress bars for batch operations

**Color Coding:**
- ✓ Green: Approved/Successful
- ⚠️ Yellow: Warning/Needs attention
- 🔄 Blue: Action available (regenerate, edit)
- ✏️ Gray: Edit mode available

---

## 11. Open Questions

1. **Target age range:** What specific age group(s)? (0-3, 4-7, 8-12?)
2. **Story length:** How many scenes/pages per story? (5, 10, 20?)
3. **~~Platform priority~~:** ✓ Local web application (localhost)
4. **~~Monetization~~:** ✓ Personal use (user covers their own API costs via API keys)
5. **~~AI providers~~:** ✓ Default: Ollama (granite4:small-h) + DALL-E 3 (configurable)
6. **Default language:** What should be the default language? Priority languages to support initially? (Spanish, French, Mandarin, German?)
7. **~~User accounts~~:** ✓ Not required (local application, single user)
8. **Content moderation:** How to ensure child-safe content?

---

## 12. Next Steps

1. **Clarify open questions** with stakeholders
2. **~~Choose technology stack~~** ✓ Python + Flask/FastAPI + Ollama + DALL-E
3. **Set up development environment**
   - Install Python 3.10+
   - Install and configure Ollama
   - Pull granite4:small-h model
   - Set up OpenAI API key for DALL-E
4. **Create proof-of-concept** for character consistency
5. **Test Ollama integration** with multilingual story generation
6. **Test DALL-E API** for image generation
7. **Design wireframes/mockups** for 3-step workflow
8. **Build MVP** with core 3-step functionality
9. **Test with target users** and iterate

### Prerequisites for Development
- **Ollama installed and running** locally
- `granite4:small-h` model pulled (`ollama pull granite4:small-h`)
- **OpenAI API account** with DALL-E access
- Python development environment

---

**Document Version:** 1.0
**Last Updated:** 2026-01-12
**Status:** Draft - Awaiting stakeholder review
