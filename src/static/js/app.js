// ===== Global State =====
let currentStory = null;
let currentConfig = null;
let currentTab = 'text-generation';

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
const generateBtn = document.getElementById('generate-btn');
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
                               <button class="btn-small save-image-btn" onclick="savePageImage(${page.page_number})">Save Image</button>`
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
                        <label for="page-${page.page_number}-prompt">Image Prompt:</label>
                        <textarea class="page-prompt-edit" id="page-${page.page_number}-prompt" rows="3" readonly>${page.image_prompt || ''}</textarea>
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

    // Display characters
    const charactersDiv = document.getElementById('story-characters');
    if (story.characters && story.characters.length > 0) {
        charactersDiv.innerHTML = '<h3>Characters</h3>';
        story.characters.forEach(char => {
            const charDiv = document.createElement('div');
            charDiv.className = 'character-card';
            charDiv.innerHTML = `
                <h4>${char.name}</h4>
                <p><strong>Species:</strong> ${char.species || 'N/A'}</p>
                <p><strong>Description:</strong> ${char.physical_description || 'N/A'}</p>
                ${char.clothing ? `<p><strong>Clothing:</strong> ${char.clothing}</p>` : ''}
                ${char.distinctive_features ? `<p><strong>Features:</strong> ${char.distinctive_features}</p>` : ''}
                ${char.personality_traits ? `<p><strong>Traits:</strong> ${char.personality_traits}</p>` : ''}
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

    // Show loading indicator
    const loadingDiv = document.getElementById(`page-${pageNumber}-loading`);
    loadingDiv.classList.remove('hidden');

    try {
        const requestData = {
            scene_description: page.text,
            character_profiles: currentStory.characters || [],
            art_style: currentStory.metadata.art_style || 'cartoon',
            story_title: currentStory.metadata.title || '',
            session_id: currentStory.image_session_id || null,
            art_bible: currentStory.art_bible || null,
            character_references: currentStory.character_references || null
        };

        const response = await fetch(`${API_BASE}/images/stories/${currentStory.id}/pages/${pageNumber}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
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

        // Update the page with the image URL
        page.image_url = result.image_url;

        // Update the display
        const previewSection = document.getElementById(`page-${pageNumber}-image-preview`);
        if (previewSection) {
            previewSection.innerHTML = `
                <img src="${result.image_url}" alt="Page ${pageNumber} illustration">
                <button class="btn-small save-image-btn" onclick="savePageImage(${pageNumber})">Save Image</button>
            `;
        }

        // Hide loading indicator
        loadingDiv.classList.add('hidden');

        // Auto-save the image immediately (OpenAI URLs expire quickly)
        await savePageImage(pageNumber);
    } catch (error) {
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
        projectsList.innerHTML = '<p>No saved projects yet.</p>';
        return;
    }

    projectsList.innerHTML = '';
    projects.forEach(project => {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'project-item';

        // Format creation date
        const createdDate = project.created_at ? new Date(project.created_at).toLocaleDateString() : 'Unknown';

        projectDiv.innerHTML = `
            <div class="project-info">
                <h4>${project.title || 'Untitled'}</h4>
                <p class="project-date">Created: ${createdDate}</p>
            </div>
            <div class="project-actions">
                <button class="btn-delete" onclick="deleteProject('${project.id}')">Delete</button>
            </div>
        `;
        projectDiv.onclick = (e) => {
            if (!e.target.classList.contains('btn-delete')) {
                loadProject(project.id);
            }
        };
        projectsList.appendChild(projectDiv);
    });
}

// ===== Load Project =====
async function loadProject(projectId) {
    try {
        const response = await fetch(`${API_BASE}/projects/${projectId}`);
        if (!response.ok) throw new Error('Failed to load project');

        const project = await response.json();
        currentStory = project.story;

        // Reset Visual Consistency tab for loaded project
        resetVisualConsistencyTab();

        displayStory(currentStory);
        switchTab('text-generation');
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

        // Show art bible section if there's a prompt
        if (artBible.prompt) {
            document.getElementById('art-bible-section').classList.remove('hidden');
            document.getElementById('art-bible-prompt').value = artBible.prompt;
        }

        // Display existing art bible image
        if (artBible.local_image_path || artBible.image_url) {
            const previewDiv = document.getElementById('art-bible-preview');
            previewDiv.classList.remove('hidden');
            previewDiv.innerHTML = `
                <img src="${getImageUrl(artBible.local_image_path, artBible.image_url)}" alt="Art Bible Reference">
                <button class="btn-small save-image-btn" onclick="saveArtBibleImage()">Save Image</button>
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

            // Store art bible in story if not present
            if (!currentStory.art_bible) {
                currentStory.art_bible = {
                    prompt: result.prompt,
                    art_style: result.art_style
                };
            }

        } catch (error) {
            showError(`Failed to generate art bible prompt: ${error.message}`);
        }
    };

    // Generate art bible image
    generateImageBtn.onclick = async () => {
        const prompt = document.getElementById('art-bible-prompt').value;
        if (!prompt) {
            showError('Please generate or enter an art bible prompt first');
            return;
        }

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
                    story_title: currentStory.metadata.title || ''
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate image');
            }

            const result = await response.json();

            // Update art bible with image URL
            if (!currentStory.art_bible) {
                currentStory.art_bible = {};
            }
            currentStory.art_bible.image_url = result.image_url;
            currentStory.art_bible.prompt = prompt;

            // Store session ID for conversation continuity
            if (result.session_id) {
                currentStory.image_session_id = result.session_id;
            }

            // Display art bible image
            const previewDiv = document.getElementById('art-bible-preview');
            previewDiv.classList.remove('hidden');
            previewDiv.innerHTML = `
                <img src="${result.image_url}" alt="Art Bible Reference">
                <button class="btn-small save-image-btn" onclick="saveArtBibleImage()">Save Image</button>
                <p>Art Bible generated successfully! This will be used as a style reference for all story illustrations.</p>
            `;

            loadingDiv.classList.add('hidden');

            // Auto-save the image immediately (OpenAI URLs expire quickly)
            await saveArtBibleImage();

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

        charCard.innerHTML = `
            <h4>${character.name} (${character.species || 'Character'})</h4>

            <div class="character-ref-controls">
                <button class="btn-small" onclick="generateCharacterPrompt(${index})">
                    Generate Reference Prompt
                </button>
                <button class="btn-small" onclick="uploadCharacterRef(${index})">
                    Upload Custom Reference
                </button>
            </div>

            <div id="char-ref-prompt-${index}" class="character-ref-prompt hidden">
                <label>Character Reference Prompt (editable):</label>
                <textarea id="char-prompt-${index}" class="prompt-textarea" rows="5">${existingRef ? existingRef.prompt : ''}</textarea>
                <div class="image-actions" style="margin-top: 10px;">
                    <button class="btn-small" onclick="generateCharacterImage(${index})">
                        Generate Reference Image
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
                    <button class="btn-small save-image-btn" onclick="saveCharacterImage(${index})">Save Image</button>
                ` : ''}
            </div>
        `;

        charactersList.appendChild(charCard);
    });
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

    const loadingDiv = document.getElementById(`char-loading-${charIndex}`);
    loadingDiv.classList.remove('hidden');

    try {
        // Prepare request body - conversation session maintains art bible context
        const requestBody = {
            prompt: prompt,
            character_name: character.name,
            story_id: currentStory.id,
            include_turnaround: true
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

        // Update character reference with image URL
        const existingIndex = currentStory.character_references.findIndex(
            ref => ref.character_name === character.name
        );

        if (existingIndex >= 0) {
            currentStory.character_references[existingIndex].image_url = result.image_url;
        } else {
            currentStory.character_references.push({
                character_name: character.name,
                prompt: prompt,
                image_url: result.image_url
            });
        }

        // Display character reference image
        const previewDiv = document.getElementById(`char-preview-${charIndex}`);
        previewDiv.classList.remove('hidden');
        previewDiv.innerHTML = `
            <img src="${result.image_url}" alt="${character.name} Reference">
            <button class="btn-small save-image-btn" onclick="saveCharacterImage(${charIndex})">Save Image</button>
            <p>Reference image for ${character.name} generated successfully!</p>
        `;

        loadingDiv.classList.add('hidden');

        // Auto-save the image immediately (OpenAI URLs expire quickly)
        await saveCharacterImage(charIndex);

    } catch (error) {
        loadingDiv.classList.add('hidden');
        showError(`Failed to generate image for ${character.name}: ${error.message}`);
    }
}

function uploadCharacterRef(charIndex) {
    alert('Image upload functionality coming soon! For now, please use the generated character references.');
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
    } catch (error) {
        showError(`Failed to save character image: ${error.message}`);
    }
}

async function savePageImage(pageNumber) {
    if (!currentStory) {
        showError('No story loaded');
        return;
    }

    const page = currentStory.pages.find(p => p.page_number === pageNumber);
    if (!page || !page.image_url) {
        showError('No page image to save');
        return;
    }

    try {
        const filename = `page_${pageNumber}_${Date.now()}.png`;

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

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save image');
        }

        const result = await response.json();

        // Update page with local path
        page.local_image_path = result.local_path;

        console.log(`Page ${pageNumber} image saved to:`, result.local_path);
    } catch (error) {
        showError(`Failed to save page image: ${error.message}`);
    }
}
