"""Load the preserved content-table schema without importing a legacy crawler runtime."""
import importlib.util
import sys
from app.paths import WORKSPACE_ROOT

source = WORKSPACE_ROOT / 'vendor/content-schema/models.py'
spec = importlib.util.spec_from_file_location('sentimentscope_content_schema', source)
if spec is None or spec.loader is None:
    raise ImportError('Missing vendor/content-schema/models.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Base = module.Base
