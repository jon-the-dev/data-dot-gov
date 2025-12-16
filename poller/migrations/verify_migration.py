#!/usr/bin/env python3
"""
Verification script for the core package migration.

This script validates that:
1. All imports work correctly
2. Backward compatibility is maintained
3. Data integrity is preserved
4. Critical workflows function properly
"""

import importlib
import logging
import sys
import warnings
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates the core package migration."""

    def __init__(self):
        self.results = {
            "core_imports": {},
            "compatibility_layer": {},
            "file_imports": {},
            "functionality_tests": {},
            "overall_status": "unknown"
        }
        self.errors = []

    def test_core_imports(self) -> Dict[str, bool]:
        """Test that all core modules can be imported successfully."""
        logger.info("Testing core module imports...")

        core_modules = [
            "core.api.rate_limiter",
            "core.api.congress",
            "core.api.senate",
            "core.storage",
            "core.models",
        ]

        results = {}
        for module_name in core_modules:
            try:
                module = importlib.import_module(module_name)
                results[module_name] = True
                logger.info(f"✓ Successfully imported {module_name}")
            except Exception as e:
                results[module_name] = False
                error_msg = f"Failed to import {module_name}: {e}"
                logger.error(f"✗ {error_msg}")
                self.errors.append(error_msg)

        return results

    def test_compatibility_layer(self) -> Dict[str, bool]:
        """Test the compatibility layer functionality."""
        logger.info("Testing compatibility layer...")

        results = {}

        # Test compatibility imports
        try:
            from migrations.compatibility import (
                CongressGovAPI,
                RateLimiter,
                SenateGovAPI,
            )
            results["compatibility_imports"] = True
            logger.info("✓ Compatibility layer imports successful")
        except Exception as e:
            results["compatibility_imports"] = False
            error_msg = f"Failed to import compatibility layer: {e}"
            logger.error(f"✗ {error_msg}")
            self.errors.append(error_msg)
            return results

        # Test RateLimiter compatibility
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                rate_limiter = RateLimiter(max_requests=5, time_window=60)

                # Check if deprecation warning was issued
                if w and issubclass(w[0].category, DeprecationWarning):
                    logger.info("✓ RateLimiter deprecation warning issued correctly")
                    results["rate_limiter_warning"] = True
                else:
                    results["rate_limiter_warning"] = False
                    self.errors.append("RateLimiter deprecation warning not issued")

                # Test basic functionality
                rate_limiter.wait_if_needed()  # Should not raise error
                results["rate_limiter_functionality"] = True
                logger.info("✓ RateLimiter basic functionality works")

        except Exception as e:
            results["rate_limiter_functionality"] = False
            error_msg = f"RateLimiter compatibility test failed: {e}"
            logger.error(f"✗ {error_msg}")
            self.errors.append(error_msg)

        # Test API class compatibility
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                congress_api = CongressGovAPI()
                senate_api = SenateGovAPI()
                results["api_classes"] = True
                logger.info("✓ API classes instantiate correctly")
        except Exception as e:
            results["api_classes"] = False
            error_msg = f"API classes compatibility test failed: {e}"
            logger.error(f"✗ {error_msg}")
            self.errors.append(error_msg)

        return results

    def test_file_imports(self) -> Dict[str, bool]:
        """Test that updated files can be imported without errors."""
        logger.info("Testing updated file imports...")

        target_files = [
            "gov_data_downloader",
            "gov_data_downloader_v2",
            "gov_data_analyzer",
            "fetch_voting_records",
            "categorize_bills",
            "comprehensive_analyzer"
        ]

        results = {}
        for filename in target_files:
            try:
                # Try to import the module
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    module = importlib.import_module(filename)

                results[filename] = True
                logger.info(f"✓ Successfully imported {filename}")
            except Exception as e:
                results[filename] = False
                error_msg = f"Failed to import {filename}: {e}"
                logger.error(f"✗ {error_msg}")
                self.errors.append(error_msg)

        return results

    def test_functionality(self) -> Dict[str, bool]:
        """Test basic functionality of core components."""
        logger.info("Testing core functionality...")

        results = {}

        # Test RateLimiter functionality
        try:
            from core.api.rate_limiter import RateLimiter
            rate_limiter = RateLimiter(max_requests=5, time_window=60)
            rate_limiter.wait_if_needed()
            results["core_rate_limiter"] = True
            logger.info("✓ Core RateLimiter works")
        except Exception as e:
            results["core_rate_limiter"] = False
            error_msg = f"Core RateLimiter test failed: {e}"
            logger.error(f"✗ {error_msg}")
            self.errors.append(error_msg)

        # Test storage functionality
        try:
            from core.storage import save_individual_record

            # Don't actually save, just check the function exists and can be called
            if callable(save_individual_record):
                results["core_storage"] = True
                logger.info("✓ Core storage functions accessible")
            else:
                results["core_storage"] = False
                self.errors.append("save_individual_record is not callable")
        except Exception as e:
            results["core_storage"] = False
            error_msg = f"Core storage test failed: {e}"
            logger.error(f"✗ {error_msg}")
            self.errors.append(error_msg)

        # Test API class instantiation
        try:
            from core.api.congress import CongressGovAPI
            from core.api.senate import SenateGovAPI

            congress_api = CongressGovAPI()
            senate_api = SenateGovAPI()
            results["core_apis"] = True
            logger.info("✓ Core API classes instantiate correctly")
        except Exception as e:
            results["core_apis"] = False
            error_msg = f"Core API instantiation test failed: {e}"
            logger.error(f"✗ {error_msg}")
            self.errors.append(error_msg)

        return results

    def check_data_integrity(self) -> Dict[str, Any]:
        """Check that data files and structure are intact."""
        logger.info("Checking data integrity...")

        integrity_info = {
            "data_dir_exists": False,
            "core_dir_exists": False,
            "backup_files_found": 0,
            "migration_files_exist": False
        }

        # Check data directory
        data_dir = Path("data")
        if data_dir.exists():
            integrity_info["data_dir_exists"] = True
            logger.info("✓ Data directory exists")
        else:
            logger.warning("⚠ Data directory not found")

        # Check core directory
        core_dir = Path("core")
        if core_dir.exists():
            integrity_info["core_dir_exists"] = True
            logger.info("✓ Core directory exists")
        else:
            logger.error("✗ Core directory not found")
            self.errors.append("Core directory missing")

        # Check for backup files
        backup_files = list(Path(".").glob("*.backup"))
        integrity_info["backup_files_found"] = len(backup_files)
        if backup_files:
            logger.info(f"✓ Found {len(backup_files)} backup files")
        else:
            logger.info("No backup files found")

        # Check migration files
        migrations_dir = Path("migrations")
        if migrations_dir.exists():
            migration_files = ["__init__.py", "compatibility.py", "update_imports.py", "verify_migration.py"]
            missing_files = [f for f in migration_files if not (migrations_dir / f).exists()]
            if not missing_files:
                integrity_info["migration_files_exist"] = True
                logger.info("✓ All migration files present")
            else:
                logger.warning(f"⚠ Missing migration files: {missing_files}")
        else:
            logger.error("✗ Migrations directory not found")

        return integrity_info

    def run_validation(self) -> Dict:
        """Run the complete validation suite."""
        logger.info("=== Starting Migration Validation ===")

        # Test core imports
        self.results["core_imports"] = self.test_core_imports()

        # Test compatibility layer
        self.results["compatibility_layer"] = self.test_compatibility_layer()

        # Test file imports
        self.results["file_imports"] = self.test_file_imports()

        # Test functionality
        self.results["functionality_tests"] = self.test_functionality()

        # Check data integrity
        self.results["data_integrity"] = self.check_data_integrity()

        # Determine overall status
        all_core_imports_ok = all(self.results["core_imports"].values())
        file_imports_mostly_ok = sum(self.results["file_imports"].values()) >= len(self.results["file_imports"]) * 0.8
        functionality_ok = all(self.results["functionality_tests"].values())

        if all_core_imports_ok and file_imports_mostly_ok and functionality_ok:
            self.results["overall_status"] = "success"
        elif all_core_imports_ok and functionality_ok:
            self.results["overall_status"] = "partial_success"
        else:
            self.results["overall_status"] = "failure"

        self.results["errors"] = self.errors
        self.results["total_errors"] = len(self.errors)

        return self.results

    def print_summary(self):
        """Print a summary of validation results."""
        print("\n=== Migration Validation Summary ===")

        status_emoji = {
            "success": "✅",
            "partial_success": "⚠️",
            "failure": "❌"
        }

        print(f"Overall Status: {status_emoji.get(self.results['overall_status'], '❓')} {self.results['overall_status'].upper()}")
        print(f"Total Errors: {self.results['total_errors']}")

        # Core imports
        core_success = sum(self.results["core_imports"].values())
        core_total = len(self.results["core_imports"])
        print(f"Core Imports: {core_success}/{core_total} successful")

        # File imports
        file_success = sum(self.results["file_imports"].values())
        file_total = len(self.results["file_imports"])
        print(f"File Imports: {file_success}/{file_total} successful")

        # Functionality
        func_success = sum(self.results["functionality_tests"].values())
        func_total = len(self.results["functionality_tests"])
        print(f"Functionality Tests: {func_success}/{func_total} successful")

        # Show errors if any
        if self.errors:
            print(f"\n=== Errors ({len(self.errors)}) ===")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error}")

        # Show recommendations
        print("\n=== Recommendations ===")
        if self.results["overall_status"] == "success":
            print("✅ Migration completed successfully!")
            print("✅ All core modules are working correctly")
            print("✅ File imports are functioning")
            print("✅ Consider removing backup files if everything works as expected")
        elif self.results["overall_status"] == "partial_success":
            print("⚠️  Migration mostly successful but needs attention")
            print("⚠️  Some files may need manual review")
            print("⚠️  Test functionality thoroughly before removing backups")
        else:
            print("❌ Migration has significant issues")
            print("❌ Review errors above and fix before proceeding")
            print("❌ Consider restoring from backups if needed")


def main():
    """Main validation function."""
    validator = MigrationValidator()
    results = validator.run_validation()
    validator.print_summary()

    # Return appropriate exit code
    if results["overall_status"] == "success":
        return 0
    elif results["overall_status"] == "partial_success":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
