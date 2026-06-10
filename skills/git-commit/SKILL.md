---
name: git-commit
description: >
  Use this skill whenever the user wants to commit changes to git, create a commit message, review staged or unstaged changes, or asks anything related to "commit", "git status", "what changed", "stage changes", "version this". Trigger even when the user just says "help me commit" or "let's commit". This skill runs git commands to analyze changes and produces a commit message following the project's pattern, extracted from the branch name. Always use this skill before writing any git commit command.
---

# Git Commit Skill

Helps the user build and execute well-formatted git commits, with the message derived from the real project context (branch name, diff, logs).

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

**If multiple scopes have changes:** present a native selection UI with one entry per scope. Each entry should show the folder name and a short summary of what changed (modified/new/deleted file count). Include an "All folders" option.

Example options to present:
```
1. pocs/beeai-fase-three/
   Modified app files + new agents/orchestrator.py and tools/agent_tools.py
2. pocs/beeai-fase-two/
   New untracked folder
3. .gitignore + .claude/
   New config/ignore files
4. All folders (*)
   Include all changes in a single commit or let me split them
```

Wait for selection before proceeding. From this point on, **only consider files inside the selected scope**.

---

### 2. Collect repository context

Run in sequence for the selected scope:

```bash
git branch --show-current
git diff HEAD -- <selected-scope>
git log --oneline -10
```

If `git diff HEAD` returns nothing for the selected scope, inform the user and stop.

---

### 3. Extract the ticket ID from the branch name

Analyze the branch name from `git branch --show-current`.

- Pattern `PROJ-1234-...`, `PROJ-1234/...`, or a Jira-style ID at the start → extract `PROJ-1234`
- No detectable ID → **do not invent one**, message will have no prefix

| Branch | Extracted prefix |
|---|---|
| `CARS-42-login-page` | `CARS-42` |
| `feature/PROJ-100-refactor` | `PROJ-100` |
| `main` | *(none)* |
| `fix-button-style` | *(none)* |

---

### 4. Ask about commit grouping

Present a native selection UI:

```
How would you like to commit these changes?

1. Single commit — everything in one commit
2. Split commits — separate new files from modifications
3. Let me decide — show me the files and I'll choose the grouping
```

- **Single commit:** proceed to step 5 with all files in scope.
- **Split commits:** propose a logical grouping based on the diff (e.g. new files in one group, modified in another), then present each group as a native selection for the user to confirm or rearrange.
- **Let me decide:** list all files in scope and ask the user to describe the grouping they want.

---

### 5. Determine the commit verb

Analyze `git diff HEAD` and `git status` to identify the **dominant action** among the files in the group:

| Dominant action | Verb |
|---|---|
| Mostly new files (`A` in status) | `Implemented` |
| Mostly modified files (`M` in status) | `Updated` / `Changed` |
| Mostly deleted files (`D` in status) | `Removed` |
| Mixed, no clear dominance | Verb that best represents the most significant change |

Verbs must be in the **past participle**:
- Implemented, Added, Updated, Changed, Fixed, Removed, Refactored, Adjusted, Extracted, Moved

---

### 6. Build the commit message

**With ticket prefix:**
```
PROJ-1234 Verb clear and objective description of what was done
```

**Without prefix:**
```
Verb clear and objective description of what was done
```

Rules:
- First letter capitalized, no trailing period
- Max ~72 characters on the main line
- Describes *what* changed, not *why*
- Additional context may follow after a blank line

**Examples:**
```
CARS-42 Implemented Field component with Compound Components pattern

PROJ-100 Updated submit button behavior on the login form

Fixed type error in useAuth hook
```

---

### 7. Present suggestion and wait for approval

Show the suggested message in a code block, followed by the list of files to be committed.

Then present a native selection UI:

```
Commit with this message?

1. Yes, commit now
2. Edit the message — I'll retype it
3. Change the verb
4. Cancel
```

- **Yes:** proceed to step 8.
- **Edit the message:** ask the user to type the new message, then re-present this selection.
- **Change the verb:** present a native selection with all available verbs, re-build the message, then re-present this selection.
- **Cancel:** stop, no git write commands executed.

---

### 8. Execute the commit (only after explicit approval)

```bash
git add <files in scope>
git commit -m "<approved message>"
```

If there are multiple commits (split grouping), execute one at a time. Before each commit after the first, present a native selection UI:

```
Ready for the next commit: "<next message>"
Files: <list>

1. Yes, commit this one too
2. Skip this commit
3. Stop here
```

After all commits, show:

```bash
git log --oneline -3
```

---

## Allowed git commands

### ✅ Read (always allowed)
```
git status
git status --short
git diff
git diff HEAD
git diff HEAD -- <path>
git diff --staged
git branch --show-current
git branch -a
git log --oneline -N   (N up to 20)
git show --stat HEAD
```

### ✅ Write (only after explicit user approval)
```
git add <specific files>
git add -p
git commit -m "<message>"
git commit --amend -m "<message>"   (only if the user explicitly requests it)
```

### ❌ Never execute
```
git reset --hard
git reset HEAD~N
git rebase
git push --force
git push --force-with-lease
git clean -fd
git stash drop
git branch -D
git tag -d
git reflog expire
```

> If the user requests any blocked command, inform them it is outside the scope of this skill and suggest they run it manually with caution.

---

## General behavior

- **Language:** respond in the same language the user is using
- **Tone:** direct, no unnecessary padding
- **Never run write git commands without explicit approval**
- **Always use native selection UI for choices** — never ask open-ended questions when options are known
- If the repository is not found (`not a git repository`), inform the user and stop
- If there are no changes (`nothing to commit`), inform and stop
- On any git error, show the error message and explain what happened