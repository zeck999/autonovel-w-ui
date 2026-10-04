/**
    ui/js/views/branches.js — Narrative Versioning & Branches View
 */

import { store } from '../store.js';
import { api } from '../api.js';

export function renderBranches(container) {
    const state = store.state;
    const pid = state.activeProjectId;

    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Create Narrative Branch</div>
                <form id="create-branch-form">
                    <div class="form-group">
                        <label class="form-label" for="branch-name">Branch Name</label>
                        <input type="text" id="branch-name" class="form-control" required placeholder="e.g. alt-ending-chapter3">
                    </div>
                    <button type="submit" class="btn btn-primary">Create Branch</button>
                </form>
            </div>

            <div class="card">
                <div class="card-title">Switch Active Branch</div>
                <form id="switch-branch-form">
                    <div class="form-group">
                        <label class="form-label" for="switch-branch-select">Target Branch</label>
                        <select id="switch-branch-select" class="form-control">
                            ${state.branches.map(b => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`).join('')}
                        </select>
                    </div>
                    <button type="submit" class="btn">Switch Branch</button>
                </form>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Project Branches (${escapeHtml(pid || 'Global/Default')})</div>
            ${state.branches.length === 0 ? `
                <div class="empty-state">
                    <h3>No branches found</h3>
                    <p>Create a branch to experiment with alternative storylines.</p>
                </div>
            ` : `
                <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem;">
                    ${state.branches.map(b => `<span class="badge" style="font-size: 1rem; padding: 0.4rem 0.8rem;">${escapeHtml(b)}</span>`).join('')}
                </div>
            `}
        </div>

        <div class="card">
            <div class="card-title">Revision History & Scores</div>
            ${state.history.length === 0 ? `
                <div class="empty-state">
                    <h3>No revision history recorded</h3>
                    <p>Run pipeline evaluation or draft chapters to generate revision history.</p>
                </div>
            ` : `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Chapter</th>
                                <th>Commit</th>
                                <th>Phase</th>
                                <th>Score</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.history.map(h => `
                                <tr>
                                    <td><strong>#${escapeHtml(String(h.chapter_num || '-'))}</strong></td>
                                    <td><code>${escapeHtml(h.commit || '-')}</code></td>
                                    <td>${escapeHtml(h.phase || '-')}</td>
                                    <td><span class="badge badge-success">${escapeHtml(String(h.score || 0.0))}</span></td>
                                    <td>${escapeHtml(h.description || '-')}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;

    const createForm = document.getElementById('create-branch-form');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const branchName = document.getElementById('branch-name').value;
            try {
                await api.createBranch({ branch_name: branchName, project_id: pid });
                await store.refreshActiveProjectData();
                renderBranches(container);
            } catch (err) {
                alert(`Error creating branch: ${err.message}`);
            }
        });
    }

    const switchForm = document.getElementById('switch-branch-form');
    if (switchForm) {
        switchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const branchName = document.getElementById('switch-branch-select').value;
            try {
                await api.switchBranch({ branch_name: branchName, project_id: pid });
                await store.refreshActiveProjectData();
                alert(`Successfully switched to branch: ${branchName}`);
                renderBranches(container);
            } catch (err) {
                alert(`Error switching branch: ${err.message}`);
            }
        });
    }
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
