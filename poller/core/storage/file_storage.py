#!/usr/bin/env python3
"""
File Storage Module - Unified JSON file storage for Congressional Transparency Platform

This module consolidates bulk and individual record storage patterns from the existing codebase
into a unified API with support for incremental saves, indexing, and resumable operations.

Features:
- Bulk JSON storage (save lists of records to single files)
- Individual record storage (save each record as separate JSON file)
- Automatic indexing for quick lookups
- Incremental saving with resume capability
- Thread-safe operations
- Data validation and integrity checks
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def save_individual_record(
    record: Dict, record_type: str, identifier: str, base_dir: str = "data"
) -> str:
    """
    Save an individual record as a JSON file

    Args:
        record: The record data to save
        record_type: Type of record (e.g., 'bills', 'votes', 'filings')
        identifier: Unique identifier for the record
        base_dir: Base directory for data storage

    Returns:
        Path to the saved file
    """
    # Create directory structure
    dir_path = Path(base_dir) / record_type
    dir_path.mkdir(parents=True, exist_ok=True)

    # Clean identifier for filename
    safe_id = identifier.replace("/", "_").replace(" ", "_").replace(":", "_")
    safe_id = safe_id.replace("\\", "_").replace("?", "_").replace("*", "_")
    safe_id = safe_id.replace("<", "_").replace(">", "_").replace("|", "_")
    safe_id = safe_id.replace('"', "_").replace("'", "_")

    filename = f"{safe_id}.json"
    filepath = dir_path / filename

    # Add metadata to record
    enriched_record = {
        **record,
        "_metadata": {
            "record_type": record_type,
            "identifier": identifier,
            "saved_at": datetime.utcnow().isoformat(),
            "file_path": str(filepath),
        },
    }

    # Save the record
    with open(filepath, "w") as f:
        json.dump(enriched_record, f, indent=2, default=str)

    logger.debug(f"Saved {record_type} record to {filepath}")
    return str(filepath)


def save_index(records: List[Dict], record_type: str, base_dir: str = "data"):
    """
    Save an index file with record summaries

    Args:
        records: List of records to index
        record_type: Type of records
        base_dir: Base directory for data storage
    """
    if not records:
        return

    # Create directory structure
    dir_path = Path(base_dir) / record_type
    dir_path.mkdir(parents=True, exist_ok=True)

    # Create index
    index_data = {
        "record_type": record_type,
        "total_records": len(records),
        "created_at": datetime.utcnow().isoformat(),
        "records": [],
    }

    for record in records:
        # Extract key fields for the index
        index_entry = {
            "identifier": record.get("id")
            or record.get("uuid")
            or record.get("number"),
            "title": record.get("title")
            or record.get("name")
            or record.get("description", "")[:100],
            "date": record.get("date")
            or record.get("filed_date")
            or record.get("created"),
            "type": record.get("type") or record.get("filing_type"),
        }

        # Add record-specific fields
        if "congress" in record:
            index_entry["congress"] = record["congress"]
        if "chamber" in record:
            index_entry["chamber"] = record["chamber"]
        if "party" in record:
            index_entry["party"] = record["party"]
        if "state" in record:
            index_entry["state"] = record["state"]

        index_data["records"].append(index_entry)

    # Save index
    index_path = dir_path / "index.json"
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2, default=str)

    logger.info(f"Saved index for {len(records)} {record_type} records to {index_path}")


def load_individual_record(
    record_type: str, identifier: str, base_dir: str = "data"
) -> Optional[Dict]:
    """
    Load an individual record from file

    Args:
        record_type: Type of record
        identifier: Record identifier
        base_dir: Base directory for data storage

    Returns:
        Record data or None if not found
    """
    # Clean identifier for filename
    safe_id = identifier.replace("/", "_").replace(" ", "_").replace(":", "_")
    safe_id = safe_id.replace("\\", "_").replace("?", "_").replace("*", "_")
    safe_id = safe_id.replace("<", "_").replace(">", "_").replace("|", "_")
    safe_id = safe_id.replace('"', "_").replace("'", "_")

    filepath = Path(base_dir) / record_type / f"{safe_id}.json"

    if not filepath.exists():
        return None

    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading record {identifier}: {e}")
        return None


def load_index(record_type: str, base_dir: str = "data") -> Optional[Dict]:
    """
    Load index file for a record type

    Args:
        record_type: Type of records
        base_dir: Base directory for data storage

    Returns:
        Index data or None if not found
    """
    index_path = Path(base_dir) / record_type / "index.json"

    if not index_path.exists():
        return None

    try:
        with open(index_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading index for {record_type}: {e}")
        return None


def list_record_types(base_dir: str = "data") -> List[str]:
    """
    List all available record types in the data directory

    Args:
        base_dir: Base directory for data storage

    Returns:
        List of record type names
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        return []

    return [d.name for d in base_path.iterdir() if d.is_dir()]


def get_record_count(record_type: str, base_dir: str = "data") -> int:
    """
    Get the number of records for a given type

    Args:
        record_type: Type of records
        base_dir: Base directory for data storage

    Returns:
        Number of records
    """
    dir_path = Path(base_dir) / record_type
    if not dir_path.exists():
        return 0

    # Count JSON files (excluding index.json)
    return len([f for f in dir_path.glob("*.json") if f.name != "index.json"])


def search_records(
    record_type: str,
    query: str,
    field: Optional[str] = None,
    base_dir: str = "data",
    limit: int = 100,
) -> List[Dict]:
    """
    Search records by text query

    Args:
        record_type: Type of records to search
        query: Search query (case-insensitive)
        field: Specific field to search in (optional)
        base_dir: Base directory for data storage
        limit: Maximum number of results

    Returns:
        List of matching records
    """
    dir_path = Path(base_dir) / record_type
    if not dir_path.exists():
        return []

    results = []
    query_lower = query.lower()

    for json_file in dir_path.glob("*.json"):
        if json_file.name == "index.json":
            continue

        try:
            with open(json_file) as f:
                record = json.load(f)

            if field:
                # Search in specific field
                field_value = str(record.get(field, "")).lower()
                if query_lower in field_value:
                    results.append(record)
            else:
                # Search in all string fields
                record_str = json.dumps(record).lower()
                if query_lower in record_str:
                    results.append(record)

            if len(results) >= limit:
                break

        except Exception as e:
            logger.error(f"Error searching record {json_file}: {e}")
            continue

    return results


class FileStorage:
    """
    Unified file storage class that supports both bulk and individual record storage
    with automatic indexing and resumable operations.
    """

    def __init__(self, base_dir: str = "data", auto_index: bool = True):
        """
        Initialize FileStorage instance.

        Args:
            base_dir: Base directory for data storage
            auto_index: Whether to automatically maintain index files
        """
        self.base_dir = Path(base_dir)
        self.auto_index = auto_index
        self._lock = threading.Lock()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bulk_records(
        self,
        records: List[Dict[str, Any]],
        record_type: str,
        filename: str,
        incremental: bool = True,
        max_records: Optional[int] = None,
    ) -> str:
        """
        Save a list of records to a single JSON file (bulk storage pattern).

        Args:
            records: List of records to save
            record_type: Type of record (e.g., 'bills', 'votes', 'filings')
            filename: Output filename
            incremental: Whether to support incremental saves
            max_records: Maximum number of records to save (for testing)

        Returns:
            Path to the saved file
        """
        with self._lock:
            # Create directory
            dir_path = self.base_dir / record_type
            dir_path.mkdir(parents=True, exist_ok=True)
            filepath = dir_path / filename

            existing_records = []

            # Handle incremental saving
            if incremental and filepath.exists():
                try:
                    with open(filepath) as f:
                        existing_data = json.load(f)
                    existing_records = (
                        existing_data if isinstance(existing_data, list) else []
                    )
                    logger.info(
                        f"Found {len(existing_records)} existing records in {filepath}"
                    )
                except Exception as e:
                    logger.warning(f"Could not load existing data from {filepath}: {e}")

            # Combine records
            all_records = existing_records + records

            # Apply max_records limit
            if max_records and len(all_records) > max_records:
                all_records = all_records[:max_records]
                logger.info(f"Limited to {max_records} records")

            # Save records
            with open(filepath, "w") as f:
                json.dump(all_records, f, indent=2, default=str)

            logger.info(f"Saved {len(all_records)} records to {filepath}")

            # Update index if enabled
            if self.auto_index:
                self._update_bulk_index(record_type, filename, len(all_records))

            return str(filepath)

    def save_individual_record(
        self,
        record: Dict[str, Any],
        record_type: str,
        identifier: str,
        congress: Optional[int] = None,
    ) -> str:
        """
        Save an individual record as a separate JSON file (individual storage pattern).

        Args:
            record: Record data to save
            record_type: Type of record (e.g., 'bills', 'votes', 'members')
            identifier: Unique identifier for the record
            congress: Optional congress number for organization

        Returns:
            Path to the saved file
        """
        with self._lock:
            # Create directory structure
            if congress:
                dir_path = self.base_dir / record_type / str(congress)
            else:
                dir_path = self.base_dir / record_type
            dir_path.mkdir(parents=True, exist_ok=True)

            # Clean identifier for filename
            safe_id = self._sanitize_filename(identifier)
            filename = f"{safe_id}.json"
            filepath = dir_path / filename

            # Add metadata to record
            enriched_record = {
                **record,
                "_metadata": {
                    "record_type": record_type,
                    "identifier": identifier,
                    "saved_at": datetime.utcnow().isoformat(),
                    "file_path": str(filepath),
                },
            }

            # Save the record
            with open(filepath, "w") as f:
                json.dump(enriched_record, f, indent=2, default=str)

            logger.debug(f"Saved individual record to {filepath}")

            # Update index if enabled
            if self.auto_index:
                self._update_individual_index(record_type, identifier, record, congress)

            return str(filepath)

    def save_record(self, record: Dict, record_type: str, identifier: str) -> str:
        """Save an individual record (backward compatibility)"""
        return self.save_individual_record(record, record_type, identifier)

    def load_records(
        self,
        record_type: str,
        filename: Optional[str] = None,
        congress: Optional[int] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Load records from storage.

        Args:
            record_type: Type of record to load
            filename: Specific filename for bulk records (optional)
            congress: Congress number for individual records (optional)

        Returns:
            List of records (bulk) or dict of records (individual)
        """
        if filename:
            # Load bulk records
            filepath = self.base_dir / record_type / filename
            if not filepath.exists():
                logger.warning(f"File not found: {filepath}")
                return []

            with open(filepath) as f:
                return json.load(f)
        else:
            # Load individual records
            if congress:
                dir_path = self.base_dir / record_type / str(congress)
            else:
                dir_path = self.base_dir / record_type

            if not dir_path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                return {}

            records = {}
            for json_file in dir_path.glob("*.json"):
                if json_file.name == "index.json":
                    continue
                try:
                    with open(json_file) as f:
                        record = json.load(f)
                    record_id = json_file.stem
                    records[record_id] = record
                except Exception as e:
                    logger.warning(f"Error loading {json_file}: {e}")

            return records

    def load_record(self, record_type: str, identifier: str) -> Optional[Dict]:
        """Load an individual record (backward compatibility)"""
        return load_individual_record(record_type, identifier, str(self.base_dir))

    def get_existing_identifiers(
        self, record_type: str, congress: Optional[int] = None
    ) -> List[str]:
        """
        Get list of existing record identifiers from index.

        Args:
            record_type: Type of record
            congress: Congress number (optional)

        Returns:
            List of existing record identifiers
        """
        index_data = self._load_index(record_type, congress)
        return [r.get("id", "") for r in index_data.get("records", [])]

    def save_index(
        self,
        records: List[Dict[str, Any]],
        record_type: str,
        congress: Optional[int] = None,
    ) -> str:
        """
        Save an index file listing all records.

        Args:
            records: List of records with metadata
            record_type: Type of record
            congress: Congress number (optional)

        Returns:
            Path to the index file
        """
        with self._lock:
            if congress:
                index_path = self.base_dir / record_type / str(congress) / "index.json"
            else:
                index_path = self.base_dir / record_type / "index.json"

            index_path.parent.mkdir(parents=True, exist_ok=True)

            index_data = {
                "count": len(records),
                "last_updated": datetime.now().isoformat(),
                "record_type": record_type,
                "congress": congress,
                "records": records,
            }

            with open(index_path, "w") as f:
                json.dump(index_data, f, indent=2)

            logger.info(f"Saved index with {len(records)} records to {index_path}")
            return str(index_path)

    def load_index(self, record_type: str) -> Optional[Dict]:
        """Load index for a record type"""
        return load_index(record_type, self.base_dir)

    def list_types(self) -> List[str]:
        """List all record types"""
        return list_record_types(self.base_dir)

    def count_records(self, record_type: str) -> int:
        """Count records of a given type"""
        return get_record_count(record_type, self.base_dir)

    def search(
        self,
        record_type: str,
        query: str,
        field: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Search records"""
        return search_records(record_type, query, field, self.base_dir, limit)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Dictionary with storage stats
        """
        stats = {"base_dir": self.base_dir, "record_types": {}, "total_records": 0}

        for record_type in self.list_types():
            count = self.count_records(record_type)
            stats["record_types"][record_type] = count
            stats["total_records"] += count

        return stats

    def _sanitize_filename(self, identifier: str) -> str:
        """
        Sanitize identifier for use as filename.

        Args:
            identifier: Raw identifier

        Returns:
            Sanitized filename
        """
        # Replace problematic characters
        safe_id = identifier.replace("/", "_").replace(" ", "_").replace(":", "_")
        safe_id = safe_id.replace("\\", "_").replace("?", "_").replace("*", "_")
        safe_id = safe_id.replace("<", "_").replace(">", "_").replace("|", "_")
        safe_id = safe_id.replace('"', "_").replace("'", "_")
        return safe_id

    def _update_bulk_index(self, record_type: str, filename: str, count: int) -> None:
        """Update bulk storage index."""
        index_path = self.base_dir / record_type / "bulk_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing index
        bulk_index = {}
        if index_path.exists():
            try:
                with open(index_path) as f:
                    bulk_index = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load bulk index: {e}")

        # Update index
        bulk_index[filename] = {
            "count": count,
            "last_updated": datetime.now().isoformat(),
            "record_type": record_type,
        }

        # Save index
        with open(index_path, "w") as f:
            json.dump(bulk_index, f, indent=2)

    def _update_individual_index(
        self,
        record_type: str,
        identifier: str,
        record: Dict[str, Any],
        congress: Optional[int] = None,
    ) -> None:
        """Update individual storage index."""
        index_data = self._load_index(record_type, congress)

        # Create record metadata
        record_meta = {
            "id": identifier,
            "filename": f"{self._sanitize_filename(identifier)}.json",
            "last_updated": datetime.now().isoformat(),
        }

        # Add some basic metadata from the record if available
        if "title" in record:
            record_meta["title"] = record["title"]
        if "number" in record:
            record_meta["number"] = record["number"]
        if "type" in record:
            record_meta["type"] = record["type"]

        # Update or add record
        existing_records = index_data.get("records", [])
        updated = False
        for i, existing in enumerate(existing_records):
            if existing.get("id") == identifier:
                existing_records[i] = record_meta
                updated = True
                break

        if not updated:
            existing_records.append(record_meta)

        # Save updated index
        index_data["records"] = existing_records
        index_data["count"] = len(existing_records)
        index_data["last_updated"] = datetime.now().isoformat()

        self.save_index(existing_records, record_type, congress)

    def _load_index(
        self, record_type: str, congress: Optional[int] = None
    ) -> Dict[str, Any]:
        """Load existing index data."""
        if congress:
            index_path = self.base_dir / record_type / str(congress) / "index.json"
        else:
            index_path = self.base_dir / record_type / "index.json"

        if not index_path.exists():
            return {"records": [], "count": 0}

        try:
            with open(index_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load index from {index_path}: {e}")
            return {"records": [], "count": 0}

    def cleanup_empty_dirs(self):
        """Remove empty directories"""
        base_path = Path(self.base_dir)
        for dir_path in base_path.iterdir():
            if dir_path.is_dir():
                try:
                    # Try to remove if empty
                    dir_path.rmdir()
                    logger.info(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty, which is fine
                    pass


# Standalone functions for backward compatibility
def save_bulk_records(
    records: List[Dict[str, Any]],
    record_type: str,
    filename: str,
    base_dir: str = "data",
    incremental: bool = True,
) -> str:
    """
    Save bulk records using standalone function (backward compatibility).

    Args:
        records: List of records to save
        record_type: Type of record
        filename: Output filename
        base_dir: Base directory
        incremental: Whether to support incremental saves

    Returns:
        Path to saved file
    """
    storage = FileStorage(base_dir=base_dir)
    return storage.save_bulk_records(records, record_type, filename, incremental)


def load_records(
    record_type: str,
    filename: Optional[str] = None,
    base_dir: str = "data",
    congress: Optional[int] = None,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load records using standalone function (backward compatibility).

    Args:
        record_type: Type of record to load
        filename: Specific filename for bulk records (optional)
        base_dir: Base directory
        congress: Congress number for individual records (optional)

    Returns:
        Records data
    """
    storage = FileStorage(base_dir=base_dir)
    return storage.load_records(record_type, filename, congress)
