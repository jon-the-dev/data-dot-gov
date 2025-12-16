"""
Congressional Transparency Platform - Unified Storage Module

This module provides consolidated storage capabilities for the Congressional Transparency Platform,
including JSON file storage (bulk and individual), compressed storage, and database operations.

Key Features:
- Unified API for all storage operations
- Support for both bulk and individual record storage
- Gzip compression for space efficiency
- Database abstraction layer
- Thread-safe operations
- Progress tracking and resumable operations
- Data integrity checks

Usage:
    from core.storage import FileStorage, CompressedStorage, DatabaseStorage

    # File storage
    storage = FileStorage(base_dir="data")
    storage.save_bulk_records(records, "bills", "congress_118_bills.json")
    storage.save_individual_record(record, "bills", "118_HR_1555")

    # Compressed storage
    compressed = CompressedStorage(base_dir="data")
    compressed.save_record(record, "bills/118_HR_1555.json", compress=True)

    # Database storage
    db = DatabaseStorage(connection_string="postgresql://...")
    db.save_records(records, "bills")
"""

from .compressed import (
    CompressedStorage,
    load_compressed_record,
    save_compressed_record,
)
from .database import DatabaseConnection, DatabaseStorage
from .file_storage import (
    FileStorage,
    load_records,
    save_bulk_records,
    save_index,
    save_individual_record,
)

__all__ = [
    # File storage
    "FileStorage",
    "save_bulk_records",
    "save_individual_record",
    "save_index",
    "load_records",
    # Compressed storage
    "CompressedStorage",
    "save_compressed_record",
    "load_compressed_record",
    # Database storage
    "DatabaseStorage",
    "DatabaseConnection",
]

__version__ = "1.0.0"
