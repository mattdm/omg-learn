#!/bin/bash
set -e

# omg-learn Hook Installation Script
# Installs platform hooks for pattern-based mistake prevention

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 omg-learn Hook Installer"
echo "============================"
echo ""

# Detect platform
detect_platform() {
    if [[ -d ".claude" ]] || [[ -d "$HOME/.claude" ]]; then
        echo "claude"
    elif [[ -d ".cursor" ]] || [[ -d "$HOME/.cursor" ]]; then
        echo "cursor"
    else
        echo "unknown"
    fi
}

PLATFORM=$(detect_platform)

if [[ "$PLATFORM" == "unknown" ]]; then
    echo "❌ Could not detect Claude Code or Cursor installation"
    echo "   Please ensure you're running this from a project directory"
    echo "   with .claude/ or .cursor/ subdirectory, or have"
    echo "   ~/.claude/ or ~/.cursor/ in your home directory."
    exit 1
fi

echo "✅ Detected platform: $PLATFORM"
echo ""

# Ask for installation scope
echo "Choose installation scope:"
echo "  1) Global (all projects)"
echo "  2) Project-local (current project only)"
read -p "Enter choice [1-2]: " SCOPE_CHOICE

case $SCOPE_CHOICE in
    1)
        HOOKS_DIR="$HOME/.$PLATFORM/hooks"
        PATTERNS_FILE="$HOME/.$PLATFORM/omg-learn-patterns.json"
        SCOPE="global"
        ;;
    2)
        if [[ ! -d ".$PLATFORM" ]]; then
            mkdir -p ".$PLATFORM"
        fi
        HOOKS_DIR=".$PLATFORM/hooks"
        PATTERNS_FILE=".$PLATFORM/omg-learn-patterns.json"
        SCOPE="project-local"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Installing hooks to: $HOOKS_DIR"
echo "Patterns file: $PATTERNS_FILE"
echo ""

# Create hooks directory
mkdir -p "$HOOKS_DIR"

# Install hook scripts based on platform
if [[ "$PLATFORM" == "claude" ]]; then
    echo "📝 Installing Claude Code hooks..."
    cp "$SCRIPT_DIR/hooks/pretool-checker.sh" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/pretool-checker.sh"
    cp "$SCRIPT_DIR/hooks/prompt-checker.sh" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/prompt-checker.sh"
    echo "   ✅ pretool-checker.sh"
    echo "   ✅ prompt-checker.sh"
elif [[ "$PLATFORM" == "cursor" ]]; then
    echo "📝 Installing Cursor hooks..."
    cp "$SCRIPT_DIR/hooks/before-shell.sh" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/before-shell.sh"
    cp "$SCRIPT_DIR/hooks/before-prompt.sh" "$HOOKS_DIR/"
    chmod +x "$HOOKS_DIR/before-prompt.sh"
    echo "   ✅ before-shell.sh"
    echo "   ✅ before-prompt.sh"
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
      "id": "omg-detection-example",
      "description": "Example pattern: Detects 'omg!' in user prompts as a teaching example",
      "hook": "UserPromptSubmit",
      "pattern": "[Oo][Mm][Gg]!",
      "action": "warn",
      "message": "💡 Detected 'omg!' - This is an example pattern. You can add more patterns through omg-learn.",
      "enabled": true,
      "note": "This is just an example to demonstrate the pattern system. Delete or disable if not needed."
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
                    "command": "'"$HOOKS_DIR/pretool-checker.sh"'"
                  }
                ]
              }
            ],
            "UserPromptSubmit": [
              {
                "hooks": [
                  {
                    "type": "command",
                    "command": "'"$HOOKS_DIR/prompt-checker.sh"'"
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
        SHELL_HOOK_PATH="$HOOKS_DIR/before-shell.sh"
        PROMPT_HOOK_PATH="$HOOKS_DIR/before-prompt.sh"
    else
        # Project-local: use relative paths (relative to hooks.json location)
        # hooks.json is in .cursor/, so path is ./hooks/script.sh
        SHELL_HOOK_PATH="./hooks/before-shell.sh"
        PROMPT_HOOK_PATH="./hooks/before-prompt.sh"
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
        "command": "$SHELL_HOOK_PATH"
      }
    ],
    "beforeSubmitPrompt": [
      {
        "command": "$PROMPT_HOOK_PATH"
      }
    ]
  }
}
EOF
        echo "   ✅ Created $HOOKS_FILE"
    else
        echo "   ℹ️  Hooks file already exists: $HOOKS_FILE"
        echo "      Please manually add to hooks.json:"
        echo "      - beforeShellExecution: $SHELL_HOOK_PATH"
        echo "      - beforeSubmitPrompt: $PROMPT_HOOK_PATH"
    fi
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Review the patterns file: $PATTERNS_FILE"
echo "  2. Start using omg-learn - say 'omg!' when you spot a mistake"
echo "  3. Create patterns through the guided workflow"
echo ""
echo "To test the installation:"
echo "  - Try saying 'omg!' in a prompt (should trigger the example pattern)"
echo "  - Add custom patterns through the omg-learn skill workflow"
echo ""
