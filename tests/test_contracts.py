import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'runtime/deps')]
from relaygraph.store import DatabaseUnavailable, tenant_graph, validate_change
from relaygraph.web import create_app


class UnavailableStore:
    def __init__(self, tenant):
        self.tenant = tenant

    def state(self):
        raise DatabaseUnavailable('Graph unavailable in this explicitly injected HTTP boundary test.')


class Contracts(unittest.TestCase):
    def test_tenant_isolation_and_namespace_restriction(self):
        self.assertNotEqual(tenant_graph('demo'), tenant_graph('reviewer'))
        self.assertEqual(tenant_graph('demo'), tenant_graph('demo'))
        for value in ['../demo', 'demo MATCH (n)', '', 'A', 'x'*33]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                tenant_graph(value)

    def test_dates_must_be_real_and_explicitly_zoned(self):
        for deadline in ['2026-02-30T17:00:00+08:00', '2026-10-19T17:00', 'tomorrow', '2026-10-19T17:00:00Z']:
            with self.subTest(deadline=deadline), self.assertRaises(ValueError):
                validate_change({'deadline': deadline, 'material': 'Form'})

    def test_extra_input_fields_and_controls_are_rejected(self):
        data = {'deadline': '2026-10-19T17:00:00+08:00', 'material': 'Form'}
        with self.assertRaises(ValueError):
            validate_change({**data, 'query': 'MATCH (n) DELETE n'})
        with self.assertRaises(ValueError):
            validate_change({**data, 'material': 'secret\ncommand'})

    def test_dependency_outage_is_not_a_successful_demo(self):
        client = create_app(UnavailableStore).test_client()
        result = client.get('/api/state')
        self.assertEqual(result.status_code, 503)
        self.assertFalse(result.json['fallback'])
        self.assertNotIn('nodes', result.json)

    def test_cross_origin_write_is_rejected_before_database(self):
        client = create_app(UnavailableStore).test_client()
        result = client.post('/api/seed', json={}, headers={'Origin': 'https://outside.example'})
        self.assertEqual(result.status_code, 403)

    def test_payload_extensions_and_invalid_workspace_are_rejected(self):
        client = create_app(UnavailableStore).test_client()
        result = client.post('/api/preview', json={'change': {}, 'query': 'unsafe'})
        self.assertEqual(result.status_code, 400)
        result = client.get('/api/state', headers={'X-Workspace': '../outside'})
        self.assertEqual(result.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
