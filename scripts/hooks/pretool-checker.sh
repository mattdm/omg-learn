#!/bin/bash
# pretool-checker.sh - omg-learn PreToolUse Hook
# Checks tool usage against configured patterns

# Read hook input from stdin
INPUT=$(cat)

# Extract tool information
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input.file_path // .tool_input.content // empty' 2>/dev/null)

# Debug logging (optional - uncomment for troubleshooting)
# echo "DEBUG: Tool: $TOOL_NAME, Input: $TOOL_INPUT" >> /tmp/omg-learn-hook.log

# Load patterns from both global and project-local configs
GLOBAL_PATTERNS="$HOME/.claude/omg-learn-patterns.json"
LOCAL_PATTERNS=".claude/omg-learn-patterns.json"

# Merge patterns (project-local overrides global for same ID)
MERGED_PATTERNS='[]'

if [[ -f "$GLOBAL_PATTERNS" ]]; then
    MERGED_PATTERNS=$(jq '.patterns' "$GLOBAL_PATTERNS" 2>/dev/null || echo '[]')
fi

if [[ -f "$LOCAL_PATTERNS" ]]; then
    LOCAL=$(jq '.patterns' "$LOCAL_PATTERNS" 2>/dev/null || echo '[]')
    # Merge: add local patterns, they override global by ID
    MERGED_PATTERNS=$(jq --argjson local "$LOCAL" --argjson global "$MERGED_PATTERNS" '
        $local + ($global | map(select(.id as $id | $local | map(.id) | index($id) | not)))
    ' <<< 'null')
fi

# Check each pattern
while IFS= read -r pattern; do
    # Skip if pattern is disabled
    ENABLED=$(echo "$pattern" | jq -r '.enabled // true')
    if [[ "$ENABLED" != "true" ]]; then
        continue
    fi

    # Check if this pattern applies to this hook and matcher
    PATTERN_HOOK=$(echo "$pattern" | jq -r '.hook // empty')
    PATTERN_MATCHER=$(echo "$pattern" | jq -r '.matcher // empty')

    # Skip if not a PreToolUse pattern
    if [[ "$PATTERN_HOOK" != "PreToolUse" ]]; then
        continue
    fi

    # Skip if matcher doesn't match tool name
    if [[ -n "$PATTERN_MATCHER" ]] && ! echo "$TOOL_NAME" | grep -qE "$PATTERN_MATCHER"; then
        continue
    fi

    # Get pattern details
    PATTERN_REGEX=$(echo "$pattern" | jq -r '.pattern // empty')
    EXCLUDE_PATTERN=$(echo "$pattern" | jq -r '.exclude_pattern // empty')
    ACTION=$(echo "$pattern" | jq -r '.action // "warn"')
    MESSAGE=$(echo "$pattern" | jq -r '.message // "Pattern matched"')
    CHECK_SCRIPT=$(echo "$pattern" | jq -r '.check_script // empty')

    # Run custom check script if specified
    if [[ -n "$CHECK_SCRIPT" ]] && [[ -f "$CHECK_SCRIPT" ]]; then
        if ! "$CHECK_SCRIPT" "$TOOL_INPUT" 2>/dev/null; then
            # Custom script returned non-zero, pattern matched
            case "$ACTION" in
                block)
                    jq -n --arg msg "$MESSAGE" '{"permission": "deny", "user_message": $msg}'
                    exit 0
                    ;;
                ask)
                    jq -n --arg msg "$MESSAGE" '{"permission": "ask", "user_message": $msg}'
                    exit 0
                    ;;
                warn)
                    jq -n --arg msg "⚠️ Warning: $MESSAGE" '{"permission": "allow", "agent_message": $msg}'
                    exit 0
                    ;;
            esac
        fi
        continue
    fi

    # Check regex pattern
    if [[ -n "$PATTERN_REGEX" ]]; then
        # Check if tool input matches pattern
        if echo "$TOOL_INPUT" | grep -qE "$PATTERN_REGEX"; then
            # If there's an exclude pattern, check it
            if [[ -n "$EXCLUDE_PATTERN" ]]; then
                if echo "$TOOL_INPUT" | grep -qE "$EXCLUDE_PATTERN"; then
                    # Exclude pattern matched, skip this pattern
                    continue
                fi
            fi

            # Pattern matched! Take action
            case "$ACTION" in
                block)
                    jq -n --arg msg "$MESSAGE" '{"permission": "deny", "user_message": $msg}'
                    exit 0
                    ;;
                ask)
                    jq -n --arg msg "$MESSAGE" '{"permission": "ask", "user_message": $msg}'
                    exit 0
                    ;;
                warn)
                    jq -n --arg msg "⚠️ Warning: $MESSAGE" '{"permission": "allow", "agent_message": $msg}'
                    exit 0
                    ;;
            esac
        fi
    fi
done < <(echo "$MERGED_PATTERNS" | jq -c '.[]' 2>/dev/null || echo '[]')

# No patterns matched, allow
echo '{"permission": "allow"}'
exit 0
