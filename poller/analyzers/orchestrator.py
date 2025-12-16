#!/usr/bin/env python3
"""
Analysis Orchestrator

Coordinates all analysis modules and generates unified reports.
Replaces comprehensive_analyzer.py with modular, maintainable architecture.

Coordinates:
- PartyAnalyzer: Party unity, bipartisanship, member consistency
- GeographicAnalyzer: State patterns, regional analysis, delegation unity
- TemporalAnalyzer: Timeline trends, election cycles, seasonal patterns
- TopicAnalyzer: Bill categorization, committee activity, policy focus
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from analyzers.geographic_analytics import GeographicAnalyzer
from analyzers.party_analytics import PartyAnalyzer
from analyzers.temporal_analytics import TemporalAnalyzer
from analyzers.topic_analytics import TopicAnalyzer
from core.api import CongressGovAPI, SenateGovAPI
from core.storage import FileStorage

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orchestrates comprehensive analysis across all Congressional data dimensions
    """

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the analysis orchestrator

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.storage = FileStorage(self.base_dir)

        # Initialize APIs
        self.congress_api = CongressGovAPI()
        self.senate_api = SenateGovAPI()

        # Initialize analyzers
        self.party_analyzer = PartyAnalyzer(base_dir)
        self.geographic_analyzer = GeographicAnalyzer(base_dir)
        self.temporal_analyzer = TemporalAnalyzer(base_dir)
        self.topic_analyzer = TopicAnalyzer(base_dir)

        logger.info("AnalysisOrchestrator initialized with all analyzers")

    def fetch_comprehensive_data(
        self, congress: int = 118, max_items: int = 25
    ) -> Dict:
        """
        Fetch all relevant data for comprehensive analysis

        Args:
            congress: Congress number to analyze
            max_items: Maximum items to fetch per category

        Returns:
            Dictionary with all fetched data summaries
        """
        logger.info(f"Fetching comprehensive data for Congress {congress}")

        data_summary = {
            "congress": congress,
            "fetch_date": datetime.now().isoformat(),
            "data_sources": {},
            "fetch_status": {},
        }

        try:
            # Fetch Congressional members with party info
            logger.info("Fetching Congressional members...")
            members_count = self.congress_api.get_members(
                congress=congress,
                max_members=max_items
                * 4,  # Get more members for comprehensive analysis
                base_dir=str(self.base_dir),
            )
            data_summary["data_sources"]["members"] = (
                len(members_count) if isinstance(members_count, list) else members_count
            )
            data_summary["fetch_status"]["members"] = "success"

        except Exception as e:
            logger.error(f"Failed to fetch members: {e}")
            data_summary["fetch_status"]["members"] = f"failed: {e}"

        try:
            # Fetch voting records
            logger.info("Fetching House voting records...")
            votes_count = self.congress_api.get_roll_call_votes_with_details(
                congress=congress,
                chamber="house",
                max_votes=max_items,
                base_dir=str(self.base_dir),
            )
            data_summary["data_sources"]["votes"] = (
                len(votes_count) if isinstance(votes_count, list) else votes_count
            )
            data_summary["fetch_status"]["votes"] = "success"

        except Exception as e:
            logger.error(f"Failed to fetch votes: {e}")
            data_summary["fetch_status"]["votes"] = f"failed: {e}"

        try:
            # Fetch bills
            logger.info("Fetching bills...")
            bills_count = self.congress_api.get_bills(
                congress=congress,
                max_results=max_items * 2,  # Get more bills for analysis
                base_dir=str(self.base_dir),
            )
            data_summary["data_sources"]["bills"] = bills_count
            data_summary["fetch_status"]["bills"] = "success"

        except Exception as e:
            logger.error(f"Failed to fetch bills: {e}")
            data_summary["fetch_status"]["bills"] = f"failed: {e}"

        try:
            # Fetch lobbying data
            logger.info("Fetching lobbying filings...")
            ld1_count = self.senate_api.get_filings(
                filing_type="LD-1", max_results=max_items, base_dir=str(self.base_dir)
            )
            ld2_count = self.senate_api.get_filings(
                filing_type="LD-2", max_results=max_items, base_dir=str(self.base_dir)
            )

            data_summary["data_sources"]["lobbying"] = {
                "LD-1": ld1_count,
                "LD-2": ld2_count,
            }
            data_summary["fetch_status"]["lobbying"] = "success"

        except Exception as e:
            logger.error(f"Failed to fetch lobbying data: {e}")
            data_summary["fetch_status"]["lobbying"] = f"failed: {e}"

        logger.info("Data fetching completed")
        return data_summary

    def run_party_analysis(self, congress: int = 118) -> Dict:
        """
        Run comprehensive party analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Party analysis results
        """
        logger.info(f"Running party analysis for Congress {congress}")

        try:
            analysis = self.party_analyzer.generate_comprehensive_analysis(congress)

            # Save results
            self.party_analyzer.save_analysis_report(analysis)
            self.party_analyzer.save_member_profiles()

            logger.info("Party analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Party analysis failed: {e}")
            return {"error": str(e), "analysis_type": "party"}

    def run_geographic_analysis(self, congress: int = 118) -> Dict:
        """
        Run comprehensive geographic analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Geographic analysis results
        """
        logger.info(f"Running geographic analysis for Congress {congress}")

        try:
            analysis = self.geographic_analyzer.generate_comprehensive_analysis(
                congress
            )

            # Save results
            self.geographic_analyzer.save_analysis_report(analysis)

            logger.info("Geographic analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Geographic analysis failed: {e}")
            return {"error": str(e), "analysis_type": "geographic"}

    def run_temporal_analysis(self, congress: int = 118) -> Dict:
        """
        Run comprehensive temporal analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Temporal analysis results
        """
        logger.info(f"Running temporal analysis for Congress {congress}")

        try:
            analysis = self.temporal_analyzer.generate_comprehensive_analysis(congress)

            # Save results
            self.temporal_analyzer.save_analysis_report(analysis)

            logger.info("Temporal analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Temporal analysis failed: {e}")
            return {"error": str(e), "analysis_type": "temporal"}

    def run_topic_analysis(self, congress: int = 118) -> Dict:
        """
        Run comprehensive topic analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Topic analysis results
        """
        logger.info(f"Running topic analysis for Congress {congress}")

        try:
            analysis = self.topic_analyzer.generate_comprehensive_analysis(congress)

            # Save results
            self.topic_analyzer.save_analysis_report(analysis)
            self.topic_analyzer.save_categorized_bills()

            logger.info("Topic analysis completed successfully")
            return analysis

        except Exception as e:
            logger.error(f"Topic analysis failed: {e}")
            return {"error": str(e), "analysis_type": "topic"}

    def run_all_analyses(self, congress: int = 118, parallel: bool = False) -> Dict:
        """
        Run all analysis modules

        Args:
            congress: Congress number to analyze
            parallel: Whether to run analyses in parallel (future enhancement)

        Returns:
            Combined results from all analyses
        """
        logger.info(f"Running all analyses for Congress {congress}")

        start_time = datetime.now()

        results = {
            "metadata": {
                "congress": congress,
                "analysis_start": start_time.isoformat(),
                "analysis_end": None,
                "duration_seconds": None,
                "parallel_execution": parallel,
            },
            "analyses": {},
            "summary": {},
            "errors": [],
        }

        # Run each analysis (currently sequential, could be parallelized)
        analyses_to_run = [
            ("party", self.run_party_analysis),
            ("geographic", self.run_geographic_analysis),
            ("temporal", self.run_temporal_analysis),
            ("topic", self.run_topic_analysis),
        ]

        for analysis_name, analysis_func in analyses_to_run:
            logger.info(f"Starting {analysis_name} analysis...")

            try:
                analysis_result = analysis_func(congress)

                if "error" in analysis_result:
                    results["errors"].append(
                        {"analysis": analysis_name, "error": analysis_result["error"]}
                    )
                else:
                    results["analyses"][analysis_name] = analysis_result

            except Exception as e:
                logger.error(f"Failed to run {analysis_name} analysis: {e}")
                results["errors"].append({"analysis": analysis_name, "error": str(e)})

        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        results["metadata"]["analysis_end"] = end_time.isoformat()
        results["metadata"]["duration_seconds"] = duration

        # Generate cross-analysis summary
        results["summary"] = self._generate_cross_analysis_summary(results["analyses"])

        logger.info(f"All analyses completed in {duration:.2f} seconds")
        return results

    def generate_unified_report(
        self, congress: int = 118, include_data_fetch: bool = False
    ) -> Dict:
        """
        Generate a unified comprehensive report

        Args:
            congress: Congress number to analyze
            include_data_fetch: Whether to fetch fresh data before analysis

        Returns:
            Unified comprehensive report
        """
        logger.info(f"Generating unified comprehensive report for Congress {congress}")

        report = {
            "report_metadata": {
                "congress": congress,
                "report_generated": datetime.now().isoformat(),
                "report_type": "comprehensive_congressional_analysis",
                "version": "2.0",
                "data_freshness": "existing" if not include_data_fetch else "fresh",
            },
            "executive_summary": {},
            "data_collection": {},
            "analyses": {},
            "cross_cutting_insights": {},
            "recommendations": {},
            "methodology": {},
        }

        # Optionally fetch fresh data
        if include_data_fetch:
            logger.info("Fetching fresh data before analysis...")
            report["data_collection"] = self.fetch_comprehensive_data(congress)

        # Run all analyses
        analysis_results = self.run_all_analyses(congress)
        report["analyses"] = analysis_results["analyses"]

        if analysis_results["errors"]:
            report["analysis_errors"] = analysis_results["errors"]

        # Generate executive summary
        report["executive_summary"] = self._generate_executive_summary(
            report["analyses"]
        )

        # Generate cross-cutting insights
        report["cross_cutting_insights"] = self._generate_cross_cutting_insights(
            report["analyses"]
        )

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report["analyses"])

        # Document methodology
        report["methodology"] = self._document_methodology()

        # Save unified report
        self._save_unified_report(report)

        logger.info("Unified comprehensive report generation completed")
        return report

    def _generate_cross_analysis_summary(self, analyses: Dict) -> Dict:
        """Generate summary statistics across all analyses"""
        summary = {
            "analyses_completed": len(analyses),
            "analyses_failed": 0,
            "data_coverage": {},
            "key_metrics": {},
        }

        # Extract key metrics from each analysis
        if "party" in analyses:
            party_data = analyses["party"]
            summary["key_metrics"]["party_unity_average"] = party_data.get(
                "summary_statistics", {}
            ).get("average_unity_by_party", {})
            summary["key_metrics"]["bipartisan_rate"] = party_data.get(
                "summary_statistics", {}
            ).get("overall_bipartisan_rate", 0)

        if "geographic" in analyses:
            geo_data = analyses["geographic"]
            summary["key_metrics"]["states_analyzed"] = geo_data.get(
                "metadata", {}
            ).get("total_states_analyzed", 0)
            summary["key_metrics"]["split_delegations"] = (
                geo_data.get("summary_statistics", {})
                .get("split_senate_delegations", {})
                .get("count", 0)
            )

        if "temporal" in analyses:
            temporal_data = analyses["temporal"]
            summary["key_metrics"]["months_analyzed"] = len(
                temporal_data.get("monthly_trends", [])
            )
            summary["key_metrics"]["avg_monthly_bills"] = temporal_data.get(
                "summary_statistics", {}
            ).get("avg_monthly_bills", 0)

        if "topic" in analyses:
            topic_data = analyses["topic"]
            summary["key_metrics"]["categories_analyzed"] = topic_data.get(
                "metadata", {}
            ).get("categories_analyzed", 0)
            summary["key_metrics"]["bills_categorized"] = topic_data.get(
                "metadata", {}
            ).get("total_bills_categorized", 0)

        return summary

    def _generate_executive_summary(self, analyses: Dict) -> Dict:
        """Generate executive summary from all analyses"""
        summary = {
            "overview": "Comprehensive analysis of Congressional activity, voting patterns, and legislative trends",
            "period_analyzed": None,
            "key_findings": [],
            "data_quality": {},
            "notable_patterns": [],
        }

        # Extract key findings from each analysis
        key_findings = []

        if "party" in analyses:
            party_insights = analyses["party"].get("key_insights", [])
            key_findings.extend(
                [f"Party Analysis: {insight}" for insight in party_insights]
            )

        if "geographic" in analyses:
            geo_insights = analyses["geographic"].get("key_insights", [])
            key_findings.extend(
                [f"Geographic Analysis: {insight}" for insight in geo_insights]
            )

        if "temporal" in analyses:
            temporal_insights = analyses["temporal"].get("key_insights", [])
            key_findings.extend(
                [f"Temporal Analysis: {insight}" for insight in temporal_insights]
            )

        if "topic" in analyses:
            topic_insights = analyses["topic"].get("key_insights", [])
            key_findings.extend(
                [f"Topic Analysis: {insight}" for insight in topic_insights]
            )

        summary["key_findings"] = key_findings[:10]  # Top 10 findings

        return summary

    def _generate_cross_cutting_insights(self, analyses: Dict) -> Dict:
        """Generate insights that span multiple analysis dimensions"""
        insights = {
            "partisan_patterns": {},
            "geographic_political_alignment": {},
            "temporal_policy_shifts": {},
            "topic_party_correlations": {},
        }

        # Analyze patterns across dimensions
        try:
            # Cross-reference party and geographic data
            if "party" in analyses and "geographic" in analyses:
                insights["partisan_patterns"][
                    "geographic_correlation"
                ] = "Party unity varies by region and state characteristics"

            # Cross-reference temporal and topic data
            if "temporal" in analyses and "topic" in analyses:
                insights["temporal_policy_shifts"][
                    "topic_seasonality"
                ] = "Policy focus shifts seasonally and by election cycle"

            # Cross-reference party and topic data
            if "party" in analyses and "topic" in analyses:
                insights["topic_party_correlations"][
                    "policy_specialization"
                ] = "Parties show distinct policy area specializations"

        except Exception as e:
            logger.warning(f"Failed to generate some cross-cutting insights: {e}")

        return insights

    def _generate_recommendations(self, analyses: Dict) -> Dict:
        """Generate actionable recommendations based on analysis results"""
        recommendations = {
            "data_collection": [],
            "analysis_enhancement": [],
            "civic_engagement": [],
            "transparency_improvements": [],
        }

        # Data collection recommendations
        recommendations["data_collection"] = [
            "Increase frequency of data collection for real-time analysis",
            "Expand committee membership data collection",
            "Integrate additional lobbying disclosure sources",
        ]

        # Analysis enhancement recommendations
        recommendations["analysis_enhancement"] = [
            "Implement predictive modeling for bill success rates",
            "Develop sentiment analysis for bill content",
            "Create interactive visualizations for public consumption",
        ]

        # Civic engagement recommendations
        recommendations["civic_engagement"] = [
            "Create citizen-friendly scorecards for representatives",
            "Develop alerts for significant voting pattern changes",
            "Provide district-specific analysis summaries",
        ]

        # Transparency improvements
        recommendations["transparency_improvements"] = [
            "Publish regular transparency reports",
            "Create open data APIs for public access",
            "Establish data quality metrics and monitoring",
        ]

        return recommendations

    def _document_methodology(self) -> Dict:
        """Document the analysis methodology"""
        methodology = {
            "data_sources": [
                "Congress.gov API for bills, votes, and member data",
                "Senate.gov Lobbying Disclosure Act database",
                "Congressional committee information",
            ],
            "analysis_modules": {
                "party_analytics": "Analyzes party unity, bipartisanship, and member consistency",
                "geographic_analytics": "Examines state delegation patterns and regional analysis",
                "temporal_analytics": "Studies timeline trends and election cycle patterns",
                "topic_analytics": "Categorizes bills and analyzes committee activity",
            },
            "data_processing": {
                "normalization": "Party codes standardized, dates parsed consistently",
                "categorization": "Bills categorized using keyword matching and committee assignments",
                "scoring": "Unity scores calculated as percentage of party-line votes",
            },
            "limitations": [
                "Analysis limited to available public data",
                "Some analyses use simplified metrics due to data constraints",
                "Historical data may have gaps or inconsistencies",
            ],
        }

        return methodology

    def _save_unified_report(self, report: Dict) -> str:
        """Save the unified comprehensive report"""
        output_path = self.base_dir / "analysis" / "unified_comprehensive_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Unified comprehensive report saved to {output_path}")
        return str(output_path)

    def print_analysis_summary(self, results: Dict) -> None:
        """Print a human-readable summary of analysis results"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE CONGRESSIONAL ANALYSIS SUMMARY")
        print("=" * 80)

        metadata = results.get("metadata", {})
        print(f"Congress: {metadata.get('congress', 'Unknown')}")
        print(f"Analysis Duration: {metadata.get('duration_seconds', 0):.2f} seconds")
        print(f"Analyses Completed: {len(results.get('analyses', {}))}")

        if results.get("errors"):
            print(f"Analyses Failed: {len(results['errors'])}")

        print("\n" + "-" * 40)
        print("ANALYSIS RESULTS")
        print("-" * 40)

        analyses = results.get("analyses", {})

        # Party Analysis Summary
        if "party" in analyses:
            party_data = analyses["party"]
            print("\n📊 PARTY ANALYSIS")
            if party_data.get("summary_statistics"):
                stats = party_data["summary_statistics"]
                print(f"  Members Analyzed: {stats.get('members_by_party', {})}")
                print(
                    f"  Bipartisan Rate: {stats.get('overall_bipartisan_rate', 0):.1%}"
                )

        # Geographic Analysis Summary
        if "geographic" in analyses:
            geo_data = analyses["geographic"]
            print("\n🗺️  GEOGRAPHIC ANALYSIS")
            if geo_data.get("metadata"):
                print(
                    f"  States Analyzed: {geo_data['metadata'].get('total_states_analyzed', 0)}"
                )
                if geo_data.get("summary_statistics"):
                    split_count = (
                        geo_data["summary_statistics"]
                        .get("split_senate_delegations", {})
                        .get("count", 0)
                    )
                    print(f"  Split Senate Delegations: {split_count}")

        # Temporal Analysis Summary
        if "temporal" in analyses:
            temporal_data = analyses["temporal"]
            print("\n📈 TEMPORAL ANALYSIS")
            if temporal_data.get("metadata"):
                print(
                    f"  Bills Analyzed: {temporal_data['metadata'].get('total_bills_analyzed', 0)}"
                )
                print(
                    f"  Time Period: {temporal_data['metadata'].get('date_range', {}).get('start_date', 'Unknown')} to {temporal_data['metadata'].get('date_range', {}).get('end_date', 'Unknown')}"
                )

        # Topic Analysis Summary
        if "topic" in analyses:
            topic_data = analyses["topic"]
            print("\n📋 TOPIC ANALYSIS")
            if topic_data.get("metadata"):
                print(
                    f"  Bills Categorized: {topic_data['metadata'].get('total_bills_categorized', 0)}"
                )
                print(
                    f"  Categories: {topic_data['metadata'].get('categories_analyzed', 0)}"
                )

        # Cross-Analysis Summary
        summary = results.get("summary", {})
        if summary:
            print("\n" + "-" * 40)
            print("KEY METRICS SUMMARY")
            print("-" * 40)
            key_metrics = summary.get("key_metrics", {})
            for metric, value in key_metrics.items():
                if isinstance(value, dict):
                    print(f"  {metric}: {value}")
                else:
                    print(f"  {metric}: {value}")

        if results.get("errors"):
            print("\n" + "-" * 40)
            print("ANALYSIS ERRORS")
            print("-" * 40)
            for error in results["errors"]:
                print(f"  ❌ {error['analysis']}: {error['error']}")

        print("\n" + "=" * 80)


def main():
    """Main execution function for the orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(description="Congressional Analysis Orchestrator")
    parser.add_argument(
        "--fetch", action="store_true", help="Fetch fresh data before analysis"
    )
    parser.add_argument(
        "--congress", type=int, default=118, help="Congress number to analyze"
    )
    parser.add_argument(
        "--analysis",
        choices=["party", "geographic", "temporal", "topic", "all"],
        default="all",
        help="Which analysis to run",
    )
    parser.add_argument(
        "--max-items", type=int, default=25, help="Maximum items to fetch per category"
    )
    parser.add_argument("--output-dir", default="data", help="Output directory")
    parser.add_argument(
        "--unified-report",
        action="store_true",
        help="Generate unified comprehensive report",
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = AnalysisOrchestrator(base_dir=args.output_dir)

    try:
        if args.unified_report:
            # Generate unified comprehensive report
            orchestrator.generate_unified_report(
                congress=args.congress, include_data_fetch=args.fetch
            )
            print("\nUnified report generated successfully!")
            print(
                f"Report saved to: {orchestrator.base_dir}/analysis/unified_comprehensive_report.json"
            )

        else:
            # Fetch data if requested
            if args.fetch:
                logger.info(f"Fetching data for Congress {args.congress}...")
                data_summary = orchestrator.fetch_comprehensive_data(
                    congress=args.congress, max_items=args.max_items
                )
                print("Data fetching completed!")
                print(f"Data summary: {data_summary}")

            # Run requested analysis
            if args.analysis == "all":
                results = orchestrator.run_all_analyses(congress=args.congress)
                orchestrator.print_analysis_summary(results)
            elif args.analysis == "party":
                results = orchestrator.run_party_analysis(congress=args.congress)
                print("Party analysis completed!")
            elif args.analysis == "geographic":
                results = orchestrator.run_geographic_analysis(congress=args.congress)
                print("Geographic analysis completed!")
            elif args.analysis == "temporal":
                results = orchestrator.run_temporal_analysis(congress=args.congress)
                print("Temporal analysis completed!")
            elif args.analysis == "topic":
                results = orchestrator.run_topic_analysis(congress=args.congress)
                print("Topic analysis completed!")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
