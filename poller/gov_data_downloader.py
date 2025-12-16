#!/usr/bin/env python3
"""
Government Data Downloader - Downloads lobbying data from senate.gov and legislative data from congress.gov
Respects API rate limits and terms of service for both APIs
"""

import argparse
import json
import logging

# Import from consolidated core package
import warnings
from pathlib import Path
from typing import Dict, List

from core.api.congress import CongressGovAPI
from core.api.senate import SenateGovAPI
from dotenv import load_dotenv

# Deprecation warning for this script
warnings.warn(
    "gov_data_downloader.py is deprecated. Use core package APIs directly or use comprehensive_analyzer.py",
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


# SenateGovAPI is now imported from core.api.senate


# CongressGovAPI is now imported from core.api.congress


# save_data function replaced by core.storage.save_individual_record
# For legacy compatibility, creating a wrapper
def save_data(data: List[Dict], filename: str, output_dir: str = "data"):
    """
    Legacy wrapper for core storage function

    Args:
        data: Data to save
        filename: Output filename
        output_dir: Output directory
    """
    import warnings

    warnings.warn(
        "save_data is deprecated, use core.storage functions",
        DeprecationWarning,
        stacklevel=2,
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = Path(output_dir) / filename

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Saved {len(data)} records to {filepath}")


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
        "--congress-votes", action="store_true", help="Download congressional votes"
    )
    parser.add_argument(
        "--chamber",
        choices=["senate", "house"],
        default="senate",
        help="Chamber for congressional votes",
    )
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
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

    # Initialize APIs (use core package if available)
    senate_api = None
    congress_api = None

    if args.senate_filings or args.senate_lobbyists:
        if _USE_CORE:
            from core.api.senate import SenateGovAPI as CoreSenateGovAPI

            senate_api = CoreSenateGovAPI()
        else:
            senate_api = SenateGovAPI()

    if args.congress_bills or args.congress_votes:
        if _USE_CORE:
            from core.api.congress import CongressGovAPI as CoreCongressGovAPI

            congress_api = CoreCongressGovAPI()
        else:
            congress_api = CongressGovAPI()

    # Download Senate.gov data
    if senate_api:
        if args.senate_filings:
            logger.info("Downloading lobbying filings...")

            # Download LD-1 (registrations)
            ld1_filings = senate_api.get_filings(
                filing_type="LD-1",
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                output_dir=args.output_dir,
            )
            # Data already saved incrementally

            # Download LD-2 (quarterly reports)
            ld2_filings = senate_api.get_filings(
                filing_type="LD-2",
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                output_dir=args.output_dir,
            )
            # Data already saved incrementally

        if args.senate_lobbyists:
            logger.info("Downloading lobbyist information...")
            lobbyists = senate_api.get_lobbyists(
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                output_dir=args.output_dir,
            )
            # Data already saved incrementally

    # Download Congress.gov data
    if congress_api:
        if args.congress_bills:
            logger.info(f"Downloading bills from {args.congress}th Congress...")
            bills = congress_api.get_bills(
                congress=args.congress,
                max_results=args.max_results,
                output_dir=args.output_dir,
            )
            if not bills:  # Data already saved incrementally
                logger.info("Bills already saved to file")

        if args.congress_votes:
            logger.info(
                f"Downloading {args.chamber} votes from {args.congress}th Congress..."
            )
            if args.chamber.lower() == "house":
                votes = congress_api.get_house_votes(
                    congress=args.congress, max_results=args.max_results
                )
            else:
                # For senate, get bills with vote information
                logger.info("Getting bills with vote data for Senate...")
                votes = congress_api.get_bills_with_votes(
                    congress=args.congress, max_results=args.max_results
                )
            save_data(
                votes,
                f"congress_{args.congress}_{args.chamber}_votes.json",
                args.output_dir,
            )

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
    print("\nPlease respect these limits and terms of service.")
    print("=" * 60)


if __name__ == "__main__":
    main()
