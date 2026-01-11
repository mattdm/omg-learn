#!/usr/bin/env python3
"""
Pattern manager for omg-learn.
Provides CRUD operations for pattern management.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import json_utils from same directory
try:
    # Try relative import first (when used as module)
    from .json_utils import (
        read_json_file,
        write_json_file,
        merge_patterns,
        find_pattern,
        add_pattern as json_add_pattern,
        update_pattern as json_update_pattern,
        delete_pattern as json_delete_pattern
    )
except ImportError:
    # Fall back to direct import (when run as script)
    import json_utils
    read_json_file = json_utils.read_json_file
    write_json_file = json_utils.write_json_file
    merge_patterns = json_utils.merge_patterns
    find_pattern = json_utils.find_pattern
    json_add_pattern = json_utils.add_pattern
    json_update_pattern = json_utils.update_pattern
    json_delete_pattern = json_utils.delete_pattern


class PatternManager:
    """Manages omg-learn patterns across global and project-local scopes."""

    def __init__(self, platform: str = 'claude'):
        """
        Initialize pattern manager.

        Args:
            platform: 'claude' or 'cursor'
        """
        self.platform = platform
        self.home = Path.home()

        # Determine pattern file paths based on platform
        if platform == 'claude':
            self.global_file = self.home / '.claude' / 'omg-learn-patterns.json'
            self.local_file = Path('.claude') / 'omg-learn-patterns.json'
        else:  # cursor
            self.global_file = self.home / '.cursor' / 'omg-learn-patterns.json'
            self.local_file = Path('.cursor') / 'omg-learn-patterns.json'

    def _detect_platform(self) -> str:
        """Auto-detect platform from directory structure."""
        if (Path('.claude').exists() or (self.home / '.claude').exists()):
            return 'claude'
        elif (Path('.cursor').exists() or (self.home / '.cursor').exists()):
            return 'cursor'
        else:
            return 'claude'  # default

    def list_patterns(
        self,
        scope: str = 'all',
        enabled_only: bool = False
    ) -> List[Dict]:
        """
        List all patterns with metadata.

        Args:
            scope: 'all', 'global', or 'local'
            enabled_only: Only return enabled patterns

        Returns:
            List of pattern dictionaries with added 'scope' field
        """
        patterns = []

        if scope in ('all', 'global'):
            global_patterns = read_json_file(str(self.global_file)).get('patterns', [])
            for p in global_patterns:
                p['_scope'] = 'global'
                p['_file'] = str(self.global_file)
                patterns.append(p)

        if scope in ('all', 'local'):
            local_patterns = read_json_file(str(self.local_file)).get('patterns', [])
            for p in local_patterns:
                p['_scope'] = 'local'
                p['_file'] = str(self.local_file)
                patterns.append(p)

        # If scope is 'all', merge and mark overrides
        if scope == 'all':
            # Build a map to track which patterns are in which scope
            pattern_scopes = {}
            for p in patterns:
                pid = p.get('id')
                if pid:
                    if pid not in pattern_scopes:
                        pattern_scopes[pid] = []
                    pattern_scopes[pid].append(p['_scope'])

            # Mark patterns that exist in both scopes
            for p in patterns:
                pid = p.get('id')
                if pid and len(pattern_scopes.get(pid, [])) > 1:
                    if p['_scope'] == 'local':
                        p['_overrides_global'] = True

            # Remove duplicates (local overrides global)
            seen_ids = set()
            unique_patterns = []
            # Process local first (they win)
            for p in [p for p in patterns if p['_scope'] == 'local']:
                pid = p.get('id')
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    unique_patterns.append(p)
            # Then global (skip if already seen)
            for p in [p for p in patterns if p['_scope'] == 'global']:
                pid = p.get('id')
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    unique_patterns.append(p)

            patterns = unique_patterns

        if enabled_only:
            patterns = [p for p in patterns if p.get('enabled', True)]

        return patterns

    def get_pattern(self, pattern_id: str) -> Optional[Tuple[Dict, str]]:
        """
        Get a pattern by ID.

        Args:
            pattern_id: Pattern ID to find

        Returns:
            Tuple of (pattern dict, scope) or None if not found
            Searches local first, then global
        """
        # Check local first
        local_patterns = read_json_file(str(self.local_file)).get('patterns', [])
        pattern = find_pattern(local_patterns, pattern_id)
        if pattern:
            pattern['_scope'] = 'local'
            pattern['_file'] = str(self.local_file)
            return (pattern, 'local')

        # Check global
        global_patterns = read_json_file(str(self.global_file)).get('patterns', [])
        pattern = find_pattern(global_patterns, pattern_id)
        if pattern:
            pattern['_scope'] = 'global'
            pattern['_file'] = str(self.global_file)
            return (pattern, 'global')

        return None

    def add_pattern(
        self,
        pattern: Dict,
        scope: str = 'global'
    ) -> bool:
        """
        Add a new pattern.

        Args:
            pattern: Pattern dictionary
            scope: 'global' or 'local'

        Returns:
            True if successful, False otherwise
        """
        file_path = str(self.global_file if scope == 'global' else self.local_file)
        return json_add_pattern(file_path, pattern, scope)

    def enable_pattern(
        self,
        pattern_id: str,
        scope: Optional[str] = None
    ) -> bool:
        """
        Enable a pattern.

        Args:
            pattern_id: Pattern ID to enable
            scope: 'global', 'local', or None (auto-detect)

        Returns:
            True if successful, False otherwise
        """
        if scope is None:
            # Auto-detect scope
            result = self.get_pattern(pattern_id)
            if not result:
                print(f"Pattern '{pattern_id}' not found", file=sys.stderr)
                return False
            _, scope = result

        file_path = str(self.global_file if scope == 'global' else self.local_file)
        return json_update_pattern(file_path, pattern_id, {'enabled': True})

    def disable_pattern(
        self,
        pattern_id: str,
        scope: Optional[str] = None
    ) -> bool:
        """
        Disable a pattern.

        Args:
            pattern_id: Pattern ID to disable
            scope: 'global', 'local', or None (auto-detect)

        Returns:
            True if successful, False otherwise
        """
        if scope is None:
            # Auto-detect scope
            result = self.get_pattern(pattern_id)
            if not result:
                print(f"Pattern '{pattern_id}' not found", file=sys.stderr)
                return False
            _, scope = result

        file_path = str(self.global_file if scope == 'global' else self.local_file)
        return json_update_pattern(file_path, pattern_id, {'enabled': False})

    def delete_pattern(
        self,
        pattern_id: str,
        scope: Optional[str] = None,
        confirm: bool = True
    ) -> bool:
        """
        Delete a pattern.

        Args:
            pattern_id: Pattern ID to delete
            scope: 'global', 'local', or None (auto-detect)
            confirm: Ask for confirmation before deleting

        Returns:
            True if successful, False otherwise
        """
        if scope is None:
            # Auto-detect scope
            result = self.get_pattern(pattern_id)
            if not result:
                print(f"Pattern '{pattern_id}' not found", file=sys.stderr)
                return False
            _, scope = result

        if confirm:
            response = input(f"Delete pattern '{pattern_id}' from {scope}? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled", file=sys.stderr)
                return False

        file_path = str(self.global_file if scope == 'global' else self.local_file)
        return json_delete_pattern(file_path, pattern_id)

    def update_pattern(
        self,
        pattern_id: str,
        updates: Dict,
        scope: Optional[str] = None
    ) -> bool:
        """
        Update an existing pattern.

        Args:
            pattern_id: Pattern ID to update
            updates: Dictionary of fields to update
            scope: 'global', 'local', or None (auto-detect)

        Returns:
            True if successful, False otherwise
        """
        if scope is None:
            # Auto-detect scope
            result = self.get_pattern(pattern_id)
            if not result:
                print(f"Pattern '{pattern_id}' not found", file=sys.stderr)
                return False
            _, scope = result

        file_path = str(self.global_file if scope == 'global' else self.local_file)
        return json_update_pattern(file_path, pattern_id, updates)


# CLI interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Pattern manager for omg-learn')
    parser.add_argument('--platform', choices=['claude', 'cursor'], default='claude',
                        help='Platform to use')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # list command
    list_parser = subparsers.add_parser('list', help='List patterns')
    list_parser.add_argument('--scope', choices=['all', 'global', 'local'], default='all',
                             help='Scope to list')
    list_parser.add_argument('--enabled', action='store_true',
                             help='Only show enabled patterns')

    # show command
    show_parser = subparsers.add_parser('show', help='Show pattern details')
    show_parser.add_argument('pattern_id', help='Pattern ID')

    # enable command
    enable_parser = subparsers.add_parser('enable', help='Enable a pattern')
    enable_parser.add_argument('pattern_id', help='Pattern ID')
    enable_parser.add_argument('--scope', choices=['global', 'local'],
                               help='Scope (auto-detected if not specified)')

    # disable command
    disable_parser = subparsers.add_parser('disable', help='Disable a pattern')
    disable_parser.add_argument('pattern_id', help='Pattern ID')
    disable_parser.add_argument('--scope', choices=['global', 'local'],
                                help='Scope (auto-detected if not specified)')

    # delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a pattern')
    delete_parser.add_argument('pattern_id', help='Pattern ID')
    delete_parser.add_argument('--scope', choices=['global', 'local'],
                               help='Scope (auto-detected if not specified)')
    delete_parser.add_argument('--yes', action='store_true',
                               help='Skip confirmation')

    args = parser.parse_args()

    pm = PatternManager(platform=args.platform)

    if args.command == 'list':
        patterns = pm.list_patterns(scope=args.scope, enabled_only=args.enabled)
        print(json.dumps(patterns, indent=2))

    elif args.command == 'show':
        result = pm.get_pattern(args.pattern_id)
        if result:
            pattern, scope = result
            print(json.dumps(pattern, indent=2))
        else:
            print(f"Pattern '{args.pattern_id}' not found", file=sys.stderr)
            sys.exit(1)

    elif args.command == 'enable':
        if pm.enable_pattern(args.pattern_id, args.scope):
            print(f"Enabled pattern: {args.pattern_id}")
        else:
            sys.exit(1)

    elif args.command == 'disable':
        if pm.disable_pattern(args.pattern_id, args.scope):
            print(f"Disabled pattern: {args.pattern_id}")
        else:
            sys.exit(1)

    elif args.command == 'delete':
        if pm.delete_pattern(args.pattern_id, args.scope, confirm=not args.yes):
            print(f"Deleted pattern: {args.pattern_id}")
        else:
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)
