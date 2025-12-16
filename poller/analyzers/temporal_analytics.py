#!/usr/bin/env python3
"""
Temporal Analytics Module

Consolidates timeline trends, election cycles, and seasonal patterns analysis.
Based on functionality from analyze_timeline.py.

Key features:
- Timeline trends analysis
- Election cycle patterns
- Seasonal legislative patterns
- Congressional productivity cycles
- Pre/post-election behavior analysis
"""

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

from core.api import CongressGovAPI
from core.storage import FileStorage

logger = logging.getLogger(__name__)


@dataclass
class BillData:
    """Data class for bill information"""

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
    """Data class for timeline analysis metrics"""

    date: str
    period_type: str  # monthly, quarterly, yearly
    party_counts: Dict[str, int]
    total_bills: int
    success_rate: float
    avg_cosponsors: float
    chamber_breakdown: Dict[str, int]
    policy_areas: Dict[str, int]
    election_cycle_phase: str


@dataclass
class ElectionCyclePattern:
    """Election cycle behavior patterns"""

    cycle_year: int
    pre_election_activity: Dict[str, int]
    post_election_activity: Dict[str, int]
    party_behavior_changes: Dict[str, Dict]


@dataclass
class SeasonalPattern:
    """Seasonal legislative activity patterns"""

    month: int
    month_name: str
    avg_bills_introduced: int
    avg_success_rate: float
    avg_cosponsors: float
    party_distribution: Dict[str, int]


class TemporalAnalyzer:
    """Comprehensive temporal analytics for Congressional data"""

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the temporal analyzer

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.storage = FileStorage(self.base_dir)
        self.congress_api = CongressGovAPI()

        # Analysis parameters
        self.election_years = {2020, 2022, 2024, 2026}  # Even years are election years

        # Data containers
        self.bills_data: List[BillData] = []
        self.members_data: Dict[str, Dict] = {}
        self.timeline_data: List[TimelineMetrics] = []

        logger.info("TemporalAnalyzer initialized")

    def load_member_data(self, congress: int = 118) -> Dict[str, Dict]:
        """
        Load member data

        Args:
            congress: Congress number to analyze

        Returns:
            Dictionary of member data
        """
        logger.info(f"Loading member data for Congress {congress}")

        members_data = self.storage.load_congress_members(congress)
        self.members_data = members_data

        logger.info(f"Loaded {len(members_data)} members")
        return members_data

    def load_bill_data(self, congress: int = 118) -> List[BillData]:
        """
        Load bill data for temporal analysis

        Args:
            congress: Congress number to analyze

        Returns:
            List of processed bill data
        """
        logger.info(f"Loading bill data for Congress {congress}")

        bills_raw = self.storage.load_congress_bills(congress)
        bills_data = []

        for bill_id, bill_data in bills_raw.items():
            # Extract sponsor information
            party, sponsor_name, sponsor_state = self._extract_sponsor_info(bill_data)

            # Check if bill became law
            became_law = self._check_bill_success(bill_data)

            # Extract additional metrics
            latest_action = bill_data.get("latestAction", {})
            latest_action_date = latest_action.get("actionDate", "")
            latest_action_text = latest_action.get("text", "")

            committee_count = bill_data.get("committees", {}).get("count", 0)
            cosponsor_count = bill_data.get("cosponsors", {}).get("count", 0)
            policy_area = bill_data.get("policyArea", {}).get("name", "")

            bill = BillData(
                bill_id=bill_id,
                introduced_date=bill_data.get("introducedDate", ""),
                congress=bill_data.get("congress", congress),
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

            bills_data.append(bill)

        self.bills_data = bills_data
        logger.info(f"Loaded {len(bills_data)} bills")
        return bills_data

    def _extract_sponsor_info(self, bill_data: Dict) -> Tuple[str, str, str]:
        """Extract sponsor party, name, and state information"""
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

    def _check_bill_success(self, bill_data: Dict) -> bool:
        """Check if bill became law"""
        laws = bill_data.get("laws", [])
        return len(laws) > 0

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
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
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None

    def determine_election_cycle_phase(self, date: datetime) -> str:
        """Determine the election cycle phase for a given date"""
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
        """Determine the congressional session phase"""
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
        """
        Analyze monthly trends in congressional activity

        Returns:
            List of monthly timeline metrics
        """
        logger.info("Analyzing monthly trends")

        # Group bills by month
        monthly_data = defaultdict(list)

        for bill in self.bills_data:
            date = self._parse_date(bill.introduced_date)
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
        """
        Analyze quarterly trends in congressional activity

        Returns:
            List of quarterly timeline metrics
        """
        logger.info("Analyzing quarterly trends")

        # Group bills by quarter
        quarterly_data = defaultdict(list)

        for bill in self.bills_data:
            date = self._parse_date(bill.introduced_date)
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
        """
        Analyze patterns related to election cycles

        Returns:
            Election cycle analysis results
        """
        logger.info("Analyzing election cycle patterns")

        election_analysis = {
            "pre_election_activity": defaultdict(list),
            "post_election_activity": defaultdict(list),
            "election_vs_off_year": {},
            "party_behavior_changes": {},
        }

        for bill in self.bills_data:
            date = self._parse_date(bill.introduced_date)
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
        """
        Analyze seasonal patterns in legislative activity

        Returns:
            Seasonal analysis results
        """
        logger.info("Analyzing seasonal patterns")

        seasonal_data = {
            "monthly_activity": defaultdict(list),
            "seasonal_summary": {},
            "holiday_effects": {},
        }

        # Group by month across all years
        for bill in self.bills_data:
            date = self._parse_date(bill.introduced_date)
            if date:
                month = date.month
                seasonal_data["monthly_activity"][month].append(bill)

        # Calculate monthly averages
        seasonal_patterns = []
        for month in range(1, 13):
            bills = seasonal_data["monthly_activity"][month]
            if bills:
                avg_bills = len(bills)
                avg_success_rate = sum(1 for b in bills if b.became_law) / len(bills)
                avg_cosponsors = mean([b.cosponsor_count for b in bills])

                party_distribution = Counter(b.party for b in bills)

                pattern = SeasonalPattern(
                    month=month,
                    month_name=datetime(2024, month, 1).strftime("%B"),
                    avg_bills_introduced=avg_bills,
                    avg_success_rate=avg_success_rate,
                    avg_cosponsors=avg_cosponsors,
                    party_distribution=dict(party_distribution),
                )

                seasonal_patterns.append(pattern)

                seasonal_data["seasonal_summary"][month] = {
                    "month_name": pattern.month_name,
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
        seasonal_data["seasonal_patterns"] = seasonal_patterns

        return seasonal_data

    def detect_productivity_cycles(self) -> Dict[str, Any]:
        """
        Detect legislative productivity cycles and patterns

        Returns:
            Productivity cycle analysis
        """
        logger.info("Detecting productivity cycles")

        cycles = {
            "congressional_sessions": {},
            "annual_patterns": {},
            "peak_periods": [],
            "low_periods": [],
        }

        # Group by congressional session
        session_data = defaultdict(list)

        for bill in self.bills_data:
            date = self._parse_date(bill.introduced_date)
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
            date = self._parse_date(bill.introduced_date)
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

    def calculate_moving_averages(
        self, metrics: List[TimelineMetrics], window: int = 3
    ) -> List[Dict]:
        """
        Calculate moving averages for trend analysis

        Args:
            metrics: List of timeline metrics
            window: Window size for moving average

        Returns:
            List of moving average data
        """
        logger.info(f"Calculating moving averages with window size {window}")

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

    def generate_visualization_data(self) -> Dict[str, Any]:
        """
        Generate data structures optimized for visualization

        Returns:
            Visualization-ready data
        """
        logger.info("Generating visualization data")

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
        """Calculate success rate for a specific party in a given month"""
        month_bills = [
            bill
            for bill in self.bills_data
            if self._parse_date(bill.introduced_date)
            and self._parse_date(bill.introduced_date).strftime("%Y-%m") == month_key
            and bill.party == party
        ]

        if not month_bills:
            return 0.0

        successful = sum(1 for bill in month_bills if bill.became_law)
        return successful / len(month_bills)

    def generate_comprehensive_analysis(self, congress: int = 118) -> Dict[str, Any]:
        """
        Generate comprehensive temporal analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Complete temporal analysis report
        """
        logger.info(
            f"Generating comprehensive temporal analysis for Congress {congress}"
        )

        # Load data
        self.load_member_data(congress)
        self.load_bill_data(congress)

        if not self.bills_data:
            logger.error("No bill data loaded. Cannot proceed with analysis.")
            return {}

        # Run analyses
        monthly_metrics = self.analyze_monthly_trends()
        quarterly_metrics = self.analyze_quarterly_trends()
        election_analysis = self.analyze_election_cycle_patterns()
        seasonal_analysis = self.analyze_seasonal_patterns()
        productivity_cycles = self.detect_productivity_cycles()
        visualization_data = self.generate_visualization_data()

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
            self._parse_date(bill.introduced_date)
            for bill in self.bills_data
            if self._parse_date(bill.introduced_date)
        ]
        date_range = {
            "start_date": min(dates).isoformat() if dates else None,
            "end_date": max(dates).isoformat() if dates else None,
            "total_months": len({d.strftime("%Y-%m") for d in dates}) if dates else 0,
        }

        report = {
            "metadata": {
                "congress": congress,
                "analysis_date": datetime.now().isoformat(),
                "total_bills_analyzed": total_bills,
                "date_range": date_range,
                "data_sources": ["congress_bills", "member_profiles"],
            },
            "summary_statistics": {
                "overall_success_rate": overall_success_rate,
                "avg_cosponsors": avg_cosponsors,
                "party_distribution": dict(party_distribution),
                "chamber_distribution": dict(chamber_distribution),
            },
            "monthly_trends": [
                {
                    "date": m.date,
                    "party_counts": m.party_counts,
                    "total_bills": m.total_bills,
                    "success_rate": m.success_rate,
                    "avg_cosponsors": m.avg_cosponsors,
                    "election_phase": m.election_cycle_phase,
                }
                for m in monthly_metrics
            ],
            "quarterly_trends": [
                {
                    "date": m.date,
                    "party_counts": m.party_counts,
                    "total_bills": m.total_bills,
                    "success_rate": m.success_rate,
                    "avg_cosponsors": m.avg_cosponsors,
                    "election_phase": m.election_cycle_phase,
                }
                for m in quarterly_metrics
            ],
            "election_cycle_patterns": election_analysis,
            "seasonal_patterns": seasonal_analysis,
            "productivity_cycles": productivity_cycles,
            "visualization_data": visualization_data,
            "temporal_insights": {
                "monthly_trends_count": len(monthly_metrics),
                "quarterly_trends_count": len(quarterly_metrics),
                "seasonal_peak_month": seasonal_analysis.get("peak_activity_month"),
                "seasonal_low_month": seasonal_analysis.get("low_activity_month"),
                "election_behavior_changes": len(
                    election_analysis.get("party_behavior_changes", {})
                ),
                "peak_periods_count": len(productivity_cycles.get("peak_periods", [])),
                "low_periods_count": len(productivity_cycles.get("low_periods", [])),
            },
            "key_insights": self._generate_key_insights(
                monthly_metrics, election_analysis, seasonal_analysis
            ),
        }

        return report

    def save_analysis_report(self, report: Dict, output_file: str = None) -> str:
        """
        Save temporal analysis report

        Args:
            report: Analysis report to save
            output_file: Optional output file path

        Returns:
            Path to saved file
        """
        if output_file is None:
            output_file = "analysis/temporal_analytics_report.json"

        output_path = self.base_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Temporal analysis report saved to {output_path}")
        return str(output_path)

    def _generate_key_insights(
        self,
        monthly_metrics: List[TimelineMetrics],
        election_analysis: Dict,
        seasonal_analysis: Dict,
    ) -> List[str]:
        """Generate key insights from temporal analysis"""
        insights = []

        # Monthly trend insights
        if monthly_metrics:
            total_months = len(monthly_metrics)
            avg_monthly_bills = mean([m.total_bills for m in monthly_metrics])
            insights.append(
                f"Average {avg_monthly_bills:.1f} bills introduced per month over {total_months} months"
            )

        # Election cycle insights
        if election_analysis.get("party_behavior_changes"):
            for party, changes in election_analysis["party_behavior_changes"].items():
                success_change = changes.get("success_rate_change", 0)
                if abs(success_change) > 0.05:  # 5% change threshold
                    direction = "increased" if success_change > 0 else "decreased"
                    insights.append(
                        f"{party} success rate {direction} by {abs(success_change):.1%} post-election"
                    )

        # Seasonal insights
        peak_month = seasonal_analysis.get("peak_activity_month")
        low_month = seasonal_analysis.get("low_activity_month")
        if peak_month and low_month:
            peak_name = datetime(2024, peak_month, 1).strftime("%B")
            low_name = datetime(2024, low_month, 1).strftime("%B")
            insights.append(
                f"Peak legislative activity in {peak_name}, lowest in {low_name}"
            )

        # Success rate insights
        if monthly_metrics:
            success_rates = [
                m.success_rate for m in monthly_metrics if m.success_rate > 0
            ]
            if success_rates:
                avg_success = mean(success_rates)
                insights.append(f"Average bill success rate: {avg_success:.1%}")

        return insights
