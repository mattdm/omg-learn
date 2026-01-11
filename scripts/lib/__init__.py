"""
omg-learn library package.
Provides pattern management, testing, and utilities.
"""

__version__ = '2.0.0'

from .json_utils import (
    read_json_file,
    write_json_file,
    merge_patterns,
    get_patterns,
    add_pattern,
    update_pattern,
    delete_pattern,
    find_pattern
)

from .pattern_manager import PatternManager

__all__ = [
    'read_json_file',
    'write_json_file',
    'merge_patterns',
    'get_patterns',
    'add_pattern',
    'update_pattern',
    'delete_pattern',
    'find_pattern',
    'PatternManager'
]
