#!/usr/bin/env python3
"""
Fetch committee and subcommittee data from Congress.gov API.
Uses the unified CongressGovAPI and core storage patterns.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.api.congress import CongressGovAPI
from core.models.committee import Committee
from core.models.enums import Chamber, CommitteeType
from core.storage.file_storage import FileStorage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommitteeFetcher:
    """Fetches committee data using the unified CongressGovAPI and core storage patterns."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_dir: str = "data",
        max_workers: int = 5,
    ):
        """Initialize the fetcher with API credentials."""
        self.congress_api = CongressGovAPI(api_key=api_key, max_workers=max_workers)
        self.storage = FileStorage(base_dir=base_dir)
        self.base_dir = Path(base_dir)

        # Create directories following project patterns
        self.committees_dir = self.base_dir / "committees"
        self.committees_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_committee_data(
        self, committee_data: Dict, chamber: str, congress: int
    ) -> Optional[Committee]:
        """Normalize committee data to use our Committee model."""
        try:
            # Map chamber string to Chamber enum
            chamber_enum = Chamber.normalize(chamber)

            # Determine committee type
            committee_type = CommitteeType.STANDING  # Default
            if committee_data.get("parent"):
                committee_type = CommitteeType.SUBCOMMITTEE
            elif "joint" in chamber.lower():
                committee_type = CommitteeType.JOINT
            elif "select" in committee_data.get("name", "").lower():
                committee_type = CommitteeType.SELECT

            # Create committee object
            committee = Committee(
                system_code=committee_data.get("systemCode", ""),
                name=committee_data.get("name", ""),
                chamber=chamber_enum,
                committee_type=committee_type,
                code=committee_data.get("code"),
                thomas_id=committee_data.get("thomasId"),
                parent_committee=(
                    committee_data.get("parent", {}).get("systemCode")
                    if committee_data.get("parent")
                    else None
                ),
                subcommittees=[
                    sub.get("systemCode", "")
                    for sub in committee_data.get("subcommittees", [])
                ],
                jurisdiction=committee_data.get("jurisdiction"),
                url=committee_data.get("url"),
                congress_url=committee_data.get("congress_url"),
                congress=congress,
                is_active=True,
                source_api="congress.gov",
            )

            return committee
        except Exception as e:
            logger.error(f"Error normalizing committee data: {e}")
            return None

    def fetch_all_committees(self, congress: int = 118) -> Dict[str, List[Committee]]:
        """Fetch all committees for a given congress using CongressGovAPI."""
        logger.info(f"Fetching committees for Congress {congress}")

        committees = {"house": [], "senate": [], "joint": []}

        # Fetch by chamber using the unified API
        for chamber in ["house", "senate", "joint"]:
            logger.info(f"Fetching {chamber} committees...")

            offset = 0
            limit = 250

            while True:
                endpoint = f"/committee/{congress}/{chamber}"
                params = {"offset": offset, "limit": limit}

                data = self.congress_api._make_request(endpoint, params)
                if not data or "committees" not in data:
                    break

                chamber_committees = data["committees"]
                if not chamber_committees:
                    break

                # Normalize and validate committee data
                for committee_data in chamber_committees:
                    committee = self._normalize_committee_data(
                        committee_data, chamber, congress
                    )
                    if committee:
                        committees[chamber].append(committee)

                # Check for more pages
                if len(chamber_committees) < limit:
                    break
                offset += limit

            logger.info(f"Found {len(committees[chamber])} {chamber} committees")

        return committees

    def fetch_committee_details(
        self, chamber: str, committee_code: str, congress: int = 118
    ) -> Optional[Committee]:
        """Fetch detailed information for a specific committee."""
        logger.debug(f"Fetching details for {chamber}/{committee_code}")

        endpoint = f"/committee/{chamber}/{committee_code}"
        data = self.congress_api._make_request(endpoint)

        if data and "committee" in data:
            return self._normalize_committee_data(data["committee"], chamber, congress)
        return None

    def fetch_committee_bills(
        self,
        chamber: str,
        committee_code: str,
        congress: int = 118,
        max_bills: int = 1000,
    ) -> List[Dict]:
        """Fetch bills associated with a committee."""
        logger.info(f"Fetching bills for {chamber}/{committee_code}")

        bills = []
        offset = 0
        limit = 250

        while len(bills) < max_bills:
            endpoint = f"/committee/{chamber}/{committee_code}/bills"
            params = {"offset": offset, "limit": limit}

            data = self.congress_api._make_request(endpoint, params)
            if not data or "bills" not in data:
                break

            batch = data["bills"]
            if not batch:
                break

            bills.extend(batch)

            if len(batch) < limit:
                break
            offset += limit

        return bills[:max_bills]

    def fetch_committee_reports(
        self, chamber: str, committee_code: str, congress: int = 118
    ) -> List[Dict]:
        """Fetch committee reports."""
        logger.info(f"Fetching reports for {chamber}/{committee_code}")

        reports = []
        offset = 0
        limit = 250

        while True:
            endpoint = f"/committee/{chamber}/{committee_code}/reports"
            params = {"offset": offset, "limit": limit}

            data = self.congress_api._make_request(endpoint, params)
            if not data or "reports" not in data:
                break

            batch = data["reports"]
            if not batch:
                break

            reports.extend(batch)

            if len(batch) < limit:
                break
            offset += limit

        return reports

    def fetch_bill_committees(
        self, congress: int, bill_type: str, bill_number: int
    ) -> List[Dict]:
        """Fetch committees associated with a specific bill."""
        endpoint = f"/bill/{congress}/{bill_type}/{bill_number}/committees"
        data = self.congress_api._make_request(endpoint)

        if data and "committees" in data:
            return data["committees"]
        return []

    def save_committee_data(
        self, committees: Dict[str, List[Committee]], congress: int
    ):
        """Save committee data using the unified storage pattern."""
        for chamber, committee_list in committees.items():
            if not committee_list:
                continue

            # Save each committee as individual file
            for committee in committee_list:
                record_type = f"committees/{congress}/{chamber}"
                identifier = committee.system_code or committee.code or "unknown"

                # Convert to dict for storage
                committee_dict = committee.model_dump_json_safe()

                # Save using unified storage
                self.storage.save_individual_record(
                    committee_dict, record_type, identifier, congress=None
                )

            # Create index data for this chamber
            index_records = []
            for committee in committee_list:
                index_records.append(
                    {
                        "id": committee.system_code or committee.code,
                        "name": committee.name,
                        "type": committee.committee_type.value,
                        "is_subcommittee": committee.is_subcommittee,
                        "parent": committee.parent_committee,
                        "member_count": committee.member_count,
                    }
                )

            # Save index
            record_type = f"committees/{congress}/{chamber}"
            self.storage.save_index(index_records, record_type)

            logger.info(
                f"Saved {len(committee_list)} {chamber} committees using unified storage"
            )

    def save_committee_bills(
        self, chamber: str, committee_code: str, bills: List[Dict], congress: int
    ):
        """Save committee bill assignments using unified storage."""
        if not bills:
            return

        # Save as bulk record for committee bills
        record_type = f"committee_bills/{congress}"
        identifier = f"{chamber}_{committee_code}"

        data = {
            "congress": congress,
            "chamber": chamber,
            "committee_code": committee_code,
            "bill_count": len(bills),
            "bills": bills,
            "fetched_at": datetime.now().isoformat(),
        }

        self.storage.save_individual_record(data, record_type, identifier)
        logger.info(f"Saved {len(bills)} bills for {committee_code}")

    def fetch_and_save_all(
        self,
        congress: int = 118,
        fetch_bills: bool = True,
        max_bills_per_committee: int = 100,
    ):
        """Fetch and save all committee data using unified patterns."""
        logger.info(
            f"Starting comprehensive committee data fetch for Congress {congress}"
        )

        # Fetch all committees
        committees = self.fetch_all_committees(congress)
        self.save_committee_data(committees, congress)

        # Fetch detailed data and bills for each committee
        if fetch_bills:
            all_committees = []
            for chamber, committee_list in committees.items():
                for committee in committee_list:
                    all_committees.append((chamber, committee))

            logger.info(f"Fetching bills for {len(all_committees)} committees")

            with ThreadPoolExecutor(
                max_workers=self.congress_api.max_workers
            ) as executor:
                futures = []

                for chamber, committee in all_committees:
                    code = committee.system_code or committee.code
                    if code:
                        future = executor.submit(
                            self._fetch_committee_data_wrapper,
                            chamber,
                            code,
                            congress,
                            max_bills_per_committee,
                        )
                        futures.append((future, chamber, code))

                for future, chamber, code in futures:
                    try:
                        future.result(timeout=60)
                    except Exception as e:
                        logger.error(f"Error processing {chamber}/{code}: {e}")

        logger.info("Committee data fetch complete!")

    def _fetch_committee_data_wrapper(
        self, chamber: str, code: str, congress: int, max_bills: int
    ):
        """Wrapper to fetch and save committee bills."""
        try:
            bills = self.fetch_committee_bills(chamber, code, congress, max_bills)
            if bills:
                self.save_committee_bills(chamber, code, bills, congress)
        except Exception as e:
            logger.error(f"Error fetching data for {chamber}/{code}: {e}")

    def generate_committee_summary(self, congress: int = 118) -> Dict:
        """Generate a summary of committee data using unified storage."""
        summary = {
            "congress": congress,
            "chambers": {},
            "total_committees": 0,
            "total_subcommittees": 0,
            "generated_at": datetime.now().isoformat(),
        }

        for chamber in ["house", "senate", "joint"]:
            record_type = f"committees/{congress}/{chamber}"
            index_data = self.storage.load_index(record_type)

            if not index_data:
                summary["chambers"][chamber] = {
                    "committees": 0,
                    "subcommittees": 0,
                    "total": 0,
                }
                continue

            committees = 0
            subcommittees = 0

            for record in index_data.get("records", []):
                if record.get("is_subcommittee", False) or record.get("parent"):
                    subcommittees += 1
                else:
                    committees += 1

            summary["chambers"][chamber] = {
                "committees": committees,
                "subcommittees": subcommittees,
                "total": committees + subcommittees,
            }

            summary["total_committees"] += committees
            summary["total_subcommittees"] += subcommittees

        # Save summary using storage
        record_type = f"committees/{congress}"
        self.storage.save_individual_record(summary, record_type, "summary")

        return summary


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch committee data from Congress.gov"
    )
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument(
        "--fetch-bills", action="store_true", help="Fetch committee bills"
    )
    parser.add_argument(
        "--max-bills", type=int, default=100, help="Max bills per committee"
    )
    parser.add_argument(
        "--chamber",
        choices=["house", "senate", "joint"],
        help="Fetch only specific chamber",
    )
    parser.add_argument("--summary", action="store_true", help="Generate summary only")

    args = parser.parse_args()

    fetcher = CommitteeFetcher()

    if args.summary:
        summary = fetcher.generate_committee_summary(args.congress)
        print(json.dumps(summary, indent=2))
    else:
        fetcher.fetch_and_save_all(
            congress=args.congress,
            fetch_bills=args.fetch_bills,
            max_bills_per_committee=args.max_bills,
        )


if __name__ == "__main__":
    main()
