#!/usr/bin/env python3
"""
Specialized Fetcher Module - Advanced fetching capabilities for specific government data.

This module consolidates specialized fetching functionality from:
- fetch_voting_records.py
- fetch_committees.py
- The fetching parts of gov_data_analyzer.py

Key Features:
- Fetching detailed voting records with member positions
- Fetching committee information and activities
- Fetching member data with party affiliations
- Cross-referencing and enriching data
- Detailed member voting analysis
- Committee membership and bill assignments
- Party voting pattern analysis
"""

import argparse
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from core package
from core.api import CongressGovAPI
from core.storage import CompressedStorage, FileStorage, save_individual_record
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SpecializedFetcher:
    """
    Specialized fetcher for advanced government data operations.

    Provides methods for:
    - Detailed voting records with member positions
    - Committee information and activities
    - Member data with party affiliations and voting history
    - Cross-referencing and data enrichment
    """

    def __init__(
        self,
        data_dir: str = "data",
        api_key: Optional[str] = None,
        max_workers: int = 5,
        use_compression: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the specialized fetcher.

        Args:
            data_dir: Base directory for data storage
            api_key: Congress.gov API key
            max_workers: Number of parallel workers
            use_compression: Whether to use compressed storage
            verbose: Enable verbose logging
        """
        self.data_dir = Path(data_dir)
        self.max_workers = max_workers
        self.use_compression = use_compression
        self.verbose = verbose

        # Set up logging
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Initialize storage
        if use_compression:
            self.storage = CompressedStorage(base_dir=str(self.data_dir))
        else:
            self.storage = FileStorage(base_dir=str(self.data_dir))

        # Initialize API client
        self.congress_api = CongressGovAPI(
            api_key=api_key or os.getenv("DATA_GOV_API_KEY"), max_workers=max_workers
        )

        # Data caches for cross-referencing
        self.members_cache = {}
        self.party_cache = {}
        self.committees_cache = {}

        logger.info(f"Initialized SpecializedFetcher with data_dir={self.data_dir}")

    def _load_existing_members(self, congress: int) -> Dict[str, Dict]:
        """Load existing member data for cross-referencing."""
        members_dir = self.data_dir / f"members/{congress}"
        if not members_dir.exists():
            return {}

        members = {}
        for file_path in members_dir.glob("*.json"):
            if file_path.name not in ["index.json", "summary.json"]:
                try:
                    with open(file_path) as f:
                        member_data = json.load(f)
                        bioguide_id = member_data.get("bioguideId", file_path.stem)
                        members[bioguide_id] = member_data
                except Exception as e:
                    logger.warning(f"Could not load member from {file_path}: {e}")

        logger.info(f"Loaded {len(members)} existing members for congress {congress}")
        return members

    def _enrich_vote_with_member_data(
        self, vote_data: Dict, members_data: Dict[str, Dict]
    ) -> Dict:
        """Enrich vote data with member party information."""
        if "recordedVotes" not in vote_data:
            return vote_data

        # Enrich member votes with party information
        enriched_votes = []
        party_breakdown = defaultdict(lambda: defaultdict(int))

        for recorded_vote in vote_data["recordedVotes"]:
            member_id = recorded_vote.get("member", {}).get("bioguideId")
            if member_id and member_id in members_data:
                member_info = members_data[member_id]
                recorded_vote["member"]["party"] = member_info.get("party", "Unknown")
                recorded_vote["member"]["state"] = member_info.get("state", "Unknown")
                recorded_vote["member"]["district"] = member_info.get("district")

                # Track party breakdown
                party = member_info.get("party", "Unknown")
                vote_position = recorded_vote.get("vote", "Unknown")
                party_breakdown[party][vote_position] += 1

            enriched_votes.append(recorded_vote)

        vote_data["recordedVotes"] = enriched_votes
        vote_data["partyBreakdown"] = dict(party_breakdown)

        return vote_data

    def fetch_detailed_voting_records(
        self,
        congress: int = 118,
        max_votes: int = 100,
        chamber: str = "house",
        start_session: int = 1,
        force: bool = False,
    ) -> Tuple[int, List[str]]:
        """
        Fetch detailed voting records with member positions and party analysis.

        Args:
            congress: Congress number
            max_votes: Maximum number of votes to fetch
            chamber: Chamber ('house' or 'senate')
            start_session: Starting session number
            force: Force fetch even if data exists

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        logger.info(
            f"Fetching detailed voting records for {chamber} congress {congress}"
        )

        # Load existing members for enrichment
        members_data = self._load_existing_members(congress)
        if not members_data:
            logger.warning(
                "No member data found for enrichment, fetching members first..."
            )
            self.fetch_members_with_party_data(congress)
            members_data = self._load_existing_members(congress)

        # Get list of votes
        votes_data = self.congress_api.get_votes(
            congress=congress, chamber=chamber, limit=max_votes
        )

        if not votes_data or "votes" not in votes_data:
            logger.warning("No votes data received")
            return 0, []

        votes = votes_data["votes"]
        saved_files = []

        # Process each vote in detail
        for vote in votes:
            try:
                session = vote.get("sessionNumber", start_session)
                roll_call = vote.get("rollCall")

                if not roll_call:
                    continue

                # Get detailed vote with member positions
                vote_detail = self.congress_api.get_vote_detail(
                    congress=congress,
                    chamber=chamber,
                    session=session,
                    roll_call=roll_call,
                )

                if not vote_detail:
                    continue

                # Enrich with member party data
                enriched_vote = self._enrich_vote_with_member_data(
                    vote_detail, members_data
                )

                # Save the enriched vote
                vote_id = f"{congress}_{session}_{roll_call}"
                output_dir = f"{chamber}_votes_detailed/{congress}"

                if self.use_compression:
                    file_path = self.storage.save_record(
                        enriched_vote, f"{output_dir}/{vote_id}.json", compress=True
                    )
                else:
                    file_path = save_individual_record(
                        enriched_vote, output_dir, vote_id, str(self.data_dir)
                    )

                saved_files.append(file_path)

                # Log party breakdown for interesting votes
                if enriched_vote.get("partyBreakdown"):
                    breakdown = enriched_vote["partyBreakdown"]
                    logger.debug(f"Vote {roll_call} party breakdown: {breakdown}")

            except Exception as e:
                logger.error(
                    f"Failed to process vote {vote.get('rollCall', 'unknown')}: {e}"
                )

        logger.info(f"Successfully fetched and saved {len(saved_files)} detailed votes")
        return len(saved_files), saved_files

    def fetch_committees_with_details(
        self,
        congress: int = 118,
        include_bills: bool = True,
        include_memberships: bool = True,
        max_bills_per_committee: int = 500,
    ) -> Tuple[int, List[str]]:
        """
        Fetch committees with detailed information, bills, and memberships.

        Args:
            congress: Congress number
            include_bills: Whether to fetch bills for each committee
            include_memberships: Whether to fetch membership information
            max_bills_per_committee: Maximum bills to fetch per committee

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        logger.info(f"Fetching committees with details for congress {congress}")

        saved_files = []
        all_committees = {}

        # Fetch committees by chamber
        for chamber in ["house", "senate", "joint"]:
            logger.info(f"Fetching {chamber} committees...")

            committees_data = self.congress_api.get_committees(
                congress=congress, chamber=chamber
            )

            if not committees_data or "committees" not in committees_data:
                logger.warning(f"No {chamber} committees data received")
                continue

            chamber_committees = []

            # Process each committee
            for committee in committees_data["committees"]:
                try:
                    committee_code = committee.get("systemCode")
                    if not committee_code:
                        continue

                    # Get detailed committee information
                    committee_detail = self.congress_api.get_committee_detail(
                        chamber=chamber, committee_code=committee_code
                    )

                    if committee_detail:
                        enriched_committee = committee_detail.copy()

                        # Add bills if requested
                        if include_bills:
                            bills_data = self.congress_api.get_committee_bills(
                                chamber=chamber,
                                committee_code=committee_code,
                                congress=congress,
                                limit=max_bills_per_committee,
                            )
                            if bills_data:
                                enriched_committee["associatedBills"] = bills_data.get(
                                    "bills", []
                                )

                        # Add membership if requested
                        if include_memberships:
                            # This would require additional API calls to get member details
                            # For now, we'll include what's available in the committee data
                            pass

                        chamber_committees.append(enriched_committee)

                        # Save individual committee
                        committee_id = f"{congress}_{chamber}_{committee_code}"
                        output_dir = f"committees/{congress}"

                        if self.use_compression:
                            file_path = self.storage.save_record(
                                enriched_committee,
                                f"{output_dir}/{committee_id}.json",
                                compress=True,
                            )
                        else:
                            file_path = save_individual_record(
                                enriched_committee,
                                output_dir,
                                committee_id,
                                str(self.data_dir),
                            )

                        saved_files.append(file_path)

                except Exception as e:
                    logger.error(
                        f"Failed to process committee {committee.get('name', 'unknown')}: {e}"
                    )

            all_committees[chamber] = chamber_committees
            logger.info(f"Processed {len(chamber_committees)} {chamber} committees")

        # Save summary
        summary = {
            "congress": congress,
            "fetch_date": datetime.now().isoformat(),
            "committees_by_chamber": {
                chamber: len(committees)
                for chamber, committees in all_committees.items()
            },
            "total_committees": sum(
                len(committees) for committees in all_committees.values()
            ),
        }

        summary_path = save_individual_record(
            summary, f"committees/{congress}", "summary", str(self.data_dir)
        )
        saved_files.append(summary_path)

        logger.info(f"Successfully fetched {len(saved_files)} committee files")
        return len(saved_files), saved_files

    def fetch_members_with_party_data(
        self,
        congress: int = 118,
        chamber: Optional[str] = None,
        include_voting_history: bool = False,
    ) -> Tuple[int, List[str]]:
        """
        Fetch Congressional members with enhanced party and voting data.

        Args:
            congress: Congress number
            chamber: Chamber filter ('house' or 'senate')
            include_voting_history: Whether to include voting history summary

        Returns:
            Tuple of (count, list_of_file_paths)
        """
        logger.info(f"Fetching members with party data for congress {congress}")

        # Get members from Congress API
        members_data = self.congress_api.get_members(congress=congress, chamber=chamber)

        if not members_data or "members" not in members_data:
            logger.warning("No members data received")
            return 0, []

        members = members_data["members"]
        saved_files = []
        party_summary = defaultdict(int)

        # Process each member
        for member in members:
            try:
                bioguide_id = member.get("bioguideId")
                if not bioguide_id:
                    continue

                # Enrich member data
                enriched_member = member.copy()

                # Add party summary tracking
                party = member.get("party", "Unknown")
                party_summary[party] += 1

                # Add voting history if requested
                if include_voting_history:
                    # This would require fetching individual member voting records
                    # For now, we'll set up the structure
                    enriched_member["votingHistory"] = {
                        "totalVotes": 0,
                        "partyUnityScore": None,
                        "lastUpdated": datetime.now().isoformat(),
                    }

                # Save individual member
                if self.use_compression:
                    file_path = self.storage.save_record(
                        enriched_member,
                        f"members/{congress}/{bioguide_id}.json",
                        compress=True,
                    )
                else:
                    file_path = save_individual_record(
                        enriched_member,
                        f"members/{congress}",
                        bioguide_id,
                        str(self.data_dir),
                    )

                saved_files.append(file_path)

            except Exception as e:
                logger.error(
                    f"Failed to process member {member.get('name', 'unknown')}: {e}"
                )

        # Save party summary
        summary = {
            "congress": congress,
            "chamber": chamber,
            "fetch_date": datetime.now().isoformat(),
            "total_members": len(saved_files),
            "party_breakdown": dict(party_summary),
            "chambers": {},
        }

        # Break down by chamber if not filtered
        if not chamber:
            chamber_breakdown = defaultdict(lambda: defaultdict(int))
            for member_file in saved_files:
                try:
                    with open(member_file) as f:
                        member_data = json.load(f)
                        member_chamber = member_data.get("chamber", "unknown")
                        member_party = member_data.get("party", "Unknown")
                        chamber_breakdown[member_chamber][member_party] += 1
                except Exception:
                    continue
            summary["chambers"] = dict(chamber_breakdown)

        summary_path = save_individual_record(
            summary, f"members/{congress}", "summary", str(self.data_dir)
        )
        saved_files.append(summary_path)

        logger.info(f"Successfully fetched {len(saved_files)} member files")
        logger.info(f"Party breakdown: {dict(party_summary)}")
        return len(saved_files), saved_files

    def analyze_party_voting_patterns(
        self, congress: int = 118, chamber: str = "house", min_votes: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze party voting patterns from detailed voting records.

        Args:
            congress: Congress number
            chamber: Chamber to analyze
            min_votes: Minimum votes required for analysis

        Returns:
            Analysis results dictionary
        """
        logger.info(
            f"Analyzing party voting patterns for {chamber} congress {congress}"
        )

        # Load detailed votes
        votes_dir = self.data_dir / f"{chamber}_votes_detailed/{congress}"
        if not votes_dir.exists():
            logger.error(f"No detailed votes found in {votes_dir}")
            return {}

        vote_files = list(votes_dir.glob("*.json"))
        if len(vote_files) < min_votes:
            logger.warning(
                f"Only {len(vote_files)} votes found, minimum {min_votes} required"
            )

        # Analyze votes
        party_stats = defaultdict(
            lambda: {
                "total_votes": 0,
                "yea_votes": 0,
                "nay_votes": 0,
                "not_voting": 0,
                "present": 0,
            }
        )

        bipartisan_votes = 0
        partisan_votes = 0
        total_analyzed = 0

        for vote_file in vote_files:
            try:
                with open(vote_file) as f:
                    vote_data = json.load(f)

                party_breakdown = vote_data.get("partyBreakdown", {})
                if not party_breakdown:
                    continue

                total_analyzed += 1

                # Check if vote was bipartisan (both major parties had members on both sides)
                is_bipartisan = False
                for party in ["Democratic", "Republican"]:
                    if party in party_breakdown:
                        party_votes = party_breakdown[party]
                        if (
                            party_votes.get("Yea", 0) > 0
                            and party_votes.get("Nay", 0) > 0
                        ):
                            is_bipartisan = True
                            break

                if is_bipartisan:
                    bipartisan_votes += 1
                else:
                    partisan_votes += 1

                # Aggregate party statistics
                for party, votes in party_breakdown.items():
                    party_stats[party]["total_votes"] += sum(votes.values())
                    for vote_type, count in votes.items():
                        if vote_type.lower() in party_stats[party]:
                            party_stats[party][vote_type.lower()] += count

            except Exception as e:
                logger.error(f"Failed to analyze vote file {vote_file}: {e}")

        # Calculate party unity scores
        for party in party_stats:
            stats = party_stats[party]
            total = stats["total_votes"]
            if total > 0:
                stats["yea_percentage"] = (stats["yea_votes"] / total) * 100
                stats["nay_percentage"] = (stats["nay_votes"] / total) * 100
                stats["not_voting_percentage"] = (stats["not_voting"] / total) * 100

        analysis = {
            "congress": congress,
            "chamber": chamber,
            "analysis_date": datetime.now().isoformat(),
            "votes_analyzed": total_analyzed,
            "bipartisan_votes": bipartisan_votes,
            "partisan_votes": partisan_votes,
            "bipartisan_percentage": (
                (bipartisan_votes / total_analyzed * 100) if total_analyzed > 0 else 0
            ),
            "party_statistics": dict(party_stats),
        }

        # Save analysis
        analysis_path = save_individual_record(
            analysis,
            f"analysis/{congress}",
            f"{chamber}_party_voting_analysis",
            str(self.data_dir),
        )

        logger.info(f"Party voting analysis completed, saved to {analysis_path}")
        logger.info(
            f"Analyzed {total_analyzed} votes: {bipartisan_votes} bipartisan, {partisan_votes} partisan"
        )

        return analysis

    def cross_reference_data(
        self,
        congress: int = 118,
        include_vote_member_links: bool = True,
        include_bill_committee_links: bool = True,
    ) -> Dict[str, Any]:
        """
        Cross-reference data between members, votes, bills, and committees.

        Args:
            congress: Congress number
            include_vote_member_links: Link votes to member records
            include_bill_committee_links: Link bills to committee records

        Returns:
            Cross-reference results
        """
        logger.info(f"Cross-referencing data for congress {congress}")

        results = {
            "congress": congress,
            "cross_reference_date": datetime.now().isoformat(),
            "links_created": {
                "vote_member": 0,
                "bill_committee": 0,
                "member_committee": 0,
            },
        }

        # Link votes to members
        if include_vote_member_links:
            vote_member_links = self._link_votes_to_members(congress)
            results["links_created"]["vote_member"] = vote_member_links

        # Link bills to committees
        if include_bill_committee_links:
            bill_committee_links = self._link_bills_to_committees(congress)
            results["links_created"]["bill_committee"] = bill_committee_links

        # Save cross-reference results
        results_path = save_individual_record(
            results,
            f"analysis/{congress}",
            "cross_reference_results",
            str(self.data_dir),
        )

        logger.info(f"Cross-reference completed, saved to {results_path}")
        return results

    def _link_votes_to_members(self, congress: int) -> int:
        """Link voting records to member profiles."""
        # Implementation would create indexes linking votes to member records
        # For now, return placeholder count
        return 0

    def _link_bills_to_committees(self, congress: int) -> int:
        """Link bills to committee records."""
        # Implementation would create indexes linking bills to committees
        # For now, return placeholder count
        return 0


def main():
    """Command-line interface for the specialized fetcher."""
    parser = argparse.ArgumentParser(description="Specialized Government Data Fetcher")

    # Data source options
    parser.add_argument(
        "--detailed-votes",
        action="store_true",
        help="Fetch detailed voting records with member positions",
    )
    parser.add_argument(
        "--committees",
        action="store_true",
        help="Fetch committees with details, bills, and memberships",
    )
    parser.add_argument(
        "--members",
        action="store_true",
        help="Fetch members with party data and voting history",
    )
    parser.add_argument(
        "--analyze-voting", action="store_true", help="Analyze party voting patterns"
    )
    parser.add_argument(
        "--cross-reference",
        action="store_true",
        help="Cross-reference data between types",
    )

    # Parameters
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument("--chamber", choices=["house", "senate"], help="Chamber filter")
    parser.add_argument(
        "--max-votes", type=int, default=100, help="Maximum votes to fetch"
    )
    parser.add_argument(
        "--max-bills-per-committee",
        type=int,
        default=500,
        help="Maximum bills per committee",
    )

    # Options
    parser.add_argument("--data-dir", default="data", help="Data directory")
    parser.add_argument(
        "--force", action="store_true", help="Force fetch even if data exists"
    )
    parser.add_argument(
        "--compressed", action="store_true", help="Use compressed storage"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5, help="Number of parallel workers"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = SpecializedFetcher(
        data_dir=args.data_dir,
        max_workers=args.max_workers,
        use_compression=args.compressed,
        verbose=args.verbose,
    )

    # Execute requested operations
    if args.detailed_votes:
        count, files = fetcher.fetch_detailed_voting_records(
            congress=args.congress,
            max_votes=args.max_votes,
            chamber=args.chamber or "house",
            force=args.force,
        )
        print(f"Fetched {count} detailed voting records")

    if args.committees:
        count, files = fetcher.fetch_committees_with_details(
            congress=args.congress, max_bills_per_committee=args.max_bills_per_committee
        )
        print(f"Fetched {count} committee files")

    if args.members:
        count, files = fetcher.fetch_members_with_party_data(
            congress=args.congress, chamber=args.chamber
        )
        print(f"Fetched {count} member files")

    if args.analyze_voting:
        analysis = fetcher.analyze_party_voting_patterns(
            congress=args.congress, chamber=args.chamber or "house"
        )
        if analysis:
            print(f"Analyzed {analysis.get('votes_analyzed', 0)} votes")
            print(f"Bipartisan: {analysis.get('bipartisan_percentage', 0):.1f}%")

    if args.cross_reference:
        fetcher.cross_reference_data(congress=args.congress)
        print(f"Cross-referenced data for congress {args.congress}")


if __name__ == "__main__":
    main()
