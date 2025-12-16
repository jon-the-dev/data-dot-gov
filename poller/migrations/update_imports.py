#!/usr/bin/env python3
"""
Automated script to update imports across the codebase to use core modules.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ImportUpdater:
    """Updates Python files to use core package imports."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.changes_made = []
        self.files_processed = 0
        self.errors = []

    def get_files_to_update(self) -> List[Path]:
        """Get list of Python files that need updating."""
        target_files = [
            "gov_data_downloader.py",
            "gov_data_downloader_v2.py",
            "gov_data_analyzer.py",
            "fetch_voting_records.py",
            "fetch_committees.py",
            "smart_fetch.py",
            "historical_data_fetcher.py",
            "categorize_bills.py",
            "comprehensive_analyzer.py"
        ]

        # Add all analyze_*.py files
        analyze_files = list(self.base_dir.glob("analyze_*.py"))

        files = []
        for filename in target_files:
            file_path = self.base_dir / filename
            if file_path.exists():
                files.append(file_path)

        files.extend(analyze_files)
        return files

    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of the file before modification."""
        backup_path = file_path.with_suffix(".py.backup")
        backup_path.write_text(file_path.read_text())
        return backup_path

    def update_imports_section(self, content: str) -> Tuple[str, List[str]]:
        """Update the imports section of a file."""
        changes = []

        # Pattern for the old try/except import block
        old_import_pattern = re.compile(
            r"# Import from new core package.*?\n.*?try:\s*\n.*?from core import.*?\n.*?_USE_CORE = True\s*\n.*?except ImportError:\s*\n.*?# Fallback to local implementations.*?\n.*?_USE_CORE = False",
            re.DOTALL | re.MULTILINE
        )

        new_imports = """# Import from consolidated core package
import warnings
from core.api.rate_limiter import RateLimiter
from core.api.congress import CongressGovAPI
from core.api.senate import SenateGovAPI
from core.storage import save_individual_record, save_index

# Deprecation warning for this script
warnings.warn(
    f"This script is deprecated. Use core package APIs directly or use comprehensive_analyzer.py",
    DeprecationWarning,
    stacklevel=2
)"""

        if old_import_pattern.search(content):
            content = old_import_pattern.sub(new_imports, content)
            changes.append("Updated import section to use core modules")

        return content, changes

    def remove_local_classes(self, content: str) -> Tuple[str, List[str]]:
        """Remove local class definitions that are now in core."""
        changes = []

        # Remove RateLimiter class
        rate_limiter_pattern = re.compile(
            r"class RateLimiter:.*?(?=\n\n\nclass|\n\n\ndef|\n\n\nif __name__|\Z)",
            re.DOTALL
        )

        if rate_limiter_pattern.search(content):
            content = rate_limiter_pattern.sub("# RateLimiter is now imported from core.api.rate_limiter\n", content)
            changes.append("Removed local RateLimiter class")

        # Remove SenateGovAPI class
        senate_api_pattern = re.compile(
            r"class SenateGovAPI:.*?(?=\n\n\nclass|\n\n\ndef|\n\n\nif __name__|\Z)",
            re.DOTALL
        )

        if senate_api_pattern.search(content):
            content = senate_api_pattern.sub("# SenateGovAPI is now imported from core.api.senate\n", content)
            changes.append("Removed local SenateGovAPI class")

        # Remove CongressGovAPI class
        congress_api_pattern = re.compile(
            r"class CongressGovAPI:.*?(?=\n\n\nclass|\n\n\ndef|\n\n\nif __name__|\Z)",
            re.DOTALL
        )

        if congress_api_pattern.search(content):
            content = congress_api_pattern.sub("# CongressGovAPI is now imported from core.api.congress\n", content)
            changes.append("Removed local CongressGovAPI class")

        return content, changes

    def update_local_functions(self, content: str) -> Tuple[str, List[str]]:
        """Update local storage functions to use core or add deprecation warnings."""
        changes = []

        # Pattern for save_individual_record function
        save_record_pattern = re.compile(
            r"def save_individual_record\(.*?\).*?(?=\ndef|\nclass|\nif __name__|\Z)",
            re.DOTALL
        )

        if save_record_pattern.search(content):
            # Add deprecation warning to the function
            def add_deprecation_warning(match):
                func_def = match.group(0)
                # Insert warning after the docstring
                if '"""' in func_def:
                    # Find end of docstring
                    lines = func_def.split("\n")
                    new_lines = []
                    in_docstring = False
                    docstring_closed = False

                    for line in lines:
                        new_lines.append(line)
                        if '"""' in line:
                            if not in_docstring:
                                in_docstring = True
                            elif in_docstring and not docstring_closed:
                                # Add warning after docstring
                                new_lines.append("    import warnings")
                                new_lines.append('    warnings.warn("save_individual_record is deprecated, use core.storage", DeprecationWarning, stacklevel=2)')
                                docstring_closed = True

                    return "\n".join(new_lines)
                else:
                    # No docstring, add warning at beginning of function
                    lines = func_def.split("\n")
                    if len(lines) > 1:
                        lines.insert(1, "    import warnings")
                        lines.insert(2, '    warnings.warn("save_individual_record is deprecated, use core.storage", DeprecationWarning, stacklevel=2)')
                    return "\n".join(lines)

            content = save_record_pattern.sub(add_deprecation_warning, content)
            changes.append("Added deprecation warning to local save_individual_record function")

        return content, changes

    def update_file(self, file_path: Path) -> Dict:
        """Update a single file."""
        result = {
            "file": str(file_path),
            "success": False,
            "changes": [],
            "backup_created": None,
            "error": None
        }

        try:
            # Read original content
            original_content = file_path.read_text()
            content = original_content
            all_changes = []

            # Create backup
            backup_path = self.backup_file(file_path)
            result["backup_created"] = str(backup_path)

            # Update imports
            content, changes = self.update_imports_section(content)
            all_changes.extend(changes)

            # Remove local classes
            content, changes = self.remove_local_classes(content)
            all_changes.extend(changes)

            # Update local functions
            content, changes = self.update_local_functions(content)
            all_changes.extend(changes)

            # Only write if changes were made
            if content != original_content:
                file_path.write_text(content)
                result["success"] = True
                result["changes"] = all_changes
                logger.info(f"Updated {file_path.name}: {len(all_changes)} changes")
            else:
                logger.info(f"No changes needed for {file_path.name}")
                # Remove backup if no changes
                backup_path.unlink()
                result["backup_created"] = None
                result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error updating {file_path.name}: {e}")

        return result

    def run(self) -> Dict:
        """Run the import update process."""
        logger.info("Starting import update process...")

        files_to_update = self.get_files_to_update()
        logger.info(f"Found {len(files_to_update)} files to update")

        results = {
            "files_processed": 0,
            "files_updated": 0,
            "files_with_errors": 0,
            "total_changes": 0,
            "details": []
        }

        for file_path in files_to_update:
            result = self.update_file(file_path)
            results["details"].append(result)
            results["files_processed"] += 1

            if result["success"]:
                if result["changes"]:
                    results["files_updated"] += 1
                    results["total_changes"] += len(result["changes"])
            else:
                results["files_with_errors"] += 1

        logger.info(f"Process completed: {results['files_updated']} files updated, {results['total_changes']} total changes")

        return results


def main():
    """Main execution function."""
    updater = ImportUpdater()
    results = updater.run()

    # Print summary
    print("\n=== Import Update Summary ===")
    print(f"Files processed: {results['files_processed']}")
    print(f"Files updated: {results['files_updated']}")
    print(f"Files with errors: {results['files_with_errors']}")
    print(f"Total changes: {results['total_changes']}")

    # Print details
    print("\n=== Detailed Results ===")
    for detail in results["details"]:
        if detail["changes"]:
            print(f"\n{detail['file']}:")
            for change in detail["changes"]:
                print(f"  - {change}")
            if detail["backup_created"]:
                print(f"  Backup: {detail['backup_created']}")
        elif detail["error"]:
            print(f"\n{detail['file']}: ERROR - {detail['error']}")

    # Show which files need manual review
    if results["files_with_errors"] > 0:
        print(f"\n⚠️  {results['files_with_errors']} files had errors and need manual review")

    return 0 if results["files_with_errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
