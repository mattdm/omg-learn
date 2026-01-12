#!/usr/bin/env python3
"""
after-tool.py - omg-learn Cursor Hook (afterMCPExecution)
Executes automation commands after MCP tool execution (Write/Edit)
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
    # Cursor sends: {"tool_name": "...", "tool_input": {...}, "result_json": "...", "duration": 123}
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})
    result_json = data.get('result_json', '')
except Exception as e:
    # If parsing fails, continue without action (observation-only for Cursor)
    sys.exit(0)

# Extract file path from tool_input
file_path = tool_input.get('file_path') or tool_input.get('path') or ''

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

    # Skip if not PostToolUse or afterMCPExecution
    hook = pattern.get('hook', '')
    if hook not in ('PostToolUse', 'afterMCPExecution'):
        continue

    # Check matcher
    matcher = pattern.get('matcher', '')
    if matcher and matcher != '*':
        # Check if tool_name matches any part of matcher (e.g., "Write|Edit")
        if not any(m.strip() == tool_name for m in matcher.split('|')):
            continue

    # Check file_pattern if specified
    file_pattern_regex = pattern.get('file_pattern', '')
    if file_pattern_regex:
        if not file_path:
            continue  # No file path to match against
        if not re.search(file_pattern_regex, file_path):
            continue  # File pattern doesn't match

    # Check command_on_success flag
    if pattern.get('command_on_success', False):
        # Skip if result indicates error/failure
        if 'error' in str(result_json).lower() or 'fail' in str(result_json).lower():
            continue

    # Pattern matched! Execute action
    action = pattern.get('action', 'notify')
    message = pattern.get('message', 'Pattern matched')

    if action == 'run':
        # Execute command with template substitution
        command_template = pattern.get('command', '')
        if not command_template:
            continue

        # Prepare template variables
        file_name = os.path.basename(file_path) if file_path else ''
        file_dir = os.path.dirname(file_path) if file_path else ''
        file_ext = os.path.splitext(file_path)[1] if file_path else ''

        # Substitute variables in command template
        try:
            exec_command = command_template.format(
                file_path=file_path,
                file_name=file_name,
                file_dir=file_dir,
                file_ext=file_ext
            )
        except KeyError:
            # Template variable not found, skip
            continue

        # Execute command with timeout
        timeout = pattern.get('timeout', 30)
        try:
            result = subprocess.run(
                exec_command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                text=True,
                cwd=file_dir if file_dir else None
            )
            # Cursor's afterMCPExecution is observation-only
            # Just execute silently, no output expected
        except subprocess.TimeoutExpired:
            pass  # Silent timeout
        except Exception:
            pass  # Silent error

        # Exit after first match (observation-only)
        sys.exit(0)

# No patterns matched or no action needed
sys.exit(0)
