"""
Consolidated data models for the Congressional Transparency Platform.

This package provides comprehensive Pydantic v2 models for all government data structures
including bills, members, votes, committees, and lobbying data with proper validation,
relationships, and computed properties.
"""

from .bill import Bill, BillAction, BillSponsor, BillSubject
from .committee import (
    BillCommitteeAction,
    Committee,
    CommitteeActivity,
    CommitteeMeeting,
    CommitteeMember,
)
from .enums import (
    BillType,
    Chamber,
    CommitteeRole,
    CommitteeType,
    FilingType,
    MemberType,
    Party,
    VotePosition,
)
from .lobbying import GovernmentPosition, LobbyingFiling, LobbyingIssue, Lobbyist
from .member import Member, MemberDepiction, MemberTerm
from .vote import MemberVote, Vote, VoteBreakdown

__all__ = [
    # Enums
    "Party",
    "Chamber",
    "VotePosition",
    "BillType",
    "FilingType",
    "MemberType",
    "CommitteeType",
    "CommitteeRole",
    # Bill models
    "Bill",
    "BillAction",
    "BillSponsor",
    "BillSubject",
    # Member models
    "Member",
    "MemberTerm",
    "MemberDepiction",
    # Vote models
    "Vote",
    "VoteBreakdown",
    "MemberVote",
    # Committee models
    "Committee",
    "CommitteeMember",
    "CommitteeActivity",
    "CommitteeMeeting",
    "BillCommitteeAction",
    # Lobbying models
    "LobbyingFiling",
    "Lobbyist",
    "LobbyingIssue",
    "GovernmentPosition",
]
