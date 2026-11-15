"""Build the PDF handout from the same Markdown the web page shows.

    python build_pdf.py [--main PATH] [--out FILE] [--edge PATH]

Starts the local page of tools/check_progress.py, prints its print view (?print=1) with
headless Microsoft Edge, stops the server. Run it again after replacing screenshots.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from common import HERE, main_checkout

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--main", type=Path)
    ap.add_argument("--out", type=Path, default=HERE / "dist" / "EPSS - Git and GitHub in VS Code - group tutorial.pdf")
    ap.add_argument("--edge", default=next((p for p in EDGE if Path(p).exists()), None))
    args = ap.parse_args()
    if not args.edge:
        raise SystemExit("Microsoft Edge not found; pass --edge PATH (Chrome works too).")
    root = args.main or main_checkout()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    server = subprocess.Popen([sys.executable, "-u", "tools/check_progress.py", "--serve", "--port", "8795"],
                              cwd=root, stdout=subprocess.PIPE, text=True)
    try:
        url = re.search(r"http://\S+", server.stdout.readline()).group(0)
        subprocess.run([args.edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=20000", f"--print-to-pdf={args.out}", url + "?print=1"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    finally:
        server.terminate()
    print(f"written: {args.out}  ({args.out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
