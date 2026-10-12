import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import uvicorn

if __name__ == '__main__':
    uvicorn.run('app.web.main:app', host='127.0.0.1', port=9000, access_log=False)
