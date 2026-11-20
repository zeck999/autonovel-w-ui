import test from 'node:test';
import assert from 'node:assert/strict';
import { stageFrame } from '../js/stage-preview.js';

test('stage navigation reconstructs persistent visuals without replaying past effects', () => {
    const cues = [
        { text: 'Intro', actions: [{ kind: 'bg', image: 'forest.png' }, { kind: 'emotion', char: 'Elena', image: 'calm.png' }] },
        { text: 'Orage', actions: [{ kind: 'shake', intensity: 'high' }, { kind: 'emotion', char: 'Elena', image: 'fear.png' }] },
        { text: 'Après', actions: [] },
    ];
    assert.equal(stageFrame(cues, 1).shake, 'high');
    assert.deepEqual(stageFrame(cues, 2), { background: 'forest.png', portraits: new Map([['Elena', 'fear.png']]), shake: undefined, text: 'Après' });
    assert.equal(stageFrame(cues, 0).portraits.get('Elena'), 'calm.png');
    assert.equal(stageFrame([], 0).text, '');
});
