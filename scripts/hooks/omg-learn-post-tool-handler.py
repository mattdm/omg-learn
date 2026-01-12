#!/usr/bin/env python3
"""
omg-learn-post-tool-handler.py - Claude Code PostToolUse hook
Executes automation commands after tool usage (auto-format, lint, etc.)
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
    tool_input = data.get('tool_input', {})
    tool_output = data.get('tool_output', '')
except Exception as e:
    # If parsing fails, continue without action
    print(json.dumps({'decision': 'continue'}))
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

    # Skip if not PostToolUse
    if pattern.get('hook') != 'PostToolUse':
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
        # Skip if tool_output indicates error/failure
        if 'error' in str(tool_output).lower() or 'fail' in str(tool_output).lower():
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
            command = command_template.format(
                file_path=file_path,
                file_name=file_name,
                file_dir=file_dir,
                file_ext=file_ext
            )
        except KeyError as e:
            # Template variable not found, skip
            print(json.dumps({
                'decision': 'continue',
                'agent_message': f"⚠️ Command template error: {e}"
            }), file=sys.stderr)
            continue

        # Execute command with timeout
        timeout = pattern.get('timeout', 30)
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                text=True,
                cwd=file_dir if file_dir else None
            )

            # Determine what to show based on show_output flag
            if pattern.get('show_output', False):
                # Show command output to user
                output_msg = f"✓ {message}"
                if result.stdout:
                    output_msg += f"\n\n{result.stdout}"
                if result.stderr and result.returncode != 0:
                    output_msg += f"\n\nErrors:\n{result.stderr}"

                print(json.dumps({
                    'decision': 'continue',
                    'user_message': output_msg
                }))
            else:
                # Silent execution, only notify on error
                if result.returncode != 0 and result.stderr:
                    print(json.dumps({
                        'decision': 'continue',
                        'agent_message': f"⚠️ {message} (command failed)\n{result.stderr}"
                    }), file=sys.stderr)
                else:
                    # Success, no output
                    print(json.dumps({'decision': 'continue'}))

            sys.exit(0)

        except subprocess.TimeoutExpired:
            print(json.dumps({
                'decision': 'continue',
                'agent_message': f"⚠️ Command timeout ({timeout}s): {command}"
            }), file=sys.stderr)
            sys.exit(0)

        except Exception as e:
            print(json.dumps({
                'decision': 'continue',
                'agent_message': f"⚠️ Command execution failed: {e}"
            }), file=sys.stderr)
            sys.exit(0)

    elif action == 'notify':
        # Just show notification message
        print(json.dumps({
            'decision': 'continue',
            'user_message': f"ℹ️ {message}"
        }))
        sys.exit(0)

    elif action == 'warn':
        # Show warning message
        print(json.dumps({
            'decision': 'continue',
            'agent_message': f"⚠️ {message}"
        }))
        sys.exit(0)

# No patterns matched, continue normally
print(json.dumps({'decision': 'continue'}))
sys.exit(0)
