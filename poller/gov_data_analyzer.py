#!/usr/bin/env python3
"""
Government Data Analyzer - Enhanced downloader with parallel processing and vote analysis
Fetches member data, voting records, and links them for party-based analysis
"""

import argparse
import json
import logging

# Import from consolidated core package
import warnings
from pathlib import Path
from typing import Any, Dict

from core.api.congress import CongressGovAPI
from core.storage import save_individual_record
from dotenv import load_dotenv

# Deprecation warning for this script
warnings.warn(
    "This script is deprecated. Use core package APIs directly or use comprehensive_analyzer.py",
    DeprecationWarning,
    stacklevel=2,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# RateLimiter is now imported from core.api.rate_limiter


def save_individual_record(
    record: Dict, record_type: str, identifier: str, base_dir: str = "data"
) -> str:
    """
    Save an individual record as a JSON file

    Args:
        record: The record data to save
        record_type: Type of record (e.g., 'bills', 'votes', 'members')
        identifier: Unique identifier for the record
        base_dir: Base directory for data storage

    Returns:
        Path to the saved file
    """
    import warnings

    warnings.warn(
        "save_individual_record is deprecated, use core.storage",
        DeprecationWarning,
        stacklevel=2,
    )
    # Create directory structure
    dir_path = Path(base_dir) / record_type
    dir_path.mkdir(parents=True, exist_ok=True)

    # Clean identifier for filename
    safe_id = identifier.replace("/", "_").replace(" ", "_").replace(":", "_")
    filename = f"{safe_id}.json"
    filepath = dir_path / filename

    # Save the record
    with open(filepath, "w") as f:
        json.dump(record, f, indent=2, default=str)

    return str(filepath)


def load_existing_records(record_type: str, base_dir: str = "data") -> Dict[str, Any]:
    """
    Load all existing records of a type

    Args:
        record_type: Type of record
        base_dir: Base directory

    Returns:
        Dictionary mapping record IDs to records
    """
    dir_path = Path(base_dir) / record_type

    if not dir_path.exists():
        return {}

    records = {}
    for filepath in dir_path.glob("*.json"):
        if filepath.name != "index.json":
            try:
                with open(filepath) as f:
                    record = json.load(f)
                    # Use filename without .json as ID
                    record_id = filepath.stem
                    records[record_id] = record
            except Exception as e:
                logger.warning(f"Could not load {filepath}: {e}")

    return records


# CongressGovAPI is now imported from core.api.congress


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Download and analyze Congressional voting data"
    )
    parser.add_argument("--members", action="store_true", help="Download member data")
    parser.add_argument(
        "--votes", action="store_true", help="Download detailed vote data"
    )
    parser.add_argument(
        "--analyze", action="store_true", help="Analyze voting patterns"
    )
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
    parser.add_argument(
        "--chamber",
        choices=["house", "senate", "both"],
        default="house",
        help="Chamber for votes",
    )
    parser.add_argument(
        "--max-votes", type=int, default=10, help="Maximum votes to fetch details for"
    )
    parser.add_argument(
        "--max-members", type=int, default=50, help="Maximum members to fetch"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5, help="Maximum parallel workers"
    )
    parser.add_argument("--output-dir", default="data", help="Output directory")

    args = parser.parse_args()

    # If no specific action, do everything
    if not any([args.members, args.votes, args.analyze]):
        args.members = True
        args.votes = True
        args.analyze = True

    # Initialize API
    api = CongressGovAPI(max_workers=args.max_workers)

    if args.members:
        logger.info(f"Downloading members of {args.congress}th Congress...")
        members = api.get_members(
            congress=args.congress,
            base_dir=args.output_dir,
            max_members=args.max_members,
        )
        logger.info(f"Downloaded {len(members)} members")

    if args.votes:
        if args.chamber in ["house", "both"]:
            logger.info("Downloading House votes with details...")
            house_votes = api.get_roll_call_votes_with_details(
                congress=args.congress,
                chamber="house",
                max_votes=args.max_votes,
                base_dir=args.output_dir,
            )
            logger.info(
                f"Downloaded {len(house_votes)} House votes with member details"
            )

        if args.chamber in ["senate", "both"]:
            logger.info("Downloading Senate votes...")
            senate_votes = api.get_roll_call_votes_with_details(
                congress=args.congress,
                chamber="senate",
                max_votes=args.max_votes,
                base_dir=args.output_dir,
            )
            logger.info(f"Downloaded {len(senate_votes)} Senate votes")

    if args.analyze:
        logger.info("Analyzing voting patterns...")
        analysis = api.analyze_party_votes(base_dir=args.output_dir)

        print("\n" + "=" * 60)
        print("VOTING PATTERN ANALYSIS")
        print("=" * 60)
        print(f"Total Votes Analyzed: {analysis['total_votes_analyzed']}")
        print(f"Bipartisan Votes: {analysis.get('bipartisan_percentage', 0):.1f}%")
        print(f"Party Line Votes: {analysis.get('party_line_percentage', 0):.1f}%")

        if analysis.get("vote_topics"):
            print("\nVote Topics by Party Support:")
            for topic, votes in analysis["vote_topics"].items():
                print(f"  {topic.capitalize()}:")
                for party_action, count in votes.items():
                    print(f"    {party_action}: {count}")
        print("=" * 60)

    logger.info("Data collection and analysis complete!")

    # Print summary
    print("\n" + "=" * 60)
    print("DATA COLLECTION SUMMARY")
    print("=" * 60)
    print(f"Congress: {args.congress}th")
    print(f"Output Directory: {args.output_dir}/")
    print("\nAvailable Data:")
    print("- Member profiles with party affiliations")
    print("- Detailed roll call votes with individual member positions")
    print("- Party voting breakdowns")
    print("- Bipartisanship analysis")
    print("\nUse this data to:")
    print("- Show how representatives vote along party lines")
    print("- Identify bipartisan legislation")
    print("- Track individual member voting records")
    print("- Analyze voting patterns by topic")
    print("=" * 60)


if __name__ == "__main__":
    main()
