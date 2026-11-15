"""Instructor dashboard: progress of every group, for the projector.

    python dashboard.py groups.txt        one repository address per line; other text on the line is the label
    python dashboard.py --sheet URL       a Google Sheet published as CSV (File > Share > Publish to web > CSV)
    python dashboard.py --fake out        folders with a status.json each (testing; dry_run.py writes them)

Reads status.json from each repository's tutorial-status branch (written by the group's own GitHub
Actions run). Read-only. Uses your GitHub CLI sign-in (gh auth token) or GH_TOKEN when available,
which lifts the rate limit; works without, for a handful of groups. The list is re-read on every
round, so groups appear as they register. Standard library only.
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = re.compile(r"github\.com[/:]+([\w.-]+)/([\w.-]+?)(?:\.git)?(?=[/\s,;\"']|$)")
state = {"groups": [], "checked": None, "error": ""}
memory = {}  # slug -> {"etag", "status", "done", "since"}


def token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def read_list(args):
    """[(label, slug)] from the text file or the published sheet."""
    if args.sheet:
        with urllib.request.urlopen(args.sheet, timeout=15) as r:
            rows = list(csv.reader(io.StringIO(r.read().decode("utf-8-sig"))))
    else:
        rows = [[line] for line in Path(args.groups).read_text(encoding="utf-8").splitlines()]
    groups, seen = [], set()
    for row in rows:
        text = " ".join(row)
        m = REPO.search(text)
        if not m or text.lstrip().startswith("#"):
            continue
        slug = f"{m.group(1)}/{m.group(2)}"
        if slug.lower() in seen:
            continue
        seen.add(slug.lower())
        others = [c.strip() for c in (row if args.sheet else [REPO.sub("", text).replace("https://", "")])
                  if c.strip() and not REPO.search(c)]
        groups.append((others[0].strip(" ,;:-") if others and others[0].strip(" ,;:-") else slug, slug))
    return groups


def fetch_status(slug, tok):
    """Latest status.json of one group; None while there is none. Conditional request (ETag)."""
    mem = memory.setdefault(slug, {"etag": "", "status": None, "done": -1, "since": time.time()})
    req = urllib.request.Request(
        f"https://api.github.com/repos/{slug}/contents/status.json?ref=tutorial-status",
        headers={"Accept": "application/vnd.github.raw+json", "User-Agent": "epss-git-dashboard"})
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    if mem["etag"]:
        req.add_header("If-None-Match", mem["etag"])
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            mem["status"], mem["etag"] = json.load(r), r.headers.get("ETag", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            mem["status"] = None
        elif e.code != 304:
            raise
    return mem


def poll(args):
    tok = "" if args.fake else token()
    while True:
        try:
            if args.fake:
                found = [(p.parent.name, p) for p in sorted(Path(args.fake).glob("*/status.json"))]
                groups = []
                for label, path in found:
                    mem = memory.setdefault(label, {"done": -1, "since": time.time()})
                    mem["status"] = json.loads(path.read_text(encoding="utf-8"))
                    groups.append((label, label))
            else:
                groups = read_list(args)
                for _, slug in groups:
                    fetch_status(slug, tok)
            rows = []
            for label, slug in groups:
                mem, st = memory[slug], memory[slug]["status"]
                if st and st["done"] != mem["done"]:
                    mem["done"], mem["since"] = st["done"], time.time()
                rows.append({"label": label, "repo": slug, "status": st,
                             "quiet_min": int((time.time() - mem["since"]) / 60)})
            state.update(groups=rows, checked=datetime.datetime.now().strftime("%H:%M:%S"), error="")
        except Exception as e:  # keep the projector alive; show the reason
            state["error"] = f"{type(e).__name__}: {e}"
        time.sleep(args.every)


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Groups · Git tutorial</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>
:root{--bg:#f7f7f5;--s:#fff;--t:#1d2228;--m:#5b6672;--l:#dfe3e8;--ok:#1a7f37;--okbg:#dff3e6;--bad:#b42318;--warn:#9a6700;--warnbg:#fff4d6}
@media (prefers-color-scheme:dark){:root{--bg:#15181c;--s:#1d2126;--t:#e6e9ed;--m:#9aa5b1;--l:#343b44;--ok:#4ac26b;--okbg:#1c3626;--bad:#f47067;--warn:#d4a72c;--warnbg:#3a3015}}
body{margin:0;padding:1.2rem 1.5rem;background:var(--bg);color:var(--t);font:18px/1.4 system-ui,"Segoe UI",sans-serif}
h1{font-size:1.4rem;margin:0 0 .2rem}.sub{color:var(--m);margin:0 0 1rem}.err{color:var(--bad)}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--s)}
th,td{border:1px solid var(--l);padding:.4rem .6rem;text-align:center;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{color:var(--m);font-weight:600;font-size:.9rem}
td.ok{background:var(--okbg);color:var(--ok);font-weight:700}td.no{color:var(--l)}td.unk{color:var(--warn)}
td.n{font-variant-numeric:tabular-nums;font-weight:700}tr.done td.n{color:var(--ok)}
.flag{font-size:.85rem;padding:.05rem .5rem;border-radius:1rem;margin-left:.3rem}
.flag.bad{background:var(--bad);color:#fff}.flag.quiet{background:var(--warnbg);color:var(--warn)}
a{color:inherit}ol{color:var(--m);font-size:.9rem;columns:2;margin:1rem 0 0;padding-left:1.4rem}
td.none{color:var(--m);font-style:italic;text-align:left}
</style></head><body><h1>Git tutorial · groups</h1><p class="sub" id="sub"></p>
<div class="wrap"><table id="t"></table></div><ol id="legend"></ol><script>
const STUCK=__STUCK__;
async function draw(){
  const s=await (await fetch('api/groups',{cache:'no-store'})).json();
  const withStatus=s.groups.filter(g=>g.status), titles=withStatus[0]?.status.checkpoints.map(c=>c.title)||[];
  const finished=withStatus.filter(g=>g.status.done>=g.status.total-0&&g.status.done===g.status.total).length;
  sub.innerHTML=`${s.groups.length} groups · ${withStatus.length} reporting · ${finished} finished · checked ${s.checked||'…'}`+(s.error?` · <span class="err">${s.error}</span>`:'');
  const n=titles.length||8, head='<tr><th>Group</th>'+Array.from({length:n},(_,i)=>`<th title="${titles[i]||''}">${i+1}</th>`).join('')+'<th>Done</th><th>Last change</th></tr>';
  const rows=s.groups.map(g=>{
    const link=`<a href="https://github.com/${g.repo}" target="_blank" rel="noopener">${g.label}</a>`;
    if(!g.status) return `<tr><td>${link}</td><td class="none" colspan="${n+2}">no status yet (no push since the repository was created, or wrong address)</td></tr>`;
    const st=g.status, done=st.done===st.total;
    const cells=st.checkpoints.map(c=>c.ok===true?'<td class="ok">✓</td>':c.ok===null?'<td class="unk">?</td>':'<td class="no">·</td>').join('');
    const flags=(st.problems?.length?`<span class="flag bad" title="${st.problems.join('; ')}">broken</span>`:'')+(!done&&g.quiet_min>=STUCK?`<span class="flag quiet">quiet ${g.quiet_min} min</span>`:'');
    const when=new Date(st.updated).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
    return `<tr class="${done?'done':''}"><td>${link}${flags}</td>${cells}<td class="n">${st.done}/${st.total}</td><td>${when}</td></tr>`;
  }).join('');
  t.innerHTML=head+rows; legend.innerHTML=titles.map(x=>`<li>${x}</li>`).join('');
}
draw(); setInterval(draw, 5000);
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("groups", nargs="?", default="groups.txt")
    ap.add_argument("--sheet", help="URL of a Google Sheet published as CSV")
    ap.add_argument("--fake", help="folder with <name>/status.json files, instead of GitHub")
    ap.add_argument("--every", type=int, default=45, help="seconds between rounds (default 45)")
    ap.add_argument("--stuck", type=int, default=10, help="minutes without progress before a group is flagged")
    ap.add_argument("--port", type=int, default=8780)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()
    if not (args.sheet or args.fake) and not Path(args.groups).exists():
        raise SystemExit(f"{args.groups} not found. Create it with one repository address per line, or use --sheet URL.")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/api/groups"):
                body, kind = json.dumps(state).encode(), "application/json"
            else:
                body, kind = PAGE.replace("__STUCK__", str(args.stuck)).encode(), "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    threading.Thread(target=poll, args=(args,), daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Dashboard: {url}   (Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
