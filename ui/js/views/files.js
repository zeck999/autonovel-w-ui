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

    const foundationFiles = files.filter(f => !f.name.startsWith('chapters/'));
    const chapterFiles = files.filter(f => f.name.startsWith('chapters/'));

    container.innerHTML = `
        <div class="grid-2" style="grid-template-columns: 280px 1fr; gap: 1.5rem;">
            <!-- File List Sidebar -->
            <div class="card" style="height: fit-content;">
                <div class="card-title">Fichiers du Projet</div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Projet : <strong>${escapeHtml(pid)}</strong>
                </p>

                <!-- Section 1: Fichiers de Fondation & Lore -->
                <div style="font-size: 0.75rem; font-weight: bold; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.4rem; letter-spacing: 0.05em;">Fichiers de Fondation & Lore</div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem;" id="foundation-file-list">
                    ${foundationFiles.map(f => `
                        <button class="btn ${f.name === selectedFile ? 'btn-primary' : ''}" style="text-align: left; justify-content: flex-start; width: 100%;" data-filename="${escapeHtml(f.name)}">
                            <span>📄 ${escapeHtml(f.name)}</span>
                            <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">${f.exists ? `${f.size}b` : 'créer'}</span>
                        </button>
                    `).join('')}
                </div>

                <!-- Section 2: Chapitres -->
                <div style="font-size: 0.75rem; font-weight: bold; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.4rem; letter-spacing: 0.05em;">Chapitres</div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.75rem;" id="chapter-file-list">
                    ${chapterFiles.length === 0 ? `<div style="font-size: 0.85rem; color: var(--text-muted); font-style: italic; padding: 0.25rem 0;">Aucun chapitre.</div>` : ''}
                    ${chapterFiles.map(f => `
                        <button class="btn ${f.name === selectedFile ? 'btn-primary' : ''}" style="text-align: left; justify-content: flex-start; width: 100%;" data-filename="${escapeHtml(f.name)}">
                            <span>📖 ${escapeHtml(f.name.replace('chapters/', ''))}</span>
                            <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">${f.exists ? `${f.size}b` : 'créer'}</span>
                        </button>
                    `).join('')}
                </div>

                <!-- Quick-create form/button for new chapters -->
                <form id="new-chapter-form" style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                    <input type="text" id="new-chapter-name" class="form-control" placeholder="chapter_01.md" style="font-size: 0.85rem;" required>
                    <button type="submit" class="btn btn-sm btn-primary" title="Créer un chapitre">+ Chap</button>
                </form>

                <hr style="border: 0; border-top: 1px solid var(--border-color); margin: 0.5rem 0 1rem 0;">

                <form id="new-custom-file-form" style="display: flex; gap: 0.5rem;">
                    <input type="text" id="new-filename" class="form-control" placeholder="autre_fichier.md" style="font-size: 0.85rem;" required>
                    <button type="submit" class="btn btn-sm" title="Créer un autre fichier">+</button>
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

                ${selectedFile.startsWith('chapters/') ? `
                    <div id="ai-modifier-toolbar" style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 1rem; padding: 0.75rem; background: var(--bg-surface-hover); border: 1px solid var(--border-color); border-radius: 4px;">
                        <input type="text" id="ai-prompt-input" class="form-control" placeholder="Instruction IA (ex: Rendre le dialogue plus tendu, ajouter des détails sensoriels...)" style="flex: 1; font-size: 0.9rem;">
                        <button id="ai-modify-btn" class="btn btn-sm btn-primary" title="Modifier le chapitre avec l'IA">✨ Modifier avec l'IA</button>
                        <span id="ai-modify-status" style="font-size: 0.85rem; color: var(--text-muted); white-space: nowrap;"></span>
                    </div>
                ` : ''}

                <div class="form-group" style="margin-bottom: 0;">
                    <textarea id="file-editor-textarea" class="form-control" style="font-family: monospace; font-size: 0.95rem; min-height: 500px; line-height: 1.5; resize: vertical;" placeholder="Contenu du fichier Markdown...">${escapeHtml(fileContent)}</textarea>
                </div>
            </div>
        </div>
    `;

    container.querySelectorAll('[data-filename]').forEach(btn => {
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

    const aiModifyBtn = document.getElementById('ai-modify-btn');
    const aiPromptInput = document.getElementById('ai-prompt-input');
    const aiModifyStatus = document.getElementById('ai-modify-status');

    if (aiModifyBtn && aiPromptInput && textarea) {
        aiModifyBtn.addEventListener('click', async () => {
            const promptText = aiPromptInput.value.trim();
            if (!promptText) {
                aiModifyStatus.textContent = 'Veuillez saisir une instruction pour l’IA.';
                aiModifyStatus.style.color = 'var(--danger)';
                return;
            }
            aiModifyBtn.disabled = true;
            aiPromptInput.disabled = true;
            aiModifyStatus.textContent = 'IA en cours...';
            aiModifyStatus.style.color = 'var(--accent)';
            try {
                const res = await api.modifyChapterWithAI(pid, selectedFile, textarea.value, promptText);
                textarea.value = res.content;
                aiModifyStatus.textContent = '✓ Chapitre modifié avec succès !';
                aiModifyStatus.style.color = 'var(--success)';
                setTimeout(() => { aiModifyStatus.textContent = ''; }, 4000);
            } catch (err) {
                aiModifyStatus.textContent = `Erreur : ${err.message}`;
                aiModifyStatus.style.color = 'var(--danger)';
            } finally {
                aiModifyBtn.disabled = false;
                aiPromptInput.disabled = false;
            }
        });
    }

    const newChapterForm = document.getElementById('new-chapter-form');
    if (newChapterForm) {
        newChapterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('new-chapter-name');
            let val = input.value.trim();
            if (val) {
                if (!val.startsWith('chapters/')) {
                    val = `chapters/${val}`;
                }
                store.state.selectedProjectFile = val;
                try {
                    await api.saveProjectFile(pid, val, `# ${val}\n\nNouveau chapitre.`);
                    await renderFiles(container);
                } catch (err) {
                    alert(`Erreur création chapitre: ${err.message}`);
                }
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
