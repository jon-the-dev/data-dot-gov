#!/usr/bin/env python3
"""
Fetch Congressional members and votes using the core package.
Replaces gov_data_analyzer.py with proper core integration.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List

from core.api import CongressGovAPI
from core.storage import FileStorage

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def analyze_voting_patterns(votes: List[Dict]) -> Dict:
    """Analyze voting patterns to identify party-line and bipartisan votes."""

    patterns = {
        "party_line_votes": [],
        "bipartisan_votes": [],
        "total_votes": len(votes),
    }

    for vote in votes:
        if "parties" in vote:
            party_breakdown = vote.get("parties", {})

            # Calculate party unity (simplified)
            if "D" in party_breakdown and "R" in party_breakdown:
                d_yes = party_breakdown["D"].get("yes", 0)
                d_no = party_breakdown["D"].get("no", 0)
                r_yes = party_breakdown["R"].get("yes", 0)
                r_no = party_breakdown["R"].get("no", 0)

                # Party line vote if parties voted oppositely
                if (d_yes > d_no and r_no > r_yes) or (d_no > d_yes and r_yes > r_no):
                    patterns["party_line_votes"].append(
                        {
                            "vote_id": vote.get("rollCallNumber", "Unknown"),
                            "question": vote.get("question", "Unknown"),
                            "date": vote.get("date", "Unknown"),
                        }
                    )
                # Bipartisan if significant support from both parties
                elif d_yes > 10 and r_yes > 10:
                    patterns["bipartisan_votes"].append(
                        {
                            "vote_id": vote.get("rollCallNumber", "Unknown"),
                            "question": vote.get("question", "Unknown"),
                            "date": vote.get("date", "Unknown"),
                        }
                    )

    patterns["party_line_percentage"] = (
        len(patterns["party_line_votes"]) / patterns["total_votes"] * 100
        if patterns["total_votes"] > 0
        else 0
    )
    patterns["bipartisan_percentage"] = (
        len(patterns["bipartisan_votes"]) / patterns["total_votes"] * 100
        if patterns["total_votes"] > 0
        else 0
    )

    return patterns


def main():
    parser = argparse.ArgumentParser(description="Fetch and analyze Congressional data")

    # Data type flags
    parser.add_argument(
        "--members", action="store_true", help="Fetch Congressional members"
    )
    parser.add_argument("--votes", action="store_true", help="Fetch roll call votes")
    parser.add_argument(
        "--analyze", action="store_true", help="Analyze voting patterns"
    )

    # Parameters
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
    parser.add_argument(
        "--chamber",
        choices=["house", "senate", "both"],
        default="both",
        help="Chamber to fetch data for",
    )
    parser.add_argument(
        "--max-members", type=int, default=50, help="Maximum members to fetch"
    )
    parser.add_argument(
        "--max-votes", type=int, default=10, help="Maximum votes to fetch"
    )
    parser.add_argument(
        "--max-workers", type=int, default=10, help="Number of parallel workers"
    )
    parser.add_argument(
        "--output-dir", type=str, default="data", help="Output directory"
    )

    args = parser.parse_args()

    # Initialize API
    api = CongressGovAPI(max_workers=args.max_workers)
    storage = FileStorage(base_dir=Path(args.output_dir))

    all_members = []
    all_votes = []

    # Fetch members
    if args.members:
        if args.chamber in ["house", "both"]:
            logger.info(f"Fetching House members from {args.congress}th Congress...")
            house_members = api.get_members(
                congress=args.congress, chamber="house", max_results=args.max_members
            )
            logger.info(f"✅ Fetched {len(house_members)} House members")
            all_members.extend(house_members)

            # Save to storage
            storage.save_bulk_records(
                house_members, f"members/{args.congress}", "house_members.json"
            )

        if args.chamber in ["senate", "both"]:
            logger.info(f"Fetching Senate members from {args.congress}th Congress...")
            senate_members = api.get_members(
                congress=args.congress, chamber="senate", max_results=args.max_members
            )
            logger.info(f"✅ Fetched {len(senate_members)} Senate members")
            all_members.extend(senate_members)

            # Save to storage
            storage.save_bulk_records(
                senate_members, f"members/{args.congress}", "senate_members.json"
            )

    # Fetch votes
    if args.votes:
        if args.chamber in ["house", "both"]:
            logger.info(f"Fetching House votes from {args.congress}th Congress...")
            house_votes = api.get_house_votes(
                congress=args.congress, max_results=args.max_votes
            )
            logger.info(f"✅ Fetched {len(house_votes)} House votes")
            all_votes.extend(house_votes)

            # Save to storage
            storage.save_bulk_records(
                house_votes, f"votes/{args.congress}", "house_votes.json"
            )

        if args.chamber in ["senate", "both"]:
            logger.info(f"Fetching Senate votes from {args.congress}th Congress...")
            senate_votes = api.get_detailed_votes(
                congress=args.congress, chamber="senate", max_votes=args.max_votes
            )
            logger.info(f"✅ Fetched {len(senate_votes)} Senate votes")
            all_votes.extend(senate_votes)

            # Save to storage
            storage.save_bulk_records(
                senate_votes, f"votes/{args.congress}", "senate_votes.json"
            )

    # Analyze voting patterns
    if args.analyze and all_votes:
        logger.info("Analyzing voting patterns...")
        patterns = analyze_voting_patterns(all_votes)

        # Display analysis results
        logger.info("\n📊 VOTING PATTERN ANALYSIS")
        logger.info(f"{'=' * 50}")
        logger.info(f"Total votes analyzed: {patterns['total_votes']}")
        logger.info(
            f"Party-line votes: {len(patterns['party_line_votes'])} ({patterns['party_line_percentage']:.1f}%)"
        )
        logger.info(
            f"Bipartisan votes: {len(patterns['bipartisan_votes'])} ({patterns['bipartisan_percentage']:.1f}%)"
        )

        # Save analysis
        storage.save_bulk_records(
            [patterns],  # save_bulk_records expects a list
            "analysis",
            f"voting_patterns_{args.congress}.json",
        )
        logger.info(f"\n✅ Analysis saved to {args.output_dir}/analysis/")

    # Summary
    total_fetched = len(all_members) + len(all_votes)
    if total_fetched > 0:
        logger.info(f"\n🎉 Total records fetched: {total_fetched}")
        logger.info(f"  - Members: {len(all_members)}")
        logger.info(f"  - Votes: {len(all_votes)}")
        logger.info(f"Data saved to: {Path(args.output_dir).absolute()}")


if __name__ == "__main__":
    main()
