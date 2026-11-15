# Part 4 · When things go wrong (5 min, then keep for reference)

Read the first recipe together now. Keep the rest for the day you need it.

<div class="key" style="background: #fff8c5; color: #1f2328; border-left: 4px solid #d4a72c; border-radius: 6px; padding: 0.1em 1em; margin: 1em 0">

💡 Before anything else, two questions tell you where you are: **which branch?** (bottom-left corner) and **what changed?** (Source Control view). The task **Tutorial: check progress** answers both.

</div>

## Recipes

Click a problem to see its fix.

<details open>
<summary style="color: #e5484d">⚠️ <b>I committed on <code>main</code> by mistake, and the push is refused</b></summary>

The message says *protected branch*, or *changes must be made through a pull request*.

1. Click `main` in the bottom-left corner, **Create new branch…**, give it a name. Your commit comes with you.
2. **Publish Branch**, then open a pull request as usual.
3. Put your local `main` back in line with GitHub: switch to `main`, open a terminal and type `git reset --hard origin/main`.

</details>

<details>
<summary style="color: #e5484d">⚠️ <b>I want to undo my last commit</b> (not pushed yet)</summary>

**`···` › Commit › Undo Last Commit**. The commit disappears; its changes are back under Staged Changes. Not possible during a merge: abort the merge first (orange box below).

</details>

<details>
<summary style="color: #e5484d">⚠️ <b>A merged pull request broke <code>main</code></b></summary>

Open that pull request on GitHub and click **Revert**. It creates a new pull request that undoes it. Nothing is erased from the history.

</details>

<div class="important" style="background: #fff1e5; color: #1f2328; border-left: 4px solid #e8590c; border-radius: 6px; padding: 0.1em 1em; margin: 1em 0">

🛑 **I am in the middle of a merge and lost.** You can tell by the Commit button, which says **Continue**, or by the message *Cannot do a soft reset in the middle of a merge*. **Ctrl+Shift+P**, `Git: Abort Merge`. Everything is as before the merge. It has no button or menu: the Command Palette is the only way.

</div>

<details>
<summary style="color: #e5484d">⚠️ <b>VS Code will not switch branch or pull: "your local changes would be overwritten"</b></summary>

You have changes that are not committed. Commit them. Or park them: **`···` › Stash › Stash**, and later **`···` › Stash › Pop Stash**.

</details>

<details>
<summary style="color: #e5484d">⚠️ <b>Pull says "need to specify how to reconcile divergent branches"</b></summary>

The third line of step 0.1 is missing on this computer: `git config --global pull.rebase false`.

</details>

<details>
<summary style="color: #e5484d">⚠️ <b>Push is refused with 403, or asks me to sign in again</b></summary>

You are signed in with another GitHub account, or you never accepted the invitation to the repository.

</details>

<details>
<summary style="color: #e5484d">⚠️ <b>Some commits show a grey face on GitHub instead of my picture</b></summary>

The email in `git config --global user.email` is not one of the emails of your GitHub account. Fix it (step 0.1); new commits will be linked.

</details>

<details>
<summary style="color: #e5484d">⚠️ <b>Nothing works any more</b> (the last resort, which always works)</summary>

Everything you pushed is safe on GitHub. Rename your folder (for example add `-broken`), clone again (step 0.3), and copy over any file you had not committed. Keep the broken folder until the end of the day.

</details>

<div class="important" style="background: #fff1e5; color: #1f2328; border-left: 4px solid #e8590c; border-radius: 6px; padding: 0.1em 1em; margin: 1em 0">

🛑 **Never** use `git push --force` on a branch you share. It erases your teammates' work on GitHub. If something seems to need it, ask first.

</div>

## Five habits

<div class="key" style="background: #fff8c5; color: #1f2328; border-left: 4px solid #d4a72c; border-radius: 6px; padding: 0.1em 1em; margin: 1em 0">

1. **Pull before you start, push before you stop.**
2. **One task, one branch, one pull request.** `main` always works.
3. **Read the diff before every commit.**
4. **Small commits, with a message that says what and why.**
5. **Notebooks: one owner at a time, outputs cleared.**

</div>

## Words

| Word | Meaning |
|---|---|
| repository (repo) | the project folder with its whole history |
| commit | a saved snapshot, with an author, a date and a message |
| stage | choose which changes go into the next commit |
| push / pull | send your commits to GitHub / bring the others' commits to you |
| fetch | ask GitHub what is new, without changing your files |
| clone | copy a repository from GitHub to your computer, once |
| branch | a separate line of commits; `main` is the shared one |
| merge | combine two lines of commits |
| conflict | both sides changed the same lines; people decide the result |
| pull request (PR) | a GitHub page proposing to merge a branch into `main` |
| review | a teammate reads the pull request and approves it |
| origin | the name Git gives to the repository on GitHub; `origin/main` is GitHub's `main` |

## For your real project

Do the same, for real: one person creates the repository and invites the others (0.2), protects `main` (2.1), and from then on everybody works as in Part 2. A branch called `tutorial-status` exists in this practice repository: it belongs to the progress check, and you can ignore it.
