#!/bin/bash
# before-shell.sh - omg-learn Cursor Hook (beforeShellExecution)
# Checks shell commands against configured patterns
# Cursor-compatible version (uses beforeShellExecution event)

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$(dirname "$SCRIPT_DIR")/lib"

# Read hook input from stdin
INPUT=$(cat)

# Extract command from Cursor's beforeShellExecution format
COMMAND=$(python3 -c "
import json, sys
try:
    data = json.loads('''$INPUT''')
    # Cursor sends: {\"command\": \"git commit ...\"}
    print(data.get('command', ''))
except:
    print('')
")

# Debug logging (optional - uncomment for troubleshooting)
# echo "DEBUG: Command: $COMMAND" >> /tmp/omg-learn-hook.log

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
    'matcher': pattern.get('matcher', ''),
    'pattern': pattern.get('pattern', ''),
    'exclude_pattern': pattern.get('exclude_pattern', ''),
    'action': pattern.get('action', 'warn'),
    'message': pattern.get('message', 'Pattern matched'),
    'check_script': pattern.get('check_script', '')
}))
")

    ENABLED=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print('true' if json.load(sys.stdin).get('enabled') else 'false')")
    PATTERN_HOOK=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('hook', ''))")
    PATTERN_MATCHER=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('matcher', ''))")
    PATTERN_REGEX=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('pattern', ''))")
    EXCLUDE_PATTERN=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('exclude_pattern', ''))")
    ACTION=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('action', 'warn'))")
    MESSAGE=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('message', 'Pattern matched'))")
    CHECK_SCRIPT=$(echo "$PATTERN_DATA" | python3 -c "import json, sys; print(json.load(sys.stdin).get('check_script', ''))")

    # Skip if pattern is disabled
    if [[ "$ENABLED" != "true" ]]; then
        continue
    fi

    # Skip if not a PreToolUse pattern (or beforeShellExecution)
    # Accept both for compatibility
    if [[ "$PATTERN_HOOK" != "PreToolUse" ]] && [[ "$PATTERN_HOOK" != "beforeShellExecution" ]]; then
        continue
    fi

    # Skip if matcher doesn't match (Bash for shell commands)
    if [[ -n "$PATTERN_MATCHER" ]] && [[ "$PATTERN_MATCHER" != "*" ]] && [[ "$PATTERN_MATCHER" != "Bash" ]]; then
        continue
    fi

    # Run custom check script if specified
    if [[ -n "$CHECK_SCRIPT" ]] && [[ -f "$CHECK_SCRIPT" ]]; then
        if ! "$CHECK_SCRIPT" "$COMMAND" 2>/dev/null; then
            # Custom script returned non-zero, pattern matched
            case "$ACTION" in
                block)
                    json_response "false" "$MESSAGE"
                    exit 0
                    ;;
                ask)
                    # Cursor doesn't support ask, treat as warning
                    json_response "true" "⚠️ Warning: $MESSAGE"
                    exit 0
                    ;;
                warn)
                    json_response "true" "⚠️ Warning: $MESSAGE"
                    exit 0
                    ;;
            esac
        fi
        continue
    fi

    # Check regex pattern
    if [[ -n "$PATTERN_REGEX" ]]; then
        # Check if command matches pattern
        if echo "$COMMAND" | grep -qE "$PATTERN_REGEX"; then
            # If there's an exclude pattern, check it
            if [[ -n "$EXCLUDE_PATTERN" ]]; then
                if echo "$COMMAND" | grep -qE "$EXCLUDE_PATTERN"; then
                    # Exclude pattern matched, skip this pattern
                    continue
                fi
            fi

            # Pattern matched! Take action
            case "$ACTION" in
                block)
                    json_response "false" "$MESSAGE"
                    exit 0
                    ;;
                ask)
                    # Cursor doesn't support ask, treat as warning
                    json_response "true" "⚠️ Warning: $MESSAGE"
                    exit 0
                    ;;
                warn)
                    json_response "true" "⚠️ Warning: $MESSAGE"
                    exit 0
                    ;;
            esac
        fi
    fi
done

# No patterns matched, allow
json_response "true" ""
exit 0
