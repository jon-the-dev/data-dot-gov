"""
Vote data models for Congressional roll call votes.

Provides comprehensive Pydantic v2 models for vote data including
party breakdowns, member positions, and computed voting analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .enums import Chamber, Party, VotePosition


class VoteBreakdown(BaseModel):
    """Party breakdown for a vote."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    party: Party = Field(description="Political party")
    yea: int = Field(default=0, ge=0, description="Yea votes")
    nay: int = Field(default=0, ge=0, description="Nay votes")
    present: int = Field(default=0, ge=0, description="Present votes")
    not_voting: int = Field(default=0, ge=0, description="Not voting")

    @field_validator("party", mode="before")
    @classmethod
    def normalize_party(cls, v: Any) -> Party:
        """Normalize party input."""
        return Party.normalize(v)

    @computed_field
    @property
    def total_votes(self) -> int:
        """Total votes cast by this party."""
        return self.yea + self.nay + self.present + self.not_voting

    @computed_field
    @property
    def voting_members(self) -> int:
        """Members who cast yea/nay votes."""
        return self.yea + self.nay

    @computed_field
    @property
    def yea_percentage(self) -> float:
        """Percentage of voting members who voted yea."""
        if self.voting_members == 0:
            return 0.0
        return (self.yea / self.voting_members) * 100

    @computed_field
    @property
    def party_unity_score(self) -> float:
        """Party unity score (percentage voting with majority)."""
        if self.voting_members == 0:
            return 0.0

        majority_position = "yea" if self.yea > self.nay else "nay"
        majority_votes = self.yea if majority_position == "yea" else self.nay
        return (majority_votes / self.voting_members) * 100

    @computed_field
    @property
    def majority_position(self) -> VotePosition:
        """The majority position for this party."""
        if self.yea > self.nay:
            return VotePosition.YEA
        elif self.nay > self.yea:
            return VotePosition.NAY
        else:
            return VotePosition.PRESENT  # Tie or no clear majority


class MemberVote(BaseModel):
    """Individual member's vote on a roll call."""

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
    vote_position: VotePosition = Field(description="How the member voted")
    district: Optional[int] = Field(
        None, ge=0, description="District number (House only)"
    )

    @field_validator("party", mode="before")
    @classmethod
    def normalize_party(cls, v: Any) -> Party:
        """Normalize party input."""
        return Party.normalize(v)

    @field_validator("vote_position", mode="before")
    @classmethod
    def normalize_vote_position(cls, v: Any) -> VotePosition:
        """Normalize vote position input."""
        return VotePosition.normalize(v)

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted display name."""
        party_display = f" ({self.party})" if self.party != Party.UNKNOWN else ""
        state_display = f"-{self.state}" if self.state else ""
        district_display = f"-{self.district}" if self.district is not None else ""

        return f"{self.name}{party_display}{state_display}{district_display}"

    def voted_with_party_majority(self, party_breakdown: VoteBreakdown) -> bool:
        """Check if member voted with their party's majority."""
        if party_breakdown.party != self.party:
            return False
        return self.vote_position == party_breakdown.majority_position


class Vote(BaseModel):
    """Model for Congressional roll call vote data."""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for API flexibility
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

    # Required identification fields
    congress: int = Field(ge=1, le=200, description="Congress number")
    chamber: Chamber = Field(description="Chamber where vote occurred")
    session: int = Field(ge=1, le=3, description="Session number")
    roll_call: int = Field(ge=1, description="Roll call number")

    # Vote details
    question: Optional[str] = Field(None, description="Question being voted on")
    description: Optional[str] = Field(None, description="Vote description")
    date: Optional[str] = Field(None, description="Date of vote")
    result: Optional[str] = Field(None, description="Vote result")

    # Related legislation
    bill: Optional[Dict[str, Any]] = Field(None, description="Associated bill")
    amendment: Optional[Dict[str, Any]] = Field(
        None, description="Associated amendment"
    )

    # Vote totals
    yea_count: int = Field(default=0, ge=0, description="Total yea votes")
    nay_count: int = Field(default=0, ge=0, description="Total nay votes")
    present_count: int = Field(default=0, ge=0, description="Total present votes")
    not_voting_count: int = Field(default=0, ge=0, description="Total not voting")

    # Party breakdown
    party_breakdown: List[VoteBreakdown] = Field(
        default_factory=list, description="Vote breakdown by party"
    )

    # Individual member votes
    member_votes: List[MemberVote] = Field(
        default_factory=list, description="Individual member votes"
    )

    # Metadata
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

    @computed_field
    @property
    def vote_id(self) -> str:
        """Unique identifier for this vote."""
        return f"{self.congress}_{self.chamber.value}_{self.session}_{self.roll_call}"

    @computed_field
    @property
    def display_name(self) -> str:
        """Get formatted vote name."""
        return f"{self.chamber.value.title()} Roll Call {self.roll_call} ({self.congress}-{self.session})"

    @computed_field
    @property
    def total_votes(self) -> int:
        """Get total number of votes cast."""
        return (
            self.yea_count + self.nay_count + self.present_count + self.not_voting_count
        )

    @computed_field
    @property
    def voting_members(self) -> int:
        """Get number of members who cast yea/nay votes."""
        return self.yea_count + self.nay_count

    @computed_field
    @property
    def passed(self) -> bool:
        """Check if vote passed based on result or simple majority."""
        if self.result:
            result_lower = self.result.lower()
            # Check for explicit pass/fail keywords
            pass_keywords = ["passed", "agreed", "confirmed", "adopted"]
            fail_keywords = ["failed", "rejected", "defeated"]

            if any(word in result_lower for word in pass_keywords):
                return True
            elif any(word in result_lower for word in fail_keywords):
                return False

        # Fall back to simple majority
        return self.yea_count > self.nay_count

    @computed_field
    @property
    def margin_of_victory(self) -> int:
        """Get margin of victory (positive if passed, negative if failed)."""
        return self.yea_count - self.nay_count

    @computed_field
    @property
    def participation_rate(self) -> float:
        """Calculate participation rate (percentage who voted yea/nay)."""
        if self.total_votes == 0:
            return 0.0
        return (self.voting_members / self.total_votes) * 100

    def get_party_breakdown_dict(self) -> Dict[Party, VoteBreakdown]:
        """Get party breakdown as a dictionary."""
        return {breakdown.party: breakdown for breakdown in self.party_breakdown}

    def get_party_unity_scores(self) -> Dict[Party, float]:
        """Calculate party unity scores."""
        return {
            breakdown.party: breakdown.party_unity_score
            for breakdown in self.party_breakdown
            if breakdown.party != Party.UNKNOWN
        }

    @computed_field
    @property
    def is_party_line_vote(self) -> bool:
        """Check if this was a party-line vote (>90% unity for major parties)."""
        unity_scores = self.get_party_unity_scores()
        major_parties = [Party.DEMOCRATIC, Party.REPUBLICAN]
        major_party_scores = [
            score for party, score in unity_scores.items() if party in major_parties
        ]

        if len(major_party_scores) < 2:
            return False

        return all(score >= 90.0 for score in major_party_scores)

    @computed_field
    @property
    def is_bipartisan_vote(self) -> bool:
        """Check if vote had bipartisan support (parties agreed on majority position)."""
        party_breakdown = self.get_party_breakdown_dict()
        major_parties = [Party.DEMOCRATIC, Party.REPUBLICAN]

        major_party_positions = [
            party_breakdown[party].majority_position
            for party in major_parties
            if party in party_breakdown
        ]

        if len(major_party_positions) < 2:
            return False

        # All major parties have the same majority position
        return len(set(major_party_positions)) == 1

    def get_cross_party_support(self) -> Dict[str, Any]:
        """Get detailed cross-party support metrics."""
        party_breakdown = self.get_party_breakdown_dict()
        major_parties = [Party.DEMOCRATIC, Party.REPUBLICAN]

        support_metrics = {
            "is_bipartisan": self.is_bipartisan_vote,
            "is_party_line": self.is_party_line_vote,
            "party_positions": {},
            "cross_party_votes": {},
        }

        for party in major_parties:
            if party not in party_breakdown:
                continue

            breakdown = party_breakdown[party]
            support_metrics["party_positions"][party.value] = {
                "majority_position": breakdown.majority_position.value,
                "yea_percentage": breakdown.yea_percentage,
                "unity_score": breakdown.party_unity_score,
            }

        # Calculate cross-party voting (members voting against party majority)
        cross_party_count = 0
        total_major_party_members = 0

        for member_vote in self.member_votes:
            if (
                member_vote.party in major_parties
                and member_vote.party in party_breakdown
            ):
                total_major_party_members += 1
                party_majority = party_breakdown[member_vote.party].majority_position
                if member_vote.vote_position != party_majority:
                    cross_party_count += 1

        if total_major_party_members > 0:
            support_metrics["cross_party_voting_rate"] = (
                cross_party_count / total_major_party_members
            ) * 100
        else:
            support_metrics["cross_party_voting_rate"] = 0.0

        return support_metrics

    def get_members_by_vote(self, position: VotePosition) -> List[MemberVote]:
        """Get all members who voted in a specific position."""
        return [vote for vote in self.member_votes if vote.vote_position == position]

    def get_members_by_party(self, party: Party) -> List[MemberVote]:
        """Get all members of a specific party."""
        return [vote for vote in self.member_votes if vote.party == party]

    def get_swing_voters(self) -> List[MemberVote]:
        """Get members who voted against their party's majority."""
        party_breakdown = self.get_party_breakdown_dict()
        swing_voters = []

        for member_vote in self.member_votes:
            if member_vote.party in party_breakdown:
                party_majority = party_breakdown[member_vote.party].majority_position
                if member_vote.vote_position != party_majority:
                    swing_voters.append(member_vote)

        return swing_voters

    def get_bill_info(self) -> Optional[Dict[str, str]]:
        """Extract bill information if available."""
        if not self.bill:
            return None

        return {
            "congress": str(self.bill.get("congress", "")),
            "type": self.bill.get("type", ""),
            "number": str(self.bill.get("number", "")),
            "title": self.bill.get("title", ""),
        }

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """Dump model to JSON-safe dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
