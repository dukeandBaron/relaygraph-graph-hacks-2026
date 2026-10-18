"""Actual FalkorDB integration. No mocked graph or model is used here."""
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'runtime/deps')]
from relaygraph.store import Conflict, GraphStore

RUN = str(int(time.time()))
CHANGE = {'deadline': '2026-10-19T17:00:00+08:00', 'material': 'Signed declaration'}
EVENTS = []


class RealGraphTests(unittest.TestCase):
    def new_store(self, name):
        store = GraphStore('qa_' + RUN + '_' + name)
        result = store.seed()
        self.assertTrue(result['created'])
        return store

    def test_multihop_impact_and_unrelated_work(self):
        store = self.new_store('paths')
        preview = store.preview(CHANGE)
        self.assertEqual(preview['tasks'], ['catering', 'register', 'travel'])
        self.assertEqual(preview['unaffectedTasks'], ['accessibility'])
        paths = {row['task']: row['path'] for row in preview['impacts']}
        self.assertEqual(paths['catering'], ['catering', 'travel', 'register', 'deadline'])
        self.assertEqual(len(preview['affectedArtifacts']), 4)
        EVENTS.append({'check': self._testMethodName, 'preview': preview})

    def test_adoption_and_restart_persistence(self):
        store = self.new_store('persist')
        preview = store.preview(CHANGE)
        result = store.apply(CHANGE, preview['proposal'], 1, 'persist_' + RUN, True)
        self.assertTrue(result['applied'])
        self.assertEqual(result['revision'], 2)
        fresh = GraphStore(store.tenant)
        state = fresh.state()
        nodes = {node['id']: node for node in state['nodes']}
        self.assertEqual(nodes['receipt_register']['state'], 'needs_recheck')
        self.assertEqual(nodes['receipt_register']['kind'], 'Artifact')
        self.assertEqual(nodes['receipt_register']['artifactKind'], 'receipt')
        self.assertEqual(nodes['ack_register']['kind'], 'Artifact')
        self.assertEqual(nodes['ack_register']['state'], 'needs_reconfirmation')
        self.assertEqual(nodes['ack_travel']['state'], 'needs_reconfirmation')
        self.assertEqual(nodes['ack_catering']['state'], 'needs_reconfirmation')
        self.assertEqual(nodes['ack_accessibility']['state'], 'confirmed')
        self.assertEqual(nodes['accessibility']['state'], 'current')
        self.assertEqual(nodes['deadline']['value'], CHANGE['deadline'])
        self.assertIn('2026-10-20 18:00', nodes['notice_v1']['body'])
        self.assertIn('Signed declaration', nodes['notice_v2']['body'])
        self.assertEqual(len(fresh.actions()), 3)
        self.assertEqual(fresh.seed()['created'], False)
        EVENTS.append({'check': self._testMethodName, 'state': state, 'actions': fresh.actions()})

    def test_unconfirmed_or_tampered_proposal_leaves_graph_unchanged(self):
        store = self.new_store('reject')
        preview = store.preview(CHANGE)
        before = store.state()
        with self.assertRaises(ValueError):
            store.apply(CHANGE, preview['proposal'], 1, 'reject_' + RUN, False)
        with self.assertRaises(Conflict):
            store.apply(CHANGE, 'tampered', 1, 'tampered_' + RUN, True)
        with self.assertRaises(Conflict):
            store.apply(CHANGE, preview['proposal'], 99, 'stale_' + RUN, True)
        self.assertEqual(store.state(), before)

    def test_idempotency_conflict_and_cross_workspace_rejection(self):
        first = self.new_store('first')
        second = self.new_store('second')
        preview = first.preview(CHANGE)
        with self.assertRaises(Conflict):
            second.apply(CHANGE, preview['proposal'], 1, 'cross_' + RUN, True)
        self.assertEqual(second.state()['revision'], 1)
        operation = 'dedupe_' + RUN
        first.apply(CHANGE, preview['proposal'], 1, operation, True)
        duplicate = first.apply(CHANGE, preview['proposal'], 1, operation, True)
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(len(first.actions()), 3)
        with self.assertRaises(Conflict):
            first.apply({**CHANGE, 'material': 'Different document'}, preview['proposal'], 1, operation, True)
        self.assertEqual(second.state()['revision'], 1)

    def test_source_trace_uses_real_graph_paths(self):
        store = self.new_store('sources')
        preview = store.preview(CHANGE)
        store.apply(CHANGE, preview['proposal'], 1, 'sources_' + RUN, True)
        explanation = store.explain('catering')
        ids = {record['source'] for record in explanation['evidence']}
        self.assertEqual(ids, {'notice_v1', 'notice_v2'})
        self.assertTrue(any(record['path'] == ['catering', 'travel', 'register', 'deadline'] for record in explanation['evidence']))
        self.assertTrue(any(record['requirement'] == 'declaration' for record in explanation['evidence']))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RealGraphTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    output = ROOT / 'artifacts' / ('integration_' + RUN + '.json')
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({'actual_falkordb': True, 'run_id': RUN, 'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'mock_graph_used': False, 'online_model_calls': 0, 'events': EVENTS}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(output))
    raise SystemExit(0 if result.wasSuccessful() else 1)
