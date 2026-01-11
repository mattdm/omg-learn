#!/bin/bash
# prompt-checker.sh - omg-learn UserPromptSubmit Hook
# Checks user prompts against configured patterns

# Read hook input from stdin
INPUT=$(cat)

# Extract prompt text
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Load patterns from both global and project-local configs
GLOBAL_PATTERNS="$HOME/.claude/omg-learn-patterns.json"
LOCAL_PATTERNS=".claude/omg-learn-patterns.json"

# Merge patterns (project-local overrides global for same ID)
MERGED_PATTERNS='{"patterns":[]}'

if [[ -f "$GLOBAL_PATTERNS" ]]; then
    MERGED_PATTERNS=$(jq '.patterns' "$GLOBAL_PATTERNS" 2>/dev/null || echo '[]')
fi

if [[ -f "$LOCAL_PATTERNS" ]]; then
    LOCAL=$(jq '.patterns' "$LOCAL_PATTERNS" 2>/dev/null || echo '[]')
    # Merge: add local patterns, they override global by ID
    MERGED_PATTERNS=$(jq --argjson local "$LOCAL" '
        . as $global |
        $local + ($global | map(select(.id as $id | $local | map(.id) | index($id) | not)))
    ' <<< "$MERGED_PATTERNS")
fi

# Check each pattern
while IFS= read -r pattern; do
    # Skip if pattern is disabled
    ENABLED=$(echo "$pattern" | jq -r '.enabled // true')
    if [[ "$ENABLED" != "true" ]]; then
        continue
    fi

    # Check if this pattern applies to UserPromptSubmit
    PATTERN_HOOK=$(echo "$pattern" | jq -r '.hook // empty')

    if [[ "$PATTERN_HOOK" != "UserPromptSubmit" ]]; then
        continue
    fi

    # Get pattern details
    PATTERN_REGEX=$(echo "$pattern" | jq -r '.pattern // empty')
    ACTION=$(echo "$pattern" | jq -r '.action // "warn"')
    MESSAGE=$(echo "$pattern" | jq -r '.message // "Pattern matched"')

    # Check regex pattern
    if [[ -n "$PATTERN_REGEX" ]]; then
        # Check if prompt matches pattern
        if echo "$PROMPT" | grep -qE "$PATTERN_REGEX"; then
            # Pattern matched! Take action
            case "$ACTION" in
                block)
                    echo "{\"permission\": \"deny\", \"user_message\": \"$MESSAGE\"}"
                    exit 0
                    ;;
                ask)
                    echo "{\"permission\": \"ask\", \"user_message\": \"$MESSAGE\"}"
                    exit 0
                    ;;
                warn)
                    # For UserPromptSubmit, inject message into agent context
                    echo "{\"permission\": \"allow\", \"agent_message\": \"$MESSAGE\"}"
                    exit 0
                    ;;
            esac
        fi
    fi
done < <(echo "$MERGED_PATTERNS" | jq -c '.[]' 2>/dev/null || echo '[]')

# No patterns matched, allow
echo '{"permission": "allow"}'
exit 0
