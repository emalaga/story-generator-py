// ===== Global State =====
let currentStory = null;
let currentConfig = null;
let currentTab = 'text-generation';

// ===== API Base URL =====
const API_BASE = '/api';

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

    // Update image generation tab if story exists
    if (tabName === 'image-generation') {
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
                        ${page.image_url
                            ? `<img src="${page.image_url}" alt="Page ${page.page_number} illustration">`
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
                            ${page.image_url ? 'Regenerate' : 'Generate'} Image
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
    populateSelect('num-pages', parameters.page_counts, defaults.num_pages);
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
        // Build the prompt using the character profiles and scene description
        const scene_description = page.text;
        const character_profiles = currentStory.characters || [];
        const art_style = currentStory.metadata.art_style || 'cartoon';

        // Call API to generate the prompt
        const response = await fetch(`${API_BASE}/prompts/image`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scene_description: scene_description,
                character_profiles: character_profiles,
                art_style: art_style
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
            art_style: currentStory.metadata.art_style || 'cartoon'
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

        // Update the page with the image URL
        page.image_url = result.image_url;

        // Update the display
        const previewSection = document.getElementById(`page-${pageNumber}-image-preview`);
        if (previewSection) {
            previewSection.innerHTML = `<img src="${result.image_url}" alt="Page ${pageNumber} illustration">`;
        }

        // Hide loading indicator
        loadingDiv.classList.add('hidden');
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

        const projectIds = await response.json();
        displayProjects(projectIds);
    } catch (error) {
        showError('Failed to load projects: ' + error.message);
    }
}

// ===== Display Projects =====
function displayProjects(projectIds) {
    const projectsList = document.getElementById('projects-list');

    if (projectIds.length === 0) {
        projectsList.innerHTML = '<p>No saved projects yet.</p>';
        return;
    }

    projectsList.innerHTML = '';
    projectIds.forEach(id => {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'project-item';
        projectDiv.innerHTML = `
            <div class="project-info">
                <h4>Project: ${id}</h4>
                <p>Click to load</p>
            </div>
            <div class="project-actions">
                <button class="btn-delete" onclick="deleteProject('${id}')">Delete</button>
            </div>
        `;
        projectDiv.onclick = (e) => {
            if (!e.target.classList.contains('btn-delete')) {
                loadProject(id);
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
