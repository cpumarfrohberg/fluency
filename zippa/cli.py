# cli.py
from pathlib import Path

import typer

from .main import extract_items, pack_items
from .utils import read_zipignore

VERBOSE_OPTION = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
DEFAULT_ZIP_NAME = "output.zip"

app = typer.Typer()


@app.command()
def pack(
    items: list[str] = typer.Argument(..., help="Files or directories to zip"),
    output: str = typer.Option(
        DEFAULT_ZIP_NAME, "--output", "-o", help="Output zip file"
    ),
    work_dir: str | None = typer.Option(
        None,
        "--work-dir",
        "-d",
        help="Directory to work from (default: current directory)",
    ),
    exclude: list[str] = typer.Option(
        [], "--exclude", "-x", help="Additional file patterns to exclude"
    ),
    exclude_file: str = typer.Option(
        ".zipignore", "--exclude-file", help="Path to .zipignore file"
    ),
    compress_level: int = typer.Option(
        3, "--compress-level", "-c", help="Compression level (0-9)", min=0, max=9
    ),
    ask_overwrite: bool = typer.Option(
        False, "--ask", help="Ask before overwriting existing files"
    ),
    force_overwrite: bool = typer.Option(
        False, "--force-overwrite", "-f", help="Force overwrite without asking"
    ),
    verbose: bool = VERBOSE_OPTION,
):
    """Zip directories and files with exclusion support"""

    if verbose:
        typer.echo("Warning: Using verbose mode.")
        if work_dir:
            typer.echo(f"Would work from: {work_dir}")

    zipignore_patterns = read_zipignore(exclude_file)

    # Combine with command-line exclusions
    all_exclude_patterns = zipignore_patterns + exclude

    base_dir = work_dir or "."

    if verbose:
        if base_dir == ".":
            typer.echo("Working from current directory")
        else:
            typer.echo(f"Working from directory: {base_dir}")

    # Handle overwrite logic at CLI level
    overwrite = force_overwrite  # Force takes precedence

    if not overwrite and Path(output).exists():
        if ask_overwrite:
            overwrite = typer.confirm(
                f"Output file '{output}' already exists. Overwrite?"
            )
        else:
            overwrite = False

    # Consume the generator to execute the packing
    for message in pack_items(
        base_dir,
        items,
        output,
        all_exclude_patterns,
        compress_level,
        overwrite=overwrite,
    ):
        if verbose:
            typer.echo(f"  {message}")


@app.command()
def extract(
    source: str = typer.Argument(..., help="Zip file to extract"),
    output: str = typer.Option(None, "--output", "-o", help="Output directory"),
    item_name: str = typer.Option(
        None, "--item-name", "-i", help="Item name to extract"
    ),
    ask_overwrite: bool = typer.Option(
        False, "--ask", help="Ask before overwriting existing files"
    ),
    force_overwrite: bool = typer.Option(
        False, "--force-overwrite", "-f", help="Force overwrite without asking"
    ),
    verbose: bool = VERBOSE_OPTION,
):
    """Extract items from a zip file"""

    if verbose:
        typer.echo("Warning: Both --verbose and --quiet specified. Using verbose mode.")

    # Handle overwrite logic at CLI level
    overwrite = force_overwrite

    if not overwrite and output and Path(output).exists():
        if ask_overwrite:
            overwrite = typer.confirm(
                f"Output directory '{output}' contains existing files. Overwrite?"
            )
        else:
            overwrite = False

    extract_items(
        zip_file=source,
        target_path=output,
        item_name=item_name,
        overwrite=overwrite,
    )


@app.command()
def list(
    source: str = typer.Argument(..., help="Zip file to list contents"),
    verbose: bool = VERBOSE_OPTION,
):
    """List contents of a zip file"""

    if verbose:
        typer.echo(f"Listing contents of {source}")

    # TODO: Implement list functionality using ZipArchiveManager
    # This would show the contents without extracting
    typer.echo(f"Contents of {source}:")
    typer.echo("(List functionality not yet implemented)")


if __name__ == "__main__":
    app()
