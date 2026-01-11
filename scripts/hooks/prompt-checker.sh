#!/bin/bash
# Optimized prompt-checker.sh - Single Python process for all operations

# Read hook input from stdin and pass via env var
export HOOK_INPUT=$(cat)

# Pattern file paths
GLOBAL_PATTERNS="$HOME/.claude/omg-learn-patterns.json"
LOCAL_PATTERNS=".claude/omg-learn-patterns.json"

# Single Python process handles everything
python3 <<PYTHON
import json
import sys
import re
import os
from pathlib import Path

# Parse input from environment variable
try:
    data = json.loads(os.environ['HOOK_INPUT'])
    prompt = data.get('prompt', '')
except:
    print(json.dumps({'permission': 'allow'}))
    sys.exit(0)

# Load and merge patterns
def load_patterns(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f).get('patterns', [])
    except:
        return []

global_patterns = load_patterns('$GLOBAL_PATTERNS')
local_patterns = load_patterns('$LOCAL_PATTERNS')

# Merge (local overrides global by ID)
patterns_by_id = {p['id']: p for p in global_patterns if 'id' in p}
patterns_by_id.update({p['id']: p for p in local_patterns if 'id' in p})
patterns = list(patterns_by_id.values())

# Check each pattern
for pattern in patterns:
    # Skip if disabled
    if not pattern.get('enabled', True):
        continue

    # Skip if not UserPromptSubmit
    if pattern.get('hook') != 'UserPromptSubmit':
        continue

    # Check regex pattern (case-insensitive for prompts)
    pattern_regex = pattern.get('pattern', '')
    if pattern_regex:
        if re.search(pattern_regex, prompt, re.IGNORECASE):
            # Pattern matched!
            action = pattern.get('action', 'warn')
            message = pattern.get('message', 'Pattern matched')

            if action == 'block':
                print(json.dumps({'permission': 'deny', 'user_message': message}))
            elif action == 'ask':
                print(json.dumps({'permission': 'ask', 'user_message': message}))
            else:
                print(json.dumps({'permission': 'allow', 'agent_message': message}))
            sys.exit(0)

# No patterns matched, allow
print(json.dumps({'permission': 'allow'}))
PYTHON
