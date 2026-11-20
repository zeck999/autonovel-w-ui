"""Text-only transport. Keeps the existing Anthropic response contract for callers."""
import os
from urllib.parse import urlsplit
import httpx


def api_key():
    if os.environ.get('AUTONOVEL_TEXT_PROVIDER', 'anthropic') == 'openai-compatible':
        return os.environ.get('AUTONOVEL_TEXT_API_KEY', '')
    return os.environ.get('ANTHROPIC_API_KEY', '')


def post_messages(url, **kwargs):
    provider = os.environ.get('AUTONOVEL_TEXT_PROVIDER', 'anthropic')
    if provider == 'anthropic':
        return httpx.post(url, **kwargs)
    if provider != 'openai-compatible':
        raise ValueError('Unsupported text provider')
    base = os.environ.get('AUTONOVEL_TEXT_BASE_URL', '').rstrip('/')
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Invalid text provider URL')
    model = os.environ.get('AUTONOVEL_TEXT_MODEL', '').strip()
    if not model or not api_key():
        raise ValueError('Text provider model and API key are required')
    original = kwargs.pop('json')
    messages = []
    system = original.get('system')
    if system:
        if isinstance(system, list):
            system = '\n'.join(part['text'] for part in system if part.get('type') == 'text')
        messages.append({'role': 'system', 'content': system})
    for message in original.get('messages', []):
        content = message['content']
        if isinstance(content, list):
            if any(part.get('type') != 'text' for part in content):
                raise ValueError('Only text content is supported by the text provider')
            content = '\n'.join(part['text'] for part in content)
        messages.append({'role': message['role'], 'content': content})
    payload = {'model': model, 'messages': messages, 'max_tokens': original.get('max_tokens', 4096)}
    for name in ('temperature', 'top_p'):
        if name in original:
            payload[name] = original[name]
    if original.get('stop_sequences'):
        payload['stop'] = original['stop_sequences']
    kwargs['headers'] = {'Authorization': 'Bearer ' + api_key(), 'Content-Type': 'application/json'}
    response = httpx.post(base + '/chat/completions', json=payload, **kwargs)
    if not response.is_success:
        return response
    data = response.json()
    choice = data['choices'][0]
    text = choice['message'].get('content')
    if not isinstance(text, str):
        raise ValueError('Text provider returned no text')
    usage = data.get('usage', {})
    normalized = {'content': [{'type': 'text', 'text': text}],
                  'stop_reason': 'max_tokens' if choice.get('finish_reason') == 'length' else 'end_turn',
                  'usage': {'input_tokens': usage.get('prompt_tokens', 0), 'output_tokens': usage.get('completion_tokens', 0)}}
    return httpx.Response(response.status_code, json=normalized, request=response.request)
