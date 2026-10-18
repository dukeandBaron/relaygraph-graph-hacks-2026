import json
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
messages = [
    {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'relaygraph-verifier', 'version': '1.0'}}},
    {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
    {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'inspect_workspace', 'arguments': {}}},
    {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call', 'params': {'name': 'explain_task', 'arguments': {'task': 'catering'}}},
    {'jsonrpc': '2.0', 'id': 5, 'method': 'tools/call', 'params': {'name': 'run_cypher', 'arguments': {'query': 'MATCH (n) DELETE n'}}},
]
result = subprocess.run([sys.executable, str(root / 'mcp_stdio.py')], input='\n'.join(json.dumps(row) for row in messages)+'\n', capture_output=True, encoding='utf-8', timeout=30)
assert result.returncode == 0, result.stderr
responses = [json.loads(line) for line in result.stdout.splitlines()]
assert len(responses) == 5
by_id = {row['id']: row['result'] for row in responses}
assert by_id[1]['protocolVersion'] == '2025-03-26'
assert len(by_id[2]['tools']) == 3
assert by_id[3]['isError'] is False
state = json.loads(by_id[3]['content'][0]['text'])
assert state['initialized'] is True
explanation = json.loads(by_id[4]['content'][0]['text'])
assert any(row['path'] == ['catering','travel','register','deadline'] for row in explanation['evidence'])
assert by_id[5]['isError'] is True
record = {'actual_stdio_roundtrip': True, 'actual_falkordb': True, 'checks_passed': 5, 'external_model_invoked': False, 'configuration_changed': False, 'responses': responses}
path = root / 'artifacts' / ('mcp_acceptance_' + str(int(time.time())) + '.json')
path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'receipt': str(path), 'checks_passed': 5, 'graph_revision': state['revision']}))
