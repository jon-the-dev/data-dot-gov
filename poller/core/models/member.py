"""
Member data models for Congressional representatives and senators.

Provides comprehensive Pydantic v2 models for member data including
personal information, terms of service, and computed properties.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .enums import Chamber, MemberType, Party


class MemberDepiction(BaseModel):
    """Visual depiction information for a member."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    attribution: Optional[str] = Field(None, description="Attribution for the image")
    image_url: Optional[str] = Field(
        None, alias="imageUrl", description="URL to member's official photo"
    )


class MemberTerm(BaseModel):
    """A term of service for a congressional member."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    chamber: Chamber = Field(description="Chamber of service")
    congress: int = Field(ge=1, le=200, description="Congress number")
    district: Optional[int] = Field(
        None, ge=0, le=99, description="District number (House only)"
    )
    start_year: int = Field(
        alias="startYear", ge=1789, description="Start year of term"
    )
    end_year: int = Field(alias="endYear", ge=1789, description="End year of term")
    member_type: Optional[MemberType] = Field(
        None, alias="memberType", description="Type of member"
    )
    state_code: str = Field(
        alias="stateCode",
        min_length=2,
        max_length=2,
        description="Two-letter state code",
    )
    state_name: str = Field(
        alias="stateName", min_length=1, description="Full state name"
    )

    @field_validator("chamber", mode="before")
    @classmethod
    def normalize_chamber(cls, v: Any) -> Chamber:
        """Normalize chamber input."""
        return Chamber.normalize(v)

    @field_validator("member_type", mode="before")
    @classmethod
    def normalize_member_type(cls, v: Any) -> Optional[MemberType]:
        """Normalize member type input."""
        return MemberType.normalize(v)

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str) -> str:
        """Validate state code format."""
        return v.upper()

    @computed_field
    @property
    def term_length(self) -> int:
        """Calculate length of term in years."""
        return self.end_year - self.start_year

    @computed_field
    @property
    def is_current_term(self) -> bool:
        """Check if this term is currently active."""
        current_year = datetime.now().year
        return self.start_year <= current_year <= self.end_year


class Member(BaseModel):
    """Model for Congressional member data with comprehensive validation."""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for flexibility with API data
        validate_assignment=True,
        str_strip_whitespace=True,
        populate_by_name=True,  # Allow field aliases
    )

    # Required identification fields
    bioguide_id: str = Field(
        alias="bioguideId", min_length=1, description="Unique bioguide identifier"
    )
    name: str = Field(min_length=1, description="Full name")
    party: Party = Field(description="Political party affiliation")
    state: str = Field(min_length=1, description="State name")
    chamber: Chamber = Field(description="Congressional chamber")

    # Optional name components
    first_name: Optional[str] = Field(None, alias="firstName", description="First name")
    last_name: Optional[str] = Field(None, alias="lastName", description="Last name")
    middle_name: Optional[str] = Field(
        None, alias="middleName", description="Middle name"
    )
    suffix: Optional[str] = Field(None, description="Name suffix (Jr., Sr., etc.)")
    nickname: Optional[str] = Field(None, description="Nickname")

    # District and representation
    district: Optional[int] = Field(
        None, ge=0, le=99, description="District number (House only)"
    )
    party_code: Optional[str] = Field(
        None, alias="partyCode", description="Raw party code from API"
    )

    # Service information
    terms: List[MemberTerm] = Field(
        default_factory=list, description="Terms of service"
    )
    is_current: bool = Field(
        default=True, description="Whether member is currently serving"
    )

    # Visual information
    depiction: Optional[MemberDepiction] = Field(
        None, description="Photo and attribution info"
    )

    # Optional biographical data
    birth_year: Optional[int] = Field(None, ge=1700, le=2100, description="Birth year")
    death_year: Optional[int] = Field(None, ge=1700, le=2100, description="Death year")

    # URLs and external references
    url: Optional[str] = Field(None, description="API URL for this member")
    website: Optional[str] = Field(None, description="Official website")
    social_media: Dict[str, str] = Field(
        default_factory=dict, description="Social media accounts"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Record creation time"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    source_api: str = Field(default="congress.gov", description="Source API")

    @field_validator("party", mode="before")
    @classmethod
    def normalize_party(cls, v: Any) -> Party:
        """Normalize party input to standard enum."""
        return Party.normalize(v)

    @field_validator("chamber", mode="before")
    @classmethod
    def normalize_chamber(cls, v: Any) -> Chamber:
        """Normalize chamber input to standard enum."""
        return Chamber.normalize(v)

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: Optional[int], info) -> Optional[int]:
        """Validate district based on chamber."""
        # District should only be set for House members
        chamber = info.data.get("chamber")
        if chamber == Chamber.HOUSE and v is None:
            # House members should have a district
            pass  # Allow None for now, could be at-large
        elif chamber == Chamber.SENATE and v is not None:
            # Senators should not have a district
            return None
        return v

    @field_validator("death_year")
    @classmethod
    def validate_death_year(cls, v: Optional[int], info) -> Optional[int]:
        """Validate death year is after birth year."""
        if v is not None and "birth_year" in info.data:
            birth_year = info.data["birth_year"]
            if birth_year is not None and v <= birth_year:
                raise ValueError("Death year must be after birth year")
        return v

    @computed_field
    @property
    def full_name(self) -> str:
        """Get formatted full name from components."""
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

    @computed_field
    @property
    def display_name(self) -> str:
        """Get display name with title and party."""
        title_map = {
            Chamber.HOUSE: "Rep.",
            Chamber.SENATE: "Sen.",
        }

        title = title_map.get(self.chamber, "")
        party_display = f" ({self.party.value})" if self.party != Party.UNKNOWN else ""
        state_display = f"-{self.state}" if self.state else ""
        district_display = f"-{self.district}" if self.district is not None else ""

        return f"{title} {self.name}{party_display}{state_display}{district_display}".strip()

    @computed_field
    @property
    def current_term(self) -> Optional[MemberTerm]:
        """Get the current term of service."""
        current_year = datetime.now().year
        for term in self.terms:
            if term.start_year <= current_year <= term.end_year:
                return term
        return None

    @computed_field
    @property
    def total_years_served(self) -> int:
        """Calculate total years of service across all terms."""
        return sum(term.term_length for term in self.terms)

    @computed_field
    @property
    def chambers_served(self) -> List[Chamber]:
        """Get list of chambers where member has served."""
        chambers = {term.chamber for term in self.terms}
        return sorted(chambers, key=lambda x: x.value)

    @computed_field
    @property
    def is_senator(self) -> bool:
        """Check if member is/was a senator."""
        return self.chamber == Chamber.SENATE

    @computed_field
    @property
    def is_representative(self) -> bool:
        """Check if member is/was a representative."""
        return self.chamber == Chamber.HOUSE

    @computed_field
    @property
    def is_alive(self) -> bool:
        """Check if member is still alive."""
        return self.death_year is None

    def get_terms_in_congress(self, congress: int) -> List[MemberTerm]:
        """Get terms served in a specific congress."""
        return [term for term in self.terms if term.congress == congress]

    def served_in_congress(self, congress: int) -> bool:
        """Check if member served in a specific congress."""
        return len(self.get_terms_in_congress(congress)) > 0

    def get_terms_by_chamber(self, chamber: Chamber) -> List[MemberTerm]:
        """Get all terms served in a specific chamber."""
        return [term for term in self.terms if term.chamber == chamber]

    def years_in_chamber(self, chamber: Chamber) -> int:
        """Calculate total years served in a specific chamber."""
        terms = self.get_terms_by_chamber(chamber)
        return sum(term.term_length for term in terms)

    def party_history(self) -> Dict[Party, int]:
        """Get party affiliation history by years served."""
        # This would need to be enhanced with term-specific party data
        # For now, return current party
        return {self.party: self.total_years_served}

    def model_dump_json_safe(self) -> Dict[str, Any]:
        """Dump model to JSON-safe dictionary."""
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")
