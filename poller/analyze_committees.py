#!/usr/bin/env python3
"""
Analyze committee data including memberships, activity, and effectiveness.
"""

import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CommitteeAnalyzer:
    """Analyzes committee data and generates insights."""

    def __init__(self, base_dir: str = "data"):
        """Initialize the analyzer with data directory."""
        self.base_dir = Path(base_dir)
        self.committees_dir = self.base_dir / "committees"
        self.bills_dir = self.base_dir / "congress_bills"
        self.members_dir = self.base_dir / "members"
        self.committee_bills_dir = self.base_dir / "committee_bills"
        self.analysis_dir = self.base_dir / "analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def load_committees(self, congress: int = 118) -> Dict[str, List[Dict]]:
        """Load all committees for a given congress."""
        committees = {}
        congress_dir = self.committees_dir / str(congress)

        for chamber in ["house", "senate", "joint"]:
            chamber_dir = congress_dir / chamber
            if not chamber_dir.exists():
                continue

            chamber_committees = []
            for file in chamber_dir.glob("*.json"):
                if file.name == "index.json":
                    continue

                with open(file) as f:
                    committee = json.load(f)
                    committee["chamber"] = chamber
                    chamber_committees.append(committee)

            committees[chamber] = chamber_committees

        return committees

    def load_bills_with_committees(self, congress: int = 118) -> List[Dict]:
        """Load bills that have committee assignments."""
        bills = []
        bills_dir = self.bills_dir / str(congress)

        if not bills_dir.exists():
            return bills

        for file in bills_dir.glob("*.json"):
            if file.name == "index.json":
                continue

            with open(file) as f:
                bill = json.load(f)
                if "committees" in bill and bill["committees"]:
                    bills.append(bill)

        return bills

    def load_members(self, congress: int = 118) -> Dict[str, Dict]:
        """Load member data."""
        members = {}
        members_dir = self.members_dir / str(congress)

        if not members_dir.exists():
            return members

        for file in members_dir.glob("*.json"):
            if file.name in ["index.json", "summary.json"]:
                continue

            with open(file) as f:
                member = json.load(f)
                bio_id = member.get("bioguideId", "")
                if bio_id:
                    members[bio_id] = member

        return members

    def analyze_committee_structure(self, committees: Dict[str, List[Dict]]) -> Dict:
        """Analyze committee structure and hierarchy."""
        analysis = {
            "total_committees": 0,
            "total_subcommittees": 0,
            "by_chamber": {},
            "largest_committees": [],
            "committee_types": Counter(),
        }

        for chamber, committee_list in committees.items():
            chamber_stats = {
                "committees": 0,
                "subcommittees": 0,
                "standing": 0,
                "select": 0,
                "special": 0,
                "joint": 0,
            }

            for committee in committee_list:
                if committee.get("parent"):
                    chamber_stats["subcommittees"] += 1
                    analysis["total_subcommittees"] += 1
                else:
                    chamber_stats["committees"] += 1
                    analysis["total_committees"] += 1

                # Count by type
                committee_type = committee.get("type", "unknown").lower()
                chamber_stats[committee_type] = chamber_stats.get(committee_type, 0) + 1
                analysis["committee_types"][committee_type] += 1

            analysis["by_chamber"][chamber] = chamber_stats

        return analysis

    def analyze_committee_activity(
        self, committees: Dict[str, List[Dict]], bills: List[Dict]
    ) -> Dict:
        """Analyze committee activity based on bill assignments."""
        activity = {
            "most_active_committees": Counter(),
            "committee_bill_counts": {},
            "bills_by_committee_type": defaultdict(int),
            "average_committees_per_bill": 0,
            "bills_with_multiple_committees": 0,
        }

        committees_per_bill = []

        for bill in bills:
            bill_committees = bill.get("committees", [])
            committees_per_bill.append(len(bill_committees))

            if len(bill_committees) > 1:
                activity["bills_with_multiple_committees"] += 1

            for committee in bill_committees:
                name = committee.get("name", "Unknown")
                code = committee.get("systemCode", committee.get("code", ""))
                chamber = committee.get("chamber", "").lower()

                # Count by committee
                activity["most_active_committees"][name] += 1

                if code not in activity["committee_bill_counts"]:
                    activity["committee_bill_counts"][code] = {
                        "name": name,
                        "chamber": chamber,
                        "bill_count": 0,
                        "bills": [],
                    }

                activity["committee_bill_counts"][code]["bill_count"] += 1

                # Track bill IDs
                bill_id = (
                    f"{bill.get('congress')}_{bill.get('type')}_{bill.get('number')}"
                )
                activity["committee_bill_counts"][code]["bills"].append(bill_id)

        if committees_per_bill:
            activity["average_committees_per_bill"] = sum(committees_per_bill) / len(
                committees_per_bill
            )

        # Get top 10 most active committees
        activity["top_10_committees"] = activity["most_active_committees"].most_common(
            10
        )

        return activity

    def analyze_committee_party_composition(
        self, committees: Dict[str, List[Dict]], members: Dict[str, Dict]
    ) -> Dict:
        """Analyze party composition of committees (if membership data available)."""
        # Note: This requires committee membership data which would need to be fetched separately
        # For now, return a placeholder structure
        return {
            "note": "Committee membership data needs to be fetched separately",
            "placeholder": True,
        }

    def analyze_committee_effectiveness(
        self, committees: Dict[str, List[Dict]], bills: List[Dict]
    ) -> Dict:
        """Analyze committee effectiveness based on bill outcomes."""
        effectiveness = {
            "bills_by_status": defaultdict(lambda: defaultdict(int)),
            "committee_success_rates": {},
            "bills_became_law": [],
        }

        for bill in bills:
            status = "active"  # Default status

            # Check if bill became law
            if bill.get("laws"):
                status = "became_law"
                effectiveness["bills_became_law"].append(
                    {
                        "bill_id": f"{bill.get('congress')}_{bill.get('type')}_{bill.get('number')}",
                        "title": bill.get("title"),
                        "committees": [
                            c.get("name") for c in bill.get("committees", [])
                        ],
                    }
                )
            elif "latestAction" in bill:
                action_text = bill["latestAction"].get("text", "").lower()
                if (
                    "passed" in action_text
                    and "house" in action_text
                    and "senate" in action_text
                ):
                    status = "passed_both"
                elif "passed" in action_text:
                    status = "passed_one"
                elif "failed" in action_text or "rejected" in action_text:
                    status = "failed"

            # Count by committee
            for committee in bill.get("committees", []):
                code = committee.get("systemCode", committee.get("code", "unknown"))
                effectiveness["bills_by_status"][code][status] += 1

        # Calculate success rates
        for code, statuses in effectiveness["bills_by_status"].items():
            total = sum(statuses.values())
            if total > 0:
                effectiveness["committee_success_rates"][code] = {
                    "total_bills": total,
                    "became_law": statuses.get("became_law", 0),
                    "passed_both": statuses.get("passed_both", 0),
                    "passed_one": statuses.get("passed_one", 0),
                    "success_rate": (statuses.get("became_law", 0) / total) * 100,
                }

        return effectiveness

    def _extract_policy_area(self, bill: Dict) -> Optional[str]:
        """Extract policy area from bill data."""
        if "policyArea" not in bill:
            return None

        policy_area = bill["policyArea"]
        if isinstance(policy_area, dict):
            return policy_area.get("name")
        return policy_area

    def _extract_subjects(self, bill: Dict) -> List[str]:
        """Extract subjects from bill data."""
        if "subjects" not in bill:
            return []

        subjects_data = bill["subjects"]
        subjects = []

        if isinstance(subjects_data, dict):
            subjects = subjects_data.get("legislativeSubjects", [])
            if isinstance(subjects, dict):
                subjects = subjects.get("legislativeSubject", [])
        elif isinstance(subjects_data, list):
            subjects = subjects_data

        # Normalize subject names
        subject_names = []
        for subject in subjects:
            if isinstance(subject, dict):
                subject_name = subject.get("name", "")
            else:
                subject_name = str(subject)

            if subject_name:
                subject_names.append(subject_name)

        return subject_names

    def analyze_committee_topics(
        self, committees: Dict[str, List[Dict]], bills: List[Dict]
    ) -> Dict:
        """Analyze topics handled by different committees."""
        topics = {
            "committees_by_policy_area": defaultdict(set),
            "policy_areas_by_committee": defaultdict(set),
            "most_common_subjects": Counter(),
        }

        for bill in bills:
            # Extract policy area and subjects using helper methods
            policy_area = self._extract_policy_area(bill)
            subjects = self._extract_subjects(bill)

            # Map to committees
            for committee in bill.get("committees", []):
                name = committee.get("name", "Unknown")
                code = committee.get("systemCode", committee.get("code", ""))

                if policy_area:
                    topics["committees_by_policy_area"][policy_area].add(name)
                    topics["policy_areas_by_committee"][code].add(policy_area)

                for subject_name in subjects:
                    topics["most_common_subjects"][subject_name] += 1

        # Convert sets to lists for JSON serialization
        topics["committees_by_policy_area"] = {
            k: list(v) for k, v in topics["committees_by_policy_area"].items()
        }
        topics["policy_areas_by_committee"] = {
            k: list(v) for k, v in topics["policy_areas_by_committee"].items()
        }

        # Get top subjects
        topics["top_20_subjects"] = topics["most_common_subjects"].most_common(20)

        return topics

    def generate_comprehensive_report(self, congress: int = 118) -> Dict:
        """Generate a comprehensive committee analysis report."""
        logger.info(
            f"Generating comprehensive committee analysis for Congress {congress}"
        )

        # Load data
        committees = self.load_committees(congress)
        bills = self.load_bills_with_committees(congress)
        members = self.load_members(congress)

        logger.info(f"Loaded {sum(len(c) for c in committees.values())} committees")
        logger.info(f"Loaded {len(bills)} bills with committee assignments")
        logger.info(f"Loaded {len(members)} members")

        # Run analyses
        report = {
            "metadata": {
                "congress": congress,
                "generated_at": datetime.now().isoformat(),
                "data_sources": {
                    "committees_count": sum(len(c) for c in committees.values()),
                    "bills_with_committees": len(bills),
                    "members_count": len(members),
                },
            },
            "analyses": {},
        }

        # Committee structure
        logger.info("Analyzing committee structure...")
        report["analyses"]["structure"] = self.analyze_committee_structure(committees)

        # Committee activity
        logger.info("Analyzing committee activity...")
        report["analyses"]["activity"] = self.analyze_committee_activity(
            committees, bills
        )

        # Committee effectiveness
        logger.info("Analyzing committee effectiveness...")
        report["analyses"]["effectiveness"] = self.analyze_committee_effectiveness(
            committees, bills
        )

        # Committee topics
        logger.info("Analyzing committee topics...")
        report["analyses"]["topics"] = self.analyze_committee_topics(committees, bills)

        # Party composition (placeholder for now)
        report["analyses"]["party_composition"] = (
            self.analyze_committee_party_composition(committees, members)
        )

        # Key insights
        report["key_insights"] = self.generate_key_insights(report["analyses"])

        return report

    def generate_key_insights(self, analyses: Dict) -> List[str]:
        """Generate key insights from the analyses."""
        insights = []

        # Structure insights
        structure = analyses.get("structure", {})
        if structure:
            total = structure.get("total_committees", 0) + structure.get(
                "total_subcommittees", 0
            )
            insights.append(f"Congress has {total} total committees and subcommittees")

        # Activity insights
        activity = analyses.get("activity", {})
        if activity:
            avg_committees = activity.get("average_committees_per_bill", 0)
            insights.append(
                f"Bills are referred to an average of {avg_committees:.1f} committees"
            )

            multi_committee = activity.get("bills_with_multiple_committees", 0)
            insights.append(f"{multi_committee} bills involve multiple committees")

            if activity.get("top_10_committees"):
                top_committee = activity["top_10_committees"][0]
                insights.append(
                    f"Most active committee: {top_committee[0]} with {top_committee[1]} bills"
                )

        # Effectiveness insights
        effectiveness = analyses.get("effectiveness", {})
        if effectiveness:
            laws_count = len(effectiveness.get("bills_became_law", []))
            insights.append(f"{laws_count} bills with committee assignments became law")

        # Topic insights
        topics = analyses.get("topics", {})
        if topics and topics.get("top_20_subjects"):
            top_subject = topics["top_20_subjects"][0]
            insights.append(
                f"Most common bill subject: {top_subject[0]} ({top_subject[1]} occurrences)"
            )

        return insights

    def save_report(self, report: Dict, filename: str = "committee_analysis.json"):
        """Save the analysis report to a file."""
        filepath = self.analysis_dir / filename
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Report saved to {filepath}")
        return filepath


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Analyze committee data")
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument("--base-dir", default="data", help="Base data directory")
    parser.add_argument("--output", help="Output file name")

    args = parser.parse_args()

    analyzer = CommitteeAnalyzer(base_dir=args.base_dir)
    report = analyzer.generate_comprehensive_report(congress=args.congress)

    # Print key insights
    print("\n" + "=" * 60)
    print(f"Committee Analysis for {args.congress}th Congress")
    print("=" * 60)

    for insight in report["key_insights"]:
        print(f"• {insight}")

    print("\n" + "-" * 60)
    print("Top 10 Most Active Committees:")
    print("-" * 60)

    for i, (name, count) in enumerate(
        report["analyses"]["activity"]["top_10_committees"], 1
    ):
        print(f"{i:2}. {name}: {count} bills")

    # Save report
    output_file = args.output or f"committee_analysis_{args.congress}.json"
    filepath = analyzer.save_report(report, output_file)

    print("\n" + "=" * 60)
    print(f"Full report saved to: {filepath}")
    print("=" * 60)


if __name__ == "__main__":
    main()
