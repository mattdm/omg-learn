# OMG! Learning Skill

A skill for AI agents that enables learning from user corrections by creating or updating skills when users express frustration with "omg!" during corrections.

## What it does

This skill provides a structured workflow for:
- Detecting when users say "omg!" during corrections
- Analyzing what went wrong and what should be preserved
- Creating or updating skills to prevent the same mistakes
- Handling both global and project-local skill creation
- **Designing preventive hooks** (Claude Code only - see below)

## Features by Platform

| Feature | Claude Code | Goose | OpenSkills | Cursor |
|---------|-------------|-------|------------|--------|
| Skill creation workflow | ✅ | ✅ | ✅ | ✅ |
| "omg!" detection | ✅ | ✅ | ✅ | ✅ |
| Global/project skills | ✅ | ✅ | ✅ | ✅ |
| **Platform hooks (NEW!)** | **✅** | ❌ | ❌ | **✅ Cursor** |
| Skill hooks (limited) | ✅ Claude Code only | ❌ | ❌ | ❌ |

## About Platform Hooks vs Skill Hooks

### Platform Hooks (NEW - Recommended!)

**Platform hooks** are always-active scripts that catch mistakes BEFORE they happen!

**How they work:**
- ✅ Always active (run before every command/tool use)
- ✅ Catch mistakes BEFORE they happen (not after)
- ✅ Check against configurable patterns
- ✅ Can block, warn, or ask for confirmation
- ✅ Extendable through simple JSON config file

**Supported platforms:**
- ✅ **Claude Code** - Full support
- ✅ **Cursor** - Full support
- ❌ **Goose, OpenSkills** - Not supported (yet)

**Example:** After installing, you can create a pattern that blocks `npm test | head -50` and shows an error message BEFORE the command runs.

### Skill Hooks (Claude Code Only - Limited)

**Skill hooks** are hooks defined within skills that only activate when the skill is loaded.

**Critical limitation**: Skill hooks **ONLY work when the skill is already loaded**!

This means:
- ❌ CANNOT catch the mistake that triggered "omg!" (skill isn't loaded yet)
- ✅ CAN enforce safe behavior in **workflow skills** (explicitly invoked like `/deploy`, `/release`)
- ❌ DON'T help for passive knowledge skills (they load too late)

**When skill hooks are useful:**
- Workflow skills you explicitly invoke (e.g., `/safe-commit`, `/deploy`, `/migrate`)
- Skills that enforce process during intentional operations
- NOT for learning from mistakes (they can't prevent the first occurrence)

**Platform support:**
- ✅ **Claude Code**: Full skill hook support
- ❌ **Goose, OpenSkills, Cursor**: No skill hook support

**Recommendation:** Use **platform hooks** (above) for catching mistakes, skill hooks for workflow enforcement.

## Installation

Choose the installation method for your platform. All methods work equally well!

### Claude Code

Skills are auto-discovered from skills directories - just copy and go!

**Global (all projects):**
```bash
cp -r omg-learn ~/.claude/skills/
```

**Project-specific:**
```bash
mkdir -p .claude/skills
cp -r omg-learn .claude/skills/
git add .claude/skills/omg-learn
git commit -m "Add omg-learn skill"
```

### Goose

Skills are auto-discovered from multiple skill directories - just copy to any of them!

**Global (all projects) - choose one:**
```bash
# Preferred - compatible with Claude Code
cp -r omg-learn ~/.claude/skills/

# Or Goose-specific locations
cp -r omg-learn ~/.config/goose/skills/
cp -r omg-learn ~/.config/agents/skills/
```

**Project-specific - choose one:**
```bash
# Preferred - compatible with Claude Code
mkdir -p .claude/skills
cp -r omg-learn .claude/skills/

# Or Goose-specific locations
mkdir -p .goose/skills
cp -r omg-learn .goose/skills/

mkdir -p .agents/skills
cp -r omg-learn .agents/skills/
```

**Tip:** Use `.claude/skills/` for maximum compatibility across platforms!

### OpenSkills

**Global:**
```bash
cp -r omg-learn ~/.agent/skills/
openskills sync -y
```

**Project-specific:**
```bash
cp -r omg-learn .agent/skills/
openskills sync -y
```

### Cursor

**Global:**
```bash
cp -r omg-learn ~/.agent/skills/
openskills sync -y
```

**Project-specific:**
```bash
cp -r omg-learn .agent/skills/
openskills sync -y
```

### Mixed Teams (Multiple Tools)

If your team uses different tools, use symlinks for compatibility:
```bash
# In your project root - choose the pattern that works for your team
ln -s .claude/skills .agent/skills   # OpenSkills/Cursor ← Claude Code
ln -s .claude/skills .goose/skills   # Goose ← Claude Code
ln -s .goose/skills .agent/skills    # OpenSkills ← Goose
```

**Recommendation:** Use `.claude/skills/` as your primary location since it's supported by both Claude Code and Goose (Goose checks `.claude/skills/` first). Then symlink for other tools as needed.

## Installing Platform Hooks (Optional but Recommended!)

Platform hooks catch mistakes BEFORE they happen. This is optional - omg-learn works fine without them, but hooks make it much more powerful!

### Automatic Installation (Recommended)

The omg-learn skill will offer to install hooks automatically the first time you use it. Just say "yes" when prompted!

### Manual Installation

**For Claude Code or Cursor:**

1. Navigate to where you installed omg-learn:
   ```bash
   cd ~/.claude/skills/omg-learn  # or ~/.agent/skills/omg-learn for Cursor
   ```

2. Run the installation script:
   ```bash
   ./scripts/install-hooks.sh
   ```

3. Choose scope:
   - **Global** (all projects) - Recommended for most users
   - **Project-local** (current project only) - For project-specific patterns

4. The script will:
   - Auto-detect your platform (Claude Code or Cursor)
   - Install hook scripts to the appropriate location
   - Create initial config with "omg!" detection example
   - Register hooks in your settings

### What Gets Installed

**Claude Code:**
- `~/.claude/hooks/pretool-checker.sh` - Checks before tool use
- `~/.claude/hooks/prompt-checker.sh` - Checks user prompts
- `~/.claude/omg-learn-patterns.json` - Pattern configuration file

**Cursor:**
- `~/.cursor/hooks/before-shell.sh` - Checks before shell commands
- `~/.cursor/omg-learn-patterns.json` - Pattern configuration file

### Managing Patterns

**View current patterns:**
```bash
cat ~/.claude/omg-learn-patterns.json  # or ~/.cursor/omg-learn-patterns.json
```

**Disable a pattern:**
Edit the patterns file and set `"enabled": false`

**Add patterns:**
Use the omg-learn workflow (it will ask if you want to create a pattern after creating a skill)

## Usage

### Recommended: Create a Custom Command

Instead of relying on "omg!" detection, we recommend creating an explicit command in your editor. This is clearer and more reliable.

**For Cursor**, create `.cursor/commands/omg.md`:
```markdown
Oh no! You just did something bad. You'll need to fix that, but FIRST let's make sure that you learn and don't do it again. Everyone makes mistakes, but it's frustrating to never learn. Luckily, you CAN learn.

1. Run `openskills read omg-learn` and follow that process.
2. git commit the new skill
  * unstage other changes if necessary (but do not lose them!)
  * add and commit just the skill changes or additions
  * if on a branch, if possible, cherry-pick that to `main`
  * re-stage anything else uncommited
3. now, using the new skill, correct the mistake
4. and back to your regular work, smarter and wiser
```

**For Claude Code:**

Create a deliberate workflow when you make a mistake that should be learned:

1. **Invoke the skill:**
   ```
   /omg-learn
   ```
   Or let Claude detect "omg!" in your corrections

2. **Follow the guided process:**
   - Claude analyzes what went wrong
   - Determines if skill should be global or project-local
   - Checks for existing skills to update
   - Proposes the new/updated skill content
   - Creates the skill file after your approval
   - Skill is immediately available (auto-discovered)

3. **Commit the skill (for project skills):**
   ```bash
   git add .claude/skills/<skill-name>
   git commit -m "Add <skill-name> skill: <brief description>"
   ```

4. **Use the new skill:**
   Claude now has persistent knowledge and won't make that mistake again!

**Tip:** For team projects, commit skills to version control so everyone benefits from the learning.

**For Goose:**

Goose automatically discovers and loads skills - just invoke when you need it:

1. **Trigger the skill:**
   - Say "omg!" during a correction (Goose will auto-detect and match the skill)
   - Or explicitly request: "Use the omg-learn skill"

2. **Follow the guided workflow:**
   - Goose analyzes the correction and determines what knowledge to preserve
   - Proposes creating or updating a skill with proper structure
   - Shows the full skill content for your approval
   - Creates the skill file after approval
   - Skill is immediately available (auto-discovered on next session)

3. **Commit for team sharing (project skills):**
   ```bash
   git add .claude/skills/<skill-name>  # or .goose/skills/
   git commit -m "Add <skill-name> skill: <brief description>"
   ```

4. **Benefit from persistent learning:**
   Goose now has this knowledge permanently and won't make the same mistake!

**Note:** Goose loads skills at session start, so restart your session or explicitly invoke to use new skills immediately.

### Alternative: "omg!" Detection

If you prefer, the AI can also detect when you say "omg!" during a correction:

1. **Analyze the correction** - Identify what went wrong
2. **Check for global intent** - Determine if it should be global or project-local
3. **Search existing skills** - Look for related skills to update
4. **Propose changes** - Show what will be created/updated
5. **Create/update skill** - After user approval
6. **Register the skill** - Run `openskills sync -y`

## Dependencies

**All Platforms:**
- [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) skill
  - Pre-installed in Claude Code and Goose
  - Install separately for OpenSkills/Cursor

**Platform-Specific:**
- **OpenSkills/Cursor**: [`openskills`](https://github.com/numman-ali/openskills) CLI tool
- **Claude Code/Goose**: No additional tools needed (built-in skill support)

**For Platform Hooks (Optional):**
- `jq` - JSON parser for hook scripts (usually pre-installed on Mac/Linux)
  - Install: `brew install jq` (Mac) or `sudo apt install jq` (Linux)
  - Hooks will warn if jq is not available and suggest manual configuration

## Structure

This skill follows the standard skill format:
- `SKILL.md` - Main skill file with YAML frontmatter
- Progressive disclosure principle
- Concise, action-oriented content

## Best Practices

**Keep your base instructions minimal.** Too many instructions dilute their impact:

- **AGENTS.md**: Include only your project's MOST CRUCIAL guidance. Add up-front detail on how to load skills on demand (e.g., "Run `openskills read <skill-name>` when you need specific knowledge"). Let skills handle the details.
- **Cursor Rules**: Same principle - too many rules and they lose weight. Keep it focused.

Skills are meant to be loaded on-demand for specific situations, keeping your agent's base context clean and effective.

## License

This skill is released into the public domain under the [Unlicense](https://unlicense.org/). Use it however you like!
