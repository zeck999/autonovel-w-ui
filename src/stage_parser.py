"""Parse standalone, non-executable stage directions into ordered reading cues."""
import re

ASSET_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
               '.webp': 'image/webp', '.gif': 'image/gif'}
ASSET = re.compile(r'[A-Za-z0-9_-]{1,96}\.(?:png|jpe?g|webp|gif)')
TAG = re.compile(r'^ {0,3}\[(emotion|shake|bg)(?=\s|\]|$)(.*)\]\s*$')
START = re.compile(r'^ {0,3}\[(emotion|shake|bg)(?=\s|\]|$)')
ATTRIBUTE = re.compile(r'\s+([a-z]+)="([^"\[\]]{1,128})"')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
SLUG = re.compile(r'[A-Za-z0-9_-]{1,40}')


def parse_action(line):
    match = TAG.fullmatch(line)
    if not match:
        return None
    kind, rest = match.groups()
    attrs = {}
    while rest.strip():
        attr = ATTRIBUTE.match(rest)
        if not attr or attr[1] in attrs:
            return None
        attrs[attr[1]] = attr[2]
        rest = rest[attr.end():]
    if kind == 'bg' and attrs.keys() == {'image'} and ASSET.fullmatch(attrs['image']):
        return {'kind': kind, **attrs}
    if kind == 'emotion' and attrs.keys() == {'char', 'state'} and all(SLUG.fullmatch(v) for v in attrs.values()):
        return {'kind': kind, **attrs, 'image': f"{attrs['char']}--{attrs['state']}.png"}
    if kind == 'shake' and attrs.keys() == {'intensity'} and attrs['intensity'] in {'low', 'medium', 'high'}:
        return {'kind': kind, **attrs}
    return None


def parse_stage(content: str) -> dict:
    cues, warnings, lines, actions = [], [], [], []
    fence = None

    def flush():
        text = '\n'.join(lines).strip('\n')
        if text.strip() or actions:
            cues.append({'text': text, 'actions': actions.copy()})
        lines.clear()
        actions.clear()

    for number, line in enumerate(content.splitlines(), 1):
        delimiter = FENCE.match(line)
        if fence:
            if delimiter and delimiter[1][0] == fence[0] and len(delimiter[1]) >= len(fence) and not delimiter[2].strip():
                fence = None
            lines.append(line)
        elif delimiter:
            fence = delimiter[1]
            lines.append(line)
        elif START.match(line):
            action = parse_action(line)
            if action is None:
                warnings.append({'line': number, 'message': 'Balise de mise en scène invalide'})
                lines.append(line)
            else:
                if any(s.strip() for s in lines):
                    flush()
                actions.append(action)
        else:
            lines.append(line)
    flush()
    return {'cues': cues, 'warnings': warnings}
