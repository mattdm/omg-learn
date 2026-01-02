---
name: omg-learn
description: Learning from user corrections by creating or updating skills. Use when user says "omg!" during corrections, when user provides feedback to create persistent knowledge, when creating skills from corrections, when updating existing skills based on mistakes, or when user wants to ensure AI never makes the same mistake again. Handles both creating new skills and updating existing ones, with guidance on global vs project-local skills.
---

# OMG! Learning from Corrections

When the user says "omg!" (case-insensitive) while correcting you, create or update a skill so you never make that mistake again.

## Quick Reference: Load skill-creator First

**ALWAYS load the skill-creator skill before creating any skill:**

Read the skill file: `.agent/skills/skill-creator/SKILL.md`

The skill-creator provides complete guidance on skill structure, progressive disclosure, and best practices.

## Workflow

When user says "omg!" during a correction:

### 1. Analyze the Correction

- What did you do wrong?
- What is the correct behavior/information?
- What knowledge should be preserved?

### 2. Check for Global Intent

If user says "globally", "system wide", "everywhere", or similar:
- Ask: "Should this be a global skill (~/.agent/skills/) or project-local (.agent/skills/)?"
- **Global skills**: Apply to all projects system-wide
- **Project skills**: Live in `.agent/skills/` (same as `.claude/skills/`)

### 3. Check Existing Skills

Search the appropriate location for related skills:
- If found: Propose updating that skill
- If not found: Propose creating a new skill

### 4. Propose Changes (Show for Approval)

- For updates: Show before/after diff
- For new skills: Show the full content with frontmatter
- Indicate storage location (global vs project-local)

### 5. After Approval: Create or Update

Create or update the skill file at the specified location.

### 6. Run openskills sync

Update AGENTS.md (or global registry) with the new/updated skill:

```bash
openskills sync -y
```

## Essential Skill Structure (Embedded from skill-creator)

### Required Components

Every skill MUST have:

```
skill-name/
└── SKILL.md (required)
    ├── YAML frontmatter (REQUIRED!)
    │   ├── name: skill-name (REQUIRED)
    │   └── description: ... (REQUIRED)
    └── Markdown body with instructions
```

### YAML Frontmatter (MANDATORY)

```yaml
---
name: skill-name
description: Comprehensive description of what the skill does AND when to use it. Include triggers, contexts, and use cases. This is the PRIMARY triggering mechanism - be thorough!
---
```

**Critical**:
- `name` and `description` are REQUIRED
- Skills without frontmatter won't be listed in the skills table in AGENTS.md
- Description must include BOTH what the skill does AND when to use it
- Don't put "when to use" in the body - it's only loaded AFTER triggering

### Optional Bundled Resources

```
skill-name/
├── SKILL.md (required)
├── scripts/          - Executable code (Python/Bash/etc.) for deterministic tasks
├── references/       - Documentation loaded into context as needed
└── assets/           - Files used in output (templates, icons, etc.)
```

**When to use:**
- **scripts/**: Repeatedly rewritten code, deterministic reliability needed
- **references/**: Detailed docs, schemas, API specs (keeps SKILL.md lean)
- **assets/**: Templates, images, boilerplate copied to output

### Progressive Disclosure Principle

Skills use three-level loading:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed by Claude

**Keep SKILL.md concise** - The context window is a shared resource. Move detailed information to `references/` files.

### Conciseness is Key

Default assumption: Claude is already smart. Only add context Claude doesn't have.

Challenge each piece of information:
- "Does Claude really need this explanation?"
- "Does this paragraph justify its token cost?"

Prefer concise examples over verbose explanations.

## Storage Locations

- **Project skills**: `.agent/skills/<name>/SKILL.md` (version controlled with this project)
- **Global skills**: `~/.agent/skills/<name>/SKILL.md` (applies to all projects)

Note: `.claude/skills` is a symlink to `.agent/skills` for compatibility with different AI agents.

## Example Workflow

User: "omg! This project uses a custom binary location, it's at target/x86_64-unknown-linux-musl/release/myapp"

Your response:
1. Load skill-creator skill
2. Analyze: You looked in wrong location for binary
3. Check: No existing skill about binary locations for this project
4. Propose: Creating `.agent/skills/binary-locations/SKILL.md` with proper frontmatter
5. Show the full content for approval
6. After approval: Create the skill file
7. Run `openskills sync -y` to register it

## Registration

After creating/updating a skill:
- Project skills: Automatically registered in `AGENTS.md` via `openskills sync`
- Global skills: Registered in `~/.agent/skills/registry.md` (or equivalent)
