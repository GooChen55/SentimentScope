"""Check tracked file boundaries and local Markdown links without runtime services."""
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
LOCAL_ONLY = (
    "var/", "docs/reference/", "vendor/mediacrawler/",
    "references/evaluation/",
)
TOKEN = re.compile(
    rb"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    rb"github_pat_[A-Za-z0-9_]{20,})"
)


def main():
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT,
    ).decode("utf-8").split("\0")
    tracked = [name for name in tracked if name]
    errors = []
    checked_links = 0
    for name in tracked:
        path = ROOT / name
        parts = path.relative_to(ROOT).parts
        if name.startswith(LOCAL_ONLY) or any(
            part in {".venv", "node_modules", "__pycache__", ".pytest_cache", "dist"}
            for part in parts
        ) or (".env" in path.name and not path.name.endswith(".example")):
            errors.append(f"Local-only file is tracked: {name}")
        if not path.is_file():
            errors.append(f"Missing tracked file: {name}")
            continue
        content = path.read_bytes()
        if TOKEN.search(content) or re.search(
            rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", content,
        ):
            errors.append(f"Credential pattern detected: {name}")
        if path.suffix != ".md":
            continue
        for link in re.findall(r"\]\(([^)]+)\)", content.decode("utf-8-sig")):
            link = link.strip().strip("<>")
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT):
                errors.append(f"Link escapes repository: {name} -> {link}")
                continue
            relative = target.relative_to(ROOT).as_posix()
            # Dependencies are fetched by the documented setup steps.
            if relative.startswith(("vendor/mediacrawler/", "references/evaluation/")):
                continue
            checked_links += 1
            if not target.exists():
                errors.append(f"Broken local link: {name} -> {link}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Repository checks passed: {len(tracked)} files, {checked_links} local links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
