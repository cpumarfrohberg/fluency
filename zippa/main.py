# main.py
import fnmatch
from pathlib import Path
from typing import Iterator, NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile


class ZipItem(NamedTuple):
    item_type: str
    item_path: Path
    arcname: str


def _iter_zip_items(
    path: Path, base_path: Path, exclude_patterns: list[str], include_dirs: bool = True
):
    if path.is_file():
        relative_path = path.relative_to(base_path)
        yield ZipItem("file", path, str(relative_path))
        return

    for item_type, item_path in _traverse_files_and_dirs(
        path, exclude_patterns, include_dirs
    ):
        relative_path = item_path.relative_to(base_path)
        if item_type == "dir":
            yield ZipItem("dir", item_path, f"{relative_path}/")
        else:
            yield ZipItem("file", item_path, str(relative_path))


def _traverse_files_and_dirs(
    source_path: Path, exclude_patterns: list[str], include_dirs: bool = True
) -> Iterator[tuple[str, Path]]:
    if source_path.is_file():
        print(f"Processing file: {source_path}")
        yield ("file", source_path)
    elif source_path.is_dir():
        print(f"Processing subdirectory: {source_path}")
        for item in source_path.rglob("*"):
            # Calculate relative path for pattern matching
            relative_path = item.relative_to(source_path)

            if any(
                fnmatch.fnmatch(item.name, p) or fnmatch.fnmatch(str(relative_path), p)
                for p in exclude_patterns
            ):
                continue

            if item.is_dir():
                if include_dirs:
                    print(f"  Adding directory: {item}")
                    yield ("dir", item)
            else:
                print(f"  Adding file: {item}")
                yield ("file", item)


def _validate_directory(path: Path, directory_type: str = "directory") -> Path:
    if not path.exists():
        raise NotADirectoryError(f"{directory_type} path '{path}' does not exist")

    if not path.is_dir():
        raise NotADirectoryError(f"'{path}' is not a directory")

    return path


def _validate_source_file(path: Path) -> bool:
    has_files = any(item.is_file() for item in path.rglob("*"))
    if not has_files:
        print(f"Warning: Source directory '{path}' contains no files")
    return has_files


def pack_items(
    base_dir: Path,
    items: list[str],
    output_zip: Path,
    exclude_patterns: list[str],
    compress_level: int,
    include_dirs: bool = True,
    overwrite: bool = False,
) -> Iterator[str]:
    yield f"Starting to pack {len(items)} items from {base_dir}"

    validated_base_path = _validate_directory(base_dir, "Source directory")
    _validate_source_file(base_dir)

    output_path = output_zip
    target_dir = output_path.parent
    _validate_directory(target_dir, "Target directory")

    if output_path.exists() and not overwrite:
        yield f"Output file {output_zip} already exists. Skipping."
        return

    with ZipFile(
        str(output_zip), "w", ZIP_DEFLATED, compresslevel=compress_level
    ) as archive:
        files_added, dirs_added = 0, 0

        for item_str in items:
            if item_str == ".":
                target_path = validated_base_path
            else:
                target_path = validated_base_path / item_str

            yield f"Processing item: {item_str}"

            for zip_item in _iter_zip_items(
                target_path, validated_base_path, exclude_patterns, include_dirs
            ):
                if zip_item.item_type == "dir":
                    archive.writestr(zip_item.arcname, "")
                    dirs_added += 1
                    yield f"Added directory: {zip_item.item_path.name}"
                else:
                    archive.write(zip_item.item_path, arcname=zip_item.arcname)
                    files_added += 1
                    yield f"Added file: {zip_item.item_path.name}"

        archive.printdir()
        print(f"Added {files_added} files and {dirs_added} directories to {output_zip}")

        yield f"Completed: {files_added} files, {dirs_added} directories"


def _check_existing_files(archive: ZipFile, target_path: Path) -> list[str]:
    return [
        member.filename
        for member in archive.infolist()
        if not member.is_dir() and (target_path / member.filename).exists()
    ]


def extract_items(
    zip_file: Path,
    target_path: Path | None = None,
    item_name: str | None = None,
    overwrite: bool = False,
) -> None:
    if target_path is None:
        target_path = Path(".")

    _validate_source_file(zip_file)
    validated_target_path = _validate_directory(target_path, "Target directory")

    with ZipFile(str(zip_file), "r") as archive:
        existing_files = _check_existing_files(archive, validated_target_path)
        if not overwrite and existing_files:
            print(
                f"Warning: {len(existing_files)} files already exist and would be overwritten."
            )
            print("Use --force-overwrite to overwrite or --ask to confirm each file.")
            return

        if item_name is None:
            archive.extractall(validated_target_path)
            print(f"Extracted all items from {zip_file} to {validated_target_path}")
        else:
            archive.extract(item_name, validated_target_path)
            print(f"Extracted {item_name} from {zip_file} to {validated_target_path}")
