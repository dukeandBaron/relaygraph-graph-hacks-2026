import logging
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .store import Conflict, DatabaseUnavailable, GraphStore, tenant_graph

ROOT = Path(__file__).resolve().parents[1]


def create_app(store_factory=GraphStore):
    app = Flask(__name__, static_folder=None)
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
    stores, lock = {}, threading.Lock()

    def store():
        tenant = request.headers.get('X-Workspace', 'demo')
        tenant_graph(tenant)
        with lock:
            if tenant not in stores:
                if len(stores) >= 32:
                    raise ValueError('This local demo has reached its 32-workspace limit.')
                stores[tenant] = store_factory(tenant)
            return stores[tenant]

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('Send a JSON object.')
        return data

    @app.before_request
    def same_origin_writes():
        if request.method == 'POST':
            origin = request.headers.get('Origin')
            if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
                return jsonify(error='Cross-origin writes are not enabled.'), 403

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(Conflict)
    def conflict(error):
        return jsonify(error=str(error)), 409

    @app.errorhandler(DatabaseUnavailable)
    def unavailable(error):
        return jsonify(error=str(error), database='unavailable', fallback=False), 503

    @app.errorhandler(Exception)
    def unexpected(error):
        if isinstance(error, HTTPException):
            return jsonify(error=error.description), error.code
        logging.exception('RelayGraph request failed')
        return jsonify(error='The graph request failed. Inspect the local server log; no success or substitute state was returned.'), 500

    @app.get('/')
    def home():
        return send_from_directory(ROOT / 'web', 'index.html')

    @app.get('/assets/<path:name>')
    def asset(name):
        return send_from_directory(ROOT / 'web', name)

    @app.get('/api/state')
    def state():
        return jsonify(store().state())

    @app.post('/api/seed')
    def seed():
        result = store().seed()
        return jsonify(**result, state=store().state())

    @app.post('/api/preview')
    def preview():
        data = body()
        if set(data) != {'change'}:
            raise ValueError('Only the change field is accepted.')
        return jsonify(store().preview(data['change']))

    @app.post('/api/adopt')
    def adopt():
        data = body()
        if set(data) != {'change', 'proposal', 'expectedRevision', 'operationId', 'confirmed'}:
            raise ValueError('The command must contain only the documented adoption fields.')
        return jsonify(store().apply(data['change'], data['proposal'], data['expectedRevision'], data['operationId'], data['confirmed']))

    @app.get('/api/explain/<task>')
    def explain(task):
        return jsonify(store().explain(task))

    @app.get('/api/actions')
    def actions():
        return jsonify(actions=store().actions())

    @app.get('/api/tools')
    def tools():
        return jsonify(protocol='read-only graph tools for an external assistant; not an autonomous LLM endpoint', tools=[{'name': 'explain_task', 'path': '/api/explain/<task>', 'method': 'GET'}, {'name': 'list_review_actions', 'path': '/api/actions', 'method': 'GET'}, {'name': 'inspect_graph', 'path': '/api/state', 'method': 'GET'}])

    return app
