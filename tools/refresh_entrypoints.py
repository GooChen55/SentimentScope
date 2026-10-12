"""Regenerate Windows console launchers for the current moved virtual environment."""
import json
import sys
import argparse
from importlib.metadata import distributions
from pathlib import Path

from pip._vendor.distlib.scripts import ScriptMaker

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--environment', type=Path, default=Path(sys.prefix))
environment = parser.parse_args().environment.resolve()
workspace = Path(__file__).resolve().parents[1]
if not environment.is_relative_to(workspace) or environment.name != '.venv':
    raise SystemExit('Choose a virtual environment inside this workspace')
scripts = environment / 'Scripts'
executable = scripts / 'python.exe'
if not executable.is_file():
    raise SystemExit('Missing virtual-environment Python')
maker = ScriptMaker(None, str(scripts))
maker.executable = str(executable)
maker.clobber = True
maker.variants = {""}
count = 0
installed = list(distributions(path=[str(environment / 'Lib/site-packages')]))
for distribution in installed:
    for entrypoint in distribution.entry_points:
        if entrypoint.group not in {"console_scripts", "gui_scripts"}:
            continue
        maker.make(f"{entrypoint.name} = {entrypoint.value}",
                   {"gui": entrypoint.group == "gui_scripts"})
        count += 1
if any(dist.metadata['Name'].lower() == 'pip' for dist in installed):
    maker.make(f"pip{sys.version_info.major}.{sys.version_info.minor} = pip._internal.cli.main:main")
    count += 1
print(json.dumps({"environment": str(environment), "refreshed_entrypoints": count}))
