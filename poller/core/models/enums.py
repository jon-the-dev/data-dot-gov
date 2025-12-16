"""
Enums for categorical data in the Congressional Transparency Platform.

Defines standard enums for party affiliation, chambers, vote positions,
bill types, and other categorical fields with proper validation.
"""

from enum import Enum
from typing import Optional


class Party(str, Enum):
    """Political party affiliation."""

    DEMOCRATIC = "D"
    REPUBLICAN = "R"
    INDEPENDENT = "I"
    LIBERTARIAN = "L"
    GREEN = "G"
    UNKNOWN = "Unknown"

    @classmethod
    def normalize(cls, party_input: Optional[str]) -> "Party":
        """
        Normalize party input to standard enum value.

        Args:
            party_input: Raw party string from API

        Returns:
            Normalized Party enum value
        """
        if not party_input:
            return cls.UNKNOWN

        party_upper = party_input.upper().strip()

        # Map common variations
        party_map = {
            "DEMOCRATIC": cls.DEMOCRATIC,
            "DEMOCRAT": cls.DEMOCRATIC,
            "DEM": cls.DEMOCRATIC,
            "D": cls.DEMOCRATIC,
            "REPUBLICAN": cls.REPUBLICAN,
            "REP": cls.REPUBLICAN,
            "R": cls.REPUBLICAN,
            "INDEPENDENT": cls.INDEPENDENT,
            "IND": cls.INDEPENDENT,
            "I": cls.INDEPENDENT,
            "LIBERTARIAN": cls.LIBERTARIAN,
            "LIB": cls.LIBERTARIAN,
            "L": cls.LIBERTARIAN,
            "GREEN": cls.GREEN,
            "G": cls.GREEN,
        }

        return party_map.get(party_upper, cls.UNKNOWN)


class Chamber(str, Enum):
    """Congressional chamber."""

    HOUSE = "house"
    SENATE = "senate"
    JOINT = "joint"
    UNKNOWN = "unknown"

    @classmethod
    def normalize(cls, chamber_input: Optional[str]) -> "Chamber":
        """
        Normalize chamber input to standard enum value.

        Args:
            chamber_input: Raw chamber string from API

        Returns:
            Normalized Chamber enum value
        """
        if not chamber_input:
            return cls.UNKNOWN

        chamber_lower = chamber_input.lower().strip()

        if chamber_lower in ["house", "h", "house of representatives"]:
            return cls.HOUSE
        elif chamber_lower in ["senate", "s"]:
            return cls.SENATE
        elif chamber_lower in ["joint", "j"]:
            return cls.JOINT

        return cls.UNKNOWN


class VotePosition(str, Enum):
    """Vote position by a member."""

    YEA = "Yea"
    NAY = "Nay"
    PRESENT = "Present"
    NOT_VOTING = "Not Voting"
    PAIRED = "Paired"
    UNKNOWN = "Unknown"

    @classmethod
    def normalize(cls, vote_input: Optional[str]) -> "VotePosition":
        """
        Normalize vote input to standard enum value.

        Args:
            vote_input: Raw vote string from API

        Returns:
            Normalized VotePosition enum value
        """
        if not vote_input:
            return cls.UNKNOWN

        vote_lower = vote_input.lower().strip()

        vote_map = {
            "yea": cls.YEA,
            "yes": cls.YEA,
            "aye": cls.YEA,
            "nay": cls.NAY,
            "no": cls.NAY,
            "present": cls.PRESENT,
            "not voting": cls.NOT_VOTING,
            "not_voting": cls.NOT_VOTING,
            "paired": cls.PAIRED,
        }

        return vote_map.get(vote_lower, cls.UNKNOWN)


class BillType(str, Enum):
    """Congressional bill types."""

    HOUSE_BILL = "HR"  # House Bill
    SENATE_BILL = "S"  # Senate Bill
    HOUSE_JOINT_RESOLUTION = "HJRES"  # House Joint Resolution
    SENATE_JOINT_RESOLUTION = "SJRES"  # Senate Joint Resolution
    HOUSE_CONCURRENT_RESOLUTION = "HCONRES"  # House Concurrent Resolution
    SENATE_CONCURRENT_RESOLUTION = "SCONRES"  # Senate Concurrent Resolution
    HOUSE_RESOLUTION = "HRES"  # House Simple Resolution
    SENATE_RESOLUTION = "SRES"  # Senate Simple Resolution

    @classmethod
    def normalize(cls, bill_type_input: Optional[str]) -> Optional["BillType"]:
        """
        Normalize bill type input to standard enum value.

        Args:
            bill_type_input: Raw bill type string from API

        Returns:
            Normalized BillType enum value or None if invalid
        """
        if not bill_type_input:
            return None

        bill_type_upper = bill_type_input.upper().strip()

        # Direct mapping
        for bill_type in cls:
            if bill_type.value == bill_type_upper:
                return bill_type

        return None

    @property
    def chamber_of_origin(self) -> Chamber:
        """Get the chamber where this bill type originates."""
        if self.value.startswith("H"):
            return Chamber.HOUSE
        elif self.value.startswith("S"):
            return Chamber.SENATE
        else:
            return Chamber.UNKNOWN

    @property
    def is_resolution(self) -> bool:
        """Check if this is a resolution (not a bill)."""
        return "RES" in self.value

    @property
    def is_joint_resolution(self) -> bool:
        """Check if this is a joint resolution."""
        return "JRES" in self.value


class FilingType(str, Enum):
    """Lobbying filing types."""

    REGISTRATION = "LD-1"  # Lobbying Registration
    QUARTERLY_REPORT = "LD-2"  # Quarterly Lobbying Report
    REVOLVING_DOOR = "RR"  # Revolving Door Report

    @classmethod
    def normalize(cls, filing_type_input: Optional[str]) -> Optional["FilingType"]:
        """
        Normalize filing type input to standard enum value.

        Args:
            filing_type_input: Raw filing type string from API

        Returns:
            Normalized FilingType enum value or None if invalid
        """
        if not filing_type_input:
            return None

        filing_type_upper = filing_type_input.upper().strip()

        # Handle variations
        if "LD-1" in filing_type_upper or "LD1" in filing_type_upper:
            return cls.REGISTRATION
        elif "LD-2" in filing_type_upper or "LD2" in filing_type_upper:
            return cls.QUARTERLY_REPORT
        elif "RR" in filing_type_upper:
            return cls.REVOLVING_DOOR

        return None


class MemberType(str, Enum):
    """Type of congressional member."""

    REPRESENTATIVE = "Representative"
    SENATOR = "Senator"
    DELEGATE = "Delegate"
    RESIDENT_COMMISSIONER = "Resident Commissioner"

    @classmethod
    def normalize(cls, member_type_input: Optional[str]) -> Optional["MemberType"]:
        """
        Normalize member type input to standard enum value.

        Args:
            member_type_input: Raw member type string from API

        Returns:
            Normalized MemberType enum value or None if invalid
        """
        if not member_type_input:
            return None

        member_type_lower = member_type_input.lower().strip()

        if "representative" in member_type_lower or "rep" in member_type_lower:
            return cls.REPRESENTATIVE
        elif "senator" in member_type_lower or "sen" in member_type_lower:
            return cls.SENATOR
        elif "delegate" in member_type_lower:
            return cls.DELEGATE
        elif (
            "resident commissioner" in member_type_lower
            or "commissioner" in member_type_lower
        ):
            return cls.RESIDENT_COMMISSIONER

        return None


class CommitteeType(str, Enum):
    """Congressional committee types."""

    STANDING = "Standing"
    SUBCOMMITTEE = "Subcommittee"
    SELECT = "Select"
    SPECIAL = "Special"
    JOINT = "Joint"
    OTHER = "Other"

    @classmethod
    def normalize(cls, committee_type_input: Optional[str]) -> "CommitteeType":
        """
        Normalize committee type input to standard enum value.

        Args:
            committee_type_input: Raw committee type string from API

        Returns:
            Normalized CommitteeType enum value
        """
        if not committee_type_input:
            return cls.OTHER

        committee_type_lower = committee_type_input.lower().strip()

        if "standing" in committee_type_lower:
            return cls.STANDING
        elif "subcommittee" in committee_type_lower or "sub" in committee_type_lower:
            return cls.SUBCOMMITTEE
        elif "select" in committee_type_lower:
            return cls.SELECT
        elif "special" in committee_type_lower:
            return cls.SPECIAL
        elif "joint" in committee_type_lower:
            return cls.JOINT

        return cls.OTHER


class CommitteeRole(str, Enum):
    """Committee member roles."""

    CHAIR = "Chair"
    RANKING_MEMBER = "Ranking Member"
    VICE_CHAIR = "Vice Chair"
    MEMBER = "Member"
    EX_OFFICIO = "Ex Officio"
    UNKNOWN = "Unknown"

    @classmethod
    def normalize(cls, role_input: Optional[str]) -> "CommitteeRole":
        """
        Normalize committee role input to standard enum value.

        Args:
            role_input: Raw role string from API

        Returns:
            Normalized CommitteeRole enum value
        """
        if not role_input:
            return cls.MEMBER

        role_lower = role_input.lower().strip()

        # Map common variations
        if any(
            term in role_lower
            for term in ["chair", "chairman", "chairwoman", "chairperson"]
        ):
            if "vice" in role_lower or "deputy" in role_lower:
                return cls.VICE_CHAIR
            else:
                return cls.CHAIR
        elif any(
            term in role_lower for term in ["ranking", "ranking member", "minority"]
        ):
            return cls.RANKING_MEMBER
        elif any(
            term in role_lower for term in ["vice chair", "vice chairman", "deputy"]
        ):
            return cls.VICE_CHAIR
        elif any(
            term in role_lower for term in ["ex officio", "ex-officio", "exofficio"]
        ):
            return cls.EX_OFFICIO
        elif role_lower in ["member", "regular member", "committee member"]:
            return cls.MEMBER

        return cls.UNKNOWN

    @property
    def is_leadership(self) -> bool:
        """Check if this role is a leadership position."""
        return self in [self.CHAIR, self.RANKING_MEMBER, self.VICE_CHAIR]

    @property
    def is_voting_member(self) -> bool:
        """Check if this role typically has voting privileges."""
        # Ex officio members may not always have voting rights
        return self != self.EX_OFFICIO

    @property
    def priority_order(self) -> int:
        """Get numeric priority for sorting (lower = higher priority)."""
        priority_map = {
            self.CHAIR: 1,
            self.VICE_CHAIR: 2,
            self.RANKING_MEMBER: 3,
            self.MEMBER: 4,
            self.EX_OFFICIO: 5,
            self.UNKNOWN: 6,
        }
        return priority_map.get(self, 999)
