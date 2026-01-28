// ===== Global State =====
let currentStory = null;
let currentConfig = null;
let currentTab = 'projects';

// ===== API Base URL =====
const API_BASE = '/api';

// ===== Image URL Helper =====
// Converts local_image_path to API URL, or falls back to original URL
function getImageUrl(localPath, fallbackUrl) {
    if (localPath) {
        return `${API_BASE}/${localPath}`;  // Convert 'images/...' to '/api/images/...'
    }
    return fallbackUrl;
}

// ===== DOM Elements =====
const storyForm = document.getElementById('story-form');
const generateBtn = document.getElementById('generate-btn-top');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error-message');
const storyDisplaySection = document.getElementById('story-display-section');
const noStoryPlaceholder = document.getElementById('no-story-placeholder');
const saveProjectBtn = document.getElementById('save-project-btn');
const newStoryBtn = document.getElementById('new-story-btn');
const loadProjectsBtn = document.getElementById('load-projects-btn');

// ===== Initialize App =====
document.addEventListener('DOMContentLoaded', async () => {
    await loadConfiguration();
    await loadProjects();
    setupEventListeners();
    setupTabs();
});

// ===== Setup Tabs =====
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    currentTab = tabName;

    // Update tabs based on which one is selected
    if (tabName === 'visual-consistency') {
        updateVisualConsistencyTab();
    } else if (tabName === 'image-generation') {
        updateImageGenerationTab();
    } else if (tabName === 'pdf-export') {
        updatePDFTab();
    }
}

function updateImageGenerationTab() {
    const noStoryDiv = document.getElementById('image-gen-no-story');
    const contentDiv = document.getElementById('image-gen-content');

    if (!currentStory || !currentStory.pages || currentStory.pages.length === 0) {
        noStoryDiv.classList.remove('hidden');
        contentDiv.classList.add('hidden');
        return;
    }

    noStoryDiv.classList.add('hidden');
    contentDiv.classList.remove('hidden');

    // Update story info bar
    const infoBar = document.getElementById('image-story-info');
    infoBar.innerHTML = `
        <h3>${currentStory.metadata.title}</h3>
        <p>${currentStory.pages.length} pages &bull; ${currentStory.metadata.art_style || 'cartoon'} style</p>
    `;

    // Update pages list
    const pagesList = document.getElementById('image-pages-list');
    pagesList.innerHTML = '';

    currentStory.pages.forEach(page => {
        const pageCard = document.createElement('div');
        pageCard.className = 'image-page-card';
        pageCard.innerHTML = `
            <h4>Page ${page.page_number}</h4>
            <div class="image-page-content">
                <div class="image-preview-section">
                    <div id="page-${page.page_number}-image-preview">
                        ${(page.local_image_path || page.image_url)
                            ? `<img src="${getImageUrl(page.local_image_path, page.image_url)}" alt="Page ${page.page_number} illustration">
                               <div class="image-action-buttons">
                                   <button class="btn-small btn-delete-image" onclick="deletePageImage(${page.page_number})">Delete Image</button>
                               </div>`
                            : '<div class="image-placeholder">No image generated yet</div>'
                        }
                    </div>
                    <div class="image-loading hidden" id="page-${page.page_number}-loading">
                        <div class="spinner-small"></div>
                        <span>Generating image...</span>
                    </div>
                </div>
                <div class="image-controls-section">
                    <div>
                        <label><strong>Page Text:</strong></label>
                        <div class="page-text-display">${page.text}</div>
                    </div>
                    <div class="page-prompt-section">
                        <label for="page-${page.page_number}-prompt">Image Prompt (editable):</label>
                        <textarea class="page-prompt-edit" id="page-${page.page_number}-prompt" rows="5">${page.image_prompt || ''}</textarea>
                        <button class="btn-small" onclick="generateImagePrompt(${page.page_number})">
                            ${page.image_prompt ? 'Regenerate' : 'Generate'} Prompt
                        </button>
                    </div>
                    <div class="image-actions">
                        <button class="btn-small" onclick="generatePageImage(${page.page_number})">
                            ${(page.local_image_path || page.image_url) ? 'Regenerate' : 'Generate'} Image
                        </button>
                    </div>
                </div>
            </div>
        `;
        pagesList.appendChild(pageCard);
    });
}

// ===== Load Configuration from API =====
async function loadConfiguration() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        if (!response.ok) throw new Error('Failed to load configuration');

        currentConfig = await response.json();
        populateFormFields();
    } catch (error) {
        showError('Failed to load configuration: ' + error.message);
    }
}

// ===== Populate Form Fields =====
function populateFormFields() {
    if (!currentConfig) return;

    const { parameters, defaults } = currentConfig;

    // Populate dropdowns
    populateSelect('language', parameters.languages, defaults.language);
    populateSelect('age-group', parameters.age_groups, defaults.age_group);
    populateSelect('complexity', parameters.complexities, defaults.complexity);
    populateSelect('vocabulary', parameters.vocabulary_levels, defaults.vocabulary_diversity);
    // num-pages is now a text input, not a dropdown
    populateSelect('genre', parameters.genres, defaults.genre);
    populateSelect('art-style', parameters.art_styles, defaults.art_style);
}

// ===== Populate Select Element =====
function populateSelect(elementId, options, defaultValue) {
    const select = document.getElementById(elementId);
    select.innerHTML = '';

    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        if (option === defaultValue) {
            optionElement.selected = true;
        }
        select.appendChild(optionElement);
    });
}

// ===== Setup Event Listeners =====
function setupEventListeners() {
    storyForm.addEventListener('submit', handleStoryGeneration);
    saveProjectBtn.addEventListener('click', handleSaveProject);
    newStoryBtn.addEventListener('click', handleNewStory);
    loadProjectsBtn.addEventListener('click', loadProjects);
}

// ===== Handle Story Generation =====
async function handleStoryGeneration(e) {
    e.preventDefault();

    const formData = new FormData(storyForm);
    const data = {
        title: formData.get('title'),
        language: formData.get('language'),
        age_group: formData.get('age_group'),
        complexity: formData.get('complexity'),
        vocabulary_diversity: formData.get('vocabulary_diversity'),
        num_pages: parseInt(formData.get('num_pages')),
        words_per_page: parseInt(formData.get('words_per_page')) || 50,
        genre: formData.get('genre'),
        art_style: formData.get('art_style'),
    };

    // Add optional fields if provided
    if (formData.get('theme')) {
        data.theme = formData.get('theme');
    }
    if (formData.get('custom_prompt')) {
        data.custom_prompt = formData.get('custom_prompt');
    }

    showLoading();
    hideError();

    try {
        const response = await fetch(`${API_BASE}/stories`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate story');
        }

        currentStory = await response.json();

        // Debug logging
        console.log('=== STORY GENERATED ===');
        console.log('Story ID:', currentStory.id);
        console.log('Characters:', currentStory.characters);
        console.log('Number of characters:', (currentStory.characters || []).length);

        // Reset Visual Consistency tab for new story
        resetVisualConsistencyTab();

        displayStory(currentStory);
        hideLoading();
    } catch (error) {
        hideLoading();
        showError('Failed to generate story: ' + error.message);
    }
}

// ===== Display Story (Text Only) =====
function displayStory(story) {
    // Hide placeholder, show story
    noStoryPlaceholder.classList.add('hidden');
    storyDisplaySection.classList.remove('hidden');

    // Display metadata
    const metadataDiv = document.getElementById('story-metadata');
    metadataDiv.innerHTML = `
        <h3>${story.metadata.title}</h3>
        <p><strong>Language:</strong> ${story.metadata.language}</p>
        <p><strong>Age Group:</strong> ${story.metadata.age_group}</p>
        <p><strong>Genre:</strong> ${story.metadata.genre || 'N/A'}</p>
        <p><strong>Pages:</strong> ${story.metadata.num_pages}</p>
        <p><strong>Art Style:</strong> ${story.metadata.art_style || 'N/A'}</p>
    `;

    // Display pages (text only, editable)
    const pagesDiv = document.getElementById('story-pages');
    pagesDiv.innerHTML = '<h3>Story Pages</h3>';

    // Check if pages exist
    if (!story.pages || story.pages.length === 0) {
        pagesDiv.innerHTML += '<p>No pages generated. Please try generating the story again.</p>';
        console.error('Story has no pages:', story);
        return;
    }

    story.pages.forEach(page => {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'story-page';
        pageDiv.innerHTML = `
            <h4>Page ${page.page_number}</h4>
            <div class="page-text-section">
                <textarea class="page-text-edit" id="page-${page.page_number}-text" rows="4">${page.text}</textarea>
                <button class="btn-text-save" onclick="savePageText(${page.page_number})">Save Text</button>
            </div>
        `;
        pagesDiv.appendChild(pageDiv);
    });

    // Display characters (editable)
    const charactersDiv = document.getElementById('story-characters');
    if (story.characters && story.characters.length > 0) {
        charactersDiv.innerHTML = '<h3>Characters</h3>';
        story.characters.forEach((char, index) => {
            const charDiv = document.createElement('div');
            charDiv.className = 'character-card';
            charDiv.innerHTML = `
                <h4>${char.name}</h4>
                <div class="character-field">
                    <label for="char-${index}-species"><strong>Species:</strong></label>
                    <input type="text" id="char-${index}-species" value="${char.species || ''}" placeholder="e.g., rabbit, human, dragon">
                </div>
                <div class="character-field">
                    <label for="char-${index}-description"><strong>Description:</strong></label>
                    <textarea id="char-${index}-description" rows="2" placeholder="Physical appearance...">${char.physical_description || ''}</textarea>
                </div>
                <div class="character-field">
                    <label for="char-${index}-clothing"><strong>Clothing:</strong></label>
                    <textarea id="char-${index}-clothing" rows="2" placeholder="What they wear...">${char.clothing || ''}</textarea>
                </div>
                <div class="character-field">
                    <label for="char-${index}-features"><strong>Features:</strong></label>
                    <textarea id="char-${index}-features" rows="2" placeholder="Distinctive features...">${char.distinctive_features || ''}</textarea>
                </div>
                <div class="character-field">
                    <label for="char-${index}-traits"><strong>Traits:</strong></label>
                    <textarea id="char-${index}-traits" rows="2" placeholder="Personality traits...">${char.personality_traits || ''}</textarea>
                </div>
                <button class="btn-text-save" onclick="saveCharacter(${index})">Save Character</button>
            `;
            charactersDiv.appendChild(charDiv);
        });
    } else {
        charactersDiv.innerHTML = '';
    }
}

// ===== Save Page Text =====
function savePageText(pageNumber) {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    const page = currentStory.pages.find(p => p.page_number === pageNumber);
    if (!page) {
        showError('Page not found');
        return;
    }

    const textArea = document.getElementById(`page-${pageNumber}-text`);
    const newText = textArea.value.trim();

    if (!newText) {
        showError('Page text cannot be empty');
        return;
    }

    // Update the page text in memory
    page.text = newText;

    // Show success feedback
    alert('Page text saved! Switch to the Image Generation tab to create images.');
}

// ===== Save Character =====
function saveCharacter(charIndex) {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    if (!currentStory.characters || !currentStory.characters[charIndex]) {
        showError('Character not found');
        return;
    }

    const character = currentStory.characters[charIndex];

    // Get values from input fields
    const species = document.getElementById(`char-${charIndex}-species`).value.trim();
    const description = document.getElementById(`char-${charIndex}-description`).value.trim();
    const clothing = document.getElementById(`char-${charIndex}-clothing`).value.trim();
    const features = document.getElementById(`char-${charIndex}-features`).value.trim();
    const traits = document.getElementById(`char-${charIndex}-traits`).value.trim();

    // Update the character in memory
    character.species = species;
    character.physical_description = description;
    character.clothing = clothing;
    character.distinctive_features = features;
    character.personality_traits = traits;

    // Show success feedback
    alert(`Character "${character.name}" saved! Changes will be used when generating images.`);
}

// ===== Generate Image Prompt =====
async function generateImagePrompt(pageNumber) {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    const page = currentStory.pages.find(p => p.page_number === pageNumber);
    if (!page) {
        showError('Page not found');
        return;
    }

    try {
        // Build the prompt using the character profiles, art bible, character references, and scene description
        const scene_description = page.text;
        const character_profiles = currentStory.characters || [];
        const art_style = currentStory.metadata.art_style || 'cartoon';
        const art_bible = currentStory.art_bible || null;
        const character_references = currentStory.character_references || null;

        // Call API to generate the prompt
        const response = await fetch(`${API_BASE}/prompts/image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scene_description: scene_description,
                character_profiles: character_profiles,
                art_style: art_style,
                art_bible: art_bible,
                character_references: character_references
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate prompt');
        }

        const result = await response.json();

        // Update the page with the generated prompt
        page.image_prompt = result.prompt;

        // Update the display
        const promptArea = document.getElementById(`page-${pageNumber}-prompt`);
        if (promptArea) {
            promptArea.value = result.prompt;
        }

    } catch (error) {
        showError(`Failed to generate prompt for page ${pageNumber}: ${error.message}`);
    }
}

// ===== Generate Page Image =====
async function generatePageImage(pageNumber) {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    const page = currentStory.pages.find(p => p.page_number === pageNumber);
    if (!page) {
        showError('Page not found');
        return;
    }

    // Get the edited prompt from the textarea (if user edited it)
    const promptTextarea = document.getElementById(`page-${pageNumber}-prompt`);
    const customPrompt = promptTextarea ? promptTextarea.value.trim() : '';

    // Get size and detail from global dropdowns
    const size = document.getElementById('page-image-size').value;
    const detail = document.getElementById('page-image-detail').value;

    // Show loading indicator
    const loadingDiv = document.getElementById(`page-${pageNumber}-loading`);
    loadingDiv.classList.remove('hidden');

    try {
        console.log(`[generatePageImage] Starting for page ${pageNumber}`);
        const requestData = {
            scene_description: page.text,
            character_profiles: currentStory.characters || [],
            art_style: currentStory.metadata.art_style || 'cartoon',
            story_title: currentStory.metadata.title || '',
            session_id: currentStory.image_session_id || null,
            art_bible: currentStory.art_bible || null,
            character_references: currentStory.character_references || null,
            size: size,
            quality: detail
        };

        // If user has edited the prompt, use it directly
        if (customPrompt) {
            requestData.custom_prompt = customPrompt;
            console.log(`[generatePageImage] Using custom prompt (length: ${customPrompt.length})`);
        }

        console.log(`[generatePageImage] Sending request to API...`);
        const response = await fetch(`${API_BASE}/images/stories/${currentStory.id}/pages/${pageNumber}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
        });

        console.log(`[generatePageImage] Response received, status: ${response.status}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate image');
        }

        console.log(`[generatePageImage] Parsing JSON response...`);
        const result = await response.json();
        console.log(`[generatePageImage] JSON parsed, local_image_path: ${result.local_image_path}`);

        // Store session ID for conversation continuity
        if (result.session_id) {
            currentStory.image_session_id = result.session_id;
            console.log(`[generatePageImage] Session ID updated: ${result.session_id}`);
        }

        // Update the page with the local image path (image is already saved by backend)
        page.local_image_path = result.local_image_path;
        console.log(`[generatePageImage] page.local_image_path updated`);

        // Also save the prompt that was used
        const promptTextareaForSave = document.getElementById(`page-${pageNumber}-prompt`);
        if (promptTextareaForSave) {
            page.image_prompt = promptTextareaForSave.value;
        }

        // Update the display using the local path
        const previewSection = document.getElementById(`page-${pageNumber}-image-preview`);
        console.log(`[generatePageImage] previewSection found: ${!!previewSection}`);
        if (previewSection) {
            previewSection.innerHTML = `
                <img src="${getImageUrl(result.local_image_path, null)}" alt="Page ${pageNumber} illustration" onerror="console.error('Image failed to load for page ${pageNumber}')">
                <div class="image-action-buttons">
                    <button class="btn-small btn-delete-image" onclick="deletePageImage(${pageNumber})">Delete Image</button>
                </div>
            `;
            console.log(`[generatePageImage] innerHTML updated`);
        }

        // Hide loading indicator
        loadingDiv.classList.add('hidden');
        console.log(`[generatePageImage] Loading hidden, auto-saving project...`);

        // Auto-save project to persist the changes
        await autoSaveProject();
        console.log(`[generatePageImage] Auto-save completed`);
    } catch (error) {
        console.error(`[generatePageImage] ERROR:`, error);
        loadingDiv.classList.add('hidden');
        showError(`Failed to generate image for page ${pageNumber}: ${error.message}`);
    }
}

// ===== Handle Save Project =====
async function handleSaveProject() {
    if (!currentStory) {
        showError('No story to save');
        return;
    }

    const projectData = {
        id: currentStory.id,
        name: currentStory.metadata.title,
        story: currentStory,
        status: 'completed',
        character_profiles: currentStory.characters || [],
        image_prompts: []
    };

    try {
        const response = await fetch(`${API_BASE}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(projectData),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save project');
        }

        alert('Project saved successfully!');
        await loadProjects();
    } catch (error) {
        showError('Failed to save project: ' + error.message);
    }
}

// ===== Handle New Story =====
function handleNewStory() {
    currentStory = null;
    storyDisplaySection.classList.add('hidden');
    noStoryPlaceholder.classList.remove('hidden');
    storyForm.reset();
    populateFormFields();
    switchTab('text-generation');
}

// ===== Load Projects =====
async function loadProjects() {
    try {
        const response = await fetch(`${API_BASE}/projects`);
        if (!response.ok) throw new Error('Failed to load projects');

        const projects = await response.json();
        displayProjects(projects);
    } catch (error) {
        showError('Failed to load projects: ' + error.message);
    }
}

// ===== Display Projects =====
function displayProjects(projects) {
    const projectsList = document.getElementById('projects-list');

    if (projects.length === 0) {
        projectsList.innerHTML = '<p class="no-projects-message">No saved projects yet. Go to the Text Generation tab to create your first story!</p>';
        return;
    }

    projectsList.innerHTML = '';
    projects.forEach(project => {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'project-item-compact';

        // Format creation date
        const createdDate = project.created_at ? new Date(project.created_at).toLocaleDateString() : 'Unknown';

        // Extract story details (now at root level from API)
        const numPages = project.num_pages || 'N/A';
        const language = project.language || 'N/A';
        const customPrompt = project.user_prompt || '';

        const detailsId = `project-details-${project.id}`;

        projectDiv.innerHTML = `
            <div class="project-row">
                <button class="project-expand-btn" aria-expanded="false" aria-controls="${detailsId}" title="Show details">
                    <span class="expand-arrow">&#9654;</span>
                </button>
                <h4 class="project-title">${project.title || 'Untitled'}</h4>
                <div class="project-actions-inline">
                    <button class="btn btn-primary btn-small btn-load-project" onclick="event.stopPropagation(); loadProject('${project.id}')">Load</button>
                    <button class="btn-delete btn-small" onclick="event.stopPropagation(); deleteProject('${project.id}')">Delete</button>
                </div>
            </div>
            <div id="${detailsId}" class="project-details-collapsible hidden">
                <div class="project-details-content">
                    <span class="project-detail"><strong>Pages:</strong> ${numPages}</span>
                    <span class="project-detail"><strong>Language:</strong> ${language}</span>
                    <span class="project-detail"><strong>Created:</strong> ${createdDate}</span>
                    ${customPrompt ? `<p class="project-custom-prompt"><strong>Story Idea:</strong> ${customPrompt.length > 200 ? customPrompt.substring(0, 200) + '...' : customPrompt}</p>` : ''}
                </div>
            </div>
        `;

        // Add toggle functionality for expand button
        const expandBtn = projectDiv.querySelector('.project-expand-btn');
        const detailsSection = projectDiv.querySelector('.project-details-collapsible');
        expandBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = expandBtn.getAttribute('aria-expanded') === 'true';
            expandBtn.setAttribute('aria-expanded', !isExpanded);
            expandBtn.classList.toggle('expanded', !isExpanded);
            detailsSection.classList.toggle('hidden', isExpanded);
        });

        projectsList.appendChild(projectDiv);
    });
}

// ===== Populate Form with Project Data =====
function populateFormWithProject(story) {
    if (!story || !story.metadata) return;

    const metadata = story.metadata;

    // Set form field values
    document.getElementById('title').value = metadata.title || '';
    document.getElementById('language').value = metadata.language || '';
    document.getElementById('age-group').value = metadata.age_group || '';
    document.getElementById('complexity').value = metadata.complexity || '';
    document.getElementById('vocabulary').value = metadata.vocabulary_diversity || '';
    document.getElementById('num-pages').value = metadata.num_pages || 5;
    document.getElementById('words-per-page').value = metadata.words_per_page || 50;
    document.getElementById('genre').value = metadata.genre || '';
    document.getElementById('art-style').value = metadata.art_style || '';
    document.getElementById('custom-prompt').value = metadata.user_prompt || '';
}

// ===== Load Project =====
async function loadProject(projectId) {
    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}`);
        if (!response.ok) throw new Error('Failed to load project');

        const project = await response.json();
        currentStory = project.story;

        // Don't reset visual consistency - we want to keep saved art_bible and character_references
        // Clear the image_session_id since the session is no longer valid
        // (sessions don't persist across server restarts)
        // When generating new images, the backend will automatically rebuild
        // the visual context using the saved art_bible and character prompts
        currentStory.image_session_id = null;

        // Populate form fields with project metadata
        populateFormWithProject(currentStory);

        displayStory(currentStory);
        switchTab('text-generation');

        console.log('Project loaded:', projectId);
        console.log('Art Bible:', currentStory.art_bible);
        console.log('Character References:', currentStory.character_references);

        // Show info message if visual assets exist
        if (currentStory.art_bible || (currentStory.character_references && currentStory.character_references.length > 0)) {
            console.log('Note: Visual context will be rebuilt when generating new images.');
        }
    } catch (error) {
        showError('Failed to load project: ' + error.message);
    }
}

// ===== Delete Project =====
async function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}`, {
            method: 'DELETE',
        });

        if (!response.ok && response.status !== 204) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete project');
        }

        await loadProjects();
    } catch (error) {
        showError('Failed to delete project: ' + error.message);
    }
}

// ===== UI Helper Functions =====
function showLoading() {
    loadingDiv.classList.remove('hidden');
    generateBtn.disabled = true;
}

function hideLoading() {
    loadingDiv.classList.add('hidden');
    generateBtn.disabled = false;
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    errorDiv.classList.add('hidden');
}

// ===== VISUAL CONSISTENCY TAB FUNCTIONS =====

function resetVisualConsistencyTab() {
    // Clear art bible data
    if (currentStory && currentStory.art_bible) {
        currentStory.art_bible = null;
    }

    // Clear character references
    if (currentStory && currentStory.character_references) {
        currentStory.character_references = [];
    }

    // Clear any displayed prompts and images in the UI
    const artBiblePrompt = document.getElementById('art-bible-prompt');
    const artBibleImagePreview = document.getElementById('art-bible-image-preview');
    if (artBiblePrompt) artBiblePrompt.value = '';
    if (artBibleImagePreview) artBibleImagePreview.innerHTML = '';
}

function updateVisualConsistencyTab() {
    const noStoryDiv = document.getElementById('visual-no-story');
    const contentDiv = document.getElementById('visual-content');

    if (!currentStory || !currentStory.characters || currentStory.characters.length === 0) {
        noStoryDiv.classList.remove('hidden');
        contentDiv.classList.add('hidden');
        return;
    }

    noStoryDiv.classList.add('hidden');
    contentDiv.classList.remove('hidden');

    // Update story info bar
    const infoBar = document.getElementById('visual-story-info');
    infoBar.innerHTML = `
        <h3>${currentStory.metadata.title}</h3>
        <p>Art Style: ${currentStory.metadata.art_style || 'cartoon'} &bull; ${currentStory.characters.length} character(s)</p>
    `;

    // Setup art bible section
    setupArtBibleSection();

    // Setup character references
    setupCharacterReferences();
}

function setupArtBibleSection() {
    // Display existing art bible if available
    if (currentStory.art_bible) {
        const artBible = currentStory.art_bible;

        // Show art bible section if there's a prompt OR an image
        if (artBible.prompt || artBible.local_image_path || artBible.image_url) {
            document.getElementById('art-bible-section').classList.remove('hidden');
        }

        // Populate the prompt if available
        if (artBible.prompt) {
            document.getElementById('art-bible-prompt').value = artBible.prompt;
        }

        // Display existing art bible image
        if (artBible.local_image_path || artBible.image_url) {
            const previewDiv = document.getElementById('art-bible-preview');
            previewDiv.classList.remove('hidden');
            previewDiv.innerHTML = `
                <img src="${getImageUrl(artBible.local_image_path, artBible.image_url)}" alt="Art Bible Reference">
                <div class="image-action-buttons">
                    <button class="btn-small btn-delete-image" onclick="deleteArtBibleImage()">Delete Image</button>
                </div>
                <p>Art Bible reference loaded.</p>
            `;
        }
    }

    // Setup event listeners for art bible
    const generatePromptBtn = document.getElementById('generate-art-bible-prompt-btn');
    const generateImageBtn = document.getElementById('generate-art-bible-image-btn');
    const uploadBtn = document.getElementById('upload-art-bible-btn');

    // Generate art bible prompt
    generatePromptBtn.onclick = async () => {
        try {
            const response = await fetch(`${API_BASE}/visual-consistency/art-bible/generate-prompt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    art_style: currentStory.metadata.art_style || 'cartoon',
                    genre: currentStory.metadata.genre,
                    story_title: currentStory.metadata.title
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate prompt');
            }

            const result = await response.json();

            // Show art bible section and populate prompt
            document.getElementById('art-bible-section').classList.remove('hidden');
            document.getElementById('art-bible-prompt').value = result.prompt;

            // Store art bible in story (create or update)
            if (!currentStory.art_bible) {
                currentStory.art_bible = {
                    prompt: result.prompt,
                    art_style: result.art_style
                };
            } else {
                currentStory.art_bible.prompt = result.prompt;
            }

            // Hide save button since prompt was just auto-saved
            document.getElementById('save-art-bible-prompt-btn').classList.add('hidden');

        } catch (error) {
            showError(`Failed to generate art bible prompt: ${error.message}`);
        }
    };

    // Art Bible prompt change listener - show Save button when user edits
    const artBiblePromptTextarea = document.getElementById('art-bible-prompt');
    const saveArtBiblePromptBtn = document.getElementById('save-art-bible-prompt-btn');

    artBiblePromptTextarea.addEventListener('input', () => {
        // Show save button when user makes changes
        saveArtBiblePromptBtn.classList.remove('hidden');
    });

    // Save Art Bible prompt
    saveArtBiblePromptBtn.onclick = () => {
        const prompt = artBiblePromptTextarea.value;
        if (!currentStory.art_bible) {
            currentStory.art_bible = { prompt: prompt };
        } else {
            currentStory.art_bible.prompt = prompt;
        }
        saveArtBiblePromptBtn.classList.add('hidden');
    };

    // Generate art bible image
    generateImageBtn.onclick = async () => {
        const prompt = document.getElementById('art-bible-prompt').value;
        if (!prompt) {
            showError('Please generate or enter an art bible prompt first');
            return;
        }

        // Get size and detail from dropdowns
        const size = document.getElementById('art-bible-size').value;
        const detail = document.getElementById('art-bible-detail').value;

        const loadingDiv = document.getElementById('art-bible-loading');
        loadingDiv.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE}/visual-consistency/art-bible/generate-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    art_style: currentStory.metadata.art_style || 'cartoon',
                    story_id: currentStory.id,
                    story_title: currentStory.metadata.title || '',
                    size: size,
                    quality: detail
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate image');
            }

            const result = await response.json();

            // Update art bible with local image path (image is already saved by backend)
            if (!currentStory.art_bible) {
                currentStory.art_bible = {};
            }
            currentStory.art_bible.local_image_path = result.local_image_path;
            currentStory.art_bible.prompt = prompt;

            // Store session ID for conversation continuity
            if (result.session_id) {
                currentStory.image_session_id = result.session_id;
            }

            // Display art bible image using the local path
            const previewDiv = document.getElementById('art-bible-preview');
            previewDiv.classList.remove('hidden');
            previewDiv.innerHTML = `
                <img src="${getImageUrl(result.local_image_path, null)}" alt="Art Bible Reference">
                <div class="image-action-buttons">
                    <button class="btn-small btn-delete-image" onclick="deleteArtBibleImage()">Delete Image</button>
                </div>
                <p>Art Bible generated and saved successfully! This will be used as a style reference for all story illustrations.</p>
            `;

            loadingDiv.classList.add('hidden');

            // Auto-save project to persist the changes
            await autoSaveProject();

        } catch (error) {
            loadingDiv.classList.add('hidden');
            showError(`Failed to generate art bible image: ${error.message}`);
        }
    };

    // Upload custom art bible (placeholder for now)
    uploadBtn.onclick = () => {
        alert('Image upload functionality coming soon! For now, please use the generated art bible.');
    };
}

function setupCharacterReferences() {
    const charactersList = document.getElementById('character-references-list');
    charactersList.innerHTML = '';

    if (!currentStory.characters || currentStory.characters.length === 0) {
        charactersList.innerHTML = '<p>No characters found in this story.</p>';
        return;
    }

    // Initialize character_references array if not present
    if (!currentStory.character_references) {
        currentStory.character_references = [];
    }

    currentStory.characters.forEach((character, index) => {
        const charCard = document.createElement('div');
        charCard.className = 'character-ref-card';
        charCard.id = `char-ref-${index}`;

        // Find existing reference for this character
        const existingRef = currentStory.character_references.find(
            ref => ref.character_name === character.name
        );

        // Show prompt section if there's an existing reference
        const showPromptSection = existingRef && (existingRef.prompt || existingRef.local_image_path || existingRef.image_url);

        charCard.innerHTML = `
            <h4>${character.name} (${character.species || 'Character'})</h4>

            <div class="character-ref-controls">
                <button class="btn-small" onclick="generateCharacterPrompt(${index})">
                    ${existingRef && existingRef.prompt ? 'Regenerate' : 'Generate'} Reference Prompt
                </button>
                <button class="btn-small" onclick="uploadCharacterRef(${index})">
                    Upload Custom Reference
                </button>
            </div>

            <div id="char-ref-prompt-${index}" class="character-ref-prompt ${showPromptSection ? '' : 'hidden'}">
                <label>Character Reference Prompt (editable):</label>
                <textarea id="char-prompt-${index}" class="prompt-textarea" rows="5">${existingRef && existingRef.prompt ? existingRef.prompt : ''}</textarea>
                <button id="save-char-prompt-${index}" class="btn-small btn-save-prompt hidden" onclick="saveCharacterPrompt(${index})">Save Prompt</button>
                <div class="image-options-row" style="margin-top: 10px;">
                    <div class="form-group-inline">
                        <label for="char-size-${index}">Size:</label>
                        <select id="char-size-${index}">
                            <option value="1024x1024">1024x1024 (Square)</option>
                            <option value="1536x1024" selected>1536x1024 (Landscape)</option>
                            <option value="1024x1536">1024x1536 (Portrait)</option>
                        </select>
                    </div>
                    <div class="form-group-inline">
                        <label for="char-detail-${index}">Detail:</label>
                        <select id="char-detail-${index}">
                            <option value="low" selected>Low</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                </div>
                <div class="image-actions" style="margin-top: 10px;">
                    <button class="btn-small" onclick="generateCharacterImage(${index})">
                        ${existingRef && (existingRef.local_image_path || existingRef.image_url) ? 'Regenerate' : 'Generate'} Reference Image
                    </button>
                </div>
            </div>

            <div class="image-loading hidden" id="char-loading-${index}">
                <div class="spinner-small"></div>
                <span>Generating character reference...</span>
            </div>

            <div id="char-preview-${index}" class="character-ref-preview ${existingRef && (existingRef.local_image_path || existingRef.image_url) ? '' : 'hidden'}">
                ${existingRef && (existingRef.local_image_path || existingRef.image_url) ? `
                    <img src="${getImageUrl(existingRef.local_image_path, existingRef.image_url)}" alt="${character.name} Reference">
                    <div class="image-action-buttons">
                        <button class="btn-small btn-delete-image" onclick="deleteCharacterImage(${index})">Delete Image</button>
                    </div>
                ` : ''}
            </div>
        `;

        charactersList.appendChild(charCard);

        // Add input listener to show Save button when user edits prompt
        const charPromptTextarea = document.getElementById(`char-prompt-${index}`);
        const saveCharPromptBtn = document.getElementById(`save-char-prompt-${index}`);
        if (charPromptTextarea && saveCharPromptBtn) {
            charPromptTextarea.addEventListener('input', () => {
                saveCharPromptBtn.classList.remove('hidden');
            });
        }
    });
}

// Save character prompt manually
function saveCharacterPrompt(charIndex) {
    const character = currentStory.characters[charIndex];
    const prompt = document.getElementById(`char-prompt-${charIndex}`).value;
    const saveBtn = document.getElementById(`save-char-prompt-${charIndex}`);

    if (!currentStory.character_references) {
        currentStory.character_references = [];
    }

    // Update or create character reference
    const existingIndex = currentStory.character_references.findIndex(
        ref => ref.character_name === character.name
    );

    if (existingIndex >= 0) {
        currentStory.character_references[existingIndex].prompt = prompt;
    } else {
        currentStory.character_references.push({
            character_name: character.name,
            prompt: prompt,
            species: character.species,
            physical_description: character.physical_description
        });
    }

    // Hide save button after saving
    saveBtn.classList.add('hidden');
}

async function generateCharacterPrompt(charIndex) {
    const character = currentStory.characters[charIndex];

    try {
        const response = await fetch(`${API_BASE}/visual-consistency/character-reference/generate-prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                character: {
                    name: character.name,
                    species: character.species,
                    physical_description: character.physical_description,
                    clothing: character.clothing,
                    distinctive_features: character.distinctive_features,
                    personality_traits: character.personality_traits
                },
                art_style: currentStory.metadata.art_style || 'cartoon',
                include_turnaround: true
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate prompt');
        }

        const result = await response.json();

        // Show prompt section and populate it
        document.getElementById(`char-ref-prompt-${charIndex}`).classList.remove('hidden');
        document.getElementById(`char-prompt-${charIndex}`).value = result.prompt;

        // Store in character_references
        if (!currentStory.character_references) {
            currentStory.character_references = [];
        }

        // Update or create character reference
        const existingIndex = currentStory.character_references.findIndex(
            ref => ref.character_name === character.name
        );

        if (existingIndex >= 0) {
            currentStory.character_references[existingIndex].prompt = result.prompt;
        } else {
            currentStory.character_references.push({
                character_name: character.name,
                prompt: result.prompt,
                species: character.species,
                physical_description: character.physical_description
            });
        }

        // Hide save button since prompt was just auto-saved
        const saveBtn = document.getElementById(`save-char-prompt-${charIndex}`);
        if (saveBtn) {
            saveBtn.classList.add('hidden');
        }

    } catch (error) {
        showError(`Failed to generate prompt for ${character.name}: ${error.message}`);
    }
}

async function generateCharacterImage(charIndex) {
    const character = currentStory.characters[charIndex];
    const prompt = document.getElementById(`char-prompt-${charIndex}`).value;

    if (!prompt) {
        showError('Please generate or enter a character reference prompt first');
        return;
    }

    // Get size and detail from dropdowns
    const size = document.getElementById(`char-size-${charIndex}`).value;
    const detail = document.getElementById(`char-detail-${charIndex}`).value;

    const loadingDiv = document.getElementById(`char-loading-${charIndex}`);
    loadingDiv.classList.remove('hidden');

    try {
        // Prepare request body - conversation session maintains art bible context
        const requestBody = {
            prompt: prompt,
            character_name: character.name,
            story_id: currentStory.id,
            include_turnaround: true,
            size: size,
            quality: detail
        };

        const response = await fetch(`${API_BASE}/visual-consistency/character-reference/generate-image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate image');
        }

        const result = await response.json();

        // Store session ID for conversation continuity
        if (result.session_id) {
            currentStory.image_session_id = result.session_id;
        }

        // Update character reference with local image path (image is already saved by backend)
        const existingIndex = currentStory.character_references.findIndex(
            ref => ref.character_name === character.name
        );

        if (existingIndex >= 0) {
            currentStory.character_references[existingIndex].local_image_path = result.local_image_path;
        } else {
            currentStory.character_references.push({
                character_name: character.name,
                prompt: prompt,
                local_image_path: result.local_image_path
            });
        }

        // Display character reference image using the local path
        const previewDiv = document.getElementById(`char-preview-${charIndex}`);
        previewDiv.classList.remove('hidden');
        previewDiv.innerHTML = `
            <img src="${getImageUrl(result.local_image_path, null)}" alt="${character.name} Reference">
            <div class="image-action-buttons">
                <button class="btn-small btn-delete-image" onclick="deleteCharacterImage(${charIndex})">Delete Image</button>
            </div>
            <p>Reference image for ${character.name} generated and saved successfully!</p>
        `;

        loadingDiv.classList.add('hidden');

        // Auto-save project to persist the changes
        await autoSaveProject();

    } catch (error) {
        loadingDiv.classList.add('hidden');
        showError(`Failed to generate image for ${character.name}: ${error.message}`);
    }
}

function uploadCharacterRef(charIndex) {
    alert('Image upload functionality coming soon! For now, please use the generated character references.');
}

// ===== Auto-save Project =====
async function autoSaveProject() {
    if (!currentStory) return;

    const projectData = {
        id: currentStory.id,
        name: currentStory.metadata.title,
        story: currentStory,
        status: 'completed',
        character_profiles: currentStory.characters || [],
        image_prompts: []
    };

    try {
        const response = await fetch(`${API_BASE}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(projectData),
        });

        if (!response.ok) {
            const error = await response.json();
            console.warn('Auto-save warning:', error.error);
        } else {
            console.log('Project auto-saved successfully');
        }
    } catch (error) {
        console.warn('Auto-save warning:', error.message);
    }
}

// ===== Save Image Functions =====
async function saveArtBibleImage() {
    if (!currentStory || !currentStory.art_bible || !currentStory.art_bible.image_url) {
        showError('No art bible image to save');
        return;
    }

    try {
        const filename = `art_bible_${Date.now()}.png`;

        const response = await fetch(`${API_BASE}/images/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: currentStory.art_bible.image_url,
                project_id: currentStory.id,
                image_type: 'art_bible',
                filename: filename
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save image');
        }

        const result = await response.json();

        // Update art bible with local path
        currentStory.art_bible.local_image_path = result.local_path;

        console.log('Art Bible image saved successfully to:', result.local_path);

        // Auto-save project to persist the image path
        await autoSaveProject();
    } catch (error) {
        showError(`Failed to save art bible image: ${error.message}`);
    }
}

async function saveCharacterImage(charIndex) {
    if (!currentStory || !currentStory.characters || !currentStory.characters[charIndex]) {
        showError('Character not found');
        return;
    }

    const character = currentStory.characters[charIndex];
    const charRef = currentStory.character_references.find(ref => ref.character_name === character.name);

    if (!charRef || !charRef.image_url) {
        showError('No character reference image to save');
        return;
    }

    try {
        const filename = `character_${character.name.replace(/\s+/g, '_')}_${Date.now()}.png`;

        const response = await fetch(`${API_BASE}/images/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: charRef.image_url,
                project_id: currentStory.id,
                image_type: 'character',
                filename: filename
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save image');
        }

        const result = await response.json();

        // Update character reference with local path
        charRef.local_image_path = result.local_path;

        console.log(`Character reference image for ${character.name} saved to:`, result.local_path);

        // Auto-save project to persist the image path
        await autoSaveProject();
    } catch (error) {
        showError(`Failed to save character image: ${error.message}`);
    }
}

async function savePageImage(pageNumber) {
    console.log(`[savePageImage] Starting for page ${pageNumber}`);
    if (!currentStory) {
        console.error(`[savePageImage] No story loaded`);
        showError('No story loaded');
        return;
    }

    const page = currentStory.pages.find(p => p.page_number === pageNumber);
    if (!page || !page.image_url) {
        console.error(`[savePageImage] No page image to save, page: ${!!page}, image_url: ${!!page?.image_url}`);
        showError('No page image to save');
        return;
    }

    console.log(`[savePageImage] Image URL length: ${page.image_url.length}`);

    try {
        const filename = `page_${pageNumber}_${Date.now()}.png`;
        console.log(`[savePageImage] Saving as: ${filename}`);

        const response = await fetch(`${API_BASE}/images/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: page.image_url,
                project_id: currentStory.id,
                image_type: 'page',
                filename: filename
            }),
        });

        console.log(`[savePageImage] Response status: ${response.status}`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save image');
        }

        const result = await response.json();
        console.log(`[savePageImage] Save successful, local_path: ${result.local_path}`);

        // Update page with local path
        page.local_image_path = result.local_path;

        // Also save the prompt that was used
        const promptTextarea = document.getElementById(`page-${pageNumber}-prompt`);
        if (promptTextarea) {
            page.image_prompt = promptTextarea.value;
        }

        console.log(`[savePageImage] Page ${pageNumber} image saved to:`, result.local_path);

        // Update the display to use local path
        const previewSection = document.getElementById(`page-${pageNumber}-image-preview`);
        if (previewSection && page.local_image_path) {
            console.log(`[savePageImage] Updating display with local path: ${page.local_image_path}`);
            const localImageUrl = getImageUrl(page.local_image_path, page.image_url);
            console.log(`[savePageImage] Local image URL: ${localImageUrl}`);
            previewSection.innerHTML = `
                <img src="${localImageUrl}" alt="Page ${pageNumber} illustration" onerror="console.error('Local image failed to load for page ${pageNumber}')">
                <div class="image-action-buttons">
                    <button class="btn-small save-image-btn" onclick="savePageImage(${pageNumber})">Save Image</button>
                    <button class="btn-small btn-delete-image" onclick="deletePageImage(${pageNumber})">Delete Image</button>
                </div>
            `;
        }

        // Auto-save project to persist the image path and prompt
        console.log(`[savePageImage] Starting autoSaveProject...`);
        await autoSaveProject();
        console.log(`[savePageImage] autoSaveProject completed`);
    } catch (error) {
        console.error(`[savePageImage] ERROR:`, error);
        showError(`Failed to save page image: ${error.message}`);
    }
}

// ===== DELETE IMAGE FUNCTIONS =====

async function deleteArtBibleImage() {
    if (!currentStory || !currentStory.art_bible) {
        showError('No art bible to delete');
        return;
    }

    if (!confirm('Are you sure you want to delete the art bible image?')) {
        return;
    }

    const artBible = currentStory.art_bible;
    const imagePath = artBible.local_image_path;

    try {
        // Delete the file from server if it's a saved local image
        if (imagePath) {
            const response = await fetch(`${API_BASE}/images/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_path: imagePath
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                console.warn('Failed to delete image file:', error.error);
            }
        }

        // Clear art bible image data
        currentStory.art_bible.image_url = null;
        currentStory.art_bible.local_image_path = null;

        // Update the display
        const previewDiv = document.getElementById('art-bible-preview');
        previewDiv.classList.add('hidden');
        previewDiv.innerHTML = '';

        console.log('Art bible image deleted');

        // Auto-save project
        await autoSaveProject();
    } catch (error) {
        showError(`Failed to delete art bible image: ${error.message}`);
    }
}

async function deleteCharacterImage(charIndex) {
    if (!currentStory || !currentStory.characters || !currentStory.characters[charIndex]) {
        showError('Character not found');
        return;
    }

    const character = currentStory.characters[charIndex];
    const charRef = currentStory.character_references?.find(ref => ref.character_name === character.name);

    if (!charRef) {
        showError('No character reference image to delete');
        return;
    }

    if (!confirm(`Are you sure you want to delete the reference image for ${character.name}?`)) {
        return;
    }

    const imagePath = charRef.local_image_path;

    try {
        // Delete the file from server if it's a saved local image
        if (imagePath) {
            const response = await fetch(`${API_BASE}/images/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_path: imagePath
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                console.warn('Failed to delete image file:', error.error);
            }
        }

        // Clear character reference image data
        charRef.image_url = null;
        charRef.local_image_path = null;

        // Update the display
        const previewDiv = document.getElementById(`char-preview-${charIndex}`);
        previewDiv.classList.add('hidden');
        previewDiv.innerHTML = '';

        console.log(`Character image for ${character.name} deleted`);

        // Auto-save project
        await autoSaveProject();
    } catch (error) {
        showError(`Failed to delete character image: ${error.message}`);
    }
}

async function deletePageImage(pageNumber) {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    const page = currentStory.pages.find(p => p.page_number === pageNumber);
    if (!page) {
        showError('Page not found');
        return;
    }

    if (!confirm(`Are you sure you want to delete the image for page ${pageNumber}?`)) {
        return;
    }

    const imagePath = page.local_image_path;

    try {
        // Delete the file from server if it's a saved local image
        if (imagePath) {
            const response = await fetch(`${API_BASE}/images/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_path: imagePath
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                console.warn('Failed to delete image file:', error.error);
            }
        }

        // Clear page image data
        page.image_url = null;
        page.local_image_path = null;

        // Update the display
        const previewSection = document.getElementById(`page-${pageNumber}-image-preview`);
        if (previewSection) {
            previewSection.innerHTML = '<div class="image-placeholder">No image generated yet</div>';
        }

        console.log(`Page ${pageNumber} image deleted`);

        // Auto-save project
        await autoSaveProject();
    } catch (error) {
        showError(`Failed to delete page image: ${error.message}`);
    }
}

// ===== PDF EXPORT TAB FUNCTIONS =====

function updatePDFTab() {
    const noStoryDiv = document.getElementById('pdf-no-story');
    const contentDiv = document.getElementById('pdf-content');

    if (!currentStory || !currentStory.pages || currentStory.pages.length === 0) {
        noStoryDiv.classList.remove('hidden');
        contentDiv.classList.add('hidden');
        return;
    }

    noStoryDiv.classList.add('hidden');
    contentDiv.classList.remove('hidden');

    // Update story info bar
    const infoBar = document.getElementById('pdf-story-info');
    infoBar.innerHTML = `
        <h3>${currentStory.metadata.title}</h3>
        <p>${currentStory.pages.length} pages &bull; ${currentStory.metadata.art_style || 'cartoon'} style</p>
    `;

    // Load PDF options from story if available
    if (currentStory.pdf_options) {
        const opts = currentStory.pdf_options;
        document.getElementById('pdf-mode').value = opts.pdf_mode || 'text-next-to-image';
        document.getElementById('pdf-font').value = opts.font || 'Helvetica';
        document.getElementById('pdf-font-size').value = opts.font_size || 12;
        document.getElementById('pdf-font-color').value = opts.font_color || 'black';
        document.getElementById('pdf-layout').value = opts.layout || 'portrait';
        document.getElementById('pdf-page-size').value = opts.page_size || 'letter';
        document.getElementById('pdf-image-placement').value = opts.image_placement || 'top';
        document.getElementById('pdf-image-size').value = opts.image_size || 'medium';
        document.getElementById('pdf-text-placement').value = opts.text_placement || 'top-left';
        document.getElementById('pdf-include-title').checked = opts.include_title_page !== false;
        document.getElementById('pdf-page-numbers').checked = opts.show_page_numbers !== false;
    }

    // Hide download section initially
    document.getElementById('pdf-download-section').classList.add('hidden');

    // Setup event listeners for PDF buttons
    setupPDFEventListeners();
}

function setupPDFEventListeners() {
    const saveBtn = document.getElementById('save-pdf-options-btn');
    const generateBtn = document.getElementById('generate-pdf-btn');

    // Remove existing listeners by replacing elements
    const newSaveBtn = saveBtn.cloneNode(true);
    const newGenerateBtn = generateBtn.cloneNode(true);
    saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
    generateBtn.parentNode.replaceChild(newGenerateBtn, generateBtn);

    newSaveBtn.addEventListener('click', savePDFOptions);
    newGenerateBtn.addEventListener('click', generatePDF);

    // Setup PDF mode toggle
    const pdfModeSelect = document.getElementById('pdf-mode');
    if (pdfModeSelect) {
        pdfModeSelect.addEventListener('change', togglePDFMode);
        // Initialize visibility based on current mode
        togglePDFMode();
    }
}

function togglePDFMode() {
    const pdfMode = document.getElementById('pdf-mode').value;
    const textNextToImageOptions = document.querySelectorAll('.pdf-text-next-to-image-option');
    const textOverImageOptions = document.querySelectorAll('.pdf-text-over-image-option');

    if (pdfMode === 'text-over-image') {
        // Hide and disable "text next to image" options
        textNextToImageOptions.forEach(option => {
            option.style.display = 'none';
            const select = option.querySelector('select');
            if (select) select.disabled = true;
        });

        // Show "text over image" options
        textOverImageOptions.forEach(option => {
            option.style.display = '';
            const select = option.querySelector('select');
            if (select) select.disabled = false;
        });
    } else {
        // Show and enable "text next to image" options
        textNextToImageOptions.forEach(option => {
            option.style.display = '';
            const select = option.querySelector('select');
            if (select) select.disabled = false;
        });

        // Hide "text over image" options
        textOverImageOptions.forEach(option => {
            option.style.display = 'none';
            const select = option.querySelector('select');
            if (select) select.disabled = true;
        });
    }
}

function getPDFOptionsFromForm() {
    const pdfMode = document.getElementById('pdf-mode').value;

    const options = {
        pdf_mode: pdfMode,
        font: document.getElementById('pdf-font').value,
        font_size: parseInt(document.getElementById('pdf-font-size').value),
        font_color: document.getElementById('pdf-font-color').value,
        include_title_page: document.getElementById('pdf-include-title').checked,
        show_page_numbers: document.getElementById('pdf-page-numbers').checked
    };

    // Add mode-specific options
    if (pdfMode === 'text-next-to-image') {
        options.layout = document.getElementById('pdf-layout').value;
        options.page_size = document.getElementById('pdf-page-size').value;
        options.image_placement = document.getElementById('pdf-image-placement').value;
        options.image_size = document.getElementById('pdf-image-size').value;
    } else {
        // text-over-image mode
        options.text_placement = document.getElementById('pdf-text-placement').value;
        // Set defaults for disabled fields to avoid backend errors
        options.layout = 'portrait';
        options.page_size = 'letter';
        options.image_placement = 'background';
        options.image_size = 'full';
    }

    return options;
}

async function savePDFOptions() {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    // Get options from form
    currentStory.pdf_options = getPDFOptionsFromForm();

    console.log('PDF options saved:', currentStory.pdf_options);

    // Auto-save project
    await autoSaveProject();

    alert('PDF options saved successfully!');
}

async function generatePDF() {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    // Get PDF options from form
    const pdfOptions = getPDFOptionsFromForm();

    // Show loading
    const loadingDiv = document.getElementById('pdf-loading');
    loadingDiv.classList.remove('hidden');

    // Hide download section while generating
    document.getElementById('pdf-download-section').classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/projects/${currentStory.id}/pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(pdfOptions),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to generate PDF');
        }

        const result = await response.json();

        // Show download section
        const downloadSection = document.getElementById('pdf-download-section');
        downloadSection.classList.remove('hidden');

        const downloadLink = document.getElementById('pdf-download-link');
        downloadLink.href = result.pdf_url;
        downloadLink.download = result.filename || 'story.pdf';

        // Also save PDF options
        currentStory.pdf_options = pdfOptions;
        await autoSaveProject();

        console.log('PDF generated:', result.pdf_url);
    } catch (error) {
        showError(`Failed to generate PDF: ${error.message}`);
    } finally {
        loadingDiv.classList.add('hidden');
    }
}
