import { api } from './api.js';

export function stageFrame(cues, index) {
    let background;
    const portraits = new Map();
    for (let i = 0; i <= index && i < cues.length; i++) {
        for (const action of cues[i].actions) {
            if (action.kind === 'bg') background = action.image;
            if (action.kind === 'emotion') portraits.set(action.char, action.image);
        }
    }
    const shake = cues[index]?.actions.filter(action => action.kind === 'shake').at(-1)?.intensity;
    return { background, portraits, shake, text: cues[index]?.text ?? '' };
}

export function mountStagePreview(panel, editor, projectId, isCurrent) {
    const find = selector => panel.querySelector(selector);
    const scene = find('.stage-scene');
    const backdrop = find('.stage-background');
    const portraits = find('.stage-portraits');
    const text = find('.stage-prose');
    const status = find('.stage-status');
    const warnings = find('.stage-warnings');
    const previous = find('.stage-previous');
    const next = find('.stage-next');
    let cues = [], index = 0, timer, generation = 0, frame = 0;
    const urls = new Set();
    function clearImages() {
        for (const url of urls) URL.revokeObjectURL(url);
        urls.clear();
        backdrop.replaceChildren();
        portraits.replaceChildren();
    }
    async function image(parent, filename, label, currentFrame) {
        try {
            const blob = await api.getStageAsset(projectId, filename);
            if (!isCurrent() || !panel.open || currentFrame !== frame) return;
            const source = URL.createObjectURL(blob);
            urls.add(source);
            const element = document.createElement('img');
            element.alt = label;
            element.src = source;
            parent.replaceChildren(element);
        } catch {
            if (isCurrent() && panel.open && currentFrame === frame) parent.textContent = `Image indisponible : ${filename}`;
        }
    }
    function render(playEffect = false) {
        const currentFrame = ++frame;
        clearImages();
        const state = stageFrame(cues, index);
        text.textContent = state.text;
        status.textContent = cues.length ? `${index + 1} / ${cues.length}` : 'Chapitre vide';
        previous.disabled = index <= 0;
        next.disabled = index >= cues.length - 1;
        scene.dataset.shake = '';
        if (playEffect && state.shake) {
            requestAnimationFrame(() => {
                if (currentFrame === frame) scene.dataset.shake = state.shake;
            });
        }
        if (state.background) image(backdrop, state.background, 'Décor', currentFrame);
        for (const [character, filename] of state.portraits) {
            const slot = document.createElement('div');
            portraits.append(slot);
            image(slot, filename, character, currentFrame);
        }
    }
    function schedule() {
        clearTimeout(timer);
        const request = ++generation;
        if (!panel.open || !isCurrent()) {
            ++frame;
            clearImages();
            return;
        }
        timer = setTimeout(async () => {
            try {
                const result = await api.previewStage(projectId, editor.value);
                if (!isCurrent() || !panel.open || request !== generation) return;
                cues = result.cues;
                index = Math.min(index, Math.max(0, cues.length - 1));
                warnings.textContent = result.warnings.map(warning => `Ligne ${warning.line} : ${warning.message}`).join('\n');
                render();
            } catch (error) {
                if (!isCurrent() || !panel.open || request !== generation) return;
                cues = [];
                index = 0;
                warnings.textContent = '';
                render();
                status.textContent = `Aperçu indisponible : ${error.message}`;
            }
        }, 300);
    }
    panel.addEventListener('toggle', schedule);
    editor.addEventListener('input', schedule);
    previous.addEventListener('click', () => { if (index > 0) { index--; render(); } });
    next.addEventListener('click', () => { if (index + 1 < cues.length) { index++; render(true); } });
    const dispose = () => {
        clearTimeout(timer);
        ++generation;
        ++frame;
        clearImages();
        window.removeEventListener('autonovel-navigation', dispose);
    };
    window.addEventListener('autonovel-navigation', dispose);
    return dispose;
}
