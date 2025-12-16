"""
Data models for Senate lobbying data structures.

Provides type-safe models for lobbying filings, lobbyists, and related
data from Senate.gov Lobbying Disclosure API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseRecord, validate_required_field


@dataclass
class LobbingFiling(BaseRecord):
    """Model for lobbying disclosure filing data"""

    # Required fields
    filing_uuid: str = field(default="")
    filing_type: str = field(default="")
    filing_year: Optional[int] = None
    filing_period: Optional[str] = None

    # Client information
    client_name: Optional[str] = None
    client_general_description: Optional[str] = None
    client_address: Optional[str] = None
    client_city: Optional[str] = None
    client_state: Optional[str] = None
    client_zip: Optional[str] = None
    client_country: Optional[str] = None

    # Registrant information
    registrant_name: Optional[str] = None
    registrant_description: Optional[str] = None
    registrant_address: Optional[str] = None
    registrant_city: Optional[str] = None
    registrant_state: Optional[str] = None
    registrant_zip: Optional[str] = None
    registrant_country: Optional[str] = None

    # Filing details
    filed_date: Optional[str] = None
    effective_date: Optional[str] = None
    income: Optional[float] = None
    expenses: Optional[float] = None

    # Issues and activities
    issues: List[str] = field(default_factory=list)
    specific_issues: List[str] = field(default_factory=list)
    lobbying_activities: List[Dict[str, Any]] = field(default_factory=list)

    # Government entities contacted
    government_entities: List[str] = field(default_factory=list)

    # Lobbyists
    lobbyists: List[Dict[str, Any]] = field(default_factory=list)

    # Termination info (for LD-2 filings)
    is_terminated: bool = False
    termination_date: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        self.record_type = "lobbying_filing"
        self.identifier = self.filing_uuid

        # Validate required fields
        validate_required_field(self.filing_uuid, "filing_uuid")
        validate_required_field(self.filing_type, "filing_type")

        # Validate filing type
        valid_types = ["LD-1", "LD-2", "RR"]
        if self.filing_type not in valid_types:
            # Don't fail, just normalize
            if "LD-1" in self.filing_type.upper():
                self.filing_type = "LD-1"
            elif "LD-2" in self.filing_type.upper():
                self.filing_type = "LD-2"
            elif "RR" in self.filing_type.upper():
                self.filing_type = "RR"

    @property
    def display_name(self) -> str:
        """Get formatted filing name"""
        client = self.client_name or "Unknown Client"
        registrant = self.registrant_name or "Unknown Registrant"
        return f"{self.filing_type}: {client} via {registrant}"

    @property
    def total_amount(self) -> float:
        """Get total financial amount (income or expenses)"""
        return (self.income or 0) + (self.expenses or 0)

    @property
    def issue_count(self) -> int:
        """Get number of issues"""
        return len(self.issues)

    @property
    def lobbyist_count(self) -> int:
        """Get number of lobbyists"""
        return len(self.lobbyists)

    def get_filing_quarter(self) -> Optional[str]:
        """Get filing quarter from period"""
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
        }

        period_upper = self.filing_period.upper()
        for key, quarter in period_map.items():
            if key in period_upper:
                return quarter

        return self.filing_period

    def is_registration(self) -> bool:
        """Check if this is a registration filing"""
        return self.filing_type in ["LD-1", "RR"]

    def is_quarterly_report(self) -> bool:
        """Check if this is a quarterly report"""
        return self.filing_type == "LD-2"

    def get_primary_issues(self, limit: int = 5) -> List[str]:
        """Get primary issues (first N issues)"""
        return self.issues[:limit]


@dataclass
class Lobbyist(BaseRecord):
    """Model for individual lobbyist data"""

    # Required fields
    lobbyist_id: str = field(default="")
    name: str = field(default="")

    # Optional fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    covered_position: Optional[str] = None

    # Contact information
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

    # Employment history
    previous_government_positions: List[Dict[str, Any]] = field(default_factory=list)

    # Activity tracking
    total_filings: int = 0
    active_clients: List[str] = field(default_factory=list)
    issues_lobbied: List[str] = field(default_factory=list)

    # Date information
    registration_date: Optional[str] = None
    last_activity_date: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        self.record_type = "lobbyist"
        self.identifier = self.lobbyist_id

        # Validate required fields
        validate_required_field(self.lobbyist_id, "lobbyist_id")
        validate_required_field(self.name, "name")

    @property
    def display_name(self) -> str:
        """Get formatted lobbyist name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)

        return " ".join(parts) if parts else self.name

    @property
    def has_government_experience(self) -> bool:
        """Check if lobbyist has previous government positions"""
        return len(self.previous_government_positions) > 0

    @property
    def client_count(self) -> int:
        """Get number of active clients"""
        return len(self.active_clients)

    @property
    def issue_count(self) -> int:
        """Get number of issues lobbied on"""
        return len(set(self.issues_lobbied))

    def get_government_positions(self) -> List[str]:
        """Get list of previous government position titles"""
        positions = []
        for pos in self.previous_government_positions:
            if isinstance(pos, dict) and "position" in pos:
                positions.append(pos["position"])
            elif isinstance(pos, str):
                positions.append(pos)
        return positions

    def is_active(self) -> bool:
        """Check if lobbyist is currently active"""
        return self.total_filings > 0 or len(self.active_clients) > 0


@dataclass
class LobbyingIssue(BaseRecord):
    """Model for lobbying issue data"""

    # Required fields
    issue_code: str = field(default="")
    description: str = field(default="")

    # Optional fields
    category: Optional[str] = None
    subcategory: Optional[str] = None

    # Activity tracking
    filing_count: int = 0
    total_amount: float = 0.0
    lobbyist_count: int = 0
    client_count: int = 0

    # Time tracking
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        self.record_type = "lobbying_issue"
        self.identifier = self.issue_code

        # Validate required fields
        validate_required_field(self.issue_code, "issue_code")
        validate_required_field(self.description, "description")

    @property
    def display_name(self) -> str:
        """Get formatted issue name"""
        return f"{self.issue_code}: {self.description}"

    @property
    def average_amount_per_filing(self) -> float:
        """Get average amount per filing"""
        if self.filing_count == 0:
            return 0.0
        return self.total_amount / self.filing_count

    def is_high_activity(self, filing_threshold: int = 10) -> bool:
        """Check if this is a high-activity issue"""
        return self.filing_count >= filing_threshold

    def is_high_value(self, amount_threshold: float = 100000.0) -> bool:
        """Check if this is a high-value issue"""
        return self.total_amount >= amount_threshold
