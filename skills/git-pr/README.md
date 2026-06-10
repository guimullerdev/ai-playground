# git-commit skill

A Claude skill that analyzes your repository context and produces well-formatted git commit messages, then executes the commit after your approval. Every decision point uses Claude Code's native selection UI — arrow keys, Enter to confirm, no typing required.

---

## What it does

When triggered, the skill:

1. Scans all changed files and groups them by project/folder — if changes span multiple scopes, presents a selection UI so you pick which one to commit
2. Reads the branch name, diff, and recent log for the selected scope
3. Extracts a Jira-style ticket ID from the branch name (if present)
4. Asks how you want to group the commit (single, split by type, or custom)
5. Picks the right verb based on what actually happened (new files → `Implemented`, edits → `Updated`, deletions → `Removed`, etc.)
6. Suggests a formatted commit message and presents options to confirm, edit, or change the verb
7. Runs `git add` + `git commit` only after you confirm — for split commits, asks between each one

---

## Interactive UI at every step

All choices are presented as native Claude Code selections — no open-ended questions:

**Scope selection** (when changes span multiple folders):
```
1. pocs/beeai-fase-three/
   Modified app files + new agents/orchestrator.py and tools/agent_tools.py
2. pocs/beeai-fase-two/
   New untracked folder
3. .gitignore + .claude/
   New config/ignore files
4. All folders (*)
```

**Commit grouping:**
```
1. Single commit — everything in one commit
2. Split commits — separate new files from modifications
3. Let me decide — show me the files and I'll choose the grouping
```

**Message approval:**
```
1. Yes, commit now
2. Edit the message — I'll retype it
3. Change the verb
4. Cancel
```

**Between split commits:**
```
1. Yes, commit this one too
2. Skip this commit
3. Stop here
```

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

**Read-only (always safe to run):**
- `git status`, `git diff`, `git diff HEAD -- <path>`, `git diff --staged`
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