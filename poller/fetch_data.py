#!/usr/bin/env python3
"""
Modern data fetcher using the core package APIs.
Replaces gov_data_downloader_v2.py with proper core integration.
"""

import argparse
import logging
from pathlib import Path

from core.api import CongressGovAPI, SenateGovAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Fetch Congressional and Senate data")

    # Data type flags
    parser.add_argument(
        "--congress-bills", action="store_true", help="Fetch Congress bills"
    )
    parser.add_argument(
        "--congress-votes", action="store_true", help="Fetch Congress votes"
    )
    parser.add_argument(
        "--senate-filings", action="store_true", help="Fetch Senate lobbying filings"
    )
    parser.add_argument(
        "--senate-lobbyists", action="store_true", help="Fetch Senate lobbyists"
    )
    parser.add_argument("--all", action="store_true", help="Fetch all data types")

    # Parameters
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number (default: 118)"
    )
    parser.add_argument(
        "--max-results", type=int, default=25, help="Maximum results per category"
    )
    parser.add_argument(
        "--max-workers", type=int, default=10, help="Number of parallel workers"
    )

    args = parser.parse_args()

    # If no specific flags, fetch all
    if not any(
        [
            args.congress_bills,
            args.congress_votes,
            args.senate_filings,
            args.senate_lobbyists,
        ]
    ):
        args.all = True

    if args.all:
        args.congress_bills = True
        args.congress_votes = True
        args.senate_filings = True
        args.senate_lobbyists = True

    # Initialize APIs
    congress_api = CongressGovAPI(max_workers=args.max_workers)
    senate_api = SenateGovAPI()  # Note: SenateGovAPI doesn't support max_workers

    total_fetched = 0

    # Fetch Congress bills
    if args.congress_bills:
        logger.info(
            f"Fetching up to {args.max_results} bills from Congress {args.congress}..."
        )
        try:
            bills = congress_api.get_bills(
                congress=args.congress, max_results=args.max_results
            )
            logger.info(f"✅ Fetched {len(bills)} bills")
            total_fetched += len(bills)
        except Exception as e:
            logger.error(f"Failed to fetch bills: {e}")

    # Fetch Congress votes
    if args.congress_votes:
        logger.info(
            f"Fetching up to {args.max_results} House votes from Congress {args.congress}..."
        )
        try:
            votes = congress_api.get_house_votes(
                congress=args.congress, max_results=args.max_results
            )
            logger.info(f"✅ Fetched {len(votes)} House votes")
            total_fetched += len(votes)
        except Exception as e:
            logger.error(f"Failed to fetch House votes: {e}")

    # Fetch Senate lobbying filings
    if args.senate_filings:
        logger.info(f"Fetching up to {args.max_results} Senate lobbying filings...")
        try:
            # Try YY (Year-End Reports - most common filings)
            yy_filings = senate_api.get_filings(
                filing_type="YY",
                max_results=args.max_results // 2,  # Split between YY and MM
            )
            logger.info(f"✅ Fetched {len(yy_filings)} Year-End Report filings")

            # Try MM (Mid-Year Reports)
            mm_filings = senate_api.get_filings(
                filing_type="MM", max_results=args.max_results // 2
            )
            logger.info(f"✅ Fetched {len(mm_filings)} Mid-Year Report filings")

            total_fetched += len(yy_filings) + len(mm_filings)
        except Exception as e:
            logger.error(f"Failed to fetch lobbying filings: {e}")

    # Fetch Senate lobbyists
    if args.senate_lobbyists:
        logger.info(f"Fetching up to {args.max_results} Senate lobbyists...")
        try:
            lobbyists = senate_api.get_lobbyists(max_results=args.max_results)
            logger.info(f"✅ Fetched {len(lobbyists)} lobbyists")
            total_fetched += len(lobbyists)
        except Exception as e:
            logger.error(f"Failed to fetch lobbyists: {e}")

    logger.info(f"\n🎉 Total records fetched: {total_fetched}")

    # Show data location
    data_dir = Path("data")
    if data_dir.exists():
        logger.info(f"Data saved to: {data_dir.absolute()}")


if __name__ == "__main__":
    main()
