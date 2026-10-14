/**
    ui/js/views/projects.js — Projects Management View & Interactive Creation Wizard
 */

import { store } from '../store.js';
import { api } from '../api.js';

let wizardState = {
    name: '',
    concept: '',
    universe_id: '',
    genre: '',
    tone: '',
    protagonist: '',
    conflict: '',
    world_setting: ''
};

let activeStep = 1;
let aiSuggestionsModal = {
    fieldKey: null,
    suggestions: [],
    loading: false
};

export function renderProjects(container) {
    const state = store.state;

    container.innerHTML = `
        <div class="grid-2">
            <!-- Interactive Project Creation Wizard Card -->
            <div class="card" style="grid-column: 1 / -1;">
                <div class="card-title">
                    <span>✨ Interactive Project Creation Wizard</span>
                    <span style="font-size: 0.9rem; color: var(--text-muted); font-family: var(--font-mono);">Step ${activeStep} of 5</span>
                </div>
                <p style="color: var(--text-muted); margin-bottom: 1.5rem;">
                    Design your novel step-by-step using accordion sections, contextual examples, free-choice inputs, and AI-powered inspiration.
                </p>

                <!-- Wizard Progress / Step Tabs -->
                <div style="display: flex; gap: 0.5rem; margin-bottom: 2rem; flex-wrap: wrap;">
                    <button class="btn btn-sm ${activeStep === 1 ? 'btn-primary' : ''}" data-wizard-step="1">1. Concept</button>
                    <button class="btn btn-sm ${activeStep === 2 ? 'btn-primary' : ''}" data-wizard-step="2">2. Genre & Tone</button>
                    <button class="btn btn-sm ${activeStep === 3 ? 'btn-primary' : ''}" data-wizard-step="3">3. Characters</button>
                    <button class="btn btn-sm ${activeStep === 4 ? 'btn-primary' : ''}" data-wizard-step="4">4. World Lore</button>
                    <button class="btn btn-sm ${activeStep === 5 ? 'btn-primary' : ''}" data-wizard-step="5">5. Summary & Create</button>
                </div>

                <form id="wizard-form">
                    <!-- Step 1: Concept & Title -->
                    <div class="wizard-step-panel" data-step="1" style="display: ${activeStep === 1 ? 'block' : 'none'};">
                        <h3 style="color: var(--accent); margin-bottom: 1rem; font-family: var(--font-display);">Step 1: Project Title & Core Premise</h3>
                        
                        <div class="form-group">
                            <label class="form-label" for="wiz-name">Project Title</label>
                            <input type="text" id="wiz-name" class="form-control" required placeholder="e.g. The Clockwork Empire" value="${escapeAttr(wizardState.name)}">
                            <small style="color: var(--text-muted);">Example: <em>Chronicles of the Astral Vault</em></small>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="wiz-concept">
                                Core Concept / Premise
                                <button type="button" class="btn btn-sm" style="float: right; padding: 0.1rem 0.5rem; font-size: 0.8rem;" data-ai-suggest="concept">✨ Generate 4 AI Choices</button>
                            </label>
                            <textarea id="wiz-concept" class="form-control" required placeholder="A brief description of the story's core hook...">${escapeHtml(wizardState.concept)}</textarea>
                            <small style="color: var(--text-muted);">Example: <em>A clockwork artisan discovers an illegal cog that controls human memories.</em></small>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="wiz-universe">Shared Universe (Optional)</label>
                            <select id="wiz-universe" class="form-control">
                                <option value="">-- None (Standalone Project) --</option>
                                ${state.universes.map(u => `<option value="${u.id}" ${wizardState.universe_id === u.id ? 'selected' : ''}>${escapeHtml(u.name)}</option>`).join('')}
                            </select>
                        </div>

                        <div style="display: flex; justify-content: flex-end; margin-top: 1.5rem;">
                            <button type="button" class="btn btn-primary" data-action="next-step">Next: Genre & Tone &rarr;</button>
                        </div>
                    </div>

                    <!-- Step 2: Genre & Tone -->
                    <div class="wizard-step-panel" data-step="2" style="display: ${activeStep === 2 ? 'block' : 'none'};">
                        <h3 style="color: var(--accent); margin-bottom: 1rem; font-family: var(--font-display);">Step 2: Genre & Atmospheric Tone</h3>

                        <div class="form-group">
                            <label class="form-label" for="wiz-genre">
                                Literary Genre
                                <button type="button" class="btn btn-sm" style="float: right; padding: 0.1rem 0.5rem; font-size: 0.8rem;" data-ai-suggest="genre">✨ Generate 4 AI Choices</button>
                            </label>
                            <input type="text" id="wiz-genre" class="form-control" required placeholder="e.g. Cyberpunk / Tech Noir" value="${escapeAttr(wizardState.genre)}">
                            <small style="color: var(--text-muted);">Example: <em>Epic High Fantasy, Hard Sci-Fi, Gothic Mystery</em></small>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="wiz-tone">
                                Narrative Tone
                                <button type="button" class="btn btn-sm" style="float: right; padding: 0.1rem 0.5rem; font-size: 0.8rem;" data-ai-suggest="tone">✨ Generate 4 AI Choices</button>
                            </label>
                            <input type="text" id="wiz-tone" class="form-control" required placeholder="e.g. Dark, Gritty & Atmospheric" value="${escapeAttr(wizardState.tone)}">
                            <small style="color: var(--text-muted);">Example: <em>Witty & Adventurous, Melancholic & Philosophical</em></small>
                        </div>

                        <div style="display: flex; justify-content: space-between; margin-top: 1.5rem;">
                            <button type="button" class="btn" data-action="prev-step">&larr; Back</button>
                            <button type="button" class="btn btn-primary" data-action="next-step">Next: Characters &rarr;</button>
                        </div>
                    </div>

                    <!-- Step 3: Characters & Protagonist -->
                    <div class="wizard-step-panel" data-step="3" style="display: ${activeStep === 3 ? 'block' : 'none'};">
                        <h3 style="color: var(--accent); margin-bottom: 1rem; font-family: var(--font-display);">Step 3: Protagonist & Central Conflict</h3>

                        <div class="form-group">
                            <label class="form-label" for="wiz-protagonist">
                                Protagonist Profile
                                <button type="button" class="btn btn-sm" style="float: right; padding: 0.1rem 0.5rem; font-size: 0.8rem;" data-ai-suggest="protagonist">✨ Generate 4 AI Choices</button>
                            </label>
                            <textarea id="wiz-protagonist" class="form-control" required placeholder="Describe your main character...">${escapeHtml(wizardState.protagonist)}</textarea>
                            <small style="color: var(--text-muted);">Example: <em>A cynical archival clerk with a hidden robotic arm and a penchant for forbidden lore.</em></small>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="wiz-conflict">
                                Central Conflict & Stakes
                                <button type="button" class="btn btn-sm" style="float: right; padding: 0.1rem 0.5rem; font-size: 0.8rem;" data-ai-suggest="conflict">✨ Generate 4 AI Choices</button>
                            </label>
                            <textarea id="wiz-conflict" class="form-control" required placeholder="What is at stake in this story?">${escapeHtml(wizardState.conflict)}</textarea>
                            <small style="color: var(--text-muted);">Example: <em>Stopping a cascading collapse of the planetary power grid before midnight.</em></small>
                        </div>

                        <div style="display: flex; justify-content: space-between; margin-top: 1.5rem;">
                            <button type="button" class="btn" data-action="prev-step">&larr; Back</button>
                            <button type="button" class="btn btn-primary" data-action="next-step">Next: World Lore &rarr;</button>
                        </div>
                    </div>

                    <!-- Step 4: World Lore & Setting -->
                    <div class="wizard-step-panel" data-step="4" style="display: ${activeStep === 4 ? 'block' : 'none'};">
                        <h3 style="color: var(--accent); margin-bottom: 1rem; font-family: var(--font-display);">Step 4: World Lore & Setting</h3>

                        <div class="form-group">
                            <label class="form-label" for="wiz-world">
                                World Setting / Environment
                                <button type="button" class="btn btn-sm" style="float: right; padding: 0.1rem 0.5rem; font-size: 0.8rem;" data-ai-suggest="world_setting">✨ Generate 4 AI Choices</button>
                            </label>
                            <textarea id="wiz-world" class="form-control" required placeholder="Describe the physical or societal setting...">${escapeHtml(wizardState.world_setting)}</textarea>
                            <small style="color: var(--text-muted);">Example: <em>A multi-tiered vertical city built inside a colossal hollow mountain.</em></small>
                        </div>

                        <div style="display: flex; justify-content: space-between; margin-top: 1.5rem;">
                            <button type="button" class="btn" data-action="prev-step">&larr; Back</button>
                            <button type="button" class="btn btn-primary" data-action="next-step">Review Summary &rarr;</button>
                        </div>
                    </div>

                    <!-- Step 5: Summary & Review -->
                    <div class="wizard-step-panel" data-step="5" style="display: ${activeStep === 5 ? 'block' : 'none'};">
                        <h3 style="color: var(--accent); margin-bottom: 1rem; font-family: var(--font-display);">Step 5: Final Review & Lore Generation</h3>
                        <p style="color: var(--text-muted); margin-bottom: 1.5rem;">
                            Review your project parameters below. Upon confirmation, Autonovel will automatically generate <code>seed.txt</code>, <code>world.md</code>, <code>characters.md</code>, <code>canon.md</code>, <code>outline.md</code>, and <code>state.json</code>.
                        </p>

                        <div style="background: var(--bg-primary); border: 1px solid var(--border-color); padding: 1.25rem; border-radius: 4px; margin-bottom: 1.5rem;">
                            <p><strong>Title:</strong> <span id="review-name">${escapeHtml(wizardState.name || '(Not specified)')}</span></p>
                            <p><strong>Concept:</strong> <span id="review-concept">${escapeHtml(wizardState.concept || '(Not specified)')}</span></p>
                            <p><strong>Genre:</strong> <span id="review-genre">${escapeHtml(wizardState.genre || '(Not specified)')}</span></p>
                            <p><strong>Tone:</strong> <span id="review-tone">${escapeHtml(wizardState.tone || '(Not specified)')}</span></p>
                            <p><strong>Protagonist:</strong> <span id="review-protagonist">${escapeHtml(wizardState.protagonist || '(Not specified)')}</span></p>
                            <p><strong>Conflict:</strong> <span id="review-conflict">${escapeHtml(wizardState.conflict || '(Not specified)')}</span></p>
                            <p><strong>World Setting:</strong> <span id="review-world">${escapeHtml(wizardState.world_setting || '(Not specified)')}</span></p>
                            <p><strong>Universe ID:</strong> <span id="review-universe">${escapeHtml(wizardState.universe_id || 'Standalone')}</span></p>
                        </div>

                        <div style="display: flex; justify-content: space-between; margin-top: 1.5rem;">
                            <button type="button" class="btn" data-action="prev-step">&larr; Back</button>
                            <button type="submit" class="btn btn-primary" style="background: var(--success); border-color: var(--success);">✨ Create Project & Generate Files</button>
                        </div>
                    </div>
                </form>
            </div>

            <!-- Active Project Selector Card -->
            <div class="card">
                <div class="card-title">Active Project Selector</div>
                <p style="color: var(--text-muted); margin-bottom: 1.5rem;">
                    Select which project is currently active across the dashboard, pipeline, and versioning views.
                </p>
                <div class="form-group">
                    <label class="form-label" for="active-project-select">Active Project</label>
                    <select id="active-project-select" class="form-control">
                        <option value="">-- Select Project --</option>
                        ${state.projects.map(p => `<option value="${p.id}" ${p.id === state.activeProjectId ? 'selected' : ''}>${escapeHtml(p.name)} (${p.id})</option>`).join('')}
                    </select>
                </div>
            </div>
        </div>

        <!-- AI Suggestions Modal / Drawer Overlay if active -->
        ${aiSuggestionsModal.fieldKey ? `
            <div id="ai-modal-overlay" style="position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 2000; display: flex; align-items: center; justify-content: center; padding: 1rem;">
                <div class="card" style="max-width: 600px; width: 100%; border: 2px solid var(--accent); position: relative;">
                    <div class="card-title" style="font-size: 1.3rem;">
                        <span>✨ AI Suggestions for ${escapeHtml(aiSuggestionsModal.fieldKey)}</span>
                        <button type="button" class="btn btn-sm btn-danger" data-action="close-ai-modal">✕</button>
                    </div>
                    <p style="color: var(--text-muted); margin-bottom: 1rem;">Select one of the 4 AI-generated choices below to populate your parameter field, or close to keep writing freely.</p>
                    
                    ${aiSuggestionsModal.loading ? `
                        <div style="text-align: center; padding: 2rem; color: var(--accent);">Generating 4 intelligent choices...</div>
                    ` : `
                        <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                            ${aiSuggestionsModal.suggestions.map((sug, idx) => `
                                <div class="ai-suggestion-item" data-suggestion-text="${escapeAttr(sug)}" style="background: var(--bg-primary); border: 1px solid var(--border-color); padding: 0.85rem 1rem; border-radius: 4px; cursor: pointer; transition: border-color 0.2s;">
                                    <strong>Option ${idx + 1}:</strong> ${escapeHtml(sug)}
                                </div>
                            `).join('')}
                        </div>
                    `}
                </div>
            </div>
        ` : ''}

        <div class="card">
            <div class="card-title">All Projects</div>
            ${state.projects.length === 0 ? `
                <div class="empty-state">
                    <h3>No projects found</h3>
                    <p>Use the wizard above to create your first project.</p>
                </div>
            ` : `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Concept</th>
                                <th>Universe</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.projects.map(p => `
                                <tr>
                                    <td><code>${escapeHtml(p.id)}</code></td>
                                    <td><strong>${escapeHtml(p.name)}</strong></td>
                                    <td>${escapeHtml(p.concept || '-')}</td>
                                    <td>${escapeHtml(p.universe_id || 'None')}</td>
                                    <td>
                                        <div style="display: flex; gap: 0.5rem;">
                                            <button class="btn btn-sm ${p.id === state.activeProjectId ? 'btn-primary' : ''}" data-action="select" data-id="${p.id}">
                                                ${p.id === state.activeProjectId ? 'Active' : 'Select'}
                                            </button>
                                            <button class="btn btn-sm btn-danger" data-action="delete" data-id="${p.id}">Delete</button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;

    // Sync input values to wizardState on change / input
    const bindInput = (id, key) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', (e) => {
                wizardState[key] = e.target.value;
            });
            el.addEventListener('change', (e) => {
                wizardState[key] = e.target.value;
            });
        }
    };
    bindInput('wiz-name', 'name');
    bindInput('wiz-concept', 'concept');
    bindInput('wiz-universe', 'universe_id');
    bindInput('wiz-genre', 'genre');
    bindInput('wiz-tone', 'tone');
    bindInput('wiz-protagonist', 'protagonist');
    bindInput('wiz-conflict', 'conflict');
    bindInput('wiz-world', 'world_setting');

    // Step tab clicks
    container.querySelectorAll('[data-wizard-step]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            syncWizardStateFromDOM();
            activeStep = parseInt(e.target.getAttribute('data-wizard-step'), 10);
            renderProjects(container);
        });
    });

    // Next / Prev buttons
    container.querySelectorAll('[data-action="next-step"]').forEach(btn => {
        btn.addEventListener('click', () => {
            syncWizardStateFromDOM();
            if (activeStep < 5) {
                activeStep++;
                renderProjects(container);
            }
        });
    });

    container.querySelectorAll('[data-action="prev-step"]').forEach(btn => {
        btn.addEventListener('click', () => {
            syncWizardStateFromDOM();
            if (activeStep > 1) {
                activeStep--;
                renderProjects(container);
            }
        });
    });

    // AI suggestion trigger buttons
    container.querySelectorAll('[data-ai-suggest]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            syncWizardStateFromDOM();
            const fieldKey = e.target.getAttribute('data-ai-suggest');
            aiSuggestionsModal = {
                fieldKey,
                suggestions: [],
                loading: true
            };
            renderProjects(container);

            try {
                const res = await api.wizardSuggest({
                    field_key: fieldKey,
                    current_parameters: wizardState
                });
                aiSuggestionsModal.suggestions = res.suggestions || [];
                aiSuggestionsModal.loading = false;
                renderProjects(container);
            } catch (err) {
                alert(`Failed to generate AI suggestions: ${err.message}`);
                aiSuggestionsModal = { fieldKey: null, suggestions: [], loading: false };
                renderProjects(container);
            }
        });
    });

    // Close AI modal button
    const closeAiBtn = container.querySelector('[data-action="close-ai-modal"]');
    if (closeAiBtn) {
        closeAiBtn.addEventListener('click', () => {
            aiSuggestionsModal = { fieldKey: null, suggestions: [], loading: false };
            renderProjects(container);
        });
    }

    // AI suggestion item click
    container.querySelectorAll('.ai-suggestion-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const text = e.currentTarget.getAttribute('data-suggestion-text');
            const fieldKey = aiSuggestionsModal.fieldKey;
            if (fieldKey) {
                const mapping = {
                    'concept': 'wiz-concept',
                    'genre': 'wiz-genre',
                    'tone': 'wiz-tone',
                    'protagonist': 'wiz-protagonist',
                    'conflict': 'wiz-conflict',
                    'world_setting': 'wiz-world'
                };
                const inputId = mapping[fieldKey];
                if (inputId) {
                    wizardState[fieldKey] = text;
                    const el = document.getElementById(inputId);
                    if (el) el.value = text;
                }
            }
            aiSuggestionsModal = { fieldKey: null, suggestions: [], loading: false };
            renderProjects(container);
        });
    });

    // Wizard Form submission (Final step create project)
    const wizardForm = document.getElementById('wizard-form');
    if (wizardForm) {
        wizardForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            syncWizardStateFromDOM();

            try {
                const newProj = await api.wizardCreate(wizardState);
                store.setActiveProject(newProj.id);
                await store.refreshGlobalData();
                // Reset wizard state
                wizardState = { name: '', concept: '', universe_id: '', genre: '', tone: '', protagonist: '', conflict: '', world_setting: '' };
                activeStep = 1;
                renderProjects(container);
                alert(`Project "${newProj.name}" created successfully with all lore files generated!`);
            } catch (err) {
                alert(`Error creating project via wizard: ${err.message}`);
            }
        });
    }

    // Active project select dropdown
    const activeSelect = document.getElementById('active-project-select');
    if (activeSelect) {
        activeSelect.addEventListener('change', (e) => {
            store.setActiveProject(e.target.value || null);
            renderProjects(container);
        });
    }

    // Table action buttons
    container.querySelectorAll('[data-action="select"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            store.setActiveProject(e.target.getAttribute('data-id'));
            renderProjects(container);
        });
    });

    container.querySelectorAll('[data-action="delete"]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const pid = e.target.getAttribute('data-id');
            if (confirm(`Are you sure you want to delete project ${pid}?`)) {
                try {
                    await api.deleteProject(pid);
                    await store.refreshGlobalData();
                    renderProjects(container);
                } catch (err) {
                    alert(`Error deleting project: ${err.message}`);
                }
            }
        });
    });
}

function syncWizardStateFromDOM() {
    const getValue = (id) => {
        const el = document.getElementById(id);
        return el ? el.value : '';
    };
    if (document.getElementById('wiz-name')) wizardState.name = getValue('wiz-name');
    if (document.getElementById('wiz-concept')) wizardState.concept = getValue('wiz-concept');
    if (document.getElementById('wiz-universe')) wizardState.universe_id = getValue('wiz-universe');
    if (document.getElementById('wiz-genre')) wizardState.genre = getValue('wiz-genre');
    if (document.getElementById('wiz-tone')) wizardState.tone = getValue('wiz-tone');
    if (document.getElementById('wiz-protagonist')) wizardState.protagonist = getValue('wiz-protagonist');
    if (document.getElementById('wiz-conflict')) wizardState.conflict = getValue('wiz-conflict');
    if (document.getElementById('wiz-world')) wizardState.world_setting = getValue('wiz-world');
}

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeAttr(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}
