#!/usr/bin/env python3
"""
omg-learn-tool-checker.py - Claude Code PreToolUse hook
Checks tool usage against configured patterns
"""

import json
import sys
import re
import subprocess
import os
from pathlib import Path

# Pattern file paths
GLOBAL_PATTERNS = os.path.expanduser("~/.claude/omg-learn-patterns.json")
LOCAL_PATTERNS = ".claude/omg-learn-patterns.json"

# Parse input from stdin
try:
    data = json.loads(sys.stdin.read())
    tool_name = data.get('tool_name', '')
    tool_input_obj = data.get('tool_input', {})
    tool_input = (
        tool_input_obj.get('command') or
        tool_input_obj.get('file_path') or
        tool_input_obj.get('content') or
        ''
    )
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

    # Skip if not PreToolUse
    if pattern.get('hook') != 'PreToolUse':
        continue

    # Check matcher
    matcher = pattern.get('matcher', '')
    if matcher and matcher != '*' and matcher != tool_name:
        continue

    # Run check script if present
    check_script = pattern.get('check_script', '')
    if check_script:
        try:
            result = subprocess.run(
                [check_script, tool_input],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                # Pattern matched
                action = pattern.get('action', 'warn')
                message = pattern.get('message', 'Pattern matched')

                if action == 'block':
                    print(json.dumps({'permission': 'deny', 'user_message': message}))
                elif action == 'ask':
                    print(json.dumps({'permission': 'ask', 'user_message': message}))
                else:
                    print(json.dumps({'permission': 'allow', 'agent_message': f'⚠️ Warning: {message}'}))
                sys.exit(0)
        except:
            pass
        continue

    # Check regex pattern
    pattern_regex = pattern.get('pattern', '')
    if pattern_regex:
        if re.search(pattern_regex, tool_input):
            # Check exclude pattern
            exclude = pattern.get('exclude_pattern', '')
            if exclude and re.search(exclude, tool_input):
                continue

            # Pattern matched!
            action = pattern.get('action', 'warn')
            message = pattern.get('message', 'Pattern matched')

            if action == 'block':
                print(json.dumps({'permission': 'deny', 'user_message': message}))
            elif action == 'ask':
                print(json.dumps({'permission': 'ask', 'user_message': message}))
            else:
                print(json.dumps({'permission': 'allow', 'agent_message': f'⚠️ Warning: {message}'}))
            sys.exit(0)

# No patterns matched, allow
print(json.dumps({'permission': 'allow'}))
