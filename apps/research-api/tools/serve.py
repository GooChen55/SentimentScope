import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn

if __name__ == '__main__':
    uvicorn.run('app.app:app', host='127.0.0.1', port=5001, access_log=False)
