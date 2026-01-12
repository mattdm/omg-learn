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

**Note:** This repository contains the source code. Installation copies the hooks to your global or project-local configuration.

```bash
# Clone the repository
git clone https://github.com/yourusername/omg-learn.git
cd omg-learn

# Run the installer (interactive)
./scripts/install-hooks.sh

# Choose:
#   1) Global (all projects) - installs to ~/.claude/ or ~/.cursor/
#   2) Project-local (current project only) - installs to .claude/ or .cursor/

# The installer will:
# - Detect your platform (Claude Code or Cursor)
# - Copy hook scripts to the appropriate directory
# - Register hooks in settings.json (Claude Code) or hooks.json (Cursor)
# - Create a minimal patterns file with just the "omg!" trigger pattern
# - For Cursor: Install the cursor rule for skill discovery

# Verify installation
omg-learn list
```

**Clean Slate:** Installation creates only a minimal patterns file. The examples in `examples/` are documentation - use them as reference, but you'll build your own patterns through the omg-learn workflow.

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

### 🌟 Context Injection Patterns (The Magic Sauce!)

**Proactive** guidance > **Reactive** blocking. Context injection guides Claude's decisions BEFORE they happen:

- Detect keywords in user prompts (e.g., "force push", "production", ".env")
- Inject instructions into Claude's prompt
- Non-disruptive - no permission dialogs
- Claude sees guidance and makes better decisions upfront

**Example use cases:**
- Remind Claude about project conventions (coding style, architecture patterns)
- Educational hints when specific topics mentioned (force push → when to use it)
- Deployment checklists when "production" mentioned
- Fun surprises like pizza parties!

**🌟 Best Practice: Link Patterns to Skills**

When you create a skill, also create a companion context injection pattern:
- Pattern triggers on relevant keywords from the skill description
- Reminds Claude to use the skill when appropriate
- Proactive guidance instead of reactive blocking
- Makes skills discoverable as you work

**Example:** Create a "database-migrations" skill → add pattern that triggers on "database", "migration", "schema" → Claude automatically uses the skill when you mention database changes!

**Important:** Context injection is for GUIDANCE and EDUCATION. For dangerous operations (committing secrets, deleting files), you still need prevention patterns with `block` action!

**How it works:**
- **Claude Code**: Context added directly to Claude's prompt (true magic!)
- **Cursor**: Message shown as warning to user (user sees it, not Cursor AI)

### 🛡️ Preventive Patterns (When Context Injection Can't Help)

**Reactive** patterns catch mistakes after Claude decides to do them:

- **Block** dangerous operations (commit to main, force push to production) - hard stop for severe consequences
- **Warn** about risky actions (large file commits, modifying generated files) - educational
- **Ask** for confirmation (last resort - most disruptive!)
  - ⚠️ **Cursor users:** "ask" is very disruptive - prefer context injection or "block" instead!
  - ⚠️ **Claude Code users:** "ask" less disruptive but still prefer context injection when possible

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

- **Shell commands** (before and after execution)
- **File writes** (before and after writing)
- **File edits** (before and after editing)
- **User prompts** (before processing)

**Hook Types:**

| Hook | When | Use For |
|------|------|---------|
| PreToolUse | Before tool execution | Prevention, safety checks, warnings |
| PostToolUse | After tool execution | Automation, formatting, linting, testing |
| UserPromptSubmit | On user prompt | Context injection, skill reminders |

**PostToolUse hooks enable automation:**
- Auto-format files with ruff, prettier, black
- Run linters after save (ruff check, eslint)
- Execute tests automatically
- Compile code on changes
- Any post-execution automation

### Pattern Matching

Each pattern has:
- **Regex** for simple matching
- **Exclude patterns** to avoid false positives
- **Check scripts** for complex logic (git branch, env checks)
- **Actions** (block/warn/ask)

### CLI Tools

Pure Python implementation:
- No external dependencies (pure Python)
- Works on Linux/Mac
- Fast (~30ms per hook execution)
- Clean, maintainable code with proper syntax highlighting
- Extensible and well-tested

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
ls ~/.claude/hooks/omg-learn-tool-checker.py
cat ~/.claude/settings.json | grep hooks

# Test manually
echo '{"tool_name":"Bash","tool_input":{"command":"git commit"}}' | \
  ~/.claude/hooks/omg-learn-tool-checker.py
```

**Cursor:**
```bash
# Check installation
ls ~/.cursor/hooks/before-shell.py
cat ~/.cursor/hooks.json

# Test manually
echo '{"command":"git commit"}' | ~/.cursor/hooks/before-shell.py
```

### Pattern not matching?

```bash
# Test the pattern
omg-learn test no-commit-to-main "git commit -m 'fix'"

# Simulate full execution
omg-learn simulate "git commit -m 'fix'"
```

### Enable debug logging

Add debug output to hook scripts (omg-learn-tool-checker.py, etc.):
```python
# Add at the top after imports:
import sys
sys.stderr.write(f"DEBUG: Tool: {tool_name}, Input: {tool_input}\n")
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
