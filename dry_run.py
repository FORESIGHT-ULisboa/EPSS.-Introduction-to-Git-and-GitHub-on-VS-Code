"""Replay the whole tutorial with three local clones and a local bare repository standing in for GitHub.

    python dry_run.py [--main PATH] [--keep]

No network, no GitHub account. Run it with the epss Python (report.py needs pandas/matplotlib).
It pastes the code exactly as printed in the guide, asserts that every engineered event happens
(rejected push, clean merge, conflicts) and that tools/check_progress.py agrees after each part.
Status snapshots are written to out/stage-*/status.json (input for: python dashboard.py --fake out).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from common import HERE, main_checkout, snippets

PEOPLE = {"A": ("Ana Silva", "ana@example.org"), "B": ("Bruno Costa", "bruno@example.org"),
          "C": ("Carla Dias", "carla@example.org")}
ENV = dict(os.environ, TUTORIAL_OFFLINE="1", GITHUB_REPOSITORY="demo/epss-git-tutorial-g00",
           GIT_TERMINAL_PROMPT="0", MPLBACKEND="Agg")
for k in ("GITHUB_TOKEN", "GH_TOKEN"):
    ENV.pop(k, None)
steps_ok = 0


def ok(condition, what):
    global steps_ok
    if not condition:
        raise SystemExit(f"FAILED: {what}")
    steps_ok += 1
    print(f"  ok  {what}")


def run(cmd, cwd, expect=0, env=ENV):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if expect is not None and (r.returncode == 0) != (expect == 0):
        raise SystemExit(f"FAILED: {' '.join(map(str, cmd))} in {cwd.name} -> {r.returncode}\n{r.stdout}\n{r.stderr}")
    return r


class Clone:
    def __init__(self, work, name, remote):
        self.dir, self.name = work / name, name
        run(["git", "clone", "-q", str(remote), str(self.dir)], work)
        person = PEOPLE.get(name, ("GitHub", "noreply@example.org"))
        for key, value in (("user.name", person[0]), ("user.email", person[1]), ("pull.rebase", "false"),
                           ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
            self.git("config", key, value)

    def git(self, *args, expect=0):
        return run(["git", *args], self.dir, expect)

    def read(self, path):
        return (self.dir / path).read_text(encoding="utf-8")

    def write(self, path, text):
        (self.dir / path).write_text(text, encoding="utf-8", newline="\n")

    def commit(self, message, *paths):
        self.git("add", *paths)
        self.git("commit", "-q", "-m", message)

    def status(self):
        return json.loads(run([sys.executable, "tools/check_progress.py", "--json"], self.dir).stdout)

    def conflicted(self):
        return self.git("diff", "--name-only", "--diff-filter=U").stdout.split()


def expect(member, stage, **want):
    """Compare checkpoint verdicts with what the tutorial should have reached; save a snapshot."""
    st = member.status()
    got = {c["id"].replace("-", "_"): c["ok"] for c in st["checkpoints"]}
    for cid, value in want.items():
        ok(got[cid] is value, f"checkpoint {cid} is {value} after {stage}")
    out = HERE / "out" / f"stage-{stage}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "status.json").write_text(json.dumps(st, indent=1), encoding="utf-8")
    return st


def fill_member(text, letter, name):
    head, rest = text.split(f"## Member {letter}\n", 1)
    block, sep, tail = rest.partition("\n## ")
    block = block.replace("Name: ...", f"Name: {name}").replace("GitHub user: ...", f"GitHub user: {name.split()[0].lower()}")
    block = block.replace("Favourite weather: ...", "Favourite weather: drizzle")
    return f"{head}## Member {letter}\n{block}{sep}{tail}"


def accept_both(text):
    return "".join(l for l in text.splitlines(True) if not l.startswith(("<<<<<<< ", "=======", ">>>>>>> ")))


def switch_on(text):
    """Guide 2.2: delete the raise line, then Toggle Line Comment on the '# ' lines below it."""
    out, after = [], False
    for line in text.splitlines():
        if "raise NotImplementedError" in line:
            after = True
            continue
        if after and line.lstrip().startswith("# "):
            line = line.replace("# ", "", 1)
        out.append(line)
    return "\n".join(out) + "\n"


def paste_report(text, lines):
    marker = "below this line ---\n\n# --- members"
    assert marker in text, "report.py markers changed"
    return text.replace(marker, f"below this line ---\n{lines}# --- members")


def run_all(nb):
    """What 'Run All' leaves in the file: counters and outputs (same on every computer here)."""
    n = 0
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            n += 1
            cell["execution_count"] = n
            cell["outputs"] = [{"output_type": "execute_result", "execution_count": n, "metadata": {},
                                "data": {"text/plain": ["<output>"], "image/png": "iVBORw0KGgo" + "A" * 4000}}]
    return nb


def new_cell(source):
    return {"cell_type": "code", "id": uuid.uuid4().hex[:8], "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.rstrip("\n").splitlines(True)}


def dump(nb):
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def pr_merge(web, number, branch, author, expect_conflict=False):
    """The Merge pull request button: a --no-ff merge on GitHub's side, by the PR author."""
    web.git("fetch", "-q", "origin")
    web.git("checkout", "-q", "main")
    web.git("reset", "-q", "--hard", "origin/main")
    env = dict(ENV, GIT_AUTHOR_NAME=PEOPLE[author][0], GIT_AUTHOR_EMAIL=PEOPLE[author][1])
    r = run(["git", "merge", "--no-ff", "-m", f"Merge pull request #{number} from demo/{branch}", f"origin/{branch}"],
            web.dir, expect=None, env=env)
    if expect_conflict:
        ok(r.returncode != 0 and "CONFLICT" in r.stdout, f"PR #{number} ({branch}) cannot be merged: conflict")
        web.git("merge", "--abort")
        return
    ok(r.returncode == 0, f"PR #{number} ({branch}) merges cleanly")
    web.git("push", "-q", "origin", "main")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--main", type=Path)
    ap.add_argument("--keep", action="store_true", help="keep the temporary folder")
    args = ap.parse_args()
    src = args.main or main_checkout()
    code = snippets(src)
    need = {"report:A", "report:B", "report:C", "notebook:A", "notebook:B"}
    ok(need <= set(code), f"guide contains the {len(need)} code snippets")

    work = Path(tempfile.mkdtemp(prefix="epss-git-dry-"))
    print(f"working in {work}\n\nPart 0")
    seed = work / "seed"
    files = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], src).stdout.split("\n")
    for f in filter(None, files):
        if (src / f).is_file():
            (seed / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / f, seed / f)
    run(["git", "init", "-q", "-b", "main"], seed)
    run(["git", "-c", "user.name=Template", "-c", "user.email=template@example.org", "-c", "core.autocrlf=false",
         "add", "-A"], seed)
    run(["git", "-c", "user.name=Ana Silva", "-c", "user.email=ana@example.org", "commit", "-q", "-m", "Initial commit"], seed)
    remote = work / "github.git"
    run(["git", "clone", "-q", "--bare", str(seed), str(remote)], work)
    A, B, C = (Clone(work, n, remote) for n in "ABC")
    web = Clone(work, "web", remote)
    expect(A, "0-setup", repo=True, first_push=False, everyone=False, conflict=False)

    print("\nPart 1.1  first commit and push")
    A.write("TEAM.md", fill_member(A.read("TEAM.md"), "A", PEOPLE["A"][0]))
    A.commit("Add member A to the team", "TEAM.md")
    A.git("push", "-q")
    B.git("pull", "-q"); C.git("pull", "-q")
    expect(B, "1.1-first-push", first_push=True, everyone=False)

    print("\nPart 1.2  rejected push, clean merge")
    for m in (B, C):
        m.write("TEAM.md", fill_member(m.read("TEAM.md"), m.name, PEOPLE[m.name][0]))
        m.commit(f"Add member {m.name} to the team", "TEAM.md")
    B.git("push", "-q")
    r = C.git("push", expect=None)
    ok(r.returncode != 0 and "rejected" in r.stderr, "C's push is rejected")
    r = C.git("pull", "--no-edit", expect=None)
    ok(r.returncode == 0 and not C.conflicted(), "C's pull merges B's commit without a conflict")
    C.git("push", "-q")
    A.git("pull", "-q"); B.git("pull", "-q")
    expect(A, "1.2-everyone", everyone=True, conflict=False)

    print("\nPart 1.3  conflict on the team name")
    for m, name in ((A, "Rain Check"), (B, "The Cumulonimbus")):
        m.write("TEAM.md", m.read("TEAM.md").replace("(to be decided)", name))
        m.commit("Choose a team name", "TEAM.md")
    A.git("push", "-q")
    ok(B.git("push", expect=None).returncode != 0, "B's push is rejected")
    r = B.git("pull", "--no-edit", expect=None)
    ok(r.returncode != 0 and B.conflicted() == ["TEAM.md"], "B's pull stops with a conflict in TEAM.md only")
    ok(any("conflict markers" in p for p in B.status()["problems"]), "the check reports the conflict markers")
    B.git("checkout", "--theirs", "TEAM.md")  # Accept Incoming Change
    B.git("add", "TEAM.md")
    B.git("commit", "-q", "--no-edit")
    B.git("push", "-q")
    A.git("pull", "-q"); C.git("pull", "-q")
    st = expect(C, "1.3-conflict", conflict=True, prs=False, wired=False)
    ok(not st["problems"], "no problems left after resolving")

    print("\nPart 2  branches and pull requests")
    tasks = {"A": ("feature/stats", "weather/stats.py"), "B": ("feature/temperature", "weather/temperature.py"),
             "C": ("feature/plots", "weather/plots.py")}
    for m in (A, B, C):
        branch, module = tasks[m.name]
        m.git("checkout", "-q", "-b", branch)
        m.write(module, switch_on(m.read(module)))
        m.write("report.py", paste_report(m.read("report.py"), code[f"report:{m.name}"]))
        r = run([sys.executable, "report.py"], m.dir)
        ok("days loaded" in r.stdout, f"{m.name}: report.py runs on {branch}")
        m.commit(f"Add {module} and use it in the report", module, "report.py")
        m.git("push", "-q", "-u", "origin", branch)
    ok(not (C.dir / "outputs").exists() or "outputs" not in C.git("status", "--porcelain").stdout,
       "outputs/ is ignored by git")
    pr_merge(web, 1, tasks["A"][0], "A")
    for number, m in ((2, B), (3, C)):
        branch = tasks[m.name][0]
        pr_merge(web, number, branch, m.name, expect_conflict=True)
        m.git("fetch", "-q", "origin")
        r = m.git("merge", "--no-edit", "origin/main", expect=None)
        ok(r.returncode != 0 and m.conflicted() == ["report.py"], f"{m.name}: merging origin/main conflicts in report.py only")
        m.write("report.py", accept_both(m.read("report.py")))  # Accept Both Changes
        ok("days loaded" in run([sys.executable, "report.py"], m.dir).stdout, f"{m.name}: report.py runs after Accept Both")
        m.git("add", "report.py")
        m.git("commit", "-q", "--no-edit")
        m.git("push", "-q")
        pr_merge(web, number, branch, m.name)
    for m in (A, B, C):
        m.git("checkout", "-q", "main")
        m.git("pull", "-q")
        m.git("branch", "-q", "-d", tasks[m.name][0])
    out = run([sys.executable, "report.py"], A.dir).stdout
    ok(all(s in out for s in ("rain_mm", "tmean_c", "Plot saved to")), "report.py on main prints all three parts")
    expect(A, "2-pull-requests", prs=True, wired=True, notebook=False)

    print("\nPart 3  notebooks")
    nb_tasks = {"A": "notebook/monthly-table", "B": "notebook/mean-temperature"}
    for m in (A, B):
        m.git("checkout", "-q", "-b", nb_tasks[m.name])
        nb = json.loads(m.read("analysis.ipynb"))
        nb["cells"].append(new_cell(code[f"notebook:{m.name}"]))
        m.write("analysis.ipynb", dump(run_all(nb)))
        m.commit("Add a cell to the notebook", "analysis.ipynb")
        m.git("push", "-q", "-u", "origin", nb_tasks[m.name])
    pr_merge(web, 4, nb_tasks["A"], "A")
    pr_merge(web, 5, nb_tasks["B"], "B", expect_conflict=True)
    B.git("fetch", "-q", "origin")
    r = B.git("merge", "--no-edit", "origin/main", expect=None)
    ok(r.returncode != 0 and B.conflicted() == ["analysis.ipynb"], "B: merging origin/main conflicts in the notebook")
    try:
        json.loads(B.read("analysis.ipynb"))
        ok(False, "the conflicted notebook is not valid JSON")
    except ValueError:
        ok(True, "the conflicted notebook is not valid JSON (does not open)")
    ok(any("analysis.ipynb" in p for p in B.status()["problems"]), "the check reports the broken notebook")
    B.git("checkout", "--theirs", "analysis.ipynb")  # Accept All Incoming
    nb = json.loads(B.read("analysis.ipynb"))
    ok("monthly_summary" in dump(nb) and "add_tmean" not in dump(nb), "after Accept All Incoming: A's cell is there, B's is gone")
    nb["cells"].append(new_cell(code["notebook:B"]))
    for cell in nb["cells"]:  # Clear All Outputs
        if cell["cell_type"] == "code":
            cell["execution_count"], cell["outputs"] = None, []
    B.write("analysis.ipynb", dump(nb))
    B.git("add", "analysis.ipynb")
    B.git("commit", "-q", "--no-edit")
    B.git("push", "-q")
    pr_merge(web, 5, nb_tasks["B"], "B")
    for m in (A, B, C):
        m.git("checkout", "-q", "main")
        m.git("pull", "-q")
    st = expect(C, "3-notebook", repo=True, first_push=True, everyone=True, conflict=True, prs=True, wired=True, notebook=True)
    ok(st["done"] == 7 and not st["problems"], "7 of 8 verified offline (protection is only visible on GitHub), no problems")

    cells = [c for c in json.loads(C.read("analysis.ipynb"))["cells"] if c["cell_type"] == "code"]
    program = "\n".join("".join(c["source"]).rstrip().rstrip(";") for c in cells)
    r = run([sys.executable, "-c", program], C.dir)
    ok(r.returncode == 0, "the final notebook's code cells run top to bottom")

    print(f"\nAll {steps_ok} checks passed.")
    if args.keep:
        print(f"kept: {work}")
    else:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
