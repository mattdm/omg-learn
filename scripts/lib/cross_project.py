#!/usr/bin/env python3
"""
Cross-project pattern management for omg-learn.
Enables syncing, exporting, and importing patterns.
"""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import from same directory
try:
    from .pattern_manager import PatternManager
    from .json_utils import read_json_file, write_json_file
except ImportError:
    import pattern_manager
    import json_utils
    PatternManager = pattern_manager.PatternManager
    read_json_file = json_utils.read_json_file
    write_json_file = json_utils.write_json_file


class CrossProjectManager:
    """Manages cross-project pattern operations."""

    def __init__(self, platform: str = 'claude'):
        """
        Initialize cross-project manager.

        Args:
            platform: 'claude' or 'cursor'
        """
        self.pm = PatternManager(platform=platform)
        self.platform = platform

    def get_sync_status(self) -> Dict[str, List[str]]:
        """
        Get sync status between global and local patterns.

        Returns:
            Dictionary with:
            - only_global: Pattern IDs only in global
            - only_local: Pattern IDs only in local
            - different: Pattern IDs that differ between global and local
            - same: Pattern IDs that are identical
        """
        global_patterns = self.pm.list_patterns(scope='global')
        local_patterns = self.pm.list_patterns(scope='local')

        global_ids = {p.get('id') for p in global_patterns if p.get('id')}
        local_ids = {p.get('id') for p in local_patterns if p.get('id')}

        # Build pattern maps
        global_map = {p.get('id'): p for p in global_patterns if p.get('id')}
        local_map = {p.get('id'): p for p in local_patterns if p.get('id')}

        only_global = list(global_ids - local_ids)
        only_local = list(local_ids - global_ids)

        # Check for differences in patterns that exist in both
        different = []
        same = []
        for pid in global_ids & local_ids:
            g_pattern = {k: v for k, v in global_map[pid].items() if not k.startswith('_')}
            l_pattern = {k: v for k, v in local_map[pid].items() if not k.startswith('_')}

            if g_pattern != l_pattern:
                different.append(pid)
            else:
                same.append(pid)

        return {
            'only_global': sorted(only_global),
            'only_local': sorted(only_local),
            'different': sorted(different),
            'same': sorted(same)
        }

    def push_to_global(
        self,
        pattern_ids: Optional[List[str]] = None,
        merge_strategy: str = 'ask'
    ) -> Dict[str, Any]:
        """
        Push patterns from local to global.

        Args:
            pattern_ids: List of pattern IDs to push, or None for all local patterns
            merge_strategy: 'overwrite', 'skip', or 'ask'

        Returns:
            Dictionary with results
        """
        if pattern_ids is None:
            # Get all local patterns
            local_patterns = self.pm.list_patterns(scope='local')
            pattern_ids = [p.get('id') for p in local_patterns if p.get('id')]

        results = {
            'pushed': [],
            'skipped': [],
            'failed': []
        }

        for pid in pattern_ids:
            result = self.pm.get_pattern(pid)
            if not result:
                results['failed'].append((pid, 'Pattern not found'))
                continue

            pattern, scope = result

            if scope != 'local':
                results['skipped'].append((pid, 'Not a local pattern'))
                continue

            # Check if pattern exists in global
            global_result = self.pm.get_pattern(pid)
            exists_in_global = global_result is not None and global_result[1] == 'global'

            if exists_in_global and merge_strategy == 'skip':
                results['skipped'].append((pid, 'Already exists in global'))
                continue

            if exists_in_global and merge_strategy == 'ask':
                response = input(f"Pattern '{pid}' exists in global. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    results['skipped'].append((pid, 'User declined to overwrite'))
                    continue

            # Remove metadata fields
            clean_pattern = {k: v for k, v in pattern.items() if not k.startswith('_')}

            # Add to global
            if self.pm.add_pattern(clean_pattern, scope='global'):
                results['pushed'].append(pid)
            else:
                results['failed'].append((pid, 'Failed to add to global'))

        return results

    def pull_from_global(
        self,
        pattern_ids: Optional[List[str]] = None,
        override: bool = False
    ) -> Dict[str, Any]:
        """
        Pull patterns from global to local.

        Args:
            pattern_ids: List of pattern IDs to pull, or None for all global patterns
            override: If True, override existing local patterns without asking

        Returns:
            Dictionary with results
        """
        if pattern_ids is None:
            # Get all global patterns
            global_patterns = self.pm.list_patterns(scope='global')
            pattern_ids = [p.get('id') for p in global_patterns if p.get('id')]

        results = {
            'pulled': [],
            'skipped': [],
            'failed': []
        }

        for pid in pattern_ids:
            result = self.pm.get_pattern(pid)
            if not result:
                results['failed'].append((pid, 'Pattern not found'))
                continue

            pattern, scope = result

            # Get from global specifically
            global_data = read_json_file(str(self.pm.global_file))
            global_patterns = global_data.get('patterns', [])
            global_pattern = next((p for p in global_patterns if p.get('id') == pid), None)

            if not global_pattern:
                results['skipped'].append((pid, 'Not a global pattern'))
                continue

            # Check if pattern exists in local
            local_data = read_json_file(str(self.pm.local_file))
            local_patterns = local_data.get('patterns', [])
            exists_in_local = any(p.get('id') == pid for p in local_patterns)

            if exists_in_local and not override:
                response = input(f"Pattern '{pid}' exists in local. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    results['skipped'].append((pid, 'User declined to overwrite'))
                    continue

            # Add to local
            if self.pm.add_pattern(global_pattern, scope='local'):
                results['pulled'].append(pid)
            else:
                results['failed'].append((pid, 'Failed to add to local'))

        return results

    def export_patterns(
        self,
        pattern_ids: List[str],
        output_file: str,
        include_scripts: bool = True
    ) -> bool:
        """
        Export patterns to a file (JSON or ZIP).

        Args:
            pattern_ids: List of pattern IDs to export
            output_file: Output file path (.json or .zip)
            include_scripts: Include check scripts in export (ZIP only)

        Returns:
            True if successful, False otherwise
        """
        output_path = Path(output_file)

        # Collect patterns
        patterns_to_export = []
        scripts_to_include = set()

        for pid in pattern_ids:
            result = self.pm.get_pattern(pid)
            if not result:
                print(f"Warning: Pattern '{pid}' not found, skipping")
                continue

            pattern, scope = result

            # Remove metadata fields
            clean_pattern = {k: v for k, v in pattern.items() if not k.startswith('_')}
            patterns_to_export.append(clean_pattern)

            # Track scripts
            check_script = pattern.get('check_script')
            if check_script and include_scripts:
                scripts_to_include.add(check_script)

        if not patterns_to_export:
            print("No patterns to export")
            return False

        # Determine format based on extension
        if output_path.suffix == '.json':
            # Export as JSON
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'patterns': patterns_to_export
            }
            return write_json_file(str(output_path), export_data)

        elif output_path.suffix == '.zip':
            # Export as ZIP
            try:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # Add metadata
                    metadata = {
                        'version': '1.0',
                        'exported_at': datetime.now().isoformat(),
                        'pattern_count': len(patterns_to_export),
                        'includes_scripts': len(scripts_to_include) > 0
                    }
                    zf.writestr('metadata.json', json.dumps(metadata, indent=2))

                    # Add patterns
                    patterns_data = {
                        'version': '1.0',
                        'patterns': patterns_to_export
                    }
                    zf.writestr('patterns.json', json.dumps(patterns_data, indent=2))

                    # Add scripts if any
                    if scripts_to_include:
                        for script_path in scripts_to_include:
                            script_file = Path(script_path)
                            if script_file.exists():
                                zf.write(script_file, f'scripts/{script_file.name}')

                return True

            except Exception as e:
                print(f"Error creating ZIP: {e}")
                return False

        else:
            print(f"Unsupported file format: {output_path.suffix}")
            return False

    def import_patterns(
        self,
        import_file: str,
        scope: str = 'ask',
        override: bool = False
    ) -> Dict[str, Any]:
        """
        Import patterns from a file (JSON or ZIP).

        Args:
            import_file: Input file path
            scope: 'global', 'local', or 'ask'
            override: If True, override existing patterns without asking

        Returns:
            Dictionary with results
        """
        import_path = Path(import_file)

        if not import_path.exists():
            return {'error': f"File not found: {import_file}"}

        # Determine scope if not specified
        if scope == 'ask':
            print("Import to global or local?")
            print("  1) Global (~/.{platform}/)")
            print("  2) Local (./.{platform}/)")
            choice = input("Enter choice [1-2]: ")
            scope = 'global' if choice == '1' else 'local'

        results = {
            'imported': [],
            'skipped': [],
            'failed': [],
            'scripts_extracted': []
        }

        patterns_to_import = []

        # Read patterns based on format
        if import_path.suffix == '.json':
            data = read_json_file(str(import_path))
            patterns_to_import = data.get('patterns', [])

        elif import_path.suffix == '.zip':
            try:
                with zipfile.ZipFile(import_path, 'r') as zf:
                    # Read patterns
                    patterns_json = zf.read('patterns.json').decode('utf-8')
                    data = json.loads(patterns_json)
                    patterns_to_import = data.get('patterns', [])

                    # Extract scripts if present
                    for name in zf.namelist():
                        if name.startswith('scripts/'):
                            script_name = Path(name).name
                            target_dir = Path(f'.{self.platform}') / 'scripts' / 'patterns'
                            target_dir.mkdir(parents=True, exist_ok=True)
                            target_file = target_dir / script_name

                            with zf.open(name) as source, open(target_file, 'wb') as target:
                                shutil.copyfileobj(source, target)
                            target_file.chmod(0o755)  # Make executable
                            results['scripts_extracted'].append(str(target_file))

            except Exception as e:
                return {'error': f"Error reading ZIP: {e}"}

        else:
            return {'error': f"Unsupported file format: {import_path.suffix}"}

        # Import patterns
        for pattern in patterns_to_import:
            pid = pattern.get('id')
            if not pid:
                results['failed'].append(('(no id)', 'Pattern has no ID'))
                continue

            # Check if pattern already exists
            existing = self.pm.get_pattern(pid)
            if existing and not override:
                response = input(f"Pattern '{pid}' already exists. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    results['skipped'].append((pid, 'User declined to overwrite'))
                    continue

            # Add pattern
            if self.pm.add_pattern(pattern, scope=scope):
                results['imported'].append(pid)
            else:
                results['failed'].append((pid, 'Failed to add pattern'))

        return results


# CLI interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Cross-project pattern management')
    parser.add_argument('--platform', choices=['claude', 'cursor'], default='claude',
                        help='Platform to use')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # status command
    status_parser = subparsers.add_parser('status', help='Show sync status')

    # push command
    push_parser = subparsers.add_parser('push', help='Push patterns to global')
    push_parser.add_argument('pattern_ids', nargs='*', help='Pattern IDs to push (all if not specified)')
    push_parser.add_argument('--strategy', choices=['overwrite', 'skip', 'ask'], default='ask',
                             help='Merge strategy')

    # pull command
    pull_parser = subparsers.add_parser('pull', help='Pull patterns from global')
    pull_parser.add_argument('pattern_ids', nargs='*', help='Pattern IDs to pull (all if not specified)')
    pull_parser.add_argument('--override', action='store_true',
                             help='Override existing local patterns')

    # export command
    export_parser = subparsers.add_parser('export', help='Export patterns')
    export_parser.add_argument('pattern_ids', nargs='+', help='Pattern IDs to export')
    export_parser.add_argument('-o', '--output', required=True, help='Output file (.json or .zip)')
    export_parser.add_argument('--no-scripts', action='store_true',
                                help='Do not include check scripts')

    # import command
    import_parser = subparsers.add_parser('import', help='Import patterns')
    import_parser.add_argument('file', help='File to import (.json or .zip)')
    import_parser.add_argument('--scope', choices=['global', 'local', 'ask'], default='ask',
                                help='Import scope')
    import_parser.add_argument('--override', action='store_true',
                                help='Override existing patterns')

    args = parser.parse_args()

    cpm = CrossProjectManager(platform=args.platform)

    if args.command == 'status':
        status = cpm.get_sync_status()
        print("Sync Status:")
        print(f"  Only in global: {len(status['only_global'])}")
        print(f"  Only in local: {len(status['only_local'])}")
        print(f"  Different: {len(status['different'])}")
        print(f"  Same: {len(status['same'])}")

    elif args.command == 'push':
        pattern_ids = args.pattern_ids if args.pattern_ids else None
        results = cpm.push_to_global(pattern_ids, args.strategy)
        print(f"Pushed: {len(results['pushed'])}")
        print(f"Skipped: {len(results['skipped'])}")
        print(f"Failed: {len(results['failed'])}")

    elif args.command == 'pull':
        pattern_ids = args.pattern_ids if args.pattern_ids else None
        results = cpm.pull_from_global(pattern_ids, args.override)
        print(f"Pulled: {len(results['pulled'])}")
        print(f"Skipped: {len(results['skipped'])}")
        print(f"Failed: {len(results['failed'])}")

    elif args.command == 'export':
        success = cpm.export_patterns(
            args.pattern_ids,
            args.output,
            include_scripts=not args.no_scripts
        )
        if success:
            print(f"Exported to: {args.output}")
        else:
            print("Export failed")
            sys.exit(1)

    elif args.command == 'import':
        results = cpm.import_patterns(args.file, args.scope, args.override)
        if 'error' in results:
            print(f"Error: {results['error']}")
            sys.exit(1)
        print(f"Imported: {len(results['imported'])}")
        print(f"Skipped: {len(results['skipped'])}")
        print(f"Failed: {len(results['failed'])}")
        if results['scripts_extracted']:
            print(f"Extracted scripts: {len(results['scripts_extracted'])}")

    else:
        parser.print_help()
        sys.exit(1)
