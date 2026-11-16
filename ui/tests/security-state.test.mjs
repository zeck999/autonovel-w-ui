import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalChapterName, draftKey, saveDraft, readDraft, setNavigationGuard, canLeaveEditor, clearNavigationGuard } from '../js/editor-state.js';

function storage() {
    const values = new Map();
    return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
}

test('chapter names use the pipeline convention, reject paths and invalid names', () => {
    assert.equal(canonicalChapterName('chapter_1.md'), 'ch_01.md');
    assert.equal(canonicalChapterName('ch_12.md'), 'ch_12.md');
    for (const name of ['../ch_01.md', 'ch_00.md', 'world.md', 'x;rm.md']) assert.throws(() => canonicalChapterName(name));
});
test('drafts are scoped by project/file and removed only when equal to saved text', () => {
    const local = storage();
    const first = draftKey('one', 'chapters/ch_01.md');
    const second = draftKey('two', 'chapters/ch_01.md');
    saveDraft(local, first, 'new text', 'saved');
    assert.deepEqual(readDraft(local, first), { content: 'new text', original: 'saved' });
    assert.equal(readDraft(local, second), null);
    saveDraft(local, first, 'new text', 'new text');
    assert.equal(readDraft(local, first), null);
});
test('navigation respects the editor guard and cleanup', () => {
    setNavigationGuard(() => false);
    assert.equal(canLeaveEditor(), false);
    clearNavigationGuard();
    assert.equal(canLeaveEditor(), true);
});
test('API follows background job and concurrent repeated clicks create a single request', async () => {
    globalThis.sessionStorage = storage();
    sessionStorage.setItem('autonovel_token', 'test-only');
    globalThis.window = { dispatchEvent() {}, prompt() { throw new Error('unexpected auth'); } };
    globalThis.CustomEvent = class { constructor(name, options) { this.type = name; this.detail = options.detail; } };
    const calls = [];
    globalThis.fetch = async (url, options) => {
        calls.push([url, options]);
        if (url === '/api/pipeline/run') return new Response(JSON.stringify({ id: 'job-test', status: 'queued' }), { status: 202 });
        assert.equal(url, '/api/jobs/job-test');
        return new Response(JSON.stringify({ id: 'job-test', status: 'succeeded', result: { phase: 'foundation' } }), { status: 200 });
    };
    const { api } = await import('../js/api.js');
    const results = await Promise.all([api.runPipelinePhase({ project_id: 'demo', phase: 'foundation' }), api.runPipelinePhase({ project_id: 'demo', phase: 'foundation' })]);
    assert.deepEqual(results[0], { phase: 'foundation' });
    assert.deepEqual(results[1], results[0]);
    assert.equal(calls.filter(([url]) => url === '/api/pipeline/run').length, 1);
    assert.equal(calls[0][1].headers.Authorization, 'Bearer test-only');
    assert.ok(calls[0][1].headers['Idempotency-Key']);
    assert.equal(sessionStorage.getItem('autonovel_pending_jobs'), '{}');
    await api.saveProjectFile('demo', 'chapters/ch_01.md', 'next', 'original').catch(() => {});
    const saved = calls.at(-1);
    assert.deepEqual(JSON.parse(saved[1].body), { content: 'next', expected_content: 'original' });
});
