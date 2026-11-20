/**
    ui/js/router.js — Hash-based SPA Router for Autonovel Web UI
 */

import { canLeaveEditor, clearNavigationGuard, hasUnsavedChanges } from './editor-state.js';
import { renderDashboard } from './views/dashboard.js';
import { renderProjects } from './views/projects.js';
import { renderUniverses } from './views/universes.js';
import { renderFiles } from './views/files.js';
import { renderBranches } from './views/branches.js';
import { renderStory } from './views/story.js';
import { renderPipeline } from './views/pipeline.js';
import { renderCoherence } from './views/coherence.js';
import { renderSettings } from './views/settings.js';

let currentHash = null;
let restoringHash = false;

const routes = {
    '#/dashboard': renderDashboard,
    '#/assistant': renderProjects,
    '#/projects': renderProjects,
    '#/universes': renderUniverses,
    '#/files': renderFiles,
    '#/branches': renderBranches,
    '#/story': renderStory,
    '#/pipeline': renderPipeline,
    '#/settings': renderSettings,
    '#/coherence': renderCoherence,
    '#/': renderDashboard
};

export function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    window.addEventListener('beforeunload', event => {
        if (hasUnsavedChanges()) { event.preventDefault(); event.returnValue = ''; }
    });
    
    // Mobile hamburger menu toggle
    const hamburger = document.getElementById('hamburger-toggle');
    const nav = document.querySelector('nav.main-nav');
    if (hamburger && nav) {
        hamburger.addEventListener('click', () => {
            nav.classList.toggle('open');
        });
    }

    handleRoute();
}

export function navigate(hash) {
    window.location.hash = hash;
}

function handleRoute() {
    const hash = window.location.hash || '#/dashboard';
    if (restoringHash) { restoringHash = false; return; }
    if (currentHash !== null && !canLeaveEditor()) {
        restoringHash = true;
        window.location.hash = currentHash;
        return;
    }
    clearNavigationGuard();
    window.dispatchEvent(new Event('autonovel-navigation'));
    currentHash = hash;
    const viewRenderer = routes[hash] || renderDashboard;
    
    // Update active nav links
    document.querySelectorAll('nav.main-nav a').forEach(a => {
        if (a.getAttribute('href') === hash) {
            a.classList.add('active');
        } else {
            a.classList.remove('active');
        }
    });

    // Close mobile nav if open
    const nav = document.querySelector('nav.main-nav');
    if (nav) {
        nav.classList.remove('open');
    }

    const container = document.getElementById('app-content');
    if (container) {
        container.innerHTML = '';
        viewRenderer(container);
    }
}
