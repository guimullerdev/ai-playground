---
name: git-commit
description: >
  Use this skill whenever the user wants to commit changes to git, create a commit message, review staged or unstaged changes, or asks anything related to "commit", "git status", "what changed", "stage changes", "version this". Trigger even when the user just says "help me commit" or "let's commit". This skill runs git commands to analyze changes and produces a commit message following the project's pattern, extracted from the branch name. Always use this skill before writing any git commit command.
---

# Git Commit Skill

Helps the user build and execute well-formatted git commits, with the message derived from the real project context (branch name, diff, logs).

---

## Required flow

Always follow these steps **in order**:

### 1. Select the project/folder scope

Before analyzing anything, run:

```bash
git status --short
```

Look at the paths returned. If files span **multiple distinct top-level folders or subprojects** (e.g. `poc-auth/`, `poc-table/`, `apps/dashboard/`), ask the user:

> "I can see changes across multiple folders. Which project or folder do you want to commit right now?"

List the distinct folders found so the user can pick one or more. Wait for the answer before proceeding.

If all changes are already in a single folder/scope, skip the question and proceed.

From this point on, **only consider files inside the selected scope**. Ignore everything else.

---

### 2. Collect repository context

Run the commands below in sequence. **Never skip any.**

```bash
git branch --show-current
git diff HEAD -- <selected-folder>
git log --oneline -10
```

If `git diff HEAD` returns nothing for the selected scope (no changes), inform the user and stop.

---

### 3. Extract the ticket ID from the branch name

Analyze the branch name returned by `git branch --show-current`.

- If the branch follows the pattern `PROJ-1234-...` or `PROJ-1234/...` or starts with a Jira-style ID at the beginning, extract it: `PROJ-1234`
- If no ID is detectable, **do not invent one** — the message will have no prefix

**Examples:**
| Branch | Extracted prefix |
|---|---|
| `CARS-42-login-page` | `CARS-42` |
| `feature/PROJ-100-refactor` | `PROJ-100` |
| `main` | *(no prefix)* |
| `fix-button-style` | *(no prefix)* |

---

### 4. Ask about commit grouping

Before suggesting any message, **ask the user**:

> "I've analyzed the changes. Do you want a **single commit** with everything, or would you prefer to **split** into separate commits (e.g. new files in one commit, updates in another)?"

- If splitting: ask the user to indicate which files go in each commit, or suggest a logical grouping based on the diff and wait for confirmation.
- If single: proceed to step 4 with all files.

---

### 5. Determine the commit verb

Analyze `git diff HEAD` and `git status` to identify the **dominant action** among the files in the group:

| Dominant action | Verb to use |
|---|---|
| Mostly new files (`A` in status) | `Implemented` |
| Mostly modified files (`M` in status) | `Updated` / `Changed` |
| Mostly deleted files (`D` in status) | `Removed` |
| Mixed with no clear dominance | Use the verb that best represents the most significant change |

Verbs must be in the **past participle**, reflecting what was done:
- Implemented, Added, Updated, Changed, Fixed, Removed, Refactored, Adjusted, Extracted, Moved

---

### 6. Build the commit message

**Format with prefix (branch has ID):**
```
PROJ-1234 Verb clear and objective description of what was done
```

**Format without prefix:**
```
Verb clear and objective description of what was done
```

Message rules:
- **English**
- First letter capitalized, no trailing period
- Max ~72 characters on the main line
- Objective: describes *what* changed, not *why*
- If there is relevant context (e.g. multiple modules), additional lines may follow after a blank line

**Examples:**
```
CARS-42 Implemented Field component with Compound Components pattern

PROJ-100 Updated submit button behavior on the login form

Fixed type error in useAuth hook
```

---

### 7. Present suggestion and wait for approval

Show the user:
1. The suggested message in a code block
2. The files that will be included
3. Ask: **"Should I run the commit with this message, or would you like to adjust anything?"**

Wait for the response before executing any write git command.

---

### 8. Execute the commit (only after explicit approval)

If the user approves:

```bash
git add <files in group>
git commit -m "<approved message>"
```

If there are multiple commits, execute one at a time and wait for confirmation between each.

After the commit, show the result of:
```bash
git log --oneline -3
```

---

## Allowed git commands

This skill may only execute the following commands. **Nothing else.**

### ✅ Read (always allowed)
```
git status
git status --short
git diff
git diff HEAD
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

> If the user requests any command from the blocked list, inform them it is outside the scope of this skill and suggest they run it manually with caution.

---

## General behavior

- **Language:** always respond in the same language the user is using
- **Tone:** direct, no unnecessary padding
- **Never run write git commands without explicit approval**
- If the repository is not found (`not a git repository`), inform the user and stop
- If there are no changes (`nothing to commit`), inform and stop
- On any git error, show the error message and explain what happened