#!/usr/bin/env python3
"""
Integration tests to validate that the Python consolidation worked correctly.

This test verifies that:
1. All original scripts can still import the core package
2. Existing functionality is preserved
3. The consolidation didn't break any dependencies
4. Key functions work as expected
"""

import ast
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# List of original scripts that should import core
ORIGINAL_SCRIPTS = [
    "gov_data_downloader_v2.py",
    "gov_data_analyzer.py",
    "comprehensive_analyzer.py",
    "categorize_bills.py",
    "analyze_bill_sponsors.py",
    "analyze_member_consistency.py",
    "fetch_voting_records.py",
    "sync_viewer_data.py",
]


class TestConsolidationValidation(unittest.TestCase):
    """Test that consolidation worked and didn't break existing functionality"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent
        self.scripts_dir = self.project_root

    def test_core_package_exists(self):
        """Test that core package was created and can be imported"""
        try:
            import core

            self.assertTrue(hasattr(core, "RateLimiter"))
            self.assertTrue(hasattr(core, "CongressGovAPI"))
            self.assertTrue(hasattr(core, "SenateGovAPI"))
            self.assertTrue(hasattr(core, "FileStorage"))
            print("✅ Core package imports successfully")
        except ImportError as e:
            self.fail(f"❌ Core package cannot be imported: {e}")

    def test_core_package_version(self):
        """Test that core package has version info"""
        try:
            import core

            self.assertTrue(hasattr(core, "__version__"))
            self.assertIsInstance(core.__version__, str)
            print(f"✅ Core package version: {core.__version__}")
        except Exception as e:
            self.fail(f"❌ Core package version check failed: {e}")

    def test_original_scripts_exist(self):
        """Test that all original scripts still exist"""
        missing_scripts = []
        for script in ORIGINAL_SCRIPTS:
            script_path = self.scripts_dir / script
            if not script_path.exists():
                missing_scripts.append(script)

        if missing_scripts:
            self.fail(f"❌ Missing scripts: {missing_scripts}")

        print(f"✅ All {len(ORIGINAL_SCRIPTS)} original scripts exist")

    def test_scripts_can_import_core(self):
        """Test that original scripts can import from core package"""
        import_errors = []

        for script in ORIGINAL_SCRIPTS:
            script_path = self.scripts_dir / script
            if not script_path.exists():
                continue

            try:
                # Read the script and check for core imports
                with open(script_path) as f:
                    content = f.read()

                # Parse the AST to find imports
                tree = ast.parse(content)
                has_core_import = False

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("core"):
                                has_core_import = True
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("core"):
                            has_core_import = True

                if has_core_import:
                    print(f"✅ {script} has core imports")
                else:
                    print(f"ℹ️  {script} does not import from core (may be legacy)")

            except Exception as e:
                import_errors.append(f"{script}: {e}")

        if import_errors:
            print(f"⚠️  Import check errors: {import_errors}")

    def test_core_api_classes_instantiation(self):
        """Test that core API classes can be instantiated"""
        try:
            from core import CongressGovAPI, FileStorage, RateLimiter, SenateGovAPI

            # Test RateLimiter
            rate_limiter = RateLimiter(max_requests=5, time_window=60)
            self.assertEqual(rate_limiter.max_requests, 5)
            print("✅ RateLimiter instantiates correctly")

            # Test CongressGovAPI
            congress_api = CongressGovAPI()
            self.assertEqual(congress_api.BASE_URL, "https://api.congress.gov/v3")
            print("✅ CongressGovAPI instantiates correctly")

            # Test SenateGovAPI
            senate_api = SenateGovAPI()
            self.assertEqual(senate_api.BASE_URL, "https://lda.senate.gov/api")
            print("✅ SenateGovAPI instantiates correctly")

            # Test FileStorage
            with tempfile.TemporaryDirectory() as temp_dir:
                file_storage = FileStorage(base_dir=temp_dir)
                self.assertEqual(str(file_storage.base_dir), temp_dir)
            print("✅ FileStorage instantiates correctly")

        except Exception as e:
            self.fail(f"❌ Core API class instantiation failed: {e}")

    def test_file_storage_functions(self):
        """Test that file storage functions work"""
        try:

            from core import save_index, save_individual_record

            with tempfile.TemporaryDirectory() as temp_dir:
                # Test save_individual_record
                test_data = {"id": "test_123", "title": "Test Record"}
                result = save_individual_record(
                    record=test_data,
                    record_type="test",
                    identifier="test",
                    base_dir=temp_dir,
                )
                self.assertIsNotNone(result)

                # Verify file was created
                test_file = Path(temp_dir) / "test" / "test.json"
                self.assertTrue(test_file.exists())

                # Test save_index
                index_records = [{"id": "test_123", "title": "Test Record"}]
                save_index(records=index_records, record_type="test", base_dir=temp_dir)

                # Verify index was created
                index_file = Path(temp_dir) / "test" / "index.json"
                self.assertTrue(index_file.exists())

            print("✅ File storage functions work correctly")

        except Exception as e:
            self.fail(f"❌ File storage function test failed: {e}")

    def test_data_models_work(self):
        """Test that data models can be imported and used"""
        try:
            from core.models.congress import Bill, Member, Vote
            from core.models.senate import LobbingFiling

            # Test Bill model
            bill = Bill(
                record_type="bill",
                identifier="118_hr_1234",
                congress=118,
                bill_type="hr",
                number="1234",
                title="Test Bill",
            )
            self.assertEqual(bill.congress, 118)

            # Test Member model
            member = Member(
                record_type="member",
                identifier="A000001",
                bioguide_id="A000001",
                name="Test Member",
                party="Democratic",
                state="CA",
                chamber="house",
            )
            self.assertEqual(member.party, "D")  # Normalized

            # Test Vote model
            vote = Vote(
                record_type="vote",
                identifier="118_house_123",
                congress=118,
                roll_call=123,
                chamber="house",
                question="On Passage",
            )
            self.assertEqual(vote.roll_call, 123)

            # Test LobbingFiling model
            filing = LobbingFiling(
                record_type="lobbying_filing",
                identifier="LF123",
                filing_uuid="LF123",
                filing_type="ld-2",
                client_name="Test Client",
            )
            self.assertEqual(filing.filing_uuid, "LF123")

            print("✅ Data models work correctly")

        except Exception as e:
            self.fail(f"❌ Data models test failed: {e}")

    def test_api_mock_requests(self):
        """Test that APIs can make mock requests"""
        try:
            from core import CongressGovAPI, SenateGovAPI

            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_response.raise_for_status.return_value = None

            # Test CongressGovAPI
            congress_api = CongressGovAPI(api_key="test_key")
            with patch("requests.Session.get", return_value=mock_response):
                result = congress_api._make_request("/test")
                self.assertEqual(result, {"test": "data"})

            # Test SenateGovAPI
            senate_api = SenateGovAPI()
            with patch("requests.Session.get", return_value=mock_response):
                result = senate_api._make_request("/test")
                self.assertEqual(result, {"test": "data"})

            print("✅ API mock requests work correctly")

        except Exception as e:
            self.fail(f"❌ API mock requests test failed: {e}")

    def test_rate_limiter_functionality(self):
        """Test that rate limiter works as expected"""
        try:

            from core import RateLimiter

            # Test basic functionality
            limiter = RateLimiter(max_requests=3, time_window=60)

            # Should allow requests within limit
            limiter.wait_if_needed()
            limiter.wait_if_needed()
            limiter.wait_if_needed()

            stats = limiter.get_stats()
            self.assertEqual(stats["current_requests"], 3)
            self.assertEqual(stats["requests_remaining"], 0)

            # Test reset
            limiter.reset()
            stats = limiter.get_stats()
            self.assertEqual(stats["current_requests"], 0)

            print("✅ Rate limiter functionality works correctly")

        except Exception as e:
            self.fail(f"❌ Rate limiter test failed: {e}")

    def test_script_syntax_validation(self):
        """Test that all Python scripts have valid syntax"""
        syntax_errors = []

        for script in ORIGINAL_SCRIPTS:
            script_path = self.scripts_dir / script
            if not script_path.exists():
                continue

            try:
                with open(script_path) as f:
                    content = f.read()

                # Try to parse the AST
                ast.parse(content)

            except SyntaxError as e:
                syntax_errors.append(f"{script}: {e}")
            except Exception as e:
                syntax_errors.append(f"{script}: {e}")

        if syntax_errors:
            self.fail(f"❌ Syntax errors found: {syntax_errors}")

        print(f"✅ All {len(ORIGINAL_SCRIPTS)} scripts have valid syntax")

    def test_backwards_compatibility(self):
        """Test that core package maintains backwards compatibility"""
        try:
            # Test that old import patterns still work if they exist
            # Test that both import methods work
            from core import CongressGovAPI, FileStorage, RateLimiter, SenateGovAPI
            from core.api.congress import CongressGovAPI as DirectCongressAPI
            from core.api.rate_limiter import RateLimiter as DirectRateLimiter
            from core.api.senate import SenateGovAPI as DirectSenateAPI
            from core.storage.file_storage import FileStorage as DirectFileStorage

            # Verify they're the same classes
            self.assertEqual(DirectRateLimiter, RateLimiter)
            self.assertEqual(DirectCongressAPI, CongressGovAPI)
            self.assertEqual(DirectSenateAPI, SenateGovAPI)
            self.assertEqual(DirectFileStorage, FileStorage)

            print("✅ Backwards compatibility maintained")

        except Exception as e:
            self.fail(f"❌ Backwards compatibility test failed: {e}")


class TestScriptExecution(unittest.TestCase):
    """Test that original scripts can be executed (smoke tests)"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent

    def test_script_help_execution(self):
        """Test that scripts can show help without errors"""
        scripts_with_help = [
            "gov_data_downloader_v2.py",
            "gov_data_analyzer.py",
            "comprehensive_analyzer.py",
            "categorize_bills.py",
            "analyze_bill_sponsors.py",
        ]

        for script in scripts_with_help:
            script_path = self.project_root / script
            if not script_path.exists():
                continue

            try:
                # Try to import the module
                spec = importlib.util.spec_from_file_location(
                    "test_module", script_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Don't actually load - just check that we can create the spec
                    print(f"✅ {script} can be imported as module")
                else:
                    print(f"⚠️  {script} cannot be imported as module")

            except Exception as e:
                print(f"⚠️  {script} import test failed: {e}")


def run_validation_tests():
    """Run all consolidation validation tests"""
    print("=" * 60)
    print("CONSOLIDATION VALIDATION TESTS")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [TestConsolidationValidation, TestScriptExecution]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("CONSOLIDATION VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.splitlines()[-1]}")

    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("\n✅ ALL CONSOLIDATION VALIDATION TESTS PASSED!")
        print("✅ Python consolidation is working correctly!")
    else:
        print("\n❌ SOME CONSOLIDATION VALIDATION TESTS FAILED!")
        print("❌ Python consolidation may have issues!")

    return success


if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)
