/**
    ui/js/views/pipeline.js — Pipeline Orchestration & Monitoring View
 */

import { store } from '../store.js';
import { api } from '../api.js';

export function renderPipeline(container) {
    const state = store.state;
    const pid = state.activeProjectId;
    const pipeline = state.pipelineStatus || {};

    const phases = [
        { id: 'foundation', name: '1. Foundation', desc: 'Generate world, characters, canon, and brief.' },
        { id: 'outline', name: '2. Outline', desc: 'Build chapter outlines and arc summary.' },
        { id: 'draft', name: '3. Draft', desc: 'Draft chapters iteratively.' },
        { id: 'review', name: '4. Review & Judge', desc: 'Evaluate novel with AI critic and score chapters.' },
        { id: 'revise', name: '5. Revise', desc: 'Apply editorial cuts and adversarial edits.' },
        { id: 'typeset', name: '6. Typeset', desc: 'Compile LaTeX manuscript and ePub.' },
        { id: 'audiobook', name: '7. Audiobook', desc: 'Generate audiobook script and voice assets.' }
    ];

    container.innerHTML = `
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Run Pipeline Phase</div>
                <form id="pipeline-run-form">
                    <div class="form-group">
                        <label class="form-label" for="pipeline-phase-select">Select Phase</label>
                        <select id="pipeline-phase-select" class="form-control" required>
                            ${phases.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label" for="pipeline-cycles">Max Cycles (optional)</label>
                        <input type="number" id="pipeline-cycles" class="form-control" min="1" max="10" placeholder="Default">
                    </div>
                    <button type="submit" class="btn btn-primary" id="run-phase-btn">Execute Phase</button>
                </form>
            </div>

            <div class="card">
                <div class="card-title">Project Evaluation</div>
                <p style="color: var(--text-muted); margin-bottom: 1.5rem;">
                    Trigger an independent AI literary evaluation on the current project or chapter.
                </p>
                <form id="pipeline-eval-form">
                    <div class="form-group">
                        <label class="form-label" for="eval-chapter">Chapter Number (optional)</label>
                        <input type="number" id="eval-chapter" class="form-control" min="1" placeholder="All chapters if empty">
                    </div>
                    <button type="submit" class="btn">Run Evaluation</button>
                </form>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Pipeline Status (${escapeHtml(pid || 'Global/Default')})</div>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
                <span class="badge badge-success">Phase: ${escapeHtml(pipeline.phase || 'idle')}</span>
                <span class="badge">Iteration: ${escapeHtml(String(pipeline.iteration || 0))}</span>
                <span class="badge">Score: ${escapeHtml(String(pipeline.score || 0.0))}</span>
            </div>

            <h3 style="font-family: var(--font-display); font-size: 1.3rem; color: var(--accent); margin-bottom: 0.75rem; text-transform: uppercase;">Phases Overview</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Phase</th>
                            <th>Description</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${phases.map(p => `
                            <tr>
                                <td><strong>${escapeHtml(p.name)}</strong></td>
                                <td>${escapeHtml(p.desc)}</td>
                                <td>
                                    <button class="btn btn-sm ${pipeline.phase === p.id ? 'btn-primary' : ''}" data-run-phase="${p.id}">
                                        Run
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Run form submission
    const runForm = document.getElementById('pipeline-run-form');
    if (runForm) {
        runForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const phase = document.getElementById('pipeline-phase-select').value;
            const cyclesVal = document.getElementById('pipeline-cycles').value;
            const maxCycles = cyclesVal ? parseInt(cyclesVal, 10) : null;
            const btn = document.getElementById('run-phase-btn');

            try {
                btn.disabled = true;
                btn.textContent = 'Executing...';
                await api.runPipelinePhase({
                    phase,
                    project_id: pid,
                    max_cycles: maxCycles
                });
                await store.refreshActiveProjectData();
                alert(`Pipeline phase '${phase}' executed successfully!`);
                renderPipeline(container);
            } catch (err) {
                alert(`Pipeline error: ${err.message}`);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Execute Phase';
            }
        });
    }

    // Evaluation form
    const evalForm = document.getElementById('pipeline-eval-form');
    if (evalForm) {
        evalForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const chVal = document.getElementById('eval-chapter').value;
            const chapterNum = chVal ? parseInt(chVal, 10) : null;

            try {
                const res = await api.evaluateProject({
                    project_id: pid,
                    chapter_num: chapterNum
                });
                await store.refreshActiveProjectData();
                alert(`Evaluation completed. Score: ${res.score || 'N/A'}`);
                renderPipeline(container);
            } catch (err) {
                alert(`Evaluation error: ${err.message}`);
            }
        });
    }

    // Table Run buttons
    container.querySelectorAll('[data-run-phase]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const phase = e.target.getAttribute('data-run-phase');
            try {
                e.target.disabled = true;
                e.target.textContent = '...';
                await api.runPipelinePhase({
                    phase,
                    project_id: pid
                });
                await store.refreshActiveProjectData();
                alert(`Phase '${phase}' completed.`);
                renderPipeline(container);
            } catch (err) {
                alert(`Error running phase ${phase}: ${err.message}`);
            } finally {
                e.target.disabled = false;
                e.target.textContent = 'Run';
            }
        });
    });
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
