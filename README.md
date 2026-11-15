# Instructor tools for the Git tutorial

This branch (`instructor`) is separate from `main` on purpose. Students get `main` through **Use this template**, which copies only the default branch, so nothing here reaches them.

On this PC the two branches are two folders (git worktrees):

| Folder | Branch | What |
|---|---|---|
| `EPSS. Introduction to Git and GitHub on VS Code` | `main` | what students receive: guide, exercise files, progress check |
| `epss-git-tutorial-instructor` | `instructor` | this folder |

Run the Python scripts from an **Anaconda Prompt with `epss` activated** (`conda activate epss`), from this folder.

| Script | Use |
|---|---|
| `dry_run.py` | Replays the whole tutorial with three local clones, no GitHub. Run it after any change to the guide or the exercise files: it pastes the code printed in the guide and fails if a rejected push, a merge or a conflict stops happening as the guide says. |
| `dashboard.py` | Progress of all groups, for the projector. |
| `setup_member.ps1` | Gives one clone the identity of member A, B or C (for recording). |
| `make_placeholders.py` | Grey placeholders for missing screenshots; `--list` prints the shot list. |
| `build_pdf.py` | PDF handout from the same Markdown as the web page. Writes to `dist/`. |

## In class: the dashboard

1. Students do one thing (guide, step 0.2): member A pastes the repository address into your class sheet.
2. Either copy the addresses into `groups.txt` (one per line; any other text on the line becomes the label, e.g. `G01 https://github.com/ana/epss-git-tutorial-g01`), or pass the sheet's CSV link. If the sheet is shared as "anyone with the link", replace `/edit?usp=sharing` with `/export?format=csv` (add `&gid=<n>` for a tab other than the first); otherwise publish it (**File › Share › Publish to web › CSV**).
3. Run one of:

   ```
   python dashboard.py groups.txt
   python dashboard.py --sheet "https://docs.google.com/spreadsheets/d/<SHEET_ID>/export?format=csv"
   ```

The page shows groups × the eight checkpoints, a red **broken** flag when a group's last commit has conflict markers, a notebook that is not valid, or a syntax error, and a **quiet N min** flag when nothing has moved for 10 minutes (`--stuck`). The list is re-read every round (`--every`, 45 s), so groups appear as they register. It only reads; it uses your `gh` sign-in to avoid GitHub's rate limit.

A group's status appears about a minute after its first push. Before that the row says *no status yet*.

To see it without any group: `python dry_run.py` then `python dashboard.py --fake out`.

## Recording: three members on one PC

**Once**

1. Update Git for Windows (this PC had 2.36.1; the students' guide assumes a current version).
2. Three browser profiles (e.g. Edge profiles), each signed in to one GitHub account: yours (A) and the two others (B, C). Give each a theme colour matching the VS Code windows: A blue, B green, C orange.
3. For B and C, in their browser profile: **GitHub › Settings › Developer settings › Personal access tokens › Tokens (classic) › Generate new token (classic)**, scope **`public_repo`** only, expiry 7 days. Fine-grained tokens do not work here: they cannot reach a repository owned by another person.
4. Three folders outside OneDrive, each with a `.env` made from `.env.example`:

   ```text
   C:\EPSS_git_demo\A\.env     MEMBER=A, your name and email, GITHUB_USER and GITHUB_TOKEN empty
   C:\EPSS_git_demo\B\.env     MEMBER=B, name, email, user and token of account B
   C:\EPSS_git_demo\C\.env     MEMBER=C, name, email, user and token of account C
   ```

   The email must be one registered in that GitHub account, or the commits will not show the account's picture.

**Each take**

1. As A, in the browser: create the group repository from the template and invite B and C (guide 0.2). Accept the invitations in profiles B and C.
2. Clone it three times with **Git: Clone** in VS Code, into `A`, `B` and `C` (guide 0.3). The repository is public, so cloning needs no sign-in.
3. Off camera, once per clone:

   ```powershell
   .\setup_member.ps1 C:\EPSS_git_demo\A\epss-git-tutorial-g01
   ```

   It reads the `.env` from the clone or its parent folder and, **in that clone only**: sets the commit name and email; makes git take the token from the `.env` when pushing (the token is not copied anywhere); colours the VS Code window and titles it `MEMBER B`; stops VS Code from offering its own GitHub sign-in. It prints which GitHub user the token belongs to. `-Undo` removes all of it. Reload the VS Code window afterwards (**Developer: Reload Window**).
4. Follow the guide. Pushes from B's and C's windows are silent (no sign-in), as are yours.

**To film the real first sign-in** (guide 1.1), which the `.env` route skips: use member A's window before running `setup_member.ps1` on it, after removing your stored GitHub credential (**Windows Credential Manager › Windows Credentials › `git:https://github.com` › Remove**). You sign in again on camera; nothing else is lost.

**Things to know while recording**

- The two other accounts' user names and pictures will be visible in the video and in screenshots.
- Click paths checked on screen in the first recording run (VS Code 1.145, Nov 2026): first sign-in (*Connect to GitHub* window), rejected-push message, merge **Continue** button, ruleset form, pull request and review pages, **Branch › Merge…** list, **Clear All Outputs**. Not yet seen on screen: **Accept All Incoming** in the Source Control right-click menu (3.1), **Start a review** on a line comment (2.4), the macOS sign-in variant. Correct the guide where the screen disagrees.
- During a recording, **Sync Changes** hides the rejected push in 1.2: C must use **`···` › Push**. And leave the team name alone until 1.3.
- Delete the two tokens on GitHub after recording.

## Screenshots

The guide refers to 37 images in `docs/img/` on `main`. They are grey placeholders until you save a real screenshot under the same name (PNG, about 1280 px wide). `python make_placeholders.py --list` prints each file name with what it must show. After replacing them: `python build_pdf.py`.

## After editing the guide

1. `python dry_run.py` (must end with *All … checks passed*).
2. `python build_pdf.py`.
3. Commit and push `main` through a pull request; GitHub Pages republishes the web page within a minute or two.

Code blocks in the guide that students paste are marked with a hidden comment, `<!-- snippet: name -->`. The dry run reads them by that name, so keep the comments when editing.
