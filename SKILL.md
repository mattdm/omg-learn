---
name: omg-learn
description: Learning from user corrections by creating or updating skills. Use when user says "omg!" during corrections, when user provides feedback to create persistent knowledge, when creating skills from corrections, when updating existing skills based on mistakes, or when user wants to ensure AI never makes the same mistake again. Handles both creating new skills and updating existing ones, with guidance on global vs project-local skills.
---

# OMG! Learning from Corrections

When the user says "omg!" (case-insensitive) while correcting you, create or update a skill so you never make that mistake again.

**ALWAYS load the skill-creator skill first.**

## Workflow

When user says "omg!" during a correction:

### 1. Analyze the Correction

- What did you do wrong?
- What is the correct behavior/information?
- What knowledge should be preserved?
- **Is this a workflow skill?** (Will it be explicitly invoked like `/deploy` or `/migrate`?)

**Important**: When creating the skill description, include specific trigger contexts.
Think about WHEN the skill should activate - situations, actions, or tasks.
Examples: "Use when building/running project", "Use when analyzing database code", "When you have deployment questions"

**Consider skill hooks ONLY for workflow skills**:
- Workflow skills are explicitly invoked (user runs `/skill-name`)
- Hooks enforce safe behavior during that workflow
- Examples: `/deploy`, `/release`, `/migrate`, `/code-review`
- **Don't use hooks for passive knowledge** - they won't catch the first mistake!

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
- **Always show hooks** if they're part of the solution
- Explain what the hook checks and when it triggers
- Indicate storage location (global vs project-local)

### 5. After Approval: Create or Update

Create or update the skill file at the specified location.

### 6. Register the Skill

The skill will be registered according to your platform's skill discovery mechanism.

## Essential Skill Structure (Embedded from skill-creator)

### Required Components

Every skill MUST have:

```
skill-name/
└── SKILL.md (required)
    ├── YAML frontmatter (REQUIRED!)
    │   ├── name: skill-name (REQUIRED)
    │   ├── description: ... (REQUIRED)
    │   └── hooks: ... (OPTIONAL but POWERFUL!)
    └── Markdown body with instructions
```

### YAML Frontmatter (MANDATORY)

```yaml
---
name: skill-name
description: Comprehensive description of what the skill does AND when to use it. Include triggers, contexts, and use cases. This is the PRIMARY triggering mechanism - be thorough!
hooks:
  PreToolUse:
    - matcher: "ToolName"
      hooks:
        - type: command
          command: "./scripts/check-behavior.sh $TOOL_INPUT"
          once: true
---
```

**Critical**:
- `name` and `description` are REQUIRED
- Skills without frontmatter won't be listed in the skills table in AGENTS.md
- Description must include BOTH what the skill does AND when to use it
- Don't put "when to use" in the body - it's only loaded AFTER triggering

### Skill Hooks: Limited But Useful

**CRITICAL LIMITATION**: Skill hooks **ONLY work when the skill is already loaded**!

This means:
- ❌ A hook CANNOT catch the mistake that triggered the "omg!" (the skill isn't loaded yet)
- ✅ A hook CAN prevent mistakes during intentional workflows (when the skill is loaded on purpose)

**Skill hooks are most useful for WORKFLOW skills**, not correction-based skills:

**Good use cases** (skill is intentionally loaded):
- A `/deploy` skill: Hook blocks deployment to production on wrong branch
- A `/code-review` skill: Hook validates that review checklist steps are followed
- A `/database-migration` skill: Hook prevents unsafe migration commands
- A `/release` skill: Hook ensures changelog is updated before release

**Poor use cases** (skill loads AFTER the mistake):
- Learning from "omg!" moments - the hook can't catch the first occurrence
- Corrective skills - they only load after you've already made the mistake

**For omg-learn**: Only include hooks if the resulting skill is meant to be **explicitly invoked** for a workflow, not just for passive learning.

Skill hooks run during the skill's lifecycle and can **intercept** actions before they happen:

- **PreToolUse**: Runs BEFORE a tool is used (can block unwanted actions)
- **PostToolUse**: Runs AFTER a tool completes (can validate results)
- **Stop**: Runs when the skill finishes

**Available environment variables in hooks**:
- `$TOOL_INPUT`: The input being passed to the tool
- `$TOOL_NAME`: Name of the tool being called

**Hook examples that prevent mistakes**:

```yaml
# Example 1: Prevent committing to wrong branch
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c 'if [[ \"$TOOL_INPUT\" == *\"git commit\"* ]]; then branch=$(git branch --show-current); if [[ \"$branch\" == \"main\" ]]; then echo \"ERROR: Direct commits to main not allowed\"; exit 1; fi; fi'"

# Example 2: Validate file paths before writing
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "./scripts/validate-write-path.sh $TOOL_INPUT"

# Example 3: Check for secrets before committing
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c 'if [[ \"$TOOL_INPUT\" == *\"git add\"* ]]; then git diff --cached | grep -qE \"(API_KEY|SECRET|PASSWORD)\" && echo \"WARNING: Possible secrets detected\" && exit 1 || exit 0; fi'"

# Example 4: Prevent head with command output (loses critical end output)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c 'if [[ \"$TOOL_INPUT\" == *\"|\"*\"head\"* ]] && [[ \"$TOOL_INPUT\" != *\"cat \"* ]] && [[ \"$TOOL_INPUT\" != *\"<\"* ]]; then echo \"ERROR: Using head with command output loses critical success/failure info at the end. Use full output or tail instead.\"; exit 1; fi'"
```

**When designing a skill from an "omg!" moment**:

1. **Decide if hooks make sense**: Is this a workflow skill that will be explicitly invoked? Or just passive knowledge?
2. **If workflow skill**:
   - **Identify the mistake**: What tool was used incorrectly?
   - **Design a hook matcher**: Which tool needs interception? (Bash, Write, Edit, etc.)
   - **Write validation logic**: What check would have caught this?
   - **Add to frontmatter**: Include the hook in the YAML
   - **Make it user-invocable**: User should explicitly run `/skill-name` to activate it
3. **If passive knowledge**: Skip hooks, just document the correct behavior in the skill body

Skill hooks are **scoped to the skill** - they only run when the skill is active and are automatically cleaned up when done.

### Common Hook Patterns for Catching Mistakes

**Pattern 1: Validate before running commands**
```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c '[[ \"$TOOL_INPUT\" == *\"dangerous-command\"* ]] && echo \"Blocked!\" && exit 1'"
```

**Pattern 2: Check file paths before writing**
```yaml
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "bash -c 'echo \"$TOOL_INPUT\" | grep -q \"forbidden/path\" && echo \"Cannot write to forbidden path\" && exit 1'"
```

**Pattern 3: Validate after editing**
```yaml
hooks:
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "./scripts/lint-file.sh"
```

**Pattern 4: One-time setup check**
```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check-dependencies.sh"
          once: true
```

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

## Example Workflows

### Example 1: Passive Knowledge Skill (No Hooks)

User: "omg! This project uses a custom binary location, it's at target/x86_64-unknown-linux-musl/release/myapp"

**Your response:**
1. Load skill-creator skill
2. Analyze: You looked in wrong location for binary
3. **Is this a workflow skill?** No - this is passive knowledge that should auto-load
4. **Skip hooks** - hooks can't catch the first mistake anyway
5. Propose: Creating skill WITHOUT hooks (just documentation)
6. Check: No existing skill about binary locations for this project
7. Show the skill content for approval
8. After approval: Create the skill file
9. Register the skill according to your platform

```yaml
---
name: project-binary-location
description: Custom binary location for this project. Use when building or running the project binary.
---

# Binary Location

This project uses a custom target for the binary:
- Location: `target/x86_64-unknown-linux-musl/release/myapp`
- Use this path when running or testing the binary
```

### Example 2: Workflow Skill (WITH Hooks)

User: "omg! Don't commit to main! Always use feature branches! And make sure I always run this check before committing."

**Your response:**
1. Load skill-creator skill
2. Analyze: Committed directly to main branch
3. **Is this a workflow skill?** Yes - user wants an explicit workflow to run before commits
4. **Design as user-invocable workflow**: User runs `/commit` which enforces branch rules
5. Propose skill with hook:

```yaml
---
name: safe-commit
description: Safe commit workflow with branch protection. Invoke explicitly with /safe-commit before making commits.
user-invocable: true
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c 'if [[ \"$TOOL_INPUT\" == *\"git commit\"* ]]; then branch=$(git branch --show-current); if [[ \"$branch\" == \"main\" || \"$branch\" == \"master\" ]]; then echo \"ERROR: Direct commits to main/master not allowed. Use feature branches.\"; exit 1; fi; fi'"
---

# Safe Commit Workflow

Run this skill explicitly with `/safe-commit` before making commits.

The hook will block commits to main/master branches.

When starting new work:
1. Create branch: `git checkout -b feature/description`
2. Make changes
3. Run `/safe-commit` to activate protection
4. Commit with confidence - hook prevents main/master commits
```

5. Show this for approval with explanation: "Hook only works when you explicitly run `/safe-commit` - it can't catch passive commits"
6. After approval: Create at `.agent/skills/safe-commit/SKILL.md`

### Example 3: Passive Knowledge (No Hooks - They Won't Help)

User: "omg! You used `npm test | head -50` and missed the actual test failures at the end! head is only useful for peeking at files, not command output where the crucial success/failure info is at the end!"

**Your response:**
1. Load skill-creator skill
2. Analyze: Used `head` to truncate command output, cutting off critical end results
3. **Is this a workflow skill?** No - this is general knowledge that should auto-load when running commands
4. **Skip hooks** - they won't help because:
   - The skill loads AFTER the mistake (when you say "omg!")
   - Hook can't catch the first occurrence that triggered the correction
   - This is passive knowledge, not an explicit workflow
5. Propose skill WITHOUT hooks (just documentation):

```yaml
---
name: command-output-handling
description: Best practices for command output. Use when running commands that produce output like tests, builds, or deployments.
---

# Command Output Best Practices

**NEVER use `head` with command output** - it truncates the end where success/failure messages appear.

Good patterns:
- `npm test` - See full output
- `npm test 2>&1 | tee test-output.txt` - Save full output
- `npm test | tail -100` - See the END (where errors are)

Bad patterns:
- `npm test | head -50` - Misses failures at the end
- `make build | head -100` - Misses "Build failed" messages
- `pytest | head -20` - Misses test summary

Exception: `head` is fine for reading files (`cat file.txt | head` or `head file.txt`)
```

5. Show this for approval with explanation: "This is passive knowledge - no hooks needed since they can't prevent the first mistake anyway"
6. After approval: Create at `.agent/skills/command-output-handling/SKILL.md`

**Best practice:** Commit skills to version control for team sharing.
