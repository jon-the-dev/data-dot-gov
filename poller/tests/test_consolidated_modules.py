#!/usr/bin/env python3
"""
Comprehensive test suite for consolidated modules.
Tests all core components for functionality and backward compatibility.
"""

import json
import os
import sys
import tempfile
import threading
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestResults:
    """Track test results and generate reports."""

    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []

    def add_result(
        self, test_name: str, passed: bool, message: str = "", details: Any = None
    ):
        """Add a test result."""
        self.results[test_name] = {
            "passed": passed,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        if not passed:
            self.errors.append(f"{test_name}: {message}")

    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        passed_tests = sum(1 for r in self.results.values() if r["passed"])
        total_tests = len(self.results)

        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (
                    f"{(passed_tests/total_tests)*100:.1f}%"
                    if total_tests > 0
                    else "0%"
                ),
            },
            "results": self.results,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": datetime.now().isoformat(),
        }


class ModuleTester:
    """Main testing class for all consolidated modules."""

    def __init__(self):
        self.results = TestResults()
        self.temp_dir = None

    def setup_test_environment(self):
        """Set up temporary test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="senate_test_")
        print(f"Test environment: {self.temp_dir}")

    def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_imports(self):
        """Test that all modules can be imported without errors."""
        print("\n=== Testing Module Imports ===")

        import_tests = [
            # Core API modules
            ("core.api.rate_limiter", "RateLimiter"),
            ("core.api.base", "BaseAPI"),
            ("core.api.congress", "CongressGovAPI"),
            ("core.api.senate", "SenateGovAPI"),
            # Core models
            ("core.models.base", "BaseRecord"),
            ("core.models.enums", "Party"),
            ("core.models.member", "Member"),
            ("core.models.bill", "Bill"),
            ("core.models.vote", "Vote"),
            ("core.models.lobbying", "LobbyingFiling"),
            # Storage modules
            ("core.storage.file_storage", "FileStorage"),
            ("core.storage.compressed", "CompressedStorage"),
            ("core.storage.database", "DatabaseStorage"),
            # Fetchers
            ("fetchers.unified_fetcher", "UnifiedFetcher"),
            ("fetchers.specialized_fetcher", "SpecializedFetcher"),
            # Analyzers
            ("analyzers.party_analytics", "PartyAnalyzer"),
            ("analyzers.geographic_analytics", "GeographicAnalyzer"),
            ("analyzers.temporal_analytics", "TemporalAnalyzer"),
            ("analyzers.topic_analytics", "TopicAnalyzer"),
            ("analyzers.orchestrator", "AnalysisOrchestrator"),
        ]

        for module_path, class_name in import_tests:
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.results.add_result(
                    f"import_{module_path}", True, f"Successfully imported {class_name}"
                )
                print(f"✓ {module_path}.{class_name}")
            except Exception as e:
                self.results.add_result(
                    f"import_{module_path}",
                    False,
                    f"Failed to import {class_name}: {str(e)}",
                )
                print(f"✗ {module_path}.{class_name}: {str(e)}")

    def test_rate_limiter(self):
        """Test RateLimiter functionality."""
        print("\n=== Testing RateLimiter ===")

        try:
            from core.api.rate_limiter import RateLimiter

            # Test basic rate limiting
            limiter = RateLimiter(max_requests=5, time_window=1.0)

            # Test that we can make requests within limit
            start_time = time.time()
            for i in range(5):
                limiter.wait_if_needed()
            elapsed = time.time() - start_time

            self.results.add_result(
                "rate_limiter_basic",
                elapsed < 0.5,
                f"Basic rate limiting test completed in {elapsed:.3f}s",
            )

            # Test that rate limiting kicks in
            start_time = time.time()
            limiter.wait_if_needed()  # This should cause a delay
            elapsed = time.time() - start_time

            self.results.add_result(
                "rate_limiter_delay",
                elapsed >= 0.5,
                f"Rate limiting delay test: {elapsed:.3f}s delay",
            )

            # Test thread safety
            results = []

            def worker():
                for _ in range(3):
                    start = time.time()
                    limiter.wait_if_needed()
                    results.append(time.time() - start)

            threads = [threading.Thread(target=worker) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.results.add_result(
                "rate_limiter_threading",
                len(results) == 9,
                f"Thread safety test: {len(results)} requests completed",
            )

            print("✓ RateLimiter tests passed")

        except Exception as e:
            self.results.add_result(
                "rate_limiter_basic", False, f"RateLimiter test failed: {str(e)}"
            )
            print(f"✗ RateLimiter test failed: {str(e)}")

    def test_data_models(self):
        """Test Pydantic data models."""
        print("\n=== Testing Data Models ===")

        try:
            from core.models.bill import Bill
            from core.models.enums import Party
            from core.models.member import Member
            from core.models.vote import Vote

            # Test Member model
            member_data = {
                "bioguide_id": "A000001",
                "name": "John Doe",
                "first_name": "John",
                "last_name": "Doe",
                "party": "Democratic",
                "state": "CA",
                "chamber": "house",
            }

            member = Member(**member_data)
            self.results.add_result(
                "model_member_creation",
                member.bioguide_id == "A000001" and member.party == Party.DEMOCRATIC,
                f"Member model created successfully: {member.full_name}",
            )

            # Test JSON serialization
            member_json = member.model_dump()
            member_reconstructed = Member(**member_json)
            self.results.add_result(
                "model_member_serialization",
                member_reconstructed.bioguide_id == member.bioguide_id,
                "Member model serialization/deserialization successful",
            )

            # Test Bill model
            bill_data = {
                "congress": 118,
                "bill_type": "HR",
                "number": "1234",
                "title": "Test Bill",
                "introduced_date": "2024-01-15",
            }

            bill = Bill(**bill_data)
            expected_bill_id = "118_hr_1234"  # The validator converts to lowercase
            self.results.add_result(
                "model_bill_creation",
                bill.bill_id == expected_bill_id,
                f"Bill model created successfully: {bill.bill_id}",
            )

            # Test Vote model
            vote_data = {
                "congress": 118,
                "chamber": "house",
                "session": 1,
                "roll_call": 100,
                "question": "On Passage",
                "result": "Passed",
            }

            vote = Vote(**vote_data)
            expected_vote_id = "118_house_1_100"
            self.results.add_result(
                "model_vote_creation",
                vote.vote_id == expected_vote_id,
                f"Vote model created successfully: {vote.vote_id}",
            )

            print("✓ Data model tests passed")

        except Exception as e:
            self.results.add_result(
                "model_tests", False, f"Data model tests failed: {str(e)}"
            )
            print(f"✗ Data model tests failed: {str(e)}")

    def test_storage_modules(self):
        """Test storage module functionality."""
        print("\n=== Testing Storage Modules ===")

        try:
            from core.storage.file_storage import FileStorage

            # Test file storage
            storage = FileStorage(base_dir=self.temp_dir)

            # Test individual record storage
            test_data = {"id": "test_001", "name": "Test Record", "value": 42}
            storage.save_individual_record("test_collection", "test_001", test_data)

            # Test loading individual record
            loaded_data = storage.load_individual_record("test_collection", "test_001")
            self.results.add_result(
                "storage_individual_record",
                loaded_data and loaded_data["id"] == "test_001",
                "Individual record storage and retrieval successful",
            )

            # Test bulk storage
            bulk_data = [
                {"id": "bulk_001", "value": 1},
                {"id": "bulk_002", "value": 2},
                {"id": "bulk_003", "value": 3},
            ]
            filepath = storage.save_bulk_records(
                bulk_data, "bulk_collection", "test_bulk.json"
            )

            # Test bulk loading
            loaded_bulk = storage.load_records("bulk_collection", "test_bulk.json")
            self.results.add_result(
                "storage_bulk_data",
                loaded_bulk and len(loaded_bulk) == 3,
                f"Bulk storage successful: {len(loaded_bulk) if loaded_bulk else 0} records",
            )

            # Test index loading (indexes are created automatically)
            index = storage.load_index("test_collection")
            self.results.add_result(
                "storage_index",
                isinstance(index, (dict, type(None))),
                f"Index loading successful: {type(index)}",
            )

            print("✓ Storage module tests passed")

        except Exception as e:
            self.results.add_result(
                "storage_tests", False, f"Storage module tests failed: {str(e)}"
            )
            print(f"✗ Storage module tests failed: {str(e)}")

    def test_api_modules(self):
        """Test API module functionality (without making real requests)."""
        print("\n=== Testing API Modules ===")

        try:
            from core.api.congress import CongressGovAPI
            from core.api.senate import SenateGovAPI

            # Test CongressGovAPI initialization
            congress_api = CongressGovAPI(api_key="test_key", max_workers=1)
            self.results.add_result(
                "api_congress_init",
                congress_api.api_key == "test_key",
                "CongressGovAPI initialization successful",
            )

            # Test basic functionality (without making actual requests)
            # Check that the API client has necessary attributes
            has_api_key = hasattr(congress_api, "api_key")
            has_base_url = hasattr(congress_api, "base_url")
            self.results.add_result(
                "api_congress_attributes",
                has_api_key and has_base_url,
                f"CongressGovAPI has required attributes: api_key={has_api_key}, base_url={has_base_url}",
            )

            # Test SenateGovAPI initialization
            senate_api = SenateGovAPI(username="test_user", password="test_pass")
            self.results.add_result(
                "api_senate_init",
                hasattr(senate_api, "username"),
                "SenateGovAPI initialization successful",
            )

            print("✓ API module tests passed")

        except Exception as e:
            self.results.add_result(
                "api_tests", False, f"API module tests failed: {str(e)}"
            )
            print(f"✗ API module tests failed: {str(e)}")

    def test_fetcher_modules(self):
        """Test fetcher module functionality."""
        print("\n=== Testing Fetcher Modules ===")

        try:
            from fetchers.specialized_fetcher import SpecializedFetcher
            from fetchers.unified_fetcher import UnifiedFetcher

            # Test UnifiedFetcher initialization
            unified_fetcher = UnifiedFetcher(
                data_dir=self.temp_dir, api_key="test_key", max_workers=1
            )

            self.results.add_result(
                "fetcher_unified_init",
                hasattr(unified_fetcher, "congress_api"),
                "UnifiedFetcher initialization successful",
            )

            # Test SpecializedFetcher initialization
            specialized_fetcher = SpecializedFetcher(
                data_dir=self.temp_dir, api_key="test_key"
            )

            self.results.add_result(
                "fetcher_specialized_init",
                hasattr(specialized_fetcher, "storage"),
                "SpecializedFetcher initialization successful",
            )

            print("✓ Fetcher module tests passed")

        except Exception as e:
            self.results.add_result(
                "fetcher_tests", False, f"Fetcher module tests failed: {str(e)}"
            )
            print(f"✗ Fetcher module tests failed: {str(e)}")

    def test_analyzer_modules(self):
        """Test analyzer module functionality."""
        print("\n=== Testing Analyzer Modules ===")

        try:
            from analyzers.geographic_analytics import GeographicAnalyzer
            from analyzers.orchestrator import AnalysisOrchestrator
            from analyzers.party_analytics import PartyAnalyzer
            from analyzers.temporal_analytics import TemporalAnalyzer
            from analyzers.topic_analytics import TopicAnalyzer

            # Create test data
            test_members = [
                {"bioguide_id": "A001", "party": "Democratic", "state": "CA"},
                {"bioguide_id": "B001", "party": "Republican", "state": "TX"},
                {"bioguide_id": "C001", "party": "Democratic", "state": "NY"},
            ]

            test_votes = [
                {
                    "vote_id": "118_1_1",
                    "positions": [
                        {"bioguide_id": "A001", "vote_position": "Yea"},
                        {"bioguide_id": "B001", "vote_position": "Nay"},
                        {"bioguide_id": "C001", "vote_position": "Yea"},
                    ],
                }
            ]

            # Test PartyAnalyzer
            party_analyzer = PartyAnalyzer(base_dir=self.temp_dir)
            # Test that analyzer has necessary attributes and methods
            has_storage = hasattr(party_analyzer, "storage")
            has_members = hasattr(party_analyzer, "members")
            has_method = hasattr(party_analyzer, "calculate_party_unity_scores")
            self.results.add_result(
                "analyzer_party",
                has_storage and has_members and has_method,
                f"PartyAnalyzer initialized with required attributes: storage={has_storage}, members={has_members}, method={has_method}",
            )

            # Test GeographicAnalyzer
            geo_analyzer = GeographicAnalyzer(base_dir=self.temp_dir)
            # Test that analyzer has necessary attributes and methods
            has_storage = hasattr(geo_analyzer, "storage")
            has_members = hasattr(geo_analyzer, "members")
            has_method = hasattr(geo_analyzer, "build_state_delegations")
            self.results.add_result(
                "analyzer_geographic",
                has_storage and has_members and has_method,
                f"GeographicAnalyzer initialized with required attributes: storage={has_storage}, members={has_members}, method={has_method}",
            )

            # Test TemporalAnalyzer
            temporal_analyzer = TemporalAnalyzer(base_dir=self.temp_dir)
            # Test that analyzer has necessary attributes and methods
            has_storage = hasattr(temporal_analyzer, "storage")
            has_data = hasattr(temporal_analyzer, "bills_data")
            has_method = hasattr(temporal_analyzer, "analyze_monthly_trends")
            self.results.add_result(
                "analyzer_temporal",
                has_storage and has_data and has_method,
                f"TemporalAnalyzer initialized with required attributes: storage={has_storage}, data={has_data}, method={has_method}",
            )

            # Test TopicAnalyzer
            topic_analyzer = TopicAnalyzer()
            test_bills = [
                {"title": "Healthcare Reform Act", "policy_area": "Health"},
                {"title": "Defense Authorization", "policy_area": "Defense"},
            ]
            categorization = topic_analyzer.categorize_bills(test_bills)
            self.results.add_result(
                "analyzer_topic",
                len(categorization) > 0,
                f"Topic analysis successful: {len(categorization)} categories",
            )

            # Test AnalysisOrchestrator
            orchestrator = AnalysisOrchestrator(base_dir=self.temp_dir)
            self.results.add_result(
                "analyzer_orchestrator",
                hasattr(orchestrator, "party_analyzer"),
                "AnalysisOrchestrator initialization successful",
            )

            print("✓ Analyzer module tests passed")

        except Exception as e:
            self.results.add_result(
                "analyzer_tests", False, f"Analyzer module tests failed: {str(e)}"
            )
            print(f"✗ Analyzer module tests failed: {str(e)}")

    def test_backward_compatibility(self):
        """Test backward compatibility with old imports."""
        print("\n=== Testing Backward Compatibility ===")

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            try:
                # Test if old script imports still work
                compatibility_tests = [
                    # Old direct imports that should still work
                    ("gov_data_analyzer", "API connections"),
                    ("categorize_bills", "Bill categorization"),
                    ("analyze_bill_sponsors", "Sponsor analysis"),
                ]

                for script_name, description in compatibility_tests:
                    try:
                        # Try to import the old script
                        module = __import__(script_name)
                        self.results.add_result(
                            f"compatibility_{script_name}",
                            True,
                            f"{description} script imports successfully",
                        )
                        print(f"✓ {script_name} imports successfully")
                    except Exception as e:
                        self.results.add_result(
                            f"compatibility_{script_name}",
                            False,
                            f"{description} script import failed: {str(e)}",
                        )
                        print(f"✗ {script_name} import failed: {str(e)}")

                # Check for deprecation warnings
                if w:
                    for warning in w:
                        self.results.add_warning(
                            f"Deprecation warning: {warning.message}"
                        )

            except Exception as e:
                self.results.add_result(
                    "compatibility_tests",
                    False,
                    f"Compatibility tests failed: {str(e)}",
                )
                print(f"✗ Compatibility tests failed: {str(e)}")

    def test_migration_verification(self):
        """Run the migration verification script."""
        print("\n=== Testing Migration Verification ===")

        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, "migrations/verify_migration.py"],
                check=False,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            success = result.returncode == 0
            self.results.add_result(
                "migration_verification",
                success,
                f"Migration verification {'passed' if success else 'failed'}: {result.stdout[:200]}...",
            )

            if success:
                print("✓ Migration verification passed")
            else:
                print(f"✗ Migration verification failed: {result.stderr}")

        except Exception as e:
            self.results.add_result(
                "migration_verification",
                False,
                f"Migration verification error: {str(e)}",
            )
            print(f"✗ Migration verification error: {str(e)}")

    def run_all_tests(self):
        """Run all test suites."""
        print("Starting Comprehensive Module Testing")
        print("=" * 50)

        self.setup_test_environment()

        try:
            # Run all test suites
            self.test_imports()
            self.test_rate_limiter()
            self.test_data_models()
            self.test_storage_modules()
            self.test_api_modules()
            self.test_fetcher_modules()
            self.test_analyzer_modules()
            self.test_backward_compatibility()
            self.test_migration_verification()

            # Generate final report
            report = self.results.generate_report()

            print("\n" + "=" * 50)
            print("TEST RESULTS SUMMARY")
            print("=" * 50)
            print(f"Total Tests: {report['summary']['total_tests']}")
            print(f"Passed: {report['summary']['passed']}")
            print(f"Failed: {report['summary']['failed']}")
            print(f"Success Rate: {report['summary']['success_rate']}")

            if report["errors"]:
                print(f"\nErrors ({len(report['errors'])}):")
                for error in report["errors"]:
                    print(f"  ✗ {error}")

            if report["warnings"]:
                print(f"\nWarnings ({len(report['warnings'])}):")
                for warning in report["warnings"]:
                    print(f"  ⚠ {warning}")

            # Save detailed report
            report_file = project_root / "test_results.json"
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to: {report_file}")

            return report

        finally:
            self.cleanup_test_environment()


if __name__ == "__main__":
    tester = ModuleTester()
    report = tester.run_all_tests()

    # Exit with error code if tests failed
    if report["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)
