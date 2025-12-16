#!/usr/bin/env python3
"""Debug storage issue."""

import tempfile
import traceback

from core.storage.file_storage import FileStorage


def debug_storage():
    temp_dir = tempfile.mkdtemp(prefix="debug_storage_")
    print(f"Testing in: {temp_dir}")

    try:
        storage = FileStorage(base_dir=temp_dir)
        print("✓ FileStorage created")

        # Test individual record storage
        test_data = {"id": "test_001", "name": "Test Record", "value": 42}
        storage.save_individual_record(test_data, "test_collection", "test_001")
        print("✓ Individual record saved")

        # Test individual record loading
        loaded_data = storage.load_record("test_collection", "test_001")
        print(f"✓ Individual record loaded: {loaded_data is not None}")

        # Test bulk storage
        bulk_data = [
            {"id": "bulk_001", "value": 1},
            {"id": "bulk_002", "value": 2},
            {"id": "bulk_003", "value": 3},
        ]
        filepath = storage.save_bulk_records(
            bulk_data, "bulk_collection", "test_bulk.json"
        )
        print(f"✓ Bulk records saved to: {filepath}")

        # Test bulk loading
        loaded_bulk = storage.load_records("bulk_collection", "test_bulk.json")
        print(
            f"✓ Bulk records loaded: {len(loaded_bulk) if loaded_bulk else 0} records"
        )

        print("All storage tests passed!")

    except Exception as e:
        print(f"✗ Storage test failed: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    debug_storage()
