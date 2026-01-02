# OMG! Learning Skill

A skill for AI agents that enables learning from user corrections by creating or updating skills when users express frustration with "omg!" during corrections.

## What it does

This skill provides a structured workflow for:
- Detecting when users say "omg!" during corrections
- Analyzing what went wrong and what should be preserved
- Creating or updating skills to prevent the same mistakes
- Handling both global and project-local skill creation

## Installation

### As a Global Skill
```bash
# Copy to your global skills directory
cp -r omg-learn ~/.agent/skills/

# Register the skill
openskills sync -y
```

### As a Project Skill
```bash
# Copy to your project's skills directory
cp -r omg-learn .agent/skills/

# Register the skill
openskills sync -y
```

## Usage

When a user says "omg!" during a correction, the AI will:

1. **Analyze the correction** - Identify what went wrong
2. **Check for global intent** - Determine if it should be global or project-local
3. **Search existing skills** - Look for related skills to update
4. **Propose changes** - Show what will be created/updated
5. **Create/update skill** - After user approval
6. **Register the skill** - Run `openskills sync -y`

## Example

```
User: "omg! The config file is at ~/.config/myapp/settings.json, not ~/.myapp/config.json"

AI Response:
1. Loads skill-creator skill
2. Analyzes: Wrong config file location assumption
3. Proposes creating .agent/skills/myapp-config-locations/SKILL.md
4. Shows full skill content for approval
5. Creates skill after approval
6. Runs openskills sync
```

## Dependencies

- `skill-creator` skill must be available
- `openskills` command for registration

## Structure

This skill follows the standard skill format:
- `SKILL.md` - Main skill file with YAML frontmatter
- Progressive disclosure principle
- Concise, action-oriented content

## License

This skill is released into the public domain under the [Unlicense](https://unlicense.org/). Use it however you like!
