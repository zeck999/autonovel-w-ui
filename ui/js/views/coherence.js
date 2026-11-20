import { api } from '../api.js';
import { store } from '../store.js';
import { escapeHtml, analysisLabel, publicationBlocked } from '../universe-state.js';

let generation = 0;
window.addEventListener('autonovel-navigation', () => { generation++; });

export async function renderCoherence(container) {
    const current = ++generation;
    const pid = store.state.activeProjectId;
    if (!pid) { container.innerHTML = '<div class="card">Sélectionnez un projet pour consulter sa cohérence et son univers.</div>'; return; }
    container.innerHTML = '<div class="card">Chargement de la cohérence…</div>';
    let state, publication, project, canon;
    try {
        [state, publication, project] = await Promise.all([api.getCoherence(pid), api.getPublication(pid), api.getProject(pid)]);
        canon = project.universe_id ? await api.getCanon(project.universe_id) : {assertions: []};
    } catch (error) {
        if (current === generation) container.innerHTML = `<div class="card">Chargement impossible : ${escapeHtml(error.message)}. Aucune action de publication disponible.</div>`;
        return;
    }
    if (current !== generation || pid !== store.state.activeProjectId) return;
    const published = publication.publication_status === 'published';
    const report = state.report || {};
    const problems = report.issues || report.errors || [];
    const proposals = state.proposals || [];
    const blocked = publicationBlocked(state, publication);
    container.innerHTML = `
      <div class="card"><div class="card-title">Cohérence, univers et publication</div>
        <p>Univers obligatoire : <strong>${escapeHtml(project.universe_id || 'Migration requise')}</strong> · Révision ${escapeHtml(canon.revision || '—')}</p>
        <p><span class="badge">${published ? 'Publié · lecture seule' : 'Brouillon'}</span> <span class="badge">${escapeHtml(analysisLabel(state.status))}</span></p>
        <p>${state.auto_enabled ? 'Après sauvegarde : analyse incrémentale regroupée en arrière-plan.' : 'Suivi automatique désactivé jusqu’à la première analyse manuelle.'}</p>
        <p>Les analyses utilisent votre fournisseur IA et peuvent être payantes. Une absence d’erreurs détectées ne garantit pas la cohérence absolue.</p>
        <button id="coherence-analyze" class="btn btn-primary">Analyser tout le roman</button>
        <button id="coherence-review" class="btn">Demander une révision argumentée d’un faux positif</button>
        ${published ? '<p>Publication irréversible : seules les corrections de forme contrôlées restent possibles depuis Fichiers.</p>' : `<button id="publish-project" class="btn btn-danger" ${blocked ? 'disabled' : ''}>Publier définitivement</button><p>Publication bloquée si analyse incomplète/périmée, propositions non validées ou contradictions restantes.</p>`}
        <p id="coherence-message" role="status"></p>
      </div>
      <div class="card"><div class="card-title">Ajouts proposés à l’univers</div>
        <p>Aucun fait n’est effacé. Les croyances et rumeurs restent attribuées à leurs personnages et à leur époque.</p>
        ${proposals.length ? `<form id="assertions-form">${proposals.map((item, index) => `<label style="display:block"><input type="checkbox" name="assertion" value="${index}" checked> ${escapeHtml(item.text || item.statement || item.content || JSON.stringify(item))}<small> ${escapeHtml(item.kind || item.type || '')} · ${escapeHtml(sourceText(item))}</small></label>`).join('')}<button class="btn btn-primary" type="submit" ${published ? 'disabled' : ''}>Valider les ajouts sélectionnés</button></form>` : '<p>Aucun ajout en attente.</p>'}
      </div>
      <div class="card"><div class="card-title">Rapport de cohérence</div>
        <p>Couverture : ${escapeHtml(typeof report.coverage === 'object' ? JSON.stringify(report.coverage) : report.coverage || (report.complete ? 'Complète' : 'Non confirmée'))}</p>
        ${report.limitations ? `<pre style="white-space:pre-wrap">${escapeHtml(typeof report.limitations === 'string' ? report.limitations : JSON.stringify(report.limitations, null, 2))}</pre>` : ''}
        ${problems.map(issue => `<article style="border-top:1px solid var(--border-color);padding:1rem 0"><strong>${escapeHtml(issue.severity || 'À vérifier')} — ${escapeHtml(issue.title || issue.description || issue.explanation || 'Incohérence')}</strong><pre style="white-space:pre-wrap">${escapeHtml(JSON.stringify(issue, null, 2))}</pre></article>`).join('') || '<p>Aucun problème listé. Vérifiez l’état et la couverture de l’analyse avant publication.</p>'}
        <button id="download-coherence" class="btn btn-secondary">Télécharger le rapport Markdown</button>
      </div>
      <div class="card"><div class="card-title">Registre de l’univers</div>
        <p>L’historique est additif. Le contenu publié et ses apports canoniques ne sont pas modifiables.</p>
        ${(canon.assertions || []).map(item => `<p><span class="badge">${item.canonical || item.canon ? 'Canon' : 'Non canonique'}</span> ${escapeHtml(item.text || item.statement || item.content || JSON.stringify(item))}<small> ${escapeHtml(sourceText(item))}</small></p>`).join('') || '<p>Univers non enrichi ou registre vide.</p>'}
      </div>`;
    const message = container.querySelector('#coherence-message');
    async function act(button, action) {
        button.disabled = true;
        message.textContent = 'Traitement en cours… Vous pouvez quitter cette vue ; aucune correction narrative n’est appliquée automatiquement.';
        try { await action(); if (current === generation) await renderCoherence(container); }
        catch (error) { if (current === generation) { message.textContent = error.message; button.disabled = false; } }
    }
    container.querySelector('#coherence-analyze').onclick = async event => {
        const button = event.currentTarget;
        try {
            const estimate = await api.estimateCoherence(pid);
            if (confirm(`Lancer l’analyse complète ? ${estimate.provider_calls} appel(s) fournisseur prévus, ${estimate.input_characters} caractères de contexte. Montant non garanti. Les futures sauvegardes déclencheront aussi des analyses payantes regroupées.`)) act(button, () => api.analyzeCoherence(pid, true));
        } catch (error) { message.textContent = error.message; }
    };
    container.querySelector('#coherence-review').onclick = event => {
        const rationale = prompt('Expliquez le faux positif avec les passages et sources qui le justifient. Une nouvelle analyse complète payante vérifiera cet argument, sans dérogation au canon.');
        if (rationale && confirm('Relancer une vérification complète payante avec cette justification ?')) act(event.currentTarget, () => api.reviewCoherence(pid, rationale));
    };
    const publish = container.querySelector('#publish-project');
    if (publish) publish.onclick = event => {
        if (confirm('Publication IRRÉVERSIBLE : le roman et ses apports deviennent canoniques. Seules les corrections de forme resteront autorisées. Confirmez-vous ?')) act(event.currentTarget, () => api.publishProject(pid));
    };
    const form = container.querySelector('#assertions-form');
    if (form) form.onsubmit = event => {
        event.preventDefault();
        const ids = [...form.querySelectorAll('input:checked')].map(input => proposals[Number(input.value)].id);
        if (!ids.length) { message.textContent = 'Sélectionnez au moins un ajout.'; return; }
        act(form.querySelector('button'), () => api.acceptAssertions(pid, state.analysis_id || report.analysis_id, ids));
    };
    container.querySelector('#download-coherence').onclick = () => {
        const text = report.markdown || state.report_markdown || `# Erreurs de cohérence\n\nÉtat : ${analysisLabel(state.status)}\n\n\`\`\`json\n${JSON.stringify(report, null, 2)}\n\`\`\`\n`;
        const url = URL.createObjectURL(new Blob([text], {type: 'text/markdown;charset=utf-8'}));
        const link = document.createElement('a'); link.href = url; link.download = 'coherence_errors.md'; link.click(); URL.revokeObjectURL(url);
    };
}

function sourceText(item) {
    const source = item.source || item.provenance || {};
    return typeof source === 'string' ? source : [source.project_id, source.file || source.filename, source.passage || source.quote].filter(Boolean).join(' · ');
}
