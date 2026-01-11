#!/usr/bin/env python3
"""
Pattern tester for omg-learn.
Tests patterns against inputs and simulates hook execution.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from same directory
try:
    from .pattern_manager import PatternManager
    from .json_utils import get_patterns
except ImportError:
    import pattern_manager
    import json_utils
    PatternManager = pattern_manager.PatternManager
    get_patterns = json_utils.get_patterns


class PatternTester:
    """Tests patterns and simulates hook execution."""

    def __init__(self, platform: str = 'claude'):
        """
        Initialize pattern tester.

        Args:
            platform: 'claude' or 'cursor'
        """
        self.pm = PatternManager(platform=platform)
        self.platform = platform

    def test_pattern(
        self,
        pattern_id: str,
        test_input: str,
        tool_name: str = 'Bash',
        show_details: bool = True
    ) -> Tuple[bool, str, str]:
        """
        Test if a pattern would match given input.

        Args:
            pattern_id: Pattern ID to test
            test_input: Input to test against
            tool_name: Tool name (Bash, Write, Edit)
            show_details: Show detailed match information

        Returns:
            Tuple of (matched, action, message)
        """
        result = self.pm.get_pattern(pattern_id)
        if not result:
            return (False, '', f"Pattern '{pattern_id}' not found")

        pattern, scope = result

        # Check if pattern is enabled
        if not pattern.get('enabled', True):
            return (False, '', f"Pattern '{pattern_id}' is disabled")

        # Check hook type
        hook_type = pattern.get('hook', '')
        if hook_type not in ('PreToolUse', 'beforeShellExecution', 'UserPromptSubmit', 'beforeSubmitPrompt'):
            return (False, '', f"Invalid hook type: {hook_type}")

        # For PreToolUse/beforeShellExecution, check matcher
        if hook_type in ('PreToolUse', 'beforeShellExecution'):
            matcher = pattern.get('matcher', '')
            if matcher and matcher != '*' and matcher != tool_name:
                return (False, '', f"Matcher '{matcher}' does not match tool '{tool_name}'")

        # Check if there's a custom check script
        check_script = pattern.get('check_script', '')
        if check_script:
            return self._test_check_script(pattern, check_script, test_input)

        # Check regex pattern
        pattern_regex = pattern.get('pattern', '')
        if not pattern_regex:
            return (False, '', "Pattern has no regex or check script")

        # Test regex match
        try:
            if re.search(pattern_regex, test_input, re.IGNORECASE if hook_type in ('UserPromptSubmit', 'beforeSubmitPrompt') else 0):
                # Check exclude pattern
                exclude_pattern = pattern.get('exclude_pattern', '')
                if exclude_pattern:
                    if re.search(exclude_pattern, test_input):
                        reason = f"Matched exclude_pattern: {exclude_pattern}"
                        return (False, '', reason)

                # Pattern matched!
                action = pattern.get('action', 'warn')
                message = pattern.get('message', 'Pattern matched')
                return (True, action, message)
            else:
                return (False, '', f"Input does not match pattern: {pattern_regex}")

        except re.error as e:
            return (False, '', f"Invalid regex: {e}")

    def _test_check_script(
        self,
        pattern: Dict,
        check_script: str,
        test_input: str
    ) -> Tuple[bool, str, str]:
        """
        Execute a check script and return result.

        Args:
            pattern: Pattern dictionary
            check_script: Path to check script
            test_input: Input to test

        Returns:
            Tuple of (matched, action, message)
        """
        script_path = Path(check_script)
        if not script_path.exists():
            # Try relative to .claude or .cursor
            base_dir = Path(f'.{self.platform}')
            script_path = base_dir / check_script
            if not script_path.exists():
                return (False, '', f"Check script not found: {check_script}")

        try:
            result = subprocess.run(
                [str(script_path), test_input],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                # Script returned non-zero, pattern matched
                action = pattern.get('action', 'warn')
                message = pattern.get('message', 'Pattern matched')
                return (True, action, message)
            else:
                # Script returned zero, pattern did not match
                reason = "Check script returned 0 (pass)"
                if result.stdout:
                    reason += f": {result.stdout.strip()}"
                return (False, '', reason)

        except subprocess.TimeoutExpired:
            return (False, '', "Check script timed out (5s)")
        except Exception as e:
            return (False, '', f"Error running check script: {e}")

    def simulate_command(
        self,
        command: str,
        tool_name: str = 'Bash',
        show_details: bool = True
    ) -> Dict[str, Any]:
        """
        Simulate what hooks would do for a given command.

        Args:
            command: Command to simulate
            tool_name: Tool name (Bash, Write, Edit)
            show_details: Show detailed information

        Returns:
            Dictionary with simulation results
        """
        # Get all enabled patterns
        all_patterns = self.pm.list_patterns(scope='all', enabled_only=True)

        # Filter patterns for this hook type and tool
        hook_type = 'PreToolUse' if self.platform == 'claude' else 'beforeShellExecution'
        relevant_patterns = [
            p for p in all_patterns
            if p.get('hook') in (hook_type, 'PreToolUse', 'beforeShellExecution')
        ]

        # Test each pattern
        results = []
        for pattern in relevant_patterns:
            pattern_id = pattern.get('id', '')
            matched, action, message = self.test_pattern(
                pattern_id,
                command,
                tool_name,
                show_details=False
            )

            results.append({
                'pattern_id': pattern_id,
                'matched': matched,
                'action': action,
                'message': message,
                'scope': pattern.get('_scope', 'unknown')
            })

        # Find first match (first match wins)
        first_match = next((r for r in results if r['matched']), None)

        return {
            'command': command,
            'tool': tool_name,
            'patterns_checked': len(results),
            'patterns_matched': [r for r in results if r['matched']],
            'first_match': first_match,
            'would_allow': first_match is None or first_match['action'] in ('warn', 'ask'),
            'would_block': first_match is not None and first_match['action'] == 'block'
        }

    def simulate_batch(
        self,
        commands: List[str],
        tool_name: str = 'Bash'
    ) -> Dict[str, Any]:
        """
        Simulate multiple commands and return statistics.

        Args:
            commands: List of commands to simulate
            tool_name: Tool name

        Returns:
            Dictionary with batch simulation results
        """
        results = []
        for cmd in commands:
            sim = self.simulate_command(cmd, tool_name, show_details=False)
            results.append(sim)

        # Calculate statistics
        total = len(results)
        blocked = len([r for r in results if r['would_block']])
        allowed = len([r for r in results if r['would_allow']])

        # Count pattern triggers
        pattern_triggers = {}
        for r in results:
            if r['first_match']:
                pid = r['first_match']['pattern_id']
                pattern_triggers[pid] = pattern_triggers.get(pid, 0) + 1

        return {
            'total_commands': total,
            'would_allow': allowed,
            'would_block': blocked,
            'pattern_triggers': pattern_triggers,
            'results': results
        }


# CLI interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Pattern tester for omg-learn')
    parser.add_argument('--platform', choices=['claude', 'cursor'], default='claude',
                        help='Platform to use')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # test command
    test_parser = subparsers.add_parser('test', help='Test a pattern')
    test_parser.add_argument('pattern_id', help='Pattern ID to test')
    test_parser.add_argument('input', help='Input to test against')
    test_parser.add_argument('--tool', default='Bash', help='Tool name (Bash, Write, Edit)')

    # simulate command
    sim_parser = subparsers.add_parser('simulate', help='Simulate hook execution')
    sim_parser.add_argument('command', help='Command to simulate')
    sim_parser.add_argument('--tool', default='Bash', help='Tool name (Bash, Write, Edit)')

    # batch command
    batch_parser = subparsers.add_parser('batch', help='Simulate batch of commands')
    batch_parser.add_argument('file', help='File with commands (one per line)')
    batch_parser.add_argument('--tool', default='Bash', help='Tool name (Bash, Write, Edit)')

    args = parser.parse_args()

    tester = PatternTester(platform=args.platform)

    if args.command == 'test':
        matched, action, message = tester.test_pattern(
            args.pattern_id,
            args.input,
            args.tool
        )

        if matched:
            print(f"✓ Pattern WOULD match")
            print(f"  Action: {action}")
            print(f"  Message: {message}")
        else:
            print(f"✗ Pattern would NOT match")
            if message:
                print(f"  Reason: {message}")

    elif args.command == 'simulate':
        result = tester.simulate_command(args.command, args.tool)

        print(f"Simulating command: {args.command}")
        print(f"Tool: {args.tool}")
        print(f"Patterns checked: {result['patterns_checked']}")
        print()

        if result['first_match']:
            match = result['first_match']
            print(f"✓ Pattern WOULD trigger: {match['pattern_id']}")
            print(f"  Action: {match['action']}")
            print(f"  Message: {match['message']}")
            print()
            if result['would_block']:
                print("Result: Command would be BLOCKED")
            else:
                print(f"Result: Command would be ALLOWED (with {match['action']})")
        else:
            print("✓ No patterns matched")
            print("Result: Command would be ALLOWED")

    elif args.command == 'batch':
        with open(args.file, 'r') as f:
            commands = [line.strip() for line in f if line.strip()]

        result = tester.simulate_batch(commands, args.tool)

        print(f"Simulated {result['total_commands']} commands")
        print(f"  Would allow: {result['would_allow']}")
        print(f"  Would block: {result['would_block']}")
        print()
        print("Pattern triggers:")
        for pid, count in sorted(result['pattern_triggers'].items(), key=lambda x: -x[1]):
            print(f"  {pid}: {count} times")

    else:
        parser.print_help()
        sys.exit(1)
