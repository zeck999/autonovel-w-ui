import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const source = fs.readFileSync(new URL('../js/universe-state.js', import.meta.url), 'utf8');
const state = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('publication fails closed without complete fresh report', () => {
    assert.equal(state.publicationBlocked({}, {}), true);
    assert.equal(state.publicationBlocked({status:'current', report:{complete:true},proposals:[]}, {publication_status:'draft'}), false);
    assert.equal(state.publicationBlocked({status:'stale', report:{complete:true}}, {}), true);
    assert.equal(state.publicationBlocked({status:'current',report:{complete:true,issues:[{severity:'high'}]}}, {}), true);
    assert.equal(state.publicationBlocked({status:'current',report:{complete:true}, proposals:[{id:'pending'}]}, {}), true);
    assert.equal(state.publicationBlocked({can_publish:true}, {publication_status:'published'}), true);
});

test('canon strings are escaped and unknown state is not presented as current', () => {
    assert.equal(state.escapeHtml('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
    assert.equal(state.analysisLabel(undefined), 'Univers non analysé');
    assert.equal(state.analysisLabel('stale'), 'À vérifier');
});

test('published file editor contains form-only explicit review and no AI rewrite', () => {
    const editor = fs.readFileSync(new URL('../js/views/files.js', import.meta.url), 'utf8');
    assert.match(editor, /!published && selectedFile.startsWith/);
    assert.match(editor, /expected_content: fileContent/);
    assert.match(editor, /candidate.proposal_id/);
    assert.match(editor, /published \? 'readonly'/);
    assert.match(editor, /publication.publication_status === 'published'/);
});


test('API exposes explicit publication confirmation and selected assertion ids', async () => {
    const session = new Map();
    globalThis.sessionStorage = {getItem:key => session.get(key) || null, setItem:(key,value) => session.set(key,value), removeItem:key => session.delete(key)};
    const requests = [];
    globalThis.fetch = async (url, options) => { requests.push({url,options}); return {ok:true,status:200,json:async()=>({publication_status:'published'})}; };
    const apiSource = fs.readFileSync(new URL('../js/api.js', import.meta.url), 'utf8');
    const {api} = await import(`data:text/javascript;base64,${Buffer.from(apiSource + '\n// universe test').toString('base64')}`);
    await api.publishProject('novel-one');
    await api.acceptAssertions('novel-one', 'analysis-1', ['fact-2']);
    await api.applyProofread('novel-one', 'proposal-1');
    assert.equal(requests[0].url, '/api/projects/novel-one/publish');
    assert.deepEqual(JSON.parse(requests[0].options.body), {confirmation:true});
    assert.deepEqual(JSON.parse(requests[1].options.body), {analysis_id:'analysis-1',assertion_ids:['fact-2']});
    assert.deepEqual(JSON.parse(requests[2].options.body), {proposal_id:'proposal-1',confirmation:true});
});
