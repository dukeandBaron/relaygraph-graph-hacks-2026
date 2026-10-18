import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
local_dependencies = root / 'runtime' / 'deps'
if local_dependencies.is_dir():
    sys.path.insert(0, str(local_dependencies))

from relaygraph.web import create_app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', '52188')), debug=False, use_reloader=False, threaded=True)
