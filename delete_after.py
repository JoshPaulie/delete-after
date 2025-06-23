#!/usr/bin/env python3
"""
File deletion script that scans directories for .delete_after files and removes files older than the specified duration.

Usage:
    python delete_after.py [--dry-run] [--verbose] [DIRECTORY]

The .delete_after file format:
    <number> <unit>

    Where:
    - number: integer or float
    - Valid units: minute(s), hour(s), day(s), week(s), month(s), year(s) (and abbreviations)

Examples:
    - "30 minutes"
    - "2.5 hours"
    - "7 days"
    - "1 week"

"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

# Version information
__version__ = "1.0.0"

# Time unit multipliers (in seconds)
UNIT_MULTIPLIERS: dict[str, int] = {
    # Minutes
    "minute": 60,
    "minutes": 60,
    "min": 60,
    "m": 60,
    # Hours
    "hour": 3600,
    "hours": 3600,
    "hr": 3600,
    "h": 3600,
    # Days
    "day": 86400,
    "days": 86400,
    "d": 86400,
    # Weeks
    "week": 604800,
    "weeks": 604800,
    "w": 604800,
    # Months (approximate - 30 days)
    "month": 2592000,
    "months": 2592000,
    "mo": 2592000,
    # Years (approximate - 365 days)
    "year": 31536000,
    "years": 31536000,
    "yr": 31536000,
    "y": 31536000,
}

# Constants
SECONDS_PER_DAY = 86400
LOG_FILE_PATH = "/var/log/delete_after.log"
HOME_LOG_PATH = "~/delete_after.log"


class DeleteAfterScript:
    """Script that scans directories and deletes old files based on .delete_after specifications."""

    def __init__(
        self,
        root_directory: str,
        *,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize the delete script.

        Args:
            root_directory: Root directory to scan
            dry_run: If True, only log what would be deleted without actually deleting

        """
        self.root_directory = Path(root_directory).resolve()
        self.dry_run = dry_run

        # Set up logging
        self.logger = self._setup_logging()

        if self.dry_run:
            self.logger.info("Running in DRY RUN mode - no files will be deleted")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration and return logger instance."""
        # Determine log file path
        log_file = (
            Path(LOG_FILE_PATH)
            if os.access("/var/log", os.W_OK)
            else Path(HOME_LOG_PATH).expanduser()
        )

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file),
            ],
        )

        return logging.getLogger("delete_after")

    # ===== File Parsing and Age Calculation =====

    def parse_delete_after_file(self, file_path: Path) -> int | None:
        """
        Parse a .delete_after file and return the duration in seconds.

        Args:
            file_path: Path to the .delete_after file

        Returns:
            Duration in seconds, or None if parsing failed

        """
        try:
            content = file_path.read_text().strip()
        except (FileNotFoundError, PermissionError, OSError):
            self.logger.exception("Error reading %s", file_path)
            return None

        # Parse format: "<number> <unit>"
        match = re.match(r"^(\d+(?:\.\d+)?)\s+(\w+)$", content.lower())
        if not match:
            self.logger.error(
                "Invalid format in %s: '%s'. Expected '<number> <unit>'",
                file_path,
                content,
            )
            return None

        number_str, unit = match.groups()
        number = float(number_str)

        if unit not in UNIT_MULTIPLIERS:
            self.logger.error(
                "Unknown unit '%s' in %s. Valid units: %s",
                unit,
                file_path,
                list(UNIT_MULTIPLIERS.keys()),
            )
            return None

        duration_seconds = int(number * UNIT_MULTIPLIERS[unit])
        self.logger.debug(
            "Parsed %s: %s %s = %s seconds",
            file_path,
            number,
            unit,
            duration_seconds,
        )
        return duration_seconds

    def get_file_age_seconds(self, file_path: Path) -> int:
        """Get the age of a file in seconds since last modification."""
        try:
            stat = file_path.stat()
            return int(time.time() - stat.st_mtime)
        except (FileNotFoundError, PermissionError, OSError):
            self.logger.exception("Error getting file age for %s", file_path)
            return 0

    # ===== File Deletion Operations =====

    def delete_old_files_in_directory(
        self,
        directory: Path,
        max_age_seconds: int,
    ) -> tuple[int, int]:
        """
        Delete files in a directory and all subdirectories that are older than max_age_seconds.

        Args:
            directory: Directory to clean (will recursively process subdirectories)
            max_age_seconds: Maximum age in seconds

        Returns:
            Tuple of (files_deleted, errors_encountered)

        """
        deleted_count = 0
        error_count = 0

        try:
            # Process all files recursively using os.walk to avoid infinite recursion
            for root, dirs, files in os.walk(directory):
                root_path = Path(root)

                # Skip directories that have their own .delete_after file (except the starting directory)
                if root_path != directory and (root_path / ".delete_after").exists():
                    self.logger.debug(
                        "Skipping %s - has its own .delete_after file",
                        root_path,
                    )
                    # Remove this directory from dirs to prevent os.walk from descending into it
                    dirs.clear()
                    continue

                # Process files in current directory
                for filename in files:
                    file_path = root_path / filename

                    # Skip .delete_after files themselves
                    if filename == ".delete_after":
                        continue

                    # Check if file should be deleted
                    deleted, error = self._process_file_for_deletion(
                        file_path,
                        max_age_seconds,
                    )
                    deleted_count += deleted
                    error_count += error

        except (OSError, PermissionError):
            self.logger.exception("Error processing directory %s", directory)
            error_count += 1

        return deleted_count, error_count

    def _process_file_for_deletion(
        self,
        file_path: Path,
        max_age_seconds: int,
    ) -> tuple[int, int]:
        """
        Process a single file to determine if it should be deleted.

        Args:
            file_path: Path to the file to process
            max_age_seconds: Maximum age in seconds before deletion

        Returns:
            Tuple of (files_deleted, errors_encountered) - each will be 0 or 1

        """
        file_age = self.get_file_age_seconds(file_path)

        if file_age <= max_age_seconds:
            # File is not old enough to delete
            age_days = file_age / SECONDS_PER_DAY
            max_age_days = max_age_seconds / SECONDS_PER_DAY
            self.logger.debug(
                "Keeping %s (age: %.1f days, limit: %.1f days)",
                file_path,
                age_days,
                max_age_days,
            )
            return 0, 0

        # File is old enough to delete
        age_days = file_age / SECONDS_PER_DAY
        max_age_days = max_age_seconds / SECONDS_PER_DAY

        if self.dry_run:
            self.logger.info(
                "[DRY RUN] Would delete %s (age: %.1f days, limit: %.1f days)",
                file_path,
                age_days,
                max_age_days,
            )
            return 1, 0

        # Actually delete the file
        try:
            file_path.unlink()
            self.logger.info(
                "Deleted %s (age: %.1f days, limit: %.1f days)",
                file_path,
                age_days,
                max_age_days,
            )
        except (FileNotFoundError, PermissionError, OSError):
            self.logger.exception("Error deleting %s", file_path)
            return 0, 1

        return 1, 0

    # ===== Directory Scanning Operations =====

    def scan_directories(self) -> dict[str, int]:
        """
        Scan all directories recursively for .delete_after files and process them.

        Returns:
            Dictionary with scan statistics

        """
        stats = {
            "directories_scanned": 0,
            "delete_after_files_found": 0,
            "files_deleted": 0,
            "errors": 0,
        }

        try:
            for root, _dirs, _files in os.walk(self.root_directory):
                root_path = Path(root)
                stats["directories_scanned"] += 1

                delete_after_file = root_path / ".delete_after"

                if delete_after_file.exists():
                    stats["delete_after_files_found"] += 1
                    self.logger.debug("Found .delete_after file in %s", root_path)

                    max_age_seconds = self.parse_delete_after_file(delete_after_file)
                    if max_age_seconds is not None:
                        deleted, errors = self.delete_old_files_in_directory(
                            root_path,
                            max_age_seconds,
                        )
                        stats["files_deleted"] += deleted
                        stats["errors"] += errors
                    else:
                        stats["errors"] += 1

        except (OSError, PermissionError):
            self.logger.exception("Error during directory scan")
            stats["errors"] += 1

        return stats

    # ===== Script Execution Method =====

    def run(self) -> dict[str, int]:
        """Run a single scan and return statistics."""
        start_time = time.time()
        self.logger.info("Starting scan of %s", self.root_directory)

        stats = self.scan_directories()

        duration = time.time() - start_time
        self.logger.info(
            "Scan completed in %.2fs - "
            "Directories: %d, "
            "Delete-after files: %d, "
            "Files deleted: %d, "
            "Errors: %d",
            duration,
            stats["directories_scanned"],
            stats["delete_after_files_found"],
            stats["files_deleted"],
            stats["errors"],
        )

        return stats


# ===== Command Line Interface =====


def main() -> int:
    """Run the delete-after script."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    # Configure logging verbosity
    if args.verbose:
        logging.getLogger("delete_after").setLevel(logging.DEBUG)

    # Validate directory argument
    directory = Path(args.directory).resolve()
    if not _validate_directory(directory):
        return 1

    # Create and run script
    script = DeleteAfterScript(
        root_directory=str(directory),
        dry_run=args.dry_run,
    )

    try:
        script.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 0
    except (OSError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Scan directories and delete old files based on .delete_after specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
.delete_after file format:
    <number> <unit>

Examples:
    30 minutes
    2.5 hours
    7 days
    1 week

Valid units: minute(s), hour(s), day(s), week(s), month(s), year(s) (and abbreviations)
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting files",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"delete-after {__version__}",
        help="Show version information",
    )

    return parser


def _validate_directory(directory: Path) -> bool:
    """
    Validate that the provided directory exists and is accessible.

    Args:
        directory: Path to validate

    Returns:
        True if directory is valid, False otherwise

    """
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist", file=sys.stderr)
        return False

    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        return False

    return True


# ===== Script Entry Point =====

if __name__ == "__main__":
    sys.exit(main())
