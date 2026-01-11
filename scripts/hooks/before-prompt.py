#!/usr/bin/env python3
"""
before-prompt.py - omg-learn Cursor Hook (beforeSubmitPrompt)
Checks user prompts against configured patterns
"""

import json
import sys
import re
import os
from pathlib import Path

# Pattern file paths for Cursor
GLOBAL_PATTERNS = os.path.expanduser("~/.cursor/omg-learn-patterns.json")
LOCAL_PATTERNS = ".cursor/omg-learn-patterns.json"

# Parse input from stdin
try:
    data = json.loads(sys.stdin.read())
    # Cursor sends: {"prompt": "user message..."}
    prompt = data.get('prompt', '')
except:
    print(json.dumps({'allowed': True}))
    sys.exit(0)

# Load and merge patterns
def load_patterns(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f).get('patterns', [])
    except:
        return []

global_patterns = load_patterns(GLOBAL_PATTERNS)
local_patterns = load_patterns(LOCAL_PATTERNS)

# Merge (local overrides global by ID)
patterns_by_id = {p['id']: p for p in global_patterns if 'id' in p}
patterns_by_id.update({p['id']: p for p in local_patterns if 'id' in p})
patterns = list(patterns_by_id.values())

# Check each pattern
for pattern in patterns:
    # Skip if disabled
    if not pattern.get('enabled', True):
        continue

    # Check if this pattern applies to UserPromptSubmit or beforeSubmitPrompt
    # Accept both for compatibility
    hook_type = pattern.get('hook', '')
    if hook_type not in ('UserPromptSubmit', 'beforeSubmitPrompt'):
        continue

    # Check regex pattern (case-insensitive for prompts)
    pattern_regex = pattern.get('pattern', '')
    if pattern_regex:
        if re.search(pattern_regex, prompt, re.IGNORECASE):
            # Pattern matched!
            action = pattern.get('action', 'warn')
            message = pattern.get('message', 'Pattern matched')

            if action == 'block':
                print(json.dumps({'allowed': False, 'message': message}))
            else:
                # Cursor doesn't support 'ask' well for prompts, treat as warning
                print(json.dumps({'allowed': True, 'message': message}))
            sys.exit(0)

# No patterns matched, allow
print(json.dumps({'allowed': True}))
