#!/usr/bin/env python3
"""
Bipartisan Cooperation Analysis Script - Analyzes cross-party collaboration patterns in Congress

This script analyzes cosponsorship patterns across party lines, identifies "bridge builder"
members with high cross-party collaboration, tracks temporal trends, and generates network
analysis of bipartisan cooperation.

Outputs data formatted for the /api/v1/trends/bipartisan-cooperation endpoint as specified
in TODO2.md lines 92-117.

Author: Claude Code SuperClaude Framework
Date: September 2024
"""

import argparse
import json
import logging
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bipartisan_cooperation_analysis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class BipartisanCooperationAnalyzer:
    """Analyzes bipartisan cooperation patterns in Congress"""

    def __init__(self, data_dir: str = "../data"):
        """
        Initialize the analyzer

        Args:
            data_dir: Base directory containing data files
        """
        self.data_dir = Path(data_dir).resolve()
        self.bill_sponsors_dir = self.data_dir / "bill_sponsors"
        self.members_dir = self.data_dir / "members" / "118"
        self.congress_bills_dir = self.data_dir / "congress_bills" / "118"
        self.analysis_dir = self.data_dir / "analysis"

        # Create output directory
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.members_data: Dict[str, Dict] = {}
        self.bill_sponsors_data: Dict[str, Dict] = {}
        self.congress_bills_data: Dict[str, Dict] = {}

        # Analysis results
        self.cross_party_cosponsorship: Dict[str, Any] = {}
        self.bipartisan_bills: Set[str] = set()
        self.bridge_builders: List[Dict] = []
        self.policy_area_cooperation: Dict[str, Dict] = {}
        self.temporal_trends: List[Dict] = []
        self.collaboration_network: Dict[Tuple[str, str], int] = defaultdict(int)

        # Analysis parameters
        self.congress_number = 118
        self.min_cosponsors_for_analysis = 2
        self.bridge_builder_threshold = 0.30  # 30% cross-party collaboration rate

        logger.info("Bipartisan Cooperation Analyzer initialized")

    def load_member_data(self) -> None:
        """Load member information from JSON files"""
        logger.info("Loading member data...")

        if not self.members_dir.exists():
            logger.error(f"Members directory not found: {self.members_dir}")
            return

        member_files = list(self.members_dir.glob("*.json"))
        logger.info(f"Found {len(member_files)} member files")

        for member_file in member_files:
            try:
                with open(member_file, encoding="utf-8") as f:
                    member_data = json.load(f)

                # Handle both single member objects and arrays of members
                if isinstance(member_data, list):
                    # Skip array files - these are aggregate files, not individual member profiles
                    logger.debug(f"Skipping array file: {member_file}")
                    continue
                elif isinstance(member_data, dict):
                    bioguide_id = member_data.get("bioguideId")
                    if bioguide_id:
                        self.members_data[bioguide_id] = member_data

            except Exception as e:
                logger.warning(f"Error loading member file {member_file}: {e}")

        logger.info(f"Loaded {len(self.members_data)} member profiles")

    def load_bill_sponsors_data(self) -> None:
        """Load bill sponsor data from JSON files"""
        logger.info("Loading bill sponsors data...")

        if not self.bill_sponsors_dir.exists():
            logger.error(f"Bill sponsors directory not found: {self.bill_sponsors_dir}")
            return

        sponsor_files = list(self.bill_sponsors_dir.glob("*.json"))
        logger.info(f"Found {len(sponsor_files)} bill sponsor files")

        for sponsor_file in sponsor_files:
            try:
                with open(sponsor_file, encoding="utf-8") as f:
                    sponsor_data = json.load(f)

                bill_id = sponsor_data.get("bill_id")
                if bill_id:
                    self.bill_sponsors_data[bill_id] = sponsor_data

            except Exception as e:
                logger.error(f"Error loading sponsor file {sponsor_file}: {e}")

        logger.info(f"Loaded {len(self.bill_sponsors_data)} bill sponsor records")

    def load_congress_bills_data(self) -> None:
        """Load Congress bills data for policy area categorization"""
        logger.info("Loading Congress bills data...")

        if not self.congress_bills_dir.exists():
            logger.error(
                f"Congress bills directory not found: {self.congress_bills_dir}"
            )
            return

        bill_files = list(self.congress_bills_dir.glob("*.json"))
        logger.info(f"Found {len(bill_files)} Congress bill files")

        for bill_file in bill_files:
            try:
                with open(bill_file, encoding="utf-8") as f:
                    bill_data = json.load(f)

                # Create bill ID from congress, type, and number
                congress = bill_data.get("congress", self.congress_number)
                bill_type = bill_data.get("type", "").lower()
                number = bill_data.get("number", "")

                if bill_type and number:
                    bill_id = f"{congress}_{bill_type}_{number}"
                    self.congress_bills_data[bill_id] = bill_data

            except Exception as e:
                logger.error(f"Error loading bill file {bill_file}: {e}")

        logger.info(f"Loaded {len(self.congress_bills_data)} Congress bill records")

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

    def get_member_name(self, bioguide_id: str) -> str:
        """
        Get member's full name

        Args:
            bioguide_id: Member's bioguide ID

        Returns:
            Member's name or 'Unknown'
        """
        member = self.members_data.get(bioguide_id, {})
        return member.get("name", "Unknown")

    def get_bill_policy_area(self, bill_id: str) -> str:
        """
        Get policy area for a bill

        Args:
            bill_id: Bill identifier

        Returns:
            Policy area name or 'Other'
        """
        bill_data = self.congress_bills_data.get(bill_id, {})
        policy_area = bill_data.get("policyArea", {})
        return policy_area.get("name", "Other") if policy_area else "Other"

    def get_bill_date(self, bill_id: str) -> Optional[str]:
        """
        Get introduction date for a bill

        Args:
            bill_id: Bill identifier

        Returns:
            Introduction date string or None
        """
        # First try from Congress bills data
        bill_data = self.congress_bills_data.get(bill_id, {})
        intro_date = bill_data.get("introducedDate")
        if intro_date:
            return intro_date

        # Fallback to sponsor data fetched_at date
        sponsor_data = self.bill_sponsors_data.get(bill_id, {})
        fetched_date = sponsor_data.get("fetched_at")
        if fetched_date:
            # Extract date part only
            return fetched_date.split("T")[0]

        return None

    def analyze_cross_party_cosponsorship(self) -> None:
        """Analyze cross-party cosponsorship patterns"""
        logger.info("Analyzing cross-party cosponsorship patterns...")

        total_bills_analyzed = 0
        bipartisan_bills_count = 0
        republicans_sponsoring_dem_bills = 0
        democrats_sponsoring_rep_bills = 0
        cross_party_collaborations = 0

        for bill_id, sponsor_data in self.bill_sponsors_data.items():
            sponsors = sponsor_data.get("sponsors", [])
            cosponsors = sponsor_data.get("cosponsors", [])

            if not sponsors or len(cosponsors) < self.min_cosponsors_for_analysis:
                continue

            total_bills_analyzed += 1

            # Get primary sponsor party
            primary_sponsor = sponsors[0]
            sponsor_party = primary_sponsor.get("party", "Unknown")
            sponsor_bioguide = primary_sponsor.get("bioguideId", "")

            # Analyze cosponsor parties
            cosponsor_parties = []
            cross_party_cosponsors = []

            for cosponsor in cosponsors:
                cosponsor_party = cosponsor.get("party", "Unknown")
                cosponsor_bioguide = cosponsor.get("bioguideId", "")
                cosponsor_parties.append(cosponsor_party)

                # Track cross-party collaborations
                if (
                    sponsor_party != cosponsor_party
                    and sponsor_party in ["R", "D"]
                    and cosponsor_party in ["R", "D"]
                ):
                    cross_party_cosponsors.append(cosponsor)
                    cross_party_collaborations += 1

                    # Track specific cross-party patterns
                    if sponsor_party == "D" and cosponsor_party == "R":
                        republicans_sponsoring_dem_bills += 1
                    elif sponsor_party == "R" and cosponsor_party == "D":
                        democrats_sponsoring_rep_bills += 1

                    # Update collaboration network
                    if sponsor_bioguide and cosponsor_bioguide:
                        # Store bidirectional collaboration
                        self.collaboration_network[
                            (sponsor_bioguide, cosponsor_bioguide)
                        ] += 1
                        self.collaboration_network[
                            (cosponsor_bioguide, sponsor_bioguide)
                        ] += 1

            # Check if bill has cross-party support
            unique_parties = set([sponsor_party] + cosponsor_parties)
            has_bipartisan_support = (
                "R" in unique_parties
                and "D" in unique_parties
                and len(cross_party_cosponsors) > 0
            )

            if has_bipartisan_support:
                bipartisan_bills_count += 1
                self.bipartisan_bills.add(bill_id)

        # Calculate overall metrics
        overall_bipartisan_rate = (
            (bipartisan_bills_count / total_bills_analyzed)
            if total_bills_analyzed > 0
            else 0.0
        )
        mutual_cosponsorship_rate = min(
            republicans_sponsoring_dem_bills, democrats_sponsoring_rep_bills
        ) / max(republicans_sponsoring_dem_bills + democrats_sponsoring_rep_bills, 1)

        self.cross_party_cosponsorship = {
            "overall_bipartisan_rate": round(overall_bipartisan_rate, 4),
            "bipartisan_bills_count": bipartisan_bills_count,
            "total_bills_analyzed": total_bills_analyzed,
            "republicans_sponsoring_dem_bills": republicans_sponsoring_dem_bills,
            "democrats_sponsoring_rep_bills": democrats_sponsoring_rep_bills,
            "mutual_cosponsorship_rate": round(mutual_cosponsorship_rate, 4),
            "total_cross_party_collaborations": cross_party_collaborations,
        }

        logger.info(
            f"Analyzed {total_bills_analyzed} bills, found {bipartisan_bills_count} bipartisan bills"
        )

    def identify_bridge_builders(self) -> None:
        """Identify members with high cross-party collaboration scores"""
        logger.info("Identifying bridge builder members...")

        member_collaboration_stats = defaultdict(
            lambda: {
                "total_collaborations": 0,
                "cross_party_collaborations": 0,
                "bills_with_cross_party_support": 0,
                "collaborating_with": set(),
            }
        )

        # Analyze collaboration patterns for each member
        for _bill_id, sponsor_data in self.bill_sponsors_data.items():
            sponsors = sponsor_data.get("sponsors", [])
            cosponsors = sponsor_data.get("cosponsors", [])

            if not sponsors or not cosponsors:
                continue

            # Process primary sponsor
            primary_sponsor = sponsors[0]
            sponsor_bioguide = primary_sponsor.get("bioguideId", "")
            sponsor_party = primary_sponsor.get("party", "Unknown")

            if sponsor_bioguide and sponsor_party in ["R", "D"]:
                has_cross_party_support = False

                for cosponsor in cosponsors:
                    cosponsor_bioguide = cosponsor.get("bioguideId", "")
                    cosponsor_party = cosponsor.get("party", "Unknown")

                    if cosponsor_bioguide:
                        member_collaboration_stats[sponsor_bioguide][
                            "total_collaborations"
                        ] += 1

                        if sponsor_party != cosponsor_party and cosponsor_party in [
                            "R",
                            "D",
                        ]:
                            member_collaboration_stats[sponsor_bioguide][
                                "cross_party_collaborations"
                            ] += 1
                            member_collaboration_stats[sponsor_bioguide][
                                "collaborating_with"
                            ].add(cosponsor_bioguide)
                            has_cross_party_support = True

                if has_cross_party_support:
                    member_collaboration_stats[sponsor_bioguide][
                        "bills_with_cross_party_support"
                    ] += 1

            # Process cosponsors for cross-party collaboration
            for cosponsor in cosponsors:
                cosponsor_bioguide = cosponsor.get("bioguideId", "")
                cosponsor_party = cosponsor.get("party", "Unknown")

                if cosponsor_bioguide and cosponsor_party in ["R", "D"]:
                    member_collaboration_stats[cosponsor_bioguide][
                        "total_collaborations"
                    ] += 1

                    if sponsor_party != cosponsor_party and sponsor_party in ["R", "D"]:
                        member_collaboration_stats[cosponsor_bioguide][
                            "cross_party_collaborations"
                        ] += 1
                        member_collaboration_stats[cosponsor_bioguide][
                            "collaborating_with"
                        ].add(sponsor_bioguide)

        # Calculate bipartisan scores and identify bridge builders
        bridge_builders = []

        for member_bioguide, stats in member_collaboration_stats.items():
            if stats["total_collaborations"] < 5:  # Minimum activity threshold
                continue

            bipartisan_score = (
                stats["cross_party_collaborations"] / stats["total_collaborations"]
                if stats["total_collaborations"] > 0
                else 0.0
            )

            if bipartisan_score >= self.bridge_builder_threshold:
                member_name = self.get_member_name(member_bioguide)
                member_party = self.get_member_party(member_bioguide)

                bridge_builders.append(
                    {
                        "name": member_name,
                        "party": member_party,
                        "bipartisan_score": round(bipartisan_score, 4),
                        "bills_crossed": stats["cross_party_collaborations"],
                        "total_collaborations": stats["total_collaborations"],
                        "unique_cross_party_partners": len(stats["collaborating_with"]),
                    }
                )

        # Sort by bipartisan score
        bridge_builders.sort(key=lambda x: x["bipartisan_score"], reverse=True)
        self.bridge_builders = bridge_builders[:20]  # Top 20 bridge builders

        logger.info(f"Identified {len(self.bridge_builders)} bridge builder members")

    def analyze_policy_area_cooperation(self) -> None:
        """Analyze bipartisan cooperation by policy area"""
        logger.info("Analyzing policy area cooperation patterns...")

        policy_area_stats = defaultdict(
            lambda: {"total_bills": 0, "bipartisan_bills": 0, "bipartisan_rate": 0.0}
        )

        for bill_id in self.bill_sponsors_data:
            policy_area = self.get_bill_policy_area(bill_id)
            policy_area_stats[policy_area]["total_bills"] += 1

            if bill_id in self.bipartisan_bills:
                policy_area_stats[policy_area]["bipartisan_bills"] += 1

        # Calculate bipartisan rates
        top_bipartisan_areas = []

        for policy_area, stats in policy_area_stats.items():
            if stats["total_bills"] >= 5:  # Minimum bill count for meaningful analysis
                bipartisan_rate = (
                    stats["bipartisan_bills"] / stats["total_bills"]
                    if stats["total_bills"] > 0
                    else 0.0
                )
                stats["bipartisan_rate"] = round(bipartisan_rate, 4)

                top_bipartisan_areas.append(
                    {
                        "policy_area": policy_area,
                        "bipartisan_rate": bipartisan_rate,
                        "bill_count": stats["total_bills"],
                        "bipartisan_count": stats["bipartisan_bills"],
                    }
                )

        # Sort by bipartisan rate
        top_bipartisan_areas.sort(key=lambda x: x["bipartisan_rate"], reverse=True)
        self.policy_area_cooperation = {
            "top_bipartisan_areas": top_bipartisan_areas[:10],
            "total_policy_areas_analyzed": len(top_bipartisan_areas),
        }

        logger.info(f"Analyzed {len(top_bipartisan_areas)} policy areas")

    def analyze_temporal_trends(self) -> None:
        """Analyze temporal trends in bipartisan cooperation"""
        logger.info("Analyzing temporal trends in bipartisan cooperation...")

        # Group bills by month
        monthly_stats = defaultdict(
            lambda: {"total_bills": 0, "bipartisan_bills": 0, "bipartisan_rate": 0.0}
        )

        for bill_id in self.bill_sponsors_data:
            bill_date = self.get_bill_date(bill_id)
            if not bill_date:
                continue

            try:
                # Extract year-month
                year_month = bill_date[:7]  # "2023-01" format
                monthly_stats[year_month]["total_bills"] += 1

                if bill_id in self.bipartisan_bills:
                    monthly_stats[year_month]["bipartisan_bills"] += 1

            except (ValueError, IndexError):
                logger.warning(f"Invalid date format for bill {bill_id}: {bill_date}")
                continue

        # Calculate monthly trends
        monthly_trends = []

        for month, stats in sorted(monthly_stats.items()):
            if stats["total_bills"] >= 3:  # Minimum for meaningful trend
                bipartisan_rate = (
                    stats["bipartisan_bills"] / stats["total_bills"]
                    if stats["total_bills"] > 0
                    else 0.0
                )

                monthly_trends.append(
                    {
                        "month": month,
                        "bipartisan_rate": round(bipartisan_rate, 4),
                        "bill_count": stats["total_bills"],
                        "bipartisan_count": stats["bipartisan_bills"],
                    }
                )

        self.temporal_trends = monthly_trends
        logger.info(f"Generated {len(monthly_trends)} monthly trend data points")

    def generate_cooperation_metrics(self) -> Dict[str, Any]:
        """Generate comprehensive cooperation metrics matching TODO2.md format"""
        logger.info("Generating comprehensive cooperation metrics...")

        cooperation_metrics = {
            "overall_bipartisan_rate": self.cross_party_cosponsorship.get(
                "overall_bipartisan_rate", 0.0
            ),
            "bipartisan_bills_count": self.cross_party_cosponsorship.get(
                "bipartisan_bills_count", 0
            ),
            "top_bipartisan_areas": self.policy_area_cooperation.get(
                "top_bipartisan_areas", []
            )[:5],
            "cross_party_cosponsorship": {
                "republicans_sponsoring_dem_bills": self.cross_party_cosponsorship.get(
                    "republicans_sponsoring_dem_bills", 0
                ),
                "democrats_sponsoring_rep_bills": self.cross_party_cosponsorship.get(
                    "democrats_sponsoring_rep_bills", 0
                ),
                "mutual_cosponsorship_rate": self.cross_party_cosponsorship.get(
                    "mutual_cosponsorship_rate", 0.0
                ),
            },
            "bridge_builders": self.bridge_builders[:10],  # Top 10 for API response
            "monthly_trends": (
                self.temporal_trends[-12:]
                if len(self.temporal_trends) > 12
                else self.temporal_trends
            ),  # Last 12 months
        }

        return cooperation_metrics

    def generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive bipartisan cooperation analysis report"""
        logger.info("Generating comprehensive analysis report...")

        cooperation_metrics = self.generate_cooperation_metrics()

        # Calculate additional insights
        total_bridge_builders = len(self.bridge_builders)
        avg_bipartisan_score = (
            statistics.mean([bb["bipartisan_score"] for bb in self.bridge_builders])
            if self.bridge_builders
            else 0.0
        )

        # Party distribution of bridge builders
        party_distribution = Counter([bb["party"] for bb in self.bridge_builders])

        report = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "congress": self.congress_number,
                "data_source": "Congress API Bill Sponsors + Member Data",
                "total_bills_analyzed": self.cross_party_cosponsorship.get(
                    "total_bills_analyzed", 0
                ),
                "total_members_analyzed": len(self.members_data),
                "min_cosponsors_threshold": self.min_cosponsors_for_analysis,
                "bridge_builder_threshold": self.bridge_builder_threshold,
            },
            "congress": self.congress_number,
            "cooperation_metrics": cooperation_metrics,
            "summary_statistics": {
                "total_cross_party_collaborations": self.cross_party_cosponsorship.get(
                    "total_cross_party_collaborations", 0
                ),
                "bridge_builders_identified": total_bridge_builders,
                "average_bridge_builder_score": round(avg_bipartisan_score, 4),
                "policy_areas_analyzed": self.policy_area_cooperation.get(
                    "total_policy_areas_analyzed", 0
                ),
                "temporal_data_points": len(self.temporal_trends),
                "bridge_builder_party_distribution": dict(party_distribution),
            },
            "insights": self._generate_insights(),
        }

        return report

    def _generate_insights(self) -> Dict[str, str]:
        """Generate textual insights from the bipartisan analysis"""
        insights = {}

        # Overall cooperation insight
        bipartisan_rate = self.cross_party_cosponsorship.get(
            "overall_bipartisan_rate", 0.0
        )
        insights["overall_cooperation"] = (
            f"Overall bipartisan cooperation rate is {bipartisan_rate:.1%}, "
            f"with {self.cross_party_cosponsorship.get('bipartisan_bills_count', 0)} bills "
            f"having cross-party support"
        )

        # Top policy area insight
        top_areas = self.policy_area_cooperation.get("top_bipartisan_areas", [])
        if top_areas:
            top_area = top_areas[0]
            insights["top_policy_area"] = (
                f"'{top_area['policy_area']}' shows highest bipartisan cooperation "
                f"at {top_area['bipartisan_rate']:.1%} rate with {top_area['bipartisan_count']} "
                f"bipartisan bills out of {top_area['bill_count']} total"
            )

        # Bridge builders insight
        if self.bridge_builders:
            top_bridge_builder = self.bridge_builders[0]
            insights["top_bridge_builder"] = (
                f"{top_bridge_builder['name']} ({top_bridge_builder['party']}) "
                f"leads in bipartisan collaboration with {top_bridge_builder['bipartisan_score']:.1%} "
                f"cross-party cooperation rate"
            )

        # Temporal trend insight
        if len(self.temporal_trends) >= 2:
            recent_trend = self.temporal_trends[-2:]
            trend_direction = (
                "increasing"
                if recent_trend[-1]["bipartisan_rate"]
                > recent_trend[-2]["bipartisan_rate"]
                else "decreasing"
            )
            insights["recent_trend"] = (
                f"Bipartisan cooperation is {trend_direction} in recent months, "
                f"with {recent_trend[-1]['bipartisan_rate']:.1%} rate in {recent_trend[-1]['month']}"
            )

        return insights

    def save_analysis_report(self, report: Dict[str, Any]) -> None:
        """Save the comprehensive analysis report"""
        report_file = self.analysis_dir / "bipartisan_cooperation_analysis.json"

        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Analysis report saved to {report_file}")

        except Exception as e:
            logger.error(f"Error saving analysis report: {e}")

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run the complete bipartisan cooperation analysis"""
        logger.info("Starting comprehensive bipartisan cooperation analysis...")

        start_time = time.time()

        try:
            # Load data
            self.load_member_data()
            self.load_bill_sponsors_data()
            self.load_congress_bills_data()

            if not self.members_data:
                logger.error("No member data loaded. Cannot proceed with analysis.")
                return {}

            if not self.bill_sponsors_data:
                logger.error(
                    "No bill sponsors data loaded. Cannot proceed with analysis."
                )
                return {}

            # Perform analysis
            self.analyze_cross_party_cosponsorship()
            self.identify_bridge_builders()
            self.analyze_policy_area_cooperation()
            self.analyze_temporal_trends()

            # Generate report
            report = self.generate_analysis_report()
            self.save_analysis_report(report)

            # Performance summary
            end_time = time.time()
            duration = end_time - start_time

            logger.info(f"Analysis completed in {duration:.2f} seconds")
            logger.info(
                f"Analyzed {len(self.bill_sponsors_data)} bills and {len(self.members_data)} members"
            )
            logger.info(
                f"Identified {len(self.bridge_builders)} bridge builder members"
            )

            # Print summary statistics
            self._print_summary_statistics(report)

            return report

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            raise

    def _print_summary_statistics(self, report: Dict[str, Any]) -> None:
        """Print summary statistics to console"""
        print("\n" + "=" * 70)
        print("BIPARTISAN COOPERATION ANALYSIS SUMMARY")
        print("=" * 70)

        metadata = report.get("metadata", {})
        cooperation_metrics = report.get("cooperation_metrics", {})
        summary_stats = report.get("summary_statistics", {})

        print(f"Congress: {metadata.get('congress', 'N/A')}")
        print(f"Analysis Date: {metadata.get('analysis_date', 'N/A')[:10]}")
        print(f"Bills Analyzed: {metadata.get('total_bills_analyzed', 0)}")
        print(f"Members Analyzed: {metadata.get('total_members_analyzed', 0)}")

        print("\nBIPARTISAN COOPERATION METRICS:")
        print(
            f"  Overall Bipartisan Rate: {cooperation_metrics.get('overall_bipartisan_rate', 0):.1%}"
        )
        print(
            f"  Bipartisan Bills Count: {cooperation_metrics.get('bipartisan_bills_count', 0)}"
        )

        cross_party = cooperation_metrics.get("cross_party_cosponsorship", {})
        print(
            f"  Republicans Supporting Dem Bills: {cross_party.get('republicans_sponsoring_dem_bills', 0)}"
        )
        print(
            f"  Democrats Supporting Rep Bills: {cross_party.get('democrats_sponsoring_rep_bills', 0)}"
        )
        print(
            f"  Mutual Cosponsorship Rate: {cross_party.get('mutual_cosponsorship_rate', 0):.1%}"
        )

        print(
            f"\nBRIDGE BUILDERS IDENTIFIED: {summary_stats.get('bridge_builders_identified', 0)}"
        )
        bridge_builders = cooperation_metrics.get("bridge_builders", [])
        if bridge_builders:
            print("  Top 5 Bridge Builders:")
            for i, bb in enumerate(bridge_builders[:5], 1):
                print(
                    f"    {i}. {bb['name']} ({bb['party']}) - {bb['bipartisan_score']:.1%}"
                )

        print("\nTOP BIPARTISAN POLICY AREAS:")
        top_areas = cooperation_metrics.get("top_bipartisan_areas", [])
        if top_areas:
            for i, area in enumerate(top_areas[:5], 1):
                print(
                    f"  {i}. {area['policy_area']} - {area['bipartisan_rate']:.1%} ({area['bipartisan_count']}/{area['bill_count']} bills)"
                )

        print(
            f"\nTEMPORAL TRENDS: {len(cooperation_metrics.get('monthly_trends', []))} monthly data points"
        )
        trends = cooperation_metrics.get("monthly_trends", [])
        if trends:
            recent_months = trends[-3:]
            print("  Recent Monthly Trends:")
            for trend in recent_months:
                print(
                    f"    {trend['month']}: {trend['bipartisan_rate']:.1%} ({trend['bipartisan_count']}/{trend['bill_count']} bills)"
                )

        print("\n" + "=" * 70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Analyze bipartisan cooperation patterns in Congress"
    )
    parser.add_argument(
        "--data-dir",
        default="../data",
        help="Base directory for input data (default: ../data)",
    )
    parser.add_argument(
        "--congress",
        type=int,
        default=118,
        help="Congress number to analyze (default: 118)",
    )
    parser.add_argument(
        "--min-cosponsors",
        type=int,
        default=2,
        help="Minimum cosponsors for analysis (default: 2)",
    )
    parser.add_argument(
        "--bridge-builder-threshold",
        type=float,
        default=0.30,
        help="Minimum bipartisan score for bridge builders (default: 0.30)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize analyzer
    analyzer = BipartisanCooperationAnalyzer(args.data_dir)
    analyzer.congress_number = args.congress
    analyzer.min_cosponsors_for_analysis = args.min_cosponsors
    analyzer.bridge_builder_threshold = args.bridge_builder_threshold

    try:
        # Run analysis
        report = analyzer.run_full_analysis()

        if report:
            print("\nAnalysis complete!")
            print(
                f"Results saved to: {analyzer.analysis_dir / 'bipartisan_cooperation_analysis.json'}"
            )
            print("Log file: bipartisan_cooperation_analysis.log")
        else:
            print("\nAnalysis failed - check logs for details")

    except Exception as e:
        logger.error(f"Analysis execution failed: {e}")
        raise


if __name__ == "__main__":
    main()
