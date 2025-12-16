#!/usr/bin/env python3
"""
Topic Analytics Module

Consolidates bill categorization, committee analysis, and policy focus.
Combines functionality from:
- categorize_bills.py (bill topic classification)
- analyze_committees.py (committee activities)

Key features:
- Bill categorization by topic
- Committee productivity metrics
- Party focus by policy area
- Committee effectiveness analysis
- Topic trending analysis
"""

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.api import CongressGovAPI
from core.storage import FileStorage

logger = logging.getLogger(__name__)


@dataclass
class TopicCategory:
    """Represents a topic category for bill classification"""

    name: str
    keywords: List[str]
    committees: List[str]
    policy_areas: List[str]


@dataclass
class BillCategorization:
    """Results of bill categorization"""

    bill_id: str
    title: str
    primary_category: str
    all_categories: List[str]
    category_scores: Dict[str, int]
    policy_area: str
    sponsors: List[Dict]


@dataclass
class CommitteeMetrics:
    """Committee activity and effectiveness metrics"""

    committee_code: str
    committee_name: str
    chamber: str
    total_bills: int
    bills_passed: int
    success_rate: float
    avg_cosponsors: float
    party_composition: Dict[str, int]
    top_policy_areas: List[Tuple[str, int]]


@dataclass
class TopicTrend:
    """Topic trending analysis"""

    category: str
    yearly_counts: Dict[str, int]
    trend_direction: str  # "rising", "declining", "stable"
    change_percentage: float
    significance: str  # "high", "medium", "low"


class TopicAnalyzer:
    """Comprehensive topic and committee analytics for Congressional data"""

    # Define topic categories with associated keywords and patterns
    TOPIC_CATEGORIES = {
        "Healthcare": TopicCategory(
            name="Healthcare",
            keywords=[
                "health",
                "medical",
                "medicare",
                "medicaid",
                "insurance",
                "hospital",
                "patient",
                "disease",
                "drug",
                "pharmaceutical",
                "mental health",
                "public health",
                "veterans health",
                "nursing",
                "doctor",
                "physician",
                "cancer",
                "diabetes",
                "healthcare",
                "clinic",
                "treatment",
                "therapy",
            ],
            committees=[
                "energy and commerce",
                "health",
                "veterans affairs",
                "ways and means",
            ],
            policy_areas=["Health"],
        ),
        "Defense/Military": TopicCategory(
            name="Defense/Military",
            keywords=[
                "defense",
                "military",
                "armed forces",
                "navy",
                "army",
                "air force",
                "marines",
                "national security",
                "veterans",
                "pentagon",
                "warfare",
                "combat",
                "troops",
                "soldiers",
                "homeland security",
                "security",
                "cyber security",
                "intelligence",
                "nato",
                "deployment",
            ],
            committees=[
                "armed services",
                "homeland security",
                "veterans affairs",
                "intelligence",
                "foreign affairs",
            ],
            policy_areas=["Armed Forces and National Security"],
        ),
        "Economy/Finance": TopicCategory(
            name="Economy/Finance",
            keywords=[
                "economic",
                "economy",
                "financial",
                "finance",
                "banking",
                "tax",
                "budget",
                "fiscal",
                "monetary",
                "trade",
                "commerce",
                "business",
                "investment",
                "jobs",
                "employment",
                "unemployment",
                "income",
                "wages",
                "inflation",
                "recession",
                "stimulus",
                "debt",
                "deficit",
            ],
            committees=[
                "financial services",
                "ways and means",
                "budget",
                "small business",
                "banking",
                "commerce",
            ],
            policy_areas=[
                "Economics and Public Finance",
                "Finance and Financial Sector",
            ],
        ),
        "Environment/Climate": TopicCategory(
            name="Environment/Climate",
            keywords=[
                "environment",
                "climate",
                "carbon",
                "emissions",
                "pollution",
                "clean energy",
                "renewable",
                "solar",
                "wind",
                "fossil fuel",
                "greenhouse",
                "conservation",
                "wildlife",
                "endangered",
                "forest",
                "water",
                "air quality",
                "global warming",
                "sustainability",
            ],
            committees=[
                "natural resources",
                "energy and commerce",
                "science",
                "agriculture",
                "transportation",
            ],
            policy_areas=["Environmental Protection", "Energy"],
        ),
        "Education": TopicCategory(
            name="Education",
            keywords=[
                "education",
                "school",
                "student",
                "teacher",
                "university",
                "college",
                "learning",
                "curriculum",
                "scholarship",
                "loan",
                "tuition",
                "educational",
                "academic",
                "literacy",
                "research",
                "science",
                "technology",
                "stem",
                "higher education",
                "k-12",
            ],
            committees=["education", "science", "judiciary"],
            policy_areas=["Education"],
        ),
        "Immigration": TopicCategory(
            name="Immigration",
            keywords=[
                "immigration",
                "immigrant",
                "border",
                "visa",
                "refugee",
                "asylum",
                "citizenship",
                "deportation",
                "alien",
                "naturalization",
                "migration",
                "undocumented",
                "sanctuary",
                "daca",
                "dreamers",
            ],
            committees=["judiciary", "homeland security", "foreign affairs"],
            policy_areas=["Immigration"],
        ),
        "Infrastructure": TopicCategory(
            name="Infrastructure",
            keywords=[
                "infrastructure",
                "transportation",
                "highway",
                "bridge",
                "road",
                "transit",
                "airport",
                "railroad",
                "broadband",
                "internet",
                "telecommunications",
                "utilities",
                "water",
                "sewer",
                "construction",
                "maintenance",
                "repair",
                "rebuild",
            ],
            committees=[
                "transportation",
                "energy and commerce",
                "natural resources",
                "public works",
            ],
            policy_areas=["Transportation and Public Works"],
        ),
        "Technology": TopicCategory(
            name="Technology",
            keywords=[
                "technology",
                "digital",
                "internet",
                "cyber",
                "artificial intelligence",
                "ai",
                "data",
                "privacy",
                "innovation",
                "research",
                "development",
                "computer",
                "software",
                "telecommunications",
                "broadband",
                "encryption",
                "blockchain",
                "robotics",
                "automation",
            ],
            committees=[
                "science",
                "energy and commerce",
                "judiciary",
                "intelligence",
                "oversight",
            ],
            policy_areas=["Science, Technology, Communications"],
        ),
        "Social Issues": TopicCategory(
            name="Social Issues",
            keywords=[
                "civil rights",
                "discrimination",
                "equality",
                "abortion",
                "marriage",
                "family",
                "women",
                "children",
                "elderly",
                "disability",
                "housing",
                "welfare",
                "social security",
                "poverty",
                "justice",
                "crime",
                "criminal justice",
                "police",
                "gun",
                "firearm",
                "violence",
            ],
            committees=[
                "judiciary",
                "oversight",
                "ways and means",
                "financial services",
            ],
            policy_areas=[
                "Civil Rights and Liberties",
                "Crime and Law Enforcement",
                "Social Welfare",
            ],
        ),
        "Foreign Policy": TopicCategory(
            name="Foreign Policy",
            keywords=[
                "foreign",
                "international",
                "diplomatic",
                "treaty",
                "embassy",
                "ambassador",
                "sanctions",
                "aid",
                "trade",
                "export",
                "import",
                "tariff",
                "alliance",
                "relations",
                "peacekeeping",
                "war",
                "conflict",
                "humanitarian",
                "development",
            ],
            committees=[
                "foreign affairs",
                "armed services",
                "intelligence",
                "ways and means",
            ],
            policy_areas=["International Affairs"],
        ),
    }

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the topic analyzer

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.storage = FileStorage(self.base_dir)
        self.congress_api = CongressGovAPI()

        # Data containers
        self.bills_data: List[Dict] = []
        self.committees_data: Dict[str, List[Dict]] = {}
        self.categorized_bills: Dict[str, List[BillCategorization]] = defaultdict(list)
        self.committee_metrics: Dict[str, CommitteeMetrics] = {}

        logger.info("TopicAnalyzer initialized")

    def load_bills_data(self, congress: int = 118) -> List[Dict]:
        """
        Load bills data for categorization

        Args:
            congress: Congress number to analyze

        Returns:
            List of bill dictionaries
        """
        logger.info(f"Loading bills data for Congress {congress}")

        bills_data = self.storage.load_congress_bills(congress)
        bills = list(bills_data.values())

        self.bills_data = bills
        logger.info(f"Loaded {len(bills)} bills")
        return bills

    def load_committees_data(self, congress: int = 118) -> Dict[str, List[Dict]]:
        """
        Load committee data

        Args:
            congress: Congress number to analyze

        Returns:
            Dictionary of committee data by chamber
        """
        logger.info(f"Loading committee data for Congress {congress}")

        committees = {}
        committees_dir = self.base_dir / "committees" / str(congress)

        for chamber in ["house", "senate", "joint"]:
            chamber_dir = committees_dir / chamber
            if not chamber_dir.exists():
                continue

            chamber_committees = []
            for file in chamber_dir.glob("*.json"):
                if file.name == "index.json":
                    continue

                try:
                    with open(file, encoding="utf-8") as f:
                        committee = json.load(f)
                        committee["chamber"] = chamber
                        chamber_committees.append(committee)
                except Exception as e:
                    logger.warning(f"Failed to load committee file {file}: {e}")

            committees[chamber] = chamber_committees

        self.committees_data = committees
        logger.info(f"Loaded {sum(len(c) for c in committees.values())} committees")
        return committees

    def categorize_bill(
        self, bill: Dict, bill_details: Optional[Dict] = None
    ) -> BillCategorization:
        """
        Categorize a single bill based on its content

        Args:
            bill: Bill data dictionary
            bill_details: Optional detailed data including subjects and committees

        Returns:
            Bill categorization result
        """
        categories = set()
        category_scores = {}

        # Get text content to analyze
        title = bill.get("title", "").lower()
        policy_area = bill.get("policyArea", {}).get("name", "").lower()

        # Get subjects if available
        subjects = []
        if bill_details:
            subjects_data = bill_details.get("subjects", {})
            if isinstance(subjects_data, dict):
                legislative_subjects = subjects_data.get("legislativeSubjects", [])
                for subj in legislative_subjects:
                    if isinstance(subj, dict):
                        subjects.append(subj.get("name", "").lower())
                    elif isinstance(subj, str):
                        subjects.append(subj.lower())
            elif isinstance(subjects_data, list):
                for subj in subjects_data:
                    if isinstance(subj, dict):
                        subjects.append(subj.get("name", "").lower())
                    elif isinstance(subj, str):
                        subjects.append(subj.lower())

        # Get committees if available
        committees = []
        if bill_details:
            committees_data = bill_details.get("committees", [])
            for comm in committees_data:
                if isinstance(comm, dict):
                    committees.append(comm.get("name", "").lower())
                elif isinstance(comm, str):
                    committees.append(comm.lower())

        # Combine all text for keyword analysis
        text_content = (
            f"{title} {policy_area} {' '.join(subjects)} {' '.join(committees)}"
        )

        # Check each category
        for category_name, category in self.TOPIC_CATEGORIES.items():
            score = 0

            # Check keywords
            for keyword in category.keywords:
                if keyword.lower() in text_content:
                    score += 1

            # Check policy areas (higher weight)
            for policy_area_term in category.policy_areas:
                if policy_area_term.lower() in policy_area:
                    score += 3

            # Check committees (higher weight)
            for committee_term in category.committees:
                for committee in committees:
                    if committee_term.lower() in committee:
                        score += 2
                        break

            category_scores[category_name] = score

            # Add category if score threshold is met
            if score >= 1:  # At least one match required
                categories.add(category_name)

        # If no categories matched, assign "Other"
        if not categories:
            categories.add("Other")
            category_scores["Other"] = 1

        # Determine primary category (highest score)
        primary_category = max(category_scores.items(), key=lambda x: x[1])[0]

        return BillCategorization(
            bill_id=f"{bill.get('congress')}_{bill.get('type')}_{bill.get('number')}",
            title=bill.get("title", ""),
            primary_category=primary_category,
            all_categories=list(categories),
            category_scores=category_scores,
            policy_area=bill.get("policyArea", {}).get("name", ""),
            sponsors=bill.get("sponsors", []),
        )

    def categorize_all_bills(
        self, bill_details_data: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, List[BillCategorization]]:
        """
        Categorize all bills and group by category

        Args:
            bill_details_data: Optional dictionary of bill detail data

        Returns:
            Dictionary mapping category names to lists of categorized bills
        """
        logger.info("Categorizing all bills")

        categorized = defaultdict(list)

        for bill in self.bills_data:
            congress = bill.get("congress")
            bill_type = bill.get("type", "").lower()
            bill_number = bill.get("number")

            bill_id = f"{congress}_{bill_type}_{bill_number}"
            bill_details = bill_details_data.get(bill_id) if bill_details_data else None

            # Categorize the bill
            categorization = self.categorize_bill(bill, bill_details)

            # Add to each category it belongs to
            for category in categorization.all_categories:
                categorized[category].append(categorization)

        self.categorized_bills = categorized
        logger.info(
            f"Categorized {len(self.bills_data)} bills into {len(categorized)} categories"
        )
        return dict(categorized)

    def analyze_party_focus_by_category(self) -> Dict[str, Any]:
        """
        Analyze which party focuses on which issues

        Returns:
            Dictionary with party focus analysis by category
        """
        logger.info("Analyzing party focus by category")

        category_party_counts = defaultdict(lambda: defaultdict(int))

        for category, bills in self.categorized_bills.items():
            for bill in bills:
                sponsors = bill.sponsors
                if sponsors:
                    primary_sponsor = sponsors[0]
                    party = primary_sponsor.get("party", "Unknown")
                    category_party_counts[category][party] += 1

        # Calculate percentages and analysis
        category_analysis = {}
        for category, party_counts in category_party_counts.items():
            total_bills = sum(party_counts.values())
            party_percentages = {
                party: (count / total_bills * 100) if total_bills > 0 else 0
                for party, count in party_counts.items()
            }

            # Find dominant party
            dominant_party = (
                max(party_counts.items(), key=lambda x: x[1])[0]
                if party_counts
                else "Unknown"
            )

            category_analysis[category] = {
                "total_bills": total_bills,
                "party_counts": dict(party_counts),
                "party_percentages": party_percentages,
                "dominant_party": dominant_party,
            }

        return category_analysis

    def analyze_success_rates_by_category(self) -> Dict[str, Any]:
        """
        Analyze success rates by category and party

        Returns:
            Dictionary with success rate analysis by category
        """
        logger.info("Analyzing success rates by category")

        category_success = defaultdict(
            lambda: {
                "total": 0,
                "enacted": 0,
                "parties": defaultdict(lambda: {"total": 0, "enacted": 0}),
            }
        )

        for category, bills in self.categorized_bills.items():
            for bill in bills:
                sponsors = bill.sponsors
                if not sponsors:
                    continue

                primary_sponsor = sponsors[0]
                party = primary_sponsor.get("party", "Unknown")

                # Count total bills
                category_success[category]["total"] += 1
                category_success[category]["parties"][party]["total"] += 1

                # Check if bill became law (this would need to be determined from actual bill data)
                # For now, using a placeholder
                became_law = False  # Would need actual law status from bill data
                if became_law:
                    category_success[category]["enacted"] += 1
                    category_success[category]["parties"][party]["enacted"] += 1

        # Calculate success rates
        success_analysis = {}
        for category, data in category_success.items():
            total = data["total"]
            enacted = data["enacted"]
            overall_rate = (enacted / total * 100) if total > 0 else 0

            party_rates = {}
            for party, party_data in data["parties"].items():
                party_total = party_data["total"]
                party_enacted = party_data["enacted"]
                party_rate = (
                    (party_enacted / party_total * 100) if party_total > 0 else 0
                )

                party_rates[party] = {
                    "total": party_total,
                    "enacted": party_enacted,
                    "success_rate_percent": round(party_rate, 2),
                }

            success_analysis[category] = {
                "total_bills": total,
                "enacted_bills": enacted,
                "overall_success_rate_percent": round(overall_rate, 2),
                "party_success_rates": party_rates,
            }

        return success_analysis

    def analyze_committee_activity(self) -> Dict[str, CommitteeMetrics]:
        """
        Analyze committee activity and effectiveness

        Returns:
            Dictionary mapping committee codes to metrics
        """
        logger.info("Analyzing committee activity")

        committee_metrics = {}
        committee_bill_counts = defaultdict(
            lambda: {
                "total_bills": 0,
                "bills_passed": 0,
                "total_cosponsors": 0,
                "policy_areas": Counter(),
            }
        )

        # Count bills by committee from bills data
        for bill in self.bills_data:
            committees = bill.get("committees", {})
            if isinstance(committees, dict):
                committee_list = committees.get("committees", [])
            else:
                committee_list = committees if isinstance(committees, list) else []

            for committee in committee_list:
                committee_code = committee.get(
                    "systemCode", committee.get("code", "unknown")
                )
                committee_name = committee.get("name", "Unknown")
                chamber = committee.get("chamber", "").lower()

                committee_bill_counts[committee_code]["total_bills"] += 1
                committee_bill_counts[committee_code]["committee_name"] = committee_name
                committee_bill_counts[committee_code]["chamber"] = chamber

                # Count cosponsors
                cosponsor_count = bill.get("cosponsors", {}).get("count", 0)
                committee_bill_counts[committee_code][
                    "total_cosponsors"
                ] += cosponsor_count

                # Track policy areas
                policy_area = bill.get("policyArea", {}).get("name", "")
                if policy_area:
                    committee_bill_counts[committee_code]["policy_areas"][
                        policy_area
                    ] += 1

                # Check if bill passed (simplified - would need actual status)
                # For now using placeholder
                if bill.get("laws", []):  # Bills that became law
                    committee_bill_counts[committee_code]["bills_passed"] += 1

        # Create metrics objects
        for committee_code, data in committee_bill_counts.items():
            total_bills = data["total_bills"]
            bills_passed = data["bills_passed"]
            success_rate = (bills_passed / total_bills * 100) if total_bills > 0 else 0
            avg_cosponsors = (
                (data["total_cosponsors"] / total_bills) if total_bills > 0 else 0
            )

            top_policy_areas = data["policy_areas"].most_common(5)

            metrics = CommitteeMetrics(
                committee_code=committee_code,
                committee_name=data.get("committee_name", "Unknown"),
                chamber=data.get("chamber", "unknown"),
                total_bills=total_bills,
                bills_passed=bills_passed,
                success_rate=success_rate,
                avg_cosponsors=avg_cosponsors,
                party_composition={},  # Would need member data
                top_policy_areas=top_policy_areas,
            )

            committee_metrics[committee_code] = metrics

        self.committee_metrics = committee_metrics
        logger.info(f"Analyzed {len(committee_metrics)} committees")
        return committee_metrics

    def analyze_trending_topics(self) -> List[TopicTrend]:
        """
        Analyze trending topics over time

        Returns:
            List of topic trend analyses
        """
        logger.info("Analyzing trending topics")

        # Group bills by year and category
        yearly_categories = defaultdict(lambda: defaultdict(int))

        for category, bills in self.categorized_bills.items():
            for bill in bills:
                # Extract year from bill data (would need actual introduced date)
                # For now using congress as proxy
                congress = (
                    getattr(bill, "congress", 118) if hasattr(bill, "congress") else 118
                )
                year = str(2023 + (congress - 118) * 2)  # Approximate year mapping
                yearly_categories[year][category] += 1

        # Calculate trends
        trends = []
        years = sorted(yearly_categories.keys())

        if len(years) >= 2:
            for category in self.TOPIC_CATEGORIES:
                if category == "Other":
                    continue

                year_counts = {}
                for year in years:
                    year_counts[year] = yearly_categories[year].get(category, 0)

                # Calculate trend
                if len(years) >= 2:
                    recent_year = years[-1]
                    previous_year = years[-2]

                    recent_count = year_counts[recent_year]
                    previous_count = year_counts[previous_year]

                    if previous_count > 0:
                        change_percentage = (
                            (recent_count - previous_count) / previous_count
                        ) * 100
                    else:
                        change_percentage = 100.0 if recent_count > 0 else 0.0

                    # Determine trend direction
                    if change_percentage > 20:
                        trend_direction = "rising"
                        significance = "high" if change_percentage > 50 else "medium"
                    elif change_percentage < -20:
                        trend_direction = "declining"
                        significance = "high" if change_percentage < -50 else "medium"
                    else:
                        trend_direction = "stable"
                        significance = "low"

                    trend = TopicTrend(
                        category=category,
                        yearly_counts=year_counts,
                        trend_direction=trend_direction,
                        change_percentage=change_percentage,
                        significance=significance,
                    )

                    trends.append(trend)

        logger.info(f"Analyzed trends for {len(trends)} topics")
        return trends

    def generate_comprehensive_analysis(self, congress: int = 118) -> Dict[str, Any]:
        """
        Generate comprehensive topic analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Complete topic analysis report
        """
        logger.info(f"Generating comprehensive topic analysis for Congress {congress}")

        # Load data
        self.load_bills_data(congress)
        self.load_committees_data(congress)

        if not self.bills_data:
            logger.error("No bill data loaded. Cannot proceed with analysis.")
            return {}

        # Run analyses
        categorized_bills = self.categorize_all_bills()
        party_focus = self.analyze_party_focus_by_category()
        success_rates = self.analyze_success_rates_by_category()
        committee_activity = self.analyze_committee_activity()
        trending_topics = self.analyze_trending_topics()

        # Calculate summary statistics
        total_bills = len(self.bills_data)
        total_categorized = sum(len(bills) for bills in categorized_bills.values())
        category_counts = {cat: len(bills) for cat, bills in categorized_bills.items()}
        top_categories = sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Committee summary
        committee_summary = {
            "total_committees": len(committee_activity),
            "most_active_committee": (
                max(committee_activity.items(), key=lambda x: x[1].total_bills)[0]
                if committee_activity
                else None
            ),
            "avg_committee_bills": (
                sum(c.total_bills for c in committee_activity.values())
                / len(committee_activity)
                if committee_activity
                else 0
            ),
        }

        report = {
            "metadata": {
                "congress": congress,
                "analysis_date": datetime.now().isoformat(),
                "total_bills_analyzed": total_bills,
                "total_bills_categorized": total_categorized,
                "categories_analyzed": len(self.TOPIC_CATEGORIES),
                "committees_analyzed": len(committee_activity),
            },
            "bill_categorization": {
                "category_distribution": category_counts,
                "top_categories": dict(top_categories),
                "categorized_bills_by_topic": {
                    category: [
                        {
                            "bill_id": bill.bill_id,
                            "title": bill.title[:100],
                            "primary_category": bill.primary_category,
                            "category_score": bill.category_scores.get(category, 0),
                        }
                        for bill in bills[:10]  # Top 10 per category
                    ]
                    for category, bills in categorized_bills.items()
                },
            },
            "party_focus_analysis": party_focus,
            "success_rates_by_category": success_rates,
            "committee_activity": {
                committee_code: {
                    "name": metrics.committee_name,
                    "chamber": metrics.chamber,
                    "total_bills": metrics.total_bills,
                    "success_rate": metrics.success_rate,
                    "avg_cosponsors": metrics.avg_cosponsors,
                    "top_policy_areas": metrics.top_policy_areas,
                }
                for committee_code, metrics in committee_activity.items()
            },
            "trending_topics": [
                {
                    "category": trend.category,
                    "trend_direction": trend.trend_direction,
                    "change_percentage": trend.change_percentage,
                    "significance": trend.significance,
                    "yearly_counts": trend.yearly_counts,
                }
                for trend in trending_topics
            ],
            "summary_statistics": {
                "category_summary": {
                    "most_popular_category": (
                        top_categories[0][0] if top_categories else "Unknown"
                    ),
                    "most_popular_count": top_categories[0][1] if top_categories else 0,
                    "least_popular_category": (
                        top_categories[-1][0] if top_categories else "Unknown"
                    ),
                },
                "committee_summary": committee_summary,
                "trending_summary": {
                    "rising_topics": [
                        t.category
                        for t in trending_topics
                        if t.trend_direction == "rising"
                    ],
                    "declining_topics": [
                        t.category
                        for t in trending_topics
                        if t.trend_direction == "declining"
                    ],
                },
            },
            "key_insights": self._generate_key_insights(
                categorized_bills, party_focus, committee_activity, trending_topics
            ),
        }

        return report

    def save_analysis_report(self, report: Dict, output_file: str = None) -> str:
        """
        Save topic analysis report

        Args:
            report: Analysis report to save
            output_file: Optional output file path

        Returns:
            Path to saved file
        """
        if output_file is None:
            output_file = "analysis/topic_analytics_report.json"

        output_path = self.base_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Topic analysis report saved to {output_path}")
        return str(output_path)

    def save_categorized_bills(self, output_dir: str = None) -> str:
        """
        Save categorized bills to separate files

        Args:
            output_dir: Output directory for categorized bills

        Returns:
            Path to saved categorized bills directory
        """
        if output_dir is None:
            output_dir = "analysis/bill_categories"

        categories_dir = self.base_dir / output_dir
        categories_dir.mkdir(parents=True, exist_ok=True)

        # Save bills by category
        for category, bills in self.categorized_bills.items():
            category_file = (
                categories_dir
                / f"{category.lower().replace('/', '_').replace(' ', '_')}.json"
            )

            category_data = {
                "category": category,
                "total_bills": len(bills),
                "last_updated": datetime.now().isoformat(),
                "bills": [
                    {
                        "bill_id": bill.bill_id,
                        "title": bill.title,
                        "primary_category": bill.primary_category,
                        "all_categories": bill.all_categories,
                        "category_scores": bill.category_scores,
                        "policy_area": bill.policy_area,
                    }
                    for bill in bills
                ],
            }

            with open(category_file, "w", encoding="utf-8") as f:
                json.dump(category_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved categorized bills to {categories_dir}")
        return str(categories_dir)

    def _generate_key_insights(
        self,
        categorized_bills: Dict,
        party_focus: Dict,
        committee_activity: Dict,
        trending_topics: List,
    ) -> List[str]:
        """Generate key insights from topic analysis"""
        insights = []

        # Bill categorization insights
        if categorized_bills:
            total_bills = sum(len(bills) for bills in categorized_bills.values())
            most_popular = max(categorized_bills.items(), key=lambda x: len(x[1]))
            insights.append(
                f"Most popular topic: {most_popular[0]} with {len(most_popular[1])} bills ({len(most_popular[1])/total_bills:.1%})"
            )

        # Party focus insights
        if party_focus:
            republican_topics = []
            democratic_topics = []

            for category, data in party_focus.items():
                if data.get("dominant_party") == "R":
                    republican_topics.append(category)
                elif data.get("dominant_party") == "D":
                    democratic_topics.append(category)

            if republican_topics:
                insights.append(
                    f"Republican-dominated topics: {', '.join(republican_topics[:3])}"
                )
            if democratic_topics:
                insights.append(
                    f"Democratic-dominated topics: {', '.join(democratic_topics[:3])}"
                )

        # Committee activity insights
        if committee_activity:
            most_active = max(
                committee_activity.items(), key=lambda x: x[1].total_bills
            )
            insights.append(
                f"Most active committee: {most_active[1].committee_name} with {most_active[1].total_bills} bills"
            )

        # Trending insights
        rising_topics = [
            t.category for t in trending_topics if t.trend_direction == "rising"
        ]
        declining_topics = [
            t.category for t in trending_topics if t.trend_direction == "declining"
        ]

        if rising_topics:
            insights.append(f"Rising topics: {', '.join(rising_topics[:3])}")
        if declining_topics:
            insights.append(f"Declining topics: {', '.join(declining_topics[:3])}")

        return insights
