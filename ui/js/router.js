/**
    ui/js/router.js — Hash-based SPA Router for Autonovel Web UI
 */

import { renderDashboard } from './views/dashboard.js';
import { renderProjects } from './views/projects.js';
import { renderUniverses } from './views/universes.js';
import { renderFiles } from './views/files.js';
import { renderBranches } from './views/branches.js';
import { renderPipeline } from './views/pipeline.js';
import { renderSettings } from './views/settings.js';

const routes = {
    '#/dashboard': renderDashboard,
    '#/assistant': renderProjects,
    '#/projects': renderProjects,
    '#/universes': renderUniverses,
    '#/files': renderFiles,
    '#/branches': renderBranches,
    '#/pipeline': renderPipeline,
    '#/settings': renderSettings,
    '#/': renderDashboard
};

export function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    
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
