#!/usr/bin/env python3
"""
Historical Congressional Data Fetcher
Implements batch processing framework for collecting historical data from congresses 113-117 (2013-2023)
Supports queue-based processing, progress tracking, resumable downloads, and intelligent rate limiting
"""

import argparse
import gzip
import hashlib
import json
import logging
import os
import pickle
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class FetchJob:
    """Represents a data fetching job in the queue"""

    job_id: str
    congress: int
    data_type: str  # 'bills', 'votes', 'members', 'committees'
    chamber: Optional[str] = None  # 'house', 'senate', or None for both
    session: Optional[int] = None
    priority: int = 1  # Lower number = higher priority
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    error_message: Optional[str] = None
    estimated_size: int = 0
    progress: float = 0.0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ProgressTracker:
    """Tracks overall progress of historical data collection"""

    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    running_jobs: int = 0
    start_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    total_records_fetched: int = 0
    total_size_bytes: int = 0

    @property
    def completion_percentage(self) -> float:
        if self.total_jobs == 0:
            return 0.0
        return (self.completed_jobs / self.total_jobs) * 100

    @property
    def elapsed_time(self) -> timedelta:
        if self.start_time is None:
            return timedelta(0)
        return datetime.now() - self.start_time


class EnhancedRateLimiter:
    """Enhanced thread-safe rate limiter with intelligent backoff"""

    def __init__(self, max_requests: int, time_window: int, burst_limit: int = None):
        """
        Initialize enhanced rate limiter

        Args:
            max_requests: Maximum requests in time window
            time_window: Time window in seconds
            burst_limit: Maximum burst requests (optional)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_limit = burst_limit or max_requests
        self.requests = deque()
        self.burst_requests = deque()
        self.lock = threading.Lock()
        self.backoff_multiplier = 1.0
        self.last_429_time = None

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded with intelligent backoff"""
        with self.lock:
            now = time.time()

            # Clean old requests
            while self.requests and now - self.requests[0] >= self.time_window:
                self.requests.popleft()

            while (
                self.burst_requests and now - self.burst_requests[0] >= 60
            ):  # 1 minute burst window
                self.burst_requests.popleft()

            # Check if we need to apply 429 backoff
            if self.last_429_time and (now - self.last_429_time) < (
                60 * self.backoff_multiplier
            ):
                wait_time = (60 * self.backoff_multiplier) - (now - self.last_429_time)
                logger.warning(
                    f"429 backoff active, waiting {wait_time:.1f} seconds..."
                )
                time.sleep(wait_time)
                now = time.time()

            # Check rate limits
            if len(self.requests) >= self.max_requests:
                oldest_request = self.requests[0]
                wait_time = self.time_window - (now - oldest_request) + 1
                if wait_time > 0:
                    logger.info(
                        f"Rate limit reached, waiting {wait_time:.1f} seconds..."
                    )
                    time.sleep(wait_time)
                    now = time.time()

            # Check burst limit
            if len(self.burst_requests) >= self.burst_limit:
                oldest_burst = self.burst_requests[0]
                wait_time = 60 - (now - oldest_burst) + 1
                if wait_time > 0:
                    logger.info(
                        f"Burst limit reached, waiting {wait_time:.1f} seconds..."
                    )
                    time.sleep(wait_time)
                    now = time.time()

            # Record this request
            self.requests.append(now)
            self.burst_requests.append(now)

    def handle_429_response(self, retry_after: Optional[int] = None):
        """Handle 429 Too Many Requests response"""
        with self.lock:
            self.last_429_time = time.time()
            self.backoff_multiplier = min(
                self.backoff_multiplier * 1.5, 8.0
            )  # Max 8x backoff

            if retry_after:
                logger.warning(f"429 received, backing off for {retry_after} seconds")
                time.sleep(retry_after)
            else:
                backoff_time = 60 * self.backoff_multiplier
                logger.warning(
                    f"429 received, backing off for {backoff_time:.1f} seconds"
                )
                time.sleep(backoff_time)

    def reset_backoff(self):
        """Reset backoff multiplier on successful requests"""
        with self.lock:
            self.backoff_multiplier = max(self.backoff_multiplier * 0.9, 1.0)


class DataIntegrityChecker:
    """Validates data integrity with checksums and completeness checks"""

    @staticmethod
    def calculate_checksum(data: Any) -> str:
        """Calculate SHA-256 checksum of data"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    @staticmethod
    def validate_record_completeness(
        record: Dict, required_fields: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate that a record has all required fields"""
        missing_fields = []
        for field in required_fields:
            if field not in record or record[field] is None:
                missing_fields.append(field)
        return len(missing_fields) == 0, missing_fields

    @staticmethod
    def create_integrity_file(filepath: Path, checksum: str, metadata: Dict):
        """Create an integrity file alongside the data file"""
        integrity_path = filepath.with_suffix(".integrity")
        integrity_data = {
            "checksum": checksum,
            "created_at": datetime.now().isoformat(),
            "file_size": filepath.stat().st_size if filepath.exists() else 0,
            "metadata": metadata,
        }
        with open(integrity_path, "w") as f:
            json.dump(integrity_data, f, indent=2)

    @staticmethod
    def verify_file_integrity(filepath: Path) -> Tuple[bool, Optional[str]]:
        """Verify file integrity using stored checksum"""
        integrity_path = filepath.with_suffix(".integrity")

        if not integrity_path.exists():
            return False, "No integrity file found"

        try:
            with open(integrity_path) as f:
                integrity_data = json.load(f)

            with open(filepath) as f:
                file_data = json.load(f)

            calculated_checksum = DataIntegrityChecker.calculate_checksum(file_data)
            stored_checksum = integrity_data.get("checksum")

            if calculated_checksum == stored_checksum:
                return True, None
            else:
                return (
                    False,
                    f"Checksum mismatch: {calculated_checksum} != {stored_checksum}",
                )

        except Exception as e:
            return False, f"Error verifying integrity: {e}"


class CompressedStorage:
    """Handles compressed storage for historical data"""

    @staticmethod
    def save_compressed_record(
        record: Dict, filepath: Path, compress: bool = True
    ) -> int:
        """Save record with optional compression"""
        if compress:
            gz_filepath = filepath.with_suffix(".json.gz")
            with gzip.open(gz_filepath, "wt") as f:
                json.dump(record, f, indent=None, separators=(",", ":"), default=str)
            return gz_filepath.stat().st_size
        else:
            with open(filepath, "w") as f:
                json.dump(record, f, indent=2, default=str)
            return filepath.stat().st_size

    @staticmethod
    def load_compressed_record(filepath: Path) -> Optional[Dict]:
        """Load record from compressed or uncompressed file"""
        # Try compressed first
        gz_filepath = filepath.with_suffix(".json.gz")
        if gz_filepath.exists():
            try:
                with gzip.open(gz_filepath, "rt") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading compressed file {gz_filepath}: {e}")

        # Try uncompressed
        if filepath.exists():
            try:
                with open(filepath) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading file {filepath}: {e}")

        return None


class JobQueue:
    """Thread-safe job queue with priority and persistence"""

    def __init__(self, queue_file: Path):
        self.queue_file = queue_file
        self.jobs: Dict[str, FetchJob] = {}
        self.pending_queue = deque()
        self.lock = threading.Lock()
        self.load_queue()

    def add_job(self, job: FetchJob):
        """Add a job to the queue"""
        with self.lock:
            self.jobs[job.job_id] = job
            if job.status == "pending":
                self.pending_queue.append(job.job_id)
            self.save_queue()

    def get_next_job(self) -> Optional[FetchJob]:
        """Get the next job from the queue"""
        with self.lock:
            while self.pending_queue:
                job_id = self.pending_queue.popleft()
                if job_id in self.jobs and self.jobs[job_id].status == "pending":
                    job = self.jobs[job_id]
                    job.status = "running"
                    job.started_at = datetime.now()
                    self.save_queue()
                    return job
            return None

    def complete_job(
        self, job_id: str, success: bool, error_message: Optional[str] = None
    ):
        """Mark a job as completed or failed"""
        with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.completed_at = datetime.now()
                if success:
                    job.status = "completed"
                    job.progress = 1.0
                else:
                    job.retry_count += 1
                    if job.retry_count >= job.max_retries:
                        job.status = "failed"
                        job.error_message = error_message
                    else:
                        job.status = "pending"
                        self.pending_queue.append(job_id)
                self.save_queue()

    def get_progress(self) -> ProgressTracker:
        """Get overall progress statistics"""
        with self.lock:
            progress = ProgressTracker()
            progress.total_jobs = len(self.jobs)

            for job in self.jobs.values():
                if job.status == "completed":
                    progress.completed_jobs += 1
                elif job.status == "failed":
                    progress.failed_jobs += 1
                elif job.status == "running":
                    progress.running_jobs += 1

            if progress.total_jobs > 0:
                # Estimate completion time based on current progress
                if progress.completed_jobs > 0:
                    # Find earliest start time
                    earliest_start = min(
                        (
                            job.started_at
                            for job in self.jobs.values()
                            if job.started_at is not None
                        ),
                        default=datetime.now(),
                    )
                    progress.start_time = earliest_start

                    elapsed = progress.elapsed_time
                    if elapsed.total_seconds() > 0:
                        rate = progress.completed_jobs / elapsed.total_seconds()
                        remaining = progress.total_jobs - progress.completed_jobs
                        if rate > 0:
                            eta_seconds = remaining / rate
                            progress.estimated_completion = datetime.now() + timedelta(
                                seconds=eta_seconds
                            )

            return progress

    def save_queue(self):
        """Save queue to disk"""
        try:
            with open(self.queue_file, "wb") as f:
                pickle.dump(self.jobs, f)
        except Exception as e:
            logger.error(f"Error saving queue: {e}")

    def load_queue(self):
        """Load queue from disk"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "rb") as f:
                    self.jobs = pickle.load(f)

                # Rebuild pending queue
                for job_id, job in self.jobs.items():
                    if job.status == "pending":
                        self.pending_queue.append(job_id)
                    elif job.status == "running":
                        # Reset running jobs to pending on restart
                        job.status = "pending"
                        self.pending_queue.append(job_id)

                logger.info(f"Loaded {len(self.jobs)} jobs from queue")
            except Exception as e:
                logger.error(f"Error loading queue: {e}")
                self.jobs = {}


class HistoricalCongressAPI:
    """Enhanced Congress.gov API client for historical data collection"""

    BASE_URL = "https://api.congress.gov/v3"

    def __init__(self, api_key: Optional[str] = None, max_workers: int = 10):
        """
        Initialize historical Congress API client

        Args:
            api_key: Congress.gov API key
            max_workers: Maximum parallel workers
        """
        self.api_key = (
            api_key
            or os.getenv("DATA_GOV_API_KEY")
            or os.getenv("CONGRESS_GOV_API_KEY")
        )
        self.session = requests.Session()
        self.max_workers = max_workers

        # Conservative rate limiting for bulk historical operations
        self.rate_limiter = EnhancedRateLimiter(
            max_requests=900,  # 900/hour to stay under 1000 limit
            time_window=3600,
            burst_limit=50,  # Allow bursts of 50 requests per minute
        )

        if not self.api_key:
            logger.warning(
                "No Congress.gov API key provided. Get one at: https://api.data.gov/signup/"
            )

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make a rate-limited request with enhanced error handling"""
        self.rate_limiter.wait_if_needed()

        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = f"{self.BASE_URL}/{endpoint}"

        if not params:
            params = {}

        headers = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        params["format"] = "json"

        try:
            response = self.session.get(url, params=params, headers=headers)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                retry_after = int(retry_after) if retry_after else None
                self.rate_limiter.handle_429_response(retry_after)
                return self._make_request(endpoint, params)

            response.raise_for_status()
            self.rate_limiter.reset_backoff()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise  # Re-raise 404 for caller handling
            logger.error(f"HTTP error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return None


class HistoricalDataFetcher:
    """Main class for fetching historical congressional data"""

    # HISTORICAL_CONGRESSES = [113, 114, 115, 116, 117]  # 2013-2023
    HISTORICAL_CONGRESSES = [117, 116, 115, 114, 113]  # 2013-2023

    def __init__(self, base_dir: str = "data", max_workers: int = 8):
        """
        Initialize historical data fetcher

        Args:
            base_dir: Base directory for data storage
            max_workers: Maximum parallel workers
        """
        self.base_dir = Path(base_dir)
        self.historical_dir = self.base_dir / "historical"
        self.historical_dir.mkdir(parents=True, exist_ok=True)

        self.max_workers = max_workers
        self.api = HistoricalCongressAPI(max_workers=max_workers)

        # Initialize job queue
        self.queue = JobQueue(self.historical_dir / "job_queue.pkl")

        # Data type configurations
        self.data_types = {
            "bills": {
                "required_fields": ["congress", "type", "number", "title"],
                "endpoint_template": "/bill/{congress}",
                "compress": True,
            },
            "members": {
                "required_fields": ["bioguideId", "name", "party"],
                "endpoint_template": "/member/{congress}",
                "compress": True,
            },
            "house_votes": {
                "required_fields": ["congress", "rollCall", "chamber"],
                "endpoint_template": "/house-vote/{congress}",
                "compress": True,
            },
            "senate_votes": {
                "required_fields": ["congress", "rollCall", "chamber"],
                "endpoint_template": "/senate-vote/{congress}",
                "compress": True,
            },
        }

    def create_historical_jobs(
        self, congresses: List[int] = None, data_types: List[str] = None
    ) -> int:
        """
        Create jobs for historical data collection

        Args:
            congresses: List of congress numbers (defaults to HISTORICAL_CONGRESSES)
            data_types: List of data types to fetch (defaults to all)

        Returns:
            Number of jobs created
        """
        if congresses is None:
            congresses = self.HISTORICAL_CONGRESSES

        if data_types is None:
            data_types = list(self.data_types.keys())

        jobs_created = 0

        for congress in congresses:
            for data_type in data_types:
                # Check if data already exists and is complete
                if self._is_data_complete(congress, data_type):
                    logger.info(
                        f"Skipping {data_type} for congress {congress} - already complete"
                    )
                    continue

                job_id = f"{congress}_{data_type}"
                job = FetchJob(
                    job_id=job_id,
                    congress=congress,
                    data_type=data_type,
                    priority=1,  # All historical jobs have same priority
                    estimated_size=self._estimate_job_size(congress, data_type),
                )

                self.queue.add_job(job)
                jobs_created += 1
                logger.info(f"Created job: {job_id}")

        logger.info(f"Created {jobs_created} historical data jobs")
        return jobs_created

    def _is_data_complete(self, congress: int, data_type: str) -> bool:
        """Check if data for a congress/type is already complete"""
        data_dir = self.historical_dir / str(congress) / data_type
        index_file = data_dir / "index.json"

        if not index_file.exists():
            return False

        try:
            with open(index_file) as f:
                index_data = json.load(f)

            # Check if marked as complete and has reasonable amount of data
            if index_data.get("complete", False) and index_data.get("count", 0) > 0:
                return True
        except Exception as e:
            logger.warning(f"Error checking completion status: {e}")

        return False

    def _estimate_job_size(self, congress: int, data_type: str) -> int:
        """Estimate the size of a job based on historical data"""
        # Rough estimates based on typical congress sizes
        estimates = {
            "bills": 10000,  # ~10k bills per congress
            "members": 535,  # ~535 members
            "house_votes": 1000,  # ~1k House votes per congress
            "senate_votes": 500,  # ~500 Senate votes per congress
        }
        return estimates.get(data_type, 1000)

    def process_job(self, job: FetchJob) -> bool:
        """
        Process a single fetch job

        Args:
            job: The job to process

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            f"Processing job {job.job_id}: {job.data_type} for congress {job.congress}"
        )

        try:
            if job.data_type == "bills":
                return self._fetch_historical_bills(job)
            elif job.data_type == "members":
                return self._fetch_historical_members(job)
            elif job.data_type == "house_votes":
                return self._fetch_historical_votes(job, "house")
            elif job.data_type == "senate_votes":
                return self._fetch_historical_votes(job, "senate")
            else:
                logger.error(f"Unknown data type: {job.data_type}")
                return False

        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            return False

    def _fetch_historical_bills(self, job: FetchJob) -> bool:
        """Fetch historical bills for a congress"""
        congress = job.congress
        data_dir = self.historical_dir / str(congress) / "bills"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing records
        existing_records = self._load_existing_records(data_dir)

        endpoint = f"/bill/{congress}"
        offset = 0
        limit = 250  # Larger batches for historical data
        total_fetched = 0
        records_index = []

        while True:
            params = {"limit": limit, "offset": offset}

            logger.info(f"Fetching bills for congress {congress}, offset {offset}")

            data = self.api._make_request(endpoint, params)
            if not data:
                break

            bills = data.get("bills", [])
            if not bills:
                break

            for bill in bills:
                bill_id = (
                    f"{bill.get('congress')}_{bill.get('type')}_{bill.get('number')}"
                )

                # Skip if already exists
                if bill_id in existing_records:
                    continue

                # Fetch detailed bill data
                if bill.get("url"):
                    detail_endpoint = bill["url"].replace(self.api.BASE_URL + "/", "")
                    detailed_bill = self.api._make_request(detail_endpoint)
                    if detailed_bill and "bill" in detailed_bill:
                        bill = detailed_bill["bill"]

                # Validate record
                is_valid, missing_fields = (
                    DataIntegrityChecker.validate_record_completeness(
                        bill, self.data_types["bills"]["required_fields"]
                    )
                )

                if not is_valid:
                    logger.warning(f"Bill {bill_id} missing fields: {missing_fields}")
                    continue

                # Save record
                filepath = data_dir / f"{bill_id}.json"
                checksum = DataIntegrityChecker.calculate_checksum(bill)

                file_size = CompressedStorage.save_compressed_record(
                    bill, filepath, compress=self.data_types["bills"]["compress"]
                )

                DataIntegrityChecker.create_integrity_file(
                    filepath,
                    checksum,
                    {"data_type": "bills", "congress": congress, "record_id": bill_id},
                )

                records_index.append(
                    {
                        "id": bill_id,
                        "congress": congress,
                        "type": bill.get("type"),
                        "number": bill.get("number"),
                        "title": bill.get("title", "")[:200],  # Truncate for index
                        "checksum": checksum,
                        "file_size": file_size,
                        "created_at": datetime.now().isoformat(),
                    }
                )

                total_fetched += 1

            # Update progress
            job.progress = min(total_fetched / job.estimated_size, 0.95)

            # Check pagination
            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit

            # Save progress periodically
            if total_fetched % 1000 == 0:
                self._save_index(data_dir, records_index, complete=False)
                logger.info(f"Fetched {total_fetched} bills for congress {congress}")

        # Save final index
        self._save_index(data_dir, records_index, complete=True)

        logger.info(f"Completed fetching {total_fetched} bills for congress {congress}")
        return True

    def _fetch_historical_members(self, job: FetchJob) -> bool:
        """Fetch historical members for a congress"""
        congress = job.congress
        data_dir = self.historical_dir / str(congress) / "members"
        data_dir.mkdir(parents=True, exist_ok=True)

        existing_records = self._load_existing_records(data_dir)

        endpoint = f"/member/{congress}"
        offset = 0
        limit = 250
        total_fetched = 0
        records_index = []

        while True:
            params = {"limit": limit, "offset": offset}

            logger.info(f"Fetching members for congress {congress}, offset {offset}")

            data = self.api._make_request(endpoint, params)
            if not data:
                break

            members = data.get("members", [])
            if not members:
                break

            for member in members:
                member_id = member.get("bioguideId", "")
                if not member_id or member_id in existing_records:
                    continue

                # Fetch detailed member data
                if member.get("url"):
                    detail_endpoint = member["url"].replace(self.api.BASE_URL + "/", "")
                    detailed_member = self.api._make_request(detail_endpoint)
                    if detailed_member and "member" in detailed_member:
                        member = detailed_member["member"]

                # Validate record
                is_valid, missing_fields = (
                    DataIntegrityChecker.validate_record_completeness(
                        member, self.data_types["members"]["required_fields"]
                    )
                )

                if not is_valid:
                    logger.warning(
                        f"Member {member_id} missing fields: {missing_fields}"
                    )
                    continue

                # Save record
                filepath = data_dir / f"{member_id}.json"
                checksum = DataIntegrityChecker.calculate_checksum(member)

                file_size = CompressedStorage.save_compressed_record(
                    member, filepath, compress=self.data_types["members"]["compress"]
                )

                DataIntegrityChecker.create_integrity_file(
                    filepath,
                    checksum,
                    {
                        "data_type": "members",
                        "congress": congress,
                        "record_id": member_id,
                    },
                )

                records_index.append(
                    {
                        "id": member_id,
                        "congress": congress,
                        "name": member.get("name", ""),
                        "party": member.get("party", ""),
                        "state": member.get("state", ""),
                        "checksum": checksum,
                        "file_size": file_size,
                        "created_at": datetime.now().isoformat(),
                    }
                )

                total_fetched += 1

            # Update progress
            job.progress = min(total_fetched / job.estimated_size, 0.95)

            # Check pagination
            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit

        # Save final index
        self._save_index(data_dir, records_index, complete=True)

        logger.info(
            f"Completed fetching {total_fetched} members for congress {congress}"
        )
        return True

    def _fetch_historical_votes(self, job: FetchJob, chamber: str) -> bool:
        """Fetch historical votes for a congress and chamber"""
        congress = job.congress
        data_dir = self.historical_dir / str(congress) / f"{chamber}_votes"
        data_dir.mkdir(parents=True, exist_ok=True)

        existing_records = self._load_existing_records(data_dir)

        endpoint = f"/{chamber}-vote/{congress}"
        offset = 0
        limit = 250
        total_fetched = 0
        records_index = []

        while True:
            params = {"limit": limit, "offset": offset}

            logger.info(
                f"Fetching {chamber} votes for congress {congress}, offset {offset}"
            )

            data = self.api._make_request(endpoint, params)
            if not data:
                break

            votes = data.get("votes", []) or data.get("rollCalls", [])
            if not votes:
                break

            for vote in votes:
                vote_id = f"{congress}_{chamber}_{vote.get('rollCall', vote.get('number', ''))}"

                if vote_id in existing_records:
                    continue

                # Validate record
                data_type_key = f"{chamber}_votes"
                is_valid, missing_fields = (
                    DataIntegrityChecker.validate_record_completeness(
                        vote, self.data_types[data_type_key]["required_fields"]
                    )
                )

                if not is_valid:
                    logger.warning(f"Vote {vote_id} missing fields: {missing_fields}")
                    continue

                # Save record
                filepath = data_dir / f"{vote_id}.json"
                checksum = DataIntegrityChecker.calculate_checksum(vote)

                file_size = CompressedStorage.save_compressed_record(
                    vote, filepath, compress=self.data_types[data_type_key]["compress"]
                )

                DataIntegrityChecker.create_integrity_file(
                    filepath,
                    checksum,
                    {
                        "data_type": f"{chamber}_votes",
                        "congress": congress,
                        "record_id": vote_id,
                    },
                )

                records_index.append(
                    {
                        "id": vote_id,
                        "congress": congress,
                        "chamber": chamber,
                        "roll_call": vote.get("rollCall", vote.get("number", "")),
                        "date": vote.get("date", ""),
                        "question": vote.get("question", "")[:200],
                        "checksum": checksum,
                        "file_size": file_size,
                        "created_at": datetime.now().isoformat(),
                    }
                )

                total_fetched += 1

            # Update progress
            job.progress = min(total_fetched / job.estimated_size, 0.95)

            # Check pagination
            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit

        # Save final index
        self._save_index(data_dir, records_index, complete=True)

        logger.info(
            f"Completed fetching {total_fetched} {chamber} votes for congress {congress}"
        )
        return True

    def _load_existing_records(self, data_dir: Path) -> Set[str]:
        """Load existing record IDs from a directory"""
        existing_records = set()

        index_file = data_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file) as f:
                    index_data = json.load(f)
                existing_records.update(
                    record.get("id", "") for record in index_data.get("records", [])
                )
            except Exception as e:
                logger.warning(f"Error loading existing records: {e}")

        return existing_records

    def _save_index(self, data_dir: Path, records: List[Dict], complete: bool = False):
        """Save index file with record metadata"""
        index_file = data_dir / "index.json"

        index_data = {
            "count": len(records),
            "complete": complete,
            "last_updated": datetime.now().isoformat(),
            "total_size_bytes": sum(r.get("file_size", 0) for r in records),
            "records": records,
        }

        with open(index_file, "w") as f:
            json.dump(index_data, f, indent=2)

    def run_historical_collection(
        self,
        congresses: List[int] = None,
        data_types: List[str] = None,
        resume: bool = True,
    ) -> None:
        """
        Run the historical data collection process

        Args:
            congresses: List of congress numbers to collect
            data_types: List of data types to collect
            resume: Whether to resume from existing queue
        """
        if not resume:
            # Clear existing queue
            self.queue.jobs.clear()

        # Create jobs if none exist or not resuming
        if not self.queue.jobs or not resume:
            jobs_created = self.create_historical_jobs(congresses, data_types)
            if jobs_created == 0:
                logger.info("No jobs to process - all data appears complete")
                return

        logger.info(
            f"Starting historical collection with {len(self.queue.jobs)} total jobs"
        )

        # Progress monitoring thread
        def monitor_progress():
            while True:
                progress = self.queue.get_progress()
                logger.info(
                    f"Progress: {progress.completion_percentage:.1f}% "
                    f"({progress.completed_jobs}/{progress.total_jobs}) "
                    f"Failed: {progress.failed_jobs}, Running: {progress.running_jobs}"
                )

                if progress.estimated_completion:
                    logger.info(
                        f"ETA: {progress.estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                if (
                    progress.completed_jobs + progress.failed_jobs
                    >= progress.total_jobs
                ):
                    break

                time.sleep(60)  # Update every minute

        # Start progress monitoring
        progress_thread = threading.Thread(target=monitor_progress, daemon=True)
        progress_thread.start()

        # Process jobs with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            # Submit initial batch of jobs
            for _ in range(self.max_workers):
                job = self.queue.get_next_job()
                if job:
                    future = executor.submit(self.process_job, job)
                    futures[future] = job.job_id

            # Process completed jobs and submit new ones
            while futures:
                for future in as_completed(futures):
                    job_id = futures[future]
                    success = False
                    error_message = None

                    try:
                        success = future.result()
                    except Exception as e:
                        error_message = str(e)
                        logger.error(f"Job {job_id} failed with exception: {e}")

                    # Mark job as complete
                    self.queue.complete_job(job_id, success, error_message)

                    # Remove from futures
                    del futures[future]

                    # Submit next job if available
                    next_job = self.queue.get_next_job()
                    if next_job:
                        new_future = executor.submit(self.process_job, next_job)
                        futures[new_future] = next_job.job_id

                    break  # Break to restart the iteration after dict modification

        # Final progress report
        final_progress = self.queue.get_progress()
        logger.info("Historical collection completed!")
        logger.info(f"Total jobs: {final_progress.total_jobs}")
        logger.info(f"Successful: {final_progress.completed_jobs}")
        logger.info(f"Failed: {final_progress.failed_jobs}")
        logger.info(f"Total time: {final_progress.elapsed_time}")

    def get_collection_summary(self) -> Dict:
        """Get summary of historical data collection"""
        summary = {
            "congresses": {},
            "total_records": 0,
            "total_size_bytes": 0,
            "data_types": list(self.data_types.keys()),
            "generated_at": datetime.now().isoformat(),
        }

        for congress in self.HISTORICAL_CONGRESSES:
            congress_dir = self.historical_dir / str(congress)
            if not congress_dir.exists():
                continue

            congress_summary = {
                "congress": congress,
                "data_types": {},
                "total_records": 0,
                "total_size": 0,
            }

            for data_type in self.data_types.keys():
                data_dir = congress_dir / data_type
                index_file = data_dir / "index.json"

                if index_file.exists():
                    try:
                        with open(index_file) as f:
                            index_data = json.load(f)

                        type_summary = {
                            "count": index_data.get("count", 0),
                            "complete": index_data.get("complete", False),
                            "size_bytes": index_data.get("total_size_bytes", 0),
                            "last_updated": index_data.get("last_updated", ""),
                        }

                        congress_summary["data_types"][data_type] = type_summary
                        congress_summary["total_records"] += type_summary["count"]
                        congress_summary["total_size"] += type_summary["size_bytes"]

                    except Exception as e:
                        logger.warning(
                            f"Error reading index for {congress}/{data_type}: {e}"
                        )

            if congress_summary["total_records"] > 0:
                summary["congresses"][str(congress)] = congress_summary
                summary["total_records"] += congress_summary["total_records"]
                summary["total_size_bytes"] += congress_summary["total_size"]

        return summary


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Fetch historical congressional data")
    parser.add_argument(
        "--congresses",
        nargs="+",
        type=int,
        default=HistoricalDataFetcher.HISTORICAL_CONGRESSES,
        help="Congress numbers to fetch (default: 117-113)",
    )
    parser.add_argument(
        "--data-types",
        nargs="+",
        choices=["bills", "members", "house_votes", "senate_votes"],
        help="Data types to fetch (default: all)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum parallel workers (default: 8)",
    )
    parser.add_argument(
        "--output-dir", default="data", help="Output directory (default: data)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from existing queue (default: True)",
    )
    parser.add_argument(
        "--no-resume", action="store_true", help="Start fresh, ignore existing queue"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show collection summary and exit"
    )
    parser.add_argument(
        "--create-jobs-only",
        action="store_true",
        help="Create jobs without running them",
    )

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = HistoricalDataFetcher(
        base_dir=args.output_dir, max_workers=args.max_workers
    )

    if args.summary:
        summary = fetcher.get_collection_summary()
        print(json.dumps(summary, indent=2))
        return

    resume = args.resume and not args.no_resume

    if args.create_jobs_only:
        jobs_created = fetcher.create_historical_jobs(args.congresses, args.data_types)
        logger.info(f"Created {jobs_created} jobs. Use --resume to run them.")
        return

    # Run historical collection
    fetcher.run_historical_collection(
        congresses=args.congresses, data_types=args.data_types, resume=resume
    )

    # Print summary
    summary = fetcher.get_collection_summary()
    print("\n" + "=" * 60)
    print("HISTORICAL DATA COLLECTION SUMMARY")
    print("=" * 60)
    print(f"Total records collected: {summary['total_records']:,}")
    print(f"Total size: {summary['total_size_bytes'] / (1024*1024*1024):.2f} GB")
    print(f"Congresses: {', '.join(summary['congresses'].keys())}")
    print(f"Data types: {', '.join(summary['data_types'])}")
    print("\nBy Congress:")
    for congress, data in summary["congresses"].items():
        print(
            f"  {congress}: {data['total_records']:,} records "
            f"({data['total_size'] / (1024*1024):.1f} MB)"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
