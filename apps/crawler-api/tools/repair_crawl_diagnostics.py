"""Enrich the two known failed tasks without changing status, data or timestamps."""
import json
from pathlib import Path
from engine_runtime import failure_details

root = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(root))
from app.paths import DATA_ROOT
path = DATA_ROOT / "tasks.json"
tasks = json.loads(path.read_text(encoding="utf-8"))
target_ids = {"fa04fcdb", "5d085efe"}
changed = 0
for task in tasks:
    if task["task_id"] not in target_ids or task["status"] != "failed":
        continue
    summary = task.get("result", {}).get("crawl_results", {}).get("platform_summary", {})
    for platform, result in summary.items():
        log = Path(result.get("output_directory", "")) / "engine.log"
        if log.exists() and "TargetClosedError" in log.read_text(encoding="utf-8", errors="replace"):
            details = failure_details(type("TargetClosedError", (Exception,), {})(""))
            result.update(details)
            task["error"] = f"{platform}：{details['error']}"
            changed += 1
if changed:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(tasks, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)
print(f"Updated diagnosis for {changed} known failed platform results")
