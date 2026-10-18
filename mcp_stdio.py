"""Minimal read-only MCP stdio transport for a caller's own AI assistant.

No model runs here. The external assistant chooses tools and reasons about their
source-bound results; graph mutations remain explicit UI actions.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'runtime/deps'))
from relaygraph.store import GraphStore

TOOLS = [
    {'name': 'inspect_workspace', 'description': 'Read the current graph revision, tasks, sources and record states.', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'explain_task', 'description': 'Retrieve multi-hop Cypher paths and original source revisions for a task.', 'inputSchema': {'type': 'object', 'properties': {'task': {'type': 'string'}}, 'required': ['task'], 'additionalProperties': False}},
    {'name': 'list_review_actions', 'description': 'Read persistent internal review actions and their owner and source paths.', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
]


def handle(message, store):
    request_id = message.get('id')
    method = message.get('method')
    if request_id is None:
        return None
    if method == 'initialize':
        requested = message.get('params', {}).get('protocolVersion')
        protocol = requested if requested in ['2024-11-05', '2025-03-26', '2025-06-18'] else '2025-03-26'
        return {'jsonrpc': '2.0', 'id': request_id, 'result': {'protocolVersion': protocol, 'capabilities': {'tools': {'listChanged': False}}, 'serverInfo': {'name': 'relaygraph-context', 'version': '1.0.0'}, 'instructions': 'All tool results come from FalkorDB. Sources and people are synthetic. These tools are read-only; do not represent a policy trace as a language-model response or human approval.'}}
    if method == 'ping':
        return {'jsonrpc': '2.0', 'id': request_id, 'result': {}}
    if method == 'tools/list':
        return {'jsonrpc': '2.0', 'id': request_id, 'result': {'tools': TOOLS}}
    if method == 'tools/call':
        params = message.get('params', {})
        name, arguments = params.get('name'), params.get('arguments', {})
        try:
            if not isinstance(arguments, dict):
                raise ValueError('Tool arguments must be an object.')
            if name == 'inspect_workspace' and not arguments:
                value = store.state()
            elif name == 'list_review_actions' and not arguments:
                value = {'actions': store.actions()}
            elif name == 'explain_task' and set(arguments) == {'task'}:
                value = store.explain(arguments['task'])
            else:
                raise ValueError('Unknown tool or undocumented arguments. Free-form queries and write operations are not accepted.')
            result = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}], 'isError': False}
        except Exception as error:
            result = {'content': [{'type': 'text', 'text': str(error)}], 'isError': True}
        return {'jsonrpc': '2.0', 'id': request_id, 'result': result}
    return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32601, 'message': 'Method not supported'}}


if __name__ == '__main__':
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
    store = GraphStore(os.environ.get('RELAYGRAPH_WORKSPACE', 'demo'))
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if not isinstance(message, dict):
                raise ValueError('Request must be an object')
            response = handle(message, store)
        except (ValueError, TypeError):
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Invalid JSON-RPC request'}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
