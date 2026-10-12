"""Workspace locations shared by the research API and agent engines."""
import os
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = SERVICE_ROOT.parents[1]
DATA_ROOT = Path(os.getenv('SENTIMENT_RESEARCH_DATA_DIR', WORKSPACE_ROOT / 'var/research')).resolve()
ENV_FILE = str(Path(os.getenv('SENTIMENT_RESEARCH_ENV_FILE', WORKSPACE_ROOT / 'config/research.env')).resolve())
LOG_DIR = WORKSPACE_ROOT / 'var/logs/research'
