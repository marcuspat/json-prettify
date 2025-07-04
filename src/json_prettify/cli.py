"""Command-line interface for JSON Prettify."""

import json
import sys
from pathlib import Path
from typing import Optional, List, Union, Tuple
import os

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TimeRemainingColumn

from .formatter import format_json, format_json_stream
from .validator import validate_json, validate_json_file, get_validation_errors
from .schema_validator import validate_against_schema
from .stats import calculate_json_stats, format_stats_output

__version__ = "1.0.0"

console = Console()
error_console = Console(stderr=True)


def get_indent_value(indent_str: str) -> Union[int, str, None]:
    """Convert indent string to appropriate value."""
    if indent_str == "tab":
        return "\t"
    try:
        return int(indent_str)
    except ValueError:
        raise click.BadParameter(f"Invalid indent value: {indent_str}. Must be 2, 4, or 'tab'")


def read_file_with_progress(file_path: Path, encoding: str, no_color: bool) -> Optional[str]:
    """Read a file with progress bar for large files (>1MB)."""
    file_size = file_path.stat().st_size
    
    # Only show progress for files larger than 1MB
    if file_size <= 1024 * 1024 or no_color:
        # Read normally for small files or when no-color is set
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    
    # Show progress for large files
    content_parts = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Reading {task.description}"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console,
        disable=no_color
    ) as progress:
        task = progress.add_task(
            description=f"{file_path.name}",
            total=file_size
        )
        
        with open(file_path, "r", encoding=encoding) as f:
            while True:
                chunk = f.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                content_parts.append(chunk)
                progress.update(task, advance=len(chunk.encode(encoding)))
    
    return ''.join(content_parts)


def write_file_with_progress(file_path: Path, content: str, encoding: str, no_color: bool) -> None:
    """Write a file with progress bar for large content (>1MB)."""
    content_bytes = content.encode(encoding)
    content_size = len(content_bytes)
    
    # Only show progress for content larger than 1MB
    if content_size <= 1024 * 1024 or no_color:
        # Write normally for small content or when no-color is set
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return
    
    # Show progress for large content
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]Writing {task.description}"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console,
        disable=no_color
    ) as progress:
        task = progress.add_task(
            description=f"{file_path.name}",
            total=content_size
        )
        
        with open(file_path, "w", encoding=encoding) as f:
            # Write in chunks
            chunk_size = 8192
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                f.write(chunk)
                progress.update(task, advance=len(chunk.encode(encoding)))


def process_single_file(
    file_path: Optional[Path],
    content: Optional[str],
    indent: Union[int, str],
    sort_keys: bool,
    compact: bool,
    validate_only: bool,
    no_color: bool,
    output_file: Optional[Path],
    encoding: str,
    schema: Optional[Path],
    stats: bool,
) -> Tuple[int, Optional[str]]:
    """Process a single file or stdin content."""
    try:
        # Read content if file path provided
        if file_path:
            try:
                content = read_file_with_progress(file_path, encoding, no_color)
            except FileNotFoundError:
                error_msg = f"File '{file_path}' not found"
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                else:
                    error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
                return 1, None
            except PermissionError:
                error_msg = f"Permission denied: '{file_path}'"
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                else:
                    error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
                return 1, None
            except UnicodeDecodeError as e:
                error_msg = f"Encoding error in '{file_path}': {str(e)}"
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                else:
                    error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
                return 1, None
        
        # Check for empty content
        if not content or not content.strip():
            error_msg = "Empty input - no JSON data found"
            if no_color:
                error_console.print(f"Error: {error_msg}")
            else:
                error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
            return 1, None
        
        # Check if content appears to be binary
        if '\x00' in content:
            error_msg = "Binary data detected - not a valid JSON text file"
            if no_color:
                error_console.print(f"Error: {error_msg}")
            else:
                error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
            return 1, None
        
        # Validation mode
        if validate_only and not schema:
            validation_result = validate_json(content)
            if validation_result is True:
                success_msg = f"✓ Valid JSON{f' ({file_path.name})' if file_path else ''}"
                if no_color:
                    console.print(f"OK: {success_msg}")
                else:
                    console.print(f"[green]{success_msg}[/green]")
                return 0, None
            else:
                # Get detailed errors
                errors = get_validation_errors(content)
                if errors:
                    error = errors[0]
                    error_msg = f"Invalid JSON{f' in {file_path.name}' if file_path else ''}: {error.message}"
                    if error.line:
                        error_msg += f" at line {error.line}"
                    if error.column:
                        error_msg += f", column {error.column}"
                else:
                    error_msg = f"Invalid JSON{f' in {file_path.name}' if file_path else ''}: {validation_result}"
                
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                else:
                    error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
                return 1, None
        
        # Schema validation if requested
        if schema:
            schema_errors = validate_against_schema(content, schema, encoding)
            if schema_errors:
                error_msg = f"Schema validation failed{f' for {file_path.name}' if file_path else ''}:"
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                    for err in schema_errors:
                        error_console.print(f"  - {err}")
                else:
                    error_lines = [error_msg] + [f"• {err}" for err in schema_errors]
                    error_console.print(Panel("\n".join(error_lines), title="[red]Schema Validation Error[/red]", border_style="red"))
                return 1, None
            elif validate_only:
                success_msg = f"✓ Valid JSON matching schema{f' ({file_path.name})' if file_path else ''}"
                if no_color:
                    console.print(f"OK: {success_msg}")
                else:
                    console.print(f"[green]{success_msg}[/green]")
                return 0, None
        
        # Show statistics if requested
        if stats:
            try:
                json_stats = calculate_json_stats(content)
                stats_output = format_stats_output(json_stats, no_color)
                
                if no_color:
                    console.print(stats_output)
                else:
                    console.print(Panel(stats_output, title=f"[blue]JSON Statistics{f' - {file_path.name}' if file_path else ''}[/blue]", border_style="blue"))
                
                # If only showing stats, don't format
                if not output_file:
                    return 0, None
            except Exception as e:
                error_msg = f"Error calculating statistics: {str(e)}"
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                else:
                    error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
                # Continue with formatting even if stats fail
        
        # Format JSON
        # Convert tab indent for formatter
        format_indent = None if compact else indent
        if isinstance(format_indent, str) and format_indent == "\t":
            # json module doesn't support tab directly, we'll post-process
            format_indent = 2
            use_tabs = True
        else:
            use_tabs = False
        
        try:
            result = format_json(
                content,
                indent=format_indent,
                sort_keys=sort_keys,
                compact=compact,
                ensure_ascii=False
            )
            
            # Post-process for tab indentation
            if use_tabs and not compact:
                lines = result.split('\n')
                processed_lines = []
                for line in lines:
                    # Count leading spaces and convert to tabs
                    stripped = line.lstrip(' ')
                    space_count = len(line) - len(stripped)
                    if space_count > 0:
                        tab_count = space_count // 2  # Since we used indent=2
                        processed_lines.append('\t' * tab_count + stripped)
                    else:
                        processed_lines.append(line)
                result = '\n'.join(processed_lines)
            
        except json.JSONDecodeError as e:
            # Get detailed error information
            errors = get_validation_errors(content)
            if errors:
                error = errors[0]
                error_msg = f"Invalid JSON: {error.message}"
                if error.line:
                    error_msg += f" at line {error.line}"
                if error.column:
                    error_msg += f", column {error.column}"
                if error.context:
                    error_msg += f" near: {error.context}"
            else:
                error_msg = f"Invalid JSON: {str(e)}"
            
            if no_color:
                error_console.print(f"Error: {error_msg}")
            else:
                error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
            return 1, None
        except ValueError as e:
            error_msg = str(e)
            if no_color:
                error_console.print(f"Error: {error_msg}")
            else:
                error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
            return 1, None
        
        return 0, result
        
    except Exception as e:
        error_msg = str(e)
        if no_color:
            error_console.print(f"Error: {error_msg}")
        else:
            error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
        return 1, None


@click.command()
@click.argument("files", nargs=-1, type=click.Path(path_type=Path))
@click.option(
    "--indent",
    "-i",
    default="2",
    type=str,
    help="Number of spaces for indentation (2, 4, or 'tab') (default: 2)",
)
@click.option(
    "--sort-keys",
    "-s",
    is_flag=True,
    help="Sort object keys alphabetically",
)
@click.option(
    "--compact",
    "-c",
    is_flag=True,
    help="Output compact JSON (no pretty-printing)",
)
@click.option(
    "--validate-only",
    "-v",
    is_flag=True,
    help="Only validate JSON, don't format",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable syntax highlighting and colored output",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write output to file instead of stdout",
)
@click.option(
    "--encoding",
    "-e",
    default="utf-8",
    help="File encoding (default: utf-8)",
)
@click.option(
    "--schema",
    type=click.Path(exists=True, path_type=Path),
    help="Validate JSON against a JSON Schema file",
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show JSON statistics (keys, depth, size, etc.)",
)
@click.version_option(version=__version__, prog_name="json-prettify")
def main(
    files: Tuple[Path, ...],
    indent: str,
    sort_keys: bool,
    compact: bool,
    validate_only: bool,
    no_color: bool,
    output: Optional[Path],
    encoding: str,
    schema: Optional[Path],
    stats: bool,
) -> None:
    """Pretty-print JSON with syntax highlighting.

    If FILES are not provided, reads from stdin.
    Supports multiple files with clear separation.
    
    Additional features:
    - Schema validation with --schema flag
    - JSON statistics with --stats flag
    - Write to file with --output flag
    """
    # Parse indent option
    try:
        indent_value = get_indent_value(indent)
    except click.BadParameter as e:
        error_console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    
    # Collect all outputs if writing to file
    all_outputs = []
    exit_code = 0
    
    # Process stdin if no files provided or "-" is specified
    if not files or (len(files) == 1 and str(files[0]) == "-"):
        # Check if stdin is provided (handle "-" as well)
        content = sys.stdin.read()
        code, result = process_single_file(
            None, content, indent_value, sort_keys, compact,
            validate_only, no_color, output, encoding, schema, stats
        )
        exit_code = max(exit_code, code)
        
        if code == 0 and result and not validate_only:
            if output:
                all_outputs.append(result)
            else:
                # Output with or without syntax highlighting
                if no_color or compact:
                    click.echo(result)
                else:
                    syntax = Syntax(result, "json", theme="monokai", line_numbers=False)
                    console.print(syntax)
    else:
        # Process multiple files
        for i, file_path in enumerate(files):
            # Check if file exists
            if not file_path.exists():
                error_msg = f"File '{file_path}' not found"
                if no_color:
                    error_console.print(f"Error: {error_msg}")
                else:
                    error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
                exit_code = 1
                continue
            
            # Show file separator for multiple files
            if len(files) > 1 and not validate_only and not output:
                if i > 0:
                    console.print()  # Empty line between files
                if no_color:
                    console.print(f"--- {file_path.name} ---")
                else:
                    console.print(f"[blue]--- {file_path.name} ---[/blue]")
            
            code, result = process_single_file(
                file_path, None, indent_value, sort_keys, compact,
                validate_only, no_color, output, encoding, schema, stats
            )
            exit_code = max(exit_code, code)
            
            if code == 0 and result and not validate_only:
                if output:
                    all_outputs.append(result)
                    # Add separator between files in output
                    if i < len(files) - 1:
                        all_outputs.append("")
                else:
                    # Output with or without syntax highlighting
                    if no_color or compact:
                        click.echo(result)
                    else:
                        syntax = Syntax(result, "json", theme="monokai", line_numbers=False)
                        console.print(syntax)
    
    # Write to output file if specified
    if output and all_outputs:
        try:
            # Create parent directories if needed
            output.parent.mkdir(parents=True, exist_ok=True)
            
            # Write all outputs
            combined_output = "\n".join(all_outputs)
            write_file_with_progress(output, combined_output, encoding, no_color)
            
            if not no_color:
                console.print(f"[green]✓ Written to {output}[/green]")
        except Exception as e:
            error_msg = f"Failed to write output file: {str(e)}"
            if no_color:
                error_console.print(f"Error: {error_msg}")
            else:
                error_console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
            sys.exit(1)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()