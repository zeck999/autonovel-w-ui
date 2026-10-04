/**
    ui/js/views/universes.js — Shared Universes Management View
 */

import { store } from '../store.js';
import { api } from '../api.js';

export function renderUniverses(container) {
    const state = store.state;

    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Create Shared Universe</div>
                <form id="create-universe-form">
                    <div class="form-group">
                        <label class="form-label" for="universe-name">Universe Name</label>
                        <input type="text" id="universe-name" class="form-control" required placeholder="e.g. Cantamura Lore">
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="universe-desc">Description / Lore</label>
                        <textarea id="universe-desc" class="form-control" required placeholder="Shared world rules, background, characters..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Create Universe</button>
                </form>
            </div>

            <div class="card">
                <div class="card-title">Universe & Series Info</div>
                <p style="color: var(--text-muted); line-height: 1.6;">
                    Shared universes allow multiple novel projects to inherit common lore, world-building, and character bibles. 
                    Attaching a universe copies foundational assets into your project upon creation.
                </p>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Existing Universes</div>
            ${state.universes.length === 0 ? `
                <div class="empty-state">
                    <h3>No universes found</h3>
                    <p>Create a shared universe above to reuse lore across multiple projects.</p>
                </div>
            ` : `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Description</th>
                                <th>Linked Projects</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${state.universes.map(u => {
                                const linkedCount = state.projects.filter(p => p.universe_id === u.id).length;
                                return `
                                    <tr>
                                        <td><code>${escapeHtml(u.id)}</code></td>
                                        <td><strong>${escapeHtml(u.name)}</strong></td>
                                        <td>${escapeHtml(u.description || '-')}</td>
                                        <td><span class="badge">${linkedCount} projects</span></td>
                                        <td>
                                            <button class="btn btn-sm btn-danger" data-delete-universe="${u.id}">Delete</button>
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `}
        </div>
    `;

    const form = document.getElementById('create-universe-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('universe-name').value;
            const description = document.getElementById('universe-desc').value;

            try {
                await api.createUniverse({ name, description });
                await store.refreshGlobalData();
                renderUniverses(container);
            } catch (err) {
                alert(`Error creating universe: ${err.message}`);
            }
        });
    }

    container.querySelectorAll('[data-delete-universe]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const uid = e.target.getAttribute('data-delete-universe');
            if (confirm(`Delete universe ${uid}? Linked projects will remain intact.`)) {
                try {
                    await api.deleteUniverse(uid);
                    await store.refreshGlobalData();
                    renderUniverses(container);
                } catch (err) {
                    alert(`Error deleting universe: ${err.message}`);
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
