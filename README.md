# omg-learn - Learn from Mistakes, Never Repeat Them

A skill for Claude Code and Cursor that learns from your corrections and creates **preventive patterns** to catch mistakes before they happen.

## What is omg-learn?

When you say **"omg!"** while correcting the AI, omg-learn:

1. **Creates a skill** from the correction (permanent knowledge)
2. **Generates a preventive pattern** (catches it before it happens again)
3. **Tests the pattern** to ensure it works
4. **Enables it** globally or per-project

**Result:** The mistake never happens again! 🎉

## Quick Start

### Installation

**Claude Code:**
```bash
# Navigate to the skill directory
cd ~/.claude/skills/omg-learn

# Install hooks and CLI
./scripts/install-hooks.sh

# Verify installation
omg-learn list
```

**Cursor:**
```bash
# Navigate to the skill directory
cd ~/.cursor/skills/omg-learn

# Install hooks and CLI
./scripts/install-hooks.sh

# Generate and install Cursor rule
./scripts/generate-cursor-rule SKILL.md --install

# Verify installation
omg-learn list
```

**Note:** Also supports `.agents/` or `.agent/` directories if you prefer generic naming.

### First Use

1. Make a mistake (or Claude makes one)
2. Say "omg!" in your response
3. Claude will:
   - Create a skill from the correction
   - Offer to generate a preventive pattern
   - Show you the pattern and test it
   - Enable it for future protection

**Example:**
```
User: "omg! You used npm test | head -20 and missed the test failures at the end!"

AI Assistant:
- Creates skill about command output handling
- Generates pattern: \|.*\bhead\b (matches pipe to head)
- Tests it: ✓ Blocks "npm test | head -20"
- Tests it: ✗ Allows "head package.json"
- Enables pattern globally

Next time: Hook blocks the command before execution!
```

## Features

### 🛡️ Preventive Patterns

Patterns catch mistakes **before** they happen:

- **Block** dangerous operations (commit to main, force push to production)
- **Warn** about risky actions (large file commits, modifying generated code)
- **Ask** for confirmation (force push, deleting branches)

### 🧠 AI-Powered Generation

The AI analyzes your mistake and auto-generates:

- Regex pattern to detect it
- Exclude pattern to avoid false positives
- Clear error message with suggested fix
- Test cases to verify it works

No regex knowledge needed!

### 🔧 Powerful CLI

```bash
omg-learn list                    # List all patterns
omg-learn show <pattern-id>       # Show details
omg-learn test <id> "input"       # Test a pattern
omg-learn simulate "command"      # See what would happen
omg-learn enable/disable <id>     # Toggle patterns
omg-learn sync                    # Cross-project sync
omg-learn export -o patterns.zip  # Share patterns
omg-learn import patterns.zip     # Import patterns
```

### 🌍 Cross-Platform

Works on both:
- **Claude Code** - Full support
- **Cursor** - Full support (different hook events)

### 📦 Cross-Project Learning

Patterns can be:
- **Global** - Apply to all projects
- **Local** - Project-specific only
- **Synced** - Share between projects
- **Exported** - Share with team (ZIP or JSON)

## Examples

### Block Commits to Main

```json
{
  "id": "no-commit-to-main",
  "description": "Block commits to main/master",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+commit",
  "check_script": "./scripts/patterns/check-branch.sh",
  "action": "block",
  "message": "Direct commits to main not allowed. Use a feature branch."
}
```

### Warn on Force Push

```json
{
  "id": "warn-force-push",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "git\\s+push.*(-f|--force)",
  "action": "ask",
  "message": "⚠️ Force push will overwrite remote history. Are you sure?"
}
```

### Prevent Piping to Head

```json
{
  "id": "no-head-with-commands",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "\\|.*\\bhead\\b",
  "exclude_pattern": "(cat |<|\\bhead\\s+[^|])",
  "action": "block",
  "message": "Using head with command output loses critical end output (like test results)"
}
```

See `examples/` directory for more!

## Architecture

### Platform Hooks

Always-active hooks that intercept:

- **Shell commands** (before execution)
- **File writes** (before writing)
- **File edits** (before editing)
- **User prompts** (before processing)

### Pattern Matching

Each pattern has:
- **Regex** for simple matching
- **Exclude patterns** to avoid false positives
- **Check scripts** for complex logic (git branch, env checks)
- **Actions** (block/warn/ask)

### CLI Tools

Pure Python implementation:
- No external dependencies (jq removed!)
- Works on Linux/Mac
- Fast enough (~30ms per hook execution)
- Extensible and maintainable

## Documentation

- **SKILL.md** - Main skill documentation (~200 lines)
- **references/pattern-generation-guide.md** - Complete pattern guide
- **references/cli-reference.md** - Full CLI documentation
- **examples/basic-patterns.md** - Simple examples
- **examples/advanced-patterns.md** - Complex patterns
- **examples/workflows.md** - Common workflows

## Platform Differences

| Feature | Claude Code | Cursor |
|---------|-------------|--------|
| Hook events | PreToolUse | beforeShellExecution |
| Prompt hooks | UserPromptSubmit | beforeSubmitPrompt |
| Skill hooks | ✅ Yes | ❌ No |
| Platform hooks | ✅ Yes | ✅ Yes |
| Pattern format | Same | Same |

## Performance

**Hook execution:** ~30ms overhead per operation

This is imperceptible to users since hooks only fire on user actions (not hot paths).

**Benchmark:**
- jq-based: 2ms
- Python-based: 30ms
- Trade-off: 28ms for zero dependencies + better capabilities

## Troubleshooting

### Hooks not triggering?

**Claude Code:**
```bash
# Check installation
ls ~/.claude/hooks/pretool-checker.sh
cat ~/.claude/settings.json | grep hooks

# Test manually
echo '{"tool_name":"Bash","tool_input":{"command":"git commit"}}' | \
  ~/.claude/hooks/pretool-checker.sh
```

**Cursor:**
```bash
# Check installation
ls ~/.cursor/hooks/before-shell.sh
cat ~/.cursor/hooks.json

# Test manually
echo '{"command":"git commit"}' | ~/.cursor/hooks/before-shell.sh
```

### Pattern not matching?

```bash
# Test the pattern
omg-learn test no-commit-to-main "git commit -m 'fix'"

# Simulate full execution
omg-learn simulate "git commit -m 'fix'"
```

### Enable debug logging

Uncomment in hook scripts:
```bash
# Line 36 in pretool-checker.sh:
echo "DEBUG: Tool: $TOOL_NAME, Input: $TOOL_INPUT" >> /tmp/omg-learn-hook.log
```

## Contributing

Found a bug? Have a pattern to share?

1. Open an issue
2. Submit a PR
3. Share your patterns (export and share the ZIP!)

## License

See LICENSE file.

## Credits

Built with AI assistance (Claude Sonnet 4.5) using the Claude Code CLI.

**Co-Authored-By:** Claude Sonnet 4.5 <noreply@anthropic.com>
