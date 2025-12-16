"""
Unified Congress.gov API client.

Provides comprehensive access to Congress.gov API (via data.gov)
with unified functionality from all existing implementations.
"""

import logging
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from core.storage.file_storage import save_individual_record

from .base import BaseAPI
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class CongressGovAPI(BaseAPI):
    """
    Unified Congress.gov API client with all features from existing implementations

    Combines functionality from:
    - gov_data_downloader.py
    - gov_data_analyzer.py
    - gov_data_downloader_v2.py
    - Other analysis scripts
    """

    BASE_URL = "https://api.congress.gov/v3"

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_workers: int = 5,
        max_requests: int = 900,
        time_window: int = 3600,
    ):
        """
        Initialize Congress.gov API client

        Args:
            api_key: API key (optional, uses .env if not provided)
            max_workers: Maximum parallel workers for concurrent operations
            max_requests: Maximum requests per time window (default: 900/hour)
            time_window: Time window in seconds (default: 1 hour)
        """
        # Support both DATA_GOV_API_KEY and CONGRESS_GOV_API_KEY for flexibility
        self.api_key = (
            api_key
            or os.getenv("DATA_GOV_API_KEY")
            or os.getenv("CONGRESS_GOV_API_KEY")
        )

        # Congress.gov rate limit via data.gov: 1000 requests per hour per API key
        # Being conservative to ensure compliance
        rate_limiter = RateLimiter(max_requests, time_window, name="CongressGovAPI")

        super().__init__(self.BASE_URL, rate_limiter, name="CongressGovAPI")

        self.max_workers = max_workers

        if not self.api_key:
            logger.warning(
                "No Congress.gov API key provided. Get one at: https://api.data.gov/signup/"
            )

        # Cache for member data
        self.members_cache = {}
        self.party_cache = {}

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        retries: int = 3,
        timeout: int = 30,
    ) -> Optional[Dict]:
        """
        Make a rate-limited request to Congress.gov API

        Args:
            endpoint: API endpoint
            params: Query parameters
            retries: Number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            Response data or None if failed
        """
        if not params:
            params = {}

        # For data.gov APIs, the API key should be in the header
        headers = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        params["format"] = "json"

        return super()._make_request(endpoint, params, headers, retries, timeout)

    def get_bills(
        self,
        congress: Optional[int] = None,
        limit: int = 25,
        max_results: int = 25,
        output_dir: str = "data",
        incremental: bool = True,
        bill_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get bills from Congress

        Args:
            congress: Congress number (e.g., 118 for 118th Congress), None for all
            limit: Number of results per page
            max_results: Maximum total results to fetch
            output_dir: Directory for incremental saves
            incremental: Whether to save incrementally
            bill_type: Specific bill type filter (hr, s, hjres, sjres, etc.)

        Returns:
            List of bill records
        """
        # Build endpoint based on parameters
        if congress and bill_type:
            endpoint = f"/bill/{congress}/{bill_type}"
            filename = f"congress_{congress}_{bill_type}_bills.json"
        elif congress:
            endpoint = f"/bill/{congress}"
            filename = f"congress_{congress}_bills.json"
        else:
            endpoint = "/bill"
            filename = "congress_all_bills.json"

        all_bills = []
        offset = 0

        # Check if we have existing data to resume from
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
                            f"Using existing data: {len(existing_data)} bills already cached"
                        )
                        return existing_data[:max_results]
                    all_bills = existing_data
                    offset = len(all_bills)
                    logger.info(
                        f"Resuming from offset {offset} with {len(all_bills)} existing bills"
                    )
                except Exception as e:
                    logger.warning(f"Could not load existing data: {e}")

        batch_count = 0

        while len(all_bills) < max_results:
            params = {
                "limit": min(limit, max_results - len(all_bills)),
                "offset": offset,
            }

            logger.info(
                f"Fetching bills (offset: {offset}, {len(all_bills)}/{max_results})..."
            )

            data = self._make_request(endpoint, params)
            if not data:
                break

            bills = data.get("bills", [])
            if not bills:
                break

            all_bills.extend(bills)
            batch_count += 1

            # Save incrementally every 5 batches
            if incremental and batch_count % 5 == 0:
                self._save_data(all_bills, filename, output_dir)
                logger.info(f"Saved checkpoint: {len(all_bills)} bills")

            if len(all_bills) >= max_results:
                logger.info(f"Reached maximum results limit: {max_results}")
                break

            # Check pagination
            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit
            time.sleep(0.5)  # Be respectful

        # Final save
        if incremental:
            self._save_data(all_bills, filename, output_dir)

        logger.info(f"Retrieved {len(all_bills)} bills")
        return all_bills[:max_results]

    def get_bill_details(
        self, congress: int, bill_type: str, bill_number: str
    ) -> Optional[Dict]:
        """
        Get detailed information about a specific bill

        Args:
            congress: Congress number
            bill_type: Bill type (hr, s, hjres, sjres, etc.)
            bill_number: Bill number

        Returns:
            Detailed bill information or None if not found
        """
        endpoint = f"/bill/{congress}/{bill_type.lower()}/{bill_number}"
        data = self._make_request(endpoint)

        if data and "bill" in data:
            return data["bill"]
        return None

    def get_bill_subjects(
        self, congress: int, bill_type: str, bill_number: str
    ) -> List[str]:
        """
        Get subjects/topics for a specific bill

        Args:
            congress: Congress number
            bill_type: Bill type
            bill_number: Bill number

        Returns:
            List of subject strings
        """
        endpoint = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/subjects"
        data = self._make_request(endpoint)

        subjects = []
        if data and "subjects" in data:
            for subject in data["subjects"]:
                if isinstance(subject, dict) and "name" in subject:
                    subjects.append(subject["name"])
                elif isinstance(subject, str):
                    subjects.append(subject)

        return subjects

    def get_bill_actions(
        self, congress: int, bill_type: str, bill_number: str
    ) -> List[Dict]:
        """
        Get actions taken on a specific bill

        Args:
            congress: Congress number
            bill_type: Bill type
            bill_number: Bill number

        Returns:
            List of action records
        """
        endpoint = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/actions"
        data = self._make_request(endpoint, {"limit": 250})

        if data and "actions" in data:
            return data["actions"]
        return []

    def get_members(
        self,
        congress: int,
        chamber: str = "house",
        limit: int = 25,
        max_results: int = 25,
        current_only: bool = True,
    ) -> List[Dict]:
        """
        Get members of Congress

        Args:
            congress: Congress number
            chamber: Chamber ('house' or 'senate')
            limit: Results per page
            max_results: Maximum total results
            current_only: Only get current members

        Returns:
            List of member records
        """
        # Use the general member endpoint with filters
        endpoint = "/member"
        all_members = []
        offset = 0

        while len(all_members) < max_results:
            params = {
                "limit": min(limit, max_results - len(all_members)),
                "offset": offset,
            }

            if current_only:
                params["currentMember"] = "true"

            logger.info(
                f"Fetching {chamber} members from {congress}th Congress (offset: {offset})..."
            )

            data = self._make_request(endpoint, params)
            if not data:
                break

            members = data.get("members", [])
            if not members:
                break

            # Filter by chamber if needed
            # Since we're getting all members, filter based on their terms
            for member in members:
                terms = member.get("terms", {}).get("item", [])
                # Check if member served in the requested chamber
                for term in terms:
                    term_chamber = term.get("chamber", "").lower()
                    if (
                        chamber.lower() == "house"
                        and "house" in term_chamber
                        or chamber.lower() == "senate"
                        and "senate" in term_chamber
                    ):
                        all_members.append(member)
                        break

            if len(all_members) >= max_results:
                break

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit
            time.sleep(0.5)

        logger.info(f"Retrieved {len(all_members)} {chamber} members")
        return all_members[:max_results]

    def get_house_votes(
        self,
        congress: int,
        session: Optional[int] = None,
        limit: int = 25,
        max_results: int = 25,
    ) -> List[Dict]:
        """
        Get House roll call votes

        Args:
            congress: Congress number
            session: Session number (optional)
            limit: Results per page
            max_results: Maximum results to fetch

        Returns:
            List of vote records
        """
        if session:
            endpoint = f"/house-vote/{congress}/{session}"
        else:
            endpoint = f"/house-vote/{congress}"

        all_votes = []
        offset = 0

        while len(all_votes) < max_results:
            params = {
                "limit": min(limit, max_results - len(all_votes)),
                "offset": offset,
            }

            logger.info(
                f"Fetching House votes from {congress}th Congress (offset: {offset})..."
            )

            data = self._make_request(endpoint, params)
            if not data:
                break

            votes = (
                data.get("votes", [])
                or data.get("rollCalls", [])
                or data.get("houseVotes", [])
            )
            if not votes:
                break

            all_votes.extend(votes)

            if len(all_votes) >= max_results:
                logger.info(f"Reached maximum results limit: {max_results}")
                break

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit
            time.sleep(0.5)

        logger.info(f"Retrieved {len(all_votes)} House votes")
        return all_votes[:max_results]

    def get_vote_details(
        self,
        congress: int,
        chamber: str,
        session: int,
        vote_number: int,
        base_dir: str = "data",
    ) -> Optional[Dict]:
        """
        Get detailed vote information including how each member voted

        Args:
            congress: Congress number
            chamber: Chamber ('house' or 'senate')
            session: Session number
            vote_number: Vote number
            base_dir: Base directory for storage

        Returns:
            Detailed vote record or None if not found
        """
        if chamber.lower() == "house":
            # Get vote details
            detail_endpoint = f"/house-vote/{congress}/{session}/{vote_number}"
            data = self._make_request(detail_endpoint)

            if not data:
                return None

            vote_info = data.get("rollCall", {})

            # Get member votes
            members_endpoint = f"/house-vote/{congress}/{session}/{vote_number}/members"
            members_data = self._make_request(members_endpoint)

            if members_data:
                # Organize votes by party
                party_breakdown = defaultdict(
                    lambda: {"yea": 0, "nay": 0, "present": 0, "not_voting": 0}
                )
                member_votes = []

                for member_vote in members_data.get("members", []):
                    vote_position = member_vote.get("votePosition", "").lower()
                    party = member_vote.get("party", "Unknown")

                    # Normalize vote position
                    if "yea" in vote_position or "aye" in vote_position:
                        vote_key = "yea"
                    elif "nay" in vote_position or "no" in vote_position:
                        vote_key = "nay"
                    elif "present" in vote_position:
                        vote_key = "present"
                    else:
                        vote_key = "not_voting"

                    party_breakdown[party][vote_key] += 1

                    member_votes.append(
                        {
                            "bioguideId": member_vote.get("bioguideId"),
                            "name": member_vote.get("name"),
                            "party": party,
                            "state": member_vote.get("state"),
                            "vote": vote_position,
                        }
                    )

                # Combine vote info with member votes
                detailed_vote = {
                    "congress": congress,
                    "session": session,
                    "rollCall": vote_number,
                    "chamber": chamber,
                    "question": vote_info.get("question", ""),
                    "description": vote_info.get("description", ""),
                    "date": vote_info.get("date", ""),
                    "result": vote_info.get("result", ""),
                    "bill": vote_info.get("bill", {}),
                    "party_breakdown": dict(party_breakdown),
                    "totals": {
                        "yea": vote_info.get("yea", 0),
                        "nay": vote_info.get("nay", 0),
                        "present": vote_info.get("present", 0),
                        "not_voting": vote_info.get("notVoting", 0),
                    },
                    "member_votes": member_votes,
                }

                # Save detailed vote
                vote_id = f"{congress}_{session}_{vote_number}"
                record_type = f"house_votes_detailed/{congress}"
                save_individual_record(detailed_vote, record_type, vote_id, base_dir)

                logger.info(
                    f"Saved detailed vote {vote_number}: {vote_info.get('question', '')[:50]}"
                )

                return detailed_vote

        return None

    def get_detailed_votes(
        self,
        congress: int,
        chamber: str = "house",
        max_votes: int = 25,
        base_dir: str = "data",
    ) -> List[Dict]:
        """
        Get roll call votes with detailed member voting records

        Args:
            congress: Congress number
            chamber: Chamber ('house' or 'senate')
            max_votes: Maximum number of votes to fetch details for
            base_dir: Base directory for storage

        Returns:
            List of vote records with member details
        """
        if chamber.lower() == "house":
            endpoint = f"/house-vote/{congress}"
            # record_type = f"house_votes_detailed/{congress}"  # Could be used for storage paths
        else:
            logger.warning(
                "Senate vote details not available via API, using bill votes"
            )
            return self._get_senate_votes_from_bills(congress, max_votes, base_dir)

        all_votes = []
        offset = 0
        limit = 20

        logger.info(f"Fetching {chamber} roll call votes from {congress}th Congress...")

        while len(all_votes) < max_votes:
            params = {"limit": min(limit, max_votes - len(all_votes)), "offset": offset}
            data = self._make_request(endpoint, params)

            if not data:
                break

            votes = data.get("votes", []) or data.get("rollCalls", [])
            if not votes:
                break

            # Process votes in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                for vote in votes[: max_votes - len(all_votes)]:
                    vote_number = vote.get("rollCall") or vote.get("number")
                    session = vote.get("session", 1)

                    if vote_number:
                        future = executor.submit(
                            self.get_vote_details,
                            congress,
                            session,
                            vote_number,
                            chamber,
                            base_dir,
                        )
                        futures.append((future, vote))

                for future, _vote in futures:
                    try:
                        detailed_vote = future.result(timeout=30)
                        if detailed_vote:
                            all_votes.append(detailed_vote)
                    except Exception as e:
                        logger.error(f"Error getting vote details: {e}")

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += limit
            time.sleep(0.5)

        logger.info(f"Retrieved {len(all_votes)} detailed votes")
        return all_votes

    def _get_senate_votes_from_bills(
        self, congress: int, max_votes: int, base_dir: str
    ) -> List[Dict]:
        """Get Senate votes by fetching bills with vote data"""
        endpoint = f"/bill/{congress}"
        votes = []
        offset = 0

        logger.info(f"Fetching Senate votes from bills in {congress}th Congress...")
        bills_processed = 0
        senate_bills_found = 0
        max_bills_to_process = 1000  # Prevent infinite processing

        while len(votes) < max_votes and bills_processed < max_bills_to_process:
            params = {"limit": 100, "offset": offset}
            logger.info(
                f"Fetching bills batch (offset: {offset}, votes found so far: {len(votes)}/{max_votes})..."
            )
            data = self._make_request(endpoint, params)

            if not data:
                logger.info("No more data available")
                break

            bills = data.get("bills", [])
            if not bills:
                logger.info("No bills in response")
                break

            logger.info(
                f"Processing {len(bills)} bills from batch (offset {offset})..."
            )

            for bill in bills:
                bills_processed += 1
                if len(votes) >= max_votes:
                    logger.info(f"Reached max_votes limit ({max_votes})")
                    break

                # Only process Senate-origin bills
                if bill.get("originChamberCode") == "S":
                    senate_bills_found += 1
                    bill_type = bill.get("type", "").lower()
                    bill_number = bill.get("number", "")

                    if bill_type and bill_number:
                        if senate_bills_found % 10 == 0:  # Log every 10th Senate bill
                            logger.info(
                                f"Processing Senate bill {senate_bills_found}: {bill_type.upper()}{bill_number} (total bills processed: {bills_processed})"
                            )

                        try:
                            actions = self.get_bill_actions(
                                congress, bill_type, bill_number
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to get actions for {bill_type.upper()}{bill_number}: {e}"
                            )
                            continue

                        for action in actions:
                            action_text = action.get("text", "").lower()

                            # Look for vote actions
                            if any(
                                term in action_text
                                for term in [
                                    "passed senate",
                                    "vote",
                                    "yea",
                                    "nay",
                                    "agreed",
                                ]
                            ):
                                if (
                                    "roll call" in action_text
                                    or "recorded vote" in action_text
                                ):
                                    vote_record = {
                                        "congress": congress,
                                        "chamber": "senate",
                                        "bill": {
                                            "type": bill_type.upper(),
                                            "number": bill_number,
                                            "title": bill.get("title", ""),
                                        },
                                        "action": action.get("text"),
                                        "date": action.get("actionDate", ""),
                                        "action_code": action.get("actionCode", ""),
                                    }
                                    votes.append(vote_record)

                                    if len(votes) >= max_votes:
                                        break

            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break

            offset += 100

        # Final summary
        logger.info("📊 Senate vote collection completed:")
        logger.info(f"  - Total bills processed: {bills_processed}")
        logger.info(f"  - Senate bills found: {senate_bills_found}")
        logger.info(f"  - Vote records extracted: {len(votes)}")
        logger.info(f"  - Requested: {max_votes}")

        if bills_processed >= max_bills_to_process:
            logger.warning(
                f"Stopped processing after {max_bills_to_process} bills limit"
            )

        return votes

    def _save_data(self, data: List[Dict], filename: str, output_dir: str = "data"):
        """Save data to JSON file"""
        import json
        from pathlib import Path

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filepath = Path(output_dir) / filename

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(data)} records to {filepath}")

    def cache_member(self, bioguide_id: str, member_data: Dict):
        """Cache member data for later use"""
        self.members_cache[bioguide_id] = member_data
        if "party" in member_data:
            self.party_cache[bioguide_id] = member_data["party"]

    def get_cached_member(self, bioguide_id: str) -> Optional[Dict]:
        """Get cached member data"""
        return self.members_cache.get(bioguide_id)

    def get_member_party(self, bioguide_id: str) -> Optional[str]:
        """Get member party from cache"""
        return self.party_cache.get(bioguide_id)
