#!/usr/bin/env python3
"""
omg-learn-prompt-checker.py - Claude Code UserPromptSubmit hook
Checks user prompts against configured patterns
"""

import json
import sys
import re
import os
from pathlib import Path

# Pattern file paths
GLOBAL_PATTERNS = os.path.expanduser("~/.claude/omg-learn-patterns.json")
LOCAL_PATTERNS = ".claude/omg-learn-patterns.json"

# Parse input from stdin
try:
    data = json.loads(sys.stdin.read())
    prompt = data.get('prompt', '')
except:
    # Parse error - allow with no output
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

            # For UserPromptSubmit hooks:
            # - Exit 0 with stdout = context added to Claude
            # - Exit 2 with stderr = block prompt, show error to user only
            if action == 'block':
                # Block the prompt and show error to user
                print(message, file=sys.stderr)
                sys.exit(2)
            else:
                # Add message as context for Claude (warn/ask)
                print(message)
                sys.exit(0)

# No patterns matched, allow (exit 0 with no output)
sys.exit(0)
