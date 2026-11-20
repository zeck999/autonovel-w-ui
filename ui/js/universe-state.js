export function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
}

export function analysisLabel(status) {
    return ({not_analyzed:'Univers non analysé', unanalysed:'Univers non analysé', pending:'À vérifier', stale:'À vérifier', queued:'En attente', running:'Analyse en cours', awaiting_validation:'Ajouts à valider', pending_review:'Ajouts à valider', current:'À jour', up_to_date:'À jour', failed:'Échec'})[status] || status || 'Univers non analysé';
}

export function publicationBlocked(state, publication) {
    if (publication.publication_status === 'published') return true;
    // Backend is authoritative; UI deliberately fails closed on missing information.
    if (state.can_publish === true) return false;
    const report = state.report || {};
    const issues = report.issues || report.errors || [];
    return !['current', 'up_to_date'].includes(state.status) || report.complete !== true || (state.proposals || []).length > 0 || issues.some(issue => issue.blocking !== false && issue.resolved !== true);
}
