/**
    ui/js/api.js — Asynchronous API client for Autonovel Web UI
 */

const API_BASE = '/api';

async function request(endpoint, options = {}) {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API request failed [${endpoint}]:`, error);
        throw error;
    }
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

    async saveProjectFile(projectId, filename, content) {
        return request(`/projects/${projectId}/files/${encodeURIComponent(filename)}`, {
            method: 'PUT',
            body: JSON.stringify({ content })
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
        return request('/pipeline/run', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    async evaluateProject(payload) {
        return request('/pipeline/evaluate', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }
};
