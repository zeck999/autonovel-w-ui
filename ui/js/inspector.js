/**
    ui/js/inspector.js — Collapsible Inspector Drawer & Live Logs Component
 */

import { store } from './store.js';

export function initInspector() {
    const drawer = document.getElementById('inspector-drawer');
    const toggleBtn = document.getElementById('inspector-toggle');
    const closeBtn = document.getElementById('inspector-close');

    if (!drawer || !toggleBtn) return;

    function toggleInspector() {
        drawer.classList.toggle('open');
    }

    toggleBtn.addEventListener('click', toggleInspector);
    if (closeBtn) closeBtn.addEventListener('click', toggleInspector);

    // Keyboard shortcut: Alt+I or Esc to close
    window.addEventListener('keydown', (e) => {
        if (e.altKey && e.key.toLowerCase() === 'i') {
            e.preventDefault();
            toggleInspector();
        } else if (e.key === 'Escape' && drawer.classList.contains('open')) {
            drawer.classList.remove('open');
        }
    });

    // Subscribe to store to update logs and metadata
    store.subscribe(state => {
        updateInspectorContent(state);
    });

    updateInspectorContent(store.state);
}

function updateInspectorContent(state) {
    const logsContainer = document.getElementById('inspector-logs');
    const metaContainer = document.getElementById('inspector-meta');
    
    if (!logsContainer || !metaContainer) return;

    const pipeline = state.pipelineStatus || {};
    const logs = pipeline.logs || [];

    if (logs.length === 0) {
        logsContainer.innerHTML = '<div class="log-line info">[System] No active pipeline logs. Ready.</div>';
    } else {
        logsContainer.innerHTML = logs.map(line => {
            let className = 'log-line';
            const lower = line.toLowerCase();
            if (lower.includes('error') || lower.includes('fail') || lower.includes('exception')) {
                className += ' error';
            } else if (lower.includes('success') || lower.includes('completed') || lower.includes('passed')) {
                className += ' success';
            } else if (lower.includes('info') || lower.includes('running')) {
                className += ' info';
            }
            return `<div class="${className}">${escapeHtml(line)}</div>`;
        }).join('');
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    metaContainer.innerHTML = `
        <div><strong>Active Project ID:</strong> ${escapeHtml(state.activeProjectId || 'None')}</div>
        <div><strong>Current Phase:</strong> ${escapeHtml(pipeline.phase || 'idle')}</div>
        <div><strong>Current Iteration:</strong> ${escapeHtml(String(pipeline.iteration || 0))}</div>
        <div><strong>Score:</strong> ${escapeHtml(String(pipeline.score || 0.0))}</div>
        <div><strong>Status:</strong> ${state.isOnline ? 'Online' : 'Offline'}</div>
        <div><strong>Last Sync:</strong> ${state.lastSync ? state.lastSync.toLocaleTimeString() : 'Never'}</div>
    `;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
