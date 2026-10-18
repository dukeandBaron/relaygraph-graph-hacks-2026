import hashlib
import json
import os
import re
import threading
from datetime import datetime

from . import queries
from .fixture import fixture


class DatabaseUnavailable(RuntimeError):
    pass


class Conflict(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def tenant_graph(tenant):
    if not isinstance(tenant, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,31}', tenant):
        raise ValueError('Workspace must start with a lowercase letter and contain at most 32 letters, digits, underscores or hyphens.')
    return 'relaygraph_' + hashlib.sha256(tenant.encode('utf-8')).hexdigest()[:16]


def validate_change(change):
    if not isinstance(change, dict) or set(change) != {'deadline', 'material'}:
        raise ValueError('A change requires exactly deadline and material fields.')
    deadline = change['deadline']
    if not isinstance(deadline, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:00\+08:00', deadline):
        raise ValueError('Use a complete deadline with explicit +08:00 timezone and seconds, for example 2026-10-19T17:00:00+08:00.')
    datetime.fromisoformat(deadline)
    material = change['material']
    if not isinstance(material, str) or not 1 <= len(material.strip()) <= 100 or any(ord(char) < 32 for char in material):
        raise ValueError('The added material must contain 1 to 100 visible characters.')
    return {'deadline': deadline, 'material': material.strip()}


class GraphStore:
    """The graph is the only state store. It has no JSON or memory fallback."""

    def __init__(self, tenant='demo'):
        self.tenant = tenant
        self.graph_name = tenant_graph(tenant)
        self.lock = threading.RLock()
        self._graph = None

    def _connect(self):
        if self._graph is None:
            try:
                from falkordb import FalkorDB
                from redis.backoff import NoBackoff
                from redis.retry import Retry
                client = FalkorDB(
                    host=os.environ.get('FALKORDB_HOST', '127.0.0.1'),
                    port=int(os.environ.get('FALKORDB_PORT', '6388')),
                    username=os.environ.get('FALKORDB_USERNAME') or None,
                    password=os.environ.get('FALKORDB_PASSWORD') or None,
                    ssl=os.environ.get('FALKORDB_TLS', '0') == '1',
                    ssl_check_hostname=True,
                    socket_connect_timeout=3, socket_timeout=5,
                    retry=Retry(NoBackoff(), 0),
                )
                self._graph = client.select_graph(self.graph_name)
            except Exception as error:
                raise DatabaseUnavailable('FalkorDB is unavailable. Start the documented database; application actions are paused.') from error
        return self._graph

    def query(self, text, params=None, read_only=True):
        try:
            graph = self._connect()
            method = graph.ro_query if read_only else graph.query
            return method(text, params=params or {}).result_set
        except DatabaseUnavailable:
            raise
        except Exception as error:
            if read_only and text == queries.META and type(error).__name__ == 'ResponseError' and any(marker in str(error).lower() for marker in ['does not exist', 'empty key', 'unknown graph']):
                return []
            # Query errors are deliberately distinguishable from connection errors.
            if type(error).__name__ in {'ConnectionError', 'TimeoutError', 'AuthenticationError'}:
                self._graph = None
                raise DatabaseUnavailable('FalkorDB did not respond. No substitute state was used.') from error
            raise

    def seed(self):
        with self.lock:
            meta = self.query(queries.META)
            if meta:
                return {'created': False, 'revision': meta[0][0], 'graph': self.graph_name}
            nodes, edges = fixture()
            values, parts, variables = {}, [], {}
            for index, (label, props) in enumerate(nodes):
                var = 'n' + str(index)
                variables[props['id']] = var
                fields = []
                for key, value in props.items():
                    parameter = var + '_' + key
                    values[parameter] = value
                    fields.append(key + ':$' + parameter)
                parts.append('(' + var + ':Entity:' + label + ' {' + ','.join(fields) + '})')
            for source, rel, destination in edges:
                parts.append('(' + variables[source] + ')-[:' + rel + ']->(' + variables[destination] + ')')
            text = "MERGE (m:Meta {id:'root'}) ON CREATE SET m.revision=0 WITH m WHERE m.revision=0 CREATE " + ','.join(parts) + " SET m.revision=1,m.title='Campus makers showcase',m.lastOperation='seed' RETURN m.revision"
            result = self.query(text, values, read_only=False)
            return {'created': bool(result), 'revision': 1, 'graph': self.graph_name}

    def state(self):
        meta = self.query(queries.META)
        if not meta:
            return {'initialized': False, 'workspace': self.tenant, 'graph': self.graph_name, 'revision': 0, 'nodes': [], 'edges': []}
        nodes = [{**row[2], 'id': row[0], 'kind': next((label for label in row[1] if label != 'Entity'), 'Entity'), 'artifactKind': row[2].get('kind')} for row in self.query(queries.NODES)]
        edges = [{'source': row[0], 'type': row[1], 'target': row[2], **row[3]} for row in self.query(queries.EDGES)]
        after = self.query(queries.META)
        if not after or after[0][0] != meta[0][0]:
            raise Conflict('The graph changed while this view was read. Refresh before reviewing or adopting a proposal.')
        return {'initialized': True, 'workspace': self.tenant, 'graph': self.graph_name, 'title': meta[0][1], 'revision': meta[0][0], 'lastOperation': meta[0][2], 'nodes': nodes, 'edges': edges, 'synthetic': True, 'runtime': 'deterministic graph policy; no online LLM'}

    def preview(self, change):
        change = validate_change(change)
        state = self.state()
        if not state['initialized']:
            raise Conflict('Load the synthetic workspace before preparing a change.')
        current = {node['id']: node for node in state['nodes']}
        if state['revision'] != 1:
            raise Conflict('This bounded demo already adopted its notice correction. Open another isolated workspace to replay it.')
        if change['deadline'] == current['deadline']['value']:
            raise ValueError('Choose a changed deadline so the graph can investigate a real difference.')
        paths = self.query(queries.IMPACT, {'changed': ['deadline']})
        impacts = []
        for task, title, owner, requirement, path in paths:
            impacts.append({'task': task, 'title': title, 'owner': owner, 'requirement': requirement, 'path': path})
        tasks = sorted({item['task'] for item in impacts})
        artifacts = [{'id': row[0], 'kind': row[1], 'title': row[2], 'state': row[3], 'task': row[4], 'basisRevision': row[5]} for row in self.query(queries.ARTIFACTS, {'tasks': tasks})]
        basis = {'workspace': self.tenant, 'revision': state['revision'], 'change': change, 'tasks': tasks, 'artifacts': sorted(item['id'] for item in artifacts)}
        return {**basis, 'proposal': digest(basis), 'impacts': impacts, 'affectedArtifacts': artifacts, 'unaffectedTasks': [node['id'] for node in state['nodes'] if node['kind'] == 'Task' and node['id'] not in tasks], 'sourceIds': ['notice_v1', 'notice_v2'], 'queries': {'impact': queries.IMPACT.strip(), 'artifacts': queries.ARTIFACTS.strip()}, 'explanation': 'The graph traverses dependency paths, prepares review actions for affected tasks, and preserves unrelated confirmations.'}

    def apply(self, change, proposal, expected_revision, operation_id, confirmed):
        if confirmed is not True:
            raise ValueError('Review the proposal and explicitly confirm adoption.')
        if not isinstance(operation_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}', operation_id):
            raise ValueError('Operation ID must contain 8 to 80 letters, digits, underscores or hyphens.')
        change = validate_change(change)
        command_digest = digest({'change': change, 'proposal': proposal, 'revision': expected_revision})
        with self.lock:
            existing = self.query(queries.OPERATION, {'id': operation_id})
            if existing:
                if existing[0][0] != command_digest:
                    raise Conflict('This operation ID already belongs to different content.')
                return {'applied': False, 'duplicate': True, 'revision': existing[0][1], 'state': self.state()}
            preview = self.preview(change)
            if expected_revision != preview['revision'] or proposal != preview['proposal']:
                raise Conflict('The graph or proposal changed. Prepare and review a fresh proposal.')
            source = 'SYNTHETIC CORRECTION - Registration closes ' + change['deadline'] + '. Added material: ' + change['material'] + '. Room A remains unchanged. Not an actual event.'
            params = {'expected': expected_revision, 'deadline': change['deadline'], 'material': change['material'], 'source': source, 'operation': operation_id, 'digest': command_digest}
            # One write query performs the compare-and-set, state transitions and log.
            parts = ["MATCH (m:Meta {id:'root'}),(r:Requirement {id:'deadline'}),(base:Requirement {id:'registration_form'}),(t:Task {id:'register'}) WHERE m.revision=$expected", "SET m.revision=m.revision+1,m.lastOperation=$operation,r.value=$deadline,r.version=2", "CREATE (s:Entity:SourceRevision {id:'notice_v2',title:'Correction notice · v2',body:$source,revision:2,synthetic:true})", "CREATE (added:Entity:Requirement {id:'declaration',title:'Additional material',value:$material,version:2})", "CREATE (r)-[:CITED_IN]->(s),(added)-[:CITED_IN]->(s),(t)-[:DEPENDS_ON]->(added)"]
            for index, task in enumerate(preview['tasks']):
                params['task' + str(index)] = task
                params['reason' + str(index)] = json.dumps([item['path'] for item in preview['impacts'] if item['task'] == task])
                parts += [f"WITH m,s MATCH (t{index}:Task {{id:$task{index}}}) SET t{index}.state='needs_review'", f"CREATE (a{index}:Entity:ReviewAction {{id:'review_'+$task{index},title:'Review changed requirements',state:'pending',reason:$reason{index},sourceIds:['notice_v1','notice_v2']}})-[:TARGETS]->(t{index})"]
            for index, artifact in enumerate(preview['affectedArtifacts']):
                params['artifact' + str(index)] = artifact['id']
                params['artifactState' + str(index)] = 'needs_recheck' if artifact['kind'] == 'receipt' else 'needs_reconfirmation'
                parts += [f"WITH m,s MATCH (f{index}:Artifact {{id:$artifact{index}}}) SET f{index}.state=$artifactState{index}"]
            parts += ["CREATE (o:Entity:Operation {id:$operation,title:'Adopted notice correction',digest:$digest,revision:2,proposal:$proposal})-[:USED_SOURCE]->(s)", "RETURN m.revision"]
            params['proposal'] = proposal
            result = self.query(' '.join(parts), params, read_only=False)
            if not result:
                raise Conflict('The graph changed before this write. No update was adopted.')
            return {'applied': True, 'duplicate': False, 'revision': result[0][0], 'state': self.state(), 'actions': self.actions()}

    def actions(self):
        return [{'id': row[0], 'title': row[1], 'state': row[2], 'task': row[3], 'taskTitle': row[4], 'owner': row[5], 'paths': json.loads(row[6]), 'sourceIds': row[7]} for row in self.query(queries.REVIEW_ACTIONS)]

    def explain(self, task):
        if not isinstance(task, str) or not re.fullmatch(r'[a-z_]{1,40}', task):
            raise ValueError('Choose a task from the workspace.')
        paths = self.query(queries.TASK_PATHS, {'task': task})
        return {'task': task, 'evidence': [{'requirement': row[0], 'title': row[1], 'currentValue': row[2], 'currentVersion': row[3], 'source': row[4], 'sourceTitle': row[5], 'sourceBody': row[6], 'path': row[7]} for row in paths], 'query': queries.TASK_PATHS.strip(), 'mode': 'graph retrieval; source versions are explicit, not inferred model citations'}
