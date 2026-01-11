# Skill-Linked Pattern Template

When creating a skill, generate a companion context injection pattern using this template.

This reference document provides the structured template that Claude uses to generate patterns conversationally.

## Pattern Structure

```json
{
  "id": "remind-[skill-name]-skill",
  "description": "Reminds Claude to use [skill-name] skill",
  "hook": "UserPromptSubmit",
  "pattern": "(keyword1|keyword2|keyword3)",
  "action": "warn",
  "message": "💡 Consider using the [skill-name] skill. It covers: [brief summary from description]\n\nSkill: ~/.claude/skills/[skill-name].md",
  "skill_reference": "[skill-name]",
  "enabled": true,
  "note": "Companion pattern for skill"
}
```

## Field Descriptions

**id:** Use format `remind-[skill-name]-skill` for consistency

**description:** Brief description of what the pattern does

**hook:** Always `UserPromptSubmit` for context injection patterns

**pattern:** Regex matching keywords (see Keyword Selection Guidelines below)

**action:** Always `warn` for context injection (not `block` or `ask`)

**message:** Template format:
```
💡 Consider using the [skill-name] skill. It covers: [brief summary]

Skill: [path to skill file]
```

**skill_reference:** The skill name (used for linking and cross-referencing)

**enabled:** Set to `true` by default

**note:** Optional note explaining the pattern

## Keyword Selection Guidelines

**Extract keywords from skill description:**
- Look for technical terms (database, git, production, authentication, etc.)
- Look for "Use when..." or "When..." clauses
- Domain-specific vocabulary
- User-provided trigger contexts

**Pattern examples:**

| Skill | Keywords | Pattern Regex |
|-------|----------|---------------|
| database-migrations | database, migration, schema, alter | `(database\|migration\|schema\|alter)` |
| branch-protection | branch, main, master, git checkout | `(branch\|main\|master\|git\\s+checkout)` |
| production-deployment | production, deploy, deployment, release | `(production\|deploy\|deployment\|release)` |
| authentication-patterns | auth, login, oauth, jwt, token | `(auth\|login\|oauth\|jwt\|token)` |

**Tips for good patterns:**
- Use word boundaries when needed: `\bkeyword\b`
- Use `\s+` for multi-word phrases: `git\s+checkout`
- Keep it simple - 3-5 keywords is usually enough
- Test the pattern to avoid false positives

## Conversational Workflow

This is how Claude should interact with the user when creating a skill-linked pattern.

### Step 1: Read the Skill Description

After the skill is created or when user requests a pattern for an existing skill, read the skill file to understand:
- What the skill is about
- When it should be used
- Technical vocabulary and domain terms

### Step 2: Suggest Keywords

Analyze the skill description and identify potential keywords.

**Example:**
```
User just created skill: database-migrations.md
Description: "Use when working with database schema changes, migrations, alters"

Claude: "I see these potential trigger keywords in your skill description:
  - database
  - migration
  - schema
  - alter

These would trigger the pattern when you mention database-related tasks."
```

### Step 3: Ask for Confirmation

Show the proposed pattern and ask if the user wants to create it.

**Example:**
```
Claude: "Should I create a companion pattern with these keywords?

The pattern would inject this context when you mention database work:
'💡 Consider using the database-migrations skill. It covers: reversible migrations, up/down functions, database safety guidelines.'

Options:
  - Yes (create with these keywords)
  - Customize (edit the keyword list)
  - Skip (don't create pattern)"
```

### Step 4: Ask About Scope (ALWAYS)

**ALWAYS explicitly ask where to save the pattern - never assume!**

Ask if the pattern should be global or local.

**Example:**
```
Claude: "Should this pattern be global (all projects) or local (this project only)?

Options:
  - Global (~/.claude/omg-learn-patterns.json) - applies everywhere
  - Local (.claude/omg-learn-patterns.json) - this project only

Default suggestion: Match the skill scope
[Since your database-migrations skill is global, I suggest making the pattern global too]"
```

**Decision guidance:**
- If skill is global → suggest global pattern (but still ask!)
- If skill is local → suggest local pattern (but still ask!)
- User may want different scopes (skill global, pattern local) - that's okay!

### Step 5: Generate Pattern JSON

Based on user confirmation, generate the complete pattern JSON:

```json
{
  "id": "remind-database-migrations-skill",
  "description": "Reminds Claude to use database-migrations skill",
  "hook": "UserPromptSubmit",
  "pattern": "(database|migration|schema|alter)",
  "action": "warn",
  "message": "💡 Consider using the database-migrations skill. It covers: reversible migrations, up/down functions, database safety guidelines.\n\nSkill: ~/.claude/skills/database-migrations.md",
  "skill_reference": "database-migrations",
  "enabled": true,
  "note": "Companion pattern for database-migrations skill"
}
```

### Step 6: Add Pattern to File

Write the pattern JSON to the appropriate patterns file based on the user's scope choice:
- Global: `~/.claude/omg-learn-patterns.json` or `~/.cursor/omg-learn-patterns.json`
- Local: `.claude/omg-learn-patterns.json` or `.cursor/omg-learn-patterns.json`

**Note:** The actual CLI implementation for adding patterns will be simple and mechanical - it just receives structured JSON and adds it to the file. NO keyword extraction or AI logic in the CLI.

## Example Workflow

**Complete example from start to finish:**

1. User says "omg! I forgot to make my database migration reversible!"

2. Claude follows omg-learn workflow:
   - Creates skill: `database-migrations.md`
   - Description: "Use when working with database schema changes. Migrations must be reversible with up() and down() functions."

3. Claude asks about skill scope:
   ```
   Should this skill be global (all projects) or local (this project only)?
   ```

4. User chooses: "Global"

5. Claude reads the skill description and suggests keywords:
   ```
   I see these keywords: database, migration, schema
   Should I create a companion pattern?
   ```

6. User confirms: "Yes"

7. Claude asks about pattern scope:
   ```
   Should this pattern be global or local?
   (Suggestion: Global, to match the skill scope)
   ```

8. User confirms: "Global"

9. Claude generates pattern JSON using this template

10. Claude writes pattern to global patterns file: `~/.claude/omg-learn-patterns.json`

11. Done! Next time user says "I need to update the database schema", the pattern triggers and reminds Claude to use the skill.

## When to Use Skill-Linked Patterns

**Use for:**
- Skills with clear technical vocabulary (database, auth, deployment, testing)
- Skills about specific domains or tools
- Skills with "Use when..." contexts
- Skills that apply to specific situations

**Don't use for:**
- Pure reference skills with no triggers
- Skills that are always active
- Skills without user-facing keywords
- Skills about general programming (too broad)

## Platform Compatibility

**Claude Code:**
- Context injection works perfectly (true context added to Claude's prompt)
- Claude sees the message and can use the skill

**Cursor:**
- Message shown as warning to user
- Cursor AI doesn't see the message (not true context injection)
- Still useful as a reminder to the user

Both platforms benefit from skill-linked patterns!
