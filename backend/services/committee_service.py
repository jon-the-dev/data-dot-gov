"""
Committee Service Module

Handles data retrieval and processing for committee-related operations.
"""

import json
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import our new models and API client
from models.committee import (
    get_committee_code_variations,
    normalize_committee_code,
)
from utils.cache_utils import DEFAULT_TTL, LONG_TTL, cache_response
from utils.congress_api import CongressAPIClient, CongressAPIError

logger = logging.getLogger(__name__)

# Use environment variable or fallback to project data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
if not DATA_DIR.exists():
    # Fallback to project root data directory for development
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    logger.info(f"Using project data directory: {DATA_DIR}")

class CommitteeService:
    """Service class for committee data operations"""

    def __init__(self):
        self.committees_dir = DATA_DIR / "committees"
        self.congress_api = CongressAPIClient()

    async def get_all_committees(self, congress: int = 118, chamber: Optional[str] = None) -> Dict[str, Any]:
        """Get all committees with optional chamber filtering"""
        committees_dir = self.committees_dir / str(congress)
        if not committees_dir.exists():
            return {
                "committees": [],
                "total": 0,
                "by_chamber": {"house": [], "senate": [], "joint": []},
                "error": f"No committee data for congress {congress}"
            }

        all_committees = []
        by_chamber = {"house": [], "senate": [], "joint": []}

        # Process each chamber directory
        for chamber_dir in committees_dir.iterdir():
            if chamber_dir.is_dir():
                chamber_name = chamber_dir.name.lower()

                # Filter by chamber if specified
                if chamber and chamber.lower() != chamber_name:
                    continue

                index_file = chamber_dir / "index.json"
                if index_file.exists():
                    try:
                        with open(index_file) as f:
                            chamber_data = json.load(f)
                            committees_list = chamber_data.get("committees", [])

                            # Add chamber info and process each committee
                            for committee in committees_list:
                                committee_info = {
                                    **committee,
                                    "chamber": chamber_name,
                                    "congress": congress
                                }
                                all_committees.append(committee_info)
                                by_chamber[chamber_name].append(committee_info)

                    except Exception as e:
                        logger.warning(f"Error reading {index_file}: {e}")

        return {
            "committees": all_committees,
            "total": len(all_committees),
            "by_chamber": by_chamber,
            "congress": congress,
            "chamber_filter": chamber
        }

    @cache_response(ttl=LONG_TTL, use_file=True)
    async def get_committee_details(self, committee_id: str, congress: int = 118, use_api: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific committee.

        Args:
            committee_id: Committee system code (supports various formats: 'ssju00', 'SSJU', etc.)
            congress: Congress number
            use_api: Whether to fetch fresh data from Congress.gov API (default: False for performance)

        Returns:
            Committee details dictionary or None if not found
        """
        # Try local files first for better performance
        local_data = await self._get_committee_details_from_files(committee_id, congress)

        # If local data exists and API not explicitly requested, return local data
        if local_data and not use_api:
            return local_data

        # Try to get from Congress.gov API if explicitly requested or local data not found
        if use_api or not local_data:
            try:
                async with self.congress_api:
                    committee = await self.congress_api.get_committee_details(committee_id, congress)
                    if committee:
                        # Convert Pydantic model to dict for backwards compatibility
                        committee_dict = committee.model_dump()
                        committee_dict["committee_id"] = committee_id
                        committee_dict["chamber_name"] = committee.chamber.value.lower()

                        # Add subcommittees
                        subcommittees = await self.congress_api.get_subcommittees(committee_id, congress)
                        committee_dict["subcommittees"] = [sub.model_dump() for sub in subcommittees]
                        committee_dict["subcommittee_count"] = len(subcommittees)

                        return committee_dict
            except CongressAPIError as e:
                logger.warning(f"API error fetching committee {committee_id}: {e}. Using local data if available.")
            except asyncio.TimeoutError as e:
                logger.warning(f"API timeout fetching committee {committee_id}: {e}. Using local data if available.")
            except Exception as e:
                logger.warning(f"Unexpected error fetching committee {committee_id} from API: {e}. Using local data if available.")

        # Return local data if available (either from initial check or as fallback)
        return local_data

    async def get_committee_subcommittees(self, committee_id: str, congress: int = 118) -> List[Dict[str, Any]]:
        """Get subcommittees for a specific committee"""
        committees_dir = self.committees_dir / str(congress)
        if not committees_dir.exists():
            return []

        subcommittees = []

        # Search all chamber directories for subcommittees
        for chamber_dir in committees_dir.iterdir():
            if chamber_dir.is_dir():
                subcommittees.extend(
                    await self._get_subcommittees_for_committee(committee_id, chamber_dir, congress)
                )

        return subcommittees

    async def _get_subcommittees_for_committee(self, committee_id: str, chamber_dir: Path, congress: int) -> List[Dict[str, Any]]:
        """Helper method to get subcommittees for a specific committee from a chamber directory"""
        subcommittees = []
        index_file = chamber_dir / "index.json"

        if index_file.exists():
            try:
                with open(index_file) as f:
                    index_data = json.load(f)
                    committees_list = index_data.get("committees", [])

                    # Find subcommittees of this committee
                    for committee in committees_list:
                        parent = committee.get("parent", {})
                        if parent.get("systemCode") == committee_id:
                            subcommittee_details = {
                                "code": committee.get("code"),
                                "name": committee.get("name"),
                                "type": committee.get("type"),
                                "parent_committee": committee_id,
                                "parent_name": parent.get("name"),
                                "chamber": chamber_dir.name.lower(),
                                "congress": congress
                            }

                            # Try to get more details from individual subcommittee file
                            subcommittee_file = chamber_dir / f"{committee.get('code')}.json"
                            if subcommittee_file.exists():
                                try:
                                    with open(subcommittee_file) as sf:
                                        sub_data = json.load(sf)
                                        subcommittee_details.update({
                                            "updateDate": sub_data.get("updateDate"),
                                            "url": sub_data.get("url"),
                                            "committeeTypeCode": sub_data.get("committeeTypeCode")
                                        })
                                except Exception as e:
                                    logger.warning(f"Error reading subcommittee file {subcommittee_file}: {e}")

                            subcommittees.append(subcommittee_details)

            except Exception as e:
                logger.warning(f"Error reading {index_file}: {e}")

        return subcommittees

    @cache_response(ttl=DEFAULT_TTL, use_file=True)
    async def get_committee_members(self, committee_id: str, congress: int = 118, use_api: bool = False) -> Dict[str, Any]:
        """
        Get members of a specific committee.

        Args:
            committee_id: Committee system code
            congress: Congress number
            use_api: Whether to fetch actual membership from Congress.gov API (default: False for performance)

        Returns:
            Dictionary with committee members and metadata
        """
        # Try to get actual members from Congress.gov API only if explicitly requested
        if use_api:
            try:
                async with self.congress_api:
                    members = await self.congress_api.get_committee_members(committee_id, congress)
                    if members:
                        # Convert Pydantic models to dicts for backwards compatibility
                        committee_members = []
                        for member in members:
                            member_dict = member.model_dump()
                            # Convert field names to match legacy format
                            member_dict["bioguideId"] = member_dict.pop("bioguide_id")
                            member_dict["imageUrl"] = member_dict.pop("image_url", None)
                            committee_members.append(member_dict)

                        committee_name = await self._get_committee_name(committee_id, congress)

                        return {
                            "committee_id": committee_id,
                            "members": committee_members,
                            "total": len(committee_members),
                            "congress": congress,
                            "committee_name": committee_name,
                            "note": "Actual committee membership from Congress.gov API"
                        }
            except (CongressAPIError, asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Error fetching members for {committee_id} from API: {e}. Falling back to bill analysis.")

        # Use bill sponsorship analysis by default or as fallback
        return await self._get_committee_members_from_bills(committee_id, congress)

    async def get_committee_bills(self, committee_id: str, congress: int = 118) -> Dict[str, Any]:
        """Get bills referred to or considered by a specific committee"""
        bills_dir = DATA_DIR / "congress_bills" / str(congress)
        if not bills_dir.exists():
            return {
                "committee_id": committee_id,
                "bills": [],
                "total": 0,
                "congress": congress,
                "message": f"No bills data found for congress {congress}"
            }

        committee_bills = []
        committee_name = await self._get_committee_name(committee_id, congress)

        # Search through bill files for committee references
        try:
            for bill_file in bills_dir.glob("*.json"):
                if bill_file.name in ["index.json", "summary.json"]:
                    continue

                try:
                    with open(bill_file) as f:
                        bill_data = json.load(f)

                    # Check for committee references in various places
                    committee_found = False

                    # Check committee reports
                    committee_reports = bill_data.get("committeeReports", [])
                    for report in committee_reports:
                        if committee_id.upper() in report.get("description", "").upper():
                            committee_found = True
                            break

                    # Check latest action text for committee references
                    if not committee_found:
                        latest_action = bill_data.get("latestAction", {})
                        action_text = latest_action.get("text", "").upper()

                        # Check for various committee name patterns
                        search_terms = [committee_id.upper()]
                        if committee_name:
                            search_terms.extend([
                                committee_name.upper(),
                                f"COMMITTEE ON THE {committee_name.upper()}",
                                f"THE {committee_name.upper()}",
                                committee_name.upper().replace(" COMMITTEE", "")
                            ])

                        for term in search_terms:
                            if term and term in action_text:
                                committee_found = True
                                break

                    # Check actions for committee references
                    if not committee_found:
                        actions = bill_data.get("actions", [])
                        for action in actions[:10]:  # Check first 10 actions
                            action_text = action.get("text", "").upper()

                            # Use same search terms as above
                            search_terms = [committee_id.upper()]
                            if committee_name:
                                search_terms.extend([
                                    committee_name.upper(),
                                    f"COMMITTEE ON THE {committee_name.upper()}",
                                    f"THE {committee_name.upper()}",
                                    committee_name.upper().replace(" COMMITTEE", "")
                                ])

                            for term in search_terms:
                                if term and term in action_text:
                                    committee_found = True
                                    break

                            if committee_found:
                                break

                    if committee_found:
                        bill_summary = {
                            "bill_id": f"{congress}_{bill_data.get('type', 'UNKNOWN')}_{bill_data.get('number', '0')}",
                            "title": bill_data.get("title", "Untitled"),
                            "type": bill_data.get("type"),
                            "number": bill_data.get("number"),
                            "introducedDate": bill_data.get("introducedDate"),
                            "latestAction": bill_data.get("latestAction"),
                            "sponsor": bill_data.get("sponsors", [{}])[0].get("fullName") if bill_data.get("sponsors") else None,
                            "policyArea": bill_data.get("policyArea", {}).get("name"),
                            "congress": congress
                        }
                        committee_bills.append(bill_summary)

                        # Limit to prevent huge responses
                        if len(committee_bills) >= 100:
                            break

                except Exception as e:
                    logger.warning(f"Error reading bill file {bill_file}: {e}")

        except Exception as e:
            logger.error(f"Error searching for committee bills: {e}")
            return {
                "committee_id": committee_id,
                "bills": [],
                "total": 0,
                "congress": congress,
                "message": f"Error searching for bills: {str(e)}"
            }

        # Sort by introduced date (newest first)
        committee_bills.sort(
            key=lambda x: x.get("introducedDate", ""),
            reverse=True
        )

        return {
            "committee_id": committee_id,
            "bills": committee_bills,
            "total": len(committee_bills),
            "congress": congress,
            "committee_name": committee_name
        }

    async def get_committee_votes(self, committee_id: str, congress: int = 118) -> Dict[str, Any]:
        """Get voting records for a specific committee"""
        # Committee-specific voting records are not currently available
        return {
            "committee_id": committee_id,
            "votes": [],
            "total": 0,
            "congress": congress,
            "message": "Committee voting records are not currently available. Data integration pending."
        }

    async def get_committee_analytics(self, committee_id: str, congress: int = 118) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific committee with actual data"""
        # Get basic committee info first
        committee_data = await self.get_committee_details(committee_id, congress)
        if not committee_data:
            return None

        try:
            # Count subcommittees
            subcommittees = await self.get_committee_subcommittees(committee_id, congress)
            subcommittee_count = len(subcommittees)

            # Get member count
            members_data = await self.get_committee_members(committee_id, congress)
            member_count = members_data.get("total", 0)

            # Get bills data for analytics
            bills_data = await self.get_committee_bills(committee_id, congress)
            bills_referred = bills_data.get("total", 0)

            # Calculate activity metrics from bills
            bills_reported = 0
            recent_activity = 0
            policy_areas = Counter()

            for bill in bills_data.get("bills", []):
                # Count bills with reports (considered "reported")
                latest_action = bill.get("latestAction", {})
                if latest_action and "report" in latest_action.get("text", "").lower():
                    bills_reported += 1

                # Count recent activity (last 6 months)
                introduced_date = bill.get("introducedDate", "")
                if introduced_date and introduced_date >= "2024-06":  # Recent threshold
                    recent_activity += 1

                # Track policy areas
                policy_area = bill.get("policyArea")
                if policy_area:
                    policy_areas[policy_area] += 1

            # Calculate activity score (0-100 based on bills and members)
            activity_score = min(100, (bills_referred * 2) + (member_count * 5) + recent_activity)

            # Build analytics response
            analytics = {
                "committee_id": committee_id,
                "name": committee_data.get("name", "Unknown"),
                "chamber": committee_data.get("chamber_name"),
                "committee_type": committee_data.get("committeeTypeCode", "Unknown"),
                "congress": congress,
                "subcommittee_count": subcommittee_count,
                "analytics": {
                    "member_count": member_count,
                    "bills_referred": bills_referred,
                    "bills_reported": bills_reported,
                    "recent_activity": recent_activity,
                    "activity_score": activity_score,
                    "top_policy_areas": [{"area": area, "count": count} for area, count in policy_areas.most_common(5)]
                },
                "last_updated": committee_data.get("updateDate"),
                "generated_at": "2024-09-24T00:00:00Z"
            }

            return analytics

        except Exception as e:
            logger.error(f"Error generating committee analytics: {e}")
            return {
                "committee_id": committee_id,
                "name": committee_data.get("name", "Unknown"),
                "chamber": committee_data.get("chamber_name"),
                "error": f"Error generating analytics: {str(e)}"
            }

    async def get_subcommittee_details(self, subcommittee_id: str, congress: int = 118) -> Optional[Dict[str, Any]]:
        """Get details for a specific subcommittee"""
        committees_dir = self.committees_dir / str(congress)
        if not committees_dir.exists():
            return None

        # Search all chamber directories for the subcommittee
        for chamber_dir in committees_dir.iterdir():
            if chamber_dir.is_dir():
                subcommittee_file = chamber_dir / f"{subcommittee_id}.json"
                if subcommittee_file.exists():
                    try:
                        with open(subcommittee_file) as f:
                            subcommittee_data = json.load(f)

                        # Enhance with additional metadata
                        subcommittee_data["chamber_name"] = chamber_dir.name.lower()
                        subcommittee_data["congress"] = congress
                        subcommittee_data["subcommittee_id"] = subcommittee_id

                        # Try to find parent committee info from the index
                        index_file = chamber_dir / "index.json"
                        parent_info = {}
                        if index_file.exists():
                            try:
                                with open(index_file) as f:
                                    index_data = json.load(f)
                                    committees_list = index_data.get("committees", [])

                                    for committee in committees_list:
                                        if committee.get("code") == subcommittee_id:
                                            parent_info = committee.get("parent", {})
                                            break
                            except Exception as e:
                                logger.warning(f"Error reading index for parent info: {e}")

                        subcommittee_data["parent_committee"] = parent_info

                        return subcommittee_data

                    except Exception as e:
                        logger.warning(f"Error reading {subcommittee_file}: {e}")

        return None

    async def committee_exists(self, committee_id: str, congress: int = 118, use_api: bool = False) -> bool:
        """Check if a committee exists using multiple code variations"""
        # Check local files first for better performance
        committees_dir = self.committees_dir / str(congress)
        if committees_dir.exists():
            # Try different code variations
            code_variations = get_committee_code_variations(committee_id)

            for code in code_variations:
                for chamber_dir in committees_dir.iterdir():
                    if chamber_dir.is_dir():
                        committee_file = chamber_dir / f"{code}.json"
                        if committee_file.exists():
                            return True

        # Try API only if explicitly requested and not found locally
        if use_api:
            try:
                async with self.congress_api:
                    committee = await self.congress_api.get_committee_details(committee_id, congress)
                    return committee is not None
            except (CongressAPIError, asyncio.TimeoutError, Exception):
                pass  # Fall through to return False

        return False

    async def _get_committee_details_from_files(self, committee_id: str, congress: int = 118) -> Optional[Dict[str, Any]]:
        """Get committee details from local JSON files (fallback method)."""
        committees_dir = self.committees_dir / str(congress)
        if not committees_dir.exists():
            return None

        # Try different code variations for file lookup
        code_variations = get_committee_code_variations(committee_id)

        for code in code_variations:
            # Search all chamber directories for the committee
            for chamber_dir in committees_dir.iterdir():
                if chamber_dir.is_dir():
                    committee_file = chamber_dir / f"{code}.json"
                    if committee_file.exists():
                        try:
                            with open(committee_file) as f:
                                committee_data = json.load(f)

                            # Enhance with additional metadata
                            committee_data["chamber_name"] = chamber_dir.name.lower()
                            committee_data["congress"] = congress
                            committee_data["committee_id"] = committee_id

                            # Try to find subcommittees from the index
                            subcommittees = await self._get_subcommittees_for_committee(
                                committee_id, chamber_dir, congress
                            )
                            committee_data["subcommittees"] = subcommittees
                            committee_data["subcommittee_count"] = len(subcommittees)

                            return committee_data

                        except Exception as e:
                            logger.warning(f"Error reading {committee_file}: {e}")

        return None

    async def _get_committee_members_from_bills(self, committee_id: str, congress: int = 118) -> Dict[str, Any]:
        """Get committee members by analyzing bill sponsorship (fallback method)."""
        members_dir = DATA_DIR / "members" / str(congress)
        if not members_dir.exists():
            return {
                "committee_id": committee_id,
                "members": [],
                "total": 0,
                "congress": congress,
                "message": f"No member data found for congress {congress}"
            }

        committee_members = []
        committee_name = await self._get_committee_name(committee_id, congress)

        # Search through member files and bills for committee associations
        try:
            # First, try to find members who sponsored bills related to this committee
            bills_dir = DATA_DIR / "congress_bills" / str(congress)
            member_committee_activity = defaultdict(int)

            if bills_dir.exists():
                # Use committee code variations for better matching
                code_variations = get_committee_code_variations(committee_id)
                normalized = normalize_committee_code(committee_id)
                search_codes = [code.upper() for code in code_variations]
                search_codes.append(normalized["short_code"])

                for bill_file in list(bills_dir.glob("*.json"))[:500]:  # Limit search for performance
                    try:
                        with open(bill_file) as f:
                            bill_data = json.load(f)

                        # Check if bill has committee association
                        committee_found = False
                        committee_reports = bill_data.get("committeeReports", [])
                        for report in committee_reports:
                            report_desc = report.get("description", "").upper()
                            if any(code in report_desc for code in search_codes):
                                committee_found = True
                                break

                        if not committee_found:
                            latest_action = bill_data.get("latestAction", {})
                            action_text = latest_action.get("text", "").upper()

                            # Check for various committee name patterns
                            search_terms = search_codes.copy()
                            if committee_name:
                                search_terms.extend([
                                    committee_name.upper(),
                                    f"COMMITTEE ON THE {committee_name.upper()}",
                                    f"THE {committee_name.upper()}",
                                    committee_name.upper().replace(" COMMITTEE", "")
                                ])

                            for term in search_terms:
                                if term and term in action_text:
                                    committee_found = True
                                    break

                        if committee_found:
                            # Track sponsors and cosponsors
                            sponsors = bill_data.get("sponsors", [])
                            for sponsor in sponsors:
                                bioguide_id = sponsor.get("bioguideId")
                                if bioguide_id:
                                    member_committee_activity[bioguide_id] += 1

                    except Exception as e:
                        logger.warning(f"Error reading bill file for member search {bill_file}: {e}")

            # Now get member details for those with committee activity
            for member_file in members_dir.glob(f"{congress}_*.json"):
                try:
                    with open(member_file) as f:
                        member_data = json.load(f)

                    bioguide_id = member_data.get("bioguideId")
                    if bioguide_id and bioguide_id in member_committee_activity:
                        member_info = {
                            "bioguideId": bioguide_id,
                            "name": member_data.get("name", "Unknown"),
                            "state": member_data.get("state"),
                            "district": member_data.get("district"),
                            "party": member_data.get("party"),
                            "chamber": member_data.get("chamber"),
                            "imageUrl": member_data.get("depiction", {}).get("imageUrl"),
                            "committee_activity": member_committee_activity[bioguide_id],
                            "role": "Member"  # Default role since we don't have leadership data
                        }
                        committee_members.append(member_info)

                        # Limit results to prevent huge responses
                        if len(committee_members) >= 50:
                            break

                except Exception as e:
                    logger.warning(f"Error reading member file {member_file}: {e}")

            # Sort by committee activity (most active first)
            committee_members.sort(key=lambda x: x.get("committee_activity", 0), reverse=True)

        except Exception as e:
            logger.error(f"Error searching for committee members: {e}")
            return {
                "committee_id": committee_id,
                "members": [],
                "total": 0,
                "congress": congress,
                "message": f"Error searching for members: {str(e)}"
            }

        return {
            "committee_id": committee_id,
            "members": committee_members,
            "total": len(committee_members),
            "congress": congress,
            "committee_name": committee_name,
            "note": "Members identified through bill sponsorship activity. Leadership roles not available in current data."
        }

    async def _get_committee_name(self, committee_id: str, congress: int = 118) -> Optional[str]:
        """Get committee name from committee data"""
        committee_data = await self.get_committee_details(committee_id, congress, use_api=False)
        if committee_data:
            return committee_data.get("name")
        return None

    @cache_response(ttl=DEFAULT_TTL, use_file=True)
    async def get_committee_hearings(
        self,
        committee_id: str,
        congress: int = 118,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get committee hearings with caching.

        Args:
            committee_id: Committee system code
            congress: Congress number
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with hearings data and metadata
        """
        try:
            async with self.congress_api:
                hearings = await self.congress_api.get_committee_hearings(
                    committee_id, congress, limit, offset
                )

                # Convert Pydantic models to dicts for response
                hearings_dict = []
                for hearing in hearings:
                    hearing_dict = hearing.model_dump()
                    # Convert datetime objects to ISO strings for JSON serialization
                    if hearing_dict.get("date"):
                        hearing_dict["date"] = hearing_dict["date"].isoformat()
                    if hearing_dict.get("created_date"):
                        hearing_dict["created_date"] = hearing_dict["created_date"].isoformat()
                    if hearing_dict.get("updated_date"):
                        hearing_dict["updated_date"] = hearing_dict["updated_date"].isoformat()

                    # Convert witnesses to dicts
                    hearing_dict["witnesses"] = [w.model_dump() for w in hearing.witnesses]

                    hearings_dict.append(hearing_dict)

                # Get committee name for context
                committee_name = await self._get_committee_name(committee_id, congress)

                return {
                    "committee_id": committee_id,
                    "committee_name": committee_name,
                    "hearings": hearings_dict,
                    "total": len(hearings_dict),
                    "limit": limit,
                    "offset": offset,
                    "congress": congress,
                    "data_source": "Congress.gov API"
                }

        except CongressAPIError as e:
            logger.error(f"Error fetching committee hearings: {e}")
            return {
                "committee_id": committee_id,
                "hearings": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "congress": congress,
                "error": f"Error fetching hearings: {str(e)}"
            }

    @cache_response(ttl=DEFAULT_TTL, use_file=True)
    async def get_committee_meetings(
        self,
        committee_id: str,
        congress: int = 118,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get committee meetings/markups with caching.

        Args:
            committee_id: Committee system code
            congress: Congress number
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with meetings data and metadata
        """
        try:
            async with self.congress_api:
                meetings = await self.congress_api.get_committee_meetings(
                    committee_id, congress, limit, offset
                )

                # Convert Pydantic models to dicts for response
                meetings_dict = []
                for meeting in meetings:
                    meeting_dict = meeting.model_dump()
                    # Convert datetime objects to ISO strings for JSON serialization
                    if meeting_dict.get("date"):
                        meeting_dict["date"] = meeting_dict["date"].isoformat()
                    if meeting_dict.get("created_date"):
                        meeting_dict["created_date"] = meeting_dict["created_date"].isoformat()
                    if meeting_dict.get("updated_date"):
                        meeting_dict["updated_date"] = meeting_dict["updated_date"].isoformat()

                    meetings_dict.append(meeting_dict)

                # Get committee name for context
                committee_name = await self._get_committee_name(committee_id, congress)

                return {
                    "committee_id": committee_id,
                    "committee_name": committee_name,
                    "meetings": meetings_dict,
                    "total": len(meetings_dict),
                    "limit": limit,
                    "offset": offset,
                    "congress": congress,
                    "data_source": "Congress.gov API"
                }

        except CongressAPIError as e:
            logger.error(f"Error fetching committee meetings: {e}")
            return {
                "committee_id": committee_id,
                "meetings": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "congress": congress,
                "error": f"Error fetching meetings: {str(e)}"
            }

    @cache_response(ttl=LONG_TTL, use_file=True)
    async def get_committee_documents(
        self,
        committee_id: str,
        congress: int = 118,
        document_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get committee documents/reports with caching.

        Args:
            committee_id: Committee system code
            congress: Congress number
            document_type: Filter by document type (report, print, document)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with documents data and metadata
        """
        try:
            async with self.congress_api:
                documents = await self.congress_api.get_committee_documents(
                    committee_id, congress, document_type, limit, offset
                )

                # Convert Pydantic models to dicts for response
                documents_dict = []
                for document in documents:
                    doc_dict = document.model_dump()
                    # Convert datetime objects to ISO strings for JSON serialization
                    if doc_dict.get("publication_date"):
                        doc_dict["publication_date"] = doc_dict["publication_date"].isoformat()
                    if doc_dict.get("created_date"):
                        doc_dict["created_date"] = doc_dict["created_date"].isoformat()
                    if doc_dict.get("updated_date"):
                        doc_dict["updated_date"] = doc_dict["updated_date"].isoformat()

                    documents_dict.append(doc_dict)

                # Get committee name for context
                committee_name = await self._get_committee_name(committee_id, congress)

                # Sort documents by publication date (newest first)
                documents_dict.sort(
                    key=lambda x: x.get("publication_date", ""),
                    reverse=True
                )

                return {
                    "committee_id": committee_id,
                    "committee_name": committee_name,
                    "documents": documents_dict,
                    "total": len(documents_dict),
                    "limit": limit,
                    "offset": offset,
                    "congress": congress,
                    "document_type_filter": document_type,
                    "data_source": "Congress.gov API"
                }

        except CongressAPIError as e:
            logger.error(f"Error fetching committee documents: {e}")
            return {
                "committee_id": committee_id,
                "documents": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "congress": congress,
                "document_type_filter": document_type,
                "error": f"Error fetching documents: {str(e)}"
            }

    async def get_committee_activity_summary(self, committee_id: str, congress: int = 118) -> Dict[str, Any]:
        """
        Get a comprehensive activity summary for a committee.

        Args:
            committee_id: Committee system code
            congress: Congress number

        Returns:
            Activity summary with hearings, meetings, and documents counts
        """
        try:
            # Get all activity types in parallel
            hearings_data = await self.get_committee_hearings(committee_id, congress, limit=1000)
            meetings_data = await self.get_committee_meetings(committee_id, congress, limit=1000)
            documents_data = await self.get_committee_documents(committee_id, congress, limit=1000)

            # Calculate activity metrics
            recent_hearings = 0
            recent_meetings = 0
            recent_documents = 0

            # Count recent activity (last 6 months)
            cutoff_date = datetime.now() - timedelta(days=180)

            for hearing in hearings_data.get("hearings", []):
                hearing_date = hearing.get("date")
                if hearing_date:
                    try:
                        parsed_date = datetime.fromisoformat(hearing_date.replace("Z", "+00:00"))
                        if parsed_date >= cutoff_date:
                            recent_hearings += 1
                    except ValueError:
                        pass

            for meeting in meetings_data.get("meetings", []):
                meeting_date = meeting.get("date")
                if meeting_date:
                    try:
                        parsed_date = datetime.fromisoformat(meeting_date.replace("Z", "+00:00"))
                        if parsed_date >= cutoff_date:
                            recent_meetings += 1
                    except ValueError:
                        pass

            for document in documents_data.get("documents", []):
                pub_date = document.get("publication_date")
                if pub_date:
                    try:
                        parsed_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        if parsed_date >= cutoff_date:
                            recent_documents += 1
                    except ValueError:
                        pass

            committee_name = await self._get_committee_name(committee_id, congress)

            return {
                "committee_id": committee_id,
                "committee_name": committee_name,
                "congress": congress,
                "activity_summary": {
                    "total_hearings": hearings_data.get("total", 0),
                    "total_meetings": meetings_data.get("total", 0),
                    "total_documents": documents_data.get("total", 0),
                    "recent_hearings": recent_hearings,
                    "recent_meetings": recent_meetings,
                    "recent_documents": recent_documents,
                    "total_recent_activity": recent_hearings + recent_meetings + recent_documents
                },
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating activity summary for {committee_id}: {e}")
            return {
                "committee_id": committee_id,
                "congress": congress,
                "error": f"Error generating activity summary: {str(e)}"
            }

# Mock data generator for when real data is not available
class MockCommitteeDataGenerator:
    """Generates mock committee data for development/testing purposes"""

    @staticmethod
    def generate_mock_committees(congress: int = 118) -> Dict[str, Any]:
        """Generate mock committee data"""
        mock_committees = [
            {
                "code": "HSAG",
                "name": "Committee on Agriculture",
                "chamber": "house",
                "congress": congress,
                "type": "Standing",
                "jurisdiction": "Agriculture, nutrition, and forestry"
            },
            {
                "code": "SSAG",
                "name": "Committee on Agriculture, Nutrition, and Forestry",
                "chamber": "senate",
                "congress": congress,
                "type": "Standing",
                "jurisdiction": "Agriculture, nutrition, and rural development"
            },
            {
                "code": "HSIF",
                "name": "Committee on Energy and Commerce",
                "chamber": "house",
                "congress": congress,
                "type": "Standing",
                "jurisdiction": "Energy, commerce, and communications"
            }
        ]

        return {
            "committees": mock_committees,
            "total": len(mock_committees),
            "by_chamber": {
                "house": [c for c in mock_committees if c["chamber"] == "house"],
                "senate": [c for c in mock_committees if c["chamber"] == "senate"],
                "joint": []
            },
            "congress": congress,
            "is_mock": True
        }
