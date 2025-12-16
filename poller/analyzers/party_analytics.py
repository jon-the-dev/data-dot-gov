#!/usr/bin/env python3
"""
Party Analytics Module

Consolidates party unity, bipartisanship, and member consistency analysis.
Combines functionality from:
- analyze_member_consistency.py (party unity scoring logic)
- analyze_bill_sponsors.py (bipartisanship metrics from co-sponsorship)
- Party voting patterns from gov_data_analyzer.py

Key features:
- Party unity scores calculation
- Cross-party cooperation metrics
- Bipartisan bill identification
- Member voting consistency tracking
"""

import json
import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from core.api import CongressGovAPI
from core.storage import FileStorage

logger = logging.getLogger(__name__)


@dataclass
class PartyUnityMetrics:
    """Metrics for party unity analysis"""

    party: str
    total_votes: int
    party_line_votes: int
    unity_score: float  # 0-1, higher = more unified
    maverick_score: float  # 1 - unity_score
    defection_count: int
    consistency_rating: str  # Loyalist, Moderate, Maverick, Swing Voter


@dataclass
class BipartisanshipMetrics:
    """Metrics for bipartisan cooperation"""

    total_bills: int
    bipartisan_bills: int
    bipartisan_rate: float
    cross_party_combinations: Dict[str, int]
    top_bipartisan_members: List[Dict]


@dataclass
class MemberConsistencyProfile:
    """Individual member consistency profile"""

    bioguide_id: str
    name: str
    party: str
    state: str
    chamber: str
    total_votes: int = 0
    party_unity_score: float = 0.0
    maverick_score: float = 0.0
    bipartisan_score: float = 0.0
    major_defections: List[Dict] = None
    cross_party_collaborations: int = 0
    consistency_rating: str = "Unknown"

    def __post_init__(self):
        if self.major_defections is None:
            self.major_defections = []


class PartyAnalyzer:
    """Comprehensive party analytics for Congressional data"""

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the party analyzer

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.storage = FileStorage(self.base_dir)
        self.congress_api = CongressGovAPI()

        # Analysis thresholds
        self.min_votes_for_analysis = 3
        self.loyalist_threshold = 0.95  # 95% party unity
        self.maverick_threshold = 0.15  # 15% defection rate
        self.bipartisan_threshold = 0.20  # 20% cross-party collaboration

        # Data containers
        self.members: Dict[str, MemberConsistencyProfile] = {}
        self.vote_records: Dict[str, List[Dict]] = defaultdict(list)
        self.bill_sponsors: Dict[str, Dict] = {}

        logger.info("PartyAnalyzer initialized")

    def load_member_data(
        self, congress: int = 118
    ) -> Dict[str, MemberConsistencyProfile]:
        """
        Load member data and create consistency profiles

        Args:
            congress: Congress number to analyze

        Returns:
            Dictionary of member profiles
        """
        logger.info(f"Loading member data for Congress {congress}")

        members_data = self.storage.load_congress_members(congress)
        profiles = {}

        for bioguide_id, member_data in members_data.items():
            # Extract current term info
            current_term = None
            for term in member_data.get("terms", []):
                if term.get("congress") == congress:
                    current_term = term
                    break

            if current_term:
                profile = MemberConsistencyProfile(
                    bioguide_id=bioguide_id,
                    name=member_data.get("name", ""),
                    party=member_data.get("party", ""),
                    state=member_data.get("state", ""),
                    chamber=member_data.get("chamber", ""),
                )
                profiles[bioguide_id] = profile

        self.members = profiles
        logger.info(f"Loaded {len(profiles)} member profiles")
        return profiles

    def load_voting_data(self, congress: int = 118) -> None:
        """
        Load voting records for analysis

        Args:
            congress: Congress number to analyze
        """
        logger.info(f"Loading voting data for Congress {congress}")

        # Load House votes
        house_votes = self.storage.load_house_votes(congress)
        for vote_id, vote_data in house_votes.items():
            for member_vote in vote_data.get("member_votes", []):
                member_id = member_vote.get("bioguideId")
                if member_id and member_id in self.members:
                    self.vote_records[member_id].append(
                        {
                            "vote_id": vote_id,
                            "vote_data": vote_data,
                            "member_vote": member_vote,
                        }
                    )

        # Load Senate votes if available
        senate_votes = self.storage.load_senate_votes(congress)
        for vote_id, vote_data in senate_votes.items():
            for member_vote in vote_data.get("member_votes", []):
                member_id = member_vote.get("bioguideId")
                if member_id and member_id in self.members:
                    self.vote_records[member_id].append(
                        {
                            "vote_id": vote_id,
                            "vote_data": vote_data,
                            "member_vote": member_vote,
                        }
                    )

        logger.info(f"Loaded voting records for {len(self.vote_records)} members")

    def load_bill_sponsor_data(self, congress: int = 118) -> None:
        """
        Load bill sponsor and co-sponsor data

        Args:
            congress: Congress number to analyze
        """
        logger.info(f"Loading bill sponsor data for Congress {congress}")

        sponsor_files = list(self.base_dir.glob(f"bill_sponsors/*_{congress}_*.json"))
        for sponsor_file in sponsor_files:
            try:
                with open(sponsor_file, encoding="utf-8") as f:
                    sponsor_data = json.load(f)
                    bill_id = sponsor_data.get("bill_id")
                    if bill_id:
                        self.bill_sponsors[bill_id] = sponsor_data
            except Exception as e:
                logger.warning(f"Failed to load sponsor file {sponsor_file}: {e}")

        logger.info(f"Loaded sponsor data for {len(self.bill_sponsors)} bills")

    def calculate_party_unity_scores(self) -> Dict[str, PartyUnityMetrics]:
        """
        Calculate party unity scores for all parties

        Returns:
            Dictionary mapping party codes to unity metrics
        """
        logger.info("Calculating party unity scores")

        party_metrics = {}

        # Group members by party
        party_members = defaultdict(list)
        for member in self.members.values():
            party_members[member.party].append(member)

        for party, members in party_members.items():
            total_votes = 0
            party_line_votes = 0
            defection_count = 0

            for member in members:
                member_votes = self.vote_records.get(member.bioguide_id, [])
                member.total_votes = len(member_votes)
                total_votes += len(member_votes)

                # Analyze each vote for party line adherence
                member_party_line = 0
                member_defections = 0

                for vote_record in member_votes:
                    vote_data = vote_record["vote_data"]
                    member_vote = vote_record["member_vote"]

                    # Determine party majority position
                    party_breakdown = vote_data.get("party_breakdown", {})
                    party_votes = party_breakdown.get(party, {})

                    if party_votes:
                        # Find majority position within party
                        majority_position = max(
                            party_votes.items(), key=lambda x: x[1]
                        )[0]
                        member_position = member_vote.get("vote", "").lower()

                        # Normalize vote positions
                        normalized_position = self._normalize_vote_position(
                            member_position
                        )

                        if normalized_position == majority_position:
                            member_party_line += 1
                        else:
                            member_defections += 1
                            # Track major defections
                            if vote_data.get("question"):
                                member.major_defections.append(
                                    {
                                        "vote_id": vote_record["vote_id"],
                                        "question": vote_data.get("question", "")[:100],
                                        "date": vote_data.get("date"),
                                        "member_vote": member_position,
                                        "party_majority": majority_position,
                                    }
                                )

                member.party_line_votes = member_party_line
                member.party_unity_score = (
                    (member_party_line / len(member_votes)) if member_votes else 0.0
                )
                member.maverick_score = 1.0 - member.party_unity_score

                # Classify member consistency
                if member.party_unity_score >= self.loyalist_threshold:
                    member.consistency_rating = "Loyalist"
                elif member.maverick_score >= self.maverick_threshold:
                    member.consistency_rating = "Maverick"
                elif 0.4 <= member.party_unity_score <= 0.6:
                    member.consistency_rating = "Swing Voter"
                else:
                    member.consistency_rating = "Moderate"

                party_line_votes += member_party_line
                defection_count += member_defections

            # Calculate overall party metrics
            unity_score = (party_line_votes / total_votes) if total_votes > 0 else 0.0

            party_metrics[party] = PartyUnityMetrics(
                party=party,
                total_votes=total_votes,
                party_line_votes=party_line_votes,
                unity_score=unity_score,
                maverick_score=1.0 - unity_score,
                defection_count=defection_count,
                consistency_rating=self._classify_party_unity(unity_score),
            )

        logger.info(f"Calculated unity scores for {len(party_metrics)} parties")
        return party_metrics

    def analyze_bipartisan_cooperation(self) -> BipartisanshipMetrics:
        """
        Analyze bipartisan cooperation patterns through co-sponsorship

        Returns:
            Bipartisanship metrics
        """
        logger.info("Analyzing bipartisan cooperation")

        total_bills = 0
        bipartisan_bills = 0
        cross_party_combinations = Counter()
        member_bipartisan_counts = defaultdict(int)

        for _bill_id, sponsor_data in self.bill_sponsors.items():
            sponsors = sponsor_data.get("sponsors", [])
            cosponsors = sponsor_data.get("cosponsors", [])

            if not sponsors:
                continue

            total_bills += 1

            # Get all parties involved
            all_parties = set()
            primary_sponsor_party = sponsors[0].get("party")
            if primary_sponsor_party:
                all_parties.add(primary_sponsor_party)

            for cosponsor in cosponsors:
                cosponsor_party = cosponsor.get("party")
                if cosponsor_party:
                    all_parties.add(cosponsor_party)

            # Check if bill has cross-party support
            if len(all_parties) > 1:
                bipartisan_bills += 1

                # Track cross-party combinations
                parties_sorted = sorted(all_parties)
                combo = " + ".join(parties_sorted)
                cross_party_combinations[combo] += 1

                # Credit members for bipartisan collaboration
                for sponsor in sponsors + cosponsors:
                    bioguide_id = sponsor.get("bioguideId")
                    if bioguide_id and bioguide_id in self.members:
                        member_bipartisan_counts[bioguide_id] += 1
                        self.members[bioguide_id].cross_party_collaborations += 1

        # Calculate bipartisan scores for members
        for member_id, count in member_bipartisan_counts.items():
            if member_id in self.members:
                member = self.members[member_id]
                # Bipartisan score based on proportion of bills that were bipartisan
                # Could be refined with total bills sponsored (count = member_bills)
                member.bipartisan_score = min(1.0, count / 10.0)  # Scale to 0-1

        # Get top bipartisan members
        top_bipartisan = sorted(
            [
                (member.name, member.party, member.cross_party_collaborations)
                for member in self.members.values()
                if member.cross_party_collaborations > 0
            ],
            key=lambda x: x[2],
            reverse=True,
        )[:20]

        top_bipartisan_members = [
            {"name": name, "party": party, "collaborations": count}
            for name, party, count in top_bipartisan
        ]

        bipartisan_rate = (bipartisan_bills / total_bills) if total_bills > 0 else 0.0

        return BipartisanshipMetrics(
            total_bills=total_bills,
            bipartisan_bills=bipartisan_bills,
            bipartisan_rate=bipartisan_rate,
            cross_party_combinations=dict(cross_party_combinations),
            top_bipartisan_members=top_bipartisan_members,
        )

    def analyze_voting_patterns(self) -> Dict[str, any]:
        """
        Analyze detailed voting patterns and swing behavior

        Returns:
            Comprehensive voting pattern analysis
        """
        logger.info("Analyzing voting patterns")

        # Initialize analysis containers
        analysis = {
            "total_votes_analyzed": 0,
            "bipartisan_votes": [],
            "partisan_votes": [],
            "swing_votes": [],
            "close_votes": [],
            "unanimous_votes": [],
        }

        # Analyze each vote
        all_votes = set()
        for member_votes in self.vote_records.values():
            for vote_record in member_votes:
                all_votes.add(vote_record["vote_id"])

        for vote_id in all_votes:
            # Get vote data
            vote_data = None
            for member_votes in self.vote_records.values():
                for vote_record in member_votes:
                    if vote_record["vote_id"] == vote_id:
                        vote_data = vote_record["vote_data"]
                        break
                if vote_data:
                    break

            if not vote_data:
                continue

            analysis["total_votes_analyzed"] += 1

            # Analyze vote characteristics
            party_breakdown = vote_data.get("party_breakdown", {})

            # Check if bipartisan
            is_bipartisan = self._is_vote_bipartisan(party_breakdown)

            # Check if close vote
            is_close = self._is_vote_close(vote_data)

            # Check if unanimous
            is_unanimous = self._is_vote_unanimous(party_breakdown)

            vote_summary = {
                "vote_id": vote_id,
                "question": vote_data.get("question", "")[:100],
                "date": vote_data.get("date"),
                "result": vote_data.get("result"),
                "party_breakdown": party_breakdown,
            }

            if is_unanimous:
                analysis["unanimous_votes"].append(vote_summary)
            elif is_bipartisan:
                analysis["bipartisan_votes"].append(vote_summary)
            else:
                analysis["partisan_votes"].append(vote_summary)

            if is_close:
                analysis["close_votes"].append(vote_summary)

        # Sort votes by date
        for vote_type in [
            "bipartisan_votes",
            "partisan_votes",
            "close_votes",
            "unanimous_votes",
        ]:
            analysis[vote_type] = sorted(
                analysis[vote_type], key=lambda x: x.get("date", ""), reverse=True
            )[
                :20
            ]  # Keep top 20

        return analysis

    def generate_party_rankings(self) -> Dict[str, List[Dict]]:
        """
        Generate rankings of members by various party-related metrics

        Returns:
            Dictionary of member rankings
        """
        logger.info("Generating party rankings")

        valid_members = [
            member
            for member in self.members.values()
            if member.total_votes >= self.min_votes_for_analysis
        ]

        rankings = {
            "most_loyal": sorted(
                valid_members, key=lambda m: m.party_unity_score, reverse=True
            )[:20],
            "biggest_mavericks": sorted(
                valid_members, key=lambda m: m.maverick_score, reverse=True
            )[:20],
            "most_bipartisan": sorted(
                valid_members, key=lambda m: m.bipartisan_score, reverse=True
            )[:20],
            "by_party": defaultdict(list),
        }

        # Group rankings by party
        for member in valid_members:
            rankings["by_party"][member.party].append(
                {
                    "name": member.name,
                    "state": member.state,
                    "unity_score": member.party_unity_score,
                    "bipartisan_score": member.bipartisan_score,
                    "consistency_rating": member.consistency_rating,
                }
            )

        # Sort party-specific rankings
        for party in rankings["by_party"]:
            rankings["by_party"][party] = sorted(
                rankings["by_party"][party],
                key=lambda m: m["unity_score"],
                reverse=True,
            )

        return rankings

    def generate_comprehensive_analysis(self, congress: int = 118) -> Dict[str, any]:
        """
        Generate comprehensive party analytics report

        Args:
            congress: Congress number to analyze

        Returns:
            Complete party analysis report
        """
        logger.info(f"Generating comprehensive party analysis for Congress {congress}")

        # Load all data
        self.load_member_data(congress)
        self.load_voting_data(congress)
        self.load_bill_sponsor_data(congress)

        # Run analyses
        party_unity = self.calculate_party_unity_scores()
        bipartisanship = self.analyze_bipartisan_cooperation()
        voting_patterns = self.analyze_voting_patterns()
        rankings = self.generate_party_rankings()

        # Generate summary statistics
        total_members = len(self.members)
        members_by_party = Counter(member.party for member in self.members.values())

        # Calculate cross-party statistics
        avg_unity_by_party = {
            party: statistics.mean(
                [m.party_unity_score for m in self.members.values() if m.party == party]
            )
            for party in members_by_party
        }

        report = {
            "metadata": {
                "congress": congress,
                "analysis_date": datetime.now().isoformat(),
                "total_members_analyzed": total_members,
                "parties_analyzed": list(members_by_party.keys()),
                "data_sources": ["voting_records", "bill_sponsors", "member_profiles"],
            },
            "party_unity_metrics": {
                party: asdict(metrics) for party, metrics in party_unity.items()
            },
            "bipartisanship_metrics": asdict(bipartisanship),
            "voting_patterns": voting_patterns,
            "member_rankings": rankings,
            "summary_statistics": {
                "members_by_party": dict(members_by_party),
                "average_unity_by_party": avg_unity_by_party,
                "overall_bipartisan_rate": bipartisanship.bipartisan_rate,
                "total_votes_analyzed": voting_patterns["total_votes_analyzed"],
            },
            "key_insights": self._generate_key_insights(
                party_unity, bipartisanship, voting_patterns
            ),
        }

        return report

    def save_analysis_report(self, report: Dict, output_file: str = None) -> str:
        """
        Save party analysis report

        Args:
            report: Analysis report to save
            output_file: Optional output file path

        Returns:
            Path to saved file
        """
        if output_file is None:
            output_file = "analysis/party_analytics_report.json"

        output_path = self.base_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Party analysis report saved to {output_path}")
        return str(output_path)

    def save_member_profiles(self, output_dir: str = None) -> str:
        """
        Save individual member consistency profiles

        Args:
            output_dir: Output directory for profiles

        Returns:
            Path to saved profiles directory
        """
        if output_dir is None:
            output_dir = "analysis/member_profiles"

        profiles_dir = self.base_dir / output_dir
        profiles_dir.mkdir(parents=True, exist_ok=True)

        for member_id, member in self.members.items():
            if member.total_votes >= self.min_votes_for_analysis:
                profile_file = profiles_dir / f"{member_id}_profile.json"
                with open(profile_file, "w", encoding="utf-8") as f:
                    json.dump(asdict(member), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.members)} member profiles to {profiles_dir}")
        return str(profiles_dir)

    def _normalize_vote_position(self, position: str) -> str:
        """Normalize vote position to standard format"""
        position_lower = position.lower()
        if position_lower in ["yea", "aye", "yes"]:
            return "yea"
        elif position_lower in ["nay", "no"]:
            return "nay"
        elif position_lower in ["present"]:
            return "present"
        else:
            return "not_voting"

    def _classify_party_unity(self, unity_score: float) -> str:
        """Classify party unity level"""
        if unity_score >= 0.95:
            return "Highly Unified"
        elif unity_score >= 0.85:
            return "Unified"
        elif unity_score >= 0.70:
            return "Mostly Unified"
        elif unity_score >= 0.55:
            return "Somewhat Divided"
        else:
            return "Highly Divided"

    def _is_vote_bipartisan(self, party_breakdown: Dict) -> bool:
        """Check if vote shows bipartisan support"""
        dem_votes = party_breakdown.get("D", {})
        rep_votes = party_breakdown.get("R", {})

        dem_total = sum(dem_votes.values())
        rep_total = sum(rep_votes.values())

        if dem_total == 0 or rep_total == 0:
            return False

        dem_yea_pct = dem_votes.get("yea", 0) / dem_total if dem_total else 0
        rep_yea_pct = rep_votes.get("yea", 0) / rep_total if rep_total else 0

        # Bipartisan if both parties have significant support (>30%) or opposition (<70%)
        both_support = dem_yea_pct > 0.3 and rep_yea_pct > 0.3
        mixed_positions = abs(dem_yea_pct - rep_yea_pct) < 0.5

        return both_support or mixed_positions

    def _is_vote_close(self, vote_data: Dict) -> bool:
        """Check if vote was close (margin < 10%)"""
        result_summary = vote_data.get("result_summary", {})
        total_votes = result_summary.get("total", 0)

        if total_votes == 0:
            return False

        yea_votes = result_summary.get("yea", 0)
        nay_votes = result_summary.get("nay", 0)

        margin = abs(yea_votes - nay_votes) / total_votes
        return margin < 0.1  # Less than 10% margin

    def _is_vote_unanimous(self, party_breakdown: Dict) -> bool:
        """Check if vote was unanimous across parties"""
        party_positions = []

        for _party, votes in party_breakdown.items():
            total = sum(votes.values())
            if total > 0:
                yea_pct = votes.get("yea", 0) / total
                if yea_pct > 0.9:
                    party_positions.append("yea")
                elif yea_pct < 0.1:
                    party_positions.append("nay")
                else:
                    return False  # Not unanimous

        # Unanimous if all parties took the same position
        return len(set(party_positions)) <= 1 and len(party_positions) >= 2

    def _generate_key_insights(
        self,
        party_unity: Dict,
        bipartisanship: BipartisanshipMetrics,
        voting_patterns: Dict,
    ) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []

        # Party unity insights
        if party_unity:
            unity_scores = [
                (party, metrics.unity_score) for party, metrics in party_unity.items()
            ]
            unity_scores.sort(key=lambda x: x[1], reverse=True)

            if unity_scores:
                most_unified = unity_scores[0]
                insights.append(
                    f"{most_unified[0]} party shows highest unity ({most_unified[1]:.1%})"
                )

        # Bipartisanship insights
        if bipartisanship.bipartisan_rate > 0:
            insights.append(
                f"{bipartisanship.bipartisan_rate:.1%} of bills show bipartisan co-sponsorship"
            )

        if bipartisanship.top_bipartisan_members:
            top_member = bipartisanship.top_bipartisan_members[0]
            insights.append(
                f"Most bipartisan member: {top_member['name']} ({top_member['party']})"
            )

        # Voting pattern insights
        total_votes = voting_patterns.get("total_votes_analyzed", 0)
        if total_votes > 0:
            bipartisan_votes = len(voting_patterns.get("bipartisan_votes", []))
            bipartisan_pct = (bipartisan_votes / total_votes) * 100
            insights.append(f"{bipartisan_pct:.1f}% of votes show bipartisan support")

        return insights
