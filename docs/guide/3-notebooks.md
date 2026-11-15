# Part 3 · Jupyter notebooks (12 min)

Notebooks are the place where groups get hurt most. A `.ipynb` file is not only your code: it also stores every output, every plot (as thousands of characters) and a counter for each cell you ran. Git sees all of that as changes.

A and B both edit the shared notebook `analysis.ipynb`. C reviews.

## 3.1 Two people in the same notebook

- [ ] **A + B** On `main`, **`···` › Pull**. Then create a branch (bottom-left corner, <mark>**Create new branch…**</mark>): A `notebook/monthly-table`, B `notebook/mean-temperature`.
- [ ] **A + B** Open `analysis.ipynb`. Click **Select Kernel** (top right), **Python Environments**, **epss**. Click **Run All**.
- [ ] **A + B** Add a code cell at the very end (**+ Code**), paste your lines, run the cell, and save.

  Member A:

  <!-- snippet: notebook:A -->
  ```python
  from weather.stats import monthly_summary

  monthly_summary(df)
  ```

  Member B:

  <!-- snippet: notebook:B -->
  ```python
  from weather.temperature import add_tmean

  add_tmean(df)["tmean_c"].plot(ylabel="°C", title="Mean temperature");
  ```

- [ ] **A + B** In the Source Control view, click `analysis.ipynb`. You wrote three lines, and the diff shows changes in every cell: outputs, pictures, counters.

![VS Code: notebook diff with outputs and execution counts](../img/24-notebook-diff.png)

- [ ] **A + B** Stage, commit (`Add monthly table to the notebook` / `Add mean temperature plot to the notebook`), **Publish Branch**, and open a pull request with **C** as reviewer.

![GitHub: B's notebook pull request, base main, compare notebook/mean-temperature, C as reviewer](../img/24a-notebook-pull-request.png)

- [ ] **C** Open both pull requests, tab **Files changed**. Try to read what your teammates did. Then **Submit review › Approve › Submit review** on both.
- [ ] **A** **Merge pull request › Confirm merge › Delete branch**.
- [ ] **B** Once A's pull request is merged, yours says it has conflicts. In VS Code, check that the corner shows `notebook/mean-temperature` and that the Source Control view lists no changes (if the notebook shows up there again, save it and **Discard Changes** on it). Close the notebook's tab.
- [ ] **B** **`···` › Fetch**, then **`···` › Branch › Merge…** with <mark>**origin/main**</mark>, as in Part 2. Git stops with a conflict in `analysis.ipynb`.

<div class="important" style="background: #fff1e5; color: #1f2328; border-left: 4px solid #e8590c; border-radius: 6px; padding: 0.1em 1em; margin: 1em 0">

🛑 **The way out of any merge: `Git: Abort Merge`.** While a merge is open (the Commit button says **Continue**), **Ctrl+Shift+P**, type `Git: Abort Merge`, Enter. Your files and branch go back to exactly how they were before the merge, and nothing is lost. Then start again calmly. It has no button: the Command Palette is the only way.

</div>

- [ ] **B** Click `analysis.ipynb` under **Merge Changes**. It no longer opens as a notebook: it is one long text with marker lines somewhere inside. Do not try to repair it by hand.

![VS Code: a notebook in conflict, shown as text](../img/25-notebook-conflict.png)

- [ ] **B** In the Source Control view, right-click `analysis.ipynb` and choose **Accept All Incoming**. You now have the version from `main` (with A's cell), and the notebook opens again. Your own cell is gone.
- [ ] **B** Add your cell again at the end and run it.

![VS Code: the notebook after the merge, with A's monthly table and B's mean temperature cell, the merge waiting for Continue](../img/25a-notebook-joint.png)
- [ ] **B** Click **Clear All Outputs** in the toolbar at the top of the notebook, next to **Run All** and **Restart** (on a narrow window it may be behind that toolbar's **`···`**). Save.
- [ ] **B** Click **+** on `analysis.ipynb`, **Continue**, **Sync Changes**. In the browser: **Merge pull request › Confirm merge › Delete branch**.
- [ ] **All** Back to `main` (bottom-left corner), then **`···` › Pull**. Open the notebook: both new cells, no outputs. **Run All** shows it works.

<!-- checkpoint: notebook -->
> **Checkpoint 8.** On `main`, the notebook has both new cells and no outputs.

<details>
<summary style="color: #e5484d">⚠️ <b>If it went wrong</b></summary>

- *No "Accept All Incoming" in the menu*: open a terminal (**Terminal › New Terminal**) and type `git checkout --theirs analysis.ipynb`. It does the same.
- *The notebook still does not open*: `Git: Abort Merge`, then start the merge again.
- *"No module named weather"*: the notebook must stay in the top folder of the repository, next to `report.py`.

</details>

## 3.2 Three rules for notebooks in a group

<div class="key" style="background: #fff8c5; color: #1f2328; border-left: 4px solid #d4a72c; border-radius: 6px; padding: 0.1em 1em; margin: 1em 0">

1. **One owner at a time.** Agree who is editing a notebook, and let nobody else touch it until that person's pull request is merged.
2. **Clear All Outputs, save, then commit.** The diff then shows your code and nothing else, and conflicts become rare. Keep the outputs only in the commit you hand in: for that one, restart the kernel, **Run All**, check it runs from top to bottom, save and commit.
3. **Put the logic in `.py` files.** Functions in `weather/*.py` merge easily, as you saw in Part 2. The notebook only calls them and shows the results.

</div>

Next: [Part 4 · When things go wrong](4-when-things-go-wrong.md)
