# git-commit skill

A Claude skill that analyzes your repository context and produces well-formatted git commit messages, then executes the commit after your approval.

---

## What it does

When triggered, the skill:

1. Scans all changed files and, if changes span multiple folders or subprojects, asks which one you want to commit — all subsequent steps are scoped to that selection
2. Reads your current branch, diff, and recent log for the selected scope
3. Extracts a Jira-style ticket ID from the branch name (if present)
4. Asks whether you want a single commit or multiple split by type of change
5. Picks the right verb based on what actually happened (new files → `Implemented`, edits → `Updated`, deletions → `Removed`, etc.)
6. Suggests a formatted commit message and waits for your approval
7. Runs `git add` + `git commit` only after you confirm

---

## Message format

**Branch with a ticket ID** (e.g. `CARS-42-login-page`):
```
CARS-42 Implemented Field component with Compound Components pattern
```

**Branch without a ticket ID** (e.g. `main`, `fix-button-style`):
```
Fixed type error in useAuth hook
```

Rules applied to every message:
- Past participle verb matching the dominant change type
- First letter capitalized, no trailing period
- Max ~72 characters on the main line
- Describes *what* changed, not *why*

---

## How to trigger it

Just talk to Claude naturally inside a project that has this skill installed:

```
let's commit
help me commit this
what changed?
I'm ready to commit
```

---

## Supported ticket ID patterns

| Branch name | Extracted prefix |
|---|---|
| `CARS-42-login-page` | `CARS-42` |
| `feature/PROJ-100-refactor` | `PROJ-100` |
| `fix/ABC-9-typo` | `ABC-9` |
| `main` | *(none)* |
| `fix-button-style` | *(none)* |

---

## Allowed git commands

The skill operates with a strict allowlist to prevent accidental data loss.

**Read-only (always safe to run):**
- `git status`, `git diff`, `git diff HEAD`, `git diff --staged`
- `git branch --show-current`, `git branch -a`
- `git log --oneline` (up to 20 entries)
- `git show --stat HEAD`

**Write (only after your explicit approval):**
- `git add <files>`
- `git add -p`
- `git commit -m "<message>"`
- `git commit --amend -m "<message>"` *(only if you ask for it)*

**Never executed:**
- `git reset --hard` / `git reset HEAD~N`
- `git rebase`
- `git push --force` / `git push --force-with-lease`
- `git clean -fd`
- `git stash drop`
- `git branch -D`
- `git reflog expire`

If you ask for any blocked command, the skill will tell you and suggest running it manually.

---

## Installation

1. Download the `git-commit-skill.skill` file
2. Open the Claude project where you want to use it
3. Go to **Project Settings → Skills**
4. Upload the `.skill` file

The skill will be available in all conversations inside that project.

---

## Language

The skill responds in the same language you're using — English or Portuguese, whichever you write in.