"""
Congress.gov API Client

Client for fetching committee membership and related data from the Congress.gov API.
Handles rate limiting, error handling, and data normalization.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from models.committee import (
    Chamber,
    Committee,
    CommitteeDocument,
    CommitteeHearing,
    CommitteeMeeting,
    CommitteeMember,
    CommitteeType,
    MemberRole,
    Subcommittee,
    Witness,
    get_committee_code_variations,
    normalize_committee_code,
)

logger = logging.getLogger(__name__)


class CongressAPIError(Exception):
    """Custom exception for Congress.gov API errors"""
    pass


class CongressAPIClient:
    """
    Congress.gov API client for fetching committee and member data.

    Handles authentication, rate limiting, and data normalization.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DATA_GOV_API_KEY")
        self.base_url = "https://api.congress.gov/v3"
        self.session = None

        # Rate limiting: 1000 requests/hour = ~16 requests/minute
        self.request_delay = 4  # seconds between requests
        self.last_request_time = 0

        if not self.api_key:
            logger.warning("No Congress.gov API key found. Some features may be limited.")

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Congressional-Transparency-Platform/1.0",
                "Accept": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make rate-limited request to Congress.gov API.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            CongressAPIError: If request fails
        """
        if not self.session:
            raise CongressAPIError("Client session not initialized. Use async context manager.")

        # Add API key to params
        if params is None:
            params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        params["format"] = "json"

        # Rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        try:
            async with self.session.get(url, params=params) as response:
                self.last_request_time = asyncio.get_event_loop().time()

                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    logger.warning(f"Resource not found: {url}")
                    return {}
                elif response.status == 429:
                    # Rate limit hit, wait longer
                    await asyncio.sleep(60)
                    async with self.session.get(url, params=params) as retry_response:
                        if retry_response.status == 200:
                            return await retry_response.json()
                        else:
                            raise CongressAPIError(f"API request failed after retry: {retry_response.status}")
                else:
                    error_text = await response.text()
                    raise CongressAPIError(f"API request failed: {response.status} - {error_text}")

        except aiohttp.ClientError as e:
            raise CongressAPIError(f"Network error: {str(e)}") from e
        except Exception as e:
            raise CongressAPIError(f"Unexpected error: {str(e)}") from e

    async def get_committee_details(self, system_code: str, congress: int = 118) -> Optional[Committee]:
        """
        Get detailed committee information including members.

        Args:
            system_code: Committee system code (e.g., 'ssju00', 'SSJU')
            congress: Congress number

        Returns:
            Committee object with details and members, or None if not found
        """
        # Try different code variations
        code_variations = get_committee_code_variations(system_code)

        for code in code_variations:
            try:
                # Determine chamber from code
                normalized = normalize_committee_code(code)
                chamber_name = normalized["chamber"].lower()

                if chamber_name == "unknown":
                    # Try all chambers
                    chambers = ["house", "senate"]
                else:
                    chambers = [chamber_name]

                for chamber in chambers:
                    url = f"{self.base_url}/committee/{chamber}/{code}"

                    logger.info(f"Fetching committee details: {url}")
                    data = await self._make_request(url)

                    if data and "committee" in data:
                        committee_data = data["committee"]

                        # Convert to Committee model
                        committee = self._parse_committee_data(committee_data, congress)

                        # Fetch members separately
                        members = await self.get_committee_members(code, congress, chamber)
                        if members:
                            committee.members = members
                            committee.member_count = len(members)

                        return committee

            except CongressAPIError as e:
                logger.warning(f"Error fetching committee {code}: {e}")
                continue

        logger.warning(f"Committee not found: {system_code}")
        return None

    async def get_committee_members(
        self,
        system_code: str,
        congress: int = 118,
        chamber: Optional[str] = None
    ) -> List[CommitteeMember]:
        """
        Get committee members from Congress.gov API.

        Note: The Congress.gov API doesn't have a direct committee members endpoint,
        so this method searches through member data for committee associations.

        Args:
            system_code: Committee system code
            congress: Congress number
            chamber: Chamber name (house/senate)

        Returns:
            List of CommitteeMember objects
        """
        members = []

        if not chamber:
            normalized = normalize_committee_code(system_code)
            chamber = normalized["chamber"].lower()

        if chamber == "unknown":
            return members

        try:
            # Fetch members from the chamber
            url = f"{self.base_url}/member/{chamber}"
            params = {"currentMember": "true", "limit": 250}

            logger.info(f"Fetching {chamber} members for committee {system_code}")
            data = await self._make_request(url, params)

            if not data or "members" not in data:
                return members

            # Check each member for committee associations
            for member_item in data["members"]:
                try:
                    member_url = member_item.get("url")
                    if member_url:
                        member_data = await self._make_request(member_url)
                        if member_data and "member" in member_data:
                            member_detail = member_data["member"]

                            # Check if member is on this committee
                            member_committees = member_detail.get("committees", {}).get("item", [])

                            for committee_info in member_committees:
                                committee_system_code = committee_info.get("systemCode", "").lower()
                                if committee_system_code == system_code.lower():
                                    # Found a member on this committee
                                    committee_member = self._parse_member_data(
                                        member_detail, committee_info, congress
                                    )
                                    members.append(committee_member)
                                    break

                except Exception as e:
                    logger.warning(f"Error processing member data: {e}")
                    continue

                # Limit to prevent too many API calls
                if len(members) >= 50:
                    break

        except CongressAPIError as e:
            logger.error(f"Error fetching committee members: {e}")

        return members

    async def get_subcommittees(self, parent_system_code: str, congress: int = 118) -> List[Subcommittee]:
        """
        Get subcommittees for a parent committee.

        Args:
            parent_system_code: Parent committee system code
            congress: Congress number

        Returns:
            List of Subcommittee objects
        """
        subcommittees = []

        try:
            committee = await self.get_committee_details(parent_system_code, congress)
            if not committee:
                return subcommittees

            # Get committee data to find subcommittees
            normalized = normalize_committee_code(parent_system_code)
            chamber = normalized["chamber"].lower()

            if chamber == "unknown":
                return subcommittees

            url = f"{self.base_url}/committee/{chamber}/{parent_system_code.lower()}"
            data = await self._make_request(url)

            if data and "committee" in data:
                committee_data = data["committee"]
                subcommittee_items = committee_data.get("subcommittees", {}).get("item", [])

                for sub_item in subcommittee_items:
                    subcommittee = Subcommittee(
                        system_code=sub_item.get("systemCode", ""),
                        name=sub_item.get("name", ""),
                        parent_system_code=parent_system_code,
                        parent_name=committee_data.get("name", ""),
                        chamber=Chamber(committee_data.get("chamber", "House")),
                        congress=congress,
                        congress_url=sub_item.get("url")
                    )
                    subcommittees.append(subcommittee)

        except CongressAPIError as e:
            logger.error(f"Error fetching subcommittees: {e}")

        return subcommittees

    def _parse_committee_data(self, committee_data: Dict[str, Any], congress: int) -> Committee:
        """Parse committee data from Congress.gov API response."""
        system_code = committee_data.get("systemCode", "")
        normalized = normalize_committee_code(system_code)

        # Parse chamber
        chamber_str = committee_data.get("chamber", "House")
        try:
            chamber = Chamber(chamber_str)
        except ValueError:
            chamber = Chamber.HOUSE

        # Parse committee type
        committee_type_str = committee_data.get("committeeTypeCode", "Standing")
        try:
            committee_type = CommitteeType(committee_type_str)
        except ValueError:
            committee_type = CommitteeType.STANDING

        # Parse update date
        update_date = None
        update_date_str = committee_data.get("updateDate")
        if update_date_str:
            try:
                update_date = datetime.fromisoformat(update_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        return Committee(
            system_code=system_code,
            name=committee_data.get("name", ""),
            chamber=chamber,
            committee_type=committee_type,
            congress=congress,
            short_code=normalized["short_code"],
            congress_url=committee_data.get("url"),
            update_date=update_date,
            is_current=committee_data.get("isCurrent", True),
            bills_count=committee_data.get("bills", {}).get("count"),
            reports_count=committee_data.get("reports", {}).get("count"),
            communications_count=committee_data.get("communications", {}).get("count"),
            nominations_count=committee_data.get("nominations", {}).get("count"),
            establishing_authority=committee_data.get("establishingAuthority"),
            loc_linked_data_id=committee_data.get("locLinkedDataId"),
            nara_id=committee_data.get("naraId"),
            superintendent_document_number=committee_data.get("superintendentDocumentNumber")
        )

    def _parse_member_data(
        self,
        member_data: Dict[str, Any],
        committee_info: Dict[str, Any],
        congress: int
    ) -> CommitteeMember:
        """Parse member data from Congress.gov API response."""

        # Parse member role
        role_str = committee_info.get("role", "Member")
        try:
            role = MemberRole(role_str)
        except ValueError:
            role = MemberRole.MEMBER

        # Parse start/end dates
        start_date = None
        end_date = None

        start_date_str = committee_info.get("startDate")
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        end_date_str = committee_info.get("endDate")
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        return CommitteeMember(
            bioguide_id=member_data.get("bioguideId", ""),
            name=member_data.get("name", ""),
            party=member_data.get("partyName"),
            state=member_data.get("state"),
            district=member_data.get("district"),
            role=role,
            start_date=start_date,
            end_date=end_date,
            is_current=end_date is None,
            image_url=member_data.get("depiction", {}).get("imageUrl"),
            congress_url=member_data.get("url"),
            terms=member_data.get("terms", {}).get("item", [])
        )

    async def search_committees(
        self,
        congress: int = 118,
        chamber: Optional[str] = None
    ) -> List[Committee]:
        """
        Search for committees in a given congress and chamber.

        Args:
            congress: Congress number
            chamber: Chamber filter (house/senate)

        Returns:
            List of Committee objects
        """
        committees = []

        try:
            if chamber:
                chambers = [chamber.lower()]
            else:
                chambers = ["house", "senate"]

            for chamber_name in chambers:
                url = f"{self.base_url}/committee/{congress}/{chamber_name}"
                params = {"limit": 250}

                logger.info(f"Searching committees in {chamber_name} for congress {congress}")
                data = await self._make_request(url, params)

                if data and "committees" in data:
                    for committee_item in data["committees"]:
                        try:
                            committee = self._parse_committee_data(committee_item, congress)
                            committees.append(committee)
                        except Exception as e:
                            logger.warning(f"Error parsing committee data: {e}")
                            continue

        except CongressAPIError as e:
            logger.error(f"Error searching committees: {e}")

        return committees

    async def get_committee_hearings(
        self,
        system_code: str,
        congress: int = 118,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommitteeHearing]:
        """
        Get committee hearings from Congress.gov API.

        Args:
            system_code: Committee system code
            congress: Congress number
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of CommitteeHearing objects
        """
        hearings = []

        try:
            # Determine chamber from code
            normalized = normalize_committee_code(system_code)
            chamber_name = normalized["chamber"].lower()

            if chamber_name == "unknown":
                chambers = ["house", "senate"]
            else:
                chambers = [chamber_name]

            for chamber in chambers:
                try:
                    url = f"{self.base_url}/committee/{chamber}/{system_code.lower()}/hearings"
                    params = {
                        "limit": limit,
                        "offset": offset,
                        "congress": congress
                    }

                    logger.info(f"Fetching committee hearings: {url}")
                    data = await self._make_request(url, params)

                    if data and "hearings" in data:
                        for hearing_item in data["hearings"]:
                            try:
                                hearing = self._parse_hearing_data(hearing_item, system_code, congress)
                                if hearing:
                                    hearings.append(hearing)
                            except Exception as e:
                                logger.warning(f"Error parsing hearing data: {e}")
                                continue

                    # If we found hearings in this chamber, don't try others
                    if hearings:
                        break

                except CongressAPIError as e:
                    logger.warning(f"Error fetching hearings for {system_code} in {chamber}: {e}")
                    continue

        except CongressAPIError as e:
            logger.error(f"Error fetching committee hearings: {e}")

        return hearings

    async def get_committee_meetings(
        self,
        system_code: str,
        congress: int = 118,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommitteeMeeting]:
        """
        Get committee meetings/markups from Congress.gov API.

        Args:
            system_code: Committee system code
            congress: Congress number
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of CommitteeMeeting objects
        """
        meetings = []

        try:
            # Determine chamber from code
            normalized = normalize_committee_code(system_code)
            chamber_name = normalized["chamber"].lower()

            if chamber_name == "unknown":
                chambers = ["house", "senate"]
            else:
                chambers = [chamber_name]

            for chamber in chambers:
                try:
                    url = f"{self.base_url}/committee/{chamber}/{system_code.lower()}/meetings"
                    params = {
                        "limit": limit,
                        "offset": offset,
                        "congress": congress
                    }

                    logger.info(f"Fetching committee meetings: {url}")
                    data = await self._make_request(url, params)

                    if data and "meetings" in data:
                        for meeting_item in data["meetings"]:
                            try:
                                meeting = self._parse_meeting_data(meeting_item, system_code, congress)
                                if meeting:
                                    meetings.append(meeting)
                            except Exception as e:
                                logger.warning(f"Error parsing meeting data: {e}")
                                continue

                    # If we found meetings in this chamber, don't try others
                    if meetings:
                        break

                except CongressAPIError as e:
                    logger.warning(f"Error fetching meetings for {system_code} in {chamber}: {e}")
                    continue

        except CongressAPIError as e:
            logger.error(f"Error fetching committee meetings: {e}")

        return meetings

    async def get_committee_documents(
        self,
        system_code: str,
        congress: int = 118,
        document_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommitteeDocument]:
        """
        Get committee documents/reports from Congress.gov API.

        Args:
            system_code: Committee system code
            congress: Congress number
            document_type: Filter by document type (report, print, document)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of CommitteeDocument objects
        """
        documents = []

        try:
            # Determine chamber from code
            normalized = normalize_committee_code(system_code)
            chamber_name = normalized["chamber"].lower()

            if chamber_name == "unknown":
                chambers = ["house", "senate"]
            else:
                chambers = [chamber_name]

            for chamber in chambers:
                try:
                    # Try different document endpoints
                    endpoints = ["reports"]
                    if not document_type or document_type != "report":
                        endpoints.extend(["prints", "documents"])

                    for endpoint in endpoints:
                        url = f"{self.base_url}/committee/{chamber}/{system_code.lower()}/{endpoint}"
                        params = {
                            "limit": limit,
                            "offset": offset,
                            "congress": congress
                        }

                        if document_type:
                            params["type"] = document_type

                        logger.info(f"Fetching committee documents: {url}")
                        data = await self._make_request(url, params)

                        if data and endpoint in data:
                            for doc_item in data[endpoint]:
                                try:
                                    document = self._parse_document_data(doc_item, system_code, congress, endpoint.rstrip("s"))
                                    if document:
                                        documents.append(document)
                                except Exception as e:
                                    logger.warning(f"Error parsing document data: {e}")
                                    continue

                    # If we found documents in this chamber, don't try others
                    if documents:
                        break

                except CongressAPIError as e:
                    logger.warning(f"Error fetching documents for {system_code} in {chamber}: {e}")
                    continue

        except CongressAPIError as e:
            logger.error(f"Error fetching committee documents: {e}")

        return documents

    def _parse_hearing_data(self, hearing_data: Dict[str, Any], system_code: str, congress: int) -> Optional[CommitteeHearing]:
        """Parse hearing data from Congress.gov API response."""
        try:
            # Generate hearing ID if not provided
            hearing_id = hearing_data.get("hearingId") or f"{system_code}_{congress}_{hearing_data.get('date', 'unknown')}"

            # Parse date
            hearing_date = None
            date_str = hearing_data.get("date")
            if date_str:
                try:
                    hearing_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        hearing_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pass

            # Parse witnesses
            witnesses = []
            witness_list = hearing_data.get("witnesses", [])
            if isinstance(witness_list, list):
                for witness_item in witness_list:
                    witness = Witness(
                        name=witness_item.get("name", "Unknown"),
                        title=witness_item.get("title"),
                        organization=witness_item.get("organization"),
                        witness_type=witness_item.get("type"),
                        testimony_url=witness_item.get("testimonyUrl"),
                        biography=witness_item.get("biography")
                    )
                    witnesses.append(witness)

            # Parse topics
            topics = hearing_data.get("topics", [])
            if isinstance(topics, str):
                topics = [topics]
            elif not isinstance(topics, list):
                topics = []

            # Parse related bills
            related_bills = hearing_data.get("relatedBills", [])
            if isinstance(related_bills, str):
                related_bills = [related_bills]
            elif not isinstance(related_bills, list):
                related_bills = []

            # Parse dates
            created_date = None
            updated_date = None

            created_str = hearing_data.get("createdDate")
            if created_str:
                try:
                    created_date = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            updated_str = hearing_data.get("updateDate")
            if updated_str:
                try:
                    updated_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            return CommitteeHearing(
                hearing_id=hearing_id,
                committee_system_code=system_code,
                committee_name=hearing_data.get("committeeName"),
                subcommittee_system_code=hearing_data.get("subcommitteeSystemCode"),
                subcommittee_name=hearing_data.get("subcommitteeName"),
                title=hearing_data.get("title", "Untitled Hearing"),
                hearing_type=hearing_data.get("hearingType"),
                date=hearing_date or datetime.now(),
                location=hearing_data.get("location"),
                congress=congress,
                status=hearing_data.get("status", "scheduled"),
                format=hearing_data.get("format"),
                is_public=hearing_data.get("isPublic", True),
                description=hearing_data.get("description"),
                witnesses=witnesses,
                topics=topics,
                agenda_url=hearing_data.get("agendaUrl"),
                transcript_url=hearing_data.get("transcriptUrl"),
                video_url=hearing_data.get("videoUrl"),
                webcast_url=hearing_data.get("webcastUrl"),
                related_bills=related_bills,
                congress_url=hearing_data.get("url"),
                created_date=created_date,
                updated_date=updated_date
            )

        except Exception as e:
            logger.error(f"Error parsing hearing data: {e}")
            return None

    def _parse_meeting_data(self, meeting_data: Dict[str, Any], system_code: str, congress: int) -> Optional[CommitteeMeeting]:
        """Parse meeting data from Congress.gov API response."""
        try:
            # Generate meeting ID if not provided
            meeting_id = meeting_data.get("meetingId") or f"{system_code}_{congress}_{meeting_data.get('date', 'unknown')}"

            # Parse date
            meeting_date = None
            date_str = meeting_data.get("date")
            if date_str:
                try:
                    meeting_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        meeting_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pass

            # Parse agenda items
            agenda_items = meeting_data.get("agendaItems", [])
            if isinstance(agenda_items, str):
                agenda_items = [agenda_items]
            elif not isinstance(agenda_items, list):
                agenda_items = []

            # Parse bills
            bills_considered = meeting_data.get("billsConsidered", [])
            bills_reported = meeting_data.get("billsReported", [])
            bills_tabled = meeting_data.get("billsTabled", [])

            for bills_list in [bills_considered, bills_reported, bills_tabled]:
                if isinstance(bills_list, str):
                    bills_list = [bills_list]
                elif not isinstance(bills_list, list):
                    bills_list = []

            # Parse dates
            created_date = None
            updated_date = None

            created_str = meeting_data.get("createdDate")
            if created_str:
                try:
                    created_date = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            updated_str = meeting_data.get("updateDate")
            if updated_str:
                try:
                    updated_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            return CommitteeMeeting(
                meeting_id=meeting_id,
                committee_system_code=system_code,
                committee_name=meeting_data.get("committeeName"),
                subcommittee_system_code=meeting_data.get("subcommitteeSystemCode"),
                subcommittee_name=meeting_data.get("subcommitteeName"),
                title=meeting_data.get("title", "Committee Meeting"),
                meeting_type=meeting_data.get("meetingType", "business meeting"),
                date=meeting_date or datetime.now(),
                location=meeting_data.get("location"),
                congress=congress,
                status=meeting_data.get("status", "scheduled"),
                format=meeting_data.get("format"),
                is_public=meeting_data.get("isPublic", True),
                purpose=meeting_data.get("purpose"),
                agenda_items=agenda_items,
                bills_considered=bills_considered,
                bills_reported=bills_reported,
                bills_tabled=bills_tabled,
                agenda_url=meeting_data.get("agendaUrl"),
                minutes_url=meeting_data.get("minutesUrl"),
                video_url=meeting_data.get("videoUrl"),
                transcript_url=meeting_data.get("transcriptUrl"),
                votes_taken=meeting_data.get("votesTaken", 0),
                amendments_offered=meeting_data.get("amendmentsOffered", 0),
                congress_url=meeting_data.get("url"),
                created_date=created_date,
                updated_date=updated_date
            )

        except Exception as e:
            logger.error(f"Error parsing meeting data: {e}")
            return None

    def _parse_document_data(self, doc_data: Dict[str, Any], system_code: str, congress: int, doc_type: str) -> Optional[CommitteeDocument]:
        """Parse document data from Congress.gov API response."""
        try:
            # Generate document ID if not provided
            document_id = doc_data.get("documentId") or f"{system_code}_{congress}_{doc_type}_{doc_data.get('number', 'unknown')}"

            # Parse dates
            publication_date = None
            created_date = None
            updated_date = None

            pub_str = doc_data.get("publicationDate") or doc_data.get("publishedDate")
            if pub_str:
                try:
                    publication_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        publication_date = datetime.strptime(pub_str, "%Y-%m-%d")
                    except ValueError:
                        pass

            created_str = doc_data.get("createdDate")
            if created_str:
                try:
                    created_date = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            updated_str = doc_data.get("updateDate")
            if updated_str:
                try:
                    updated_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            # Parse subject areas and keywords
            subject_areas = doc_data.get("subjectAreas", [])
            policy_areas = doc_data.get("policyAreas", [])
            keywords = doc_data.get("keywords", [])

            for field in [subject_areas, policy_areas, keywords]:
                if isinstance(field, str):
                    field = [field]
                elif not isinstance(field, list):
                    field = []

            # Parse related content
            related_bills = doc_data.get("relatedBills", [])
            related_hearings = doc_data.get("relatedHearings", [])

            if isinstance(related_bills, str):
                related_bills = [related_bills]
            elif not isinstance(related_bills, list):
                related_bills = []

            if isinstance(related_hearings, str):
                related_hearings = [related_hearings]
            elif not isinstance(related_hearings, list):
                related_hearings = []

            return CommitteeDocument(
                document_id=document_id,
                committee_system_code=system_code,
                committee_name=doc_data.get("committeeName"),
                subcommittee_system_code=doc_data.get("subcommitteeSystemCode"),
                subcommittee_name=doc_data.get("subcommitteeName"),
                title=doc_data.get("title", "Untitled Document"),
                document_type=doc_type,
                document_number=doc_data.get("number"),
                congress=congress,
                session=doc_data.get("session"),
                description=doc_data.get("description"),
                summary=doc_data.get("summary"),
                page_count=doc_data.get("pageCount"),
                file_size=doc_data.get("fileSize"),
                format=doc_data.get("format"),
                publication_date=publication_date,
                is_published=doc_data.get("isPublished", False),
                is_public=doc_data.get("isPublic", True),
                subject_areas=subject_areas,
                policy_areas=policy_areas,
                keywords=keywords,
                related_bills=related_bills,
                related_hearings=related_hearings,
                document_url=doc_data.get("url"),
                pdf_url=doc_data.get("pdfUrl"),
                html_url=doc_data.get("htmlUrl"),
                xml_url=doc_data.get("xmlUrl"),
                congress_url=doc_data.get("congressUrl"),
                gpo_url=doc_data.get("gpoUrl"),
                created_date=created_date,
                updated_date=updated_date
            )

        except Exception as e:
            logger.error(f"Error parsing document data: {e}")
            return None
