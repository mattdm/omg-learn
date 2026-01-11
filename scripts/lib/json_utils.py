#!/usr/bin/env python3
"""
JSON utility functions for omg-learn pattern management.
Replaces jq dependency with pure Python JSON operations.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data as dict, or empty dict if file doesn't exist
    """
    path = Path(file_path).expanduser()

    if not path.exists():
        return {}

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {file_path}: {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return {}


def write_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Write data to JSON file atomically (write to temp, then rename).

    Args:
        file_path: Path to JSON file
        data: Data to write
        indent: Indentation for pretty printing

    Returns:
        True if successful, False otherwise
    """
    path = Path(file_path).expanduser()

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file first (atomic write)
    temp_path = path.with_suffix('.tmp')

    try:
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=indent)
            f.write('\n')  # Add trailing newline

        # Atomic rename
        temp_path.replace(path)
        return True

    except Exception as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
        return False


def merge_patterns(global_file: str, local_file: str) -> List[Dict[str, Any]]:
    """
    Merge global and local pattern files.
    Local patterns override global patterns by ID.

    Args:
        global_file: Path to global patterns file
        local_file: Path to local patterns file

    Returns:
        Merged list of patterns
    """
    global_data = read_json_file(global_file)
    local_data = read_json_file(local_file)

    # Extract pattern arrays
    global_patterns = global_data.get('patterns', [])
    local_patterns = local_data.get('patterns', [])

    # Build pattern dict by ID (local overrides global)
    patterns_by_id = {}

    for pattern in global_patterns:
        pattern_id = pattern.get('id')
        if pattern_id:
            patterns_by_id[pattern_id] = pattern

    for pattern in local_patterns:
        pattern_id = pattern.get('id')
        if pattern_id:
            # Local overrides global
            patterns_by_id[pattern_id] = pattern

    # Return as list
    return list(patterns_by_id.values())


def get_patterns(
    patterns: List[Dict[str, Any]],
    hook_type: Optional[str] = None,
    matcher: Optional[str] = None,
    enabled_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Filter patterns by hook type, matcher, and enabled status.

    Args:
        patterns: List of pattern dicts
        hook_type: Filter by hook type (PreToolUse, UserPromptSubmit, etc.)
        matcher: Filter by matcher (Bash, Write, Edit, *)
        enabled_only: Only return enabled patterns

    Returns:
        Filtered list of patterns
    """
    filtered = patterns

    if enabled_only:
        filtered = [p for p in filtered if p.get('enabled', False)]

    if hook_type:
        filtered = [p for p in filtered if p.get('hook') == hook_type]

    if matcher:
        filtered = [
            p for p in filtered
            if p.get('matcher') == matcher or p.get('matcher') == '*'
        ]

    return filtered


def add_pattern(file_path: str, pattern: Dict[str, Any], scope: str = 'global') -> bool:
    """
    Add a new pattern to the pattern file.

    Args:
        file_path: Path to pattern file
        pattern: Pattern dict to add
        scope: Scope identifier (for version metadata)

    Returns:
        True if successful, False otherwise
    """
    data = read_json_file(file_path)

    # Initialize structure if needed
    if 'version' not in data:
        data['version'] = '1.0'
    if 'patterns' not in data:
        data['patterns'] = []

    # Check if pattern with same ID already exists
    pattern_id = pattern.get('id')
    if pattern_id:
        existing_ids = [p.get('id') for p in data['patterns']]
        if pattern_id in existing_ids:
            print(f"Pattern with ID '{pattern_id}' already exists", file=sys.stderr)
            return False

    # Add pattern
    data['patterns'].append(pattern)

    return write_json_file(file_path, data)


def update_pattern(file_path: str, pattern_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update an existing pattern.

    Args:
        file_path: Path to pattern file
        pattern_id: ID of pattern to update
        updates: Dict of fields to update

    Returns:
        True if successful, False if pattern not found
    """
    data = read_json_file(file_path)

    patterns = data.get('patterns', [])

    # Find and update pattern
    found = False
    for pattern in patterns:
        if pattern.get('id') == pattern_id:
            pattern.update(updates)
            found = True
            break

    if not found:
        print(f"Pattern '{pattern_id}' not found in {file_path}", file=sys.stderr)
        return False

    return write_json_file(file_path, data)


def delete_pattern(file_path: str, pattern_id: str) -> bool:
    """
    Delete a pattern from the pattern file.

    Args:
        file_path: Path to pattern file
        pattern_id: ID of pattern to delete

    Returns:
        True if successful, False if pattern not found
    """
    data = read_json_file(file_path)

    patterns = data.get('patterns', [])
    original_count = len(patterns)

    # Filter out pattern with matching ID
    data['patterns'] = [p for p in patterns if p.get('id') != pattern_id]

    if len(data['patterns']) == original_count:
        print(f"Pattern '{pattern_id}' not found in {file_path}", file=sys.stderr)
        return False

    return write_json_file(file_path, data)


def find_pattern(patterns: List[Dict[str, Any]], pattern_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a pattern by ID.

    Args:
        patterns: List of pattern dicts
        pattern_id: ID to search for

    Returns:
        Pattern dict if found, None otherwise
    """
    for pattern in patterns:
        if pattern.get('id') == pattern_id:
            return pattern
    return None


# CLI interface for direct usage from shell scripts
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='JSON utilities for omg-learn')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # merge command
    merge_parser = subparsers.add_parser('merge', help='Merge global and local patterns')
    merge_parser.add_argument('global_file', help='Global patterns file')
    merge_parser.add_argument('local_file', help='Local patterns file')

    # filter command
    filter_parser = subparsers.add_parser('filter', help='Filter patterns')
    filter_parser.add_argument('--global-file', required=True, help='Global patterns file')
    filter_parser.add_argument('--local-file', required=True, help='Local patterns file')
    filter_parser.add_argument('--hook', help='Filter by hook type')
    filter_parser.add_argument('--matcher', help='Filter by matcher')
    filter_parser.add_argument('--all', action='store_true', help='Include disabled patterns')

    # read command
    read_parser = subparsers.add_parser('read', help='Read JSON file')
    read_parser.add_argument('file', help='File to read')
    read_parser.add_argument('--key', help='Extract specific key')

    args = parser.parse_args()

    if args.command == 'merge':
        patterns = merge_patterns(args.global_file, args.local_file)
        print(json.dumps({'patterns': patterns}, indent=2))

    elif args.command == 'filter':
        patterns = merge_patterns(args.global_file, args.local_file)
        filtered = get_patterns(
            patterns,
            hook_type=args.hook,
            matcher=args.matcher,
            enabled_only=not args.all
        )
        print(json.dumps({'patterns': filtered}, indent=2))

    elif args.command == 'read':
        data = read_json_file(args.file)
        if args.key:
            # Extract specific key using dot notation (e.g., "patterns.0.id")
            keys = args.key.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)]
                else:
                    value = None
                    break
            print(json.dumps(value))
        else:
            print(json.dumps(data, indent=2))

    else:
        parser.print_help()
        sys.exit(1)
