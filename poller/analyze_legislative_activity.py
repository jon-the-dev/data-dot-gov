#!/usr/bin/env python3
"""
Legislative Activity Analysis Script - Analyzes legislative activity patterns and trends
Generates comprehensive data for the legislative activity endpoint covering sponsorship patterns,
bipartisan cooperation, monthly trends, and policy area distributions.
"""

import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LegislativeActivityAnalyzer:
    """Analyzes legislative activity patterns including sponsorship trends and bipartisan cooperation"""

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

    def load_sponsor_data(self) -> Dict[str, Dict]:
        """
        Load sponsor/cosponsor data from the bill_sponsors directory

        Returns:
            Dictionary mapping bill_id to sponsor data
        """
        logger.info("Loading sponsor data...")

        sponsors_dir = self.base_dir / "bill_sponsors"
        if not sponsors_dir.exists():
            logger.error(f"Sponsors directory not found: {sponsors_dir}")
            return {}

        sponsors = {}
        for sponsor_file in sponsors_dir.glob("*.json"):
            try:
                with open(sponsor_file) as f:
                    sponsor_data = json.load(f)
                    bill_id = sponsor_data.get("bill_id")
                    if bill_id:
                        sponsors[bill_id] = sponsor_data
            except Exception as e:
                logger.warning(f"Failed to load sponsor file {sponsor_file}: {e}")

        logger.info(f"Loaded sponsor data for {len(sponsors)} bills")
        self.sponsor_data = sponsors
        return sponsors

    def get_member_party(self, bioguide_id: str) -> str:
        """
        Get party affiliation for a member

        Args:
            bioguide_id: Member's bioguide ID

        Returns:
            Party code (Republican, Democratic, Independent, etc.) or 'Unknown'
        """
        member = self.members_data.get(bioguide_id, {})
        return member.get("party", "Unknown")

    def get_member_name(self, bioguide_id: str) -> str:
        """
        Get member's full name

        Args:
            bioguide_id: Member's bioguide ID

        Returns:
            Member's full name or bioguide_id if not found
        """
        member = self.members_data.get(bioguide_id, {})
        return member.get("name", bioguide_id)

    def normalize_party_name(self, party: str) -> str:
        """
        Normalize party names to standard format

        Args:
            party: Raw party name

        Returns:
            Normalized party name
        """
        party_mapping = {
            "R": "Republican",
            "D": "Democratic",
            "I": "Independent",
            "Republican": "Republican",
            "Democratic": "Democratic",
            "Independent": "Independent",
        }
        return party_mapping.get(party, party)

    def parse_date_to_month(self, date_str: str) -> Optional[str]:
        """
        Parse date string and return YYYY-MM format

        Args:
            date_str: Date string in various formats

        Returns:
            YYYY-MM formatted string or None if parsing fails
        """
        try:
            if date_str:
                # Handle different date formats
                if len(date_str) >= 10:  # YYYY-MM-DD format
                    return date_str[:7]  # Return YYYY-MM
                elif len(date_str) >= 7:  # YYYY-MM format
                    return date_str
        except Exception as e:
            logger.debug(f"Failed to parse date {date_str}: {e}")
        return None

    def analyze_sponsorship_patterns(self) -> Dict[str, Any]:
        """
        Analyze sponsorship patterns by party

        Returns:
            Dictionary with sponsorship statistics by party
        """
        logger.info("Analyzing sponsorship patterns by party...")

        party_stats = defaultdict(
            lambda: {
                "total_bills_sponsored": 0,
                "solo_sponsored": 0,
                "bipartisan_sponsored": 0,
                "total_cosponsors": 0,
                "bills_with_cosponsors": 0,
                "policy_areas": Counter(),
            }
        )

        # Merge bill data with sponsor data
        bill_lookup = {}
        for bill in self.bills_data:
            # Create both uppercase and lowercase versions to match sponsor data format
            bill_id_upper = f"{bill.get('congress')}_{bill.get('type', '').upper()}_{bill.get('number')}"
            bill_id_lower = f"{bill.get('congress')}_{bill.get('type', '').lower()}_{bill.get('number')}"
            bill_lookup[bill_id_upper] = bill
            bill_lookup[bill_id_lower] = bill

        for bill_id, sponsor_data in self.sponsor_data.items():
            sponsors = sponsor_data.get("sponsors", [])
            cosponsors = sponsor_data.get("cosponsors", [])

            if not sponsors:
                continue

            # Get primary sponsor
            primary_sponsor = sponsors[0]
            sponsor_bioguide = primary_sponsor.get("bioguideId")
            sponsor_party = self.normalize_party_name(
                self.get_member_party(sponsor_bioguide)
            )

            if sponsor_party == "Unknown":
                # Try to get party from sponsor data itself
                sponsor_party = self.normalize_party_name(
                    primary_sponsor.get("party", "Unknown")
                )

            # Skip if still unknown
            if sponsor_party == "Unknown":
                continue

            # Update basic stats
            party_stats[sponsor_party]["total_bills_sponsored"] += 1

            # Count cosponsors
            cosponsor_count = len(cosponsors)
            party_stats[sponsor_party]["total_cosponsors"] += cosponsor_count

            if cosponsor_count > 0:
                party_stats[sponsor_party]["bills_with_cosponsors"] += 1

            # Check if bill has cross-party support (bipartisan)
            cosponsor_parties = set()
            for cosponsor in cosponsors:
                cosponsor_bioguide = cosponsor.get("bioguideId")
                cosponsor_party = self.normalize_party_name(
                    self.get_member_party(cosponsor_bioguide)
                )

                if cosponsor_party == "Unknown":
                    cosponsor_party = self.normalize_party_name(
                        cosponsor.get("party", "Unknown")
                    )

                if cosponsor_party != "Unknown":
                    cosponsor_parties.add(cosponsor_party)

            # Check if bipartisan (sponsor party + different cosponsor parties)
            all_parties = {sponsor_party} | cosponsor_parties
            if len(all_parties) > 1:
                party_stats[sponsor_party]["bipartisan_sponsored"] += 1
            else:
                party_stats[sponsor_party]["solo_sponsored"] += 1

            # Get policy area from bill data
            bill_data = bill_lookup.get(bill_id)
            if bill_data:
                policy_area = bill_data.get("policyArea", {}).get("name")
                if policy_area:
                    party_stats[sponsor_party]["policy_areas"][policy_area] += 1

        # Calculate averages and convert to regular dict
        result = {}
        for party, stats in party_stats.items():
            avg_cosponsors = (
                stats["total_cosponsors"] / stats["total_bills_sponsored"]
                if stats["total_bills_sponsored"] > 0
                else 0
            )

            # Get top 3 policy areas
            top_policy_areas = [
                area for area, count in stats["policy_areas"].most_common(3)
            ]

            result[party] = {
                "total_bills_sponsored": stats["total_bills_sponsored"],
                "solo_sponsored": stats["solo_sponsored"],
                "bipartisan_sponsored": stats["bipartisan_sponsored"],
                "avg_cosponsors": round(avg_cosponsors, 1),
                "top_policy_areas": top_policy_areas,
            }

        return result

    def analyze_monthly_trends(self) -> List[Dict[str, Any]]:
        """
        Analyze monthly sponsorship trends by party

        Returns:
            List of monthly trend data
        """
        logger.info("Analyzing monthly sponsorship trends...")

        monthly_data = defaultdict(lambda: defaultdict(int))

        # Merge bill data with sponsor data to get introduction dates
        bill_lookup = {}
        for bill in self.bills_data:
            # Create both uppercase and lowercase versions to match sponsor data format
            bill_id_upper = f"{bill.get('congress')}_{bill.get('type', '').upper()}_{bill.get('number')}"
            bill_id_lower = f"{bill.get('congress')}_{bill.get('type', '').lower()}_{bill.get('number')}"
            bill_lookup[bill_id_upper] = bill
            bill_lookup[bill_id_lower] = bill

        for bill_id, sponsor_data in self.sponsor_data.items():
            sponsors = sponsor_data.get("sponsors", [])

            if not sponsors:
                continue

            # Get bill introduction date
            bill_data = bill_lookup.get(bill_id)
            if not bill_data:
                continue

            intro_date = bill_data.get("introducedDate")
            month = self.parse_date_to_month(intro_date)
            if not month:
                continue

            # Get sponsor party
            primary_sponsor = sponsors[0]
            sponsor_bioguide = primary_sponsor.get("bioguideId")
            sponsor_party = self.normalize_party_name(
                self.get_member_party(sponsor_bioguide)
            )

            if sponsor_party == "Unknown":
                sponsor_party = self.normalize_party_name(
                    primary_sponsor.get("party", "Unknown")
                )

            if sponsor_party != "Unknown":
                monthly_data[month][sponsor_party] += 1

        # Convert to sorted list format
        trends = []
        for month in sorted(monthly_data.keys()):
            trend_entry = {"month": month}
            for party, count in monthly_data[month].items():
                party_key = f"{party.lower()}_bills"
                trend_entry[party_key] = count
            trends.append(trend_entry)

        return trends

    def analyze_top_sponsors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Identify most active sponsors

        Args:
            limit: Maximum number of sponsors to return

        Returns:
            List of top sponsors with their activity
        """
        logger.info(f"Analyzing top {limit} sponsors...")

        sponsor_activity = Counter()
        sponsor_info = {}

        for _bill_id, sponsor_data in self.sponsor_data.items():
            sponsors = sponsor_data.get("sponsors", [])

            if not sponsors:
                continue

            primary_sponsor = sponsors[0]
            sponsor_bioguide = primary_sponsor.get("bioguideId")

            if not sponsor_bioguide:
                continue

            sponsor_activity[sponsor_bioguide] += 1

            # Store sponsor info
            if sponsor_bioguide not in sponsor_info:
                sponsor_party = self.normalize_party_name(
                    self.get_member_party(sponsor_bioguide)
                )
                if sponsor_party == "Unknown":
                    sponsor_party = self.normalize_party_name(
                        primary_sponsor.get("party", "Unknown")
                    )

                sponsor_info[sponsor_bioguide] = {
                    "name": self.get_member_name(sponsor_bioguide),
                    "party": (
                        sponsor_party[0] if sponsor_party != "Unknown" else "U"
                    ),  # First letter for display
                }

        # Get top sponsors
        top_sponsors = []
        for bioguide_id, bill_count in sponsor_activity.most_common(limit):
            info = sponsor_info.get(bioguide_id, {})
            top_sponsors.append(
                {
                    "name": info.get("name", bioguide_id),
                    "party": info.get("party", "U"),
                    "bills_sponsored": bill_count,
                }
            )

        return top_sponsors

    def calculate_bipartisan_rate(self) -> float:
        """
        Calculate overall bipartisan rate

        Returns:
            Bipartisan rate as decimal
        """
        logger.info("Calculating bipartisan rate...")

        total_bills = 0
        bipartisan_bills = 0

        for _bill_id, sponsor_data in self.sponsor_data.items():
            sponsors = sponsor_data.get("sponsors", [])
            cosponsors = sponsor_data.get("cosponsors", [])

            if not sponsors:
                continue

            total_bills += 1

            # Get sponsor party
            primary_sponsor = sponsors[0]
            sponsor_bioguide = primary_sponsor.get("bioguideId")
            sponsor_party = self.normalize_party_name(
                self.get_member_party(sponsor_bioguide)
            )

            if sponsor_party == "Unknown":
                sponsor_party = self.normalize_party_name(
                    primary_sponsor.get("party", "Unknown")
                )

            # Get cosponsor parties
            cosponsor_parties = set()
            for cosponsor in cosponsors:
                cosponsor_bioguide = cosponsor.get("bioguideId")
                cosponsor_party = self.normalize_party_name(
                    self.get_member_party(cosponsor_bioguide)
                )

                if cosponsor_party == "Unknown":
                    cosponsor_party = self.normalize_party_name(
                        cosponsor.get("party", "Unknown")
                    )

                if cosponsor_party != "Unknown":
                    cosponsor_parties.add(cosponsor_party)

            # Check if bipartisan
            all_parties = {sponsor_party} | cosponsor_parties
            if len(all_parties) > 1:
                bipartisan_bills += 1

        return round(bipartisan_bills / total_bills, 2) if total_bills > 0 else 0.0

    def generate_analysis_report(self, congress: int = 118) -> Dict[str, Any]:
        """
        Generate comprehensive legislative activity analysis report

        Args:
            congress: Congress number to analyze

        Returns:
            Complete analysis report matching TODO2.md format
        """
        logger.info(
            f"Generating legislative activity analysis for {congress}th Congress..."
        )

        # Load all data
        self.load_member_data(congress)
        self.load_bills_data(congress)
        self.load_sponsor_data()

        # Run analyses
        sponsorship_patterns = self.analyze_sponsorship_patterns()
        monthly_trends = self.analyze_monthly_trends()
        top_sponsors = self.analyze_top_sponsors()
        bipartisan_rate = self.calculate_bipartisan_rate()

        # Compile report in TODO2.md format
        report = {
            "congress": congress,
            "generated_at": datetime.now().isoformat(),
            "sponsorship_patterns": {
                "by_party": sponsorship_patterns,
                "trends": {
                    "monthly_activity": monthly_trends,
                    "bipartisan_rate": bipartisan_rate,
                    "most_active_sponsors": top_sponsors,
                },
            },
            "metadata": {
                "total_bills_analyzed": len(self.bills_data),
                "total_sponsors_analyzed": len(self.sponsor_data),
                "total_members_loaded": len(self.members_data),
                "analysis_date": datetime.now().isoformat(),
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
        description="Analyze legislative activity patterns and trends"
    )
    parser.add_argument(
        "--congress",
        type=int,
        default=118,
        help="Congress number to analyze (default: 118)",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Base directory for input/output data (default: data)",
    )
    parser.add_argument(
        "--output-file",
        help="Output file path (default: data/analysis/legislative_activity_analysis.json)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set output file path
    if not args.output_file:
        args.output_file = (
            f"{args.output_dir}/analysis/legislative_activity_analysis.json"
        )

    # Initialize analyzer
    analyzer = LegislativeActivityAnalyzer(args.output_dir)

    try:
        # Generate analysis report
        report = analyzer.generate_analysis_report(congress=args.congress)

        # Save results
        save_analysis_results(report, args.output_file)

        # Print summary
        print(f"\n{'='*70}")
        print("LEGISLATIVE ACTIVITY ANALYSIS SUMMARY")
        print(f"{'='*70}")
        print(f"Congress: {report['congress']}")
        print(f"Bills Analyzed: {report['metadata']['total_bills_analyzed']}")
        print(
            f"Bills with Sponsor Data: {report['metadata']['total_sponsors_analyzed']}"
        )
        print()

        # Party sponsorship patterns
        print("PARTY SPONSORSHIP PATTERNS:")
        patterns = report["sponsorship_patterns"]["by_party"]
        for party, stats in patterns.items():
            print(f"  {party}:")
            print(f"    Total Bills Sponsored: {stats['total_bills_sponsored']}")
            print(f"    Solo Sponsored: {stats['solo_sponsored']}")
            print(f"    Bipartisan Sponsored: {stats['bipartisan_sponsored']}")
            print(f"    Avg Cosponsors: {stats['avg_cosponsors']}")
            print(f"    Top Policy Areas: {', '.join(stats['top_policy_areas'])}")
            print()

        # Overall trends
        trends = report["sponsorship_patterns"]["trends"]
        print("OVERALL TRENDS:")
        print(f"  Bipartisan Rate: {trends['bipartisan_rate']:.1%}")
        print(f"  Monthly Data Points: {len(trends['monthly_activity'])}")
        print()

        # Top sponsors
        print("MOST ACTIVE SPONSORS:")
        for i, sponsor in enumerate(trends["most_active_sponsors"][:5], 1):
            print(
                f"  {i}. {sponsor['name']} ({sponsor['party']}): {sponsor['bills_sponsored']} bills"
            )

        print(f"{'='*70}")
        print(f"Analysis results saved to: {args.output_file}")
        print(f"{'='*70}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
