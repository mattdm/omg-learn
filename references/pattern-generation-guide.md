# Pattern Generation Guide

This guide teaches Claude how to generate effective patterns from user mistakes.

## Pattern Structure

Every pattern has these core fields:

```json
{
  "id": "unique-identifier",
  "description": "What this pattern prevents",
  "hook": "PreToolUse|UserPromptSubmit|beforeShellExecution|beforeSubmitPrompt",
  "matcher": "Bash|Write|Edit|*",
  "pattern": "regex pattern",
  "exclude_pattern": "optional exclusion regex",
  "check_script": "optional path to script",
  "action": "block|warn|ask",
  "message": "User-facing error message",
  "enabled": true
}
```

## Common Mistake Patterns

### 1. Command Output Piping Issues

**Mistake:** Piping command output to `head` loses critical end output (like test failures).

**Example:** `npm test | head -20` hides test failure summary at the end.

**Pattern:**
```json
{
  "id": "no-head-with-commands",
  "description": "Prevent piping command output to head",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "\\|.*\\bhead\\b",
  "exclude_pattern": "(cat |<|\\bhead\\s+[^|])",
  "action": "block",
  "message": "ERROR: Using head with command output loses critical information at the end (like test results). Use the full command output or tail for errors.",
  "enabled": true
}
```

**Why this works:**
- `\|.*\bhead\b` matches any pipe to `head`
- Exclude pattern allows `head package.json` (direct file read)
- Blocks before execution, preventing data loss

### 2. Branch Protection

**Mistake:** Committing directly to main/master branch.

**Pattern:**
```json
{
  "id": "no-commit-to-main",
  "description": "Block commits to main/master branches",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+commit",
  "check_script": "./scripts/patterns/check-branch.sh",
  "action": "block",
  "message": "Direct commits to main/master not allowed. Create a feature branch:\n  git checkout -b feature/your-feature",
  "enabled": true
}
```

**Check script (check-branch.sh):**
```bash
#!/bin/bash
# Returns non-zero if on main/master
BRANCH=$(git branch --show-current 2>/dev/null)
if [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]]; then
    exit 1
fi
exit 0
```

**Why use check script:**
- Branch checking requires git command execution
- Can't be done with pure regex
- Script has context about repository state

### 3. Force Push Safety

**Mistake:** Force pushing without confirmation, potentially overwriting team members' work.

**Pattern:**
```json
{
  "id": "warn-on-force-push",
  "description": "Warn before force pushing",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+push.*(-f|--force)",
  "action": "ask",
  "message": "⚠️ You're about to FORCE PUSH. This will overwrite remote history.\n\nAre you sure? Only proceed if:\n  • You're working on your own branch\n  • You've coordinated with your team\n  • You understand the consequences",
  "enabled": true
}
```

**Why ask instead of block:**
- Force push has legitimate uses (rebasing feature branches)
- Asking adds a confirmation step
- Message educates about the risks

### 4. File Write Protection

**Mistake:** Accidentally overwriting important files like LICENSE or ARCHITECTURE.md.

**Pattern:**
```json
{
  "id": "protect-important-files",
  "description": "Protect important files from accidental edits",
  "hook": "PreToolUse",
  "matcher": "Write",
  "pattern": "(LICENSE|ARCHITECTURE\\.md|CONTRIBUTING\\.md)$",
  "action": "ask",
  "message": "⚠️ You're about to modify a protected file. These files should rarely change.\n\nAre you sure this is intentional?",
  "enabled": true
}
```

**Matcher:** `Write` only triggers on file write operations

### 5. Secret Detection

**Mistake:** Committing files containing secrets (API keys, passwords).

**Pattern:**
```json
{
  "id": "no-secrets-in-commits",
  "description": "Prevent committing files with secrets",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+(commit|add)",
  "check_script": "./scripts/patterns/check-secrets.sh",
  "action": "block",
  "message": "🚨 SECRETS DETECTED in staged files!\n\nFound potential secrets. Never commit:\n  • API keys\n  • Passwords\n  • Private keys\n  • Tokens\n\nRemove secrets before committing.",
  "enabled": true
}
```

**Check script (check-secrets.sh):**
```bash
#!/bin/bash
# Check staged files for common secret patterns
git diff --cached --name-only | while read file; do
    if git diff --cached "$file" | grep -qiE "(api[_-]?key|password|secret|token|private[_-]?key)"; then
        exit 1
    fi
done
exit 0
```

### 6. Prompt-Based Detection

**Mistake:** User says "omg!" but the pattern isn't active yet.

**Pattern:**
```json
{
  "id": "omg-detection",
  "description": "Detect omg! in user prompts",
  "hook": "UserPromptSubmit",
  "pattern": "[Oo][Mm][Gg]!",
  "action": "warn",
  "message": "💡 Detected 'omg!' - Triggering omg-learn skill to capture this mistake.",
  "enabled": true
}
```

**Note:** This is case-insensitive because UserPromptSubmit hooks use `-i` flag

## Pattern Generation Workflow

When user says "omg!" about a mistake, follow these steps:

### Step 1: Analyze the Mistake

Ask yourself:
1. **What tool was used?** (Bash, Write, Edit, or was it a prompt?)
2. **What was the problematic input?** (Get the actual command/content)
3. **Why was it wrong?** (What damage occurred or almost occurred?)
4. **How can we detect it?** (Regex pattern, check script, or both?)

### Step 2: Choose Hook Type and Matcher

**For commands/operations:**
- Hook: `PreToolUse` (Claude Code) or `beforeShellExecution` (Cursor)
- Matcher: `Bash` for shell commands, `Write` for file writes, `Edit` for edits

**For user prompts:**
- Hook: `UserPromptSubmit` (Claude Code) or `beforeSubmitPrompt` (Cursor)
- No matcher needed

### Step 3: Create the Regex Pattern

**Regex Tips:**
- Use `\b` for word boundaries: `\bhead\b` matches "head" but not "header"
- Escape special chars: `\.` `\|` `\(` `\[` `\{`
- Use `\s+` for whitespace: `git\s+commit` matches "git commit" with any spacing
- Use `.*` carefully: `\|.*\bhead\b` matches pipe followed by anything, then "head"
- Anchor when needed: `(LICENSE|README\.md)$` matches end of string

**Common patterns:**
- Command: `git\s+push`
- Flag: `(-f|--force)`
- Pipe: `\|`
- File extension: `\.env$`
- Path: `/(node_modules|\.git)/`

### Step 4: Add Exclude Pattern (Optional)

Exclude patterns prevent false positives:

```
Pattern: \|.*\bhead\b (match any pipe to head)
Exclude: (cat |<|\bhead\s+[^|]) (allow direct file reads)
```

This allows:
- `head package.json` ✓
- `cat file.txt | grep foo` ✓

But blocks:
- `npm test | head -20` ✗

### Step 5: Choose Action

**block:**
- Use when the action will definitely cause problems
- Examples: commit to main, force push to main, commit secrets
- Message should explain why and suggest alternative

**warn:**
- Use when action might be problematic but has legitimate uses
- Examples: large file commits, modifying generated files
- Message should educate about potential issues

**ask:**
- Use when action requires careful consideration
- Examples: force push, deleting branches, modifying important files
- Message should list criteria for proceeding

### Step 6: Write Clear Message

Good messages:
1. **Explain what's wrong:** "Using head loses end output"
2. **Explain why it matters:** "Test failures appear at the end"
3. **Suggest alternative:** "Use full output or tail for errors"

**Format:**
```
ERROR: [What's wrong]
[Why it matters]

[Suggested alternative or fix]
```

### Step 7: Test the Pattern

Use the CLI to test:

```bash
# Test the pattern
omg-learn test <pattern-id> "git commit -m 'fix'"

# Simulate full hook execution
omg-learn simulate "git commit -m 'fix'"
```

Verify:
- ✓ Matches the problematic input
- ✓ Doesn't match legitimate uses (check excludes)
- ✓ Message is clear and helpful

## Platform-Specific Considerations

### Claude Code vs Cursor

**Hook names differ:**
- Claude Code: `PreToolUse`, `UserPromptSubmit`
- Cursor: `beforeShellExecution`, `beforeSubmitPrompt`

**Solution:** Use both in the pattern:
```json
"hook": "PreToolUse"  // Works for Claude Code
// Cursor users will use beforeShellExecution in their patterns
```

**For compatibility, teach users to create platform-specific patterns.**

### Check Scripts

**Location:**
- Global: `~/.claude/scripts/patterns/` or `~/.cursor/scripts/patterns/`
- Local: `.claude/scripts/patterns/` or `.cursor/scripts/patterns/`

**Template:**
```bash
#!/bin/bash
# check-example.sh
# Returns 0 if check passes, non-zero if pattern should trigger

# Get input (command or file path)
INPUT="$1"

# Perform check
if [some condition]; then
    exit 1  # Pattern should trigger
fi

exit 0  # Pattern should not trigger
```

## Examples by Mistake Type

### Command Mistakes

| Mistake | Pattern | Action |
|---------|---------|--------|
| `rm -rf /` | `rm\s+-rf\s+/\s*$` | block |
| `git reset --hard` on main | check-branch.sh | block |
| `npm publish` without confirmation | `npm\s+publish` | ask |
| `docker system prune -a` | `docker\s+system\s+prune\s+-a` | ask |

### File Operation Mistakes

| Mistake | Pattern | Action |
|---------|---------|--------|
| Overwrite LICENSE | `Write.*LICENSE$` | ask |
| Edit generated files | `Write.*/dist/.*` | warn |
| Modify node_modules | `(Write|Edit).*/node_modules/` | block |

### Branch/Git Mistakes

| Mistake | Pattern | Check Script |
|---------|---------|--------------|
| Commit to main | `git\s+commit` | check-branch.sh |
| Push to wrong remote | `git\s+push` | check-remote.sh |
| Merge without pull | `git\s+merge` | check-sync.sh |

## Anti-Patterns (Don't Do This)

### ❌ Too Broad
```json
{
  "pattern": "git",  // Matches ALL git commands!
  "action": "block"
}
```

**Problem:** Blocks legitimate operations

**Fix:** Be specific: `git\s+push.*(-f|--force)`

### ❌ Too Complex Regex
```json
{
  "pattern": "(?:git\\s+(?:commit|push|merge).*(?:main|master)|npm\\s+(?:publish|version).*(?:major|minor))",
  "action": "block"
}
```

**Problem:** Hard to understand, debug, and maintain

**Fix:** Create multiple simple patterns

### ❌ Wrong Hook Type
```json
{
  "hook": "UserPromptSubmit",  // Wrong!
  "matcher": "Bash",
  "pattern": "git commit"
}
```

**Problem:** UserPromptSubmit doesn't use matcher

**Fix:** Use PreToolUse for tool interception

### ❌ No Exclude Pattern
```json
{
  "pattern": "\\bhead\\b",  // Blocks "head package.json"!
  "action": "block"
}
```

**Problem:** False positives annoy users

**Fix:** Add exclude pattern for legitimate uses

## Testing Checklist

Before enabling a pattern:

- [ ] Pattern ID is unique and descriptive
- [ ] Hook type matches the interception point
- [ ] Matcher is correct (or omitted for prompts)
- [ ] Regex pattern is tested and accurate
- [ ] Exclude pattern prevents false positives
- [ ] Check script (if used) is executable and works
- [ ] Action is appropriate (block/warn/ask)
- [ ] Message is clear, explains why, and suggests fix
- [ ] Pattern is tested with `omg-learn test`
- [ ] Pattern is simulated with `omg-learn simulate`
- [ ] Real-world test: Does it catch the mistake?
- [ ] Real-world test: Does it allow legitimate use?

## Summary

**Good pattern generation:**
1. Analyzes the specific mistake
2. Chooses the right hook and matcher
3. Uses precise regex with excludes
4. Adds check scripts for complex logic
5. Chooses appropriate action
6. Writes clear, helpful messages
7. Tests thoroughly before enabling

**Remember:** Patterns are prevention, not punishment. Make them helpful!
