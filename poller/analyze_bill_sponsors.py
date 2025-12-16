#!/usr/bin/env python3
"""
Bill Sponsor Analysis Script - Analyzes sponsor and co-sponsor patterns in congressional bills
Calculates party success rates and cross-party co-sponsorship patterns
"""

import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the base API class
from gov_data_downloader_v2 import (
    CongressGovAPI,
    load_existing_index,
    save_individual_record,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CongressGovAPIv2(CongressGovAPI):
    """Extended Congress.gov API client with additional endpoints for bill analysis"""

    def get_bill_cosponsors(
        self, congress: int, bill_type: str, bill_number: str
    ) -> Optional[Dict]:
        """
        Get cosponsors for a specific bill

        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (e.g., 'hr', 's', 'hjres', 'sjres')
            bill_number: Bill number

        Returns:
            Cosponsors data or None if failed
        """
        endpoint = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/cosponsors"
        return self._make_request(endpoint)

    def get_bill_sponsors_batch(
        self, bills: List[Dict], base_dir: str = "data"
    ) -> Dict[str, Dict]:
        """
        Fetch sponsor and cosponsor data for a batch of bills

        Args:
            bills: List of bill dictionaries with congress, type, and number
            base_dir: Base directory for caching sponsor data

        Returns:
            Dictionary mapping bill_id to sponsor/cosponsor data
        """
        sponsors_data = {}
        record_type = "bill_sponsors"

        # Load existing sponsor data to avoid re-fetching
        existing_ids = set(load_existing_index(record_type, base_dir))

        for bill in bills:
            congress = bill.get("congress")
            bill_type = bill.get("type", "").lower()
            bill_number = bill.get("number")

            if not all([congress, bill_type, bill_number]):
                continue

            bill_id = f"{congress}_{bill_type}_{bill_number}"

            # Check if we already have this data
            if bill_id in existing_ids:
                try:
                    # Load from cache
                    cached_path = Path(base_dir) / record_type / f"{bill_id}.json"
                    if cached_path.exists():
                        with open(cached_path) as f:
                            sponsors_data[bill_id] = json.load(f)
                        logger.debug(f"Loaded cached sponsor data for {bill_id}")
                        continue
                except Exception as e:
                    logger.warning(f"Failed to load cached data for {bill_id}: {e}")

            logger.info(f"Fetching cosponsor data for {bill_id}...")

            # Fetch fresh data
            cosponsor_data = self.get_bill_cosponsors(congress, bill_type, bill_number)

            if cosponsor_data:
                # Store the combined sponsor/cosponsor data
                bill_sponsor_data = {
                    "bill_id": bill_id,
                    "congress": congress,
                    "type": bill_type,
                    "number": bill_number,
                    "sponsors": bill.get("sponsors", []),
                    "cosponsors": cosponsor_data.get("cosponsors", []),
                    "cosponsor_count": cosponsor_data.get("count", 0),
                    "fetched_at": datetime.now().isoformat(),
                }

                sponsors_data[bill_id] = bill_sponsor_data

                # Cache the data
                save_individual_record(
                    bill_sponsor_data, record_type, bill_id, base_dir
                )
                logger.debug(f"Cached sponsor data for {bill_id}")
            else:
                logger.warning(f"Failed to fetch cosponsor data for {bill_id}")

        return sponsors_data


class BillSponsorAnalyzer:
    """Analyzes bill sponsor and co-sponsor patterns"""

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the analyzer

        Args:
            base_dir: Base directory containing data files
        """
        self.base_dir = Path(base_dir)
        self.members_data = {}
        self.bills_data = []
        self.sponsor_data = {}

    def load_member_data(self, congress: int = 118) -> Dict[str, Dict]:
        """
        Load member data from the members directory

        Args:
            congress: Congress number to load data for

        Returns:
            Dictionary mapping bioguide_id to member data
        """
        logger.info(f"Loading member data for {congress}th Congress...")

        members_dir = self.base_dir / "members" / str(congress)
        if not members_dir.exists():
            logger.error(f"Members directory not found: {members_dir}")
            return {}

        members = {}
        for member_file in members_dir.glob("*.json"):
            try:
                with open(member_file) as f:
                    member_data = json.load(f)
                    bioguide_id = member_data.get("bioguideId")
                    if bioguide_id:
                        members[bioguide_id] = member_data
            except Exception as e:
                logger.warning(f"Failed to load member file {member_file}: {e}")

        logger.info(f"Loaded {len(members)} members")
        self.members_data = members
        return members

    def load_bills_data(self, congress: int = 118) -> List[Dict]:
        """
        Load bills data from the congress_bills directory

        Args:
            congress: Congress number to load data for

        Returns:
            List of bill dictionaries
        """
        logger.info(f"Loading bills data for {congress}th Congress...")

        bills_dir = self.base_dir / "congress_bills" / str(congress)
        if not bills_dir.exists():
            logger.error(f"Bills directory not found: {bills_dir}")
            return []

        bills = []
        for bill_file in bills_dir.glob("*.json"):
            try:
                with open(bill_file) as f:
                    bill_data = json.load(f)
                    bills.append(bill_data)
            except Exception as e:
                logger.warning(f"Failed to load bill file {bill_file}: {e}")

        logger.info(f"Loaded {len(bills)} bills")
        self.bills_data = bills
        return bills

    def get_member_party(self, bioguide_id: str) -> str:
        """
        Get party affiliation for a member

        Args:
            bioguide_id: Member's bioguide ID

        Returns:
            Party code (R, D, I, etc.) or 'Unknown'
        """
        member = self.members_data.get(bioguide_id, {})
        return member.get("party", "Unknown")

    def analyze_party_introduction_rates(self) -> Dict[str, Any]:
        """
        Analyze which party introduces more bills

        Returns:
            Dictionary with party introduction statistics
        """
        logger.info("Analyzing party introduction rates...")

        party_introductions = Counter()
        party_bill_types = defaultdict(Counter)

        for bill in self.bills_data:
            sponsors = bill.get("sponsors", [])
            if not sponsors:
                continue

            # Primary sponsor is typically the first one
            primary_sponsor = sponsors[0]
            sponsor_party = primary_sponsor.get("party", "Unknown")

            # Count by party
            party_introductions[sponsor_party] += 1

            # Count by bill type and party
            bill_type = bill.get("type", "Unknown")
            party_bill_types[sponsor_party][bill_type] += 1

        total_bills = sum(party_introductions.values())

        # Calculate percentages
        party_percentages = {
            party: (count / total_bills * 100) if total_bills > 0 else 0
            for party, count in party_introductions.items()
        }

        return {
            "total_bills_analyzed": total_bills,
            "party_introductions": dict(party_introductions),
            "party_percentages": party_percentages,
            "party_bill_types": {
                party: dict(types) for party, types in party_bill_types.items()
            },
        }

    def analyze_success_rates(self) -> Dict[str, Any]:
        """
        Analyze party success rates for bills becoming law

        Returns:
            Dictionary with success rate statistics
        """
        logger.info("Analyzing party success rates...")

        party_introduced = Counter()
        party_enacted = Counter()

        for bill in self.bills_data:
            sponsors = bill.get("sponsors", [])
            if not sponsors:
                continue

            primary_sponsor = sponsors[0]
            sponsor_party = primary_sponsor.get("party", "Unknown")

            party_introduced[sponsor_party] += 1

            # Check if bill became law
            laws = bill.get("laws", [])
            latest_action = bill.get("latestAction", {}).get("text", "").lower()

            if (
                laws
                or "became public law" in latest_action
                or "became law" in latest_action
            ):
                party_enacted[sponsor_party] += 1

        # Calculate success rates
        success_rates = {}
        for party in party_introduced:
            introduced = party_introduced[party]
            enacted = party_enacted[party]
            success_rate = (enacted / introduced * 100) if introduced > 0 else 0
            success_rates[party] = {
                "introduced": introduced,
                "enacted": enacted,
                "success_rate_percent": round(success_rate, 2),
            }

        return success_rates

    def analyze_cross_party_cosponsorship(
        self, sponsor_data: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Analyze cross-party co-sponsorship patterns

        Args:
            sponsor_data: Dictionary of sponsor/cosponsor data from API

        Returns:
            Dictionary with bipartisanship statistics
        """
        logger.info("Analyzing cross-party co-sponsorship patterns...")

        bipartisan_bills = 0
        total_bills_with_cosponsors = 0
        party_cosponsor_patterns = defaultdict(lambda: defaultdict(int))
        cross_party_counts = Counter()

        for _bill_id, data in sponsor_data.items():
            sponsors = data.get("sponsors", [])
            cosponsors = data.get("cosponsors", [])

            if not sponsors or not cosponsors:
                continue

            total_bills_with_cosponsors += 1

            # Get primary sponsor party
            primary_sponsor = sponsors[0]
            sponsor_party = primary_sponsor.get("party", "Unknown")

            # Analyze cosponsor parties
            cosponsor_parties = []
            for cosponsor in cosponsors:
                party = cosponsor.get("party", "Unknown")
                cosponsor_parties.append(party)
                party_cosponsor_patterns[sponsor_party][party] += 1

            # Check if bill has cross-party support
            unique_parties = set([sponsor_party] + cosponsor_parties)
            if len(unique_parties) > 1:
                bipartisan_bills += 1

                # Count specific cross-party combinations
                parties_sorted = sorted(unique_parties)
                combo = " + ".join(parties_sorted)
                cross_party_counts[combo] += 1

        # Calculate bipartisanship rate
        bipartisan_rate = (
            (bipartisan_bills / total_bills_with_cosponsors * 100)
            if total_bills_with_cosponsors > 0
            else 0
        )

        return {
            "total_bills_with_cosponsors": total_bills_with_cosponsors,
            "bipartisan_bills": bipartisan_bills,
            "bipartisan_rate_percent": round(bipartisan_rate, 2),
            "cross_party_combinations": dict(cross_party_counts),
            "party_cosponsor_patterns": {
                party: dict(patterns)
                for party, patterns in party_cosponsor_patterns.items()
            },
        }

    def generate_analysis_report(
        self, congress: int = 118, max_bills: int = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report

        Args:
            congress: Congress number to analyze
            max_bills: Maximum number of bills to analyze (for testing)

        Returns:
            Complete analysis report
        """
        logger.info(f"Generating analysis report for {congress}th Congress...")

        # Load data
        self.load_member_data(congress)
        bills = self.load_bills_data(congress)

        if max_bills:
            bills = bills[:max_bills]
            logger.info(f"Limited analysis to {len(bills)} bills for testing")

        # Fetch sponsor/cosponsor data
        api = CongressGovAPIv2()
        sponsor_data = api.get_bill_sponsors_batch(bills, str(self.base_dir))

        # Run analyses
        introduction_analysis = self.analyze_party_introduction_rates()
        success_analysis = self.analyze_success_rates()
        bipartisanship_analysis = self.analyze_cross_party_cosponsorship(sponsor_data)

        # Compile report
        report = {
            "metadata": {
                "congress": congress,
                "analysis_date": datetime.now().isoformat(),
                "total_bills_analyzed": len(bills),
                "total_members_loaded": len(self.members_data),
                "bills_with_sponsor_data": len(sponsor_data),
            },
            "party_introduction_rates": introduction_analysis,
            "party_success_rates": success_analysis,
            "cross_party_cosponsorship": bipartisanship_analysis,
            "summary": {
                "most_bills_introduced_by": (
                    max(
                        introduction_analysis["party_introductions"].items(),
                        key=lambda x: x[1],
                    )[0]
                    if introduction_analysis["party_introductions"]
                    else "Unknown"
                ),
                "highest_success_rate_party": (
                    max(
                        success_analysis.items(),
                        key=lambda x: x[1]["success_rate_percent"],
                    )[0]
                    if success_analysis
                    else "Unknown"
                ),
                "bipartisan_rate": bipartisanship_analysis["bipartisan_rate_percent"],
            },
        }

        return report


def save_analysis_results(report: Dict[str, Any], output_path: str):
    """
    Save analysis results to JSON file

    Args:
        report: Analysis report dictionary
        output_path: Output file path
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Analysis results saved to {output_path}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Analyze bill sponsor and co-sponsor patterns in Congress"
    )
    parser.add_argument(
        "--congress",
        type=int,
        default=118,
        help="Congress number to analyze (default: 118)",
    )
    parser.add_argument(
        "--max-bills", type=int, help="Maximum number of bills to analyze (for testing)"
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Base directory for input/output data (default: data)",
    )
    parser.add_argument(
        "--output-file",
        help="Output file path (default: data/analysis/bill_sponsors_analysis.json)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set output file path
    if not args.output_file:
        args.output_file = f"{args.output_dir}/analysis/bill_sponsors_analysis.json"

    # Initialize analyzer
    analyzer = BillSponsorAnalyzer(args.output_dir)

    try:
        # Generate analysis report
        report = analyzer.generate_analysis_report(
            congress=args.congress, max_bills=args.max_bills
        )

        # Save results
        save_analysis_results(report, args.output_file)

        # Print summary
        print(f"\n{'='*60}")
        print("BILL SPONSOR ANALYSIS SUMMARY")
        print(f"{'='*60}")
        print(f"Congress: {report['metadata']['congress']}")
        print(f"Bills Analyzed: {report['metadata']['total_bills_analyzed']}")
        print(
            f"Bills with Sponsor Data: {report['metadata']['bills_with_sponsor_data']}"
        )
        print()

        # Party introduction rates
        intro_data = report["party_introduction_rates"]
        print("PARTY INTRODUCTION RATES:")
        for party, count in intro_data["party_introductions"].items():
            percentage = intro_data["party_percentages"][party]
            print(f"  {party}: {count} bills ({percentage:.1f}%)")
        print()

        # Success rates
        print("PARTY SUCCESS RATES (Bills Becoming Law):")
        for party, data in report["party_success_rates"].items():
            print(
                f"  {party}: {data['enacted']}/{data['introduced']} ({data['success_rate_percent']}%)"
            )
        print()

        # Bipartisanship
        bipartisan_data = report["cross_party_cosponsorship"]
        print("CROSS-PARTY CO-SPONSORSHIP:")
        print(
            f"  Bipartisan Bills: {bipartisan_data['bipartisan_bills']}/{bipartisan_data['total_bills_with_cosponsors']}"
        )
        print(f"  Bipartisan Rate: {bipartisan_data['bipartisan_rate_percent']}%")
        print()

        # Top cross-party combinations
        if bipartisan_data["cross_party_combinations"]:
            print("TOP CROSS-PARTY COMBINATIONS:")
            for combo, count in sorted(
                bipartisan_data["cross_party_combinations"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]:
                print(f"  {combo}: {count} bills")

        print(f"{'='*60}")
        print(f"Analysis results saved to: {args.output_file}")
        print(f"{'='*60}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
