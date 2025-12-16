"""
Bill data models for Congressional legislation.

Provides comprehensive Pydantic v2 models for bill data including
sponsors, actions, subjects, and computed properties for analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .enums import BillType, Chamber, Party


class BillSponsor(BaseModel):
    """Sponsor or cosponsor of a bill."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    bioguide_id: str = Field(
        alias="bioguideId", min_length=1, description="Bioguide identifier"
    )
    full_name: str = Field(alias="fullName", min_length=1, description="Full name")
    first_name: Optional[str] = Field(None, alias="firstName", description="First name")
    last_name: Optional[str] = Field(None, alias="lastName", description="Last name")
    party: Party = Field(description="Political party")
    state: str = Field(min_length=1, max_length=2, description="State code")
    district: Optional[int] = Field(None, ge=0, le=99, description="District number")
    url: Optional[str] = Field(None, description="API URL for member")

    # Sponsorship details
    is_original_cosponsor: Optional[bool] = Field(
        None,
        alias="isOriginalCosponsor",
        description="Whether this is an original cosponsor",
    )
    sponsorship_date: Optional[str] = Field(
        None, alias="sponsorshipDate", description="Date of sponsorship"
    )
    is_by_request: Optional[str] = Field(
        None, alias="isByRequest", description="Whether sponsorship is by request"
    )

    @field_validator("party", mode="before")
    @classmethod
    def normalize_party(cls, v: Any) -> Party:
        """Normalize party input."""
        return Party.normalize(v)

    @field_validator("state")
    @classmethod
    def normalize_state(cls, v: str) -> str:
        """Normalize state to uppercase."""
        return v.upper()

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted display name with party and state."""
        party_display = f" ({self.party})" if self.party != Party.UNKNOWN else ""
        state_display = f"-{self.state}" if self.state else ""
        district_display = f"-{self.district}" if self.district is not None else ""

        return f"{self.full_name}{party_display}{state_display}{district_display}"


class BillSubject(BaseModel):
    """Subject or policy area classification for a bill."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    name: str = Field(min_length=1, description="Subject name")
    category: Optional[str] = Field(None, description="Subject category")
    policy_area: Optional[str] = Field(None, description="Policy area classification")


class BillAction(BaseModel):
    """An action taken on a bill during the legislative process."""

    model_config = ConfigDict(
        extra="allow",  # API data varies significantly
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    action_date: Optional[str] = Field(None, description="Date of action")
    text: str = Field(min_length=1, description="Action description")
    action_code: Optional[str] = Field(None, description="Action code")
    committee: Optional[str] = Field(None, description="Committee involved")
    chamber: Optional[Chamber] = Field(
        None, description="Chamber where action occurred"
    )

    @field_validator("chamber", mode="before")
    @classmethod
    def normalize_chamber(cls, v: Any) -> Optional[Chamber]:
        """Normalize chamber input."""
        return Chamber.normalize(v) if v else None


class Bill(BaseModel):
    """Model for Congressional bill data with comprehensive validation."""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for API flexibility
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Required identification fields
    congress: int = Field(ge=1, le=200, description="Congress number")
    bill_type: BillType = Field(alias="type", description="Type of bill")
    number: str = Field(min_length=1, description="Bill number")
    title: str = Field(min_length=1, description="Bill title")

    # Computed identifier
    bill_id: Optional[str] = Field(None, description="Computed bill identifier")

    # Origin information
    origin_chamber: Optional[Chamber] = Field(None, description="Chamber of origin")
    origin_chamber_code: Optional[str] = Field(None, description="Origin chamber code")
    introduced_date: Optional[str] = Field(None, description="Date introduced")

    # Content and description
    summary: Optional[str] = Field(None, description="Bill summary")
    constitutional_authority_statement_text: Optional[str] = Field(
        None, description="Constitutional authority statement"
    )

    # Sponsorship
    sponsors: List[BillSponsor] = Field(
        default_factory=list, description="Bill sponsors"
    )
    cosponsors: List[BillSponsor] = Field(
        default_factory=list, description="Bill cosponsors"
    )

    # Classification
    subjects: List[str] = Field(
        default_factory=list, description="Subject classifications"
    )
    policy_area: Optional[str] = Field(None, description="Primary policy area")

    # Legislative process
    actions: List[BillAction] = Field(
        default_factory=list, description="Legislative actions"
    )
    committees: List[Dict[str, Any]] = Field(
        default_factory=list, description="Committees involved"
    )

    # Status
    is_law: bool = Field(default=False, description="Whether bill became law")
    laws: List[Dict[str, Any]] = Field(
        default_factory=list, description="Public laws if enacted"
    )

    # External references
    url: Optional[str] = Field(None, description="Congress.gov URL")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    fetched_at: Optional[str] = Field(None, description="When data was fetched")
    source_api: str = Field(default="congress.gov", description="Source API")

    @field_validator("bill_type", mode="before")
    @classmethod
    def normalize_bill_type(cls, v: Any) -> BillType:
        """Normalize bill type input."""
        if isinstance(v, BillType):
            return v
        normalized = BillType.normalize(v)
        if normalized is None:
            raise ValueError(f"Invalid bill type: {v}")
        return normalized

    @field_validator("origin_chamber", mode="before")
    @classmethod
    def normalize_origin_chamber(cls, v: Any) -> Optional[Chamber]:
        """Normalize origin chamber input."""
        return Chamber.normalize(v) if v else None

    @field_validator("bill_id", mode="before")
    @classmethod
    def generate_bill_id(cls, v: Optional[str], info) -> str:
        """Generate bill ID from congress, type, and number."""
        if v:
            return v

        congress = info.data.get("congress")
        bill_type = info.data.get("bill_type") or info.data.get("type")
        number = info.data.get("number")

        if congress and bill_type and number:
            # Handle both enum and string bill types
            type_str = (
                bill_type.value if hasattr(bill_type, "value") else str(bill_type)
            )
            return f"{congress}_{type_str.lower()}_{number}"

        return ""

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted bill name."""
        return f"{self.bill_type.value} {self.number}"

    @computed_field
    @property
    def full_display_name(self) -> str:
        """Get full bill name with congress."""
        return f"{self.congress}th Congress {self.bill_type.value} {self.number}"

    @computed_field
    @property
    def sponsor_count(self) -> int:
        """Get number of sponsors."""
        return len(self.sponsors)

    @computed_field
    @property
    def cosponsor_count(self) -> int:
        """Get number of cosponsors."""
        return len(self.cosponsors)

    @computed_field
    @property
    def total_sponsors(self) -> int:
        """Get total number of sponsors and cosponsors."""
        return self.sponsor_count + self.cosponsor_count

    @computed_field
    @property
    def chamber_of_origin(self) -> Chamber:
        """Get chamber of origin based on bill type."""
        if self.origin_chamber:
            return self.origin_chamber
        return self.bill_type.chamber_of_origin

    def get_sponsors_by_party(self) -> Dict[Party, int]:
        """Get sponsor count by party."""
        party_counts = {}

        for sponsor in self.sponsors + self.cosponsors:
            party = sponsor.party
            party_counts[party] = party_counts.get(party, 0) + 1

        return party_counts

    def get_sponsors_by_state(self) -> Dict[str, int]:
        """Get sponsor count by state."""
        state_counts = {}

        for sponsor in self.sponsors + self.cosponsors:
            state = sponsor.state
            state_counts[state] = state_counts.get(state, 0) + 1

        return state_counts

    def get_primary_sponsor(self) -> Optional[BillSponsor]:
        """Get the primary sponsor (first sponsor)."""
        return self.sponsors[0] if self.sponsors else None

    @computed_field
    @property
    def is_bipartisan(self) -> bool:
        """Check if bill has bipartisan support."""
        party_counts = self.get_sponsors_by_party()
        # Remove unknown parties for this calculation
        known_parties = {k: v for k, v in party_counts.items() if k != Party.UNKNOWN}
        return len(known_parties) > 1

    @computed_field
    @property
    def bipartisan_score(self) -> float:
        """Calculate bipartisan score (0-1) based on party distribution."""
        party_counts = self.get_sponsors_by_party()
        known_parties = {k: v for k, v in party_counts.items() if k != Party.UNKNOWN}

        if len(known_parties) < 2:
            return 0.0

        total_sponsors = sum(known_parties.values())
        if total_sponsors == 0:
            return 0.0

        # Calculate entropy-like measure of party distribution
        party_ratios = [count / total_sponsors for count in known_parties.values()]
        # Bipartisan score is higher when parties are more evenly distributed
        variance = sum(
            (ratio - (1 / len(known_parties))) ** 2 for ratio in party_ratios
        )
        max_variance = (len(known_parties) - 1) / len(known_parties) ** 2
        return 1.0 - (variance / max_variance) if max_variance > 0 else 0.0

    def get_committee_names(self) -> List[str]:
        """Extract committee names from committee data."""
        names = []
        for committee in self.committees:
            if isinstance(committee, dict) and "name" in committee:
                names.append(committee["name"])
            elif isinstance(committee, str):
                names.append(committee)
        return names

    def has_subject(self, subject: str) -> bool:
        """Check if bill has a specific subject."""
        subject_lower = subject.lower()
        return any(subject_lower in s.lower() for s in self.subjects)

    def get_latest_action(self) -> Optional[BillAction]:
        """Get the most recent action."""
        if not self.actions:
            return None

        # Sort by date if available, otherwise take last
        dated_actions = [a for a in self.actions if a.action_date]
        if dated_actions:
            return max(dated_actions, key=lambda x: x.action_date)
        return self.actions[-1]

    @computed_field
    @property
    def days_since_introduction(self) -> Optional[int]:
        """Calculate days since bill was introduced."""
        if not self.introduced_date:
            return None

        try:
            intro_date = datetime.fromisoformat(
                self.introduced_date.replace("Z", "+00:00")
            )
            return (datetime.now() - intro_date).days
        except (ValueError, AttributeError):
            return None

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """Dump model to JSON-safe dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
