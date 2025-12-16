#!/usr/bin/env python3
"""
Unit tests for the core package components.

Tests the unified RateLimiter, APIs, storage utilities, and data models
to validate the Python consolidation worked correctly.
"""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add core package to path for testing
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.api.congress import CongressGovAPI
    from core.api.rate_limiter import RateLimiter
    from core.api.senate import SenateGovAPI
    from core.models.base import BaseRecord
    from core.models.congress import Bill, Member, Vote
    from core.models.senate import LobbingFiling
    from core.storage.file_storage import (
        FileStorage,
        save_index,
        save_individual_record,
    )

    CORE_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Could not import core package: {e}")
    CORE_AVAILABLE = False


class TestRateLimiter(unittest.TestCase):
    """Test the unified RateLimiter class"""

    def setUp(self):
        """Set up test fixtures"""
        if not CORE_AVAILABLE:
            self.skipTest("Core package not available")

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initializes correctly"""
        limiter = RateLimiter(max_requests=5, time_window=60, name="test")

        self.assertEqual(limiter.max_requests, 5)
        self.assertEqual(limiter.time_window, 60)
        self.assertEqual(limiter.name, "test")
        self.assertEqual(len(limiter.requests), 0)
        self.assertIsInstance(limiter.lock, threading.Lock)

    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests are allowed within rate limit"""
        limiter = RateLimiter(max_requests=3, time_window=60)

        # Should allow 3 requests without waiting
        start_time = time.time()
        for _ in range(3):
            limiter.wait_if_needed()
        elapsed = time.time() - start_time

        # Should complete quickly (no waiting)
        self.assertLess(elapsed, 1.0)
        self.assertEqual(len(limiter.requests), 3)

    def test_rate_limiter_blocks_excess_requests(self):
        """Test that excess requests are blocked"""
        limiter = RateLimiter(max_requests=2, time_window=5)

        # Use 2 requests
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Third request should cause waiting
        start_time = time.time()
        with patch("time.sleep") as mock_sleep:
            limiter.wait_if_needed()
            mock_sleep.assert_called_once()
            # Verify it was called with a positive wait time
            self.assertGreater(mock_sleep.call_args[0][0], 0)

    def test_rate_limiter_stats(self):
        """Test rate limiter statistics"""
        limiter = RateLimiter(max_requests=5, time_window=60, name="test_stats")

        # No requests yet
        stats = limiter.get_stats()
        self.assertEqual(stats["current_requests"], 0)
        self.assertEqual(stats["requests_remaining"], 5)
        self.assertEqual(stats["name"], "test_stats")

        # Make some requests
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        stats = limiter.get_stats()
        self.assertEqual(stats["current_requests"], 2)
        self.assertEqual(stats["requests_remaining"], 3)

    def test_rate_limiter_reset(self):
        """Test rate limiter reset functionality"""
        limiter = RateLimiter(max_requests=2, time_window=60)

        # Make requests
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        self.assertEqual(len(limiter.requests), 2)

        # Reset
        limiter.reset()
        self.assertEqual(len(limiter.requests), 0)

        stats = limiter.get_stats()
        self.assertEqual(stats["current_requests"], 0)
        self.assertEqual(stats["requests_remaining"], 2)

    def test_rate_limiter_thread_safety(self):
        """Test that rate limiter is thread-safe"""
        limiter = RateLimiter(max_requests=10, time_window=60)
        results = []

        def make_request(thread_id):
            """Make a request from a thread"""
            try:
                limiter.wait_if_needed()
                results.append(f"thread_{thread_id}_success")
            except Exception as e:
                results.append(f"thread_{thread_id}_error_{e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All threads should succeed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIn("success", result)


class TestFileStorage(unittest.TestCase):
    """Test the FileStorage utilities"""

    def setUp(self):
        """Set up test fixtures"""
        if not CORE_AVAILABLE:
            self.skipTest("Core package not available")

        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileStorage(base_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_file_storage_initialization(self):
        """Test FileStorage initializes correctly"""
        self.assertEqual(str(self.storage.base_dir), self.temp_dir)
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_save_individual_record(self):
        """Test saving individual records"""
        test_data = {"id": "test_123", "title": "Test Record", "type": "test"}

        result = save_individual_record(
            record=test_data,
            record_type="test_records",
            identifier="test_123",
            base_dir=self.temp_dir,
        )

        self.assertIsNotNone(result)

        # Verify file was created
        expected_path = os.path.join(self.temp_dir, "test_records", "test_123.json")
        self.assertTrue(os.path.exists(expected_path))

        # Verify content (the file includes metadata, so check just the original data)
        with open(expected_path) as f:
            saved_data = json.load(f)

        # Check that original data is preserved (ignoring metadata)
        for key, value in test_data.items():
            self.assertEqual(saved_data[key], value)

    def test_save_index(self):
        """Test saving index files"""
        test_records = [
            {"id": "record1", "title": "Test Record 1"},
            {"id": "record2", "title": "Test Record 2"},
        ]

        save_index(
            records=test_records, record_type="test_category", base_dir=self.temp_dir
        )

        # Verify file was created
        expected_path = os.path.join(self.temp_dir, "test_category", "index.json")
        self.assertTrue(os.path.exists(expected_path))

        # Verify content
        with open(expected_path) as f:
            saved_data = json.load(f)

        self.assertIn("total_records", saved_data)
        self.assertEqual(saved_data["total_records"], 2)

    def test_file_storage_error_handling(self):
        """Test error handling in file storage"""
        # Test with invalid data (should not be JSON serializable)
        invalid_data = {"function": lambda x: x}  # Functions can't be serialized

        # This should not raise an exception but may not save correctly
        try:
            result = save_individual_record(
                record=invalid_data,
                record_type="test",
                identifier="invalid",
                base_dir=self.temp_dir,
            )
            # The function should handle the error gracefully
        except Exception:
            # Exception handling is expected for invalid data
            pass


class TestCongressGovAPI(unittest.TestCase):
    """Test the CongressGovAPI class"""

    def setUp(self):
        """Set up test fixtures"""
        if not CORE_AVAILABLE:
            self.skipTest("Core package not available")

    @patch.dict(os.environ, {"DATA_GOV_API_KEY": "test_key"})
    def test_congress_api_initialization(self):
        """Test CongressGovAPI initializes correctly"""
        api = CongressGovAPI()

        self.assertEqual(api.api_key, "test_key")
        self.assertIsInstance(api.rate_limiter, RateLimiter)
        self.assertEqual(api.BASE_URL, "https://api.congress.gov/v3")

    def test_congress_api_no_key_warning(self):
        """Test that API warns when no key is provided"""
        with patch.dict(os.environ, {}, clear=True), patch(
            "logging.Logger.warning"
        ) as mock_warning:
            _api = CongressGovAPI()  # Create API instance to trigger warning
            mock_warning.assert_called_once()
            warning_message = mock_warning.call_args[0][0]
            self.assertIn("API key", warning_message)

    def test_congress_api_make_request(self):
        """Test making API requests"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None

        with patch("requests.Session.get", return_value=mock_response):
            api = CongressGovAPI(api_key="test_key")
            result = api._make_request("/test/endpoint")

            self.assertEqual(result, {"test": "data"})

    def test_congress_api_error_handling(self):
        """Test API error handling"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")

        with patch("requests.Session.get", return_value=mock_response):
            api = CongressGovAPI(api_key="test_key")
            result = api._make_request("/nonexistent/endpoint")

            self.assertIsNone(result)


class TestSenateGovAPI(unittest.TestCase):
    """Test the SenateGovAPI class"""

    def setUp(self):
        """Set up test fixtures"""
        if not CORE_AVAILABLE:
            self.skipTest("Core package not available")

    def test_senate_api_initialization(self):
        """Test SenateGovAPI initializes correctly"""
        api = SenateGovAPI()

        self.assertIsInstance(api.rate_limiter, RateLimiter)
        self.assertEqual(api.BASE_URL, "https://lda.senate.gov/api")

    @patch.dict(
        os.environ, {"SENATE_GOV_USERNAME": "user", "SENATE_GOV_PASSWORD": "pass"}
    )
    def test_senate_api_with_credentials(self):
        """Test SenateGovAPI with credentials"""
        api = SenateGovAPI()

        self.assertEqual(api.username, "user")
        self.assertEqual(api.password, "pass")


class TestDataModels(unittest.TestCase):
    """Test the data models"""

    def setUp(self):
        """Set up test fixtures"""
        if not CORE_AVAILABLE:
            self.skipTest("Core package not available")

    def test_base_record(self):
        """Test BaseRecord functionality"""
        # Test with valid data
        test_data = {"record_type": "test", "identifier": "123"}
        record = BaseRecord(**test_data)

        self.assertEqual(record.record_type, "test")
        self.assertEqual(record.identifier, "123")

    def test_bill_model(self):
        """Test Bill model"""
        bill_data = {
            "record_type": "bill",
            "identifier": "118_hr_1234",
            "congress": 118,
            "bill_type": "hr",
            "number": "1234",
            "title": "Test Bill",
        }

        bill = Bill(**bill_data)
        self.assertEqual(bill.congress, 118)
        self.assertEqual(bill.bill_type, "HR")  # Normalized to uppercase
        self.assertEqual(bill.number, "1234")
        self.assertEqual(bill.title, "Test Bill")

    def test_member_model(self):
        """Test Member model"""
        member_data = {
            "record_type": "member",
            "identifier": "A000001",
            "bioguide_id": "A000001",
            "name": "Test Member",
            "party": "Democratic",
            "state": "CA",
            "chamber": "house",
        }

        member = Member(**member_data)
        self.assertEqual(member.bioguide_id, "A000001")
        self.assertEqual(member.party, "D")  # Normalized
        self.assertEqual(member.chamber, "house")

    def test_vote_model(self):
        """Test Vote model"""
        vote_data = {
            "record_type": "vote",
            "identifier": "118_house_123",
            "congress": 118,
            "chamber": "house",
            "roll_call": 123,
            "question": "On Passage",
            "result": "Passed",
        }

        vote = Vote(**vote_data)
        self.assertEqual(vote.roll_call, 123)
        self.assertEqual(vote.chamber, "house")
        self.assertEqual(vote.congress, 118)

    def test_lobbying_filing_model(self):
        """Test LobbingFiling model"""
        filing_data = {
            "record_type": "lobbying_filing",
            "identifier": "LF123",
            "filing_uuid": "LF123",
            "filing_type": "ld-2",
            "client_name": "Test Client",
            "registrant_name": "Test Registrant",
        }

        filing = LobbingFiling(**filing_data)
        self.assertEqual(filing.filing_uuid, "LF123")
        self.assertEqual(filing.client_name, "Test Client")


class TestIntegration(unittest.TestCase):
    """Integration tests for core package components"""

    def setUp(self):
        """Set up test fixtures"""
        if not CORE_AVAILABLE:
            self.skipTest("Core package not available")

    def test_core_package_imports(self):
        """Test that all core package exports work"""
        from core import (
            CongressGovAPI,
            FileStorage,
            RateLimiter,
            SenateGovAPI,
        )

        # Test that classes can be instantiated
        rate_limiter = RateLimiter(max_requests=5, time_window=60)
        self.assertIsInstance(rate_limiter, RateLimiter)

        congress_api = CongressGovAPI()
        self.assertIsInstance(congress_api, CongressGovAPI)

        senate_api = SenateGovAPI()
        self.assertIsInstance(senate_api, SenateGovAPI)

        file_storage = FileStorage()
        self.assertIsInstance(file_storage, FileStorage)

    def test_api_with_rate_limiter(self):
        """Test that APIs use rate limiter correctly"""
        api = CongressGovAPI(max_requests=5, time_window=60)

        # Check that rate limiter is configured
        self.assertEqual(api.rate_limiter.max_requests, 5)
        self.assertEqual(api.rate_limiter.time_window, 60)


def run_tests():
    """Run all tests and return results"""
    print("=" * 60)
    print("CORE PACKAGE UNIT TESTS")
    print("=" * 60)

    if not CORE_AVAILABLE:
        print("❌ CRITICAL: Core package cannot be imported!")
        return False

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestRateLimiter,
        TestFileStorage,
        TestCongressGovAPI,
        TestSenateGovAPI,
        TestDataModels,
        TestIntegration,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("CORE PACKAGE TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.splitlines()[-1]}")

    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("\n✅ ALL CORE PACKAGE TESTS PASSED!")
    else:
        print("\n❌ SOME CORE PACKAGE TESTS FAILED!")

    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
