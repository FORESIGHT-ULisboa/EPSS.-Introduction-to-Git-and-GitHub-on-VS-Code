"""Shared helpers for the instructor scripts."""
import re
import subprocess
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main_checkout():
    """Folder of the student-facing checkout (the first git worktree)."""
    out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=HERE,
                         capture_output=True, text=True).stdout
    first = re.search(r"^worktree (.+)$", out, re.M)
    if not first:
        raise SystemExit("Cannot find the main checkout; pass --main PATH.")
    return Path(first.group(1))


def snippets(main):
    """{name: code} for every '<!-- snippet: name -->' fenced block in the guide."""
    found = {}
    for md in sorted((main / "docs" / "guide").glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for name, body in re.findall(r"<!-- snippet: (\S+) -->\s*\n[ \t]*```python\n(.*?)\n[ \t]*```", text, re.S):
            found[name] = textwrap.dedent(body) + "\n"
    return found
