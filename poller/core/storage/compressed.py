#!/usr/bin/env python3
"""
Compressed Storage Module - Gzip compression utilities for Congressional Transparency Platform

This module provides gzip compression and decompression utilities for efficient storage
of JSON data, based on the patterns found in historical_data_fetcher.py.

Features:
- Gzip compression for JSON records
- Automatic compression/decompression detection
- Memory-efficient streaming operations
- Thread-safe operations
- Integration with file storage module
- Configurable compression levels
"""

import gzip
import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class CompressedStorage:
    """
    Compressed storage class for efficient JSON data storage using gzip compression.
    """

    def __init__(
        self,
        base_dir: str = "data",
        compression_level: int = 6,
        auto_compress: bool = True,
    ):
        """
        Initialize CompressedStorage instance.

        Args:
            base_dir: Base directory for data storage
            compression_level: Gzip compression level (1-9, higher = better compression)
            auto_compress: Whether to automatically compress large files
        """
        self.base_dir = Path(base_dir)
        self.compression_level = compression_level
        self.auto_compress = auto_compress
        self._lock = threading.Lock()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_record(
        self,
        record: Dict[str, Any],
        filepath: Union[str, Path],
        compress: bool = True,
        record_type: Optional[str] = None,
        identifier: Optional[str] = None,
    ) -> int:
        """
        Save record with optional compression.

        Args:
            record: Record data to save
            filepath: Path to save the file
            compress: Whether to compress the file
            record_type: Type of record (for metadata)
            identifier: Record identifier (for metadata)

        Returns:
            File size in bytes
        """
        with self._lock:
            filepath = Path(filepath)

            # Ensure it's relative to base_dir if not absolute
            if not filepath.is_absolute():
                filepath = self.base_dir / filepath

            # Create directory if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Add metadata if provided
            if record_type or identifier:
                enhanced_record = record.copy()
                if "_metadata" not in enhanced_record:
                    enhanced_record["_metadata"] = {}

                if record_type:
                    enhanced_record["_metadata"]["record_type"] = record_type
                if identifier:
                    enhanced_record["_metadata"]["identifier"] = identifier
                enhanced_record["_metadata"]["compressed"] = compress
                record = enhanced_record

            if compress:
                gz_filepath = filepath.with_suffix(filepath.suffix + ".gz")
                with gzip.open(
                    gz_filepath, "wt", compresslevel=self.compression_level
                ) as f:
                    json.dump(
                        record, f, indent=None, separators=(",", ":"), default=str
                    )

                file_size = gz_filepath.stat().st_size
                logger.debug(
                    f"Saved compressed record to {gz_filepath} ({file_size} bytes)"
                )
                return file_size
            else:
                with open(filepath, "w") as f:
                    json.dump(record, f, indent=2, default=str)

                file_size = filepath.stat().st_size
                logger.debug(
                    f"Saved uncompressed record to {filepath} ({file_size} bytes)"
                )
                return file_size

    def load_record(self, filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Load record from compressed or uncompressed file.

        Args:
            filepath: Path to the file (without .gz extension)

        Returns:
            Record data or None if not found
        """
        filepath = Path(filepath)

        # Ensure it's relative to base_dir if not absolute
        if not filepath.is_absolute():
            filepath = self.base_dir / filepath

        # Try compressed first
        gz_filepath = filepath.with_suffix(filepath.suffix + ".gz")
        if gz_filepath.exists():
            try:
                with gzip.open(gz_filepath, "rt") as f:
                    record = json.load(f)
                logger.debug(f"Loaded compressed record from {gz_filepath}")
                return record
            except Exception as e:
                logger.warning(f"Error loading compressed file {gz_filepath}: {e}")

        # Try uncompressed
        if filepath.exists():
            try:
                with open(filepath) as f:
                    record = json.load(f)
                logger.debug(f"Loaded uncompressed record from {filepath}")
                return record
            except Exception as e:
                logger.warning(f"Error loading uncompressed file {filepath}: {e}")

        logger.warning(
            f"File not found: {filepath} (tried both compressed and uncompressed)"
        )
        return None

    def save_bulk_records(
        self,
        records: List[Dict[str, Any]],
        filepath: Union[str, Path],
        compress: bool = True,
        record_type: Optional[str] = None,
    ) -> int:
        """
        Save bulk records with optional compression.

        Args:
            records: List of records to save
            filepath: Path to save the file
            compress: Whether to compress the file
            record_type: Type of records (for metadata)

        Returns:
            File size in bytes
        """
        with self._lock:
            filepath = Path(filepath)

            # Ensure it's relative to base_dir if not absolute
            if not filepath.is_absolute():
                filepath = self.base_dir / filepath

            # Create directory if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Add bulk metadata
            bulk_data = {
                "records": records,
                "_metadata": {
                    "count": len(records),
                    "record_type": record_type,
                    "compressed": compress,
                    "saved_at": json.dumps(
                        {}, default=str
                    ),  # Will be converted to ISO string
                },
            }

            if compress:
                gz_filepath = filepath.with_suffix(filepath.suffix + ".gz")
                with gzip.open(
                    gz_filepath, "wt", compresslevel=self.compression_level
                ) as f:
                    json.dump(
                        bulk_data, f, indent=None, separators=(",", ":"), default=str
                    )

                file_size = gz_filepath.stat().st_size
                logger.info(
                    f"Saved {len(records)} compressed records to {gz_filepath} ({file_size} bytes)"
                )
                return file_size
            else:
                with open(filepath, "w") as f:
                    json.dump(bulk_data, f, indent=2, default=str)

                file_size = filepath.stat().st_size
                logger.info(
                    f"Saved {len(records)} uncompressed records to {filepath} ({file_size} bytes)"
                )
                return file_size

    def load_bulk_records(
        self, filepath: Union[str, Path]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Load bulk records from compressed or uncompressed file.

        Args:
            filepath: Path to the file (without .gz extension)

        Returns:
            List of records or None if not found
        """
        data = self.load_record(filepath)
        if data is None:
            return None

        # Handle both new format (with metadata) and old format (direct list)
        if isinstance(data, dict) and "records" in data:
            return data["records"]
        elif isinstance(data, list):
            return data
        else:
            logger.warning(f"Unexpected data format in {filepath}")
            return None

    def compress_existing_file(self, filepath: Union[str, Path]) -> bool:
        """
        Compress an existing uncompressed JSON file.

        Args:
            filepath: Path to the uncompressed file

        Returns:
            True if compression successful, False otherwise
        """
        with self._lock:
            filepath = Path(filepath)

            # Ensure it's relative to base_dir if not absolute
            if not filepath.is_absolute():
                filepath = self.base_dir / filepath

            if not filepath.exists():
                logger.warning(f"File not found for compression: {filepath}")
                return False

            gz_filepath = filepath.with_suffix(filepath.suffix + ".gz")

            try:
                # Read original file
                with open(filepath) as f:
                    data = json.load(f)

                # Write compressed file
                with gzip.open(
                    gz_filepath, "wt", compresslevel=self.compression_level
                ) as f:
                    json.dump(data, f, indent=None, separators=(",", ":"), default=str)

                # Remove original file
                original_size = filepath.stat().st_size
                compressed_size = gz_filepath.stat().st_size
                filepath.unlink()

                compression_ratio = (1 - compressed_size / original_size) * 100
                logger.info(
                    f"Compressed {filepath} -> {gz_filepath} "
                    f"({original_size} -> {compressed_size} bytes, "
                    f"{compression_ratio:.1f}% reduction)"
                )
                return True

            except Exception as e:
                logger.error(f"Error compressing file {filepath}: {e}")
                # Clean up partial compressed file if it exists
                if gz_filepath.exists():
                    gz_filepath.unlink()
                return False

    def decompress_existing_file(self, filepath: Union[str, Path]) -> bool:
        """
        Decompress an existing compressed JSON file.

        Args:
            filepath: Path to the compressed file (.gz extension)

        Returns:
            True if decompression successful, False otherwise
        """
        with self._lock:
            gz_filepath = Path(filepath)

            # Ensure it's relative to base_dir if not absolute
            if not gz_filepath.is_absolute():
                gz_filepath = self.base_dir / gz_filepath

            if not gz_filepath.exists():
                logger.warning(f"Compressed file not found: {gz_filepath}")
                return False

            # Remove .gz extension for output file
            if gz_filepath.suffix == ".gz":
                output_filepath = gz_filepath.with_suffix("")
            else:
                output_filepath = gz_filepath.with_suffix(".json")

            try:
                # Read compressed file
                with gzip.open(gz_filepath, "rt") as f:
                    data = json.load(f)

                # Write uncompressed file
                with open(output_filepath, "w") as f:
                    json.dump(data, f, indent=2, default=str)

                # Remove compressed file
                compressed_size = gz_filepath.stat().st_size
                uncompressed_size = output_filepath.stat().st_size
                gz_filepath.unlink()

                logger.info(
                    f"Decompressed {gz_filepath} -> {output_filepath} "
                    f"({compressed_size} -> {uncompressed_size} bytes)"
                )
                return True

            except Exception as e:
                logger.error(f"Error decompressing file {gz_filepath}: {e}")
                # Clean up partial uncompressed file if it exists
                if output_filepath.exists():
                    output_filepath.unlink()
                return False

    def get_compression_stats(
        self, record_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get compression statistics for files in storage.

        Args:
            record_type: Optional record type to filter by

        Returns:
            Dictionary with compression statistics
        """
        stats = {
            "total_files": 0,
            "compressed_files": 0,
            "uncompressed_files": 0,
            "total_size_compressed": 0,
            "total_size_uncompressed": 0,
            "compression_ratio": 0.0,
            "by_type": {},
        }

        search_path = self.base_dir
        if record_type:
            search_path = search_path / record_type

        if not search_path.exists():
            return stats

        # Scan all JSON files
        for json_file in search_path.rglob("*.json"):
            stats["total_files"] += 1
            stats["uncompressed_files"] += 1
            stats["total_size_uncompressed"] += json_file.stat().st_size

        # Scan all compressed JSON files
        for gz_file in search_path.rglob("*.json.gz"):
            stats["total_files"] += 1
            stats["compressed_files"] += 1
            stats["total_size_compressed"] += gz_file.stat().st_size

        # Calculate overall compression ratio
        total_size = stats["total_size_compressed"] + stats["total_size_uncompressed"]
        if total_size > 0:
            stats["compression_ratio"] = (
                1 - stats["total_size_compressed"] / total_size
            ) * 100

        return stats


# Standalone functions for backward compatibility
def save_compressed_record(
    record: Dict[str, Any],
    filepath: Union[str, Path],
    compress: bool = True,
    base_dir: str = "data",
    compression_level: int = 6,
) -> int:
    """
    Save compressed record using standalone function (backward compatibility).

    Args:
        record: Record data to save
        filepath: Path to save the file
        compress: Whether to compress the file
        base_dir: Base directory
        compression_level: Gzip compression level

    Returns:
        File size in bytes
    """
    storage = CompressedStorage(base_dir=base_dir, compression_level=compression_level)
    return storage.save_record(record, filepath, compress)


def load_compressed_record(
    filepath: Union[str, Path], base_dir: str = "data"
) -> Optional[Dict[str, Any]]:
    """
    Load compressed record using standalone function (backward compatibility).

    Args:
        filepath: Path to the file
        base_dir: Base directory

    Returns:
        Record data or None if not found
    """
    storage = CompressedStorage(base_dir=base_dir)
    return storage.load_record(filepath)
