#!/usr/bin/env python3
"""
Comprehensive Government Data Analyzer
Combines lobbying data from Senate.gov with voting data from Congress.gov
Shows relationships between lobbying, party affiliation, and voting patterns
"""

import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict

from analyze_bipartisan_cooperation import BipartisanCooperationAnalyzer
from analyze_committees import CommitteeAnalyzer

# Import new trend analyzers
from analyze_legislative_activity import LegislativeActivityAnalyzer
from analyze_member_consistency import MemberConsistencyAnalyzer
from fetch_committees import CommitteeFetcher

# Import our existing modules
from gov_data_analyzer import CongressGovAPI
from gov_data_downloader_v2 import CongressGovAPI as CongressGovAPIv2
from gov_data_downloader_v2 import SenateGovAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ComprehensiveAnalyzer:
    """Analyzes relationships between lobbying, party affiliation, and voting"""

    def __init__(self, base_dir: str = "data"):
        """Initialize the analyzer"""
        self.base_dir = Path(base_dir)
        self.congress_api = CongressGovAPI(max_workers=3)
        self.congress_api_v2 = CongressGovAPIv2()  # For bills fetching
        self.senate_api = SenateGovAPI()
        self.committee_fetcher = CommitteeFetcher(base_dir=base_dir)
        self.committee_analyzer = CommitteeAnalyzer(base_dir=base_dir)

        # Initialize trend analyzers
        self.legislative_analyzer = LegislativeActivityAnalyzer(base_dir=base_dir)
        self.bipartisan_analyzer = BipartisanCooperationAnalyzer(data_dir=base_dir)
        self.member_consistency_analyzer = MemberConsistencyAnalyzer(data_dir=base_dir)

    def fetch_comprehensive_data(
        self, congress: int = 118, max_items: int = 25
    ) -> Dict:
        """
        Fetch all relevant data for analysis

        Args:
            congress: Congress number
            max_items: Maximum items to fetch per category

        Returns:
            Dictionary with all fetched data
        """
        data = {
            "congress": congress,
            "fetch_date": datetime.now().isoformat(),
            "members": [],
            "votes": [],
            "bills": [],
            "lobbying": {"filings": [], "lobbyists": []},
        }

        # Fetch Congressional members with party info
        logger.info("Fetching Congressional members...")
        data["members"] = self.congress_api.get_members(
            congress=congress,
            max_members=max_items * 2,  # Get more members
            base_dir=str(self.base_dir),
        )

        # Fetch voting records
        logger.info("Fetching House voting records...")
        data["votes"] = self.congress_api.get_roll_call_votes_with_details(
            congress=congress,
            chamber="house",
            max_votes=max_items,
            base_dir=str(self.base_dir),
        )

        # Fetch bills (using the v2 API)
        logger.info("Fetching bills...")
        self.congress_api_v2.get_bills(
            congress=congress, max_results=max_items, base_dir=str(self.base_dir)
        )

        # Fetch committee data
        logger.info("Fetching committee data...")
        self.committee_fetcher.fetch_and_save_all(
            congress=congress, fetch_bills=True, max_bills_per_committee=max_items
        )

        # Fetch lobbying data
        logger.info("Fetching lobbying filings...")
        ld1_count = self.senate_api.get_filings(
            filing_type="LD-1", max_results=max_items, base_dir=str(self.base_dir)
        )

        ld2_count = self.senate_api.get_filings(
            filing_type="LD-2", max_results=max_items, base_dir=str(self.base_dir)
        )

        logger.info("Fetching lobbyists...")
        lobbyist_count = self.senate_api.get_lobbyists(
            max_results=max_items, base_dir=str(self.base_dir)
        )

        data["lobbying"]["filing_counts"] = {
            "LD-1": ld1_count,
            "LD-2": ld2_count,
            "lobbyists": lobbyist_count,
        }

        return data

    def analyze_party_voting_patterns(self) -> Dict:
        """
        Analyze voting patterns by party affiliation

        Returns:
            Analysis results
        """
        analysis = {
            "total_votes": 0,
            "party_unity": {},
            "bipartisan_bills": [],
            "partisan_bills": [],
            "swing_voters": [],
        }

        # Load House vote data
        votes_dir = self.base_dir / "house_votes_detailed"

        if not votes_dir.exists():
            logger.warning("No House vote data found")
            return analysis

        # Analyze each congress
        for congress_dir in votes_dir.iterdir():
            if congress_dir.is_dir():
                for vote_file in congress_dir.glob("*.json"):
                    if vote_file.name == "index.json":
                        continue

                    try:
                        with open(vote_file) as f:
                            vote = json.load(f)

                        analysis["total_votes"] += 1

                        # Analyze party breakdown
                        party_breakdown = vote.get("party_breakdown", {})

                        # Calculate party unity scores
                        for party, votes in party_breakdown.items():
                            total = sum(votes.values())
                            if total > 0:
                                # Unity = percentage voting with majority of party
                                majority_position = max(
                                    votes.items(), key=lambda x: x[1]
                                )
                                unity_score = (majority_position[1] / total) * 100

                                if party not in analysis["party_unity"]:
                                    analysis["party_unity"][party] = []
                                analysis["party_unity"][party].append(unity_score)

                        # Identify bipartisan vs partisan votes
                        is_bipartisan = self._is_bipartisan(party_breakdown)

                        vote_summary = {
                            "rollCall": vote.get("rollCall"),
                            "question": vote.get("question", "")[:100],
                            "date": vote.get("date"),
                            "party_breakdown": party_breakdown,
                        }

                        if is_bipartisan:
                            analysis["bipartisan_bills"].append(vote_summary)
                        else:
                            analysis["partisan_bills"].append(vote_summary)

                        # Identify swing voters
                        for member_vote in vote.get("member_votes", []):
                            member_party = member_vote.get("party", "")
                            member_position = member_vote.get("vote", "").lower()

                            # Check if member voted against party majority
                            if member_party in party_breakdown:
                                party_votes = party_breakdown[member_party]
                                party_majority = max(
                                    party_votes.items(), key=lambda x: x[1]
                                )[0]

                                if self._voted_against_party(
                                    member_position, party_majority
                                ):
                                    swing_vote = {
                                        "member": member_vote.get("name"),
                                        "party": member_party,
                                        "vote": member_position,
                                        "rollCall": vote.get("rollCall"),
                                        "question": vote.get("question", "")[:50],
                                    }
                                    analysis["swing_voters"].append(swing_vote)

                    except Exception as e:
                        logger.error(f"Error analyzing {vote_file}: {e}")

        # Calculate average party unity scores
        for party in analysis["party_unity"]:
            scores = analysis["party_unity"][party]
            if scores:
                analysis["party_unity"][party] = {
                    "average": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "votes_analyzed": len(scores),
                }

        # Sort bipartisan and partisan bills
        analysis["bipartisan_bills"] = sorted(
            analysis["bipartisan_bills"], key=lambda x: x.get("date", ""), reverse=True
        )[
            :10
        ]  # Keep top 10

        analysis["partisan_bills"] = sorted(
            analysis["partisan_bills"], key=lambda x: x.get("date", ""), reverse=True
        )[
            :10
        ]  # Keep top 10

        # Identify top swing voters
        swing_voter_counts = defaultdict(int)
        for swing in analysis["swing_voters"]:
            swing_voter_counts[swing["member"]] += 1

        analysis["top_swing_voters"] = sorted(
            [(member, count) for member, count in swing_voter_counts.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return analysis

    def _is_bipartisan(self, party_breakdown: Dict) -> bool:
        """Check if vote had significant bipartisan support"""
        dem_votes = party_breakdown.get("D", {})
        rep_votes = party_breakdown.get("R", {})

        dem_total = sum(dem_votes.values())
        rep_total = sum(rep_votes.values())

        if dem_total == 0 or rep_total == 0:
            return False

        dem_yea_pct = dem_votes.get("yea", 0) / dem_total if dem_total else 0
        rep_yea_pct = rep_votes.get("yea", 0) / rep_total if rep_total else 0

        # Bipartisan if both parties have > 30% support or > 30% opposition
        both_support = dem_yea_pct > 0.3 and rep_yea_pct > 0.3
        both_oppose = dem_yea_pct < 0.7 and rep_yea_pct < 0.7

        return both_support and both_oppose

    def _voted_against_party(self, member_position: str, party_majority: str) -> bool:
        """Check if member voted against party majority"""
        position_map = {
            "yea": ["yea", "aye", "yes"],
            "nay": ["nay", "no"],
            "present": ["present"],
            "not_voting": ["not voting", "not_voting"],
        }

        member_vote_type = None
        for vote_type, variations in position_map.items():
            if any(var in member_position.lower() for var in variations):
                member_vote_type = vote_type
                break

        return member_vote_type != party_majority and member_vote_type not in [
            "present",
            "not_voting",
        ]

    def analyze_lobbying_influence(self) -> Dict:
        """
        Analyze lobbying patterns and potential influence

        Returns:
            Analysis of lobbying activities
        """
        analysis = {
            "total_filings": 0,
            "top_issues": defaultdict(int),
            "top_registrants": defaultdict(int),
            "filing_trends": defaultdict(int),
            "lobbying_summary": {},
        }

        # Analyze LD-1 filings (registrations)
        ld1_dir = self.base_dir / "senate_filings" / "ld-1"
        if ld1_dir.exists():
            for filing_file in ld1_dir.glob("*.json"):
                if filing_file.name == "index.json":
                    continue

                try:
                    with open(filing_file) as f:
                        filing = json.load(f)

                    analysis["total_filings"] += 1

                    # Track registrants
                    registrant = filing.get("registrant_name", "Unknown")
                    analysis["top_registrants"][registrant] += 1

                    # Track issues
                    for issue in filing.get("lobbying_issues", []):
                        issue_code = issue.get("general_issue_code", "")
                        if issue_code:
                            analysis["top_issues"][issue_code] += 1

                    # Track filing trends by date
                    filed_date = filing.get("filed_date", "")
                    if filed_date:
                        month = filed_date[:7]  # YYYY-MM
                        analysis["filing_trends"][month] += 1

                except Exception as e:
                    logger.error(f"Error analyzing filing {filing_file}: {e}")

        # Get top items
        analysis["top_issues"] = dict(
            sorted(analysis["top_issues"].items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
        )

        analysis["top_registrants"] = dict(
            sorted(
                analysis["top_registrants"].items(), key=lambda x: x[1], reverse=True
            )[:10]
        )

        analysis["filing_trends"] = dict(sorted(analysis["filing_trends"].items()))

        return analysis

    def analyze_legislative_activity_trends(self, congress: int = 118) -> Dict:
        """
        Analyze legislative activity patterns and trends

        Returns:
            Legislative activity analysis results
        """
        logger.info("Analyzing legislative activity trends...")

        try:
            return self.legislative_analyzer.generate_analysis_report(congress)
        except Exception as e:
            logger.error(f"Error in legislative activity analysis: {e}")
            return {}

    def analyze_bipartisan_cooperation_trends(self) -> Dict:
        """
        Analyze bipartisan cooperation patterns

        Returns:
            Bipartisan cooperation analysis results
        """
        logger.info("Analyzing bipartisan cooperation trends...")

        try:
            return self.bipartisan_analyzer.run_full_analysis()
        except Exception as e:
            logger.error(f"Error in bipartisan cooperation analysis: {e}")
            return {}

    def analyze_member_consistency_trends(self) -> Dict:
        """
        Analyze member voting consistency patterns

        Returns:
            Member consistency analysis results
        """
        logger.info("Analyzing member consistency trends...")

        try:
            # Run full analysis and get the report
            self.member_consistency_analyzer.run_full_analysis()
            return self.member_consistency_analyzer.generate_analysis_report()
        except Exception as e:
            logger.error(f"Error in member consistency analysis: {e}")
            return {}

    def run_trend_analysis_pipeline(self, congress: int = 118) -> Dict:
        """
        Run just the trend analysis pipeline independently

        Args:
            congress: Congress number to analyze

        Returns:
            Dictionary with all trend analysis results
        """
        logger.info(
            f"Running comprehensive trend analysis pipeline for {congress}th Congress..."
        )

        trend_results = {
            "congress": congress,
            "generated_date": datetime.now().isoformat(),
            "trend_analyses": {},
        }

        # Run all trend analyses
        legislative_trends = self.analyze_legislative_activity_trends(congress)
        if legislative_trends:
            trend_results["trend_analyses"]["legislative_activity"] = legislative_trends

        bipartisan_trends = self.analyze_bipartisan_cooperation_trends()
        if bipartisan_trends:
            trend_results["trend_analyses"][
                "bipartisan_cooperation"
            ] = bipartisan_trends

        consistency_trends = self.analyze_member_consistency_trends()
        if consistency_trends:
            trend_results["trend_analyses"]["member_consistency"] = consistency_trends

        # Save trend analysis results
        trends_path = self.base_dir / "analysis" / "trend_analysis_comprehensive.json"
        trends_path.parent.mkdir(parents=True, exist_ok=True)

        with open(trends_path, "w") as f:
            json.dump(trend_results, f, indent=2, default=str)

        logger.info(f"Trend analysis pipeline complete. Results saved to {trends_path}")

        return trend_results

    def generate_comprehensive_report(
        self, congress: int = 118, include_trends: bool = True
    ) -> Dict:
        """
        Generate a comprehensive analysis report

        Args:
            congress: Congress number to analyze
            include_trends: Whether to include trend analyses

        Returns:
            Complete analysis report
        """
        logger.info(
            f"Generating comprehensive analysis report for {congress}th Congress..."
        )

        report = {
            "generated_date": datetime.now().isoformat(),
            "data_location": str(self.base_dir),
            "congress": congress,
            "analyses": {},
        }

        # Party voting analysis
        logger.info("Analyzing party voting patterns...")
        report["analyses"]["party_voting"] = self.analyze_party_voting_patterns()

        # Lobbying analysis
        logger.info("Analyzing lobbying influence...")
        report["analyses"]["lobbying"] = self.analyze_lobbying_influence()

        # Member statistics
        logger.info("Analyzing member statistics...")
        report["analyses"]["members"] = self._analyze_member_stats()

        # Committee analysis
        logger.info("Analyzing committee data...")
        committee_report = self.committee_analyzer.generate_comprehensive_report()
        report["analyses"]["committees"] = committee_report.get("analyses", {})
        report["analyses"]["committee_insights"] = committee_report.get(
            "key_insights", []
        )

        # Trend analyses - new comprehensive trend analysis pipeline
        if include_trends:
            logger.info("Running trend analysis pipeline...")

            # Legislative activity trends
            logger.info("Generating legislative activity trends...")
            legislative_trends = self.analyze_legislative_activity_trends(congress)
            if legislative_trends:
                report["analyses"]["legislative_trends"] = {
                    "sponsorship_patterns": legislative_trends.get(
                        "sponsorship_patterns", {}
                    ),
                    "metadata": legislative_trends.get("metadata", {}),
                    "congress": legislative_trends.get("congress", congress),
                }

            # Bipartisan cooperation trends
            logger.info("Generating bipartisan cooperation trends...")
            bipartisan_trends = self.analyze_bipartisan_cooperation_trends()
            if bipartisan_trends:
                report["analyses"]["bipartisan_trends"] = {
                    "cooperation_metrics": bipartisan_trends.get(
                        "cooperation_metrics", {}
                    ),
                    "summary_statistics": bipartisan_trends.get(
                        "summary_statistics", {}
                    ),
                    "insights": bipartisan_trends.get("insights", {}),
                    "congress": bipartisan_trends.get("congress", congress),
                }

            # Member consistency trends
            logger.info("Generating member consistency trends...")
            consistency_trends = self.analyze_member_consistency_trends()
            if consistency_trends:
                report["analyses"]["consistency_trends"] = {
                    "aggregate_statistics": consistency_trends.get(
                        "aggregate_statistics", {}
                    ),
                    "rankings": consistency_trends.get("rankings", {}),
                    "bipartisan_collaboration": consistency_trends.get(
                        "bipartisan_collaboration", {}
                    ),
                    "insights": consistency_trends.get("insights", {}),
                    "congress": consistency_trends.get("metadata", {}).get(
                        "congress", congress
                    ),
                }
        else:
            logger.info("Skipping trend analysis pipeline (include_trends=False)")

        # Save report
        report_path = self.base_dir / "analysis" / "comprehensive_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Report saved to {report_path}")

        return report

    def _analyze_member_stats(self) -> Dict:
        """Analyze member statistics"""
        stats = {
            "total_members": 0,
            "by_party": defaultdict(int),
            "by_state": defaultdict(lambda: defaultdict(int)),
            "by_chamber": defaultdict(lambda: defaultdict(int)),
        }

        members_dir = self.base_dir / "members"

        if members_dir.exists():
            for congress_dir in members_dir.iterdir():
                if congress_dir.is_dir():
                    # Load summary if available
                    summary_file = congress_dir / "summary.json"
                    if summary_file.exists():
                        with open(summary_file) as f:
                            summary = json.load(f)
                            stats["total_members"] = summary.get("total", 0)
                            stats["by_party"] = summary.get("by_party", {})
                            stats["by_state"] = summary.get("by_state", {})
                            stats["by_chamber"] = summary.get("by_chamber", {})

        return dict(stats)


def print_report_summary(report: Dict):
    """Print a human-readable summary of the report"""

    print("\n" + "=" * 80)
    print("COMPREHENSIVE GOVERNMENT DATA ANALYSIS")
    print("=" * 80)

    # Party voting analysis
    if "party_voting" in report.get("analyses", {}):
        voting = report["analyses"]["party_voting"]

        print("\n📊 PARTY VOTING PATTERNS")
        print("-" * 40)

        total_votes = voting.get("total_votes", 0)
        print(f"Total Votes Analyzed: {total_votes}")

        if voting.get("party_unity"):
            print("\nParty Unity Scores:")
            for party, scores in voting["party_unity"].items():
                if isinstance(scores, dict):
                    print(f"  {party}: {scores.get('average', 0):.1f}% average unity")

        bipartisan_count = len(voting.get("bipartisan_bills", []))
        partisan_count = len(voting.get("partisan_bills", []))

        if total_votes > 0:
            bipartisan_pct = (bipartisan_count / total_votes) * 100
            print(f"\nBipartisan Votes: {bipartisan_count} ({bipartisan_pct:.1f}%)")
            print(f"Partisan Votes: {partisan_count}")

        if voting.get("top_swing_voters"):
            print("\nTop Swing Voters (vote against party):")
            for member, count in voting["top_swing_voters"][:5]:
                print(f"  • {member}: {count} times")

    # Lobbying analysis
    if "lobbying" in report.get("analyses", {}):
        lobbying = report["analyses"]["lobbying"]

        print("\n💼 LOBBYING ACTIVITY")
        print("-" * 40)

        print(f"Total Filings: {lobbying.get('total_filings', 0)}")

        if lobbying.get("top_issues"):
            print("\nTop Lobbying Issues:")
            for issue, count in list(lobbying["top_issues"].items())[:5]:
                print(f"  • {issue}: {count} filings")

        if lobbying.get("top_registrants"):
            print("\nTop Lobbying Registrants:")
            for registrant, count in list(lobbying["top_registrants"].items())[:5]:
                print(f"  • {registrant[:50]}: {count} filings")

    # Member statistics
    if "members" in report.get("analyses", {}):
        members = report["analyses"]["members"]

        print("\n👥 CONGRESSIONAL MEMBERS")
        print("-" * 40)

        print(f"Total Members: {members.get('total_members', 0)}")

        if members.get("by_party"):
            print("\nBy Party:")
            for party, count in members["by_party"].items():
                print(f"  • {party}: {count}")

        if members.get("by_chamber"):
            print("\nBy Chamber:")
            for chamber, parties in members["by_chamber"].items():
                print(f"  {chamber.capitalize()}:")
                for party, count in parties.items():
                    print(f"    • {party}: {count}")

    # Trend analysis results - new comprehensive trend reporting
    if "legislative_trends" in report.get("analyses", {}):
        legislative = report["analyses"]["legislative_trends"]

        print("\n📈 LEGISLATIVE ACTIVITY TRENDS")
        print("-" * 40)

        sponsorship = legislative.get("sponsorship_patterns", {}).get("by_party", {})
        if sponsorship:
            print("Sponsorship by Party:")
            for party, stats in sponsorship.items():
                total_bills = stats.get("total_bills_sponsored", 0)
                bipartisan = stats.get("bipartisan_sponsored", 0)
                avg_cosponsors = stats.get("avg_cosponsors", 0)
                print(
                    f"  {party}: {total_bills} bills, {bipartisan} bipartisan ({avg_cosponsors} avg cosponsors)"
                )

    if "bipartisan_trends" in report.get("analyses", {}):
        bipartisan = report["analyses"]["bipartisan_trends"]

        print("\n🤝 BIPARTISAN COOPERATION TRENDS")
        print("-" * 40)

        cooperation = bipartisan.get("cooperation_metrics", {})
        bipartisan_rate = cooperation.get("overall_bipartisan_rate", 0)
        print(f"Overall Bipartisan Rate: {bipartisan_rate:.1%}")

        bridge_builders = cooperation.get("bridge_builders", [])
        if bridge_builders:
            print(f"Top Bridge Builders ({len(bridge_builders)} identified):")
            for i, builder in enumerate(bridge_builders[:5], 1):
                name = builder.get("name", "Unknown")
                party = builder.get("party", "U")
                score = builder.get("bipartisan_score", 0)
                print(f"  {i}. {name} ({party}): {score:.1%} bipartisan score")

    if "consistency_trends" in report.get("analyses", {}):
        consistency = report["analyses"]["consistency_trends"]

        print("\n⚖️ MEMBER CONSISTENCY TRENDS")
        print("-" * 40)

        stats = consistency.get("aggregate_statistics", {})
        total_analyzed = stats.get("total_members_analyzed", 0)
        avg_unity = stats.get("average_party_unity", 0)
        maverick_count = stats.get("maverick_count", 0)
        loyalist_count = stats.get("loyalist_count", 0)

        print(f"Members Analyzed: {total_analyzed}")
        print(f"Average Party Unity: {avg_unity:.1%}")
        print(f"Mavericks: {maverick_count}, Loyalists: {loyalist_count}")

        # Top rankings
        rankings = consistency.get("rankings", {})
        top_loyal = rankings.get("most_loyal", [])
        if top_loyal:
            print("Most Loyal Members:")
            for member in top_loyal[:3]:
                name = member.get("name", "Unknown")
                party = member.get("party", "U")
                score = member.get("score", 0)
                print(f"  • {name} ({party}): {score:.1%}")

    print("\n" + "=" * 80)
    print("DATA INSIGHTS FOR WEBSITE")
    print("=" * 80)

    print(
        """
This comprehensive analysis enables your website to provide advanced insights:

1. **Show Party-Based Voting Patterns**
   - Display how Democrats vs Republicans vote on key issues
   - Highlight bipartisan vs partisan legislation
   - Identify swing voters who break party lines
   - Track voting consistency trends over time

2. **Track Individual Representatives**
   - Show each member's voting record and party unity score
   - Compare votes to party position
   - Display state representation patterns
   - Identify mavericks vs loyalists
   - Show member consistency ratings

3. **Analyze Legislative Activity Trends**
   - Track sponsorship patterns by party
   - Show monthly legislative activity trends
   - Identify most active sponsors
   - Analyze bipartisan cooperation rates
   - Display policy area focus by party

4. **Monitor Bipartisan Cooperation**
   - Track overall bipartisan cooperation rates
   - Identify "bridge builder" members with high cross-party collaboration
   - Show top bipartisan policy areas
   - Display monthly cooperation trends
   - Analyze cross-party cosponsorship patterns

5. **Analyze Lobbying Influence**
   - Show which issues receive most lobbying attention
   - Track lobbying registrations over time
   - Identify major lobbying organizations
   - Correlate lobbying with voting patterns

6. **Enable Advanced Citizen Engagement**
   - Let users search votes by their representatives
   - Show how their state's delegation votes
   - Compare voting records across parties and states
   - Display member consistency and bipartisan scores
   - Show temporal trends in legislative activity

7. **Provide Comprehensive Transparency Metrics**
   - Party unity scores and maverick identification
   - Bipartisanship ratings and bridge builder rankings
   - Lobbying activity levels and influence patterns
   - Legislative productivity and cooperation trends
   - Temporal analysis of congressional behavior
"""
    )

    print("=" * 80)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Comprehensive government data analysis"
    )
    parser.add_argument("--fetch", action="store_true", help="Fetch new data")
    parser.add_argument("--analyze", action="store_true", help="Analyze existing data")
    parser.add_argument(
        "--trends-only", action="store_true", help="Run only trend analysis pipeline"
    )
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument(
        "--max-items", type=int, default=25, help="Maximum items to fetch per category"
    )
    parser.add_argument("--output-dir", default="data", help="Output directory")

    args = parser.parse_args()

    # If no action specified, do both (unless trends-only is specified)
    if not args.fetch and not args.analyze and not args.trends_only:
        args.fetch = True
        args.analyze = True

    # Initialize analyzer
    analyzer = ComprehensiveAnalyzer(base_dir=args.output_dir)

    # Handle trends-only mode
    if args.trends_only:
        logger.info("Running trends-only analysis pipeline...")
        trend_results = analyzer.run_trend_analysis_pipeline(congress=args.congress)
        print("\n" + "=" * 70)
        print("TREND ANALYSIS PIPELINE COMPLETE")
        print("=" * 70)
        print(f"Congress: {trend_results['congress']}")
        print(f"Generated: {trend_results['generated_date'][:10]}")
        print(f"Analyses completed: {len(trend_results['trend_analyses'])}")
        for analysis_name in trend_results["trend_analyses"]:
            print(f"  ✅ {analysis_name.replace('_', ' ').title()}")
        print("=" * 70)
        return

    # Fetch data if requested
    if args.fetch:
        logger.info(f"Fetching comprehensive data for {args.congress}th Congress...")
        analyzer.fetch_comprehensive_data(
            congress=args.congress, max_items=args.max_items
        )
        logger.info("Data fetching complete!")

    # Analyze data if requested
    if args.analyze:
        logger.info("Performing comprehensive analysis...")
        report = analyzer.generate_comprehensive_report(
            congress=args.congress, include_trends=True
        )
        print_report_summary(report)

    logger.info("Analysis complete! Check data/ directory for detailed results.")


if __name__ == "__main__":
    main()
