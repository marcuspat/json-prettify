"""JSON statistics calculation functionality."""

import json
from typing import Dict, Any, List, Tuple, Union
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class JSONStats:
    """Statistics about a JSON document."""
    total_size: int  # Size in bytes
    total_keys: int  # Total number of object keys
    unique_keys: int  # Number of unique keys
    max_depth: int  # Maximum nesting depth
    total_strings: int
    total_numbers: int
    total_booleans: int
    total_nulls: int
    total_arrays: int
    total_objects: int
    array_lengths: List[int]  # Lengths of all arrays
    string_lengths: List[int]  # Lengths of all strings
    key_frequencies: Dict[str, int]  # Frequency of each key
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of statistics."""
        summary = {
            "size_bytes": self.total_size,
            "depth": self.max_depth,
            "counts": {
                "total_keys": self.total_keys,
                "unique_keys": self.unique_keys,
                "objects": self.total_objects,
                "arrays": self.total_arrays,
                "strings": self.total_strings,
                "numbers": self.total_numbers,
                "booleans": self.total_booleans,
                "nulls": self.total_nulls
            }
        }
        
        # Add array statistics if any
        if self.array_lengths:
            summary["arrays_info"] = {
                "count": len(self.array_lengths),
                "avg_length": sum(self.array_lengths) / len(self.array_lengths),
                "max_length": max(self.array_lengths),
                "min_length": min(self.array_lengths)
            }
        
        # Add string statistics if any
        if self.string_lengths:
            summary["strings_info"] = {
                "count": len(self.string_lengths),
                "avg_length": sum(self.string_lengths) / len(self.string_lengths),
                "max_length": max(self.string_lengths),
                "min_length": min(self.string_lengths)
            }
        
        # Add top 10 most frequent keys
        if self.key_frequencies:
            sorted_keys = sorted(
                self.key_frequencies.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            summary["top_keys"] = dict(sorted_keys[:10])
        
        return summary


class JSONStatsCalculator:
    """Calculates statistics for JSON data."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.reset()
    
    def reset(self):
        """Reset all statistics."""
        self.total_keys = 0
        self.unique_keys = set()
        self.max_depth = 0
        self.total_strings = 0
        self.total_numbers = 0
        self.total_booleans = 0
        self.total_nulls = 0
        self.total_arrays = 0
        self.total_objects = 0
        self.array_lengths = []
        self.string_lengths = []
        self.key_frequencies = defaultdict(int)
    
    def calculate(self, json_data: Union[str, Dict, List]) -> JSONStats:
        """
        Calculate statistics for JSON data.
        
        Args:
            json_data: JSON string or parsed data
            
        Returns:
            JSONStats object with calculated statistics
        """
        self.reset()
        
        # Parse JSON if string
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
                size_bytes = len(json_data.encode('utf-8'))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            data = json_data
            # Estimate size by converting back to JSON
            size_bytes = len(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        
        # Calculate statistics
        self._analyze_value(data, depth=0)
        
        return JSONStats(
            total_size=size_bytes,
            total_keys=self.total_keys,
            unique_keys=len(self.unique_keys),
            max_depth=self.max_depth,
            total_strings=self.total_strings,
            total_numbers=self.total_numbers,
            total_booleans=self.total_booleans,
            total_nulls=self.total_nulls,
            total_arrays=self.total_arrays,
            total_objects=self.total_objects,
            array_lengths=self.array_lengths,
            string_lengths=self.string_lengths,
            key_frequencies=dict(self.key_frequencies)
        )
    
    def _analyze_value(self, value: Any, depth: int):
        """Recursively analyze a JSON value."""
        self.max_depth = max(self.max_depth, depth)
        
        if isinstance(value, dict):
            self.total_objects += 1
            for key, val in value.items():
                self.total_keys += 1
                self.unique_keys.add(key)
                self.key_frequencies[key] += 1
                self._analyze_value(val, depth + 1)
        
        elif isinstance(value, list):
            self.total_arrays += 1
            self.array_lengths.append(len(value))
            for item in value:
                self._analyze_value(item, depth + 1)
        
        elif isinstance(value, str):
            self.total_strings += 1
            self.string_lengths.append(len(value))
        
        elif isinstance(value, (int, float)):
            self.total_numbers += 1
        
        elif isinstance(value, bool):
            self.total_booleans += 1
        
        elif value is None:
            self.total_nulls += 1


def calculate_json_stats(json_data: Union[str, Dict, List]) -> JSONStats:
    """
    Calculate statistics for JSON data.
    
    Args:
        json_data: JSON string or parsed data
        
    Returns:
        JSONStats object with calculated statistics
    """
    calculator = JSONStatsCalculator()
    return calculator.calculate(json_data)


def format_stats_output(stats: JSONStats, no_color: bool = False) -> str:
    """
    Format statistics for display.
    
    Args:
        stats: JSONStats object
        no_color: If True, output plain text without color codes
        
    Returns:
        Formatted statistics string
    """
    summary = stats.get_summary()
    lines = []
    
    # Basic stats
    lines.append("=== JSON Statistics ===")
    lines.append(f"Size: {summary['size_bytes']:,} bytes")
    lines.append(f"Maximum depth: {summary['depth']}")
    lines.append("")
    
    # Type counts
    lines.append("Type counts:")
    counts = summary['counts']
    lines.append(f"  Objects: {counts['objects']:,}")
    lines.append(f"  Arrays: {counts['arrays']:,}")
    lines.append(f"  Strings: {counts['strings']:,}")
    lines.append(f"  Numbers: {counts['numbers']:,}")
    lines.append(f"  Booleans: {counts['booleans']:,}")
    lines.append(f"  Nulls: {counts['nulls']:,}")
    lines.append("")
    
    # Key statistics
    lines.append("Key statistics:")
    lines.append(f"  Total keys: {counts['total_keys']:,}")
    lines.append(f"  Unique keys: {counts['unique_keys']:,}")
    
    # Array info if present
    if 'arrays_info' in summary:
        info = summary['arrays_info']
        lines.append("")
        lines.append("Array statistics:")
        lines.append(f"  Count: {info['count']:,}")
        lines.append(f"  Average length: {info['avg_length']:.1f}")
        lines.append(f"  Min length: {info['min_length']:,}")
        lines.append(f"  Max length: {info['max_length']:,}")
    
    # String info if present
    if 'strings_info' in summary:
        info = summary['strings_info']
        lines.append("")
        lines.append("String statistics:")
        lines.append(f"  Count: {info['count']:,}")
        lines.append(f"  Average length: {info['avg_length']:.1f}")
        lines.append(f"  Min length: {info['min_length']:,}")
        lines.append(f"  Max length: {info['max_length']:,}")
    
    # Top keys
    if 'top_keys' in summary and summary['top_keys']:
        lines.append("")
        lines.append("Most frequent keys:")
        for key, count in list(summary['top_keys'].items())[:10]:
            lines.append(f"  '{key}': {count:,} occurrences")
    
    return "\n".join(lines)