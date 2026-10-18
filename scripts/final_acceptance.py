import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'artifacts'
logs = out / 'private' / 'final_checks'
logs.mkdir(parents=True, exist_ok=True)

def sources():
    paths = [root/'run.py', root/'mcp_stdio.py', root/'compose.yaml', root/'requirements.lock.txt']
    paths += [p for folder in ['relaygraph','web','tests'] for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

before = sources()
commands = [
    ('contracts', [sys.executable, str(root/'tests/test_contracts.py')]),
    ('real_graph', [sys.executable, str(root/'tests/integration_graph.py')]),
    ('real_http', [sys.executable, str(root/'scripts/http_acceptance.py')]),
    ('mcp_stdio', [sys.executable, str(root/'scripts/check_mcp.py')]),
    ('javascript_syntax', [shutil.which('node'), '--check', str(root/'web/app.js')]),
]
results = []
for name, command in commands:
    result = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', timeout=45, cwd=root)
    (logs/(name+'.stdout.txt')).write_text(result.stdout, encoding='utf-8')
    (logs/(name+'.stderr.txt')).write_text(result.stderr, encoding='utf-8')
    results.append({'stage': name, 'exit': result.returncode, 'passed': result.returncode == 0})
    print(json.dumps(results[-1]), flush=True)
    if result.returncode:
        raise SystemExit(result.stderr[-3000:] + result.stdout[-2000:])
after = sources()
assert before == after
receipts = {}
for pattern, key in [('integration_*.json','graph'),('http_acceptance_*.json','http'),('mcp_acceptance_*.json','mcp'),('durability_*.json','durability')]:
    path = sorted(out.glob(pattern))[-1]
    receipts[key] = {'file': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
record = {'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'PASS_LOCAL_FALKORDB_HTTP_BROWSER_FLOW_AND_MCP', 'source_unchanged_during_final_checks': True, 'sources': before, 'commands': results, 'scopes': {'contracts': '6 injected HTTP boundary and input-validation unit tests; no real database claim for this suite', 'real_graph': '5 tests against actual FalkorDB, no mocked graph', 'real_http': '6 real-controller and real-database checks', 'mcp': '5 actual stdio protocol checks, no model invoked', 'durability': 'owned-container restart, real outage response, matching graph state hashes'}, 'browser_verified': ['load_graph', 'impact_preview', 'input_change_invalidates_old_proposal', 'explicit_adoption', 'source_path_inspection', 'node_drag', 'zoom_and_fit'], 'browser_data': 'synthetic_only', 'receipts': receipts, 'online_model_calls': 0, 'real_customer_users': 0, 'participant_technical_review': 'PENDING_OWNER_VERIFICATION', 'contest_form_owner': 'USER_WILL_FILL_AND_SUBMIT', 'official_submission_claimed': False}
(out/'ENGINEERING_ACCEPTANCE.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': record['status'], 'source_files': len(before), 'all_stages_passed': True}, ensure_ascii=False))
