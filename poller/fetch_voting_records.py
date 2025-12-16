#!/usr/bin/env python3
"""
Voting Records Fetcher - Comprehensive tool to fetch and analyze congressional voting records
Addresses issues with House votes API and implements multiple fallback mechanisms
"""

import argparse
import json
import logging
import os
import time

# Import from consolidated core package
import warnings
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from core.api.rate_limiter import RateLimiter
from dotenv import load_dotenv

# Deprecation warning for this script
warnings.warn(
    "This script is deprecated. Use core package APIs directly or use comprehensive_analyzer.py",
    DeprecationWarning,
    stacklevel=2,
)

# Load environment variables
load_dotenv()


# RateLimiter is now imported from core.api.rate_limiter


class VotingRecordsFetcher:
    """Main class for fetching and analyzing congressional voting records"""

    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        """
        Initialize the voting records fetcher

        Args:
            api_key: Congress.gov API key
            verbose: Enable verbose logging
        """
        self.api_key = api_key or os.getenv("DATA_GOV_API_KEY")
        self.base_url = "https://api.congress.gov/v3"
        self.rate_limiter = RateLimiter(
            max_requests=115, time_window=60
        )  # Leave some buffer
        self.session = requests.Session()
        self.verbose = verbose

        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            raise ValueError("DATA_GOV_API_KEY environment variable is required")

        # Member data cache
        self.members_cache = {}
        self.party_cache = {}

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, retries: int = 3
    ) -> Optional[Dict]:
        """
        Make API request with rate limiting and error handling

        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            retries: Number of retry attempts

        Returns:
            API response data or None if failed
        """
        self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-Api-Key": self.api_key,
            "User-Agent": "Congress-Viewer/1.0 (Educational Use)",
        }

        if params is None:
            params = {}
        params["format"] = "json"

        for attempt in range(retries):
            try:
                self.logger.debug(f"Making request to: {url}")
                self.logger.debug(f"Parameters: {params}")

                response = self.session.get(
                    url, headers=headers, params=params, timeout=30
                )

                self.logger.debug(f"Response status: {response.status_code}")
                self.logger.debug(f"Response headers: {dict(response.headers)}")

                if response.status_code == 200:
                    data = response.json()
                    if self.verbose:
                        self.logger.debug(
                            f"Response keys: {list(data.keys()) if data else 'None'}"
                        )
                    return data
                elif response.status_code == 429:
                    wait_time = 2**attempt
                    self.logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 404:
                    self.logger.warning(f"Endpoint not found: {url}")
                    return None
                else:
                    self.logger.error(
                        f"API error {response.status_code}: {response.text}"
                    )
                    if attempt < retries - 1:
                        time.sleep(2**attempt)

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2**attempt)

        return None

    def debug_house_votes_api(self, congress: int = 118) -> Dict[str, Any]:
        """
        Debug why house-vote endpoint returns empty data

        Args:
            congress: Congress number to check

        Returns:
            Debug information about the API responses
        """
        debug_info = {
            "congress": congress,
            "endpoints_tested": [],
            "responses": {},
            "recommendations": [],
        }

        # Test various house vote endpoints
        endpoints_to_test = [
            f"/house-vote/{congress}",
            f"/house-vote/{congress}/1",  # Session 1
            f"/house-vote/{congress}/2",  # Session 2
            f"/vote/{congress}",
            f"/vote/{congress}/house",
        ]

        for endpoint in endpoints_to_test:
            self.logger.info(f"Testing endpoint: {endpoint}")
            debug_info["endpoints_tested"].append(endpoint)

            response_data = self._make_request(endpoint, {"limit": 5})

            if response_data:
                debug_info["responses"][endpoint] = {
                    "success": True,
                    "keys": list(response_data.keys()),
                    "data_structure": self._analyze_response_structure(response_data),
                }

                # Check for votes in response
                votes_found = self._extract_votes_from_response(response_data)
                debug_info["responses"][endpoint]["votes_found"] = len(votes_found)
                debug_info["responses"][endpoint]["sample_vote"] = (
                    votes_found[0] if votes_found else None
                )

            else:
                debug_info["responses"][endpoint] = {
                    "success": False,
                    "error": "No data returned",
                }

        # Generate recommendations
        working_endpoints = [
            ep
            for ep, resp in debug_info["responses"].items()
            if resp.get("success") and resp.get("votes_found", 0) > 0
        ]

        if working_endpoints:
            debug_info["recommendations"].append(
                f"Use working endpoints: {working_endpoints}"
            )
        else:
            debug_info["recommendations"].append(
                "Try alternative approach: fetch votes from bill actions"
            )
            debug_info["recommendations"].append(
                "Consider using Senate vote patterns as template"
            )

        return debug_info

    def _analyze_response_structure(self, data: Dict) -> Dict[str, Any]:
        """Analyze the structure of an API response"""
        structure = {}

        for key, value in data.items():
            if isinstance(value, list):
                structure[key] = {
                    "type": "list",
                    "length": len(value),
                    "sample_item": (
                        self._analyze_response_structure(value[0]) if value else None
                    ),
                }
            elif isinstance(value, dict):
                structure[key] = {"type": "dict", "keys": list(value.keys())}
            else:
                structure[key] = {
                    "type": type(value).__name__,
                    "sample_value": str(value)[:100] if value else None,
                }

        return structure

    def _extract_votes_from_response(self, data: Dict) -> List[Dict]:
        """Extract vote records from various response formats"""
        votes = []

        # Try different possible vote container keys
        possible_keys = [
            "votes",
            "rollCalls",
            "houseVotes",
            "senateVotes",
            "rollCallVotes",
            "houseRollCallVotes",
            "senateRollCallVotes",
        ]

        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                votes.extend(data[key])

        # Also check if data itself is a list of votes
        if isinstance(data, list):
            votes.extend(data)

        return votes

    def fetch_votes_from_bills(
        self, congress: int = 118, max_bills: int = 100
    ) -> List[Dict]:
        """
        Fetch vote data by examining bill actions for roll call votes

        Args:
            congress: Congress number
            max_bills: Maximum number of bills to examine

        Returns:
            List of vote records found in bill actions
        """
        self.logger.info(f"Fetching votes from bill actions for Congress {congress}")

        votes_found = []
        bills_processed = 0
        offset = 0

        while bills_processed < max_bills:
            # Get recent bills
            bills_data = self._make_request(
                f"/bill/{congress}",
                {"limit": 20, "offset": offset, "sort": "updateDate+desc"},
            )

            if not bills_data or "bills" not in bills_data:
                break

            bills = bills_data["bills"]
            if not bills:
                break

            for bill in bills:
                if bills_processed >= max_bills:
                    break

                bill_votes = self._extract_votes_from_bill(bill, congress)
                votes_found.extend(bill_votes)
                bills_processed += 1

                if self.verbose and bill_votes:
                    self.logger.debug(
                        f"Found {len(bill_votes)} votes in {bill.get('number', 'Unknown')}"
                    )

            offset += 20

            # Check pagination
            pagination = bills_data.get("pagination", {})
            if not pagination.get("next"):
                break

        self.logger.info(f"Found {len(votes_found)} votes from {bills_processed} bills")
        return votes_found

    def _extract_votes_from_bill(self, bill: Dict, congress: int) -> List[Dict]:
        """Extract vote information from a bill's actions"""
        votes = []

        bill_number = bill.get("number")
        bill_type = bill.get("type", "").lower()

        if not bill_number or not bill_type:
            return votes

        # Get detailed bill actions
        actions_data = self._make_request(
            f"/bill/{congress}/{bill_type}/{bill_number}/actions"
        )

        if not actions_data or "actions" not in actions_data:
            return votes

        for action in actions_data["actions"]:
            # Look for roll call vote indicators in action text
            text = action.get("text", "").lower()
            action_date = action.get("actionDate")

            if any(
                keyword in text
                for keyword in ["roll call", "roll no", "passed house", "passed senate"]
            ):
                # Try to extract roll call number
                roll_number = self._extract_roll_number(text)

                if roll_number:
                    # Fetch detailed vote record
                    vote_details = self._fetch_individual_vote(
                        congress, roll_number, action_date
                    )
                    if vote_details:
                        vote_details["bill"] = {
                            "congress": congress,
                            "type": bill_type,
                            "number": bill_number,
                            "title": bill.get("title", ""),
                            "url": bill.get("url", ""),
                        }
                        votes.append(vote_details)

        return votes

    def _extract_roll_number(self, text: str) -> Optional[int]:
        """Extract roll call number from action text"""
        import re

        # Common patterns for roll call numbers
        patterns = [
            r"roll call no\.?\s*(\d+)",
            r"roll no\.?\s*(\d+)",
            r"roll\s+(\d+)",
            r"record vote no\.?\s*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))

        return None

    def _fetch_individual_vote(
        self, congress: int, roll_number: int, date: str = None
    ) -> Optional[Dict]:
        """
        Fetch individual vote details using various endpoint patterns

        Args:
            congress: Congress number
            roll_number: Roll call number
            date: Vote date to help determine session

        Returns:
            Vote details or None if not found
        """
        # Try to determine session from date
        session = 1
        if date:
            try:
                vote_date = datetime.strptime(date, "%Y-%m-%d")
                # Simple heuristic: session 2 typically starts in odd years after January
                if vote_date.year % 2 == 1 and vote_date.month > 1:
                    session = 2
            except ValueError:
                pass

        # Try different endpoint patterns
        vote_endpoints = [
            f"/vote/{congress}/{session}/{roll_number}",
            f"/house-vote/{congress}/{session}/{roll_number}",
            f"/senate-vote/{congress}/{session}/{roll_number}",
        ]

        for endpoint in vote_endpoints:
            vote_data = self._make_request(endpoint)
            if vote_data:
                # Check for different response formats
                if "vote" in vote_data:
                    return self._parse_vote_record(vote_data["vote"])
                elif "houseRollCallVote" in vote_data:
                    return self._parse_vote_record(vote_data["houseRollCallVote"])
                elif "senateRollCallVote" in vote_data:
                    return self._parse_vote_record(vote_data["senateRollCallVote"])

        return None

    def _fetch_detailed_vote_from_summary(
        self, vote_summary: Dict, congress: int
    ) -> Optional[Dict]:
        """
        Fetch detailed vote data from a vote summary record

        Args:
            vote_summary: Vote summary from house-vote endpoint
            congress: Congress number

        Returns:
            Detailed vote record or None if not found
        """
        # Extract vote details from summary
        roll_call_number = vote_summary.get("rollCallNumber")
        session_number = vote_summary.get("sessionNumber")

        if not roll_call_number or not session_number:
            return None

        # Get basic vote info
        endpoint = f"/house-vote/{congress}/{session_number}/{roll_call_number}"
        vote_data = self._make_request(endpoint)

        if not vote_data or "houseRollCallVote" not in vote_data:
            return None

        vote_info = vote_data["houseRollCallVote"]

        # Get member votes from the /members sub-endpoint
        members_endpoint = (
            f"/house-vote/{congress}/{session_number}/{roll_call_number}/members"
        )
        members_data = self._make_request(members_endpoint)

        if not members_data or "houseRollCallVoteMemberVotes" not in members_data:
            return None

        members_vote_info = members_data["houseRollCallVoteMemberVotes"]

        # Parse the combined data
        detailed_vote = self._parse_house_vote_record(vote_info, members_vote_info)

        # Add bill information from summary if available
        if "legislationNumber" in vote_summary:
            detailed_vote["bill"] = {
                "congress": congress,
                "type": vote_summary.get("legislationType", "").lower(),
                "number": vote_summary.get("legislationNumber", ""),
                "url": vote_summary.get("legislationUrl", ""),
            }

        return detailed_vote

    def _parse_house_vote_record(
        self, vote_info: Dict, members_vote_info: Dict
    ) -> Dict:
        """Parse a House vote record with member vote data"""
        parsed_vote = {
            "vote_id": vote_info.get("rollCallNumber"),
            "congress": vote_info.get("congress"),
            "session": vote_info.get("sessionNumber"),
            "chamber": "house",
            "date": (
                vote_info.get("startDate", "").split("T")[0]
                if vote_info.get("startDate")
                else None
            ),
            "question": vote_info.get("voteQuestion", ""),
            "description": "",
            "result": vote_info.get("result", ""),
            "member_votes": [],
            "vote_totals": {},
            "party_breakdown": {},
        }

        # Process member votes from the members endpoint
        member_votes = members_vote_info.get("results", [])
        vote_counts = {"Yea": 0, "Nay": 0, "Present": 0, "Not Voting": 0}

        for member in member_votes:
            vote_cast = member.get("voteCast", "").strip()

            # Normalize vote names
            if vote_cast in ["Aye", "Yes"]:
                vote_cast = "Yea"
            elif vote_cast in ["No"]:
                vote_cast = "Nay"
            elif vote_cast in ["Not Voting", "No Vote"]:
                vote_cast = "Not Voting"

            member_vote = {
                "member_id": member.get("bioguideID"),
                "name": f"{member.get('firstName', '')} {member.get('lastName', '')}".strip(),
                "party": member.get("voteParty"),
                "state": member.get("voteState"),
                "vote": vote_cast,
            }
            parsed_vote["member_votes"].append(member_vote)

            # Count votes
            if vote_cast in vote_counts:
                vote_counts[vote_cast] += 1

        parsed_vote["vote_totals"] = vote_counts

        # Calculate party breakdown
        parsed_vote["party_breakdown"] = self._calculate_party_breakdown(
            parsed_vote["member_votes"]
        )

        return parsed_vote

    def _parse_vote_record(self, vote_data: Dict) -> Dict:
        """Parse a vote record into standardized format"""
        parsed_vote = {
            "vote_id": vote_data.get("rollCall") or vote_data.get("number"),
            "congress": vote_data.get("congress"),
            "session": vote_data.get("session"),
            "chamber": vote_data.get("chamber", "").lower(),
            "date": vote_data.get("date"),
            "question": vote_data.get("question", ""),
            "description": vote_data.get("description", ""),
            "result": vote_data.get("result", ""),
            "member_votes": [],
            "vote_totals": {},
            "party_breakdown": {},
        }

        # Extract member votes
        members = vote_data.get("members", {})
        for vote_position in ["yea", "nay", "present", "notVoting"]:
            if vote_position in members:
                member_list = members[vote_position]
                parsed_vote["vote_totals"][vote_position] = len(member_list)

                for member in member_list:
                    member_vote = {
                        "member_id": member.get("bioguideId"),
                        "name": member.get("name"),
                        "party": member.get("party"),
                        "state": member.get("state"),
                        "vote": vote_position.title(),
                    }
                    parsed_vote["member_votes"].append(member_vote)

        # Calculate party breakdown
        parsed_vote["party_breakdown"] = self._calculate_party_breakdown(
            parsed_vote["member_votes"]
        )

        return parsed_vote

    def _calculate_party_breakdown(self, member_votes: List[Dict]) -> Dict:
        """Calculate how each party voted"""
        party_votes = defaultdict(lambda: defaultdict(int))

        for vote in member_votes:
            party = vote.get("party", "Unknown")
            position = vote.get("vote", "Unknown")
            party_votes[party][position] += 1

        return dict(party_votes)

    def fetch_member_data(self, congress: int = 118) -> Dict[str, Dict]:
        """
        Fetch member data including party affiliations

        Args:
            congress: Congress number

        Returns:
            Dictionary of member data keyed by bioguide ID
        """
        if self.members_cache:
            return self.members_cache

        self.logger.info(f"Fetching member data for Congress {congress}")

        members = {}

        # Try different member endpoint patterns
        member_endpoints = [
            f"/member/congress/{congress}/house",
            f"/member/{congress}/house",
            f"/members/congress/{congress}/house",
            f"/members/{congress}/house",
        ]

        for endpoint in member_endpoints:
            house_data = self._make_request(endpoint)
            if house_data and "members" in house_data:
                self.logger.info(f"Found working House members endpoint: {endpoint}")
                for member in house_data["members"]:
                    bio_id = member.get("bioguideId")
                    if bio_id:
                        members[bio_id] = {
                            "name": member.get("name", ""),
                            "party": member.get("partyName", ""),
                            "state": member.get("state", ""),
                            "district": member.get("district"),
                            "chamber": "house",
                        }
                break

        # Try different Senate endpoint patterns
        senate_endpoints = [
            f"/member/congress/{congress}/senate",
            f"/member/{congress}/senate",
            f"/members/congress/{congress}/senate",
            f"/members/{congress}/senate",
        ]

        for endpoint in senate_endpoints:
            senate_data = self._make_request(endpoint)
            if senate_data and "members" in senate_data:
                self.logger.info(f"Found working Senate members endpoint: {endpoint}")
                for member in senate_data["members"]:
                    bio_id = member.get("bioguideId")
                    if bio_id:
                        members[bio_id] = {
                            "name": member.get("name", ""),
                            "party": member.get("partyName", ""),
                            "state": member.get("state", ""),
                            "chamber": "senate",
                        }
                break

        self.members_cache = members
        self.logger.info(f"Cached {len(members)} members")
        return members

    def analyze_voting_patterns(
        self, votes: List[Dict], members: Dict[str, Dict]
    ) -> Dict:
        """
        Analyze voting patterns to identify party line voting and swing voters

        Args:
            votes: List of vote records
            members: Member data dictionary

        Returns:
            Analysis results including swing voters and party statistics
        """
        self.logger.info("Analyzing voting patterns...")

        # Member voting statistics
        member_stats = defaultdict(
            lambda: {
                "total_votes": 0,
                "party_line_votes": 0,
                "defection_votes": 0,
                "votes_cast": [],
                "name": "",
                "party": "",
                "state": "",
            }
        )

        # Party statistics
        party_stats = defaultdict(
            lambda: {"total_votes": 0, "unity_scores": [], "members": set()}
        )

        for vote in votes:
            vote_id = vote.get("vote_id")
            party_breakdown = vote.get("party_breakdown", {})

            # Determine party majority positions
            party_positions = self._determine_party_positions(party_breakdown)

            for member_vote in vote.get("member_votes", []):
                member_id = member_vote.get("member_id")
                if not member_id:
                    continue

                member_data = members.get(member_id, {})
                # Use party from vote data if member database doesn't have it
                party = member_data.get("party") or member_vote.get("party", "Unknown")
                vote_position = member_vote.get("vote")

                # Update member stats
                stats = member_stats[member_id]
                stats["name"] = member_data.get("name") or member_vote.get("name", "")
                stats["party"] = party
                stats["state"] = member_data.get("state") or member_vote.get(
                    "state", ""
                )
                stats["total_votes"] += 1

                stats["votes_cast"].append(
                    {
                        "vote_id": vote_id,
                        "position": vote_position,
                        "date": vote.get("date"),
                        "question": vote.get("question", ""),
                    }
                )

                # Check if voted with party majority
                party_majority_position = party_positions.get(party)
                if party_majority_position and vote_position == party_majority_position:
                    stats["party_line_votes"] += 1
                elif party_majority_position and vote_position in ["Yea", "Nay"]:
                    stats["defection_votes"] += 1

                # Update party stats
                party_stats[party]["members"].add(member_id)

        # Calculate party unity scores for each vote
        for vote in votes:
            party_breakdown = vote.get("party_breakdown", {})
            for party, vote_counts in party_breakdown.items():
                total_party_votes = sum(vote_counts.values())
                if total_party_votes > 0:
                    # Unity score = percentage voting for majority position
                    majority_count = max(vote_counts.values()) if vote_counts else 0
                    unity_score = majority_count / total_party_votes
                    party_stats[party]["unity_scores"].append(unity_score)
                    party_stats[party]["total_votes"] += 1

        # Calculate final statistics
        analysis_results = {
            "summary": {
                "total_votes_analyzed": len(votes),
                "total_members": len(member_stats),
                "date_range": self._get_date_range(votes),
            },
            "members": {},
            "swing_voters": [],
            "party_statistics": {},
            "most_divisive_votes": [],
        }

        # Process member statistics
        for member_id, stats in member_stats.items():
            if stats["total_votes"] > 0:
                party_line_percentage = (
                    stats["party_line_votes"] / stats["total_votes"]
                ) * 100
                defection_percentage = (
                    stats["defection_votes"] / stats["total_votes"]
                ) * 100

                member_analysis = {
                    "name": stats["name"],
                    "party": stats["party"],
                    "state": stats["state"],
                    "total_votes": stats["total_votes"],
                    "party_line_votes": stats["party_line_votes"],
                    "defection_votes": stats["defection_votes"],
                    "party_line_percentage": round(party_line_percentage, 2),
                    "defection_percentage": round(defection_percentage, 2),
                    "swing_score": round(100 - party_line_percentage, 2),
                }

                analysis_results["members"][member_id] = member_analysis

                # Identify swing voters (less than 80% party line voting)
                if party_line_percentage < 80 and stats["total_votes"] >= 10:
                    analysis_results["swing_voters"].append(
                        {
                            "member_id": member_id,
                            "name": stats["name"],
                            "party": stats["party"],
                            "state": stats["state"],
                            "swing_score": member_analysis["swing_score"],
                            "total_votes": stats["total_votes"],
                        }
                    )

        # Sort swing voters by swing score
        analysis_results["swing_voters"].sort(
            key=lambda x: x["swing_score"], reverse=True
        )

        # Process party statistics
        for party, stats in party_stats.items():
            if stats["unity_scores"]:
                analysis_results["party_statistics"][party] = {
                    "average_unity_score": round(
                        sum(stats["unity_scores"]) / len(stats["unity_scores"]), 3
                    ),
                    "total_votes": stats["total_votes"],
                    "member_count": len(stats["members"]),
                    "unity_range": {
                        "min": round(min(stats["unity_scores"]), 3),
                        "max": round(max(stats["unity_scores"]), 3),
                    },
                }

        # Identify most divisive votes (lowest overall unity)
        vote_divisiveness = []
        for vote in votes:
            party_breakdown = vote.get("party_breakdown", {})
            overall_unity = self._calculate_overall_unity(party_breakdown)
            if overall_unity is not None:
                vote_divisiveness.append(
                    {
                        "vote_id": vote.get("vote_id"),
                        "date": vote.get("date"),
                        "question": vote.get("question", ""),
                        "unity_score": overall_unity,
                        "result": vote.get("result", ""),
                    }
                )

        vote_divisiveness.sort(key=lambda x: x["unity_score"])
        analysis_results["most_divisive_votes"] = vote_divisiveness[:10]

        return analysis_results

    def _determine_party_positions(self, party_breakdown: Dict) -> Dict[str, str]:
        """Determine each party's majority position on a vote"""
        party_positions = {}

        for party, vote_counts in party_breakdown.items():
            if not vote_counts:
                continue

            # Find the position with the most votes for this party
            max_position = max(vote_counts.items(), key=lambda x: x[1])
            if max_position[1] > 0:  # Ensure there are actual votes
                party_positions[party] = max_position[0]

        return party_positions

    def _get_date_range(self, votes: List[Dict]) -> Dict[str, str]:
        """Get the date range of votes analyzed"""
        dates = [vote.get("date") for vote in votes if vote.get("date")]
        dates = [d for d in dates if d]  # Remove None values

        if not dates:
            return {"start": "Unknown", "end": "Unknown"}

        dates.sort()
        return {"start": dates[0], "end": dates[-1]}

    def _calculate_overall_unity(self, party_breakdown: Dict) -> Optional[float]:
        """Calculate overall unity score across all parties for a vote"""
        total_members = 0
        total_majority_votes = 0

        for party, vote_counts in party_breakdown.items():
            if not vote_counts:
                continue

            party_total = sum(vote_counts.values())
            party_majority = max(vote_counts.values()) if vote_counts else 0

            total_members += party_total
            total_majority_votes += party_majority

        if total_members == 0:
            return None

        return total_majority_votes / total_members

    def save_vote_records(self, votes: List[Dict], base_dir: str = "data") -> None:
        """Save individual vote records to files"""
        votes_dir = Path(base_dir) / "votes"
        votes_dir.mkdir(parents=True, exist_ok=True)

        # Create index of all votes
        vote_index = []

        for vote in votes:
            congress = vote.get("congress", 118)
            chamber = vote.get("chamber", "unknown")
            vote_id = vote.get("vote_id", "unknown")

            # Create directory structure
            chamber_dir = votes_dir / str(congress) / chamber
            chamber_dir.mkdir(parents=True, exist_ok=True)

            # Save individual vote file
            filename = f"roll_{vote_id}.json"
            filepath = chamber_dir / filename

            with open(filepath, "w") as f:
                json.dump(vote, f, indent=2)

            # Add to index
            vote_index.append(
                {
                    "vote_id": vote_id,
                    "congress": congress,
                    "chamber": chamber,
                    "date": vote.get("date"),
                    "question": vote.get("question", ""),
                    "result": vote.get("result", ""),
                    "file_path": str(filepath.relative_to(votes_dir)),
                }
            )

        # Save index
        index_path = votes_dir / "index.json"
        with open(index_path, "w") as f:
            json.dump(
                {
                    "last_updated": datetime.now().isoformat(),
                    "total_votes": len(vote_index),
                    "votes": vote_index,
                },
                f,
                indent=2,
            )

        self.logger.info(f"Saved {len(votes)} vote records to {votes_dir}")

    def save_analysis(self, analysis: Dict, base_dir: str = "data") -> None:
        """Save voting analysis results"""
        analysis_dir = Path(base_dir) / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        filepath = analysis_dir / "voting_records_analysis.json"

        # Add metadata
        analysis["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "script_version": "1.0",
            "api_source": "congress.gov",
        }

        with open(filepath, "w") as f:
            json.dump(analysis, f, indent=2)

        self.logger.info(f"Saved voting analysis to {filepath}")

    def run_comprehensive_analysis(
        self,
        congress: int = 118,
        chamber: str = "house",
        max_votes: int = 100,
        base_dir: str = "data",
    ) -> Dict:
        """
        Run comprehensive voting records analysis

        Args:
            congress: Congress number
            chamber: Chamber to analyze (house/senate/both)
            max_votes: Maximum votes to analyze
            base_dir: Base directory for data storage

        Returns:
            Complete analysis results
        """
        self.logger.info(
            f"Starting comprehensive voting analysis for {chamber} in Congress {congress}"
        )

        # Debug API endpoints first
        debug_info = self.debug_house_votes_api(congress)
        self.logger.info(f"API Debug Results: {debug_info['recommendations']}")

        # Fetch member data
        members = self.fetch_member_data(congress)

        # Fetch vote data using multiple approaches
        all_votes = []

        # Try direct vote endpoints first
        working_endpoints = [
            ep
            for ep, resp in debug_info["responses"].items()
            if resp.get("success") and resp.get("votes_found", 0) > 0
        ]

        if working_endpoints:
            self.logger.info("Using direct vote endpoints")
            for endpoint in working_endpoints[:1]:  # Use first working endpoint
                vote_data = self._make_request(endpoint, {"limit": max_votes})
                if vote_data:
                    votes = self._extract_votes_from_response(vote_data)
                    for vote_summary in votes[:max_votes]:
                        # Get detailed vote record using the individual vote URL
                        detailed_vote = self._fetch_detailed_vote_from_summary(
                            vote_summary, congress
                        )
                        if detailed_vote and detailed_vote.get("member_votes"):
                            all_votes.append(detailed_vote)

        # Fallback: extract votes from bill actions
        if len(all_votes) < 10:  # If we don't have enough votes, try bill actions
            self.logger.info("Fetching votes from bill actions (fallback method)")
            bill_votes = self.fetch_votes_from_bills(congress, max_votes)
            all_votes.extend(bill_votes)

        # Remove duplicates
        seen_votes = set()
        unique_votes = []
        for vote in all_votes:
            vote_key = (vote.get("congress"), vote.get("vote_id"), vote.get("chamber"))
            if vote_key not in seen_votes:
                seen_votes.add(vote_key)
                unique_votes.append(vote)

        self.logger.info(f"Collected {len(unique_votes)} unique votes for analysis")

        if not unique_votes:
            self.logger.warning("No votes found for analysis")
            return {"error": "No voting data found", "debug_info": debug_info}

        # Perform analysis
        analysis = self.analyze_voting_patterns(unique_votes, members)

        # Save results
        self.save_vote_records(unique_votes, base_dir)
        self.save_analysis(analysis, base_dir)

        # Add summary info
        analysis["collection_summary"] = {
            "votes_collected": len(unique_votes),
            "members_analyzed": len(analysis.get("members", {})),
            "swing_voters_identified": len(analysis.get("swing_voters", [])),
            "api_debug_info": debug_info,
        }

        return analysis


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Fetch and analyze congressional voting records"
    )
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
    parser.add_argument(
        "--chamber",
        choices=["house", "senate", "both"],
        default="house",
        help="Chamber to analyze (default: house)",
    )
    parser.add_argument(
        "--max-votes",
        type=int,
        default=100,
        help="Maximum votes to analyze (default: 100)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--debug-only",
        action="store_true",
        help="Only run API debugging, don't fetch full data",
    )
    parser.add_argument(
        "--output-dir", default="data", help="Output directory (default: data)"
    )

    args = parser.parse_args()

    try:
        fetcher = VotingRecordsFetcher(verbose=args.verbose)

        if args.debug_only:
            # Just run debugging
            debug_info = fetcher.debug_house_votes_api(args.congress)
            print(json.dumps(debug_info, indent=2))
            return

        # Run full analysis
        results = fetcher.run_comprehensive_analysis(
            congress=args.congress,
            chamber=args.chamber,
            max_votes=args.max_votes,
            base_dir=args.output_dir,
        )

        # Print summary
        print("\nVoting Records Analysis Complete!")
        print(f"Congress: {args.congress}")
        print(f"Chamber: {args.chamber}")
        print(
            f"Votes analyzed: {results.get('collection_summary', {}).get('votes_collected', 0)}"
        )
        print(
            f"Members analyzed: {results.get('collection_summary', {}).get('members_analyzed', 0)}"
        )
        print(
            f"Swing voters identified: {results.get('collection_summary', {}).get('swing_voters_identified', 0)}"
        )

        # Show top swing voters
        swing_voters = results.get("swing_voters", [])[:5]
        if swing_voters:
            print("\nTop Swing Voters:")
            for voter in swing_voters:
                print(
                    f"  {voter['name']} ({voter['party']}-{voter['state']}): {voter['swing_score']}% swing score"
                )

        print(f"\nResults saved to {args.output_dir}/")

    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
