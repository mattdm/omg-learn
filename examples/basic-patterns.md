# Basic Pattern Examples

Simple, commonly-used patterns for everyday mistake prevention.

**Note:** In examples below, `<platform>` should be replaced with:
- `.claude` for Claude Code
- `.cursor` for Cursor
- `.agents` or `.agent` for generic setups

## Git Safety Patterns

### 1. Block Commits to Main

```json
{
  "id": "no-commit-to-main",
  "description": "Block direct commits to main/master branches",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+commit",
  "check_script": "./<platform>/scripts/patterns/check-branch.sh",
  "action": "block",
  "message": "ERROR: Direct commits to main/master not allowed.\n\nCreate a feature branch:\n  git checkout -b feature/your-feature",
  "enabled": true
}
```

**Check script (check-branch.sh):**
```bash
#!/bin/bash
BRANCH=$(git branch --show-current 2>/dev/null)
[[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]] && exit 1 || exit 0
```

### 2. Warn on Force Push

```json
{
  "id": "warn-force-push",
  "description": "Request confirmation before force pushing",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+push.*(-f|--force)",
  "action": "ask",
  "message": "⚠️ FORCE PUSH will overwrite remote history!\n\nOnly proceed if:\n  • Working on your own branch\n  • Coordinated with team\n  • You understand the risks\n\nContinue?",
  "enabled": true
}
```

**⚠️ Cursor users:** Consider using `"action": "block"` instead of "ask" for better UX. "ask" is very disruptive in Cursor!

### 3. Block Force Delete Branches

```json
{
  "id": "no-force-delete-branch",
  "description": "Prevent accidental branch deletion",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+branch\\s+-D",
  "action": "ask",
  "message": "⚠️ Force deleting a branch (git branch -D)\n\nThis will delete unmerged changes!\n\nUse 'git branch -d' for merged branches.\n\nContinue with -D?",
  "enabled": true
}
```

**⚠️ Cursor users:** Consider using `"action": "block"` instead of "ask" for better UX. "ask" is very disruptive in Cursor!

## Command Output Patterns

### 4. Prevent Piping to Head

```json
{
  "id": "no-head-with-commands",
  "description": "Prevent losing command output by piping to head",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "\\|.*\\bhead\\b",
  "exclude_pattern": "(cat |<|\\bhead\\s+[^|])",
  "action": "block",
  "message": "ERROR: Using head with command output loses critical end output!\n\nCommands like 'npm test | head -20' hide:\n  • Test failure summaries\n  • Error messages\n  • Exit codes\n\nUse full output, or 'tail' to see the end.",
  "enabled": true
}
```

**Matches:** `npm test | head -20`, `git log | head -5`
**Allows:** `head package.json`, `cat file | grep foo`

### 5. Warn on Silent Grep Failures

```json
{
  "id": "warn-grep-quiet",
  "description": "Warn when using grep -q with commands that need output",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "grep\\s+-q",
  "action": "warn",
  "message": "⚠️ grep -q suppresses output. If you need to see matches, remove -q flag.",
  "enabled": false
}
```

## File Protection Patterns

### 6. Protect Important Files

```json
{
  "id": "protect-important-files",
  "description": "Ask before modifying critical files",
  "hook": "PreToolUse",
  "matcher": "Write",
  "pattern": "(LICENSE|ARCHITECTURE\\.md|CONTRIBUTING\\.md|SECURITY\\.md)$",
  "action": "ask",
  "message": "⚠️ Modifying protected file!\n\nThese files should rarely change:\n  • LICENSE - Legal implications\n  • ARCHITECTURE.md - Core design docs\n  • CONTRIBUTING.md - Project guidelines\n\nProceed with changes?",
  "enabled": true
}
```

**⚠️ Cursor users:** Consider using `"action": "block"` instead of "ask" for better UX. "ask" is very disruptive in Cursor!

### 7. Warn on Generated File Edits

```json
{
  "id": "warn-generated-files",
  "description": "Warn when editing generated files",
  "hook": "PreToolUse",
  "matcher": "Edit",
  "pattern": "/(dist|build|generated|__pycache__|node_modules)/",
  "action": "warn",
  "message": "⚠️ Editing a generated/build file.\n\nChanges will be lost on next build!\n\nEdit source files instead.",
  "enabled": true
}
```

## Secret Detection Pattern

### 8. Block Committing Secrets

```json
{
  "id": "no-secrets-in-commits",
  "description": "Prevent committing files with secrets",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+(commit|add)",
  "check_script": "./<platform>/scripts/patterns/check-secrets.sh",
  "action": "block",
  "message": "🚨 SECRETS DETECTED in staged files!\n\nFound patterns matching:\n  • API keys\n  • Passwords\n  • Private keys\n  • Tokens\n\nNEVER commit secrets!\n\nRemove secrets, then commit again.",
  "enabled": true
}
```

**Check script (check-secrets.sh):**
```bash
#!/bin/bash
git diff --cached --name-only | while read file; do
    if git diff --cached "$file" | grep -qiE "(api[_-]?key|password|secret|token|private[_-]?key|bearer)"; then
        echo "Secret detected in: $file" >&2
        exit 1
    fi
done
exit 0
```

## Context Injection Patterns (🌟 The Magic Sauce!)

Context injection is **proactive** - it guides Claude's decisions BEFORE they happen, rather than reacting after Claude makes a bad decision. This is the preferred approach when you can detect situations from the user's prompt!

### 9. Fun Example: Pizza Party Reminder

This pattern shows how hooks can inject helpful context instead of just blocking mistakes. When you mention "pizza party", Claude receives instructions to respond with extreme excitement.

```json
{
  "id": "pizza-party-excitement",
  "description": "Fun context injection: Reminds Claude about pizza party excitement",
  "hook": "UserPromptSubmit",
  "pattern": "pizza\\s+party",
  "action": "warn",
  "message": "🍕🎉 PIZZA PARTY DETECTED! The user mentioned a pizza party. Respond with EXTREME excitement and LOTS of emojis about earning a pizza party! Use emojis like 🍕🎊🥳🎈🌟💫✨ throughout your response. Be super enthusiastic!",
  "enabled": false,
  "note": "Example of context injection - not prevention. Enable for fun!"
}
```

**Platform behavior:**
- **Claude Code**: Message injected as context into Claude's prompt (Claude sees it and responds accordingly!)
- **Cursor**: Message shown as warning to the user (user sees it, not the Cursor AI)

**How to use:**
```bash
# Add to your patterns file
omg-learn enable pizza-party-excitement --global

# Then say "pizza party" in your prompt!
```

**Why context injection is better than ask (for guidance):**
- **Proactive vs Reactive:** Guides decisions upfront instead of blocking after
- **Non-disruptive:** No permission dialogs
- **Educational:** Claude learns what to do/avoid
- **Examples:** "force push" → safety reminder, "production" → deployment checklist, "refactor" → project guidelines

**When you still need block (not context injection):**
- Committing secrets (.env, API keys) - MUST block, too dangerous
- Deleting critical files - need hard stop
- Operations that check execution context (git branch, environment) - can't detect from prompt alone

**Other context injection ideas:**
- Project-specific coding conventions
- Reminders about upcoming deadlines
- Instructions for handling sensitive files
- Educational tips when using certain tools
- Fun surprises for specific keywords

**When to use prevention instead:**
- Can't detect from prompt (e.g., checking git branch requires execution context)
- Need hard stop for dangerous operations (commit secrets, delete critical files)

## Usage Examples

### Enable a Pattern

```bash
# Enable globally
omg-learn enable no-commit-to-main --global

# Enable for this project only
omg-learn enable no-commit-to-main --local
```

### Test a Pattern

```bash
# Test if it would match
omg-learn test no-commit-to-main "git commit -m 'fix'"
# Output: ✓ Pattern WOULD match

# Test if it would allow
omg-learn test no-head-with-commands "head package.json"
# Output: ✗ Pattern would NOT match (excluded)
```

### Simulate Hook Execution

```bash
# See what would happen for a command
omg-learn simulate "git commit -m 'fix'"
# Output:
#   ✓ Pattern WOULD trigger: no-commit-to-main
#   Result: Command would be BLOCKED
```

## Tips

1. **Start with 'ask' actions** - Learn what triggers, then upgrade to 'block'
2. **Test thoroughly** - Use `omg-learn test` before enabling
3. **Add exclude patterns** - Prevent annoying false positives
4. **Keep messages clear** - Explain why AND suggest fix
5. **Enable selectively** - Not every pattern fits every project

## Next Steps

- See `advanced-patterns.md` for complex examples
- See `workflows.md` for common use cases
- See `references/pattern-generation-guide.md` for creating custom patterns
