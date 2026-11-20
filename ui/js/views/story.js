import { api } from '../api.js';
import { store } from '../store.js';
import { canLeaveEditor, clearNavigationGuard, setNavigationGuard } from '../editor-state.js';
import { layoutStory, parseStoryDraft } from '../story-graph.js';

const example = {
    start: 'chapters/ch_01.md', variables: { confiance: 0, cle: false },
    overrides: { 'chapters/ch_01.md': { confiance: 1 } },
    choices: [{ id: 'entrer', source: 'chapters/ch_01.md', target: 'chapters/ch_02.md',
        label: 'Ouvrir la porte', conditions: [{ variable: 'confiance', op: 'gte', value: 1 }], effects: { cle: true } }],
};

function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
}

function button(text, action, className = 'btn') {
    const node = element('button', text, className);
    node.type = 'button';
    node.addEventListener('click', action);
    return node;
}

function svgElement(tag, attrs) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
}

function drawStory(graph, host, details, openChapter) {
    host.replaceChildren();
    details.replaceChildren();
    if (!graph.nodes.length) {
        host.textContent = 'Aucun chapitre à afficher.';
        return;
    }
    const { positions, links, outgoing, width, height } = layoutStory(graph);
    const nodes = new Map(graph.nodes.map(node => [node.id, node]));
    const canvas = element('div', undefined, 'story-graph-canvas');
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    const svg = svgElement('svg', { width, height, 'aria-hidden': 'true' });
    const defs = svgElement('defs', {});
    const marker = svgElement('marker', { id: 'story-arrow', viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto' });
    marker.append(svgElement('path', { d: 'M 0 0 L 10 5 L 0 10 z', fill: 'currentColor' }));
    defs.append(marker);
    svg.append(defs);
    for (const edge of links) {
        const a = positions.get(edge.source), b = positions.get(edge.target);
        const leftToRight = b.x > a.x;
        let path;
        if (edge.source === edge.target) {
            path = `M${a.x + 130},${a.y} C${a.x + 185},${a.y - 31} ${a.x + 180},${a.y + 7} ${a.x + 165},${a.y + 16}`;
        } else if (a.x === b.x) {
            path = `M${a.x + 165},${a.y + 16} C${a.x + 205},${a.y + 16} ${b.x + 205},${b.y + 16} ${b.x + 165},${b.y + 16}`;
        } else {
            const ax = a.x + (leftToRight ? 165 : 0), bx = b.x + (leftToRight ? 0 : 165), mid = (ax + bx) / 2;
            path = `M${ax},${a.y + 16} C${mid},${a.y + 16} ${mid},${b.y + 16} ${bx},${b.y + 16}`;
        }
        svg.append(svgElement('path', { d: path, fill: 'none', stroke: 'currentColor', 'marker-end': 'url(#story-arrow)' }));
    }
    canvas.append(svg);
    const controls = new Map();
    function select(id) {
        const node = nodes.get(id);
        for (const [key, control] of controls) control.setAttribute('aria-pressed', String(key === id));
        const destinations = element('ul');
        for (const edge of outgoing.get(id)) {
            const item = element('li');
            item.append(button(`${edge.label} → ${nodes.get(edge.target).label}`, () => {
                select(edge.target);
                const target = controls.get(edge.target);
                target.focus();
                target.scrollIntoView({ block: 'nearest', inline: 'nearest' });
            }));
            destinations.append(item);
        }
        details.replaceChildren(element('h3', node.label), button('Ouvrir le chapitre', () => openChapter(id)),
            outgoing.get(id).length ? destinations : element('p', 'Aucun choix sortant.'));
    }
    for (const node of graph.nodes) {
        const { x, y } = positions.get(node.id);
        const control = button(`${node.id === graph.start ? 'Départ · ' : ''}${node.label}`, () => select(node.id), 'btn story-graph-node');
        control.title = node.id;
        control.style.left = `${x}px`;
        control.style.top = `${y}px`;
        controls.set(node.id, control);
        canvas.append(control);
    }
    host.append(canvas);
    select(controls.has(graph.start) ? graph.start : graph.nodes[0].id);
}

function drawHistory(history, host) {
    host.replaceChildren();
    if (!history.nodes.length) {
        host.textContent = 'Aucune révision Git disponible.';
        return;
    }
    const items = new Map();
    const list = element('ol', undefined, 'story-history');
    const visible = new Set(history.nodes.map(node => node.id));
    for (const node of history.nodes) {
        const item = element('li');
        const row = element('details');
        items.set(node.id, row);
        const refs = node.branches.length ? ` [${node.branches.join(', ')}]` : '';
        row.append(element('summary', `${node.id.slice(0, 9)} · ${node.label}${refs}`));
        const date = new Date(node.date);
        if (!Number.isNaN(date.valueOf())) row.append(element('p', date.toLocaleString('fr')));
        if (node.parents.length) {
            const parents = element('ul');
            for (const parent of node.parents) {
                const link = element('li');
                if (visible.has(parent)) link.append(button(`Parent ${parent.slice(0, 9)}`, () => {
                    const target = items.get(parent);
                    target.open = true;
                    target.querySelector('summary').focus();
                    target.scrollIntoView({ block: 'nearest' });
                }));
                else link.textContent = `Parent ${parent.slice(0, 9)} (hors de la fenêtre affichée)`;
                parents.append(link);
            }
            row.append(parents);
        } else row.append(element('p', 'Aucun parent.'));
        item.append(row);
        list.append(item);
    }
    if (history.truncated) host.append(element('p', 'Seules les révisions les plus récentes sont affichées.'));
    host.append(list);
}

export async function renderStory(container) {
    const projectId = store.state.activeProjectId;
    const root = element('div', undefined, 'story-view');
    container.replaceChildren(root);
    if (!projectId) {
        const link = element('a', 'Choisir un roman');
        link.href = '#/projects';
        root.append(element('h2', 'Parcours narratif'), link);
        return;
    }
    root.innerHTML = `
        <section class="card">
            <h2>Parcours narratif</h2>
            <p>Les variables sont propres à ce roman. Enregistre leur configuration pour mettre à jour le graphe et le test de lecture.</p>
            <form class="story-form">
                <label for="story-config">Variables, états par chapitre et choix (JSON)</label>
                <textarea id="story-config" class="form-control story-config" rows="15" spellcheck="false" readonly></textarea>
                <div class="story-actions">
                    <button type="submit" class="btn btn-primary" disabled>Enregistrer</button>
                    <button type="button" class="btn story-reload">Recharger la version enregistrée</button>
                </div>
            </form>
            <p role="status" class="story-edit-status">Chargement…</p>
            <details>
                <summary>Format et exemple</summary>
                <p><code>start</code> désigne le chapitre de départ (ou <code>null</code>). <code>variables</code> définit les valeurs initiales : booléens, nombres ou chaînes. <code>overrides</code> fixe des valeurs à l’entrée des chapitres listés.</p>
                <p>Chaque choix relie un chapitre source à un chapitre cible. Toutes ses conditions doivent être vraies : <code>eq</code> (=), <code>ne</code> (≠), <code>lt</code> (&lt;), <code>lte</code> (≤), <code>gt</code> (&gt;), <code>gte</code> (≥). <code>effects</code> fixe les nouvelles valeurs, puis la scène cible applique ses propres valeurs.</p>
                <pre class="story-example"></pre><p class="story-chapters"></p>
            </details>
        </section>
        <section class="card">
            <h2>Graphe des choix</h2>
            <p>Sélectionne un chapitre pour voir ses destinations ou ouvrir son manuscrit.</p>
            <p role="status" class="story-graph-status"></p>
            <div class="story-graph" tabindex="0" aria-label="Graphe des chapitres"></div>
            <div class="story-selection"></div>
        </section>
        <section class="card">
            <h2>Test de lecture</h2>
            <p>Simule les choix à partir de la configuration enregistrée, sans modifier le roman.</p>
            <button type="button" class="btn story-start" disabled>Depuis le début</button>
            <p role="status" class="story-play-status"></p>
            <div class="story-play"></div>
        </section>
        <section class="card">
            <h2>Chronologie des révisions Git</h2>
            <p>Les commits et leurs parents décrivent les versions du manuscrit, pas les choix du lecteur. Cette vue ne change pas de branche.</p>
            <div class="story-history-host"></div>
        </section>`;
    const find = (query) => root.querySelector(query);
    const form = find('.story-form');
    const editor = find('.story-config');
    const editStatus = find('.story-edit-status');
    const save = form.querySelector('button[type="submit"]');
    const reload = find('.story-reload');
    const graphStatus = find('.story-graph-status');
    const historyHost = find('.story-history-host');
    const restart = find('.story-start');
    const playHost = find('.story-play');
    const playStatus = find('.story-play-status');
    find('.story-example').textContent = JSON.stringify(example, null, 2);
    const current = () => root.isConnected && store.state.activeProjectId === projectId && window.location.hash === '#/story';
    let snapshot, saved = '', editing = false, playing = false, playGeneration = 0, graphGeneration = 0;
    const isDirty = () => Boolean(snapshot?.editable && editor.value !== saved);
    const sync = () => {
        save.disabled = !isDirty() || editing;
        reload.disabled = editing;
        editor.readOnly = editing || !snapshot?.editable;
    };
    function openChapter(path) {
        if (!current() || !snapshot?.chapters.includes(path) || !canLeaveEditor()) return;
        clearNavigationGuard();
        store.state.selectedProjectFile = path;
        window.location.hash = '#/files';
    }
    function updateSnapshot(response) {
        snapshot = response;
        saved = JSON.stringify(response.story, null, 2);
        editor.value = saved;
        editor.readOnly = !response.editable;
        find('.story-chapters').textContent = response.chapters.length ? `Chapitres disponibles : ${response.chapters.join(', ')}.` : 'Aucun chapitre disponible. Crée d’abord un chapitre dans Fichiers & Lore.';
        setNavigationGuard(() => !isDirty() || confirm('Quitter et abandonner les modifications non enregistrées du parcours ?'), isDirty);
        ++playGeneration;
        playing = false;
        restart.disabled = !response.chapters.length;
        playHost.replaceChildren();
        playStatus.textContent = '';
        sync();
    }
    async function refreshGraph() {
        const sequence = ++graphGeneration;
        graphStatus.textContent = 'Chargement…';
        try {
            const graph = await api.getStoryGraph(projectId);
            if (!current() || sequence !== graphGeneration) return;
            drawStory(graph.story, find('.story-graph'), find('.story-selection'), openChapter);
            drawHistory(graph.history, historyHost);
            graphStatus.textContent = '';
        } catch (error) {
            if (!current() || sequence !== graphGeneration) return;
            graphStatus.textContent = `Graphe indisponible : ${error.message}`;
            find('.story-graph').replaceChildren();
            find('.story-selection').replaceChildren();
            historyHost.replaceChildren();
        }
    }
    async function load() {
        editing = true;
        sync();
        try {
            const response = await api.getStory(projectId);
            if (!current()) return;
            updateSnapshot(response);
            editStatus.textContent = response.editable ? '' : 'Roman publié · configuration en lecture seule.';
            void refreshGraph();
        } catch (error) {
            if (current()) editStatus.textContent = `Chargement impossible : ${error.message}`;
        } finally {
            editing = false;
            if (current()) sync();
        }
    }
    reload.addEventListener('click', () => { if (canLeaveEditor()) void load(); });
    editor.addEventListener('input', sync);
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (!snapshot?.editable || editing || !isDirty()) return;
        let story;
        try { story = parseStoryDraft(editor.value); }
        catch (error) { editStatus.textContent = `JSON invalide : ${error.message}`; return; }
        editing = true;
        editor.readOnly = true;
        sync();
        try {
            const response = await api.saveStory(projectId, story, snapshot.revision);
            if (!current()) return;
            updateSnapshot(response);
            editStatus.textContent = 'Configuration enregistrée.';
            void refreshGraph();
        } catch (error) {
            if (current()) editStatus.textContent = error.status === 409
                ? 'La version enregistrée a changé. Copie tes modifications avant de recharger.' : `Enregistrement impossible : ${error.message}`;
        } finally {
            editing = false;
            if (current()) { editor.readOnly = !snapshot?.editable; sync(); }
        }
    });
    async function play(step) {
        if (playing || !current()) return;
        playing = true;
        const generation = ++playGeneration;
        playStatus.textContent = 'Évaluation des choix…';
        const choiceButtons = [...playHost.querySelectorAll('.story-choice')];
        for (const option of choiceButtons) option.disabled = true;
        restart.disabled = true;
        try {
            const result = await api.stepStory(projectId, step);
            if (!current() || generation !== playGeneration) return;
            playHost.replaceChildren(element('h3', result.chapter), button('Ouvrir le chapitre', () => openChapter(result.chapter)),
                element('pre', JSON.stringify(result.values, null, 2), 'story-example'));
            const choices = element('ul');
            for (const choice of result.choices) {
                const item = element('li');
                item.append(button(`${choice.label} → ${choice.target}`, () => play({ chapter: result.chapter, values: result.values, choice_id: choice.id }), 'btn story-choice'));
                choices.append(item);
            }
            playHost.append(result.choices.length ? choices : element('p', 'Aucun choix disponible avec cet état.'));
            playStatus.textContent = `Chapitre courant : ${result.chapter}`;
        } catch (error) {
            if (current() && generation === playGeneration) playStatus.textContent = `Test de lecture impossible : ${error.message}`;
        } finally {
            if (current() && generation === playGeneration) {
                playing = false;
                restart.disabled = false;
                for (const option of choiceButtons) option.disabled = false;
            }
        }
    }
    restart.addEventListener('click', () => {
        const chapter = snapshot?.story.start ?? snapshot?.chapters[0];
        if (chapter) void play({ chapter });
    });
    await load();
}
