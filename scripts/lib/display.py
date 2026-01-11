#!/usr/bin/env python3
"""
Display utilities for omg-learn CLI.
Provides terminal formatting, tables, and color output.
"""

import sys
from typing import List, Dict, Any, Optional


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


def supports_color() -> bool:
    """
    Check if the terminal supports color output.

    Returns:
        True if colors are supported, False otherwise
    """
    # Check if stdout is a TTY
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False

    # Check environment variables
    import os
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('TERM') == 'dumb':
        return False

    return True


USE_COLOR = supports_color()


def colored(text: str, color: str) -> str:
    """
    Apply color to text if terminal supports it.

    Args:
        text: Text to colorize
        color: Color code from Colors class

    Returns:
        Colored text or plain text if colors not supported
    """
    if USE_COLOR:
        return f"{color}{text}{Colors.RESET}"
    return text


def success(text: str) -> str:
    """Format text as success (green)."""
    return colored(text, Colors.GREEN)


def error(text: str) -> str:
    """Format text as error (red)."""
    return colored(text, Colors.RED)


def warning(text: str) -> str:
    """Format text as warning (yellow)."""
    return colored(text, Colors.YELLOW)


def info(text: str) -> str:
    """Format text as info (cyan)."""
    return colored(text, Colors.CYAN)


def bold(text: str) -> str:
    """Format text as bold."""
    return colored(text, Colors.BOLD)


def dim(text: str) -> str:
    """Format text as dim."""
    return colored(text, Colors.DIM)


def print_table(
    headers: List[str],
    rows: List[List[str]],
    alignments: Optional[List[str]] = None
) -> None:
    """
    Print a formatted table to stdout.

    Args:
        headers: Column headers
        rows: List of rows, each row is a list of column values
        alignments: Optional list of 'left', 'right', or 'center' for each column
    """
    if not rows:
        print("(empty)")
        return

    # Calculate column widths
    num_cols = len(headers)
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Default to left alignment if not specified
    if alignments is None:
        alignments = ['left'] * num_cols

    # Print top border
    print("┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐")

    # Print headers
    header_cells = []
    for i, (header, width, align) in enumerate(zip(headers, col_widths, alignments)):
        header = bold(header)
        if align == 'right':
            cell = header.rjust(width)
        elif align == 'center':
            cell = header.center(width)
        else:
            cell = header.ljust(width)
        header_cells.append(f" {cell} ")
    print("│" + "│".join(header_cells) + "│")

    # Print separator
    print("├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤")

    # Print rows
    for row in rows:
        row_cells = []
        for i, (cell, width, align) in enumerate(zip(row, col_widths, alignments)):
            cell_str = str(cell)
            if align == 'right':
                cell_str = cell_str.rjust(width)
            elif align == 'center':
                cell_str = cell_str.center(width)
            else:
                cell_str = cell_str.ljust(width)
            row_cells.append(f" {cell_str} ")
        print("│" + "│".join(row_cells) + "│")

    # Print bottom border
    print("└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘")


def print_pattern_list(patterns: List[Dict[str, Any]]) -> None:
    """
    Print a formatted list of patterns.

    Args:
        patterns: List of pattern dictionaries
    """
    if not patterns:
        print(info("No patterns found"))
        return

    headers = ["Pattern ID", "Scope", "Enabled", "Description"]
    rows = []

    for p in patterns:
        pattern_id = p.get('id', '(no id)')
        scope = p.get('_scope', 'unknown')
        enabled = "✓" if p.get('enabled', True) else "✗"
        description = p.get('description', '(no description)')

        # Truncate description if too long
        if len(description) > 50:
            description = description[:47] + "..."

        # Color code the enabled column
        if p.get('enabled', True):
            enabled = success(enabled)
        else:
            enabled = dim(enabled)

        # Add override indicator
        if p.get('_overrides_global'):
            scope = scope + " " + info("(overrides global)")

        rows.append([pattern_id, scope, enabled, description])

    print_table(headers, rows)


def print_pattern_detail(pattern: Dict[str, Any], scope: str) -> None:
    """
    Print detailed information about a single pattern.

    Args:
        pattern: Pattern dictionary
        scope: Scope ('global' or 'local')
    """
    pid = pattern.get('id', '(no id)')
    print(bold(f"Pattern: {pid}"))
    print(f"Description: {pattern.get('description', '(no description)')}")
    print(f"Scope: {scope} ({pattern.get('_file', 'unknown file')})")

    enabled = pattern.get('enabled', True)
    if enabled:
        print(f"Enabled: {success('yes')}")
    else:
        print(f"Enabled: {error('no')}")

    print()
    print(bold("Configuration:"))
    print(f"  Hook: {pattern.get('hook', 'not specified')}")

    matcher = pattern.get('matcher')
    if matcher:
        print(f"  Matcher: {matcher}")

    pattern_regex = pattern.get('pattern')
    if pattern_regex:
        print(f"  Pattern: {pattern_regex}")

    exclude = pattern.get('exclude_pattern')
    if exclude:
        print(f"  Exclude: {exclude}")

    check_script = pattern.get('check_script')
    if check_script:
        print(f"  Check Script: {check_script}")

    action = pattern.get('action', 'warn')
    print(f"  Action: {action}")

    message = pattern.get('message', '')
    if message:
        print(f"  Message: {message}")

    skill_ref = pattern.get('skill_reference')
    if skill_ref:
        print()
        print(f"Related Skill: {skill_ref}")


def print_separator(char: str = "─", width: int = 60) -> None:
    """Print a separator line."""
    print(char * width)


def print_success(message: str) -> None:
    """Print a success message with checkmark."""
    print(success("✓ ") + message)


def print_error(message: str) -> None:
    """Print an error message with X mark."""
    print(error("✗ ") + message, file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a warning message with warning symbol."""
    print(warning("⚠ ") + message)


def print_info(message: str) -> None:
    """Print an info message with info symbol."""
    print(info("ℹ ") + message)


# CLI interface for testing
if __name__ == '__main__':
    print("Color support:", supports_color())
    print()

    print("Color test:")
    print(success("Success message"))
    print(error("Error message"))
    print(warning("Warning message"))
    print(info("Info message"))
    print(bold("Bold text"))
    print(dim("Dim text"))
    print()

    print("Symbol test:")
    print_success("Operation completed")
    print_error("Operation failed")
    print_warning("This is a warning")
    print_info("This is information")
    print()

    print("Table test:")
    headers = ["Name", "Status", "Count"]
    rows = [
        ["Pattern 1", success("✓"), "5"],
        ["Pattern 2", error("✗"), "0"],
        ["Pattern 3", success("✓"), "12"],
    ]
    print_table(headers, rows)
