"""
Unified Senate.gov API client.

Provides comprehensive access to Senate.gov Lobbying Disclosure API
with unified functionality from all existing implementations.
"""

import logging
import os
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

from ..storage.file_storage import save_index, save_individual_record
from .base import BaseAPI
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class SenateGovAPI(BaseAPI):
    """
    Unified Senate.gov API client for lobbying disclosure data

    Combines functionality from:
    - gov_data_downloader.py
    - gov_data_downloader_v2.py
    """

    BASE_URL = "https://lda.senate.gov/api"

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize Senate.gov API client

        Args:
            username: API username (optional, uses .env if not provided)
            password: API password (optional, uses .env if not provided)
        """
        self.token = os.getenv("SENATE_GOV_TOKEN")
        self.username = username or os.getenv("SENATE_GOV_USERNAME")
        self.password = password or os.getenv("SENATE_GOV_PASSWORD")

        # Rate limiter: 120/minute for authenticated, 15/minute for anonymous
        if self.token or (self.username and self.password):
            rate_limiter = RateLimiter(
                max_requests=120, time_window=60, name="SenateGovAPI-Auth"
            )
            logger.info("Using authenticated rate limit (120 requests/minute)")
        else:
            rate_limiter = RateLimiter(
                max_requests=15, time_window=60, name="SenateGovAPI-Anonymous"
            )
            logger.info("Using anonymous rate limit (15 requests/minute)")

        super().__init__(self.BASE_URL, rate_limiter, name="SenateGovAPI")

        # Authenticate if credentials are available
        if not self.token and self.username and self.password:
            self.authenticate()

    def authenticate(self):
        """Authenticate with senate.gov API"""
        try:
            url = urljoin(self.BASE_URL, "/auth/login/")
            response = self.session.post(
                url, json={"username": self.username, "password": self.password}
            )
            response.raise_for_status()

            data = response.json()
            self.token = data.get("token")

            if self.token:
                # Save token to .env file
                with open(".env", "a") as f:
                    f.write(f"\nSENATE_GOV_TOKEN={self.token}\n")
                logger.info("Successfully authenticated with senate.gov")

                # Update rate limiter to authenticated limits
                self.rate_limiter = RateLimiter(
                    max_requests=120, time_window=60, name="SenateGovAPI-Auth"
                )
            else:
                logger.warning("Authentication successful but no token received")

        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        retries: int = 3,
        timeout: int = 30,
    ) -> Optional[Dict]:
        """
        Make a rate-limited request to the API

        Args:
            endpoint: API endpoint
            params: Query parameters
            retries: Number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            Response data or None if failed
        """
        headers = {}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"

        return super()._make_request(endpoint, params, headers, retries, timeout)

    def get_filings(
        self,
        filing_type: str = "LD-1",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 25,
        max_results: int = 25,
        output_dir: str = "data",
        incremental: bool = True,
        individual_files: bool = False,
    ) -> List[Dict]:
        """
        Get lobbying disclosure filings

        Args:
            filing_type: Type of filing (YY for Year-End Reports, MM for Mid-Year Reports, YT for Year-End Termination)
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            limit: Maximum number of results per page (default 25)
            max_results: Maximum total results to fetch (default 25)
            output_dir: Directory for incremental saves
            incremental: Whether to save incrementally
            individual_files: Whether to save each record as individual file

        Returns:
            List of filing records
        """
        endpoint = "/v1/filings/"
        params = {"filing_type": filing_type, "limit": limit}

        if start_date:
            params["filed_date__gte"] = start_date
        if end_date:
            params["filed_date__lte"] = end_date

        filename = f"senate_{filing_type.lower().replace('-', '')}_filings.json"
        all_filings = []
        page = 1

        # Check if we have existing data to skip or resume from
        if incremental:
            import json
            from pathlib import Path

            filepath = Path(output_dir) / filename
            if filepath.exists():
                try:
                    with open(filepath) as f:
                        existing_data = json.load(f)
                    # Check if we need to update (simple check based on count)
                    if len(existing_data) >= max_results:
                        logger.info(
                            f"Existing file has {len(existing_data)} records, skipping download"
                        )
                        return existing_data[:max_results]
                    # Resume from where we left off
                    all_filings = existing_data
                    page = (len(all_filings) // limit) + 1
                    logger.info(
                        f"Resuming from page {page} with {len(all_filings)} existing filings"
                    )
                except Exception as e:
                    logger.warning(f"Could not load existing data: {e}")

        batch_count = 0

        while len(all_filings) < max_results:
            params["page"] = page
            logger.info(f"Fetching {filing_type} filings page {page}...")

            data = self._make_request(endpoint, params)
            if not data:
                break

            results = data.get("results", [])
            if not results:
                break

            # Save individual files if requested
            if individual_files:
                for filing in results:
                    filing_id = (
                        filing.get("filing_uuid")
                        or filing.get("id")
                        or f"filing_{len(all_filings)}"
                    )
                    record_type = f"senate_filings/{filing_type.lower()}"
                    save_individual_record(filing, record_type, filing_id, output_dir)

            all_filings.extend(results)

            # Check if there are more pages
            if not data.get("next"):
                break

            batch_count += 1

            # Save incrementally every 3 batches
            if incremental and batch_count % 3 == 0:
                self._save_data(all_filings, filename, output_dir)
                logger.info(f"Saved checkpoint: {len(all_filings)} filings")

            # Check if we've reached the max
            if len(all_filings) >= max_results:
                logger.info(f"Reached maximum results limit: {max_results}")
                break

            page += 1

            # Be respectful, add small delay between pages
            time.sleep(0.5)

        # Final save
        if incremental:
            self._save_data(all_filings, filename, output_dir)

        # Save index if using individual files
        if individual_files:
            save_index(all_filings, f"senate_filings/{filing_type.lower()}", output_dir)

        logger.info(f"Retrieved {len(all_filings)} {filing_type} filings")
        return all_filings[:max_results]

    def get_lobbyists(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 25,
        max_results: int = 25,
        output_dir: str = "data",
        incremental: bool = True,
        individual_files: bool = False,
    ) -> List[Dict]:
        """
        Get lobbyist information

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum results per page (default 25)
            max_results: Maximum total results to fetch (default 25)
            output_dir: Directory for incremental saves
            incremental: Whether to save incrementally
            individual_files: Whether to save each record as individual file

        Returns:
            List of lobbyist records
        """
        endpoint = "/v1/lobbyists/"
        params = {"limit": limit}

        if start_date:
            params["created__gte"] = start_date
        if end_date:
            params["created__lte"] = end_date

        filename = "senate_lobbyists.json"
        all_lobbyists = []
        page = 1

        # Check if we have existing data
        if incremental:
            import json
            from pathlib import Path

            filepath = Path(output_dir) / filename
            if filepath.exists():
                try:
                    with open(filepath) as f:
                        existing_data = json.load(f)
                    if len(existing_data) >= max_results:
                        logger.info(
                            f"Existing file has {len(existing_data)} records, skipping download"
                        )
                        return existing_data[:max_results]
                    all_lobbyists = existing_data
                    page = (len(all_lobbyists) // limit) + 1
                    logger.info(
                        f"Resuming from page {page} with {len(all_lobbyists)} existing lobbyists"
                    )
                except Exception as e:
                    logger.warning(f"Could not load existing data: {e}")

        batch_count = 0

        while len(all_lobbyists) < max_results:
            params["page"] = page
            logger.info(f"Fetching lobbyists page {page}...")

            data = self._make_request(endpoint, params)
            if not data:
                break

            results = data.get("results", [])
            if not results:
                break

            # Save individual files if requested
            if individual_files:
                for lobbyist in results:
                    lobbyist_id = (
                        lobbyist.get("lobbyist_id")
                        or lobbyist.get("id")
                        or f"lobbyist_{len(all_lobbyists)}"
                    )
                    # Clean the name for use as identifier
                    name = lobbyist.get("name", "").replace(" ", "_").replace(",", "")
                    if name:
                        lobbyist_id = f"{lobbyist_id}_{name}"

                    save_individual_record(
                        lobbyist, "senate_lobbyists", lobbyist_id, output_dir
                    )

            all_lobbyists.extend(results)

            if not data.get("next"):
                break

            batch_count += 1

            # Save incrementally
            if incremental and batch_count % 3 == 0:
                self._save_data(all_lobbyists, filename, output_dir)
                logger.info(f"Saved checkpoint: {len(all_lobbyists)} lobbyists")

            if len(all_lobbyists) >= max_results:
                logger.info(f"Reached maximum results limit: {max_results}")
                break

            page += 1
            time.sleep(0.5)

        # Final save
        if incremental:
            self._save_data(all_lobbyists, filename, output_dir)

        # Save index if using individual files
        if individual_files:
            save_index(all_lobbyists, "senate_lobbyists", output_dir)

        logger.info(f"Retrieved {len(all_lobbyists)} lobbyists")
        return all_lobbyists[:max_results]

    def get_filing_by_id(self, filing_id: str) -> Optional[Dict]:
        """
        Get a specific filing by ID

        Args:
            filing_id: Filing ID or UUID

        Returns:
            Filing data or None if not found
        """
        endpoint = f"/v1/filings/{filing_id}/"
        return self._make_request(endpoint)

    def get_lobbyist_by_id(self, lobbyist_id: str) -> Optional[Dict]:
        """
        Get a specific lobbyist by ID

        Args:
            lobbyist_id: Lobbyist ID

        Returns:
            Lobbyist data or None if not found
        """
        endpoint = f"/v1/lobbyists/{lobbyist_id}/"
        return self._make_request(endpoint)

    def search_filings(
        self,
        query: str,
        filing_type: Optional[str] = None,
        limit: int = 25,
        max_results: int = 25,
    ) -> List[Dict]:
        """
        Search filings by text query

        Args:
            query: Search query
            filing_type: Optional filing type filter
            limit: Results per page
            max_results: Maximum total results

        Returns:
            List of matching filing records
        """
        endpoint = "/v1/filings/"
        params = {"search": query, "limit": limit}

        if filing_type:
            params["filing_type"] = filing_type

        all_results = []
        page = 1

        while len(all_results) < max_results:
            params["page"] = page
            data = self._make_request(endpoint, params)

            if not data:
                break

            results = data.get("results", [])
            if not results:
                break

            all_results.extend(results)

            if not data.get("next") or len(all_results) >= max_results:
                break

            page += 1
            time.sleep(0.5)

        logger.info(f"Found {len(all_results)} filings matching '{query}'")
        return all_results[:max_results]

    def _save_data(self, data: List[Dict], filename: str, output_dir: str = "data"):
        """Save data to JSON file"""
        import json
        from pathlib import Path

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filepath = Path(output_dir) / filename

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(data)} records to {filepath}")

    def get_api_info(self) -> Dict:
        """
        Get API information and status

        Returns:
            API info dictionary
        """
        endpoint = "/v1/"
        data = self._make_request(endpoint)

        if data:
            return data

        return {
            "status": "unknown",
            "authenticated": bool(self.token),
            "rate_limit_stats": self.rate_limiter.get_stats(),
        }
