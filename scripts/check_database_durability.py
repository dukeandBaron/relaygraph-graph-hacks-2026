"""Temporarily restart only this task's labeled database, checking outage and disk recovery."""
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / 'runtime/deps')]
from relaygraph.store import GraphStore

name = 'relaygraph-20261018'
inspection = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True, timeout=15)
assert inspection.returncode == 0
container = json.loads(inspection.stdout)[0]
assert container['Config']['Labels'].get('codex.project') == name
assert container['Name'] == '/' + name
assert container['State']['Running']
state = GraphStore('demo').state()
assert state['revision'] == 2

def fingerprint(value):
    stable = {**value, 'nodes': sorted(value['nodes'], key=lambda row: row['id']), 'edges': sorted(value['edges'], key=lambda row: json.dumps(row, sort_keys=True))}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

before = fingerprint(state)
stopped = subprocess.run(['docker', 'stop', '--time', '10', name], capture_output=True, text=True, timeout=25)
assert stopped.returncode == 0
outage = None
try:
    try:
        urllib.request.urlopen('http://127.0.0.1:52188/api/state', timeout=15)
        raise AssertionError('Graph outage was incorrectly served as success')
    except urllib.error.HTTPError as error:
        outage = {'status': error.code, 'body': json.loads(error.read())}
        assert error.code == 503 and outage['body']['fallback'] is False and 'nodes' not in outage['body']
finally:
    started = subprocess.run(['docker', 'start', name], capture_output=True, text=True, timeout=25)
    assert started.returncode == 0
after = None
for attempt in range(10):
    try:
        after = GraphStore('demo').state()
        break
    except Exception:
        if attempt == 9:
            raise
        time.sleep(.5)
assert fingerprint(after) == before
record = {'actual_database_restart': True, 'owned_container': name, 'container_ownership_label_verified': True, 'before_sha256': before, 'after_sha256': fingerprint(after), 'persistent_revision': after['revision'], 'outage': outage, 'other_containers_modified': False, 'passed': 3}
path = root / 'artifacts' / ('durability_' + str(int(time.time())) + '.json')
path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'receipt': str(path), **record}, ensure_ascii=False))
