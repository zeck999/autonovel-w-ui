/** Narrative Git history. Evaluation scores are not restorable revisions. */
import { store } from '../store.js';
import { api } from '../api.js';
import { canLeaveEditor } from '../editor-state.js';

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

export async function renderBranches(container) {
    const pid = store.state.activeProjectId;
    const route = window.location.hash;
    const isCurrent = () => pid === store.state.activeProjectId && route === window.location.hash && container.isConnected;
    if (!pid) {
        container.innerHTML = '<div class="card"><h3>Aucun projet actif</h3><p>Sélectionnez un projet pour gérer ses versions narratives.</p><a href="#/projects">Choisir un projet</a></div>';
        return;
    }
    container.innerHTML = '<div class="card">Chargement des versions narratives…</div>';
    try {
        const publication = await api.getPublication(pid);
        if (!isCurrent()) return;
        // Unknown status must not unlock mutations.
        if (publication.publication_status !== 'draft') {
            container.innerHTML = '<div class="card">Roman publié ou statut non modifiable : versions narratives bloquées. <a href="#/coherence">Consulter le canon</a></div>';
            return;
        }
        const [branches, history, status] = await Promise.all([
            api.listBranches(pid), api.getHistory(null, pid), api.getVersioningStatus(pid)
        ]);
        if (!isCurrent()) return;
        const dirty = status.dirty === true;
        container.innerHTML = `
            <div class="card">
                <div class="card-title">Versions narratives Git</div>
                <p>Branche active : <strong>${escapeHtml(status.branch || 'Aucune branche initialisée')}</strong></p>
                <p>${dirty ? 'Modifications non historisées détectées : changement de branche et restauration bloqués. Enregistrez ou traitez ces modifications sans les écraser.' : 'Aucune modification narrative non historisée détectée.'}</p>
                <p>Une restauration crée une nouvelle version. Elle ne supprime pas l’historique et ne fait pas reculer le canon partagé ni une publication.</p>
                <div id="versioning-message" role="status" aria-live="polite"></div>
            </div>
            <div class="grid-2">
                <div class="card">
                    <div class="card-title">Créer une branche narrative</div>
                    <form id="create-branch-form">
                        <label class="form-label" for="branch-name">Nom de la branche</label>
                        <input type="text" id="branch-name" class="form-control" required placeholder="ex. autre-fin-chapitre3" ${dirty ? 'disabled' : ''}>
                        <button type="submit" class="btn btn-primary" ${dirty ? 'disabled' : ''}>Créer la branche</button>
                    </form>
                </div>
                <div class="card">
                    <div class="card-title">Changer de branche</div>
                    <form id="switch-branch-form">
                        <label class="form-label" for="switch-branch-select">Branche cible</label>
                        <select id="switch-branch-select" class="form-control" ${dirty || !branches.length ? 'disabled' : ''}>
                            ${branches.map(branch => `<option value="${escapeHtml(branch)}" ${branch === status.branch ? 'selected' : ''}>${escapeHtml(branch)}</option>`).join('')}
                        </select>
                        <button type="submit" class="btn btn-secondary" ${dirty || !branches.length ? 'disabled' : ''}>Changer de branche</button>
                    </form>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Historique Git restaurable</div>
                <p>Ces lignes correspondent à des commits Git réels. Les scores d’évaluation sont des mesures séparées, pas des sauvegardes.</p>
                <div class="table-container"><table class="data-table"><thead><tr>
                    <th>Révision</th><th>Description</th><th>Action</th>
                </tr></thead><tbody>
                    ${history.length ? history.map((revision, index) => `<tr>
                        <td><code>${escapeHtml(revision.commit)}</code></td>
                        <td>${escapeHtml(revision.description)}</td>
                        <td><button type="button" class="btn btn-secondary" data-restore-index="${index}" ${dirty ? 'disabled' : ''}>Restaurer cette version</button></td>
                    </tr>`).join('') : '<tr><td colspan="3" style="text-align:center">Aucun instantané Git enregistré.</td></tr>'}
                </tbody></table></div>
            </div>`;
        let busy = false;
        const message = container.querySelector('#versioning-message');
        async function mutate(operation) {
            if (busy || !isCurrent() || !canLeaveEditor()) return;
            busy = true;
            const buttons = [...container.querySelectorAll('button')];
            const disabled = buttons.map(button => button.disabled);
            buttons.forEach(button => { button.disabled = true; });
            message.textContent = 'Opération en cours…';
            try {
                await operation();
                if (!isCurrent()) return;
                // Refresh project metadata/progression without reusing stale history.
                await store.refreshGlobalData();
                if (isCurrent()) await renderBranches(container);
            } catch (error) {
                if (isCurrent()) {
                    message.textContent = `Erreur : ${error.message}. Aucune nouvelle tentative automatique. Rechargez cette vue pour vérifier l’état réel avant de poursuivre.`;
                    buttons.forEach((button, index) => { button.disabled = disabled[index]; });
                }
            } finally { busy = false; }
        }
        container.querySelector('#create-branch-form').addEventListener('submit', event => {
            event.preventDefault();
            const branchName = container.querySelector('#branch-name').value.trim();
            if (!branchName || dirty) return;
            mutate(() => api.createBranch({ branch_name: branchName, project_id: pid }));
        });
        container.querySelector('#switch-branch-form').addEventListener('submit', event => {
            event.preventDefault();
            const branchName = container.querySelector('#switch-branch-select').value;
            if (!branchName || dirty || branchName === status.branch) return;
            if (!window.confirm(`Passer à la branche « ${branchName} » ? Le manuscrit et sa progression seront remplacés par cette branche ; la cohérence devra être revérifiée.`)) return;
            mutate(() => api.switchBranch({ branch_name: branchName, project_id: pid }));
        });
        container.querySelectorAll('[data-restore-index]').forEach(button => {
            button.addEventListener('click', () => {
                if (dirty || busy || !isCurrent()) return;
                const revision = history[Number(button.dataset.restoreIndex)];
                if (!revision?.commit) return;
                if (!window.confirm(`Restaurer la révision ${revision.commit} ? Une nouvelle version sera créée sur la branche courante. Les versions ultérieures resteront conservées et la cohérence devra être revérifiée.`)) return;
                mutate(() => api.restoreRevision(pid, revision.commit, true));
            });
        });
    } catch (error) {
        if (!isCurrent()) return;
        container.innerHTML = `<div class="card"><h3>Versions narratives indisponibles</h3><p>${escapeHtml(error.message)}</p><p>Aucune modification demandée. Rechargez la vue pour réessayer.</p></div>`;
    }
}
