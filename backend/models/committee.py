"""
Committee Data Models

Pydantic v2 models for committee, subcommittee, and membership data.
Supports both Congress.gov API format and normalized internal representation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Chamber(str, Enum):
    """Chamber enumeration"""
    HOUSE = "House"
    SENATE = "Senate"
    JOINT = "Joint"
    NO_CHAMBER = "NoChamber"


class CommitteeType(str, Enum):
    """Committee type enumeration"""
    STANDING = "Standing"
    SELECT = "Select"
    SPECIAL = "Special"
    JOINT = "Joint"
    SUBCOMMITTEE = "Subcommittee"
    TASK_FORCE = "Task Force"
    COMMISSION_OR_CAUCUS = "Commission or Caucus"
    OTHER = "Other"


class MemberRole(str, Enum):
    """Committee member role enumeration"""
    CHAIR = "Chair"
    RANKING_MEMBER = "Ranking Member"
    VICE_CHAIR = "Vice Chair"
    MEMBER = "Member"
    EX_OFFICIO = "Ex Officio"


class CommitteeMember(BaseModel):
    """Committee member model"""
    model_config = ConfigDict(extra="allow")

    bioguide_id: str = Field(..., description="Member's bioguide identifier")
    name: str = Field(..., description="Member's full name")
    party: Optional[str] = Field(None, description="Political party affiliation")
    state: Optional[str] = Field(None, description="State represented")
    district: Optional[str] = Field(None, description="District number (House only)")
    role: MemberRole = Field(default=MemberRole.MEMBER, description="Role on committee")
    start_date: Optional[datetime] = Field(None, description="Date member joined committee")
    end_date: Optional[datetime] = Field(None, description="Date member left committee (if applicable)")
    is_current: bool = Field(default=True, description="Whether member is currently on committee")
    image_url: Optional[str] = Field(None, description="Member's photo URL")

    # Additional Congress.gov API fields
    congress_url: Optional[str] = Field(None, description="Congress.gov API URL")
    terms: Optional[List[Dict[str, Any]]] = Field(None, description="Member's terms of service")


class Subcommittee(BaseModel):
    """Subcommittee model"""
    model_config = ConfigDict(extra="allow")

    system_code: str = Field(..., description="Unique system code (e.g., ssju01)")
    name: str = Field(..., description="Subcommittee name")
    parent_system_code: str = Field(..., description="Parent committee system code")
    parent_name: Optional[str] = Field(None, description="Parent committee name")
    chamber: Chamber = Field(..., description="Chamber (House/Senate/Joint)")
    committee_type: CommitteeType = Field(default=CommitteeType.SUBCOMMITTEE)
    congress: int = Field(..., description="Congress number")

    # API metadata
    congress_url: Optional[str] = Field(None, description="Congress.gov API URL")
    update_date: Optional[datetime] = Field(None, description="Last update timestamp")
    is_current: bool = Field(default=True, description="Whether subcommittee is currently active")

    # Members and activity
    members: Optional[List[CommitteeMember]] = Field(None, description="Subcommittee members")
    member_count: int = Field(default=0, description="Number of members")
    bills_count: Optional[int] = Field(None, description="Number of associated bills")


class Committee(BaseModel):
    """Main committee model"""
    model_config = ConfigDict(extra="allow")

    system_code: str = Field(..., description="Unique system code (e.g., ssju00)")
    name: str = Field(..., description="Committee name")
    chamber: Chamber = Field(..., description="Chamber (House/Senate/Joint)")
    committee_type: CommitteeType = Field(..., description="Committee type")
    congress: int = Field(..., description="Congress number")

    # Normalized codes for different formats
    short_code: Optional[str] = Field(None, description="Short code (e.g., SSJU)")
    thomas_code: Optional[str] = Field(None, description="Legacy THOMAS system code")

    # API metadata
    congress_url: Optional[str] = Field(None, description="Congress.gov API URL")
    update_date: Optional[datetime] = Field(None, description="Last update timestamp")
    is_current: bool = Field(default=True, description="Whether committee is currently active")

    # Committee structure
    subcommittees: List[Subcommittee] = Field(default_factory=list, description="Committee subcommittees")
    members: List[CommitteeMember] = Field(default_factory=list, description="Committee members")

    # Statistics and counts
    member_count: int = Field(default=0, description="Number of members")
    subcommittee_count: int = Field(default=0, description="Number of subcommittees")
    bills_count: Optional[int] = Field(None, description="Number of associated bills")
    reports_count: Optional[int] = Field(None, description="Number of committee reports")
    communications_count: Optional[int] = Field(None, description="Number of communications")
    nominations_count: Optional[int] = Field(None, description="Number of nominations (Senate only)")

    # Additional Congress.gov fields
    establishing_authority: Optional[str] = Field(None, description="Legislative authority for committee")
    jurisdiction: Optional[str] = Field(None, description="Committee jurisdiction")
    loc_linked_data_id: Optional[str] = Field(None, description="Library of Congress linked data ID")
    nara_id: Optional[str] = Field(None, description="NARA identifier")
    superintendent_document_number: Optional[str] = Field(None, description="GPO document number")


class CommitteeActivity(BaseModel):
    """Committee activity model"""
    model_config = ConfigDict(extra="allow")

    committee_system_code: str = Field(..., description="Committee system code")
    activity_type: str = Field(..., description="Type of activity")
    activity_name: str = Field(..., description="Name/description of activity")
    date: datetime = Field(..., description="Date of activity")
    congress: int = Field(..., description="Congress number")

    # Optional details
    bill_number: Optional[str] = Field(None, description="Associated bill number")
    meeting_id: Optional[str] = Field(None, description="Meeting identifier")
    description: Optional[str] = Field(None, description="Activity description")


class Witness(BaseModel):
    """Witness for committee hearings"""
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Witness name")
    title: Optional[str] = Field(None, description="Professional title")
    organization: Optional[str] = Field(None, description="Organization/affiliation")
    witness_type: Optional[str] = Field(None, description="Type of witness (e.g., expert, stakeholder)")
    testimony_url: Optional[str] = Field(None, description="URL to written testimony")
    biography: Optional[str] = Field(None, description="Brief biography")


class CommitteeHearing(BaseModel):
    """Committee hearing model"""
    model_config = ConfigDict(extra="allow")

    hearing_id: str = Field(..., description="Unique hearing identifier")
    committee_system_code: str = Field(..., description="Committee system code")
    committee_name: Optional[str] = Field(None, description="Committee name")
    subcommittee_system_code: Optional[str] = Field(None, description="Subcommittee system code if applicable")
    subcommittee_name: Optional[str] = Field(None, description="Subcommittee name")

    # Hearing details
    title: str = Field(..., description="Hearing title")
    hearing_type: Optional[str] = Field(None, description="Type of hearing")
    date: datetime = Field(..., description="Hearing date and time")
    location: Optional[str] = Field(None, description="Hearing location/room")
    congress: int = Field(..., description="Congress number")

    # Status and format
    status: str = Field(default="scheduled", description="Hearing status (scheduled, completed, cancelled)")
    format: Optional[str] = Field(None, description="Hearing format (in-person, hybrid, virtual)")
    is_public: bool = Field(default=True, description="Whether hearing is public")

    # Content
    description: Optional[str] = Field(None, description="Hearing description/purpose")
    witnesses: List[Witness] = Field(default_factory=list, description="List of witnesses")
    topics: List[str] = Field(default_factory=list, description="Hearing topics/subjects")

    # Related materials
    agenda_url: Optional[str] = Field(None, description="URL to hearing agenda")
    transcript_url: Optional[str] = Field(None, description="URL to hearing transcript")
    video_url: Optional[str] = Field(None, description="URL to hearing video")
    webcast_url: Optional[str] = Field(None, description="URL to live webcast")

    # Bills and legislation
    related_bills: List[str] = Field(default_factory=list, description="Related bill numbers")

    # Metadata
    congress_url: Optional[str] = Field(None, description="Congress.gov URL")
    created_date: Optional[datetime] = Field(None, description="When hearing was created")
    updated_date: Optional[datetime] = Field(None, description="Last update date")


class CommitteeMeeting(BaseModel):
    """Committee meeting/markup model"""
    model_config = ConfigDict(extra="allow")

    meeting_id: str = Field(..., description="Unique meeting identifier")
    committee_system_code: str = Field(..., description="Committee system code")
    committee_name: Optional[str] = Field(None, description="Committee name")
    subcommittee_system_code: Optional[str] = Field(None, description="Subcommittee system code if applicable")
    subcommittee_name: Optional[str] = Field(None, description="Subcommittee name")

    # Meeting details
    title: str = Field(..., description="Meeting title")
    meeting_type: str = Field(..., description="Type of meeting (markup, business meeting, etc.)")
    date: datetime = Field(..., description="Meeting date and time")
    location: Optional[str] = Field(None, description="Meeting location/room")
    congress: int = Field(..., description="Congress number")

    # Status and format
    status: str = Field(default="scheduled", description="Meeting status (scheduled, completed, cancelled)")
    format: Optional[str] = Field(None, description="Meeting format (in-person, hybrid, virtual)")
    is_public: bool = Field(default=True, description="Whether meeting is public")

    # Agenda and purpose
    purpose: Optional[str] = Field(None, description="Meeting purpose")
    agenda_items: List[str] = Field(default_factory=list, description="Agenda items")

    # Bills under consideration
    bills_considered: List[str] = Field(default_factory=list, description="Bills under consideration")
    bills_reported: List[str] = Field(default_factory=list, description="Bills reported out")
    bills_tabled: List[str] = Field(default_factory=list, description="Bills tabled")

    # Related materials
    agenda_url: Optional[str] = Field(None, description="URL to meeting agenda")
    minutes_url: Optional[str] = Field(None, description="URL to meeting minutes")
    video_url: Optional[str] = Field(None, description="URL to meeting video")
    transcript_url: Optional[str] = Field(None, description="URL to meeting transcript")

    # Results
    votes_taken: int = Field(default=0, description="Number of votes taken")
    amendments_offered: int = Field(default=0, description="Number of amendments offered")

    # Metadata
    congress_url: Optional[str] = Field(None, description="Congress.gov URL")
    created_date: Optional[datetime] = Field(None, description="When meeting was created")
    updated_date: Optional[datetime] = Field(None, description="Last update date")


class CommitteeDocument(BaseModel):
    """Committee document/report model"""
    model_config = ConfigDict(extra="allow")

    document_id: str = Field(..., description="Unique document identifier")
    committee_system_code: str = Field(..., description="Committee system code")
    committee_name: Optional[str] = Field(None, description="Committee name")
    subcommittee_system_code: Optional[str] = Field(None, description="Subcommittee system code if applicable")
    subcommittee_name: Optional[str] = Field(None, description="Subcommittee name")

    # Document details
    title: str = Field(..., description="Document title")
    document_type: str = Field(..., description="Type of document (report, print, document)")
    document_number: Optional[str] = Field(None, description="Official document number")
    congress: int = Field(..., description="Congress number")
    session: Optional[str] = Field(None, description="Session number")

    # Content and format
    description: Optional[str] = Field(None, description="Document description")
    summary: Optional[str] = Field(None, description="Document summary")
    page_count: Optional[int] = Field(None, description="Number of pages")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    format: Optional[str] = Field(None, description="Document format (PDF, HTML, etc.)")

    # Publication details
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    is_published: bool = Field(default=False, description="Whether document is published")
    is_public: bool = Field(default=True, description="Whether document is public")

    # Classification
    subject_areas: List[str] = Field(default_factory=list, description="Subject areas covered")
    policy_areas: List[str] = Field(default_factory=list, description="Policy areas")
    keywords: List[str] = Field(default_factory=list, description="Keywords/tags")

    # Related content
    related_bills: List[str] = Field(default_factory=list, description="Related bill numbers")
    related_hearings: List[str] = Field(default_factory=list, description="Related hearing IDs")

    # Access URLs
    document_url: Optional[str] = Field(None, description="URL to document")
    pdf_url: Optional[str] = Field(None, description="URL to PDF version")
    html_url: Optional[str] = Field(None, description="URL to HTML version")
    xml_url: Optional[str] = Field(None, description="URL to XML version")

    # Metadata
    congress_url: Optional[str] = Field(None, description="Congress.gov URL")
    gpo_url: Optional[str] = Field(None, description="GPO URL")
    created_date: Optional[datetime] = Field(None, description="When document was created")
    updated_date: Optional[datetime] = Field(None, description="Last update date")


class CommitteeAnalytics(BaseModel):
    """Committee analytics and metrics"""
    model_config = ConfigDict(extra="allow")

    committee_system_code: str = Field(..., description="Committee system code")
    committee_name: str = Field(..., description="Committee name")
    chamber: Chamber = Field(..., description="Chamber")
    committee_type: CommitteeType = Field(..., description="Committee type")
    congress: int = Field(..., description="Congress number")

    # Member analytics
    total_members: int = Field(default=0, description="Total members")
    republican_members: int = Field(default=0, description="Republican members")
    democratic_members: int = Field(default=0, description="Democratic members")
    independent_members: int = Field(default=0, description="Independent members")

    # Activity metrics
    bills_referred: int = Field(default=0, description="Bills referred to committee")
    bills_reported: int = Field(default=0, description="Bills reported by committee")
    bills_discharged: int = Field(default=0, description="Bills discharged from committee")
    meetings_held: int = Field(default=0, description="Meetings held")
    hearings_held: int = Field(default=0, description="Hearings held")
    markups_held: int = Field(default=0, description="Markup sessions held")

    # Time-based metrics
    recent_activity_count: int = Field(default=0, description="Recent activity (last 6 months)")
    activity_score: int = Field(default=0, description="Overall activity score (0-100)")

    # Policy focus
    top_policy_areas: List[Dict[str, Any]] = Field(default_factory=list, description="Top policy areas")

    # Timestamps
    last_updated: Optional[datetime] = Field(None, description="Last data update")
    generated_at: datetime = Field(default_factory=datetime.now, description="Analytics generation time")


# Helper functions for code normalization

def normalize_committee_code(system_code: str) -> Dict[str, str]:
    """
    Normalize committee codes between different formats.

    Args:
        system_code: Committee system code (e.g., 'ssju00', 'SSJU', 'hspw00')

    Returns:
        Dictionary with different code formats
    """
    system_code = system_code.strip().lower()

    # Extract chamber and committee parts
    if len(system_code) >= 4:
        chamber_code = system_code[0]  # h, s, j
        # committee_part = system_code[1:]  # e.g., 'sju00' - currently unused

        # Generate different formats
        formats = {
            "system_code": system_code,  # Original format: ssju00
            "short_code": system_code[:4].upper(),  # Short format: SSJU
            "congress_format": system_code,  # Congress.gov format: ssju00
            "chamber": _get_chamber_from_code(chamber_code),
            "is_subcommittee": not system_code.endswith("00")
        }

        return formats

    return {
        "system_code": system_code,
        "short_code": system_code.upper(),
        "congress_format": system_code,
        "chamber": "Unknown",
        "is_subcommittee": False
    }


def _get_chamber_from_code(chamber_code: str) -> str:
    """Get chamber name from chamber code."""
    mapping = {
        "h": "House",
        "s": "Senate",
        "j": "Joint"
    }
    return mapping.get(chamber_code.lower(), "Unknown")


def get_committee_code_variations(system_code: str) -> List[str]:
    """
    Get all possible variations of a committee code for searching.

    Args:
        system_code: Original committee code

    Returns:
        List of code variations to try when searching
    """
    normalized = normalize_committee_code(system_code)

    variations = [
        system_code,
        system_code.lower(),
        system_code.upper(),
        normalized["short_code"],
        normalized["congress_format"]
    ]

    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for code in variations:
        if code not in seen:
            seen.add(code)
            unique_variations.append(code)

    return unique_variations
