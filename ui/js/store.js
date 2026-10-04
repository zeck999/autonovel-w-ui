/**
    ui/js/store.js — Reactive state store for Autonovel Web UI
 */

import { api } from './api.js';

class Store {
    constructor() {
        this.state = {
            activeProjectId: localStorage.getItem('autonovel_active_project') || null,
            projects: [],
            universes: [],
            branches: [],
            pipelineStatus: { phase: 'idle', iteration: 0, score: 0.0, logs: [] },
            history: [],
            isOnline: true,
            lastSync: null
        };
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify() {
        for (const listener of this.listeners) {
            listener(this.state);
        }
    }

    setActiveProject(projectId) {
        this.state.activeProjectId = projectId;
        if (projectId) {
            localStorage.setItem('autonovel_active_project', projectId);
        } else {
            localStorage.removeItem('autonovel_active_project');
        }
        this.notify();
        this.refreshActiveProjectData();
    }

    async init() {
        await this.refreshGlobalData();
    }

    async refreshGlobalData() {
        try {
            const [projects, universes] = await Promise.all([
                api.listProjects(),
                api.listUniverses()
            ]);
            
            this.state.projects = projects;
            this.state.universes = universes;
            this.state.isOnline = true;
            this.state.lastSync = new Date();

            // Validate active project exists
            if (this.state.activeProjectId && !projects.some(p => p.id === this.state.activeProjectId)) {
                this.state.activeProjectId = projects.length > 0 ? projects[0].id : null;
                if (this.state.activeProjectId) {
                    localStorage.setItem('autonovel_active_project', this.state.activeProjectId);
                } else {
                    localStorage.removeItem('autonovel_active_project');
                }
            } else if (!this.state.activeProjectId && projects.length > 0) {
                this.state.activeProjectId = projects[0].id;
                localStorage.setItem('autonovel_active_project', this.state.activeProjectId);
            }

            await this.refreshActiveProjectData();
        } catch (error) {
            console.error("Failed to refresh global state:", error);
            this.state.isOnline = false;
        }
        this.notify();
    }

    async refreshActiveProjectData() {
        const pid = this.state.activeProjectId;
        try {
            const [branches, pipelineStatus, history] = await Promise.all([
                api.listBranches(pid),
                api.getPipelineStatus(pid),
                api.getHistory(null, pid)
            ]);
            this.state.branches = branches;
            this.state.pipelineStatus = pipelineStatus;
            this.state.history = history;
            this.state.isOnline = true;
        } catch (error) {
            console.error("Failed to refresh active project data:", error);
            this.state.isOnline = false;
        }
        this.notify();
    }
}

export const store = new Store();
