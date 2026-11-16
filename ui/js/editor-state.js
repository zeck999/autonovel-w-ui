// Independent editor state: safe to test without a browser or remote services.
let navigationGuard = null;
let dirtyCheck = null;
export function setNavigationGuard(guard, check = null) { navigationGuard = guard; dirtyCheck = check; }
export function clearNavigationGuard() { navigationGuard = null; dirtyCheck = null; }
export function hasUnsavedChanges() { return Boolean(dirtyCheck?.()); }
export function canLeaveEditor() { return !navigationGuard || navigationGuard(); }
export function draftKey(projectId, filename) {
    return `autonovel_draft:${encodeURIComponent(projectId)}:${encodeURIComponent(filename)}`;
}
export function canonicalChapterName(value) {
    const match = /^(?:ch|chapter)_(\d+)\.md$/i.exec(value.trim());
    if (!match || Number(match[1]) < 1) throw new Error('Nom attendu : ch_01.md (numéro positif).');
    return `ch_${String(Number(match[1])).padStart(2, '0')}.md`;
}
export function saveDraft(storage, key, content, original) {
    try {
        if (content === original) storage.removeItem(key);
        else storage.setItem(key, JSON.stringify({ content, original }));
    } catch { /* Storage may be unavailable; navigation protection remains active. */ }
}
export function readDraft(storage, key) {
    try { return JSON.parse(storage.getItem(key) || 'null'); } catch { return null; }
}
