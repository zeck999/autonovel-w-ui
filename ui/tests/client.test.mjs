import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalChapterName, draftKey, saveDraft, readDraft, setNavigationGuard, canLeaveEditor, clearNavigationGuard } from '../js/editor-state.js';

const memoryStorage = () => {
    const values = new Map();
    return { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
};
globalThis.sessionStorage = memoryStorage();
globalThis.window = { dispatchEvent() {}, prompt() { return 'test-token'; } };
globalThis.CustomEvent = class { constructor(type, options) { this.type = type; this.detail = options.detail; } };
const { api } = await import('../js/api.js');
const response = (value, status = 200) => ({ ok: status < 400, status, json: async () => value });

test('chapter names normalized and unsafe names rejected', () => {
    assert.equal(canonicalChapterName('chapter_1.md'), 'ch_01.md');
    assert.equal(canonicalChapterName('ch_123.md'), 'ch_123.md');
    for (const name of ['../ch_01.md', 'ch_00.md', 'other.md', 'ch_1.md/x']) assert.throws(() => canonicalChapterName(name));
});
test('drafts separated by project and filename and removed after save', () => {
    const storage = memoryStorage();
    const key = draftKey('project-a', 'chapters/ch_01.md');
    assert.notEqual(key, draftKey('project-b', 'chapters/ch_01.md'));
    saveDraft(storage, key, 'modified', 'original');
    assert.deepEqual(readDraft(storage, key), { content: 'modified', original: 'original' });
    saveDraft(storage, key, 'modified', 'modified');
    assert.equal(readDraft(storage, key), null);
});
test('navigation guard can reject without losing state', () => {
    setNavigationGuard(() => false);
    assert.equal(canLeaveEditor(), false);
    clearNavigationGuard();
    assert.equal(canLeaveEditor(), true);
});
test('job client deduplicates concurrent requests and returns final result', async () => {
    const calls = [];
    globalThis.fetch = async (url, options) => {
        calls.push([url, options]);
        return url.endsWith('/jobs/job-1') ? response({ id: 'job-1', status: 'succeeded', result: { score: 8.1 } }) : response({ id: 'job-1', status: 'queued' }, 202);
    };
    const payload = { phase: 'foundation', project_id: 'test-one' };
    const results = await Promise.all([api.runPipelinePhase(payload), api.runPipelinePhase(payload)]);
    assert.deepEqual(results, [{ score: 8.1 }, { score: 8.1 }]);
    assert.equal(calls.filter(([url]) => url.endsWith('/pipeline/run')).length, 1);
    assert.ok(calls[0][1].headers['Idempotency-Key']);
});
test('AI job request does not save a file automatically', async () => {
    const calls = [];
    globalThis.fetch = async (url, options) => {
        calls.push([url, options]);
        return url.includes('/jobs/') ? response({ id: 'ai-1', status: 'succeeded', result: { content: 'proposal', original_content: 'old' } }) : response({ id: 'ai-1', status: 'queued' }, 202);
    };
    assert.equal((await api.modifyChapterWithAI('p', 'chapters/ch_01.md', 'old', 'revise')).content, 'proposal');
    assert.equal(calls.some(([, options]) => options.method === 'PUT'), false);
    assert.equal(JSON.parse(calls[0][1].body).file_path, 'chapters/ch_01.md');
});
test('save transmits expected content and preserves 409 status', async () => {
    globalThis.fetch = async (_, options) => {
        assert.equal(JSON.parse(options.body).expected_content, 'old');
        return response({ detail: 'File changed' }, 409);
    };
    await assert.rejects(api.saveProjectFile('p', 'world.md', 'new', 'old'), error => error.status === 409);
});
test('401 asks for a session token and retries once with authorization', async () => {
    sessionStorage.removeItem('autonovel_token');
    let calls = 0;
    globalThis.fetch = async (_, options) => {
        calls++;
        if (calls === 1) return response({ detail: 'Unauthorized' }, 401);
        assert.equal(options.headers.Authorization, 'Bearer test-token');
        return response([]);
    };
    assert.deepEqual(await api.listProjects(), []);
    assert.equal(calls, 2);
});
test('known job is resumed after disconnected polling instead of submitting again', async () => {
    const payload = { project_id: 'resume-test' };
    const key = `/pipeline/evaluate:${JSON.stringify(payload)}`;
    sessionStorage.setItem('autonovel_pending_jobs', JSON.stringify({ [key]: 'existing' }));
    globalThis.fetch = async (url, options) => {
        assert.equal(options.method, undefined);
        assert.equal(url, '/api/jobs/existing');
        return response({ id: 'existing', status: 'succeeded', result: { score: 7 } });
    };
    assert.deepEqual(await api.evaluateProject(payload), { score: 7 });
});
