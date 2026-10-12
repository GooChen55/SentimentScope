"""Paths for the crawler service, kept separate from vendor code and local data."""
import os
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SERVICE_ROOT.parents[1]
DATA_ROOT = Path(os.getenv('SENTIMENT_CRAWLER_DATA_DIR', WORKSPACE_ROOT / 'var/crawler')).resolve()
ENV_FILE = Path(os.getenv('SENTIMENT_CRAWLER_ENV_FILE', WORKSPACE_ROOT / 'config/crawler.env')).resolve()
DB_CONFIG_FILE = WORKSPACE_ROOT / 'config/crawler-database.json'
PROFILE_ROOT = WORKSPACE_ROOT / 'var/browser/mediacrawler'
