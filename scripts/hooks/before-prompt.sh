#!/bin/bash
# before-prompt.sh - omg-learn Cursor Hook (beforeSubmitPrompt)
# Checks user prompts against configured patterns
# Cursor-compatible version

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(dirname "$SCRIPT_DIR")/lib"

# Read hook input from stdin
INPUT=$(cat)

# Extract prompt from Cursor's beforeSubmitPrompt format
PROMPT=$(python3 -c "
import json, sys
try:
    data = json.loads('''$INPUT''')
    # Cursor sends: {\"prompt\": \"user message...\"}
    print(data.get('prompt', ''))
except:
    print('')
")

# Load patterns from both global and project-local configs
GLOBAL_PATTERNS="$HOME/.cursor/omg-learn-patterns.json"
LOCAL_PATTERNS=".cursor/omg-learn-patterns.json"

# Merge patterns using Python (project-local overrides global for same ID)
MERGED_PATTERNS=$(python3 "$LIB_DIR/json_utils.py" merge "$GLOBAL_PATTERNS" "$LOCAL_PATTERNS" 2>/dev/null || echo '{"patterns": []}')

# Get array of patterns
PATTERNS=$(echo "$MERGED_PATTERNS" | python3 -c "import json, sys; print(json.dumps(json.load(sys.stdin).get('patterns', [])))")

# Function to generate JSON response using Python
json_response() {
    local allowed="$1"
    local message="$2"

    python3 -c "
import json
response = {'allowed': $allowed}
if '$message':
    response['message'] = '''$message'''
print(json.dumps(response))
"
}

# Check each pattern
echo "$PATTERNS" | python3 -c "
import json, sys
patterns = json.load(sys.stdin)
for pattern in patterns:
    print(json.dumps(pattern))
" | while IFS= read -r pattern; do
    # Extract pattern fields using Python
    PATTERN_DATA=$(python3 -c "
import json, sys
pattern = json.loads('''$pattern''')
print(json.dumps({
    'enabled': pattern.get('enabled', True),
    'hook': pattern.get('hook', ''),
    'pattern': pattern.get('pattern', ''),
    'action': pattern.get('action', 'warn'),
    'message': pattern.get('message', 'Pattern matched')
}))
")

    ENABLED=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print('true' if json.load(sys.stdin).get('enabled') else 'false')")
    PATTERN_HOOK=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('hook', ''))")
    PATTERN_REGEX=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('pattern', ''))")
    ACTION=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('action', 'warn'))")
    MESSAGE=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('message', 'Pattern matched'))")

    # Skip if pattern is disabled
    if [[ "$ENABLED" != "true" ]]; then
        continue
    fi

    # Check if this pattern applies to UserPromptSubmit or beforeSubmitPrompt
    # Accept both for compatibility
    if [[ "$PATTERN_HOOK" != "UserPromptSubmit" ]] && [[ "$PATTERN_HOOK" != "beforeSubmitPrompt" ]]; then
        continue
    fi

    # Check regex pattern
    if [[ -n "$PATTERN_REGEX" ]]; then
        # Check if prompt matches pattern (case-insensitive for omg!)
        if echo "$PROMPT" | grep -qiE "$PATTERN_REGEX"; then
            # Pattern matched! Take action
            case "$ACTION" in
                block)
                    json_response "false" "$MESSAGE"
                    exit 0
                    ;;
                ask)
                    # Cursor doesn't support ask well for prompts, treat as warning
                    json_response "true" "$MESSAGE"
                    exit 0
                    ;;
                warn)
                    json_response "true" "$MESSAGE"
                    exit 0
                    ;;
            esac
        fi
    fi
done

# No patterns matched, allow
json_response "true" ""
exit 0
