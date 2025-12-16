#!/usr/bin/env python3
"""
Fetch Senate lobbying disclosure data (LD-1 and LD-2 filings).

LD-1: Registration forms (new lobbyist registrations) - filing_type 'RR'
LD-2: Activity reports (quarterly activity reports) - filing_type 'Q1', 'Q2', 'Q3', 'Q4'

The Senate Lobbying Disclosure API contains 1.8M+ filings dating back to 1999.
By default, this script fetches recent filings (last 2 years) sorted newest first.
"""

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

from core.api import SenateGovAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_default_start_date() -> str:
    """Get default start date (2 years ago for recent data)"""
    two_years_ago = datetime.now() - timedelta(days=730)
    return two_years_ago.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Senate lobbying disclosure filings (LD-1 and LD-2)"
    )

    # Filing type selection
    parser.add_argument(
        "--ld1",
        action="store_true",
        help="Fetch LD-1 Registration forms (new lobbyist registrations)",
    )
    parser.add_argument(
        "--ld2", action="store_true", help="Fetch LD-2 Activity reports (quarterly)"
    )
    parser.add_argument(
        "--all", action="store_true", help="Fetch both LD-1 and LD-2 (default)"
    )

    # Parameters
    parser.add_argument(
        "--max-results",
        type=int,
        default=500,
        help="Maximum results per filing type (default: 500)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD format, default: 2 years ago)",
    )
    parser.add_argument(
        "--end-date", type=str, default=None, help="End date (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--quarters",
        type=str,
        nargs="+",
        default=["Q1", "Q2", "Q3", "Q4"],
        help="Quarters to fetch for LD-2 (default: Q1 Q2 Q3 Q4)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory (default: data)",
    )

    args = parser.parse_args()

    # Default to fetching both if no specific flag
    if not any([args.ld1, args.ld2]):
        args.all = True

    if args.all:
        args.ld1 = True
        args.ld2 = True

    # Use default start date if not specified (2 years ago for recent data)
    if not args.start_date:
        args.start_date = get_default_start_date()
        logger.info(f"Using default start date: {args.start_date} (last 2 years)")

    # Initialize Senate API
    senate_api = SenateGovAPI()

    total_fetched = 0
    ld1_count = 0
    ld2_count = 0

    # Fetch LD-1 Registration forms
    if args.ld1:
        logger.info(f"Fetching up to {args.max_results} LD-1 Registration forms...")
        logger.info("  Filing type: RR (Registration)")
        logger.info(f"  Date range: {args.start_date} to {args.end_date or 'now'}")

        try:
            ld1_filings = senate_api.get_registrations(
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                output_dir=args.output_dir,
                individual_files=True,
            )
            ld1_count = len(ld1_filings)
            total_fetched += ld1_count

            if ld1_filings:
                logger.info(f"✅ Fetched {ld1_count} LD-1 Registration filings")
                # Show sample dates
                sample_dates = [
                    f.get("dt_posted", "N/A")[:10] for f in ld1_filings[:3]
                ]
                logger.info(f"  Sample dates: {', '.join(sample_dates)}")
            else:
                logger.warning("No LD-1 filings found for the specified date range")

        except Exception as e:
            logger.error(f"Failed to fetch LD-1 filings: {e}")

    # Fetch LD-2 Activity reports
    if args.ld2:
        logger.info(f"Fetching up to {args.max_results} LD-2 Activity reports...")
        logger.info(f"  Filing types: {', '.join(args.quarters)} (Quarterly Reports)")
        logger.info(f"  Date range: {args.start_date} to {args.end_date or 'now'}")

        try:
            ld2_filings = senate_api.get_quarterly_reports(
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                output_dir=args.output_dir,
                individual_files=True,
                quarters=args.quarters,
            )
            ld2_count = len(ld2_filings)
            total_fetched += ld2_count

            if ld2_filings:
                logger.info(f"✅ Fetched {ld2_count} LD-2 Activity Report filings")
                # Show sample dates
                sample_dates = [
                    f.get("dt_posted", "N/A")[:10] for f in ld2_filings[:3]
                ]
                logger.info(f"  Sample dates: {', '.join(sample_dates)}")
            else:
                logger.warning("No LD-2 filings found for the specified date range")

        except Exception as e:
            logger.error(f"Failed to fetch LD-2 filings: {e}")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"🎉 Total lobbying filings fetched: {total_fetched}")
    logger.info(f"   LD-1 Registrations: {ld1_count}")
    logger.info(f"   LD-2 Activity Reports: {ld2_count}")
    logger.info(f"{'='*60}")

    # Show data location
    data_dir = Path(args.output_dir) / "senate_filings"
    if data_dir.exists():
        logger.info(f"\nData saved to: {data_dir.absolute()}")

        # Count files in each subdirectory
        for subdir in ["ld-1", "ld-2", "rr", "q1", "q2", "q3", "q4"]:
            subpath = data_dir / subdir
            if subpath.exists():
                file_count = len(list(subpath.glob("*.json")))
                if file_count > 0:
                    logger.info(f"  {subdir}/: {file_count} files")


if __name__ == "__main__":
    main()
