"""
Lobbying data models for Senate lobbying disclosure data.

Provides comprehensive Pydantic v2 models for lobbying filings,
lobbyists, and issue classifications with computed analytics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .enums import FilingType


class GovernmentPosition(BaseModel):
    """Previous government position held by a lobbyist."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    position: str = Field(min_length=1, description="Position title")
    agency: Optional[str] = Field(None, description="Government agency")
    start_date: Optional[str] = Field(None, description="Start date of position")
    end_date: Optional[str] = Field(None, description="End date of position")
    description: Optional[str] = Field(None, description="Position description")

    @computed_field
    @property
    def is_senior_position(self) -> bool:
        """Check if this was a senior government position."""
        senior_keywords = [
            "secretary",
            "deputy",
            "assistant secretary",
            "director",
            "commissioner",
            "administrator",
            "chief",
            "senior",
        ]
        position_lower = self.position.lower()
        return any(keyword in position_lower for keyword in senior_keywords)


class LobbyingIssue(BaseModel):
    """Issue classification for lobbying activities."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    issue_code: str = Field(min_length=1, description="Standard issue code")
    description: str = Field(min_length=1, description="Issue description")
    specific_issues: List[str] = Field(
        default_factory=list, description="Specific lobbying issues"
    )

    # Analytics fields
    filing_count: int = Field(
        default=0, ge=0, description="Number of filings mentioning this issue"
    )
    total_amount: float = Field(
        default=0.0, ge=0, description="Total lobbying amount for this issue"
    )
    lobbyist_count: int = Field(
        default=0, ge=0, description="Number of lobbyists working on this issue"
    )
    client_count: int = Field(
        default=0, ge=0, description="Number of clients lobbying on this issue"
    )

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted issue name."""
        return f"{self.issue_code}: {self.description}"

    @computed_field
    @property
    def average_amount_per_filing(self) -> float:
        """Calculate average lobbying amount per filing."""
        if self.filing_count == 0:
            return 0.0
        return self.total_amount / self.filing_count

    @computed_field
    @property
    def is_high_activity(self) -> bool:
        """Check if this is a high-activity issue (>= 10 filings)."""
        return self.filing_count >= 10

    @computed_field
    @property
    def is_high_value(self) -> bool:
        """Check if this is a high-value issue (>= $100k)."""
        return self.total_amount >= 100000.0


class Lobbyist(BaseModel):
    """Model for individual lobbyist data."""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for flexibility
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Required identification
    lobbyist_id: str = Field(min_length=1, description="Unique lobbyist identifier")
    name: str = Field(min_length=1, description="Full name")

    # Optional name components
    first_name: Optional[str] = Field(None, alias="firstName", description="First name")
    last_name: Optional[str] = Field(None, alias="lastName", description="Last name")
    suffix: Optional[str] = Field(None, description="Name suffix")

    # Position and status
    covered_position: Optional[str] = Field(
        None, description="Covered executive/legislative position"
    )

    # Contact information
    address: Optional[str] = Field(None, description="Business address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    zip_code: Optional[str] = Field(None, alias="zipCode", description="ZIP code")
    country: Optional[str] = Field(None, description="Country")

    # Professional history
    previous_government_positions: List[GovernmentPosition] = Field(
        default_factory=list, description="Previous government positions"
    )

    # Activity tracking
    total_filings: int = Field(default=0, ge=0, description="Total number of filings")
    active_clients: List[str] = Field(
        default_factory=list, description="Currently active clients"
    )
    issues_lobbied: List[str] = Field(
        default_factory=list, description="Issues lobbied on"
    )
    total_income: float = Field(default=0.0, ge=0, description="Total lobbying income")

    # Dates
    registration_date: Optional[str] = Field(None, description="Date of registration")
    last_activity_date: Optional[str] = Field(None, description="Date of last activity")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    source_api: str = Field(default="senate.gov", description="Source API")

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted lobbyist name."""
        if self.first_name and self.last_name:
            parts = [self.first_name, self.last_name]
            if self.suffix:
                parts.append(self.suffix)
            return " ".join(parts)
        return self.name

    @computed_field
    @property
    def has_government_experience(self) -> bool:
        """Check if lobbyist has previous government positions."""
        return len(self.previous_government_positions) > 0

    @computed_field
    @property
    def has_senior_government_experience(self) -> bool:
        """Check if lobbyist has senior government experience."""
        return any(pos.is_senior_position for pos in self.previous_government_positions)

    @computed_field
    @property
    def client_count(self) -> int:
        """Get number of active clients."""
        return len(set(self.active_clients))  # Use set to avoid duplicates

    @computed_field
    @property
    def issue_count(self) -> int:
        """Get number of unique issues lobbied on."""
        return len(set(self.issues_lobbied))  # Use set to avoid duplicates

    @computed_field
    @property
    def average_income_per_client(self) -> float:
        """Calculate average income per client."""
        if self.client_count == 0:
            return 0.0
        return self.total_income / self.client_count

    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if lobbyist is currently active."""
        return self.total_filings > 0 or len(self.active_clients) > 0

    @computed_field
    @property
    def is_high_volume(self) -> bool:
        """Check if this is a high-volume lobbyist (>= 10 filings)."""
        return self.total_filings >= 10

    def get_government_position_titles(self) -> List[str]:
        """Get list of previous government position titles."""
        return [pos.position for pos in self.previous_government_positions]

    def get_agencies_worked_for(self) -> List[str]:
        """Get list of government agencies previously worked for."""
        agencies = [
            pos.agency for pos in self.previous_government_positions if pos.agency
        ]
        return list(set(agencies))  # Remove duplicates


class LobbyingFiling(BaseModel):
    """Model for lobbying disclosure filing data."""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for API flexibility
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Required identification
    filing_uuid: str = Field(min_length=1, description="Unique filing identifier")
    filing_type: FilingType = Field(description="Type of filing")

    # Filing details
    filing_year: Optional[int] = Field(
        None, ge=1995, le=2050, description="Filing year"
    )
    filing_period: Optional[str] = Field(
        None, description="Filing period (Q1, Q2, etc.)"
    )

    # Client information
    client_name: Optional[str] = Field(None, description="Client name")
    client_general_description: Optional[str] = Field(
        None, description="Client description"
    )
    client_address: Optional[str] = Field(None, description="Client address")
    client_city: Optional[str] = Field(None, description="Client city")
    client_state: Optional[str] = Field(None, description="Client state")
    client_zip: Optional[str] = Field(None, description="Client ZIP code")
    client_country: Optional[str] = Field(None, description="Client country")

    # Registrant information
    registrant_name: Optional[str] = Field(None, description="Registrant name")
    registrant_description: Optional[str] = Field(
        None, description="Registrant description"
    )
    registrant_address: Optional[str] = Field(None, description="Registrant address")
    registrant_city: Optional[str] = Field(None, description="Registrant city")
    registrant_state: Optional[str] = Field(None, description="Registrant state")
    registrant_zip: Optional[str] = Field(None, description="Registrant ZIP code")
    registrant_country: Optional[str] = Field(None, description="Registrant country")

    # Financial information
    income: Optional[float] = Field(None, ge=0, description="Income from lobbying")
    expenses: Optional[float] = Field(None, ge=0, description="Lobbying expenses")

    # Dates
    filed_date: Optional[str] = Field(None, description="Date filed")
    effective_date: Optional[str] = Field(None, description="Effective date")

    # Lobbying details
    issues: List[str] = Field(default_factory=list, description="General issue areas")
    specific_issues: List[str] = Field(
        default_factory=list, description="Specific lobbying issues"
    )
    lobbying_activities: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed lobbying activities"
    )

    # Government contacts
    government_entities: List[str] = Field(
        default_factory=list, description="Government entities contacted"
    )

    # Lobbyists involved
    lobbyists: List[Dict[str, Any]] = Field(
        default_factory=list, description="Lobbyists involved"
    )

    # Termination (for LD-2 filings)
    is_terminated: bool = Field(
        default=False, description="Whether relationship is terminated"
    )
    termination_date: Optional[str] = Field(None, description="Termination date")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    source_api: str = Field(default="senate.gov", description="Source API")

    @field_validator("filing_type", mode="before")
    @classmethod
    def normalize_filing_type(cls, v: Any) -> FilingType:
        """Normalize filing type input."""
        if isinstance(v, FilingType):
            return v
        normalized = FilingType.normalize(v)
        if normalized is None:
            raise ValueError(f"Invalid filing type: {v}")
        return normalized

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted filing name."""
        client = self.client_name or "Unknown Client"
        registrant = self.registrant_name or "Unknown Registrant"
        return f"{self.filing_type.value}: {client} via {registrant}"

    @computed_field
    @property
    def total_amount(self) -> float:
        """Get total financial amount (income plus expenses)."""
        return (self.income or 0) + (self.expenses or 0)

    @computed_field
    @property
    def issue_count(self) -> int:
        """Get number of general issues."""
        return len(self.issues)

    @computed_field
    @property
    def specific_issue_count(self) -> int:
        """Get number of specific issues."""
        return len(self.specific_issues)

    @computed_field
    @property
    def lobbyist_count(self) -> int:
        """Get number of lobbyists involved."""
        return len(self.lobbyists)

    @computed_field
    @property
    def government_entity_count(self) -> int:
        """Get number of government entities contacted."""
        return len(self.government_entities)

    @computed_field
    @property
    def is_registration(self) -> bool:
        """Check if this is a registration filing."""
        return self.filing_type == FilingType.REGISTRATION

    @computed_field
    @property
    def is_quarterly_report(self) -> bool:
        """Check if this is a quarterly report."""
        return self.filing_type == FilingType.QUARTERLY_REPORT

    @computed_field
    @property
    def is_high_value(self) -> bool:
        """Check if this is a high-value filing (>= $50k)."""
        return self.total_amount >= 50000.0

    def get_filing_quarter(self) -> Optional[str]:
        """Get standardized filing quarter."""
        if not self.filing_period:
            return None

        period_map = {
            "Q1": "Q1",
            "Q2": "Q2",
            "Q3": "Q3",
            "Q4": "Q4",
            "FIRST": "Q1",
            "SECOND": "Q2",
            "THIRD": "Q3",
            "FOURTH": "Q4",
            "1": "Q1",
            "2": "Q2",
            "3": "Q3",
            "4": "Q4",
        }

        period_upper = self.filing_period.upper().strip()
        for key, quarter in period_map.items():
            if key in period_upper:
                return quarter

        return self.filing_period

    def get_primary_issues(self, limit: int = 5) -> List[str]:
        """Get primary issues (first N issues)."""
        return self.issues[:limit]

    def get_lobbyist_names(self) -> List[str]:
        """Extract lobbyist names from lobbyist data."""
        names = []
        for lobbyist in self.lobbyists:
            if isinstance(lobbyist, dict):
                name = lobbyist.get("name") or lobbyist.get("fullName")
                if name:
                    names.append(name)
        return names

    def involves_former_officials(self) -> bool:
        """Check if filing involves former government officials."""
        # This would need to cross-reference with lobbyist government experience
        # For now, check if any lobbyists have covered positions
        for lobbyist in self.lobbyists:
            if isinstance(lobbyist, dict) and (
                lobbyist.get("coveredPosition") or lobbyist.get("covered_position")
            ):
                return True
        return False

    @computed_field
    @property
    def activity_intensity(self) -> float:
        """Calculate activity intensity score based on multiple factors."""
        # Score based on: total amount, issues, lobbyists, government entities
        amount_score = min(self.total_amount / 100000, 10)  # Cap at $100k = 10 points
        issue_score = min(self.issue_count * 2, 10)  # Cap at 5 issues = 10 points
        lobbyist_score = min(
            self.lobbyist_count * 3, 15
        )  # Cap at 5 lobbyists = 15 points
        entity_score = min(
            self.government_entity_count * 2, 10
        )  # Cap at 5 entities = 10 points

        return amount_score + issue_score + lobbyist_score + entity_score

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """Dump model to JSON-safe dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
