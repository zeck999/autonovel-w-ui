/**
    ui/js/views/dashboard.js — Dashboard View
 */

import { store } from '../store.js';
import { api } from '../api.js';
import { navigate } from '../router.js';

export function renderDashboard(container) {
    const state = store.state;
    const activeProject = state.projects.find(p => p.id === state.activeProjectId);
    const pipeline = state.pipelineStatus || {};

    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Active Project</div>
                ${activeProject ? `
                    <div style="margin-bottom: 1rem;">
                        <h3 style="font-family: var(--font-display); font-size: 1.8rem; color: var(--text-main); margin-bottom: 0.3rem;">${escapeHtml(activeProject.name)}</h3>
                        <p style="color: var(--text-muted); font-size: 1.05rem; margin-bottom: 1rem;">${escapeHtml(activeProject.concept || 'No concept provided.')}</p>
                        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                            <span class="badge">Universe: ${escapeHtml(activeProject.universe_id || 'Standalone')}</span>
                            <span class="badge badge-success">Phase: ${escapeHtml(pipeline.phase || 'idle')}</span>
                            <span class="badge">Score: ${escapeHtml(String(pipeline.score || 0.0))}</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
                        <button class="btn btn-primary" id="dash-run-foundation">Run Foundation</button>
                        <button class="btn" onclick="window.location.hash='#/pipeline'">Open Pipeline</button>
                    </div>
                ` : `
                    <div class="empty-state">
                        <h3>No Project Selected</h3>
                        <p>Create or select a project to start writing.</p>
                        <button class="btn btn-primary" style="margin-top: 1rem;" onclick="window.location.hash='#/projects'">Manage Projects</button>
                    </div>
                `}
            </div>

            <div class="card">
                <div class="card-title">Quick Stats & Overview</div>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div><strong>Total Projects:</strong> ${state.projects.length}</div>
                    <div><strong>Shared Universes:</strong> ${state.universes.length}</div>
                    <div><strong>Active Branches:</strong> ${state.branches.length}</div>
                    <div><strong>System Status:</strong> <span style="color: var(--success);">Operational</span></div>
                </div>
                <div style="margin-top: 1.5rem; display: flex; gap: 1rem;">
                    <button class="btn" onclick="window.location.hash='#/projects'">View Projects</button>
                    <button class="btn" onclick="window.location.hash='#/universes'">Explore Universes</button>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Recent Projects</div>
            ${state.projects.length === 0 ? `
                <div class="empty-state">
                    <h3>No projects found</h3>
                    <p>Get started by creating your first novel project.</p>
                </div>
            ` : `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Concept</th>
                                <th>Universe</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.projects.map(p => `
                                <tr>
                                    <td><strong>${escapeHtml(p.name)}</strong></td>
                                    <td>${escapeHtml(p.concept || '-')}</td>
                                    <td>${escapeHtml(p.universe_id || 'None')}</td>
                                    <td>
                                        <button class="btn btn-sm ${p.id === state.activeProjectId ? 'btn-primary' : ''}" data-select-project="${p.id}">
                                            ${p.id === state.activeProjectId ? 'Active' : 'Select'}
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;

    // Bind event handlers
    const runFoundationBtn = document.getElementById('dash-run-foundation');
    if (runFoundationBtn) {
        runFoundationBtn.addEventListener('click', async () => {
            try {
                runFoundationBtn.disabled = true;
                runFoundationBtn.textContent = 'Running...';
                await api.runPipelinePhase({
                    phase: 'foundation',
                    project_id: state.activeProjectId
                });
                await store.refreshActiveProjectData();
                alert('Foundation phase executed successfully!');
            } catch (err) {
                alert(`Error: ${err.message}`);
            } finally {
                runFoundationBtn.disabled = false;
                runFoundationBtn.textContent = 'Run Foundation';
            }
        });
    }

    container.querySelectorAll('[data-select-project]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pid = e.target.getAttribute('data-select-project');
            store.setActiveProject(pid);
            renderDashboard(container);
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
