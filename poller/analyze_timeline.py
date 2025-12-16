#!/usr/bin/env python3
"""
Timeline Analysis Script for Congressional Activity

This script analyzes temporal patterns in congressional activity including:
- Party activity levels by month/quarter
- Bill introduction rate trends
- Success rates over time
- Pre-election vs post-election activity
- Legislative productivity cycles
- Seasonal patterns in legislation

Author: Congressional Analysis System
Date: 2024
"""

import json
import logging
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BillData:
    """Data class for bill information."""

    bill_id: str
    introduced_date: str
    congress: int
    origin_chamber: str
    bill_type: str
    party: str
    sponsor_name: str
    sponsor_state: str
    title: str
    latest_action_date: str
    latest_action_text: str
    became_law: bool = False
    committee_count: int = 0
    cosponsor_count: int = 0
    policy_area: str = ""


@dataclass
class TimelineMetrics:
    """Data class for timeline analysis metrics."""

    date: str
    period_type: str  # monthly, quarterly, yearly
    party_counts: Dict[str, int]
    total_bills: int
    success_rate: float
    avg_cosponsors: float
    chamber_breakdown: Dict[str, int]
    policy_areas: Dict[str, int]
    election_cycle_phase: str


class TimelineAnalyzer:
    """Comprehensive timeline analysis for congressional activity."""

    def __init__(self, data_dir: str = "data"):
        """Initialize the timeline analyzer."""
        self.data_dir = Path(data_dir)
        self.bills_dir = self.data_dir / "congress_bills"
        self.members_dir = self.data_dir / "members"
        self.output_dir = self.data_dir / "timeline_analysis"
        self.analysis_dir = self.data_dir / "analysis"

        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.analysis_dir.mkdir(exist_ok=True)

        # Setup logging
        self.setup_logging()

        # Data storage
        self.bills_data: List[BillData] = []
        self.members_data: Dict[str, Dict] = {}
        self.timeline_data: List[TimelineMetrics] = []

        # Analysis parameters
        self.election_years = {2020, 2022, 2024, 2026}  # Even years are election years

        self.logger.info("Timeline analyzer initialized")

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("timeline_analysis.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def load_member_data(self) -> None:
        """Load member data from JSON files."""
        self.logger.info("Loading member data...")
        member_count = 0

        for congress_dir in self.members_dir.iterdir():
            if congress_dir.is_dir():
                congress_num = congress_dir.name
                self.logger.info(f"Loading members for Congress {congress_num}")

                for member_file in congress_dir.glob("*.json"):
                    try:
                        with open(member_file, encoding="utf-8") as f:
                            member_data = json.load(f)
                            bioguide_id = member_data.get("bioguideId", "")
                            if bioguide_id:
                                self.members_data[bioguide_id] = member_data
                                member_count += 1
                    except Exception as e:
                        self.logger.error(
                            f"Error loading member file {member_file}: {e}"
                        )

        self.logger.info(f"Loaded {member_count} members")

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        try:
            # Handle various date formats
            if "T" in date_str:
                # ISO format with time
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                # Simple date format
                return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception as e:
            self.logger.warning(f"Could not parse date '{date_str}': {e}")
            return None

    def extract_sponsor_info(self, bill_data: Dict) -> Tuple[str, str, str]:
        """Extract sponsor party, name, and state information."""
        sponsors = bill_data.get("sponsors", [])
        if not sponsors:
            return "Unknown", "Unknown", "Unknown"

        sponsor = sponsors[0]  # Primary sponsor
        party = sponsor.get("party", "Unknown")
        name = sponsor.get("fullName", "Unknown")
        state = sponsor.get("state", "Unknown")

        # Normalize party names
        party_mapping = {"R": "Republican", "D": "Democratic", "I": "Independent"}
        party = party_mapping.get(party, party)

        return party, name, state

    def check_bill_success(self, bill_data: Dict) -> bool:
        """Check if bill became law."""
        laws = bill_data.get("laws", [])
        return len(laws) > 0

    def load_bill_data(self) -> None:
        """Load bill data from JSON files."""
        self.logger.info("Loading bill data...")
        bill_count = 0

        for congress_dir in self.bills_dir.iterdir():
            if congress_dir.is_dir():
                congress_num = int(congress_dir.name)
                self.logger.info(f"Loading bills for Congress {congress_num}")

                for bill_file in congress_dir.glob("*.json"):
                    try:
                        with open(bill_file, encoding="utf-8") as f:
                            bill_data = json.load(f)

                        # Extract basic information
                        bill_id = f"{congress_num}_{bill_data.get('type', '')}_{bill_data.get('number', '')}"
                        introduced_date = bill_data.get("introducedDate", "")

                        if not introduced_date:
                            continue

                        # Extract sponsor information
                        party, sponsor_name, sponsor_state = self.extract_sponsor_info(
                            bill_data
                        )

                        # Extract additional metrics
                        latest_action = bill_data.get("latestAction", {})
                        latest_action_date = latest_action.get("actionDate", "")
                        latest_action_text = latest_action.get("text", "")

                        became_law = self.check_bill_success(bill_data)
                        committee_count = bill_data.get("committees", {}).get(
                            "count", 0
                        )
                        cosponsor_count = bill_data.get("cosponsors", {}).get(
                            "count", 0
                        )

                        policy_area = bill_data.get("policyArea", {}).get("name", "")

                        bill = BillData(
                            bill_id=bill_id,
                            introduced_date=introduced_date,
                            congress=congress_num,
                            origin_chamber=bill_data.get("originChamber", ""),
                            bill_type=bill_data.get("type", ""),
                            party=party,
                            sponsor_name=sponsor_name,
                            sponsor_state=sponsor_state,
                            title=bill_data.get("title", ""),
                            latest_action_date=latest_action_date,
                            latest_action_text=latest_action_text,
                            became_law=became_law,
                            committee_count=committee_count,
                            cosponsor_count=cosponsor_count,
                            policy_area=policy_area,
                        )

                        self.bills_data.append(bill)
                        bill_count += 1

                    except Exception as e:
                        self.logger.error(f"Error loading bill file {bill_file}: {e}")

        self.logger.info(f"Loaded {bill_count} bills")

    def determine_election_cycle_phase(self, date: datetime) -> str:
        """Determine the election cycle phase for a given date."""
        year = date.year
        month = date.month

        if year in self.election_years:
            if month <= 2:
                return "Pre-Election (Early)"
            elif month <= 8:
                return "Pre-Election (Mid)"
            elif month <= 10:
                return "Pre-Election (Late)"
            else:
                return "Post-Election"
        # Odd years or non-election even years
        elif month <= 6:
            return "Mid-Term (First Half)"
        else:
            return "Mid-Term (Second Half)"

    def determine_session_phase(self, date: datetime) -> str:
        """Determine the congressional session phase."""
        year = date.year
        month = date.month

        # Congress starts in January of odd years
        congress_start_year = year if year % 2 == 1 else year - 1

        if year == congress_start_year:
            # First year of congress
            if month <= 3:
                return "Session Start"
            elif month <= 9:
                return "First Year Active"
            else:
                return "First Year End"
        # Second year of congress
        elif month <= 3:
            return "Second Year Start"
        elif month <= 9:
            return "Second Year Active"
        else:
            return "Session End"

    def analyze_monthly_trends(self) -> List[TimelineMetrics]:
        """Analyze monthly trends in congressional activity."""
        self.logger.info("Analyzing monthly trends...")

        # Group bills by month
        monthly_data = defaultdict(list)

        for bill in self.bills_data:
            date = self.parse_date(bill.introduced_date)
            if date:
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key].append(bill)

        monthly_metrics = []

        for month_key in sorted(monthly_data.keys()):
            bills = monthly_data[month_key]
            month_date = datetime.strptime(month_key, "%Y-%m")

            # Party breakdown
            party_counts = Counter(bill.party for bill in bills)

            # Success rate
            successful_bills = sum(1 for bill in bills if bill.became_law)
            success_rate = successful_bills / len(bills) if bills else 0

            # Average cosponsors
            avg_cosponsors = (
                mean([bill.cosponsor_count for bill in bills]) if bills else 0
            )

            # Chamber breakdown
            chamber_counts = Counter(bill.origin_chamber for bill in bills)

            # Policy areas
            policy_counts = Counter(
                bill.policy_area for bill in bills if bill.policy_area
            )

            # Election cycle phase
            election_phase = self.determine_election_cycle_phase(month_date)

            metrics = TimelineMetrics(
                date=month_key,
                period_type="monthly",
                party_counts=dict(party_counts),
                total_bills=len(bills),
                success_rate=success_rate,
                avg_cosponsors=avg_cosponsors,
                chamber_breakdown=dict(chamber_counts),
                policy_areas=dict(policy_counts),
                election_cycle_phase=election_phase,
            )

            monthly_metrics.append(metrics)

        return monthly_metrics

    def analyze_quarterly_trends(self) -> List[TimelineMetrics]:
        """Analyze quarterly trends in congressional activity."""
        self.logger.info("Analyzing quarterly trends...")

        # Group bills by quarter
        quarterly_data = defaultdict(list)

        for bill in self.bills_data:
            date = self.parse_date(bill.introduced_date)
            if date:
                quarter = (date.month - 1) // 3 + 1
                quarter_key = f"{date.year}-Q{quarter}"
                quarterly_data[quarter_key].append(bill)

        quarterly_metrics = []

        for quarter_key in sorted(quarterly_data.keys()):
            bills = quarterly_data[quarter_key]
            year, quarter = quarter_key.split("-Q")
            quarter_date = datetime(
                int(year), (int(quarter) - 1) * 3 + 2, 15
            )  # Mid-quarter date

            # Party breakdown
            party_counts = Counter(bill.party for bill in bills)

            # Success rate
            successful_bills = sum(1 for bill in bills if bill.became_law)
            success_rate = successful_bills / len(bills) if bills else 0

            # Average cosponsors
            avg_cosponsors = (
                mean([bill.cosponsor_count for bill in bills]) if bills else 0
            )

            # Chamber breakdown
            chamber_counts = Counter(bill.origin_chamber for bill in bills)

            # Policy areas
            policy_counts = Counter(
                bill.policy_area for bill in bills if bill.policy_area
            )

            # Election cycle phase
            election_phase = self.determine_election_cycle_phase(quarter_date)

            metrics = TimelineMetrics(
                date=quarter_key,
                period_type="quarterly",
                party_counts=dict(party_counts),
                total_bills=len(bills),
                success_rate=success_rate,
                avg_cosponsors=avg_cosponsors,
                chamber_breakdown=dict(chamber_counts),
                policy_areas=dict(policy_counts),
                election_cycle_phase=election_phase,
            )

            quarterly_metrics.append(metrics)

        return quarterly_metrics

    def analyze_election_cycle_patterns(self) -> Dict[str, Any]:
        """Analyze patterns related to election cycles."""
        self.logger.info("Analyzing election cycle patterns...")

        election_analysis = {
            "pre_election_activity": defaultdict(list),
            "post_election_activity": defaultdict(list),
            "election_vs_off_year": {},
            "party_behavior_changes": {},
        }

        for bill in self.bills_data:
            date = self.parse_date(bill.introduced_date)
            if not date:
                continue

            year = date.year
            month = date.month

            # Classify by election cycle
            if year in self.election_years:
                if month <= 10:  # Before November election
                    election_analysis["pre_election_activity"][bill.party].append(bill)
                else:  # After November election
                    election_analysis["post_election_activity"][bill.party].append(bill)

        # Calculate metrics for each party
        for party in ["Republican", "Democratic", "Independent"]:
            pre_election = election_analysis["pre_election_activity"][party]
            post_election = election_analysis["post_election_activity"][party]

            if pre_election and post_election:
                pre_success_rate = sum(1 for b in pre_election if b.became_law) / len(
                    pre_election
                )
                post_success_rate = sum(1 for b in post_election if b.became_law) / len(
                    post_election
                )

                pre_avg_cosponsors = mean([b.cosponsor_count for b in pre_election])
                post_avg_cosponsors = mean([b.cosponsor_count for b in post_election])

                election_analysis["party_behavior_changes"][party] = {
                    "pre_election_bills": len(pre_election),
                    "post_election_bills": len(post_election),
                    "pre_election_success_rate": pre_success_rate,
                    "post_election_success_rate": post_success_rate,
                    "success_rate_change": post_success_rate - pre_success_rate,
                    "pre_avg_cosponsors": pre_avg_cosponsors,
                    "post_avg_cosponsors": post_avg_cosponsors,
                    "cosponsor_change": post_avg_cosponsors - pre_avg_cosponsors,
                }

        return election_analysis

    def analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """Analyze seasonal patterns in legislative activity."""
        self.logger.info("Analyzing seasonal patterns...")

        seasonal_data = {
            "monthly_activity": defaultdict(list),
            "seasonal_summary": {},
            "holiday_effects": {},
        }

        # Group by month across all years
        for bill in self.bills_data:
            date = self.parse_date(bill.introduced_date)
            if date:
                month = date.month
                seasonal_data["monthly_activity"][month].append(bill)

        # Calculate monthly averages
        for month in range(1, 13):
            bills = seasonal_data["monthly_activity"][month]
            if bills:
                avg_bills = len(bills)
                avg_success_rate = sum(1 for b in bills if b.became_law) / len(bills)
                avg_cosponsors = mean([b.cosponsor_count for b in bills])

                party_distribution = Counter(b.party for b in bills)

                seasonal_data["seasonal_summary"][month] = {
                    "month_name": datetime(2024, month, 1).strftime("%B"),
                    "total_bills": avg_bills,
                    "success_rate": avg_success_rate,
                    "avg_cosponsors": avg_cosponsors,
                    "party_distribution": dict(party_distribution),
                }

        # Identify peak and low activity periods
        month_totals = {
            month: len(bills)
            for month, bills in seasonal_data["monthly_activity"].items()
        }
        peak_month = max(month_totals, key=month_totals.get) if month_totals else None
        low_month = min(month_totals, key=month_totals.get) if month_totals else None

        seasonal_data["peak_activity_month"] = peak_month
        seasonal_data["low_activity_month"] = low_month

        return seasonal_data

    def calculate_moving_averages(
        self, metrics: List[TimelineMetrics], window: int = 3
    ) -> List[Dict]:
        """Calculate moving averages for trend analysis."""
        self.logger.info(f"Calculating moving averages with window size {window}")

        moving_averages = []

        for i in range(len(metrics)):
            if i >= window - 1:
                window_metrics = metrics[i - window + 1 : i + 1]

                avg_total_bills = mean([m.total_bills for m in window_metrics])
                avg_success_rate = mean([m.success_rate for m in window_metrics])
                avg_cosponsors = mean([m.avg_cosponsors for m in window_metrics])

                # Party averages
                party_averages = {}
                for party in ["Republican", "Democratic", "Independent"]:
                    party_bills = [m.party_counts.get(party, 0) for m in window_metrics]
                    party_averages[party] = mean(party_bills)

                moving_avg = {
                    "date": metrics[i].date,
                    "window_size": window,
                    "avg_total_bills": avg_total_bills,
                    "avg_success_rate": avg_success_rate,
                    "avg_cosponsors": avg_cosponsors,
                    "party_averages": party_averages,
                    "election_phase": metrics[i].election_cycle_phase,
                }

                moving_averages.append(moving_avg)

        return moving_averages

    def detect_productivity_cycles(self) -> Dict[str, Any]:
        """Detect legislative productivity cycles and patterns."""
        self.logger.info("Detecting productivity cycles...")

        cycles = {
            "congressional_sessions": {},
            "annual_patterns": {},
            "peak_periods": [],
            "low_periods": [],
        }

        # Group by congressional session
        session_data = defaultdict(list)

        for bill in self.bills_data:
            date = self.parse_date(bill.introduced_date)
            if date:
                congress = bill.congress
                session_phase = self.determine_session_phase(date)
                session_key = f"Congress_{congress}_{session_phase}"
                session_data[session_key].append(bill)

        # Analyze each session phase
        for session_key, bills in session_data.items():
            if bills:
                success_rate = sum(1 for b in bills if b.became_law) / len(bills)
                avg_cosponsors = mean([b.cosponsor_count for b in bills])

                party_distribution = Counter(b.party for b in bills)

                cycles["congressional_sessions"][session_key] = {
                    "total_bills": len(bills),
                    "success_rate": success_rate,
                    "avg_cosponsors": avg_cosponsors,
                    "party_distribution": dict(party_distribution),
                }

        # Find peak and low productivity periods
        monthly_totals = defaultdict(int)
        for bill in self.bills_data:
            date = self.parse_date(bill.introduced_date)
            if date:
                month_key = date.strftime("%Y-%m")
                monthly_totals[month_key] += 1

        if monthly_totals:
            sorted_months = sorted(
                monthly_totals.items(), key=lambda x: x[1], reverse=True
            )

            # Top 10% as peak periods
            peak_count = max(1, len(sorted_months) // 10)
            cycles["peak_periods"] = sorted_months[:peak_count]

            # Bottom 10% as low periods
            cycles["low_periods"] = sorted_months[-peak_count:]

        return cycles

    def generate_visualization_data(self) -> Dict[str, Any]:
        """Generate data structures optimized for visualization."""
        self.logger.info("Generating visualization data...")

        viz_data = {
            "monthly_bill_counts": [],
            "quarterly_success_rates": [],
            "party_activity_trends": {},
            "election_cycle_comparison": {},
            "seasonal_heatmap": {},
            "moving_averages": {},
        }

        # Monthly bill counts by party
        monthly_metrics = self.analyze_monthly_trends()
        for metric in monthly_metrics:
            viz_data["monthly_bill_counts"].append(
                {
                    "date": metric.date,
                    "Republican": metric.party_counts.get("Republican", 0),
                    "Democratic": metric.party_counts.get("Democratic", 0),
                    "Independent": metric.party_counts.get("Independent", 0),
                    "total": metric.total_bills,
                    "election_phase": metric.election_cycle_phase,
                }
            )

        # Quarterly success rates
        quarterly_metrics = self.analyze_quarterly_trends()
        for metric in quarterly_metrics:
            viz_data["quarterly_success_rates"].append(
                {
                    "quarter": metric.date,
                    "success_rate": metric.success_rate,
                    "total_bills": metric.total_bills,
                    "avg_cosponsors": metric.avg_cosponsors,
                }
            )

        # Moving averages (3-month and 6-month)
        viz_data["moving_averages"]["3_month"] = self.calculate_moving_averages(
            monthly_metrics, 3
        )
        viz_data["moving_averages"]["6_month"] = self.calculate_moving_averages(
            monthly_metrics, 6
        )

        # Party activity trends
        for party in ["Republican", "Democratic", "Independent"]:
            party_trend = []
            for metric in monthly_metrics:
                party_trend.append(
                    {
                        "date": metric.date,
                        "bill_count": metric.party_counts.get(party, 0),
                        "success_rate": self._calculate_party_success_rate(
                            metric.date, party
                        ),
                    }
                )
            viz_data["party_activity_trends"][party] = party_trend

        return viz_data

    def _calculate_party_success_rate(self, month_key: str, party: str) -> float:
        """Calculate success rate for a specific party in a given month."""
        month_bills = [
            bill
            for bill in self.bills_data
            if self.parse_date(bill.introduced_date)
            and self.parse_date(bill.introduced_date).strftime("%Y-%m") == month_key
            and bill.party == party
        ]

        if not month_bills:
            return 0.0

        successful = sum(1 for bill in month_bills if bill.became_law)
        return successful / len(month_bills)

    def save_timeline_data(self) -> None:
        """Save timeline analysis data to files."""
        self.logger.info("Saving timeline analysis data...")

        # Monthly analysis
        monthly_metrics = self.analyze_monthly_trends()
        monthly_data = [
            {
                "date": m.date,
                "period_type": m.period_type,
                "party_counts": m.party_counts,
                "total_bills": m.total_bills,
                "success_rate": m.success_rate,
                "avg_cosponsors": m.avg_cosponsors,
                "chamber_breakdown": m.chamber_breakdown,
                "policy_areas": m.policy_areas,
                "election_cycle_phase": m.election_cycle_phase,
            }
            for m in monthly_metrics
        ]

        with open(self.output_dir / "monthly_analysis.json", "w") as f:
            json.dump(monthly_data, f, indent=2)

        # Quarterly analysis
        quarterly_metrics = self.analyze_quarterly_trends()
        quarterly_data = [
            {
                "date": m.date,
                "period_type": m.period_type,
                "party_counts": m.party_counts,
                "total_bills": m.total_bills,
                "success_rate": m.success_rate,
                "avg_cosponsors": m.avg_cosponsors,
                "chamber_breakdown": m.chamber_breakdown,
                "policy_areas": m.policy_areas,
                "election_cycle_phase": m.election_cycle_phase,
            }
            for m in quarterly_metrics
        ]

        with open(self.output_dir / "quarterly_analysis.json", "w") as f:
            json.dump(quarterly_data, f, indent=2)

        # Election cycle analysis
        election_analysis = self.analyze_election_cycle_patterns()
        with open(self.output_dir / "election_cycle_analysis.json", "w") as f:
            json.dump(election_analysis, f, indent=2, default=str)

        # Seasonal patterns
        seasonal_analysis = self.analyze_seasonal_patterns()
        with open(self.output_dir / "seasonal_patterns.json", "w") as f:
            json.dump(seasonal_analysis, f, indent=2, default=str)

        # Productivity cycles
        productivity_cycles = self.detect_productivity_cycles()
        with open(self.output_dir / "productivity_cycles.json", "w") as f:
            json.dump(productivity_cycles, f, indent=2, default=str)

        # Visualization data
        viz_data = self.generate_visualization_data()
        with open(self.output_dir / "visualization_data.json", "w") as f:
            json.dump(viz_data, f, indent=2, default=str)

        self.logger.info("Timeline data saved successfully")

    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive timeline analysis."""
        self.logger.info("Generating comprehensive timeline analysis...")

        # Get all analysis components
        monthly_metrics = self.analyze_monthly_trends()
        quarterly_metrics = self.analyze_quarterly_trends()
        election_analysis = self.analyze_election_cycle_patterns()
        seasonal_analysis = self.analyze_seasonal_patterns()
        productivity_cycles = self.detect_productivity_cycles()
        # Note: visualization data generation removed as it's not used in current analysis

        # Calculate summary statistics
        total_bills = len(self.bills_data)
        overall_success_rate = (
            sum(1 for bill in self.bills_data if bill.became_law) / total_bills
            if total_bills > 0
            else 0
        )
        avg_cosponsors = (
            mean([bill.cosponsor_count for bill in self.bills_data])
            if self.bills_data
            else 0
        )

        party_distribution = Counter(bill.party for bill in self.bills_data)
        chamber_distribution = Counter(bill.origin_chamber for bill in self.bills_data)

        # Date range
        dates = [
            self.parse_date(bill.introduced_date)
            for bill in self.bills_data
            if self.parse_date(bill.introduced_date)
        ]
        date_range = {
            "start_date": min(dates).isoformat() if dates else None,
            "end_date": max(dates).isoformat() if dates else None,
            "total_months": len({d.strftime("%Y-%m") for d in dates}) if dates else 0,
        }

        analysis = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "total_bills_analyzed": total_bills,
                "date_range": date_range,
                "script_version": "1.0",
            },
            "summary_statistics": {
                "overall_success_rate": overall_success_rate,
                "avg_cosponsors": avg_cosponsors,
                "party_distribution": dict(party_distribution),
                "chamber_distribution": dict(chamber_distribution),
            },
            "temporal_patterns": {
                "monthly_trends": len(monthly_metrics),
                "quarterly_trends": len(quarterly_metrics),
                "seasonal_peak_month": seasonal_analysis.get("peak_activity_month"),
                "seasonal_low_month": seasonal_analysis.get("low_activity_month"),
            },
            "election_cycle_insights": {
                "parties_analyzed": list(
                    election_analysis["party_behavior_changes"].keys()
                ),
                "behavior_changes_detected": len(
                    election_analysis["party_behavior_changes"]
                ),
            },
            "productivity_insights": {
                "peak_periods_count": len(productivity_cycles["peak_periods"]),
                "low_periods_count": len(productivity_cycles["low_periods"]),
                "session_phases_analyzed": len(
                    productivity_cycles["congressional_sessions"]
                ),
            },
            "data_quality": {
                "bills_with_dates": len(
                    [b for b in self.bills_data if self.parse_date(b.introduced_date)]
                ),
                "bills_with_sponsors": len(
                    [b for b in self.bills_data if b.party != "Unknown"]
                ),
                "bills_with_policy_areas": len(
                    [b for b in self.bills_data if b.policy_area]
                ),
            },
        }

        return analysis

    def run_analysis(self) -> None:
        """Run the complete timeline analysis."""
        self.logger.info("Starting comprehensive timeline analysis...")

        try:
            # Load data
            self.load_member_data()
            self.load_bill_data()

            if not self.bills_data:
                self.logger.error("No bill data loaded. Cannot proceed with analysis.")
                return

            # Save timeline data
            self.save_timeline_data()

            # Generate comprehensive analysis
            comprehensive_analysis = self.generate_comprehensive_analysis()

            # Save comprehensive analysis
            with open(self.analysis_dir / "timeline_analysis.json", "w") as f:
                json.dump(comprehensive_analysis, f, indent=2, default=str)

            self.logger.info("Timeline analysis completed successfully!")
            self.logger.info(f"Analyzed {len(self.bills_data)} bills")
            self.logger.info(
                f"Results saved to {self.output_dir} and {self.analysis_dir}"
            )

        except Exception as e:
            self.logger.error(f"Error during timeline analysis: {e}")
            raise


def main():
    """Main function to run timeline analysis."""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    analyzer = TimelineAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
