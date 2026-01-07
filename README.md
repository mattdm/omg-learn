# OMG! Learning Skill

A skill for AI agents that enables learning from user corrections by creating or updating skills when users express frustration with "omg!" during corrections.

## What it does

This skill provides a structured workflow for:
- Detecting when users say "omg!" during corrections
- Analyzing what went wrong and what should be preserved
- Creating or updating skills to prevent the same mistakes
- Handling both global and project-local skill creation

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
# In your project root
ln -s .claude/skills .agent/skills  # Or vice versa
```

This allows Claude Code users to use `.claude/skills/` while OpenSkills/Cursor users use `.agent/skills/` - they point to the same location.

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
  - Pre-installed in Claude Code
  - Install separately for OpenSkills/Cursor

**Platform-Specific:**
- **OpenSkills/Cursor**: [`openskills`](https://github.com/numman-ali/openskills) CLI tool
- **Claude Code**: No additional tools needed (built-in skill support)

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
