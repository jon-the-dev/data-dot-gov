#!/usr/bin/env python3
"""
Unified Fetcher Module - Consolidated data fetching functionality for government data.

This module consolidates the common fetching logic from multiple data fetcher scripts:
- gov_data_downloader.py
- gov_data_downloader_v2.py
- historical_data_fetcher.py
- smart_fetch.py

Key Features:
- Import and use consolidated core APIs (from core.api import CongressGovAPI, SenateGovAPI)
- Support both bulk and individual record fetching
- Include incremental/resumable fetching capabilities
- Handle compressed storage options
- Provide progress tracking and logging
- Support parallel processing with ThreadPoolExecutor
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Add parent directory to path to import core package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from core package
from core.api import CongressGovAPI, SenateGovAPI
from core.storage import CompressedStorage, FileStorage, save_individual_record

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UnifiedFetcher:
    """
    Unified fetcher class that consolidates common fetching functionality.

    Supports:
    - Congressional bills, votes, and member data
    - Senate lobbying filings and lobbyist data
    - Individual and bulk record fetching
    - Incremental/resumable fetching
    - Compressed storage
    - Progress tracking
    - Parallel processing
    """

    def __init__(
        self,
        data_dir: str = "data",
        api_key: Optional[str] = None,
        senate_username: Optional[str] = None,
        senate_password: Optional[str] = None,
        max_workers: int = 5,
        use_compression: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the unified fetcher.

        Args:
            data_dir: Base directory for data storage
            api_key: Congress.gov API key
            senate_username: Senate.gov username for authenticated access
            senate_password: Senate.gov password for authenticated access
            max_workers: Number of parallel workers for ThreadPoolExecutor
            use_compression: Whether to use compressed storage
            verbose: Enable verbose logging
        """
        self.data_dir = Path(data_dir)
        self.max_workers = max_workers
        self.use_compression = use_compression
        self.verbose = verbose

        # Set up logging
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Initialize storage
        if use_compression:
            self.storage = CompressedStorage(base_dir=str(self.data_dir))
        else:
            self.storage = FileStorage(base_dir=str(self.data_dir))

        # Initialize API clients
        self.congress_api = CongressGovAPI(
            api_key=api_key or os.getenv("DATA_GOV_API_KEY"), max_workers=max_workers
        )

        self.senate_api = SenateGovAPI(
            username=senate_username or os.getenv("SENATE_GOV_USERNAME"),
            password=senate_password or os.getenv("SENATE_GOV_PASSWORD"),
        )

        # Metadata for tracking fetches
        self.metadata_file = self.data_dir / ".fetch_metadata.json"
        self.metadata = self._load_metadata()

        logger.info(f"Initialized UnifiedFetcher with data_dir={self.data_dir}")

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata about previous fetches."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save metadata about fetches."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def _record_fetch(
        self, data_type: str, file_count: int = 0, status: str = "success"
    ) -> None:
        """Record that we fetched data."""
        self.metadata[data_type] = {
            "last_fetch": datetime.now().isoformat(),
            "file_count": file_count,
            "status": status,
            "compression": self.use_compression,
        }
        self._save_metadata()

    def _should_fetch(self, data_type: str, max_age_hours: int = 24) -> bool:
        """Check if we should fetch new data based on age."""
        if data_type not in self.metadata:
            logger.info(f"No previous fetch record for {data_type}")
            return True

        last_fetch = datetime.fromisoformat(self.metadata[data_type]["last_fetch"])
        age = datetime.now() - last_fetch

        if age > timedelta(hours=max_age_hours):
            logger.info(
                f"{data_type} data is {age.total_seconds()/3600:.1f} hours old, refetching"
            )
            return True

        logger.info(
            f"{data_type} data is recent ({age.total_seconds()/3600:.1f} hours old), skipping"
        )
        return False

    def _count_existing_files(self, directory: str, pattern: str = "*.json") -> int:
        """Count existing files in a directory."""
        dir_path = self.data_dir / directory
        if not dir_path.exists():
            return 0

        files = list(dir_path.glob(pattern))
        # Exclude metadata files
        files = [
            f
            for f in files
            if f.name not in ["index.json", "summary.json", ".fetch_metadata.json"]
        ]
        return len(files)

    def _get_file_hash(self, filepath: Path) -> Optional[str]:
        """Get hash of a file to detect changes."""
        if not filepath.exists():
            return None

        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def fetch_congress_bills(
        self,
        congress: int = 118,
        max_results: int = 100,
        chamber: Optional[str] = None,
        force: bool = False,
    ) -> Tuple[int, List[str]]:
        """
        Fetch Congressional bills with incremental support.

        Args:
            congress: Congress number (e.g., 118)
            max_results: Maximum number of bills to fetch
            chamber: Chamber filter ('house' or 'senate')
            force: Force fetch even if recent data exists

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        data_type = f"congress_bills_{congress}"

        if not force and not self._should_fetch(data_type):
            existing_count = self._count_existing_files(f"congress_bills/{congress}")
            logger.info(f"Skipping bills fetch, {existing_count} existing files")
            return existing_count, []

        logger.info(f"Fetching Congressional bills for congress {congress}")

        try:
            # Get bills from Congress API
            bills_data = self.congress_api.get_bills(
                congress=congress, limit=max_results
            )

            if not bills_data or "bills" not in bills_data:
                logger.warning("No bills data received")
                return 0, []

            bills = bills_data["bills"]
            saved_files = []

            # Save each bill individually
            for bill in bills:
                try:
                    bill_id = f"{congress}_{bill.get('type', 'unknown')}_{bill.get('number', 'unknown')}"

                    if self.use_compression:
                        file_path = self.storage.save_record(
                            bill,
                            f"congress_bills/{congress}/{bill_id}.json",
                            compress=True,
                        )
                    else:
                        file_path = save_individual_record(
                            bill,
                            f"congress_bills/{congress}",
                            bill_id,
                            str(self.data_dir),
                        )

                    saved_files.append(file_path)

                except Exception as e:
                    logger.error(
                        f"Failed to save bill {bill.get('number', 'unknown')}: {e}"
                    )

            # Record the fetch
            self._record_fetch(data_type, len(saved_files))

            logger.info(f"Successfully fetched and saved {len(saved_files)} bills")
            return len(saved_files), saved_files

        except Exception as e:
            logger.error(f"Failed to fetch bills: {e}")
            self._record_fetch(data_type, 0, "error")
            return 0, []

    def fetch_house_votes(
        self, congress: int = 118, max_results: int = 100, force: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Fetch House votes with member positions.

        Args:
            congress: Congress number
            max_results: Maximum number of votes to fetch
            force: Force fetch even if recent data exists

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        data_type = f"house_votes_{congress}"

        if not force and not self._should_fetch(data_type):
            existing_count = self._count_existing_files(
                f"house_votes_detailed/{congress}"
            )
            logger.info(f"Skipping votes fetch, {existing_count} existing files")
            return existing_count, []

        logger.info(f"Fetching House votes for congress {congress}")

        try:
            # Get votes from Congress API
            votes_data = self.congress_api.get_votes(
                congress=congress, chamber="house", limit=max_results
            )

            if not votes_data or "votes" not in votes_data:
                logger.warning("No votes data received")
                return 0, []

            votes = votes_data["votes"]
            saved_files = []

            # Process votes with parallel workers if available
            if self.max_workers > 1:
                saved_files = self._process_votes_parallel(votes, congress)
            else:
                saved_files = self._process_votes_sequential(votes, congress)

            # Record the fetch
            self._record_fetch(data_type, len(saved_files))

            logger.info(f"Successfully fetched and saved {len(saved_files)} votes")
            return len(saved_files), saved_files

        except Exception as e:
            logger.error(f"Failed to fetch votes: {e}")
            self._record_fetch(data_type, 0, "error")
            return 0, []

    def _process_votes_sequential(self, votes: List[Dict], congress: int) -> List[str]:
        """Process votes sequentially."""
        saved_files = []

        for vote in votes:
            try:
                # Get detailed vote information with member positions
                vote_detail = self.congress_api.get_vote_detail(
                    congress=congress,
                    chamber="house",
                    session=vote.get("sessionNumber", 1),
                    roll_call=vote.get("rollCall"),
                )

                if vote_detail:
                    vote_id = f"{congress}_{vote.get('sessionNumber', 1)}_{vote.get('rollCall')}"

                    if self.use_compression:
                        file_path = self.storage.save_record(
                            vote_detail,
                            f"house_votes_detailed/{congress}/{vote_id}.json",
                            compress=True,
                        )
                    else:
                        file_path = save_individual_record(
                            vote_detail,
                            f"house_votes_detailed/{congress}",
                            vote_id,
                            str(self.data_dir),
                        )

                    saved_files.append(file_path)

            except Exception as e:
                logger.error(
                    f"Failed to process vote {vote.get('rollCall', 'unknown')}: {e}"
                )

        return saved_files

    def _process_votes_parallel(self, votes: List[Dict], congress: int) -> List[str]:
        """Process votes in parallel using ThreadPoolExecutor."""
        saved_files = []

        def process_single_vote(vote):
            try:
                # Get detailed vote information with member positions
                vote_detail = self.congress_api.get_vote_detail(
                    congress=congress,
                    chamber="house",
                    session=vote.get("sessionNumber", 1),
                    roll_call=vote.get("rollCall"),
                )

                if vote_detail:
                    vote_id = f"{congress}_{vote.get('sessionNumber', 1)}_{vote.get('rollCall')}"

                    if self.use_compression:
                        file_path = self.storage.save_record(
                            vote_detail,
                            f"house_votes_detailed/{congress}/{vote_id}.json",
                            compress=True,
                        )
                    else:
                        file_path = save_individual_record(
                            vote_detail,
                            f"house_votes_detailed/{congress}",
                            vote_id,
                            str(self.data_dir),
                        )

                    return file_path

            except Exception as e:
                logger.error(
                    f"Failed to process vote {vote.get('rollCall', 'unknown')}: {e}"
                )
                return None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_vote = {
                executor.submit(process_single_vote, vote): vote for vote in votes
            }

            for future in as_completed(future_to_vote):
                file_path = future.result()
                if file_path:
                    saved_files.append(file_path)

        return saved_files

    def fetch_congress_members(
        self, congress: int = 118, chamber: Optional[str] = None, force: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Fetch Congressional members with party affiliations.

        Args:
            congress: Congress number
            chamber: Chamber filter ('house' or 'senate')
            force: Force fetch even if recent data exists

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        data_type = f"congress_members_{congress}"

        if not force and not self._should_fetch(data_type):
            existing_count = self._count_existing_files(f"members/{congress}")
            logger.info(f"Skipping members fetch, {existing_count} existing files")
            return existing_count, []

        logger.info(f"Fetching Congressional members for congress {congress}")

        try:
            # Get members from Congress API
            members_data = self.congress_api.get_members(
                congress=congress, chamber=chamber
            )

            if not members_data or "members" not in members_data:
                logger.warning("No members data received")
                return 0, []

            members = members_data["members"]
            saved_files = []

            # Save each member individually
            for member in members:
                try:
                    member_id = member.get(
                        "bioguideId", f"unknown_{member.get('name', 'unknown')}"
                    )

                    if self.use_compression:
                        file_path = self.storage.save_record(
                            member,
                            f"members/{congress}/{member_id}.json",
                            compress=True,
                        )
                    else:
                        file_path = save_individual_record(
                            member, f"members/{congress}", member_id, str(self.data_dir)
                        )

                    saved_files.append(file_path)

                except Exception as e:
                    logger.error(
                        f"Failed to save member {member.get('name', 'unknown')}: {e}"
                    )

            # Record the fetch
            self._record_fetch(data_type, len(saved_files))

            logger.info(f"Successfully fetched and saved {len(saved_files)} members")
            return len(saved_files), saved_files

        except Exception as e:
            logger.error(f"Failed to fetch members: {e}")
            self._record_fetch(data_type, 0, "error")
            return 0, []

    def fetch_senate_filings(
        self, filing_type: str = "ld-2", max_results: int = 100, force: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Fetch Senate lobbying filings.

        Args:
            filing_type: Type of filing ('ld-1' or 'ld-2')
            max_results: Maximum number of filings to fetch
            force: Force fetch even if recent data exists

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        data_type = f"senate_filings_{filing_type}"

        if not force and not self._should_fetch(data_type):
            existing_count = self._count_existing_files(f"senate_filings/{filing_type}")
            logger.info(
                f"Skipping {filing_type} filings fetch, {existing_count} existing files"
            )
            return existing_count, []

        logger.info(f"Fetching Senate {filing_type} filings")

        try:
            # Get filings from Senate API
            filings_data = self.senate_api.get_lobbying_filings(
                filing_type=filing_type, limit=max_results
            )

            if not filings_data:
                logger.warning("No filings data received")
                return 0, []

            saved_files = []

            # Save each filing individually
            for filing in filings_data:
                try:
                    filing_id = filing.get("filing_id", f"unknown_{len(saved_files)}")

                    if self.use_compression:
                        file_path = self.storage.save_record(
                            filing,
                            f"senate_filings/{filing_type}/{filing_id}.json",
                            compress=True,
                        )
                    else:
                        file_path = save_individual_record(
                            filing,
                            f"senate_filings/{filing_type}",
                            filing_id,
                            str(self.data_dir),
                        )

                    saved_files.append(file_path)

                except Exception as e:
                    logger.error(
                        f"Failed to save filing {filing.get('filing_id', 'unknown')}: {e}"
                    )

            # Record the fetch
            self._record_fetch(data_type, len(saved_files))

            logger.info(
                f"Successfully fetched and saved {len(saved_files)} {filing_type} filings"
            )
            return len(saved_files), saved_files

        except Exception as e:
            logger.error(f"Failed to fetch {filing_type} filings: {e}")
            self._record_fetch(data_type, 0, "error")
            return 0, []

    def fetch_all(
        self,
        congress: int = 118,
        max_results: int = 100,
        force: bool = False,
        include_senate_data: bool = True,
    ) -> Dict[str, Tuple[int, List[str]]]:
        """
        Fetch all data types in a coordinated manner.

        Args:
            congress: Congress number
            max_results: Maximum results per data type
            force: Force fetch even if recent data exists
            include_senate_data: Whether to include Senate lobbying data

        Returns:
            Dictionary mapping data type to (count, file_paths)
        """
        results = {}

        logger.info(f"Starting comprehensive data fetch for congress {congress}")

        # Fetch Congressional data
        results["bills"] = self.fetch_congress_bills(congress, max_results, force=force)
        results["votes"] = self.fetch_house_votes(congress, max_results, force=force)
        results["members"] = self.fetch_congress_members(congress, force=force)

        # Fetch Senate data if requested
        if include_senate_data:
            results["ld1_filings"] = self.fetch_senate_filings(
                "ld-1", max_results, force=force
            )
            results["ld2_filings"] = self.fetch_senate_filings(
                "ld-2", max_results, force=force
            )

        # Log summary
        total_files = sum(count for count, _ in results.values())
        logger.info(
            f"Comprehensive fetch completed: {total_files} total files across {len(results)} data types"
        )

        return results

    def get_fetch_status(self) -> Dict[str, Any]:
        """Get status of all previous fetches."""
        status = {
            "metadata_file": str(self.metadata_file),
            "data_directory": str(self.data_dir),
            "compression_enabled": self.use_compression,
            "fetches": {},
        }

        for data_type, metadata in self.metadata.items():
            existing_files = 0
            if "congress_bills" in data_type:
                congress = data_type.split("_")[-1]
                existing_files = self._count_existing_files(
                    f"congress_bills/{congress}"
                )
            elif "house_votes" in data_type:
                congress = data_type.split("_")[-1]
                existing_files = self._count_existing_files(
                    f"house_votes_detailed/{congress}"
                )
            elif "congress_members" in data_type:
                congress = data_type.split("_")[-1]
                existing_files = self._count_existing_files(f"members/{congress}")
            elif "senate_filings" in data_type:
                filing_type = data_type.split("_")[-1]
                existing_files = self._count_existing_files(
                    f"senate_filings/{filing_type}"
                )

            status["fetches"][data_type] = {
                **metadata,
                "existing_files": existing_files,
            }

        return status


def main():
    """Command-line interface for the unified fetcher."""
    parser = argparse.ArgumentParser(description="Unified Government Data Fetcher")

    # Data source options
    parser.add_argument(
        "--congress-bills", action="store_true", help="Fetch Congressional bills"
    )
    parser.add_argument("--house-votes", action="store_true", help="Fetch House votes")
    parser.add_argument(
        "--members", action="store_true", help="Fetch Congressional members"
    )
    parser.add_argument(
        "--senate-filings", action="store_true", help="Fetch Senate lobbying filings"
    )
    parser.add_argument("--all", action="store_true", help="Fetch all data types")

    # Parameters
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument(
        "--max-results", type=int, default=100, help="Maximum results per type"
    )
    parser.add_argument("--chamber", choices=["house", "senate"], help="Chamber filter")
    parser.add_argument(
        "--filing-type",
        choices=["ld-1", "ld-2"],
        default="ld-2",
        help="Senate filing type",
    )

    # Options
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument(
        "--force", action="store_true", help="Force fetch even if recent data exists"
    )
    parser.add_argument(
        "--compressed", action="store_true", help="Use compressed storage"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5, help="Number of parallel workers"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--status", action="store_true", help="Show fetch status and exit"
    )

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = UnifiedFetcher(
        data_dir=args.data_dir,
        max_workers=args.max_workers,
        use_compression=args.compressed,
        verbose=args.verbose,
    )

    # Show status if requested
    if args.status:
        status = fetcher.get_fetch_status()
        print(json.dumps(status, indent=2))
        return

    # Determine what to fetch
    if args.all:
        results = fetcher.fetch_all(
            congress=args.congress, max_results=args.max_results, force=args.force
        )

        print("\nFetch Summary:")
        for data_type, (count, _) in results.items():
            print(f"  {data_type}: {count} files")

    else:
        if args.congress_bills:
            count, files = fetcher.fetch_congress_bills(
                congress=args.congress,
                max_results=args.max_results,
                chamber=args.chamber,
                force=args.force,
            )
            print(f"Fetched {count} Congressional bills")

        if args.house_votes:
            count, files = fetcher.fetch_house_votes(
                congress=args.congress, max_results=args.max_results, force=args.force
            )
            print(f"Fetched {count} House votes")

        if args.members:
            count, files = fetcher.fetch_congress_members(
                congress=args.congress, chamber=args.chamber, force=args.force
            )
            print(f"Fetched {count} Congressional members")

        if args.senate_filings:
            count, files = fetcher.fetch_senate_filings(
                filing_type=args.filing_type,
                max_results=args.max_results,
                force=args.force,
            )
            print(f"Fetched {count} Senate {args.filing_type} filings")


if __name__ == "__main__":
    main()
