import test from 'node:test';
import assert from 'node:assert/strict';
import { layoutStory, parseStoryDraft } from '../js/story-graph.js';
import { api } from '../js/api.js';

test('story layout keeps cycles, self-loops, convergent routes and unreachable chapters', () => {
    const nodes = ['a', 'b', 'c', 'd', 'unused'].map(id => ({ id }));
    const edges = [['a', 'b'], ['a', 'c'], ['b', 'd'], ['c', 'd'], ['d', 'a'], ['d', 'd'], ['b', 'absent']]
        .map(([source, target]) => ({ source, target }));
    const { positions, links, outgoing, width, height } = layoutStory({ nodes, edges, start: 'a' });
    assert.equal(links.length, 6);
    assert.equal(outgoing.get('d').length, 2);
    assert.equal(positions.get('b').x, positions.get('c').x);
    assert.notEqual(positions.get('b').y, positions.get('c').y);
    assert.ok(positions.get('unused').x > positions.get('d').x);
    for (const { x, y } of positions.values()) assert.ok(x < width && y < height);
    assert.equal(layoutStory({ nodes: [], edges: [], start: null }).positions.size, 0);
});

test('story draft preserves typed variables and rejects non-object input', () => {
    const story = { start: null, variables: { flag: false, count: 0, name: '' }, overrides: {}, choices: [] };
    assert.deepEqual(parseStoryDraft(JSON.stringify(story)), story);
    for (const text of ['[]', 'null', '1', '{']) assert.throws(() => parseStoryDraft(text));
});

test('story client reads graph and state, submits revision guard and simulates without a PUT', async t => {
    const requests = [];
    t.mock.method(globalThis, 'fetch', async (url, options) => {
        requests.push([url, options.method ?? 'GET', options.body && JSON.parse(options.body)]);
        return { ok: true, status: 200, json: async () => ({}) };
    });
    const previous = globalThis.sessionStorage;
    globalThis.sessionStorage = { getItem: () => null };
    t.after(() => { if (previous === undefined) delete globalThis.sessionStorage; else globalThis.sessionStorage = previous; });
    const id = 'novel 1', base = '/api/projects/novel%201/story';
    const story = { start: 'chapters/ch_01.md', variables: {}, overrides: {}, choices: [] };
    const step = { chapter: story.start, values: { flag: false }, choice_id: 'a' };
    await api.getStory(id);
    await api.saveStory(id, story, 'rev1');
    await api.stepStory(id, step);
    await api.getStoryGraph(id);
    assert.deepEqual(requests, [
        [base, 'GET', undefined], [base, 'PUT', { story, expected_revision: 'rev1' }],
        [`${base}/step`, 'POST', step], [`${base}/graph`, 'GET', undefined],
    ]);
});
