#!/usr/bin/env python3
"""
Fetch Senate lobbying disclosure data (LD-1 and LD-2 filings).
"""

import argparse
import logging
from pathlib import Path

from core.api import SenateGovAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Senate lobbying disclosure filings"
    )

    # Filing type selection
    parser.add_argument(
        "--ld1", action="store_true", help="Fetch LD-1 Registration forms"
    )
    parser.add_argument(
        "--ld2", action="store_true", help="Fetch LD-2 Activity reports"
    )
    parser.add_argument("--all", action="store_true", help="Fetch both LD-1 and LD-2")

    # Parameters
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum results per filing type (default: 100)",
    )
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD format)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD format)")
    parser.add_argument(
        "--individual-files",
        action="store_true",
        help="Save each filing as individual file",
    )

    args = parser.parse_args()

    # Default to fetching both if no specific flag
    if not any([args.ld1, args.ld2]):
        args.all = True

    if args.all:
        args.ld1 = True
        args.ld2 = True

    # Initialize Senate API
    senate_api = SenateGovAPI()

    total_fetched = 0

    # Fetch LD-1 Registration forms
    if args.ld1:
        logger.info(f"Fetching up to {args.max_results} LD-1 Registration forms...")
        try:
            # The API might use different filing type codes
            # Try common variations: 'LD-1', 'RR' (Registration Report), '1'
            filing_types_to_try = ["LD-1", "RR", "1", "ld-1"]
            ld1_filings = []

            for filing_type in filing_types_to_try:
                logger.info(f"Trying filing type: {filing_type}")
                filings = senate_api.get_filings(
                    filing_type=filing_type,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    max_results=args.max_results,
                    individual_files=args.individual_files,
                    output_dir="data",
                )
                if filings:
                    ld1_filings = filings
                    logger.info(
                        f"✅ Successfully fetched {len(ld1_filings)} LD-1 filings using type '{filing_type}'"
                    )
                    break

            if not ld1_filings:
                logger.warning(
                    "Could not fetch LD-1 filings with any known filing type code"
                )

            total_fetched += len(ld1_filings)

        except Exception as e:
            logger.error(f"Failed to fetch LD-1 filings: {e}")

    # Fetch LD-2 Activity reports
    if args.ld2:
        logger.info(f"Fetching up to {args.max_results} LD-2 Activity reports...")
        try:
            # The API might use different filing type codes
            # Try common variations: 'LD-2', 'Q1', 'Q2', 'Q3', 'Q4', '2'
            filing_types_to_try = ["LD-2", "Q1", "Q2", "Q3", "Q4", "2", "ld-2"]
            ld2_filings = []

            # For LD-2, we might need to fetch quarterly reports separately
            for filing_type in filing_types_to_try:
                logger.info(f"Trying filing type: {filing_type}")
                filings = senate_api.get_filings(
                    filing_type=filing_type,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    max_results=(
                        args.max_results // 4
                        if filing_type.startswith("Q")
                        else args.max_results
                    ),
                    individual_files=args.individual_files,
                    output_dir="data",
                )
                if filings:
                    ld2_filings.extend(filings)
                    logger.info(
                        f"✅ Fetched {len(filings)} filings for type '{filing_type}'"
                    )

                    # If we got results with a quarterly type, try other quarters
                    if filing_type.startswith("Q"):
                        continue
                    else:
                        break  # Found a working non-quarterly type

            if ld2_filings:
                logger.info(f"✅ Total LD-2 filings fetched: {len(ld2_filings)}")
            else:
                logger.warning(
                    "Could not fetch LD-2 filings with any known filing type code"
                )

            total_fetched += len(ld2_filings)

        except Exception as e:
            logger.error(f"Failed to fetch LD-2 filings: {e}")

    logger.info(f"\n🎉 Total lobbying filings fetched: {total_fetched}")

    # Show data location
    data_dir = Path("data/senate_filings")
    if data_dir.exists():
        logger.info(f"Data saved to: {data_dir.absolute()}")

        # Count files in each subdirectory
        for subdir in ["ld-1", "ld-2", "rr", "q1", "q2", "q3", "q4"]:
            subpath = data_dir / subdir
            if subpath.exists():
                file_count = len(list(subpath.glob("*.json")))
                if file_count > 0:
                    logger.info(f"  {subdir}/: {file_count} files")


if __name__ == "__main__":
    main()
