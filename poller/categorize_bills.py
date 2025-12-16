#!/usr/bin/env python3
"""
Bill Categorization Script - Categorizes bills by topic/subject area
Analyzes which party focuses on which issues and calculates success rates by category
Maps party sponsorship to topics and identifies trending issues
"""

import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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


class CongressGovAPIv3(CongressGovAPI):
    """Extended Congress.gov API client with additional endpoints for bill categorization"""

    def get_bill_subjects(
        self, congress: int, bill_type: str, bill_number: str
    ) -> Optional[Dict]:
        """
        Get subjects for a specific bill

        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (e.g., 'hr', 's', 'hjres', 'sjres')
            bill_number: Bill number

        Returns:
            Subjects data or None if failed
        """
        endpoint = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/subjects"
        return self._make_request(endpoint)

    def get_bill_committees(
        self, congress: int, bill_type: str, bill_number: str
    ) -> Optional[Dict]:
        """
        Get committees for a specific bill

        Args:
            congress: Congress number (e.g., 118)
            bill_type: Bill type (e.g., 'hr', 's', 'hjres', 'sjres')
            bill_number: Bill number

        Returns:
            Committees data or None if failed
        """
        endpoint = f"/bill/{congress}/{bill_type.lower()}/{bill_number}/committees"
        return self._make_request(endpoint)

    def get_bill_details_batch(
        self, bills: List[Dict], base_dir: str = "data"
    ) -> Dict[str, Dict]:
        """
        Fetch subjects and committee data for a batch of bills

        Args:
            bills: List of bill dictionaries with congress, type, and number
            base_dir: Base directory for caching data

        Returns:
            Dictionary mapping bill_id to detailed data
        """
        details_data = {}
        record_type = "bill_details"

        # Load existing data to avoid re-fetching
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
                            details_data[bill_id] = json.load(f)
                        logger.debug(f"Loaded cached details for {bill_id}")
                        continue
                except Exception as e:
                    logger.warning(f"Failed to load cached data for {bill_id}: {e}")

            logger.info(f"Fetching details for {bill_id}...")

            # Fetch subjects and committees
            subjects_data = self.get_bill_subjects(congress, bill_type, bill_number)
            committees_data = self.get_bill_committees(congress, bill_type, bill_number)

            if subjects_data or committees_data:
                # Store the combined detailed data
                bill_details = {
                    "bill_id": bill_id,
                    "congress": congress,
                    "type": bill_type,
                    "number": bill_number,
                    "subjects": (
                        subjects_data.get("subjects", []) if subjects_data else []
                    ),
                    "committees": (
                        committees_data.get("committees", []) if committees_data else []
                    ),
                    "policy_area": bill.get("policyArea", {}),
                    "title": bill.get("title", ""),
                    "sponsors": bill.get("sponsors", []),
                    "fetched_at": datetime.now().isoformat(),
                }

                details_data[bill_id] = bill_details

                # Cache the data
                save_individual_record(bill_details, record_type, bill_id, base_dir)
                logger.debug(f"Cached details for {bill_id}")
            else:
                logger.warning(f"Failed to fetch details for {bill_id}")

        return details_data


class BillCategorizer:
    """Categorizes bills by topic and analyzes patterns"""

    # Define topic categories with associated keywords and committee patterns
    TOPIC_CATEGORIES = {
        "Healthcare": {
            "keywords": [
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
            "committees": [
                "energy and commerce",
                "health",
                "veterans affairs",
                "ways and means",
            ],
            "policy_areas": ["Health"],
        },
        "Defense/Military": {
            "keywords": [
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
            "committees": [
                "armed services",
                "homeland security",
                "veterans affairs",
                "intelligence",
                "foreign affairs",
            ],
            "policy_areas": ["Armed Forces and National Security"],
        },
        "Economy/Finance": {
            "keywords": [
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
            "committees": [
                "financial services",
                "ways and means",
                "budget",
                "small business",
                "banking",
                "commerce",
            ],
            "policy_areas": [
                "Economics and Public Finance",
                "Finance and Financial Sector",
            ],
        },
        "Environment/Climate": {
            "keywords": [
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
            "committees": [
                "natural resources",
                "energy and commerce",
                "science",
                "agriculture",
                "transportation",
            ],
            "policy_areas": ["Environmental Protection", "Energy"],
        },
        "Education": {
            "keywords": [
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
            "committees": ["education", "science", "judiciary"],
            "policy_areas": ["Education"],
        },
        "Immigration": {
            "keywords": [
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
            "committees": ["judiciary", "homeland security", "foreign affairs"],
            "policy_areas": ["Immigration"],
        },
        "Infrastructure": {
            "keywords": [
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
            "committees": [
                "transportation",
                "energy and commerce",
                "natural resources",
                "public works",
            ],
            "policy_areas": ["Transportation and Public Works"],
        },
        "Technology": {
            "keywords": [
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
            "committees": [
                "science",
                "energy and commerce",
                "judiciary",
                "intelligence",
                "oversight",
            ],
            "policy_areas": ["Science, Technology, Communications"],
        },
        "Social Issues": {
            "keywords": [
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
            "committees": [
                "judiciary",
                "oversight",
                "ways and means",
                "financial services",
            ],
            "policy_areas": [
                "Civil Rights and Liberties",
                "Crime and Law Enforcement",
                "Social Welfare",
            ],
        },
        "Foreign Policy": {
            "keywords": [
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
            "committees": [
                "foreign affairs",
                "armed services",
                "intelligence",
                "ways and means",
            ],
            "policy_areas": ["International Affairs"],
        },
    }

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the categorizer

        Args:
            base_dir: Base directory containing data files
        """
        self.base_dir = Path(base_dir)
        self.bills_data = []
        self.categorized_bills = defaultdict(list)

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

    def categorize_bill(
        self, bill: Dict, bill_details: Optional[Dict] = None
    ) -> Set[str]:
        """
        Categorize a single bill based on its content

        Args:
            bill: Bill data dictionary
            bill_details: Optional detailed data including subjects and committees

        Returns:
            Set of category names this bill belongs to
        """
        categories = set()

        # Get text content to analyze
        title = bill.get("title", "").lower()
        policy_area = bill.get("policyArea", {}).get("name", "").lower()

        # Get subjects if available
        subjects = []
        if bill_details:
            subjects_data = bill_details.get("subjects", {})
            if isinstance(subjects_data, dict):
                # Handle new structure with legislativeSubjects
                legislative_subjects = subjects_data.get("legislativeSubjects", [])
                for subj in legislative_subjects:
                    if isinstance(subj, dict):
                        subjects.append(subj.get("name", "").lower())
                    elif isinstance(subj, str):
                        subjects.append(subj.lower())
            elif isinstance(subjects_data, list):
                # Handle direct list structure
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
        for category, config in self.TOPIC_CATEGORIES.items():
            score = 0

            # Check keywords
            for keyword in config["keywords"]:
                if keyword.lower() in text_content:
                    score += 1

            # Check policy areas (higher weight)
            for policy_area_term in config.get("policy_areas", []):
                if policy_area_term.lower() in policy_area:
                    score += 3

            # Check committees (higher weight)
            for committee_term in config["committees"]:
                for committee in committees:
                    if committee_term.lower() in committee:
                        score += 2
                        break

            # Add category if score threshold is met
            if score >= 1:  # At least one match required
                categories.add(category)

        # If no categories matched, assign "Other"
        if not categories:
            categories.add("Other")

        return categories

    def categorize_all_bills(
        self, bill_details_data: Dict[str, Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Categorize all bills and group by category

        Args:
            bill_details_data: Dictionary of bill detail data

        Returns:
            Dictionary mapping category names to lists of bills
        """
        logger.info("Categorizing all bills...")

        categorized = defaultdict(list)

        for bill in self.bills_data:
            congress = bill.get("congress")
            bill_type = bill.get("type", "").lower()
            bill_number = bill.get("number")

            if not all([congress, bill_type, bill_number]):
                continue

            bill_id = f"{congress}_{bill_type}_{bill_number}"
            bill_details = bill_details_data.get(bill_id)

            # Categorize the bill
            categories = self.categorize_bill(bill, bill_details)

            # Add bill to each category it belongs to
            for category in categories:
                bill_with_categories = bill.copy()
                bill_with_categories["categories"] = list(categories)
                bill_with_categories["primary_category"] = list(categories)[
                    0
                ]  # First category as primary
                categorized[category].append(bill_with_categories)

        self.categorized_bills = categorized
        return dict(categorized)

    def analyze_party_focus_by_category(self) -> Dict[str, Any]:
        """
        Analyze which party focuses on which issues

        Returns:
            Dictionary with party focus analysis by category
        """
        logger.info("Analyzing party focus by category...")

        category_party_counts = defaultdict(lambda: defaultdict(int))

        for category, bills in self.categorized_bills.items():
            for bill in bills:
                sponsors = bill.get("sponsors", [])
                if sponsors:
                    primary_sponsor = sponsors[0]
                    party = primary_sponsor.get("party", "Unknown")
                    category_party_counts[category][party] += 1

        # Calculate percentages
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
        logger.info("Analyzing success rates by category...")

        category_success = defaultdict(
            lambda: {
                "total": 0,
                "enacted": 0,
                "parties": defaultdict(lambda: {"total": 0, "enacted": 0}),
            }
        )

        for category, bills in self.categorized_bills.items():
            for bill in bills:
                sponsors = bill.get("sponsors", [])
                if not sponsors:
                    continue

                primary_sponsor = sponsors[0]
                party = primary_sponsor.get("party", "Unknown")

                # Count total bills
                category_success[category]["total"] += 1
                category_success[category]["parties"][party]["total"] += 1

                # Check if bill became law
                laws = bill.get("laws", [])
                latest_action = bill.get("latestAction", {}).get("text", "").lower()

                if (
                    laws
                    or "became public law" in latest_action
                    or "became law" in latest_action
                ):
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

    def analyze_committee_activity_by_party(
        self, bill_details_data: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Analyze most active committees by party

        Args:
            bill_details_data: Dictionary of bill detail data

        Returns:
            Dictionary with committee activity analysis
        """
        logger.info("Analyzing committee activity by party...")

        party_committee_counts = defaultdict(lambda: defaultdict(int))

        for bill in self.bills_data:
            sponsors = bill.get("sponsors", [])
            if not sponsors:
                continue

            primary_sponsor = sponsors[0]
            party = primary_sponsor.get("party", "Unknown")

            congress = bill.get("congress")
            bill_type = bill.get("type", "").lower()
            bill_number = bill.get("number")

            if all([congress, bill_type, bill_number]):
                bill_id = f"{congress}_{bill_type}_{bill_number}"
                bill_details = bill_details_data.get(bill_id, {})

                committees = bill_details.get("committees", [])
                for committee in committees:
                    committee_name = committee.get("name", "")
                    if committee_name:
                        party_committee_counts[party][committee_name] += 1

        # Get top committees for each party
        party_committee_analysis = {}
        for party, committee_counts in party_committee_counts.items():
            sorted_committees = sorted(
                committee_counts.items(), key=lambda x: x[1], reverse=True
            )

            party_committee_analysis[party] = {
                "total_committee_assignments": sum(committee_counts.values()),
                "top_committees": sorted_committees[:10],  # Top 10 committees
                "committee_counts": dict(committee_counts),
            }

        return party_committee_analysis

    def analyze_trending_topics(self) -> Dict[str, Any]:
        """
        Analyze trending topics over time (by introduction date)

        Returns:
            Dictionary with trending topics analysis
        """
        logger.info("Analyzing trending topics...")

        # Group bills by year and category
        yearly_categories = defaultdict(lambda: defaultdict(int))

        for category, bills in self.categorized_bills.items():
            for bill in bills:
                intro_date = bill.get("introducedDate", "")
                if intro_date:
                    try:
                        year = intro_date.split("-")[0]
                        yearly_categories[year][category] += 1
                    except (IndexError, ValueError):
                        continue

        # Calculate trends
        trending_analysis = {
            "yearly_breakdown": dict(yearly_categories),
            "trending_categories": {},
            "declining_categories": {},
        }

        # Identify trending and declining categories
        years = sorted(yearly_categories.keys())
        if len(years) >= 2:
            for category in self.TOPIC_CATEGORIES:
                if category == "Other":
                    continue

                recent_counts = []
                for year in years[-2:]:  # Last 2 years
                    count = yearly_categories[year].get(category, 0)
                    recent_counts.append(count)

                if len(recent_counts) == 2 and recent_counts[0] > 0:
                    change_percent = (
                        (recent_counts[1] - recent_counts[0]) / recent_counts[0]
                    ) * 100

                    if change_percent > 20:  # Trending up
                        trending_analysis["trending_categories"][category] = {
                            "change_percent": round(change_percent, 1),
                            "previous_year_count": recent_counts[0],
                            "current_year_count": recent_counts[1],
                        }
                    elif change_percent < -20:  # Declining
                        trending_analysis["declining_categories"][category] = {
                            "change_percent": round(change_percent, 1),
                            "previous_year_count": recent_counts[0],
                            "current_year_count": recent_counts[1],
                        }

        return trending_analysis

    def save_categorized_bills(self, output_dir: str):
        """
        Save categorized bills to files

        Args:
            output_dir: Output directory for categorized bills
        """
        logger.info("Saving categorized bills...")

        categories_dir = Path(output_dir) / "bill_categories"
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
                "bills": bills,
            }

            with open(category_file, "w") as f:
                json.dump(category_data, f, indent=2, default=str)

            logger.debug(f"Saved {len(bills)} bills to {category_file}")

        # Save category index
        index_data = {
            "categories": {
                category: {
                    "count": len(bills),
                    "file": f"{category.lower().replace('/', '_').replace(' ', '_')}.json",
                }
                for category, bills in self.categorized_bills.items()
            },
            "total_bills": sum(len(bills) for bills in self.categorized_bills.values()),
            "last_updated": datetime.now().isoformat(),
        }

        with open(categories_dir / "index.json", "w") as f:
            json.dump(index_data, f, indent=2)

        logger.info(f"Saved categorized bills to {categories_dir}")

    def generate_analysis_report(
        self, congress: int = 118, max_bills: int = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive categorization analysis report

        Args:
            congress: Congress number to analyze
            max_bills: Maximum number of bills to analyze (for testing)

        Returns:
            Complete analysis report
        """
        logger.info(f"Generating categorization analysis for {congress}th Congress...")

        # Load bills data
        bills = self.load_bills_data(congress)

        if max_bills:
            bills = bills[:max_bills]
            logger.info(f"Limited analysis to {len(bills)} bills for testing")

        # Fetch detailed bill data (subjects and committees)
        api = CongressGovAPIv3()
        bill_details_data = api.get_bill_details_batch(bills, str(self.base_dir))

        # Categorize bills
        categorized_bills = self.categorize_all_bills(bill_details_data)

        # Run analyses
        party_focus_analysis = self.analyze_party_focus_by_category()
        success_analysis = self.analyze_success_rates_by_category()
        committee_analysis = self.analyze_committee_activity_by_party(bill_details_data)
        trending_analysis = self.analyze_trending_topics()

        # Calculate summary statistics
        total_categorized = sum(len(bills) for bills in categorized_bills.values())
        category_counts = {cat: len(bills) for cat, bills in categorized_bills.items()}
        top_categories = sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Compile report
        report = {
            "metadata": {
                "congress": congress,
                "analysis_date": datetime.now().isoformat(),
                "total_bills_analyzed": len(bills),
                "total_bills_categorized": total_categorized,
                "bills_with_detail_data": len(bill_details_data),
                "categories_defined": len(self.TOPIC_CATEGORIES),
            },
            "category_distribution": {
                "counts": category_counts,
                "top_categories": dict(top_categories),
            },
            "party_focus_by_category": party_focus_analysis,
            "success_rates_by_category": success_analysis,
            "committee_activity_by_party": committee_analysis,
            "trending_topics": trending_analysis,
            "summary": {
                "most_popular_category": (
                    top_categories[0][0] if top_categories else "Unknown"
                ),
                "most_popular_category_count": (
                    top_categories[0][1] if top_categories else 0
                ),
                "republican_top_category": self._get_party_top_category(
                    party_focus_analysis, "R"
                ),
                "democrat_top_category": self._get_party_top_category(
                    party_focus_analysis, "D"
                ),
                "highest_success_rate_category": self._get_highest_success_rate_category(
                    success_analysis
                ),
            },
        }

        return report

    def _get_party_top_category(self, party_focus_analysis: Dict, party: str) -> str:
        """Helper method to get top category for a party"""
        party_totals = {}
        for category, data in party_focus_analysis.items():
            party_count = data.get("party_counts", {}).get(party, 0)
            if party_count > 0:
                party_totals[category] = party_count

        if party_totals:
            return max(party_totals.items(), key=lambda x: x[1])[0]
        return "Unknown"

    def _get_highest_success_rate_category(self, success_analysis: Dict) -> str:
        """Helper method to get category with highest success rate"""
        if not success_analysis:
            return "Unknown"

        highest_rate = 0
        highest_category = "Unknown"

        for category, data in success_analysis.items():
            rate = data.get("overall_success_rate_percent", 0)
            if (
                rate > highest_rate and data.get("total_bills", 0) >= 5
            ):  # Minimum 5 bills for significance
                highest_rate = rate
                highest_category = category

        return highest_category


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
        description="Categorize congressional bills by topic and analyze patterns"
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
        help="Output file path (default: data/analysis/bill_categories_analysis.json)",
    )
    parser.add_argument(
        "--save-categories",
        action="store_true",
        help="Save categorized bills to separate files",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set output file path
    if not args.output_file:
        args.output_file = f"{args.output_dir}/analysis/bill_categories_analysis.json"

    # Initialize categorizer
    categorizer = BillCategorizer(args.output_dir)

    try:
        # Generate analysis report
        report = categorizer.generate_analysis_report(
            congress=args.congress, max_bills=args.max_bills
        )

        # Save categorized bills if requested
        if args.save_categories:
            categorizer.save_categorized_bills(args.output_dir)

        # Save analysis results
        save_analysis_results(report, args.output_file)

        # Print summary
        print(f"\n{'='*80}")
        print("BILL CATEGORIZATION ANALYSIS SUMMARY")
        print(f"{'='*80}")
        print(f"Congress: {report['metadata']['congress']}")
        print(f"Bills Analyzed: {report['metadata']['total_bills_analyzed']}")
        print(f"Bills Categorized: {report['metadata']['total_bills_categorized']}")
        print(f"Bills with Detail Data: {report['metadata']['bills_with_detail_data']}")
        print()

        # Category distribution
        print("TOP CATEGORIES:")
        for category, count in report["category_distribution"][
            "top_categories"
        ].items():
            print(f"  {category}: {count} bills")
        print()

        # Party focus
        print("PARTY FOCUS BY CATEGORY:")
        for category, data in list(report["party_focus_by_category"].items())[:5]:
            dominant_party = data["dominant_party"]
            party_counts = data["party_counts"]
            print(
                f"  {category}: Dominated by {dominant_party} "
                f"({party_counts.get(dominant_party, 0)} bills)"
            )
        print()

        # Success rates
        print("SUCCESS RATES BY CATEGORY (Top 5):")
        success_items = sorted(
            report["success_rates_by_category"].items(),
            key=lambda x: x[1]["overall_success_rate_percent"],
            reverse=True,
        )[:5]

        for category, data in success_items:
            if data["total_bills"] >= 3:  # Only show categories with enough bills
                print(
                    f"  {category}: {data['enacted_bills']}/{data['total_bills']} "
                    f"({data['overall_success_rate_percent']}%)"
                )
        print()

        # Trending topics
        trending_data = report["trending_topics"]
        if trending_data["trending_categories"]:
            print("TRENDING CATEGORIES (Growing):")
            for category, data in trending_data["trending_categories"].items():
                print(
                    f"  {category}: +{data['change_percent']}% "
                    f"({data['previous_year_count']} → {data['current_year_count']})"
                )
            print()

        if trending_data["declining_categories"]:
            print("DECLINING CATEGORIES:")
            for category, data in trending_data["declining_categories"].items():
                print(
                    f"  {category}: {data['change_percent']}% "
                    f"({data['previous_year_count']} → {data['current_year_count']})"
                )
            print()

        # Summary insights
        summary = report["summary"]
        print("KEY INSIGHTS:")
        print(
            f"  Most Popular Category: {summary['most_popular_category']} "
            f"({summary['most_popular_category_count']} bills)"
        )
        print(f"  Republican Top Category: {summary['republican_top_category']}")
        print(f"  Democrat Top Category: {summary['democrat_top_category']}")
        print(f"  Highest Success Rate: {summary['highest_success_rate_category']}")

        print(f"\n{'='*80}")
        print(f"Analysis results saved to: {args.output_file}")
        if args.save_categories:
            print(f"Categorized bills saved to: {args.output_dir}/bill_categories/")
        print(f"{'='*80}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
