#!/usr/bin/env python3
"""
Government Data Downloader V2 - Downloads and stores each record as individual JSON file
Respects API rate limits and terms of service for both APIs
"""

import argparse
import json
import logging

# Import from consolidated core package
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from core.api.congress import CongressGovAPI
from core.api.senate import SenateGovAPI
from core.storage import save_index, save_individual_record
from dotenv import load_dotenv

# Deprecation warning for this script
warnings.warn(
    "gov_data_downloader_v2.py is deprecated. Use core package APIs directly or use comprehensive_analyzer.py",
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
        record_type: Type of record (e.g., 'bills', 'votes', 'filings')
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


def save_index(records: List[Dict], record_type: str, base_dir: str = "data"):
    """
    Save an index file listing all records

    Args:
        records: List of records with metadata
        record_type: Type of record
        base_dir: Base directory
    """
    index_path = Path(base_dir) / record_type / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with open(index_path, "w") as f:
        json.dump(
            {
                "count": len(records),
                "last_updated": datetime.now().isoformat(),
                "records": records,
            },
            f,
            indent=2,
        )

    logger.info(f"Saved index with {len(records)} records to {index_path}")


def load_existing_index(record_type: str, base_dir: str = "data") -> List[str]:
    """
    Load existing record identifiers from index

    Args:
        record_type: Type of record
        base_dir: Base directory

    Returns:
        List of existing record identifiers
    """
    index_path = Path(base_dir) / record_type / "index.json"

    if not index_path.exists():
        return []

    try:
        with open(index_path) as f:
            data = json.load(f)
            return [r.get("id", "") for r in data.get("records", [])]
    except Exception as e:
        logger.warning(f"Could not load index: {e}")
        return []


# SenateGovAPI is now imported from core.api.senate


# CongressGovAPI is now imported from core.api.congress


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Download government data from senate.gov and congress.gov"
    )
    parser.add_argument(
        "--senate-filings", action="store_true", help="Download senate lobbying filings"
    )
    parser.add_argument(
        "--senate-lobbyists", action="store_true", help="Download lobbyist information"
    )
    parser.add_argument(
        "--congress-bills", action="store_true", help="Download congressional bills"
    )
    parser.add_argument(
        "--congress-votes",
        action="store_true",
        help="Download congressional House votes",
    )
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
    parser.add_argument("--session", type=int, help="Session number for House votes")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--max-results",
        type=int,
        default=25,
        help="Maximum results to fetch (default: 25 most recent)",
    )
    parser.add_argument(
        "--output-dir", default="data", help="Output directory for downloaded data"
    )

    args = parser.parse_args()

    # If no specific flags, download everything
    if not any(
        [
            args.senate_filings,
            args.senate_lobbyists,
            args.congress_bills,
            args.congress_votes,
        ]
    ):
        args.senate_filings = True
        args.senate_lobbyists = True
        args.congress_bills = True
        args.congress_votes = True

    # Initialize APIs
    senate_api = None
    congress_api = None

    if args.senate_filings or args.senate_lobbyists:
        senate_api = SenateGovAPI()

    if args.congress_bills or args.congress_votes:
        congress_api = CongressGovAPI()

    # Download Senate.gov data
    if senate_api:
        if args.senate_filings:
            logger.info("Downloading lobbying filings...")

            # Download RR (registrations)
            count = senate_api.get_filings(
                filing_type="RR",
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                base_dir=args.output_dir,
            )
            logger.info(f"Downloaded {count} Registration (RR) filings")

            # Download quarterly reports (Q1, Q2, Q3, Q4)
            quarterly_total = 0
            for quarter in ["Q1", "Q2", "Q3", "Q4"]:
                count = senate_api.get_filings(
                    filing_type=quarter,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    max_results=max(
                        1, args.max_results // 4
                    ),  # Split max_results across quarters
                    base_dir=args.output_dir,
                )
                logger.info(f"Downloaded {count} {quarter} filings")
                quarterly_total += count
            logger.info(f"Downloaded {quarterly_total} total quarterly report filings")

        if args.senate_lobbyists:
            logger.info("Downloading lobbyist information...")
            count = senate_api.get_lobbyists(
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                base_dir=args.output_dir,
            )
            logger.info(f"Downloaded {count} lobbyists")

    # Download Congress.gov data
    if congress_api:
        if args.congress_bills:
            logger.info(f"Downloading bills from {args.congress}th Congress...")
            count = congress_api.get_bills(
                congress=args.congress,
                max_results=args.max_results,
                base_dir=args.output_dir,
            )
            logger.info(f"Downloaded {count} bills")

        if args.congress_votes:
            logger.info(f"Downloading House votes from {args.congress}th Congress...")
            count = congress_api.get_house_votes(
                congress=args.congress,
                session=args.session,
                max_results=args.max_results,
                base_dir=args.output_dir,
            )
            logger.info(f"Downloaded {count} House votes")

    logger.info("Data download complete!")

    # Print TOS compliance reminder
    print("\n" + "=" * 60)
    print("IMPORTANT: Terms of Service Compliance")
    print("=" * 60)
    print("Senate.gov API:")
    print("- Rate limits: 120 req/min (authenticated), 15 req/min (anonymous)")
    print("- Data citation required with access date")
    print("- Cannot vouch for analyses after download")
    print("\nCongress.gov API (via data.gov):")
    print("- Rate limit: 1000 requests per hour with API key")
    print("- API key available at: https://api.data.gov/signup/")
    print("- Source: data.gov")
    print("\nData Storage:")
    print(f"- Individual JSON files saved in: {args.output_dir}/")
    print("- Each record type has its own directory with an index.json file")
    print("=" * 60)


if __name__ == "__main__":
    main()
