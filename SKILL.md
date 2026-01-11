---
name: omg-learn
version: 2.0.0
description: Learning from user corrections by creating skills and patterns. Patterns can prevent mistakes (block/warn/ask) or inject helpful context into prompts. Use when user says "omg!" during corrections, when user provides feedback to create persistent knowledge, or when user wants to ensure AI never makes the same mistake again.
dependencies:
  - skill-creator
---

# OMG! Learning from Corrections

When the user says "omg!" during a correction, create or update a skill AND optionally a preventive pattern.

**ALWAYS load the skill-creator skill first.**

## Quick Reference

- **CLI tool:** `omg-learn list|show|enable|disable|test|simulate|sync|export|import`
- **Pattern files:** 
  - Claude Code: `~/.claude/omg-learn-patterns.json` (global), `.claude/omg-learn-patterns.json` (local)
  - Cursor: `~/.cursor/omg-learn-patterns.json` (global), `.cursor/omg-learn-patterns.json` (local)
- **Detailed guides:** See `references/` directory

## Workflow

When user says "omg!" during a correction:

### 0. Check Platform Hooks (First Time Only)

Check if hooks are installed:
- Claude Code: Check for `~/.claude/hooks/pretool-checker.sh` or `.claude/hooks/pretool-checker.sh`
- Cursor: Check for `~/.cursor/hooks.json` or `.cursor/hooks.json`

**If NOT installed:**
- Explain platform hooks catch mistakes BEFORE they happen
- Ask: "Would you like to install hooks now?"
- If yes: Run `./scripts/install-hooks.sh`
- Platform hooks are OPTIONAL but recommended

**Platform Hooks vs Skill Hooks:**
- **Platform hooks:** Work on both Claude Code and Cursor, always active, prevent first mistake
- **Skill hooks:** Claude Code ONLY feature - hooks defined within skills themselves. Cursor does not support skill hooks.
- This skill primarily uses platform hooks for maximum compatibility

### 1. Analyze the Correction

Ask:
- What did you do wrong?
- What is the correct behavior?
- What knowledge should be preserved?
- Could this be prevented with a pattern?

**Skill creation tip:** Include trigger contexts in description.
Example: "Use when analyzing database code" or "When deploying to production"

### 2. Check for Global Intent

If user says "globally", "system wide", "everywhere":
→ Create global skill in `~/.claude/skills/` (Claude Code) or `~/.cursor/skills/` (Cursor)

Otherwise:
→ Create project-local skill in `.claude/skills/` (Claude Code) or `.cursor/skills/` (Cursor)

**Note:** Also supports `.agents/skills/` or `.agent/skills/` directories if present.

### 3. Search for Existing Skills

Search appropriate location for related skills.

If found → Propose update
If not found → Propose new skill

### 4. Propose Changes

- For updates: Show before/after diff
- For new skills: Show full YAML with frontmatter
- Indicate storage location (global vs project-local)

### 5. Create or Update Skill

After user approval, create/update the skill file.

### 6. AI-Powered Pattern Generation (If Hooks Installed)

**If platform hooks are installed, ask:**

"This mistake could be prevented with a pattern. Should I generate one?"

- If **YES** → Continue to step 7
- If **NO** → Done

**When patterns make sense:**
- **Prevention:** Mistakes with specific commands or files, detectable patterns (regex or script)
- **Context injection:** Reminders about conventions, instructions based on keywords, educational hints
- NOT for complex reasoning mistakes that require understanding

**Pattern types:**
- **Preventive patterns:** Block, warn, or ask before dangerous operations
- **Context injection patterns:** Add helpful context to Claude's prompt based on keywords (Claude Code only)

### 7. Generate and Test Pattern

See: `references/pattern-generation-guide.md` for full details.

**Step 7.1: Analyze the Mistake**

Extract key information:
- What tool was used? (Bash, Write, Edit, or prompt?)
- What was the problematic input?
- Why was it wrong?
- How can we detect it? (Regex or check script?)

**Step 7.2: Generate Pattern Components**

**Hook Type:**
- `PreToolUse` for tool interception (Bash/Write/Edit)
- `UserPromptSubmit` for prompt analysis

**Matcher:** (PreToolUse only)
- `Bash` for shell commands
- `Write` for file writes
- `Edit` for file edits
- `*` for all tools

**Pattern Regex:**
Create regex that matches the error pattern.

Examples:
- `\|.*\bhead\b` → Matches pipe to head
- `git\s+commit` → Matches git commit
- `git\s+push.*(-f|--force)` → Matches force push

**Exclude Pattern:** (optional)
Prevent false positives.

Example: `(cat |<|\bhead\s+[^|])` excludes `head package.json`

**Check Script:** (optional)
For complex logic that can't be regex.

Example: Branch checking, environment validation

**Action:**
- `block` → Prevent action entirely (PreToolUse only)
- `warn` → Allow with warning (PreToolUse), or inject context (UserPromptSubmit)
- `ask` → Request confirmation (PreToolUse), or inject context (UserPromptSubmit)

**Note on UserPromptSubmit:**
- `warn`/`ask` actions inject the message as context into Claude's prompt (Claude Code only!)
- `block` action shows error to user and prevents prompt submission
- For Cursor, messages appear as warnings to user, not injected context

**Message:**
Clear explanation with suggested fix.

Format:
```
ERROR: [What's wrong]
[Why it matters]

[Suggested alternative]
```

**Step 7.3: Show Generated Pattern**

Present the complete pattern:

```json
{
  "id": "pattern-id",
  "description": "What this prevents",
  "hook": "PreToolUse",
  "matcher": "Bash",
  "pattern": "regex here",
  "exclude_pattern": "optional exclusion",
  "action": "block",
  "message": "Clear error message",
  "enabled": true
}
```

Include explanation:
- What it matches
- What it allows (excludes)
- Test cases showing behavior

Example:
```
This pattern will:
✓ Block: npm test | head -20
✓ Block: git log | head -5
✗ Allow: head package.json
✗ Allow: cat file | grep foo
```

**Step 7.4: Test Pattern**

```bash
omg-learn test <pattern-id> "test input"
```

Verify matches/excludes work correctly.

**Step 7.5: Enable Pattern**

Ask scope and enable:

```bash
omg-learn enable <pattern-id> --global
# or
omg-learn enable <pattern-id> --local
```

### 8. Register the Skill

**Claude Code:** Skills are auto-discovered from `~/.claude/skills/` or `.claude/skills/`

**Cursor:** Skills are loaded via rules in `~/.cursor/rules/`. Use `generate-cursor-rule` script to create a rule that points to the SKILL.md.

**Done!** The skill and pattern (if created) are now active.

## Advanced Features

**Pattern Management:**
```bash
omg-learn list              # List all patterns
omg-learn show <id>         # Show pattern details
omg-learn enable <id>       # Enable a pattern
omg-learn disable <id>      # Disable a pattern
omg-learn test <id> "input" # Test pattern
omg-learn simulate "cmd"    # Simulate hook execution
```

**Cross-Project:**
```bash
omg-learn sync              # Show sync status
omg-learn export <ids> -o file.zip  # Export patterns
omg-learn import file.zip   # Import patterns
```

See `references/cli-reference.md` for full documentation.

## Platform Support

| Feature | Claude Code | Cursor | Notes |
|---------|-------------|--------|-------|
| Platform hooks | ✅ | ✅ | Different event names |
| Skill hooks | ✅ | ❌ | Claude Code only - not supported in Cursor |
| Skill discovery | ✅ Auto | ✅ Via rules | Claude auto-discovers, Cursor uses .mdc rules |
| CLI tool | ✅ | ✅ | Both platforms |
| Pattern regex | ✅ | ✅ | Same syntax |
| Check scripts | ✅ | ✅ | Bash scripts |

**Event Names:**
- Claude Code: `PreToolUse`, `UserPromptSubmit`
- Cursor: `beforeShellExecution`, `beforeSubmitPrompt`

**Skill Hooks vs Platform Hooks:**
- **Skill hooks** are defined within a skill's YAML frontmatter (Claude Code only)
- **Platform hooks** are defined in `.claude/hooks/` or `.cursor/hooks.json` (both platforms)
- This skill uses **platform hooks** for cross-platform compatibility

## Installation

**Claude Code:**
```bash
cd ~/.claude/skills/omg-learn
./scripts/install-hooks.sh
```

**Cursor:**
```bash
# Install skill
cd ~/.cursor/skills/omg-learn
./scripts/install-hooks.sh

# Generate and install Cursor rule
./scripts/generate-cursor-rule SKILL.md --install
```

**Supported directories:** `.claude/`, `.cursor/`, `.agents/`, `.agent/`

See README.md for full installation guide.

## Common Pattern Examples

See `examples/` directory for detailed examples.

**Preventive patterns:**
- Block commits to main
- Warn on force push
- Prevent piping to head
- Protect important files
- Detect secrets before commit

**Context injection patterns:**
- Remind Claude about project conventions
- Add instructions based on keywords
- Fun surprises (pizza party example!)
- Educational hints for specific tools

**Advanced patterns:**
- Environment-specific checks
- Multi-condition validation
- Custom check scripts
- Team patterns

## References

- `references/pattern-generation-guide.md` - Complete pattern generation guide
- `references/cli-reference.md` - Full CLI documentation
- `references/pattern-structure.md` - JSON schema reference
- `references/hook-system.md` - Technical hook details
- `examples/basic-patterns.md` - Simple pattern examples
- `examples/advanced-patterns.md` - Complex patterns
- `examples/workflows.md` - Common workflows

## Troubleshooting

**Hooks not working?**

Claude Code:
```bash
# Check installation
ls ~/.claude/hooks/pretool-checker.sh
cat ~/.claude/settings.json | grep hooks

# Test manually
echo '{"tool_name":"Bash","tool_input":{"command":"git commit"}}' | ~/.claude/hooks/pretool-checker.sh
```

Cursor:
```bash
# Check installation
ls ~/.cursor/hooks/before-shell.sh
cat ~/.cursor/hooks.json

# Test manually
echo '{"command":"git commit"}' | ~/.cursor/hooks/before-shell.sh
```

**Pattern not matching?**
```bash
# Test the pattern
omg-learn test <pattern-id> "your input"

# Simulate full execution
omg-learn simulate "your command"
```

**See logs:**
Uncomment debug logging in hook scripts:
```bash
# In pretool-checker.sh line 36:
echo "DEBUG: Tool: $TOOL_NAME, Input: $TOOL_INPUT" >> /tmp/omg-learn-hook.log
```

## License

See LICENSE file in the repository root.
