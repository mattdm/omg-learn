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
- **Could a hook have prevented this?** What tool was involved?

**Important**: When creating the skill description, include specific trigger contexts.
Think about WHEN the skill should activate - situations, actions, or tasks.
Examples: "Use when building/running project", "Use when analyzing database code", "When you have deployment questions"

**CRITICAL**: Think about **actionable hooks** that could catch this mistake:
- If the mistake involved running a command: Add a `PreToolUse` hook for `Bash`
- If the mistake was writing to wrong file: Add a `PreToolUse` hook for `Write`
- If the mistake was editing incorrectly: Add a `PreToolUse` hook for `Edit`
- If validation is needed after an action: Add a `PostToolUse` hook

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

### Hooks: Your Safety Net for Catching Mistakes

**IMPORTANT**: When the user says "omg!" about a mistake, consider if a **hook** could have caught it!

Hooks run during the skill's lifecycle and can **intercept** actions before they happen:

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

1. **Identify the mistake**: What tool was used incorrectly?
2. **Design a hook matcher**: Which tool needs interception? (Bash, Write, Edit, etc.)
3. **Write validation logic**: What check would have caught this?
4. **Add to frontmatter**: Include the hook in the YAML

Hooks are **scoped to the skill** - they only run when the skill is active and are automatically cleaned up when done.

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

### Example 1: Binary Location Mistake

User: "omg! This project uses a custom binary location, it's at target/x86_64-unknown-linux-musl/release/myapp"

**Your response:**
1. Load skill-creator skill
2. Analyze: You looked in wrong location for binary
3. **Consider hooks**: Could add a `PreToolUse` hook for `Bash` to validate binary paths before running
4. Check: No existing skill about binary locations for this project
5. Propose: Creating skill with validation hook
6. Show the full content (including hooks) for approval
7. After approval: Create the skill file
8. Register the skill according to your platform

### Example 2: Preventing Wrong Branch Commits

User: "omg! Don't commit to main! Always use feature branches!"

**Your response:**
1. Load skill-creator skill
2. Analyze: Committed directly to main branch
3. **Identify hook opportunity**: `PreToolUse` hook for `Bash` can intercept git commits
4. Propose skill with hook:

```yaml
---
name: branch-protection
description: Enforce feature branch workflow. Use when working with git commits.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c 'if [[ \"$TOOL_INPUT\" == *\"git commit\"* ]]; then branch=$(git branch --show-current); if [[ \"$branch\" == \"main\" || \"$branch\" == \"master\" ]]; then echo \"ERROR: Direct commits to main/master not allowed. Use feature branches.\"; exit 1; fi; fi'"
---

Always create feature branches for new work. Never commit directly to main or master.

When starting new work:
1. Create branch: `git checkout -b feature/description`
2. Make changes and commit
3. Push and create PR
```

5. Show this for approval with explanation of how the hook works
6. After approval: Create at `.agent/skills/branch-protection/SKILL.md`

### Example 3: Preventing head with Command Output

User: "omg! You used `npm test | head -50` and missed the actual test failures at the end! head is only useful for peeking at files, not command output where the crucial success/failure info is at the end!"

**Your response:**
1. Load skill-creator skill
2. Analyze: Used `head` to truncate command output, cutting off critical end results
3. **Identify hook opportunity**: `PreToolUse` hook for `Bash` can detect piping commands to `head`
4. Propose skill with hook:

```yaml
---
name: command-output-handling
description: Prevent truncating command output with head. Use when running commands that produce output.
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "bash -c 'if [[ \"$TOOL_INPUT\" == *\"|\"*\"head\"* ]] && [[ \"$TOOL_INPUT\" != *\"cat \"* ]] && [[ \"$TOOL_INPUT\" != *\"<\"* ]]; then echo \"ERROR: Using head with command output loses critical success/failure info at the end. Use full output or tail instead.\"; exit 1; fi'"
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

5. Show this for approval with explanation: "The hook detects when commands are piped to head (but allows head for file reading) and blocks execution"
6. After approval: Create at `.agent/skills/command-output-handling/SKILL.md`

**Best practice:** Commit skills to version control for team sharing.
