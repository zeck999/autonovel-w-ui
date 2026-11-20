import httpx
import pytest
from unittest.mock import patch
from src.text_provider import post_messages


def test_openai_transport(monkeypatch):
    monkeypatch.setenv('AUTONOVEL_TEXT_PROVIDER', 'openai-compatible')
    monkeypatch.setenv('AUTONOVEL_TEXT_BASE_URL', 'http://localhost:9000/v1')
    monkeypatch.setenv('AUTONOVEL_TEXT_MODEL', 'auto/smart')
    monkeypatch.setenv('AUTONOVEL_TEXT_API_KEY', 'fixture-not-real')
    response = httpx.Response(200, json={'choices':[{'message':{'content':'OK'},'finish_reason':'stop'}], 'usage':{'prompt_tokens':4}}, request=httpx.Request('POST','http://localhost'))
    with patch('src.text_provider.httpx.post', return_value=response) as send:
        result = post_messages('http://old/v1/messages', json={'model':'old','system':'Rules','max_tokens':100,'messages':[{'role':'user','content':'Hello'}]}, headers={'x-api-key':'old'}, timeout=3)
    assert result.json()['content'][0]['text'] == 'OK'
    assert send.call_args.args == ('http://localhost:9000/v1/chat/completions',)
    assert send.call_args.kwargs['json']['model'] == 'auto/smart'
    assert 'x-api-key' not in send.call_args.kwargs['headers']


def test_anthropic_unchanged(monkeypatch):
    monkeypatch.setenv('AUTONOVEL_TEXT_PROVIDER','anthropic')
    with patch('src.text_provider.httpx.post') as send:
        post_messages('http://fixture/v1/messages', json={'model':'fixture'})
        send.assert_called_once_with('http://fixture/v1/messages',json={'model':'fixture'})


def test_no_silent_fallback(monkeypatch):
    monkeypatch.setenv('AUTONOVEL_TEXT_PROVIDER','unknown')
    with pytest.raises(ValueError): post_messages('http://fixture',json={})
