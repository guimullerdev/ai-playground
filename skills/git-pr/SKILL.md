---
name: git-pr
description: >
  Use this skill whenever the user wants to open a pull request, create a PR, summarize changes for review, or asks anything related to "PR", "pull request", "open a PR", "abrir PR", "criar PR". This skill analyzes the current branch, detects the base branch automatically, summarizes the changes from diff and commits, and runs the PR creation command after approval. Always use this skill before writing any pr create command.
---

# Git PR Skill

Helps the user create a well-described pull request by analyzing the current branch context, generating a title and description from the actual changes, and running the PR creation command after approval.

> **UI rule:** Every time user input is needed, use Claude Code's native selection UI — present labeled options the user can navigate with arrow keys and confirm with Enter. Never ask open-ended questions in plain text when a selection will do.

---

## Required flow

Always follow these steps **in order**:

### 1. Select the project/folder scope

Run:

```bash
git status --short
```

Group the output by top-level folder. Apply this grouping rule: if the root folder is a known container (e.g. `pocs/`, `apps/`, `src/`, `packages/`, `services/`, `libs/`), expand one level deeper so subprojects appear as separate entries.

**If only one scope has changes:** select it automatically, no prompt needed.

**If multiple scopes have changes:** present a native selection UI with one entry per scope, showing folder name and a short summary of what changed. Include an "All folders" option.

Wait for selection before proceeding. From this point on, **only consider files inside the selected scope**.

---

### 2. Collect branch and commit context

Run in sequence:

```bash
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git log --oneline origin/HEAD..HEAD
git diff origin/HEAD..HEAD -- <selected-scope>
```

- The current branch is the **source** of the PR
- The upstream branch (from `@{upstream}`) is the **base** of the PR — strip the `origin/` prefix for use in the command
- If `@{upstream}` fails (no upstream configured), present a native selection UI listing available remote branches from `git branch -r`, and ask the user to pick the base

---

### 3. Extract ticket ID from the branch name

Analyze the branch name from `git branch --show-current`.

- Pattern `PROJ-1234-...`, `PROJ-1234/...`, or a Jira-style ID at the start → extract `PROJ-1234`
- No detectable ID → no prefix

| Branch | Extracted prefix |
|---|---|
| `CARS-42-login-page` | `CARS-42` |
| `feature/PROJ-100-refactor` | `PROJ-100` |
| `main` | *(none)* |

---

### 4. Generate PR title and description

**Title format:**

With ticket ID:
```
PROJ-1234: Verb clear and objective description of what was done
```

Without ticket ID:
```
Verb clear and objective description of what was done
```

Use the same verb rules as the commit skill (past participle, dominant action):
- Mostly new files → `Implemented`
- Mostly modified → `Updated` / `Changed`
- Mostly deleted → `Removed`
- Mixed → verb that best represents the most significant change

---

**Description format (default template):**

```markdown
## What changed
<2-4 sentence summary of what was done, derived from the diff and commit messages>

## Commits
<list of commits from git log --oneline origin/HEAD..HEAD>

## Type of change
- [ ] New feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Config / tooling
- [ ] Documentation

## Checklist
- [ ] Self-reviewed the code
- [ ] No unnecessary debug or console logs left
- [ ] Tested locally
```

Fill in "What changed" and "Commits" from the actual git data. Leave the checkboxes unchecked — the author fills them.

---

### 5. Present suggestion and wait for approval

Show:
1. The detected base branch (e.g. `base: develop`)
2. The generated title in a code block
3. The full description in a code block

Then present a native selection UI:

```
Open PR with this title and description?

1. Yes, create the PR now
2. Edit the title
3. Edit the description
4. Change the verb
5. Cancel
```

- **Yes:** proceed to step 6.
- **Edit the title:** ask the user to type the new title, then re-present this selection.
- **Edit the description:** ask the user to type or paste the new description, then re-present this selection.
- **Change the verb:** present a native selection with all available verbs (Implemented, Added, Updated, Changed, Fixed, Removed, Refactored, Adjusted, Extracted, Moved), rebuild the title, then re-present this selection.
- **Cancel:** stop, no command executed.

---

### 6. Detect available PR CLI and execute

First, try:

```bash
git pr create --base <base-branch> --title "<title>" --body "<description>"
```

If that fails (command not found or non-zero exit), try:

```bash
gh pr create --base <base-branch> --title "<title>" --body "<description>"
```

If both fail, inform the user and print the title and description so they can open the PR manually.

After a successful run, show the output of the command (which typically includes the PR URL).

---

## Allowed commands

### ✅ Read (always allowed)
```
git status --short
git branch --show-current
git branch -r
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git log --oneline origin/HEAD..HEAD
git log --oneline -N   (N up to 20)
git diff origin/HEAD..HEAD
git diff origin/HEAD..HEAD -- <path>
git show --stat HEAD
```

### ✅ Write (only after explicit user approval)
```
git pr create --base <branch> --title "<title>" --body "<description>"
gh pr create --base <branch> --title "<title>" --body "<description>"
```

### ❌ Never execute
```
git reset --hard
git reset HEAD~N
git rebase
git push --force
git push --force-with-lease
git clean -fd
git branch -D
git reflog expire
```

> If the user requests any blocked command, inform them it is outside the scope of this skill and suggest they run it manually with caution.

---

## General behavior

- **Language:** respond in the same language the user is using
- **Tone:** direct, no unnecessary padding
- **Never run the PR command without explicit approval**
- **Always use native selection UI for choices**
- If not inside a git repository, inform the user and stop
- On any git or CLI error, show the error message and explain what happened