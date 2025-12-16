#!/usr/bin/env python3
"""
Enhanced Poller Scheduler with Smart Data Freshness Checks
"""

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import schedule

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/scheduler.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class SmartScheduler:
    """Scheduler that checks data freshness before fetching"""

    def __init__(self):
        self.data_dir = Path("/app/data")
        self.metadata_file = self.data_dir / ".fetch_metadata.json"
        self.max_age_hours = int(os.getenv("DATA_MAX_AGE_HOURS", "24"))
        self.force_initial_fetch = (
            os.getenv("FORCE_INITIAL_FETCH", "false").lower() == "true"
        )

    def load_metadata(self):
        """Load metadata about previous fetches"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
                return {}
        return {}

    def check_data_freshness(self):
        """Check if data is fresh enough or needs updating"""
        metadata = self.load_metadata()

        # Define the data types we care about
        critical_data_types = [
            "congress_bills",
            "senate_filings",
            "senate_lobbyists",
            "members",
            "voting_records",
            "bill_sponsors",
        ]

        needs_update = []
        missing_data = []
        stale_data = []

        for data_type in critical_data_types:
            if data_type not in metadata:
                missing_data.append(data_type)
                needs_update.append(data_type)
                logger.info(f"No fetch record for {data_type} - needs initial fetch")
            else:
                try:
                    last_fetch = datetime.fromisoformat(
                        metadata[data_type]["last_fetch"]
                    )
                    age = datetime.now() - last_fetch

                    if age > timedelta(hours=self.max_age_hours):
                        stale_data.append(
                            f"{data_type} ({age.total_seconds()/3600:.1f}h old)"
                        )
                        needs_update.append(data_type)
                        logger.info(
                            f"{data_type} is {age.total_seconds()/3600:.1f} hours old - needs refresh"
                        )
                    else:
                        logger.info(
                            f"{data_type} is recent ({age.total_seconds()/3600:.1f}h old) - skipping"
                        )
                except Exception as e:
                    logger.warning(f"Error checking {data_type}: {e}")
                    needs_update.append(data_type)

        # Also check if we have actual files, not just metadata
        for data_type in critical_data_types:
            if data_type not in needs_update:
                # Map data types to expected directories
                dir_mappings = {
                    "congress_bills": "congress_bills/118",
                    "senate_filings": "senate_filings",
                    "senate_lobbyists": "senate_lobbyists",
                    "members": "members",
                    "voting_records": "votes/118/house",
                    "bill_sponsors": "bill_sponsors",
                }

                data_path = self.data_dir / dir_mappings.get(data_type, data_type)
                if not data_path.exists() or not any(data_path.glob("*.json")):
                    logger.warning(
                        f"{data_type} metadata exists but no actual files found - needs fetch"
                    )
                    needs_update.append(data_type)
                    missing_data.append(f"{data_type} (files missing)")

        return {
            "needs_update": bool(needs_update),
            "missing_data": missing_data,
            "stale_data": stale_data,
            "data_types_to_update": needs_update,
        }

    def run_comprehensive_fetch(self):
        """Run comprehensive data fetch and analysis"""
        try:
            logger.info("=" * 60)
            logger.info("Starting comprehensive data fetch")

            # Check what needs updating first
            freshness = self.check_data_freshness()

            if not freshness["needs_update"] and not self.force_initial_fetch:
                logger.info("All data is up-to-date, skipping fetch")
                return

            if freshness["missing_data"]:
                logger.info(f"Missing data: {', '.join(freshness['missing_data'])}")
            if freshness["stale_data"]:
                logger.info(f"Stale data: {', '.join(freshness['stale_data'])}")

            # Run the fetch using fetchers/unified_fetcher.py
            logger.info("Running unified fetcher...")
            result = subprocess.run(
                [
                    "python",
                    "/app/fetchers/unified_fetcher.py",
                    "--all",
                    "--max-results",
                    os.getenv("MAX_ITEMS", "1000"),
                    "--congress",
                    os.getenv("CONGRESS", "118"),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if result.stdout:
                logger.info(f"Fetch output: {result.stdout[:500]}")

            logger.info("Comprehensive fetch completed successfully")

            # Update metadata after successful fetch
            self.update_metadata(freshness["data_types_to_update"])

        except subprocess.TimeoutExpired:
            logger.error("Comprehensive fetch timed out after 1 hour")
        except subprocess.CalledProcessError as e:
            logger.error(f"Comprehensive fetch failed with exit code {e.returncode}")
            if e.stdout:
                logger.error(f"Output: {e.stdout[:500]}")
            if e.stderr:
                logger.error(f"Error: {e.stderr[:500]}")
        except Exception as e:
            logger.error(f"Unexpected error in comprehensive fetch: {e}")

    def run_incremental_fetch(self):
        """Run incremental updates for recent data only"""
        try:
            logger.info("Starting incremental fetch for recent updates")

            # Use smart_fetch.py for incremental updates
            result = subprocess.run(
                [
                    "python",
                    "/app/smart_fetch.py",
                    "--max-age",
                    "6",  # Only update if older than 6 hours
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if "up to date" in result.stdout.lower():
                logger.info("Incremental data is up-to-date")
            else:
                logger.info(f"Incremental fetch result: {result.stdout[:500]}")

        except subprocess.TimeoutExpired:
            logger.error("Incremental fetch timed out after 10 minutes")
        except subprocess.CalledProcessError as e:
            logger.error(f"Incremental fetch failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in incremental fetch: {e}")

    def update_metadata(self, data_types):
        """Update metadata after successful fetch"""
        metadata = self.load_metadata()

        for data_type in data_types:
            metadata[data_type] = {
                "last_fetch": datetime.now().isoformat(),
                "status": "success",
            }

        # Save updated metadata
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Updated metadata for {len(data_types)} data types")

    def check_data_availability(self):
        """Check if we have any data at all"""
        # Check for critical analysis files that indicate we have processed data
        critical_files = [
            self.data_dir / "analysis" / "comprehensive_report.json",
            self.data_dir / "analysis" / "party_voting_patterns.json",
            self.data_dir / "congress_bills" / "118",
        ]

        has_data = False
        for path in critical_files:
            if path.exists():
                if path.is_file():
                    has_data = True
                    logger.info(f"Found existing data: {path.name}")
                elif path.is_dir() and any(path.glob("*.json")):
                    has_data = True
                    logger.info(f"Found existing data in: {path.name}")

        return has_data

    def initial_startup_check(self):
        """Perform initial check on startup to determine if fetch is needed"""
        logger.info("=" * 60)
        logger.info("POLLER SERVICE STARTING - Initial Data Check")
        logger.info("=" * 60)

        # Check if we have any data at all
        has_data = self.check_data_availability()

        if not has_data:
            logger.warning(
                "No existing data found - running initial comprehensive fetch"
            )
            self.run_comprehensive_fetch()
            return

        # Check data freshness
        freshness = self.check_data_freshness()

        if freshness["needs_update"]:
            logger.info(
                f"Data needs updating - {len(freshness['data_types_to_update'])} sources need refresh"
            )
            self.run_comprehensive_fetch()
        else:
            logger.info("All data is up-to-date - no initial fetch needed")
            logger.info(
                f"Next scheduled fetch at {os.getenv('FETCH_SCHEDULE', '02:00')}"
            )


def main():
    """Main scheduler entry point"""
    scheduler = SmartScheduler()

    # Schedule configuration from environment
    fetch_schedule = os.getenv("FETCH_SCHEDULE", "02:00")
    enable_incremental = os.getenv("ENABLE_INCREMENTAL", "true").lower() == "true"
    run_on_startup = os.getenv("RUN_ON_STARTUP", "true").lower() == "true"

    logger.info("Poller Configuration:")
    logger.info(f"  - Daily fetch scheduled at: {fetch_schedule}")
    logger.info(
        f"  - Incremental updates: {'Enabled' if enable_incremental else 'Disabled'}"
    )
    logger.info(f"  - Run on startup: {'Yes' if run_on_startup else 'No'}")
    logger.info(f"  - Data max age: {scheduler.max_age_hours} hours")
    logger.info(f"  - Congress: {os.getenv('CONGRESS', '118')}")
    logger.info(f"  - Max items: {os.getenv('MAX_ITEMS', '1000')}")

    # Schedule regular tasks
    schedule.every().day.at(fetch_schedule).do(scheduler.run_comprehensive_fetch)

    if enable_incremental:
        # Run incremental updates every 4 hours
        schedule.every(4).hours.do(scheduler.run_incremental_fetch)
        logger.info("  - Incremental updates: Every 4 hours")

    # Run initial startup check (smart - only fetches if needed)
    if run_on_startup:
        scheduler.initial_startup_check()
    else:
        logger.info("Skipping startup fetch as configured")

    # Main scheduler loop
    logger.info("Scheduler running - waiting for next scheduled task...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
