#!/usr/bin/env python3
"""
before-shell.py - omg-learn Cursor Hook (beforeShellExecution)
Checks shell commands against configured patterns
"""

import json
import sys
import re
import subprocess
import os
from pathlib import Path

# Pattern file paths for Cursor
GLOBAL_PATTERNS = os.path.expanduser("~/.cursor/omg-learn-patterns.json")
LOCAL_PATTERNS = ".cursor/omg-learn-patterns.json"

# Parse input from stdin
try:
    data = json.loads(sys.stdin.read())
    # Cursor sends: {"command": "git commit ..."}
    command = data.get('command', '')
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

    # Skip if not PreToolUse or beforeShellExecution
    # Accept both for compatibility
    hook_type = pattern.get('hook', '')
    if hook_type not in ('PreToolUse', 'beforeShellExecution'):
        continue

    # Check matcher (if specified, must be Bash or *)
    matcher = pattern.get('matcher', '')
    if matcher and matcher not in ('*', 'Bash'):
        continue

    # Run check script if present
    check_script = pattern.get('check_script', '')
    if check_script and os.path.isfile(check_script):
        try:
            result = subprocess.run(
                [check_script, command],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                # Pattern matched
                action = pattern.get('action', 'warn')
                message = pattern.get('message', 'Pattern matched')

                if action == 'block':
                    print(json.dumps({'allowed': False, 'message': message}))
                else:
                    # Cursor doesn't support 'ask' well, treat as warning
                    print(json.dumps({'allowed': True, 'message': f'⚠️ Warning: {message}'}))
                sys.exit(0)
        except:
            pass
        continue

    # Check regex pattern
    pattern_regex = pattern.get('pattern', '')
    if pattern_regex:
        if re.search(pattern_regex, command):
            # Check exclude pattern
            exclude = pattern.get('exclude_pattern', '')
            if exclude and re.search(exclude, command):
                continue

            # Pattern matched!
            action = pattern.get('action', 'warn')
            message = pattern.get('message', 'Pattern matched')

            if action == 'block':
                print(json.dumps({'allowed': False, 'message': message}))
            else:
                # Cursor doesn't support 'ask' well, treat as warning
                print(json.dumps({'allowed': True, 'message': f'⚠️ Warning: {message}'}))
            sys.exit(0)

# No patterns matched, allow
print(json.dumps({'allowed': True}))
