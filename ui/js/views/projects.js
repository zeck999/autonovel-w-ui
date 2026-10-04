/**
    ui/js/views/projects.js — Projects Management View
 */

import { store } from '../store.js';
import { api } from '../api.js';

export function renderProjects(container) {
    const state = store.state;

    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Create New Project</div>
                <form id="create-project-form">
                    <div class="form-group">
                        <label class="form-label" for="project-name">Project Name</label>
                        <input type="text" id="project-name" class="form-control" required placeholder="e.g. The Clockwork Empire">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="project-concept">Concept / Premise</label>
                        <textarea id="project-concept" class="form-control" required placeholder="A brief description of the story..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="project-universe">Shared Universe (Optional)</label>
                        <select id="project-universe" class="form-control">
                            <option value="">-- None (Standalone) --</option>
                            ${state.universes.map(u => `<option value="${u.id}">${escapeHtml(u.name)}</option>`).join('')}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Project</button>
                </form>
            </div>

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

        <div class="card">
            <div class="card-title">All Projects</div>
            ${state.projects.length === 0 ? `
                <div class="empty-state">
                    <h3>No projects found</h3>
                    <p>Use the form above to create your first project.</p>
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

    // Form submission
    const form = document.getElementById('create-project-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('project-name').value;
            const concept = document.getElementById('project-concept').value;
            const universeId = document.getElementById('project-universe').value || null;

            try {
                await api.createProject({ name, concept, universe_id: universeId });
                await store.refreshGlobalData();
                renderProjects(container);
            } catch (err) {
                alert(`Error creating project: ${err.message}`);
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

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
