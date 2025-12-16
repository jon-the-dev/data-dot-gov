"""
Committee data models for Congressional committees and subcommittees.

Provides comprehensive Pydantic v2 models for committee data including
membership, activities, and jurisdictional information.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .enums import Chamber, CommitteeRole, CommitteeType, Party


class CommitteeMember(BaseModel):
    """A member of a congressional committee with enhanced role tracking."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    bioguide_id: str = Field(
        alias="bioguideId", min_length=1, description="Member bioguide ID"
    )
    name: str = Field(min_length=1, description="Member name")
    party: Party = Field(description="Member's party")
    state: str = Field(min_length=1, description="Member's state")
    rank: Optional[int] = Field(None, ge=1, description="Ranking on committee")

    # Enhanced role system
    role: CommitteeRole = Field(
        default=CommitteeRole.MEMBER, description="Committee role"
    )

    # Legacy boolean fields for backward compatibility
    is_chair: bool = Field(
        default=False, description="Whether member is committee chair (legacy)"
    )
    is_ranking_member: bool = Field(
        default=False, description="Whether member is ranking minority member (legacy)"
    )

    # Enhanced tenure tracking
    title: Optional[str] = Field(None, description="Committee position title")
    date_appointed: Optional[str] = Field(
        None, description="Date appointed to committee"
    )
    date_departed: Optional[str] = Field(
        None, description="Date departed from committee"
    )
    tenure_years: Optional[float] = Field(
        None, ge=0, description="Years of service on committee"
    )
    seniority_rank: Optional[int] = Field(
        None, ge=1, description="Seniority ranking within party on committee"
    )

    @field_validator("party", mode="before")
    @classmethod
    def normalize_party(cls, v: Any) -> Party:
        """Normalize party input."""
        return Party.normalize(v)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Any) -> CommitteeRole:
        """Normalize role input."""
        return CommitteeRole.normalize(v)

    def model_post_init(self, __context: Any) -> None:
        """Sync legacy boolean fields with role enum after initialization."""
        # Update role based on legacy fields if they are set
        if self.is_chair:
            object.__setattr__(self, "role", CommitteeRole.CHAIR)
        elif self.is_ranking_member:
            object.__setattr__(self, "role", CommitteeRole.RANKING_MEMBER)

        # Update legacy fields based on role
        if self.role == CommitteeRole.CHAIR:
            object.__setattr__(self, "is_chair", True)
        elif self.role == CommitteeRole.RANKING_MEMBER:
            object.__setattr__(self, "is_ranking_member", True)

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted display name with title."""
        party_display = f" ({self.party})" if self.party != Party.UNKNOWN else ""
        state_display = f"-{self.state}" if self.state else ""
        title_display = f", {self.title}" if self.title else ""

        return f"{self.name}{party_display}{state_display}{title_display}"

    @computed_field
    @property
    def is_leadership(self) -> bool:
        """Check if member holds leadership position."""
        return self.role.is_leadership

    @computed_field
    @property
    def is_voting_member(self) -> bool:
        """Check if member has voting privileges."""
        return self.role.is_voting_member

    @computed_field
    @property
    def role_priority(self) -> int:
        """Get numeric priority for role-based sorting."""
        return self.role.priority_order

    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if member is currently active on committee."""
        return self.date_departed is None


class CommitteeActivity(BaseModel):
    """Activity or hearing by a committee."""

    model_config = ConfigDict(
        extra="allow",  # Committee activities vary significantly
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    activity_type: str = Field(description="Type of activity (hearing, markup, etc.)")
    date: Optional[str] = Field(None, description="Date of activity")
    title: str = Field(min_length=1, description="Activity title")
    description: Optional[str] = Field(None, description="Activity description")
    location: Optional[str] = Field(None, description="Location of activity")
    witnesses: List[str] = Field(
        default_factory=list, description="Witnesses or participants"
    )
    documents: List[Dict[str, Any]] = Field(
        default_factory=list, description="Related documents"
    )

    @computed_field
    @property
    def is_hearing(self) -> bool:
        """Check if this is a hearing."""
        return "hearing" in self.activity_type.lower()

    @computed_field
    @property
    def is_markup(self) -> bool:
        """Check if this is a markup session."""
        return "markup" in self.activity_type.lower()


class CommitteeMeeting(BaseModel):
    """Enhanced model for committee meetings with detailed tracking."""

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    meeting_id: Optional[str] = Field(None, description="Unique meeting identifier")
    committee_code: str = Field(min_length=1, description="Committee system code")
    meeting_type: str = Field(description="Type of meeting (hearing, markup, business)")
    date: Optional[str] = Field(None, description="Meeting date")
    time: Optional[str] = Field(None, description="Meeting time")
    location: Optional[str] = Field(None, description="Meeting location")
    title: str = Field(min_length=1, description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")

    # Agenda and outcomes
    agenda_items: List[str] = Field(
        default_factory=list, description="Meeting agenda items"
    )
    outcomes: List[str] = Field(
        default_factory=list, description="Meeting outcomes or decisions"
    )

    # Participants
    witnesses: List[str] = Field(
        default_factory=list, description="Witnesses or presenters"
    )
    attending_members: List[str] = Field(
        default_factory=list, description="Bioguide IDs of attending members"
    )

    # Related content
    bills_considered: List[str] = Field(
        default_factory=list, description="Bill numbers considered"
    )
    documents: List[Dict[str, Any]] = Field(
        default_factory=list, description="Related documents"
    )
    transcripts: List[Dict[str, Any]] = Field(
        default_factory=list, description="Meeting transcripts"
    )

    # Status
    is_cancelled: bool = Field(
        default=False, description="Whether meeting was cancelled"
    )
    is_postponed: bool = Field(
        default=False, description="Whether meeting was postponed"
    )
    is_closed_session: bool = Field(
        default=False, description="Whether it was a closed session"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")

    @computed_field
    @property
    def is_hearing(self) -> bool:
        """Check if this is a hearing."""
        return "hearing" in self.meeting_type.lower()

    @computed_field
    @property
    def is_markup(self) -> bool:
        """Check if this is a markup session."""
        return "markup" in self.meeting_type.lower()

    @computed_field
    @property
    def is_business_meeting(self) -> bool:
        """Check if this is a business meeting."""
        return "business" in self.meeting_type.lower()

    @computed_field
    @property
    def has_witnesses(self) -> bool:
        """Check if meeting has witnesses."""
        return len(self.witnesses) > 0

    @computed_field
    @property
    def bills_count(self) -> int:
        """Get number of bills considered."""
        return len(self.bills_considered)


class BillCommitteeAction(BaseModel):
    """Model for tracking bill actions within committees."""

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Bill identification
    bill_number: str = Field(min_length=1, description="Bill number (e.g., H.R. 1234)")
    bill_title: Optional[str] = Field(None, description="Bill title")
    congress: int = Field(ge=1, le=200, description="Congress number")

    # Committee information
    committee_code: str = Field(min_length=1, description="Committee system code")
    committee_name: str = Field(min_length=1, description="Committee name")
    subcommittee_code: Optional[str] = Field(
        None, description="Subcommittee code if applicable"
    )

    # Action details
    action_type: str = Field(
        description="Type of action (referral, markup, report, discharge, etc.)"
    )
    action_date: Optional[str] = Field(None, description="Date of action")
    action_description: str = Field(
        min_length=1, description="Description of action taken"
    )

    # Referral information
    is_original_referral: bool = Field(
        default=False, description="Whether this is the original referral"
    )
    referral_type: Optional[str] = Field(
        None, description="Type of referral (sequential, joint, etc.)"
    )

    # Markup and voting
    markup_date: Optional[str] = Field(None, description="Date of markup if applicable")
    vote_results: Optional[Dict[str, Any]] = Field(
        None, description="Committee vote results if applicable"
    )
    amendments_offered: List[Dict[str, Any]] = Field(
        default_factory=list, description="Amendments offered during markup"
    )

    # Reporting
    is_reported: bool = Field(
        default=False, description="Whether bill was reported out"
    )
    report_date: Optional[str] = Field(None, description="Date reported if applicable")
    report_number: Optional[str] = Field(None, description="Committee report number")
    report_type: Optional[str] = Field(
        None, description="Type of report (favorable, unfavorable, amended, etc.)"
    )

    # Related documents
    documents: List[Dict[str, Any]] = Field(
        default_factory=list, description="Related documents"
    )

    # Status tracking
    current_status: str = Field(
        default="referred", description="Current status in committee"
    )
    is_active: bool = Field(default=True, description="Whether action is still active")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    source_api: str = Field(default="congress.gov", description="Source API")

    @computed_field
    @property
    def is_referred(self) -> bool:
        """Check if this is a referral action."""
        return "referral" in self.action_type.lower()

    @computed_field
    @property
    def is_markup_action(self) -> bool:
        """Check if this is a markup action."""
        return "markup" in self.action_type.lower()

    @computed_field
    @property
    def is_discharge_action(self) -> bool:
        """Check if this is a discharge action."""
        return "discharge" in self.action_type.lower()

    @computed_field
    @property
    def has_amendments(self) -> bool:
        """Check if amendments were offered."""
        return len(self.amendments_offered) > 0

    @computed_field
    @property
    def processing_days(self) -> Optional[int]:
        """Calculate days between referral and current action."""
        if not self.action_date:
            return None

        # This would need proper date parsing implementation
        # For now, return None as placeholder
        return None

    @computed_field
    @property
    def is_in_subcommittee(self) -> bool:
        """Check if action involves a subcommittee."""
        return self.subcommittee_code is not None

    def get_action_summary(self) -> str:
        """Get a human-readable summary of the action."""
        if self.is_referred:
            committee_info = self.committee_name
            if self.subcommittee_code:
                committee_info += " (Subcommittee)"
            return f"Referred to {committee_info}"
        elif self.is_reported:
            return f"Reported by {self.committee_name}"
        elif self.is_markup_action:
            return f"Markup by {self.committee_name}"
        else:
            return f"{self.action_type} by {self.committee_name}"


class Committee(BaseModel):
    """Model for Congressional committee data."""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for API flexibility
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Required identification fields
    system_code: str = Field(
        alias="systemCode", min_length=1, description="System code identifier"
    )
    name: str = Field(min_length=1, description="Committee name")
    chamber: Chamber = Field(description="Chamber the committee belongs to")
    committee_type: CommitteeType = Field(description="Type of committee")

    # Optional identification
    code: Optional[str] = Field(None, description="Alternative committee code")
    thomas_id: Optional[str] = Field(None, description="Thomas committee ID")

    # Hierarchy
    parent_committee: Optional[str] = Field(
        None, description="Parent committee (for subcommittees)"
    )
    subcommittees: List[str] = Field(
        default_factory=list, description="List of subcommittee codes"
    )

    # Membership
    members: List[CommitteeMember] = Field(
        default_factory=list, description="Committee members"
    )

    # Activities and meetings
    activities: List[CommitteeActivity] = Field(
        default_factory=list, description="Committee activities (legacy)"
    )
    meetings: List[CommitteeMeeting] = Field(
        default_factory=list, description="Committee meetings with detailed tracking"
    )

    # Enhanced bill activity tracking
    bill_actions: List[BillCommitteeAction] = Field(
        default_factory=list, description="Detailed bill actions in committee"
    )

    # Jurisdiction and scope
    jurisdiction: Optional[str] = Field(None, description="Committee jurisdiction")
    policy_areas: List[str] = Field(
        default_factory=list, description="Policy areas under jurisdiction"
    )

    # Bill activity
    bills_considered: List[Dict[str, Any]] = Field(
        default_factory=list, description="Bills considered by committee"
    )
    bills_reported: List[Dict[str, Any]] = Field(
        default_factory=list, description="Bills reported by committee"
    )

    # Status
    is_active: bool = Field(
        default=True, description="Whether committee is currently active"
    )

    # External references
    url: Optional[str] = Field(None, description="Committee website URL")
    congress_url: Optional[str] = Field(None, description="Congress.gov URL")

    # Metadata
    congress: Optional[int] = Field(None, ge=1, le=200, description="Congress number")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    source_api: str = Field(default="congress.gov", description="Source API")

    @field_validator("chamber", mode="before")
    @classmethod
    def normalize_chamber(cls, v: Any) -> Chamber:
        """Normalize chamber input."""
        return Chamber.normalize(v)

    @field_validator("committee_type", mode="before")
    @classmethod
    def normalize_committee_type(cls, v: Any) -> CommitteeType:
        """Normalize committee type input."""
        return CommitteeType.normalize(v)

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted committee name."""
        chamber_prefix = {
            Chamber.HOUSE: "House",
            Chamber.SENATE: "Senate",
            Chamber.JOINT: "Joint",
        }.get(self.chamber, "")

        return f"{chamber_prefix} {self.name}".strip()

    @computed_field
    @property
    def member_count(self) -> int:
        """Get total number of committee members."""
        return len(self.members)

    @computed_field
    @property
    def is_subcommittee(self) -> bool:
        """Check if this is a subcommittee."""
        return (
            self.parent_committee is not None
            or self.committee_type == CommitteeType.SUBCOMMITTEE
        )

    @computed_field
    @property
    def has_subcommittees(self) -> bool:
        """Check if this committee has subcommittees."""
        return len(self.subcommittees) > 0

    def get_members_by_party(self) -> Dict[Party, List[CommitteeMember]]:
        """Get committee members grouped by party."""
        party_members = {}
        for member in self.members:
            if member.party not in party_members:
                party_members[member.party] = []
            party_members[member.party].append(member)
        return party_members

    def get_party_breakdown(self) -> Dict[Party, int]:
        """Get count of members by party."""
        party_counts = {}
        for member in self.members:
            party_counts[member.party] = party_counts.get(member.party, 0) + 1
        return party_counts

    def get_chair(self) -> Optional[CommitteeMember]:
        """Get the committee chair."""
        chairs = [member for member in self.members if member.is_chair]
        return chairs[0] if chairs else None

    def get_ranking_member(self) -> Optional[CommitteeMember]:
        """Get the ranking minority member."""
        ranking_members = [
            member for member in self.members if member.is_ranking_member
        ]
        return ranking_members[0] if ranking_members else None

    def get_leadership(self) -> List[CommitteeMember]:
        """Get all leadership members (chair and ranking member)."""
        return [member for member in self.members if member.is_leadership]

    @computed_field
    @property
    def majority_party(self) -> Optional[Party]:
        """Get the majority party on the committee."""
        party_breakdown = self.get_party_breakdown()
        if not party_breakdown:
            return None

        # Remove unknown parties
        known_parties = {k: v for k, v in party_breakdown.items() if k != Party.UNKNOWN}
        if not known_parties:
            return None

        return max(known_parties, key=known_parties.get)

    @computed_field
    @property
    def minority_party(self) -> Optional[Party]:
        """Get the minority party on the committee."""
        party_breakdown = self.get_party_breakdown()
        if len(party_breakdown) < 2:
            return None

        # Remove unknown parties
        known_parties = {k: v for k, v in party_breakdown.items() if k != Party.UNKNOWN}
        if len(known_parties) < 2:
            return None

        sorted_parties = sorted(known_parties.items(), key=lambda x: x[1], reverse=True)
        return sorted_parties[1][0]  # Second largest party

    def get_activities_by_type(self, activity_type: str) -> List[CommitteeActivity]:
        """Get activities of a specific type."""
        activity_type_lower = activity_type.lower()
        return [
            activity
            for activity in self.activities
            if activity_type_lower in activity.activity_type.lower()
        ]

    def get_hearings(self) -> List[CommitteeActivity]:
        """Get all hearings conducted by the committee."""
        return [activity for activity in self.activities if activity.is_hearing]

    def get_markups(self) -> List[CommitteeActivity]:
        """Get all markup sessions conducted by the committee."""
        return [activity for activity in self.activities if activity.is_markup]

    @computed_field
    @property
    def activity_count(self) -> int:
        """Get total number of activities."""
        return len(self.activities)

    @computed_field
    @property
    def hearing_count(self) -> int:
        """Get total number of hearings."""
        return len(self.get_hearings())

    @computed_field
    @property
    def bills_considered_count(self) -> int:
        """Get number of bills considered."""
        return len(self.bills_considered)

    @computed_field
    @property
    def bills_reported_count(self) -> int:
        """Get number of bills reported."""
        return len(self.bills_reported)

    @computed_field
    @property
    def productivity_score(self) -> float:
        """Calculate committee productivity score based on activities and bills."""
        # Simple scoring: activities + bills considered + (2 * bills reported)
        score = (
            self.activity_count
            + self.bills_considered_count
            + (2 * self.bills_reported_count)
        )
        return float(score)

    def get_member_by_bioguide(self, bioguide_id: str) -> Optional[CommitteeMember]:
        """Get a specific member by bioguide ID."""
        for member in self.members:
            if member.bioguide_id == bioguide_id:
                return member
        return None

    def has_member(self, bioguide_id: str) -> bool:
        """Check if a member serves on this committee."""
        return self.get_member_by_bioguide(bioguide_id) is not None

    def get_bill_titles(self) -> List[str]:
        """Get titles of bills considered by the committee."""
        titles = []
        for bill in self.bills_considered + self.bills_reported:
            if isinstance(bill, dict) and "title" in bill:
                titles.append(bill["title"])
        return titles

    @computed_field
    @property
    def partisan_balance(self) -> float:
        """Calculate partisan balance (0.5 = perfectly balanced, closer to 0 or 1 = imbalanced)."""
        party_breakdown = self.get_party_breakdown()
        major_parties = [Party.DEMOCRATIC, Party.REPUBLICAN]

        major_party_counts = [party_breakdown.get(party, 0) for party in major_parties]

        total_major_party_members = sum(major_party_counts)
        if total_major_party_members == 0:
            return 0.5  # No major party members

        dem_ratio = major_party_counts[0] / total_major_party_members
        # Return distance from 0.5 (perfect balance)
        return abs(dem_ratio - 0.5)

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """Dump model to JSON-safe dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")

    # Enhanced analytics methods for new models

    def get_members_by_role(self, role: CommitteeRole) -> List[CommitteeMember]:
        """Get committee members by specific role."""
        return [member for member in self.members if member.role == role]

    def get_members_sorted_by_role(self) -> List[CommitteeMember]:
        """Get committee members sorted by role priority."""
        return sorted(self.members, key=lambda m: m.role_priority)

    def get_active_members(self) -> List[CommitteeMember]:
        """Get currently active committee members."""
        return [member for member in self.members if member.is_active]

    def get_member_tenure_stats(self) -> Dict[str, float]:
        """Get statistics about member tenure on committee."""
        tenures = [m.tenure_years for m in self.members if m.tenure_years is not None]
        if not tenures:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "median": 0.0}

        tenures.sort()
        n = len(tenures)
        return {
            "min": min(tenures),
            "max": max(tenures),
            "avg": sum(tenures) / n,
            "median": (
                tenures[n // 2]
                if n % 2 == 1
                else (tenures[n // 2 - 1] + tenures[n // 2]) / 2
            ),
        }

    def get_meetings_by_type(self, meeting_type: str) -> List[CommitteeMeeting]:
        """Get meetings of a specific type."""
        meeting_type_lower = meeting_type.lower()
        return [
            meeting
            for meeting in self.meetings
            if meeting_type_lower in meeting.meeting_type.lower()
        ]

    def get_recent_meetings(self, limit: int = 10) -> List[CommitteeMeeting]:
        """Get most recent meetings."""
        # Sort by date if available, otherwise by creation time
        sorted_meetings = sorted(
            self.meetings,
            key=lambda m: m.date or m.created_at.isoformat(),
            reverse=True,
        )
        return sorted_meetings[:limit]

    def get_bill_actions_by_type(self, action_type: str) -> List[BillCommitteeAction]:
        """Get bill actions of a specific type."""
        action_type_lower = action_type.lower()
        return [
            action
            for action in self.bill_actions
            if action_type_lower in action.action_type.lower()
        ]

    def get_referred_bills(self) -> List[BillCommitteeAction]:
        """Get bills referred to this committee."""
        return [action for action in self.bill_actions if action.is_referred]

    def get_reported_bills(self) -> List[BillCommitteeAction]:
        """Get bills reported by this committee."""
        return [action for action in self.bill_actions if action.is_reported]

    def get_bills_in_markup(self) -> List[BillCommitteeAction]:
        """Get bills currently in markup."""
        return [action for action in self.bill_actions if action.is_markup_action]

    @computed_field
    @property
    def meetings_count(self) -> int:
        """Get total number of meetings."""
        return len(self.meetings)

    @computed_field
    @property
    def hearings_count_detailed(self) -> int:
        """Get number of hearings from detailed meetings."""
        return len([m for m in self.meetings if m.is_hearing])

    @computed_field
    @property
    def markups_count_detailed(self) -> int:
        """Get number of markups from detailed meetings."""
        return len([m for m in self.meetings if m.is_markup])

    @computed_field
    @property
    def bill_actions_count(self) -> int:
        """Get total number of bill actions."""
        return len(self.bill_actions)

    @computed_field
    @property
    def referred_bills_count(self) -> int:
        """Get number of bills referred to committee."""
        return len(self.get_referred_bills())

    @computed_field
    @property
    def reported_bills_count(self) -> int:
        """Get number of bills reported by committee."""
        return len(self.get_reported_bills())

    @computed_field
    @property
    def bills_in_markup_count(self) -> int:
        """Get number of bills currently in markup."""
        return len(self.get_bills_in_markup())

    @computed_field
    @property
    def enhanced_productivity_score(self) -> float:
        """Calculate enhanced productivity score including new tracking."""
        # Enhanced scoring: meetings + bill actions + (2 * reported bills) + activities
        score = (
            self.meetings_count
            + self.bill_actions_count
            + (2 * self.reported_bills_count)
            + self.activity_count  # Legacy activities
        )
        return float(score)

    @computed_field
    @property
    def committee_efficiency(self) -> float:
        """Calculate efficiency as reported bills / referred bills ratio."""
        referred_count = self.referred_bills_count
        if referred_count == 0:
            return 0.0
        return self.reported_bills_count / referred_count

    @computed_field
    @property
    def average_member_tenure(self) -> float:
        """Calculate average member tenure on committee."""
        tenure_stats = self.get_member_tenure_stats()
        return tenure_stats.get("avg", 0.0)

    def get_committee_analytics(self) -> Dict[str, Any]:
        """Get comprehensive committee analytics."""
        return {
            "membership": {
                "total_members": self.member_count,
                "active_members": len(self.get_active_members()),
                "party_breakdown": self.get_party_breakdown(),
                "majority_party": self.majority_party,
                "minority_party": self.minority_party,
                "partisan_balance": self.partisan_balance,
                "average_tenure": self.average_member_tenure,
                "tenure_stats": self.get_member_tenure_stats(),
            },
            "activity": {
                "total_meetings": self.meetings_count,
                "hearings": self.hearings_count_detailed,
                "markups": self.markups_count_detailed,
                "legacy_activities": self.activity_count,
            },
            "legislation": {
                "bills_referred": self.referred_bills_count,
                "bills_reported": self.reported_bills_count,
                "bills_in_markup": self.bills_in_markup_count,
                "total_bill_actions": self.bill_actions_count,
                "efficiency_ratio": self.committee_efficiency,
            },
            "productivity": {
                "legacy_score": self.productivity_score,
                "enhanced_score": self.enhanced_productivity_score,
            },
        }
