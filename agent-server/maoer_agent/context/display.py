"""Project delivered list positions onto identities from paired observations."""
import html
import json
import re
import unicodedata

from maoer_agent.memory.history import podcast_identities
from maoer_agent.tools.results import catalog_page_chain, catalog_page_view


def title_key(text):
    text = html.unescape(unicodedata.normalize('NFKC', text))
    text = re.sub(r'(?<!!)\[([^\]]+)\]\([^\n]*?\)', r'\1', text)
    text = text.replace('**', '').replace('`', '').replace('\\', '')
    text = text.translate(str.maketrans('“”‘’「」『』–—', '\"\"\'\'\"\"\"\"--'))
    return re.sub(r'\s+', '', text).casefold()


def matching_items(text, episodes, podcast_id=''):
    """Only unique observed titles/explicit abbreviations identify an item."""
    key = title_key(text)
    anchors = re.findall(r'\*\*(.+?)\*\*|(?<!!)\[([^\]]+)\]\([^\n]*?\)', text)
    labels = [title_key(a or b) for a, b in anchors] or [key]
    matches = {}
    for identity, item in episodes.items():
        if podcast_id and item['podcast_id'] != podcast_id:
            continue
        title = title_key(item['title'])
        full = title == key or (len(title) >= 4 and title in key)
        # A column suffix may be omitted; ellipses explicitly mark a shortened
        # title. Never choose a closest title or infer identity from a list rank.
        base = title_key(re.split(r'[|｜〡]', item['title'], maxsplit=1)[0])
        abbreviated = any(
            (label == base and len(base) >= 8)
            or (label.endswith(('…', '...')) and len(label.rstrip('….')) >= 8
                and title.startswith(label.rstrip('….')))
            for label in labels)
        if full or abbreviated:
            matches[identity] = item
    return list(matches.values())


def displayed_episode_pages(messages):
    """Keep every delivered row, including an unresolved row, in display order."""
    end = max((i for i, m in enumerate(messages) if m['role'] == 'user'), default=len(messages))
    podcasts = podcast_identities(messages[:end])
    episodes, calls, observed, pages = {}, {}, [], []
    turn_queries = []
    for message in messages[:end]:
        if message['role'] == 'user':
            turn_queries = []
        calls.update((c['id'], c['function']) for c in message.get('tool_calls') or [])
        if message['role'] == 'tool' and message.get('tool_call_id') in calls:
            result = json.loads(message['content'])
            if result.get('status') != 'ok':
                continue
            call = calls[message['tool_call_id']]
            args = json.loads(call['arguments'])
            if call['name'] == 'list_episodes' and not args.get('position') and not args.get('episode_number'):
                row = {'call_id': message['tool_call_id'], 'arguments': args, 'result': result}
                observed.append(row)
                turn_queries.append(row)
            for item in result.get('items', []):
                if item.get('kind') == 'podcast':
                    podcasts[item['id']] = item.get('title', '')
                if item.get('kind') == 'episode' and item.get('id') and item.get('podcast_id'):
                    episodes[(item['podcast_id'], item['id'])] = item
        if message['role'] != 'assistant' or not message.get('content') or message.get('tool_calls'):
            continue

        rows, scope, previous = [], '', None
        before = len(pages)
        table = False

        def save():
            if not rows:
                return
            # A list with observed episode titles is a delivered episode list.
            # In an episode-list conversation an unrecognized new list still
            # occupies its positions, including a rewrite without another query.
            # It cannot authorize reuse of the previous list's identities.
            if not episodes and not turn_queries:
                return
            ids = {r['podcast_id'] for r in rows if r.get('podcast_id')}
            queried = {r['arguments']['podcast_id'] for r in turn_queries}
            pid = scope or (next(iter(ids)) if len(ids) == 1 else '')
            if not pid and len(queried) == 1:
                pid = next(iter(queried))
            page = {'reference': 'display' + str(len(pages) + 1), 'items': list(rows),
                    'podcast_title': podcasts.get(pid, ''),
                    'resolved': all(r['status'] == 'resolved' for r in rows)}
            if page['resolved']:
                identities = [(r['podcast_id'], r['id']) for r in rows]
                for candidate in reversed(observed):
                    view = catalog_page_view(catalog_page_chain(observed, candidate['arguments']), len(rows))
                    if view and identities == [(i.get('podcast_id'), i.get('id')) for i in view['result']['items']]:
                        page['query'] = {k: view[k] for k in ('call_id', 'arguments')}
                        page['query'].update({k: view['result'][k] for k in ('offset', 'has_more', 'next_offset') if k in view['result']})
                        break
            pages.append(page)

        def append(text, label):
            matches = matching_items(text, episodes, scope)
            row = {'position': len(rows) + 1, 'label': label}
            if len(matches) == 1:
                row.update({k: matches[0][k] for k in ('id', 'title', 'podcast_id')})
                row['status'] = 'resolved'
            else:
                row.update(status='ambiguous' if matches else 'unresolved', display_text=text[:300])
            rows.append(row)

        lines = message['content'].splitlines()
        plain = all(sum(title_key(e['title']) == title_key(line) for e in episodes.values()) == 1
                    for line in lines if line.strip())
        for line in lines:
            if plain and line.strip():
                append(line, len(rows) + 1)
                continue
            stripped = unicodedata.normalize('NFKC', line).strip()
            if stripped.startswith('|'):
                cells = [c.strip() for c in re.split(r'(?<!\\)\|', stripped.strip('|'))]
                if all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    continue
                if any(c in {'标题', '分集', '分集标题', '节目', '节目名称'} for c in cells):
                    table = True
                    continue
                numbered = bool(cells and cells[0].isdecimal())
                text = ' '.join(cells[1:] if numbered else cells)
                if numbered or table or matching_items(text, episodes, scope):
                    append(text, int(cells[0]) if numbered else len(rows) + 1)
                    table = True
                    continue
            table = False
            match = re.match(r'^\s*(?:(\d+)[.)、．]\s*|[-*•]\s+)(.+)', unicodedata.normalize('NFKC', line))
            if match:
                label = int(match[1]) if match[1] else len(rows) + 1
                if previous is not None and label != previous + 1:
                    save()
                    rows = []
                append(match[2], label)
                previous = label
            elif line.strip():
                # Markdown list continuations (dates, duration, description)
                # belong to the preceding row, not a new delivered page.
                if rows and line[:1].isspace():
                    continue
                save()
                rows, previous = [], None
                named = [pid for pid, title in podcasts.items() if title and title in line]
                scope = named[0] if len(named) == 1 else ''
        save()
        if len(pages) == before and any(q['result'].get('items') for q in turn_queries):
            rows = [{'position': 1, 'label': 1, 'status': 'unresolved',
                     'display_text': message['content'][:300]}]
            save()
    return pages[-4:]


def displayed_selection(lookup, pages):
    if lookup.get('selector_kind') != 'displayed_page':
        return None
    selected = [p for p in pages if (not lookup.get('page_reference') or p['reference'] == lookup['page_reference'])
                and (not lookup.get('podcast_title') or p.get('podcast_title') == lookup['podcast_title'])]
    if len(selected) != 1:
        return None
    page = selected[0]
    number = lookup.get('selector_value', 0)
    if not 0 < number <= len(page['items']):
        return None
    item = page['items'][number - 1]
    if item['status'] != 'resolved':
        return None
    if any(lookup.get(k) and lookup[k] != item[v] for k, v in (('episode_id', 'id'), ('podcast_id', 'podcast_id'))):
        raise ValueError('Displayed selection identity does not match its actual item')
    return page, item
