/**
    ui/js/views/files.js — Project Files & Lore Editor View
 */

import { store } from '../store.js';
import { api } from '../api.js';

export async function renderFiles(container) {
    const state = store.state;
    const pid = state.activeProjectId;

    if (!pid) {
        container.innerHTML = `
            <div class="card">
                <div class="card-title">Fichiers & Lore</div>
                <div class="empty-state">
                    <h3>Aucun projet actif</h3>
                    <p>Veuillez sélectionner un projet actif dans l'onglet Projets pour éditer ses fichiers.</p>
                    <a href="#/projects" class="btn btn-primary" style="margin-top: 1rem; display: inline-block;">Aller aux Projets</a>
                </div>
            </div>
        `;
        return;
    }

    let files = [];
    try {
        files = await api.listProjectFiles(pid);
    } catch (err) {
        console.error("Failed to list project files:", err);
    }

    let selectedFile = state.selectedProjectFile || (files.length > 0 ? files[0].name : 'seed.txt');
    let fileContent = '';

    if (selectedFile) {
        try {
            const res = await api.getProjectFile(pid, selectedFile);
            fileContent = res.content || '';
        } catch (err) {
            fileContent = `# ${selectedFile}\n\n(Fichier vide ou non trouvé — commencez à rédiger ici.)`;
        }
    }

    container.innerHTML = `
        <div class="grid-2" style="grid-template-columns: 280px 1fr; gap: 1.5rem;">
            <!-- File List Sidebar -->
            <div class="card" style="height: fit-content;">
                <div class="card-title">Fichiers du Projet</div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Projet : <strong>${escapeHtml(pid)}</strong>
                </p>
                <div style="display: flex; flex-direction: column; gap: 0.5rem;" id="file-list-container">
                    ${files.map(f => `
                        <button class="btn ${f.name === selectedFile ? 'btn-primary' : ''}" style="text-align: left; justify-content: flex-start; width: 100%;" data-filename="${escapeHtml(f.name)}">
                            <span>📄 ${escapeHtml(f.name)}</span>
                            <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">${f.exists ? `${f.size}b` : 'créer'}</span>
                        </button>
                    `).join('')}
                </div>
                <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 1.25rem 0;">
                <form id="new-custom-file-form" style="display: flex; gap: 0.5rem;">
                    <input type="text" id="new-filename" class="form-control" placeholder="autre_fichier.md" style="font-size: 0.85rem;" required>
                    <button type="submit" class="btn btn-sm btn-primary">+</button>
                </form>
            </div>

            <!-- File Editor Area -->
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div class="card-title" style="margin: 0;" id="editor-title">Édition : ${escapeHtml(selectedFile)}</div>
                    <div style="display: flex; gap: 0.75rem; align-items: center;">
                        <span id="save-status" style="font-size: 0.85rem; color: var(--text-muted);"></span>
                        <button id="save-file-btn" class="btn btn-primary">Sauvegarder</button>
                    </div>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <textarea id="file-editor-textarea" class="form-control" style="font-family: monospace; font-size: 0.95rem; min-height: 500px; line-height: 1.5; resize: vertical;" placeholder="Contenu du fichier Markdown...">${escapeHtml(fileContent)}</textarea>
                </div>
            </div>
        </div>
    `;

    container.querySelectorAll('#file-list-container button').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const fname = e.currentTarget.getAttribute('data-filename');
            store.state.selectedProjectFile = fname;
            await renderFiles(container);
        });
    });

    const saveBtn = document.getElementById('save-file-btn');
    const textarea = document.getElementById('file-editor-textarea');
    const statusSpan = document.getElementById('save-status');

    if (saveBtn && textarea) {
        saveBtn.addEventListener('click', async () => {
            saveBtn.disabled = true;
            statusSpan.textContent = 'Enregistrement...';
            try {
                await api.saveProjectFile(pid, selectedFile, textarea.value);
                statusSpan.textContent = '✓ Sauvegardé';
                setTimeout(() => { statusSpan.textContent = ''; }, 3000);
            } catch (err) {
                statusSpan.textContent = `Erreur : ${err.message}`;
            } finally {
                saveBtn.disabled = false;
            }
        });
    }

    const newFileForm = document.getElementById('new-custom-file-form');
    if (newFileForm) {
        newFileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fnameInput = document.getElementById('new-filename');
            const fname = fnameInput.value.trim();
            if (fname) {
                store.state.selectedProjectFile = fname;
                try {
                    await api.saveProjectFile(pid, fname, `# ${fname}\n\nNouveau fichier.`);
                    await renderFiles(container);
                } catch (err) {
                    alert(`Erreur création fichier: ${err.message}`);
                }
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
