"""
Data models for Congressional data structures.

Provides type-safe models for bills, votes, members, and related
Congressional data from Congress.gov API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import (
    BaseRecord,
    normalize_chamber,
    normalize_party_code,
    validate_congress_number,
    validate_required_field,
)


@dataclass
class Member(BaseRecord):
    """Model for Congressional member data"""

    # Required fields
    bioguide_id: str = field(default="")
    name: str = field(default="")
    party: str = field(default="")
    state: str = field(default="")
    chamber: str = field(default="")

    # Optional fields
    district: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    suffix: Optional[str] = None
    nickname: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    served_start: Optional[str] = None
    served_end: Optional[str] = None
    is_current: bool = True

    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        self.record_type = "member"
        self.identifier = self.bioguide_id

        # Validate required fields
        validate_required_field(self.bioguide_id, "bioguide_id")
        validate_required_field(self.name, "name")

        # Normalize party and chamber
        self.party = normalize_party_code(self.party) or "Unknown"
        self.chamber = normalize_chamber(self.chamber) or "unknown"

        # Validate chamber
        if self.chamber not in ["house", "senate", "unknown"]:
            self.chamber = "unknown"

    @property
    def full_name(self) -> str:
        """Get formatted full name"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        if self.last_name:
            parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)

        return " ".join(parts) if parts else self.name

    @property
    def display_name(self) -> str:
        """Get display name with title and party"""
        title_part = f"{self.title} " if self.title else ""
        party_part = f" ({self.party})" if self.party != "Unknown" else ""
        state_part = f"-{self.state}" if self.state else ""

        return f"{title_part}{self.name}{party_part}{state_part}"

    def is_in_congress(self, congress: int) -> bool:
        """Check if member served in a specific congress"""
        # This would need more sophisticated logic based on service dates
        # For now, just return is_current for recent congresses
        return self.is_current and congress >= 115  # Approximate


@dataclass
class Bill(BaseRecord):
    """Model for Congressional bill data"""

    # Required fields
    congress: int = 0
    bill_type: str = field(default="")
    number: str = field(default="")
    title: str = field(default="")

    # Optional fields
    introduced_date: Optional[str] = None
    origin_chamber: Optional[str] = None
    origin_chamber_code: Optional[str] = None
    url: Optional[str] = None
    constitutional_authority_statement_text: Optional[str] = None
    sponsors: List[Dict[str, Any]] = field(default_factory=list)
    cosponsors: List[Dict[str, Any]] = field(default_factory=list)
    subjects: List[str] = field(default_factory=list)
    policy_area: Optional[str] = None
    committees: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    laws: List[Dict[str, Any]] = field(default_factory=list)
    is_law: bool = False

    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        self.record_type = "bill"
        self.identifier = f"{self.congress}_{self.bill_type}_{self.number}"

        # Validate required fields
        self.congress = validate_congress_number(self.congress)
        validate_required_field(self.bill_type, "bill_type")
        validate_required_field(self.number, "number")

        # Normalize bill type
        self.bill_type = self.bill_type.upper()

        # Validate bill type
        valid_types = [
            "HR",
            "S",
            "HJRES",
            "SJRES",
            "HCONRES",
            "SCONRES",
            "HRES",
            "SRES",
        ]
        if self.bill_type not in valid_types:
            # Don't fail, just log the unusual type
            pass

        # Normalize origin chamber
        if self.origin_chamber:
            self.origin_chamber = normalize_chamber(self.origin_chamber)

    @property
    def display_name(self) -> str:
        """Get formatted bill name"""
        return f"{self.bill_type} {self.number}"

    @property
    def full_display_name(self) -> str:
        """Get full bill name with congress"""
        return f"{self.congress}th Congress {self.bill_type} {self.number}"

    @property
    def sponsor_count(self) -> int:
        """Get number of sponsors"""
        return len(self.sponsors)

    @property
    def cosponsor_count(self) -> int:
        """Get number of cosponsors"""
        return len(self.cosponsors)

    @property
    def total_sponsors(self) -> int:
        """Get total number of sponsors and cosponsors"""
        return self.sponsor_count + self.cosponsor_count

    def get_sponsors_by_party(self) -> Dict[str, int]:
        """Get sponsor count by party"""
        party_counts = {}

        for sponsor in self.sponsors + self.cosponsors:
            party = normalize_party_code(sponsor.get("party")) or "Unknown"
            party_counts[party] = party_counts.get(party, 0) + 1

        return party_counts

    def is_bipartisan(self) -> bool:
        """Check if bill has bipartisan support"""
        party_counts = self.get_sponsors_by_party()
        # Remove unknown parties for this calculation
        known_parties = {k: v for k, v in party_counts.items() if k != "Unknown"}
        return len(known_parties) > 1


@dataclass
class Vote(BaseRecord):
    """Model for Congressional vote data"""

    # Required fields
    congress: int = 0
    chamber: str = field(default="")
    session: int = 1
    roll_call: int = 0

    # Optional fields
    question: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    result: Optional[str] = None
    bill: Optional[Dict[str, Any]] = None
    amendment: Optional[Dict[str, Any]] = None

    # Vote totals
    yea_count: int = 0
    nay_count: int = 0
    present_count: int = 0
    not_voting_count: int = 0

    # Party breakdown
    party_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Individual member votes
    member_votes: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate and normalize fields after initialization"""
        self.record_type = "vote"
        self.identifier = (
            f"{self.congress}_{self.chamber}_{self.session}_{self.roll_call}"
        )

        # Validate required fields
        self.congress = validate_congress_number(self.congress)
        self.chamber = normalize_chamber(self.chamber) or "unknown"

        if self.chamber not in ["house", "senate", "unknown"]:
            self.chamber = "unknown"

    @property
    def display_name(self) -> str:
        """Get formatted vote name"""
        return f"{self.chamber.title()} Roll Call {self.roll_call}"

    @property
    def total_votes(self) -> int:
        """Get total number of votes cast"""
        return (
            self.yea_count + self.nay_count + self.present_count + self.not_voting_count
        )

    @property
    def passed(self) -> bool:
        """Check if vote passed (simple heuristic)"""
        if self.result:
            result_lower = self.result.lower()
            return any(
                word in result_lower for word in ["passed", "agreed", "confirmed"]
            )
        return self.yea_count > self.nay_count

    def get_party_unity_scores(self) -> Dict[str, float]:
        """Calculate party unity scores (percentage voting with majority of party)"""
        unity_scores = {}

        for party, votes in self.party_breakdown.items():
            if party == "Unknown":
                continue

            total_voting = votes.get("yea", 0) + votes.get("nay", 0)
            if total_voting == 0:
                continue

            majority_position = (
                "yea" if votes.get("yea", 0) > votes.get("nay", 0) else "nay"
            )
            majority_votes = votes.get(majority_position, 0)

            unity_score = (majority_votes / total_voting) * 100
            unity_scores[party] = unity_score

        return unity_scores

    def is_party_line_vote(self, threshold: float = 90.0) -> bool:
        """Check if this was a party-line vote"""
        unity_scores = self.get_party_unity_scores()
        return all(score >= threshold for score in unity_scores.values())

    def get_bipartisan_support(self) -> Dict[str, Any]:
        """Get bipartisan support metrics"""
        party_positions = {}

        for party, votes in self.party_breakdown.items():
            if party == "Unknown":
                continue

            total_voting = votes.get("yea", 0) + votes.get("nay", 0)
            if total_voting == 0:
                continue

            yea_pct = (votes.get("yea", 0) / total_voting) * 100
            party_positions[party] = {
                "yea_percentage": yea_pct,
                "nay_percentage": 100 - yea_pct,
                "majority_position": "yea" if yea_pct > 50 else "nay",
            }

        # Check if parties agree
        majority_positions = [
            pos["majority_position"] for pos in party_positions.values()
        ]
        is_bipartisan = (
            len(set(majority_positions)) == 1 and len(majority_positions) > 1
        )

        return {
            "is_bipartisan": is_bipartisan,
            "party_positions": party_positions,
            "cross_party_support": min(
                [pos["yea_percentage"] for pos in party_positions.values()] + [100]
            ),
        }
