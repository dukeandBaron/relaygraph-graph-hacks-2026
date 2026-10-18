"""Exercise the real HTTP controller and real FalkorDB, without browser mocks."""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
workspace = 'http_' + str(int(time.time()))
base = 'http://127.0.0.1:52188'
results = []

def request(path, data=None):
    payload = json.dumps(data).encode('utf-8') if data is not None else None
    req = urllib.request.Request(base + path, data=payload, headers={'Content-Type': 'application/json', 'X-Workspace': workspace})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read()
            return response.status, json.loads(raw) if path.startswith('/api/') else raw.decode('utf-8')
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())

code, state = request('/api/state')
assert code == 200 and state['initialized'] is False
results.append({'check': 'empty_graph_not_fake_sample', 'status': code})
code, seeded = request('/api/seed', {})
assert code == 200 and seeded['state']['revision'] == 1
code, preview = request('/api/preview', {'change': {'deadline': '2026-10-19T17:00:00+08:00', 'material': 'Signed declaration'}})
assert code == 200 and len(preview['tasks']) == 3 and len(preview['affectedArtifacts']) == 4
results.append({'check': 'real_http_preview', 'tasks': preview['tasks']})
command = {'change': preview['change'], 'proposal': preview['proposal'], 'expectedRevision': 1, 'operationId': 'http_acceptance_' + str(int(time.time())), 'confirmed': True}
code, adopted = request('/api/adopt', command)
assert code == 200 and adopted['applied'] and len(adopted['actions']) == 3
results.append({'check': 'real_http_adoption', 'revision': adopted['revision']})
code, duplicate = request('/api/adopt', command)
assert code == 200 and duplicate['duplicate']
results.append({'check': 'duplicate_command_not_repeated', 'duplicate': True})
code, explanation = request('/api/explain/catering')
assert code == 200 and any(row['source'] == 'notice_v2' for row in explanation['evidence'])
results.append({'check': 'real_graph_source_trace', 'source_ids': sorted({row['source'] for row in explanation['evidence']})})
code, index = request('/')
assert code == 200 and 'RelayGraph' in index and '/assets/app.js' in index
results.append({'check': 'web_entry_served', 'status': code})
record = {'workspace': workspace, 'real_http': True, 'real_falkordb': True, 'browser_clicks': False, 'online_model_calls': 0, 'passed': len(results), 'results': results}
out = root / 'artifacts' / ('http_acceptance_' + str(int(time.time())) + '.json')
out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'receipt': str(out), **record}, ensure_ascii=False))
