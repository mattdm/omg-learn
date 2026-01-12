#!/bin/bash
set -e

# omg-learn Hook Installation Script
# Installs platform hooks for pattern-based mistake prevention

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 omg-learn Hook Installer"
echo "============================"
echo ""

# Detect all platforms (supports .claude, .cursor, .agents, .agent)
detect_platforms() {
    local platforms=()

    # Check for Claude Code
    if [[ -d "$HOME/.claude" ]] || [[ -d ".claude" ]]; then
        platforms+=("claude")
    fi

    # Check for Cursor
    if [[ -d "$HOME/.cursor" ]] || [[ -d ".cursor" ]]; then
        platforms+=("cursor")
    fi

    # Check for generic .agents/.agent - add both claude and cursor if they exist
    if [[ -d "$HOME/.agents" ]] || [[ -d "$HOME/.agent" ]] || [[ -d ".agents" ]] || [[ -d ".agent" ]]; then
        if command -v claude &>/dev/null || [[ -f "$HOME/.claude/settings.json" ]]; then
            if [[ ! " ${platforms[@]} " =~ " claude " ]]; then
                platforms+=("claude")
            fi
        fi
        if command -v cursor &>/dev/null || [[ -f "$HOME/.cursor/hooks.json" ]]; then
            if [[ ! " ${platforms[@]} " =~ " cursor " ]]; then
                platforms+=("cursor")
            fi
        fi
    fi

    echo "${platforms[@]}"
}

PLATFORMS=($(detect_platforms))

if [[ ${#PLATFORMS[@]} -eq 0 ]]; then
    echo "❌ Could not detect Claude Code or Cursor installation"
    echo "   Please ensure you have one of these in your home directory:"
    echo "     - ~/.claude/ (Claude Code)"
    echo "     - ~/.cursor/ (Cursor)"
    echo "     - ~/.agents/ or ~/.agent/ (generic)"
    exit 1
fi

echo "✅ Detected platform(s): ${PLATFORMS[@]}"
echo ""

# Ask for installation scope
echo "Choose installation scope:"
echo "  1) Global (all projects)"
echo "  2) Project-local (current project only)"
read -p "Enter choice [1-2]: " SCOPE_CHOICE

case $SCOPE_CHOICE in
    1)
        SCOPE="global"
        ;;
    2)
        SCOPE="project-local"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""

# Install hooks for each detected platform
for PLATFORM in "${PLATFORMS[@]}"; do
    echo "=========================================="
    echo "Installing for: $PLATFORM"
    echo "=========================================="
    echo ""

    # Determine paths based on scope
    if [[ "$SCOPE" == "global" ]]; then
        HOOKS_DIR="$HOME/.$PLATFORM/hooks"
        PATTERNS_FILE="$HOME/.$PLATFORM/omg-learn-patterns.json"
    else
        if [[ ! -d ".$PLATFORM" ]]; then
            mkdir -p ".$PLATFORM"
        fi
        HOOKS_DIR=".$PLATFORM/hooks"
        PATTERNS_FILE=".$PLATFORM/omg-learn-patterns.json"
    fi

    echo "Installing hooks to: $HOOKS_DIR"
    echo "Patterns file: $PATTERNS_FILE"
    echo ""

    # Create hooks directory
    mkdir -p "$HOOKS_DIR"

    # Install hook scripts based on platform
    if [[ "$PLATFORM" == "claude" ]]; then
    echo "📝 Installing Claude Code hooks..."
    cp "$SCRIPT_DIR/hooks/omg-learn-tool-checker.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/omg-learn-tool-checker.py"
    cp "$SCRIPT_DIR/hooks/omg-learn-prompt-checker.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/omg-learn-prompt-checker.py"
    cp "$SCRIPT_DIR/hooks/omg-learn-post-tool-handler.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/omg-learn-post-tool-handler.py"
    echo "   ✅ omg-learn-tool-checker.py (PreToolUse)"
    echo "   ✅ omg-learn-prompt-checker.py (UserPromptSubmit)"
    echo "   ✅ omg-learn-post-tool-handler.py (PostToolUse)"
elif [[ "$PLATFORM" == "cursor" ]]; then
    echo "📝 Installing Cursor hooks..."
    cp "$SCRIPT_DIR/hooks/before-shell.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/before-shell.py"
    cp "$SCRIPT_DIR/hooks/before-prompt.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/before-prompt.py"
    cp "$SCRIPT_DIR/hooks/after-shell.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/after-shell.py"
    cp "$SCRIPT_DIR/hooks/after-tool.py" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/after-tool.py"
    echo "   ✅ before-shell.py (beforeShellExecution)"
    echo "   ✅ before-prompt.py (beforeSubmitPrompt)"
    echo "   ✅ after-shell.py (afterShellExecution)"
    echo "   ✅ after-tool.py (afterMCPExecution)"
fi

# Create initial patterns file if it doesn't exist
if [[ ! -f "$PATTERNS_FILE" ]]; then
    echo ""
    echo "📋 Creating initial patterns file..."
    cat > "$PATTERNS_FILE" <<'EOF'
{
  "version": "1.0",
  "patterns": [
    {
      "id": "omg-learn-trigger",
      "description": "Detects 'omg!' to trigger the mistake-learning workflow",
      "hook": "UserPromptSubmit",
      "pattern": "[Oo][Mm][Gg]!",
      "action": "warn",
      "message": "🤦 User caught a mistake! Follow the omg-learn workflow:\n1. Acknowledge the mistake\n2. Ask: What tool did I misuse? (Bash/Write/Edit/Prompt)\n3. Ask: What was the problematic input/behavior?\n4. Design pattern: hook, matcher, regex, action, message\n5. Test with omg-learn test\n6. Save the pattern",
      "enabled": true,
      "note": "Triggers the learning workflow when user says 'omg!' to catch mistakes"
    }
  ]
}
EOF
    echo "   ✅ Created $PATTERNS_FILE"
else
    echo ""
    echo "ℹ️  Patterns file already exists: $PATTERNS_FILE"
    echo "   Skipping creation to preserve existing patterns"
fi

# Register hooks in settings.json
echo ""
echo "🔗 Registering hooks in settings..."

if [[ "$PLATFORM" == "claude" ]]; then
    SETTINGS_FILE="$HOME/.claude/settings.json"
    if [[ "$SCOPE" == "project-local" ]]; then
        SETTINGS_FILE=".claude/settings.json"
    fi

    # Create settings file if it doesn't exist
    if [[ ! -f "$SETTINGS_FILE" ]]; then
        echo "{}" > "$SETTINGS_FILE"
    fi

    # Use jq to add hooks configuration
    if command -v jq >/dev/null 2>&1; then
        TEMP_FILE=$(mktemp)

        # Read current settings and add hooks
        jq '. + {
          "hooks": {
            "PreToolUse": [
              {
                "matcher": "Bash|Write|Edit",
                "hooks": [
                  {
                    "type": "command",
                    "command": "'"$HOOKS_DIR/omg-learn-tool-checker.py"'"
                  }
                ]
              }
            ],
            "PostToolUse": [
              {
                "matcher": "Bash|Write|Edit",
                "hooks": [
                  {
                    "type": "command",
                    "command": "'"$HOOKS_DIR/omg-learn-post-tool-handler.py"'"
                  }
                ]
              }
            ],
            "UserPromptSubmit": [
              {
                "hooks": [
                  {
                    "type": "command",
                    "command": "'"$HOOKS_DIR/omg-learn-prompt-checker.py"'"
                  }
                ]
              }
            ]
          }
        }' "$SETTINGS_FILE" > "$TEMP_FILE"

        mv "$TEMP_FILE" "$SETTINGS_FILE"
        echo "   ✅ Hooks registered in $SETTINGS_FILE"
    else
        echo "   ⚠️  jq not found. Please manually add hooks to $SETTINGS_FILE"
        echo "      See scripts/hooks/claude-code-config-example.json for the configuration"
    fi

elif [[ "$PLATFORM" == "cursor" ]]; then
    HOOKS_FILE=".cursor/hooks.json"
    if [[ "$SCOPE" == "global" ]]; then
        HOOKS_FILE="$HOME/.cursor/hooks.json"
    fi

    # Determine paths: relative for project-local, absolute for global
    if [[ "$SCOPE" == "global" ]]; then
        # Global: use absolute paths
        BEFORE_SHELL_HOOK="$HOOKS_DIR/before-shell.py"
        BEFORE_PROMPT_HOOK="$HOOKS_DIR/before-prompt.py"
        AFTER_SHELL_HOOK="$HOOKS_DIR/after-shell.py"
        AFTER_TOOL_HOOK="$HOOKS_DIR/after-tool.py"
    else
        # Project-local: use relative paths (relative to hooks.json location)
        # hooks.json is in .cursor/, so path is ./hooks/script.py
        BEFORE_SHELL_HOOK="./hooks/before-shell.py"
        BEFORE_PROMPT_HOOK="./hooks/before-prompt.py"
        AFTER_SHELL_HOOK="./hooks/after-shell.py"
        AFTER_TOOL_HOOK="./hooks/after-tool.py"
    fi

    # Create hooks file if it doesn't exist
    if [[ ! -f "$HOOKS_FILE" ]]; then
        # Cursor hooks.json format (from cursor-hooks-fix-2026-01-11.md):
        # - Requires "version": 1
        # - Hooks nested inside "hooks" object
        # - No "type": "command" field needed
        cat > "$HOOKS_FILE" <<EOF
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": "$BEFORE_SHELL_HOOK"
      }
    ],
    "afterShellExecution": [
      {
        "command": "$AFTER_SHELL_HOOK"
      }
    ],
    "beforeSubmitPrompt": [
      {
        "command": "$BEFORE_PROMPT_HOOK"
      }
    ],
    "afterMCPExecution": [
      {
        "command": "$AFTER_TOOL_HOOK"
      }
    ]
  }
}
EOF
        echo "   ✅ Created $HOOKS_FILE"
    else
        echo "   ℹ️  Hooks file already exists: $HOOKS_FILE"
        echo "      Please manually add to hooks.json:"
        echo "      - beforeShellExecution: $BEFORE_SHELL_HOOK"
        echo "      - afterShellExecution: $AFTER_SHELL_HOOK"
        echo "      - beforeSubmitPrompt: $BEFORE_PROMPT_HOOK"
        echo "      - afterMCPExecution: $AFTER_TOOL_HOOK"
    fi
fi

# Install Cursor rule for Cursor platform
if [[ "$PLATFORM" == "cursor" ]]; then
    echo ""
    echo "🔗 Installing Cursor rule..."

    # Generate and install Cursor rule
    if [[ -f "$SKILL_DIR/SKILL.md" ]]; then
        if "$SCRIPT_DIR/generate-cursor-rule" "$SKILL_DIR/SKILL.md" --install 2>/dev/null; then
            echo "   ✅ Cursor rule installed to ~/.cursor/rules/omg-learn.mdc"
        else
            echo "   ⚠️  Could not auto-install Cursor rule. You can manually run:"
            echo "      $SCRIPT_DIR/generate-cursor-rule $SKILL_DIR/SKILL.md --install"
        fi
    else
        echo "   ⚠️  SKILL.md not found. Cursor rule not installed."
    fi
fi

echo ""

done  # End of platform installation loop

echo ""
echo "=========================================="
echo "✅ Installation complete for all platforms!"
echo "=========================================="
echo ""
echo "Installed for: ${PLATFORMS[@]}"
echo ""
echo "Next steps:"
echo "  1. Review your patterns files"
if [[ "$SCOPE" == "global" ]]; then
    [[ " ${PLATFORMS[@]} " =~ " claude " ]] && echo "     - Claude Code: ~/.claude/omg-learn-patterns.json"
    [[ " ${PLATFORMS[@]} " =~ " cursor " ]] && echo "     - Cursor: ~/.cursor/omg-learn-patterns.json"
else
    [[ " ${PLATFORMS[@]} " =~ " claude " ]] && echo "     - Claude Code: .claude/omg-learn-patterns.json"
    [[ " ${PLATFORMS[@]} " =~ " cursor " ]] && echo "     - Cursor: .cursor/omg-learn-patterns.json"
fi
echo "  2. Start using omg-learn - say 'omg!' when you spot a mistake"
echo "  3. Create patterns through the guided workflow"
echo ""
echo "To test the installation:"
echo "  - Try saying 'omg!' in a prompt (should trigger the example pattern)"
echo "  - Add custom patterns through the omg-learn skill workflow"
echo ""

if [[ " ${PLATFORMS[@]} " =~ " cursor " ]]; then
    echo "Cursor-specific notes:"
    echo "  - Skills are loaded via ~/.cursor/rules/omg-learn.mdc"
    echo "  - The rule points to the SKILL.md file in this directory"
    echo ""
fi
