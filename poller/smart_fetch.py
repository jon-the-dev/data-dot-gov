#!/usr/bin/env python3
"""
Smart Fetch Script - Only fetches new or missing data
Checks existing data before making API calls to avoid redundant downloads
"""

import argparse
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SmartFetcher:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.metadata_file = self.data_dir / ".fetch_metadata.json"
        self.metadata = self.load_metadata()

    def load_metadata(self):
        """Load metadata about previous fetches"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_metadata(self):
        """Save metadata about fetches"""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def get_file_hash(self, filepath):
        """Get hash of a file to detect changes"""
        if not Path(filepath).exists():
            return None

        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def should_fetch(self, data_type, max_age_hours=24):
        """Check if we should fetch new data"""
        if data_type not in self.metadata:
            logger.info(f"No previous fetch record for {data_type}")
            return True

        last_fetch = datetime.fromisoformat(self.metadata[data_type]["last_fetch"])
        age = datetime.now() - last_fetch

        if age > timedelta(hours=max_age_hours):
            logger.info(
                f"{data_type} data is {age.total_seconds()/3600:.1f} hours old, refetching"
            )
            return True

        logger.info(
            f"{data_type} data is recent ({age.total_seconds()/3600:.1f} hours old), skipping"
        )
        return False

    def record_fetch(self, data_type, file_count=0, status="success"):
        """Record that we fetched data"""
        self.metadata[data_type] = {
            "last_fetch": datetime.now().isoformat(),
            "file_count": file_count,
            "status": status,
        }
        self.save_metadata()

    def check_existing_files(self, directory, pattern="*.json"):
        """Count existing files in a directory"""
        dir_path = self.data_dir / directory
        if not dir_path.exists():
            return 0

        files = list(dir_path.glob(pattern))
        # Exclude index files
        files = [
            f
            for f in files
            if f.name not in ["index.json", "summary.json", ".fetch_metadata.json"]
        ]
        return len(files)

    def get_fetch_commands(self, force=False, max_age_hours=24):
        """Get list of fetch commands to run based on existing data"""
        commands = []

        # Check Congressional bills
        bill_count = self.check_existing_files("congress_bills/118")
        if (
            force
            or self.should_fetch("congress_bills", max_age_hours)
            or bill_count == 0
        ):
            commands.append(
                {
                    "name": "Congressional Bills",
                    "cmd": "python gov_data_downloader_v2.py --congress-bills --congress 118 --max-results ${MAX_BILLS_ALL}",
                    "existing": bill_count,
                }
            )
        else:
            logger.info(
                f"Skipping Congressional Bills - {bill_count} files already exist"
            )

        # Check Senate filings
        filing_count = self.check_existing_files("senate_filings")
        if (
            force
            or self.should_fetch("senate_filings", max_age_hours)
            or filing_count == 0
        ):
            commands.append(
                {
                    "name": "Senate Filings",
                    "cmd": "python gov_data_downloader_v2.py --senate-filings --max-results ${MAX_RESULTS_ALL}",
                    "existing": filing_count,
                }
            )
        else:
            logger.info(f"Skipping Senate Filings - {filing_count} files already exist")

        # Check Senate lobbyists
        lobbyist_count = self.check_existing_files("senate_lobbyists")
        if (
            force
            or self.should_fetch("senate_lobbyists", max_age_hours)
            or lobbyist_count == 0
        ):
            commands.append(
                {
                    "name": "Senate Lobbyists",
                    "cmd": "python gov_data_downloader_v2.py --senate-lobbyists --max-results ${MAX_RESULTS_ALL}",
                    "existing": lobbyist_count,
                }
            )
        else:
            logger.info(
                f"Skipping Senate Lobbyists - {lobbyist_count} files already exist"
            )

        # Check members
        member_count = self.check_existing_files("members")
        if force or self.should_fetch("members", max_age_hours) or member_count == 0:
            commands.append(
                {
                    "name": "Congressional Members",
                    "cmd": "python gov_data_analyzer.py --members --congress 118 --max-members ${MAX_MEMBERS_ALL}",
                    "existing": member_count,
                }
            )
        else:
            logger.info(
                f"Skipping Congressional Members - {member_count} files already exist"
            )

        # Check voting records
        vote_count = self.check_existing_files("votes/118/house")
        if (
            force
            or self.should_fetch("voting_records", max_age_hours)
            or vote_count == 0
        ):
            commands.append(
                {
                    "name": "Voting Records",
                    "cmd": "python fetch_voting_records.py --congress 118 --max-votes ${MAX_VOTES_ALL}",
                    "existing": vote_count,
                }
            )
        else:
            logger.info(f"Skipping Voting Records - {vote_count} files already exist")

        # Check bill sponsors
        sponsor_count = self.check_existing_files("bill_sponsors")
        if (
            force
            or self.should_fetch("bill_sponsors", max_age_hours)
            or sponsor_count == 0
        ):
            commands.append(
                {
                    "name": "Bill Sponsors",
                    "cmd": "python analyze_bill_sponsors.py --congress 118 --max-bills ${MAX_BILLS_ALL}",
                    "existing": sponsor_count,
                }
            )
        else:
            logger.info(f"Skipping Bill Sponsors - {sponsor_count} files already exist")

        return commands

    def generate_makefile_snippet(self, commands):
        """Generate Makefile commands for smart fetching"""
        if not commands:
            return "echo 'All data is up to date!'"

        snippet = []
        for i, cmd in enumerate(commands, 1):
            snippet.append(
                f"\t@echo 'Stage {i}: Fetching {cmd['name']} (currently {cmd['existing']} files)...'"
            )
            snippet.append(f"\t@{cmd['cmd']}")
            snippet.append("\t@echo ''")

        return "\n".join(snippet)


def main():
    parser = argparse.ArgumentParser(
        description="Smart fetch - only download new or missing data"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force refetch even if data exists"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=24,
        help="Max age in hours before refetching (default: 24)",
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check what needs fetching"
    )
    parser.add_argument(
        "--generate-makefile", action="store_true", help="Generate Makefile snippet"
    )

    args = parser.parse_args()

    fetcher = SmartFetcher()

    # Get commands to run
    commands = fetcher.get_fetch_commands(force=args.force, max_age_hours=args.max_age)

    if args.check_only:
        print("\n=== Smart Fetch Status ===")
        print(f"Found {len(commands)} data sources that need updating:")
        for cmd in commands:
            print(f"  - {cmd['name']}: {cmd['existing']} existing files")

        # Show what we're skipping
        all_types = [
            "congress_bills",
            "senate_filings",
            "senate_lobbyists",
            "members",
            "voting_records",
            "bill_sponsors",
        ]
        skipped = [
            t
            for t in all_types
            if not any(c["name"].lower().replace(" ", "_") == t for c in commands)
        ]
        if skipped:
            print(f"\nSkipping {len(skipped)} up-to-date sources:")
            for s in skipped:
                count = fetcher.check_existing_files(s.replace("_", "/"))
                print(f"  - {s}: {count} files exist and are recent")

    elif args.generate_makefile:
        print(fetcher.generate_makefile_snippet(commands))

    elif not commands:
        print("All data is up to date! Use --force to refetch anyway.")
    else:
        print(f"Need to fetch {len(commands)} data sources")
        for cmd in commands:
            print(f"  - {cmd['name']}")


if __name__ == "__main__":
    main()
