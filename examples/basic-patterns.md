# Basic Pattern Examples

Simple, commonly-used patterns for everyday mistake prevention.

## Git Safety Patterns

### 1. Block Commits to Main

```json
{
  "id": "no-commit-to-main",
  "description": "Block direct commits to main/master branches",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+commit",
  "check_script": "./.claude/scripts/patterns/check-branch.sh",
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
  "check_script": "./.claude/scripts/patterns/check-secrets.sh",
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
