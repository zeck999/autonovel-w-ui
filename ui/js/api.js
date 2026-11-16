/**
    ui/js/api.js — Asynchronous API client for Autonovel Web UI
 */

const API_BASE = '/api';

let authenticationPrompt = null;
const activeOperations = new Map();
const pendingJobsKey = 'autonovel_pending_jobs';
function token() { return sessionStorage.getItem('autonovel_token'); }
async function authenticate() {
    if (!authenticationPrompt) authenticationPrompt = Promise.resolve().then(() => {
        const value = window.prompt('Ce serveur exige un jeton d’accès. Saisissez le jeton fourni par son administrateur :');
        if (value?.trim()) sessionStorage.setItem('autonovel_token', value.trim());
        return Boolean(value?.trim());
    }).finally(() => { authenticationPrompt = null; });
    return authenticationPrompt;
}
async function request(endpoint, options = {}, retryAuthentication = true) {
    const controller = new AbortController();
    const { timeoutMs = 30000, ...fetchOptions } = options;
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...fetchOptions,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
                ...(fetchOptions.headers || {})
            }
        });
        if (response.status === 401 && retryAuthentication) {
            sessionStorage.removeItem('autonovel_token');
            if (await authenticate()) return request(endpoint, options, false);
        }
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            const message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || data.error || '');
            const error = new Error(message || `API Error: ${response.status}`);
            error.status = response.status;
            throw error;
        }
        return response.status === 204 ? null : await response.json();
    } finally { clearTimeout(timeoutId); }
}
function pendingJobs() {
    try { return JSON.parse(sessionStorage.getItem(pendingJobsKey) || '{}'); } catch { return {}; }
}
function rememberJob(key, id) {
    const jobs = pendingJobs();
    if (id) jobs[key] = id; else delete jobs[key];
    sessionStorage.setItem(pendingJobsKey, JSON.stringify(jobs));
    if (!id) {
        let keys;
        try { keys = JSON.parse(sessionStorage.getItem('autonovel_request_keys') || '{}'); } catch { keys = {}; }
        delete keys[key];
        sessionStorage.setItem('autonovel_request_keys', JSON.stringify(keys));
    }
}
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
async function followJob(id, onProgress) {
    let lastError;
    let failures = 0;
    for (;;) {
        let job;
        try { job = await request(`/jobs/${encodeURIComponent(id)}`); failures = 0; }
        catch (error) {
            lastError = error;
            if ([401, 403, 404].includes(error.status) || ++failures >= 5) {
                throw new Error(`Suivi interrompu (tâche ${id}). La tâche peut continuer sur le serveur ; réessayez pour reprendre son suivi. ${lastError.message}`);
            }
            await pause(2000);
            continue;
        }
        onProgress?.(job);
        window.dispatchEvent(new CustomEvent('autonovel-job', { detail: job }));
        if (job.status === 'succeeded') return job.result;
        if (job.status === 'failed') {
            const error = new Error(typeof job.error === 'string' ? job.error : JSON.stringify(job.error || 'La tâche a échoué.'));
            error.jobFinished = true;
            throw error;
        }
        await pause(1000);
    }
}
async function runOperation(endpoint, payload, onProgress) {
    // A repeated click shares the existing promise; reconnects reuse the known job.
    const key = `${endpoint}:${JSON.stringify(payload)}`;
    if (activeOperations.has(key)) return activeOperations.get(key);
    const operation = (async () => {
        let id = pendingJobs()[key];
        if (!id) {
            let requestKeys;
            try { requestKeys = JSON.parse(sessionStorage.getItem('autonovel_request_keys') || '{}'); } catch { requestKeys = {}; }
            requestKeys[key] ||= globalThis.crypto.randomUUID();
            sessionStorage.setItem('autonovel_request_keys', JSON.stringify(requestKeys));
            const job = await request(endpoint, {
                method: 'POST', body: JSON.stringify(payload),
                headers: { 'Idempotency-Key': requestKeys[key] }
            });
            id = job.id;
            if (!id) throw new Error('Réponse invalide : identifiant de tâche manquant.');
            rememberJob(key, id);
        }
        try {
            const result = await followJob(id, onProgress);
            rememberJob(key, null);
            return result;
        } catch (error) {
            if (error.jobFinished) rememberJob(key, null);
            throw error;
        }
    })();
    activeOperations.set(key, operation);
    try { return await operation; } finally { activeOperations.delete(key); }
}

export const api = {
    async listProjects() {
        return request('/projects');
    },

    async createProject(payload) {
        return request('/projects', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async wizardSuggest(payload) {
        return request('/projects/wizard/suggest', {
            timeoutMs: 650000,
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async wizardCreate(payload) {
        return request('/projects/wizard/create', {
            timeoutMs: 650000,
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async getProject(projectId) {
        return request(`/projects/${projectId}`);
    },

    async deleteProject(projectId) {
        return request(`/projects/${projectId}`, {
            method: 'DELETE'
        });
    },

    async listProjectFiles(projectId) {
        return request(`/projects/${projectId}/files`);
    },

    async getProjectFile(projectId, filename) {
        return request(`/projects/${projectId}/files/${encodeURIComponent(filename)}`);
    },

    async saveProjectFile(projectId, filename, content, expectedContent) {
        return request(`/projects/${projectId}/files/${encodeURIComponent(filename)}`, {
            method: 'PUT',
            body: JSON.stringify({ content, ...(expectedContent !== undefined ? { expected_content: expectedContent } : {}) })
        });
    },

    async listUniverses() {
        return request('/universes');
    },

    async createUniverse(payload) {
        return request('/universes', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async getUniverse(universeId) {
        return request(`/universes/${universeId}`);
    },

    async deleteUniverse(universeId) {
        return request(`/universes/${universeId}`, {
            method: 'DELETE'
        });
    },

    async listBranches(projectId = null) {
        const query = projectId ? `?project_id=${projectId}` : '';
        return request(`/versioning/branches${query}`);
    },

    async createBranch(payload) {
        return request('/versioning/branches', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async switchBranch(payload) {
        return request('/versioning/switch', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async getHistory(chapterNum = null, projectId = null) {
        const params = new URLSearchParams();
        if (chapterNum !== null) params.append('chapter_num', chapterNum);
        if (projectId) params.append('project_id', projectId);
        const query = params.toString() ? `?${params.toString()}` : '';
        return request(`/versioning/history${query}`);
    },

    async getPipelineStatus(projectId = null) {
        const query = projectId ? `?project_id=${projectId}` : '';
        return request(`/pipeline/status${query}`);
    },

    async runPipelinePhase(payload) {
        return runOperation('/pipeline/run', payload);
    },

    async evaluateProject(payload) {
        return runOperation('/pipeline/evaluate', payload);
    },

    async getLatestReview() {
        const { store } = await import('./store.js');
        if (!store.state.activeProjectId) return {has_review: false};
        return request(`/reviews/latest?project_id=${encodeURIComponent(store.state.activeProjectId)}`);
    },
    async getSettingsKeys() {
        return request('/settings/keys');
    },

    async updateSettingsKeys(payload) {
        return request('/settings/keys', {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    },

    async testSettingsKey(payload) {
        return request('/settings/keys/test', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async modifyChapterWithAI(projectId, filePath, content, prompt, onProgress) {
        return runOperation(`/projects/${projectId}/chapters/modify`,
            { file_path: filePath, content, prompt }, onProgress);
    }
};