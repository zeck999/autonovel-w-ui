/**
    ui/js/views/files.js — Project Files & Lore Editor View
 */

import { store } from '../store.js';
import { api } from '../api.js';
import { mountStagePreview } from '../stage-preview.js';
import { canLeaveEditor, setNavigationGuard, clearNavigationGuard, draftKey, saveDraft, readDraft, canonicalChapterName } from '../editor-state.js';

let renderSequence = 0;
let disposeStage;
window.addEventListener('autonovel-navigation', () => { renderSequence += 1; });

export async function renderFiles(container) {
    const sequence = ++renderSequence;
    disposeStage?.();
    disposeStage = undefined;
    clearNavigationGuard();
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

    let publication;
    try { publication = await api.getPublication(pid); }
    catch (error) { container.innerHTML = `<div class="card">Statut de publication indisponible : ${escapeHtml(error.message)}. Édition bloquée.</div>`; return; }
    const published = publication.publication_status === 'published';
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
            if (err.status !== 404) {
                container.innerHTML = `<div class="card"><p>Impossible de charger le fichier : ${escapeHtml(err.message)}</p></div>`;
                return;
            }
            fileContent = '';
        }
    }

    if (sequence !== renderSequence || store.state.activeProjectId !== pid) return;
    let savedContent = fileContent;
    const storageKey = draftKey(pid, selectedFile);
    const draft = published ? null : readDraft(localStorage, storageKey);
    if (draft && draft.content !== savedContent && confirm('Restaurer le brouillon local non sauvegardé ?')) fileContent = draft.content;
    const foundationFiles = files.filter(f => !f.name.startsWith('chapters/'));
    const chapterFiles = files.filter(f => f.name.startsWith('chapters/'));

    container.innerHTML = `
        <p><a href="#/coherence">Cohérence, canon et publication</a></p><div class="grid-2" style="grid-template-columns: 280px 1fr; gap: 1.5rem;">
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
                    <input type="text" id="new-chapter-name" class="form-control" placeholder="ch_01.md" style="font-size: 0.85rem;" required>
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
                    <div class="card-title" style="margin: 0;" id="editor-title">${published ? 'Publié · lecture seule :' : 'Édition :'} ${escapeHtml(selectedFile)}</div>
                    <div style="display: flex; gap: 0.75rem; align-items: center;">
                        <span id="save-status" style="font-size: 0.85rem; color: var(--text-muted);"></span>
                        <button id="save-file-btn" ${published ? 'disabled' : ''} class="btn btn-primary">Sauvegarder</button>
                    </div>
                </div>

                ${!published && selectedFile.startsWith('chapters/') ? `
                    <div id="ai-modifier-toolbar" style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 1rem; padding: 0.75rem; background: var(--bg-surface-hover); border: 1px solid var(--border-color); border-radius: 4px;">
                        <input type="text" id="ai-prompt-input" class="form-control" placeholder="Instruction IA (ex: Rendre le dialogue plus tendu, ajouter des détails sensoriels...)" style="flex: 1; font-size: 0.9rem;">
                        <button id="ai-modify-btn" class="btn btn-sm btn-primary" title="Modifier le chapitre avec l'IA">✨ Modifier avec l'IA</button>
                        <span id="ai-modify-status" style="font-size: 0.85rem; color: var(--text-muted); white-space: nowrap;"></span>
                    </div>
                ` : ''}

                <div class="form-group" style="margin-bottom: 0;">
                    <textarea id="file-editor-textarea" ${published ? 'readonly' : ''} class="form-control" style="font-family: monospace; font-size: 0.95rem; min-height: 500px; line-height: 1.5; resize: vertical;" placeholder="Contenu du fichier Markdown...">${escapeHtml(fileContent)}</textarea>
                </div>
            </div>
        </div>
        ${published ? `<div class="card"><div class="card-title">Correction de forme d’un roman publié</div><p>Uniquement typographie, orthographe, grammaire et mise en page, sans changement de sens. L’original canonique est conservé et chaque correction est journalisée.</p><textarea id="proofread-content" class="form-control" rows="12">${escapeHtml(fileContent)}</textarea><button id="proofread-propose" class="btn btn-secondary">Vérifier ma correction de forme</button><p id="proofread-status" role="status"></p><pre id="proofread-diff" style="white-space:pre-wrap"></pre><button id="proofread-apply" class="btn btn-primary" hidden>Confirmer et appliquer cette correction</button></div>` : ''}
    `;

    if (published) container.querySelectorAll('#new-chapter-form, #new-custom-file-form').forEach(form => { form.hidden = true; form.querySelectorAll('input,button').forEach(input => { input.disabled = true; }); });
    const editor = container.querySelector('#file-editor-textarea');
    if (editor && /^chapters\/[^/]+\.md$/.test(selectedFile)) {
        const preview = document.createElement('details');
        preview.className = 'stage-preview';
        preview.innerHTML = `
            <summary>Aperçu de mise en scène</summary>
            <div class="stage-scene">
                <div class="stage-background"></div>
                <div class="stage-portraits"></div>
            </div>
            <div class="stage-prose"></div>
            <div class="stage-controls">
                <button type="button" class="btn stage-previous" disabled>Précédent</button>
                <span class="stage-status" role="status"></span>
                <button type="button" class="btn stage-next" disabled>Suivant</button>
            </div>
            <p class="stage-warnings" role="status"></p>`;
        editor.after(preview);
        disposeStage = mountStagePreview(preview, editor, pid, () => preview.isConnected && sequence === renderSequence);
    }
    const isDirty = () => Boolean(editor && editor.value !== savedContent);
    if (!published) setNavigationGuard(() => !isDirty() || confirm('Modifications non sauvegardées. Quitter cet éditeur ? Le brouillon reste disponible sur cet appareil.'), isDirty);
    if (!published) editor?.addEventListener('input', () => saveDraft(localStorage, storageKey, editor.value, savedContent));
    if (published) {
        const input = container.querySelector('#proofread-content');
        const check = container.querySelector('#proofread-propose');
        const apply = container.querySelector('#proofread-apply');
        const status = container.querySelector('#proofread-status');
        let candidate = null;
        input.addEventListener('input', () => { candidate = null; apply.hidden = true; });
        check.onclick = async () => {
            if (!confirm('Vérifier cette correction avec votre fournisseur IA ? Cette opération peut être payante. Aucune modification ne sera appliquée sans confirmation.')) return;
            check.disabled = true; input.readOnly = true; status.textContent = 'Vérification de la forme et de la cohérence…';
            try {
                const result = await api.proposeProofread(pid, {file_path: selectedFile, content: input.value, expected_content: fileContent});
                if (sequence !== renderSequence) return;
                candidate = result;
                container.querySelector('#proofread-diff').textContent = result.diff || `AVANT\n${fileContent}\n\nAPRÈS\n${input.value}`;
                const allowed = result.allowed === true || result.approved === true || result.status === 'approved';
                apply.hidden = !allowed || !result.proposal_id;
                status.textContent = result.message || (allowed ? 'Comparez les deux versions avant de confirmer. Le contrôle IA n’est pas une garantie absolue.' : 'Correction refusée ou incertaine : aucune application possible.');
            } catch (error) { status.textContent = error.message; }
            finally { check.disabled = false; input.readOnly = false; }
        };
        apply.onclick = async () => {
            if (!candidate || !confirm('Je confirme avoir comparé les versions et que la correction ne change ni sens ni fait narratif. Appliquer et journaliser ?')) return;
            apply.disabled = true;
            try { await api.applyProofread(pid, candidate.proposal_id); if (sequence === renderSequence) await renderFiles(container); }
            catch (error) { status.textContent = error.message; apply.disabled = false; }
        };
    }

    container.querySelectorAll('[data-filename]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if (!canLeaveEditor()) return;
            const fname = e.currentTarget.getAttribute('data-filename');
            store.state.selectedProjectFile = fname;
            await renderFiles(container);
        });
    });

    const saveBtn = document.getElementById('save-file-btn');
    const textarea = document.getElementById('file-editor-textarea');
    const statusSpan = document.getElementById('save-status');

    if (!published && saveBtn && textarea) {
        saveBtn.addEventListener('click', async () => {
            saveBtn.disabled = true;
            statusSpan.textContent = 'Enregistrement...';
            try {
                const content = textarea.value;
                await api.saveProjectFile(pid, selectedFile, content, savedContent);
                savedContent = content;
                saveDraft(localStorage, storageKey, textarea.value, savedContent);
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
            const inputSnapshot = textarea.value;
            const originalOnDisk = savedContent;
            aiModifyStatus.textContent = 'Génération en cours — aucune sauvegarde automatique.';
            try {
                const result = await api.modifyChapterWithAI(pid, selectedFile, inputSnapshot, promptText,
                    job => { aiModifyStatus.textContent = `Tâche ${job.id} : ${job.status} — ${job.progress || 'en cours'}`; });
                if (sequence !== renderSequence || !container.contains(textarea)) return;
                let proposal = container.querySelector('#ai-proposal');
                if (proposal) proposal.remove();
                proposal = document.createElement('section');
                proposal.id = 'ai-proposal';
                proposal.className = 'card';
                const title = document.createElement('h3');
                title.textContent = 'Proposition IA — non enregistrée';
                const preview = document.createElement('textarea');
                preview.className = 'form-control';
                preview.rows = 16;
                preview.readOnly = true;
                preview.value = result.content;
                const apply = document.createElement('button');
                apply.className = 'btn btn-primary';
                apply.textContent = 'Appliquer et enregistrer cette proposition';
                const discard = document.createElement('button');
                discard.className = 'btn';
                discard.textContent = 'Ignorer';
                discard.addEventListener('click', () => proposal.remove());
                apply.addEventListener('click', async () => {
                    if (textarea.value !== inputSnapshot || savedContent !== originalOnDisk) {
                        aiModifyStatus.textContent = 'Le texte a changé pendant la génération. Proposition conservée pour comparaison ; aucune modification appliquée.';
                        return;
                    }
                    if (!confirm('Remplacer le chapitre par cette proposition et l’enregistrer ?')) return;
                    apply.disabled = true;
                    try {
                        textarea.disabled = true;
                        saveBtn.disabled = true;
                        await api.saveProjectFile(pid, selectedFile, result.content, result.original_content ?? originalOnDisk);
                        savedContent = result.content;
                        textarea.value = result.content;
                        textarea.dispatchEvent(new Event('input'));
                        proposal.remove();
                        aiModifyStatus.textContent = 'Proposition appliquée et enregistrée.';
                    } catch (error) {
                        aiModifyStatus.textContent = `Non appliquée : ${error.message}`;
                    } finally { apply.disabled = false; textarea.disabled = false; saveBtn.disabled = false; }
                });
                proposal.append(title, preview, apply, discard);
                textarea.parentElement.append(proposal);
                aiModifyStatus.textContent = 'Proposition prête. Relisez-la avant de l’appliquer.';
            } catch (err) {
                aiModifyStatus.textContent = `Erreur : ${err.message}`;
            } finally {
                aiModifyBtn.disabled = false;
                aiPromptInput.disabled = false;
            }
        });
    }

    const newChapterForm = document.getElementById('new-chapter-form');
    if (!published && newChapterForm) {
        newChapterForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!canLeaveEditor()) return;
            const input = document.getElementById('new-chapter-name');
            try {
                const val = `chapters/${canonicalChapterName(input.value)}`;
                if (files.some(file => file.name === val && file.exists)) throw new Error('Ce chapitre existe déjà.');
                await api.saveProjectFile(pid, val, `# ${val}\n\nNouveau chapitre.`, '');
                store.state.selectedProjectFile = val;
                await renderFiles(container);
            } catch (err) {
                alert(`Erreur création chapitre : ${err.message}`);
            }
        });
    }

    const newFileForm = document.getElementById('new-custom-file-form');
    if (!published && newFileForm) {
        newFileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!canLeaveEditor()) return;
            const fnameInput = document.getElementById('new-filename');
            const fname = fnameInput.value.trim();
            if (fname) {
                store.state.selectedProjectFile = fname;
                try {
                    await api.saveProjectFile(pid, fname, `# ${fname}\n\nNouveau fichier.`, '');
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
