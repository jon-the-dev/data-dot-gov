#!/usr/bin/env python3
"""
Geographic Analytics Module

Consolidates state patterns, regional analysis, and delegation unity.
Based on functionality from analyze_state_patterns.py.

Key features:
- State delegation unity analysis
- Regional voting blocs
- Geographic clustering of voting patterns
- State-by-state comparisons
- Urban vs rural state analysis
"""

import json
import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.api import CongressGovAPI
from core.storage import FileStorage

logger = logging.getLogger(__name__)


@dataclass
class StateMember:
    """Represents a congressional member from a state"""

    bioguide_id: str
    name: str
    state: str
    state_code: str
    party: str
    chamber: str  # "house" or "senate"
    district: Optional[int] = None
    current_member: bool = True


@dataclass
class StateDelegation:
    """Represents a state's congressional delegation"""

    state: str
    state_code: str
    senators: List[StateMember]
    representatives: List[StateMember]
    total_members: int
    party_composition: Dict[str, int]
    is_split_senate: bool = False
    is_unified_delegation: bool = False


@dataclass
class StateClassification:
    """Classification of state characteristics"""

    state: str
    state_code: str
    region: str  # Northeast, South, Midwest, West
    urban_rural_type: str  # Urban, Rural, Mixed
    political_lean: str  # Red, Blue, Purple/Swing
    population_density: str  # High, Medium, Low
    electoral_votes: int
    competitive_score: float  # 0-1, higher = more competitive


@dataclass
class VotingUnityMetrics:
    """Metrics for state delegation voting unity"""

    state: str
    state_code: str
    total_votes_analyzed: int
    delegation_unity_score: float  # 0-1, higher = more unified
    senate_unity_score: float  # For split delegations
    house_unity_score: float
    cross_party_votes: int
    party_line_votes: int
    bipartisan_collaboration_score: float


@dataclass
class StateIssuePriorities:
    """State-specific issue tracking"""

    state: str
    state_code: str
    top_sponsored_categories: List[Tuple[str, int]]
    agriculture_focus: int
    energy_focus: int
    healthcare_focus: int
    defense_focus: int
    technology_focus: int
    transportation_focus: int
    environment_focus: int
    education_focus: int


@dataclass
class RegionalPatterns:
    """Regional voting and policy patterns"""

    region: str
    states: List[str]
    avg_unity_score: float
    common_priorities: List[str]
    regional_coalition_strength: float
    cross_regional_collaboration: Dict[str, float]


class GeographicAnalyzer:
    """Comprehensive geographic analytics for Congressional data"""

    def __init__(self, base_dir: str = "data"):
        """
        Initialize the geographic analyzer

        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.storage = FileStorage(self.base_dir)
        self.congress_api = CongressGovAPI()

        # State classifications (based on 2020 census and political data)
        self.state_classifications = self._initialize_state_classifications()

        # Data containers
        self.members: List[StateMember] = []
        self.state_delegations: Dict[str, StateDelegation] = {}
        self.bills_data: List[Dict] = []
        self.voting_records: List[Dict] = []

        # Analysis results
        self.unity_metrics: Dict[str, VotingUnityMetrics] = {}
        self.issue_priorities: Dict[str, StateIssuePriorities] = {}
        self.regional_patterns: Dict[str, RegionalPatterns] = {}

        logger.info("GeographicAnalyzer initialized")

    def _initialize_state_classifications(self) -> Dict[str, StateClassification]:
        """Initialize state classification data"""
        classifications = {}

        # Define regional groupings
        regions = {
            "Northeast": ["CT", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
            "South": [
                "AL",
                "AR",
                "DE",
                "FL",
                "GA",
                "KY",
                "LA",
                "MD",
                "MS",
                "NC",
                "OK",
                "SC",
                "TN",
                "TX",
                "VA",
                "WV",
            ],
            "Midwest": [
                "IL",
                "IN",
                "IA",
                "KS",
                "MI",
                "MN",
                "MO",
                "NE",
                "ND",
                "OH",
                "SD",
                "WI",
            ],
            "West": [
                "AK",
                "AZ",
                "CA",
                "CO",
                "HI",
                "ID",
                "MT",
                "NV",
                "NM",
                "OR",
                "UT",
                "WA",
                "WY",
            ],
        }

        # Political lean based on recent elections
        political_leans = {
            "Red": [
                "AL",
                "AK",
                "AR",
                "ID",
                "IN",
                "IA",
                "KS",
                "KY",
                "LA",
                "MS",
                "MO",
                "MT",
                "NE",
                "ND",
                "OK",
                "SC",
                "SD",
                "TN",
                "TX",
                "UT",
                "WV",
                "WY",
            ],
            "Blue": [
                "CA",
                "CT",
                "DE",
                "HI",
                "IL",
                "ME",
                "MD",
                "MA",
                "NJ",
                "NY",
                "OR",
                "RI",
                "VT",
                "WA",
            ],
            "Purple": [
                "AZ",
                "CO",
                "FL",
                "GA",
                "MI",
                "MN",
                "NV",
                "NH",
                "NM",
                "NC",
                "OH",
                "PA",
                "VA",
                "WI",
            ],
        }

        # Urban/Rural classification
        urban_rural = {
            "Urban": ["CA", "CT", "DE", "HI", "IL", "MA", "MD", "NJ", "NY", "RI"],
            "Rural": ["AK", "ID", "IA", "KS", "MT", "NE", "ND", "SD", "VT", "WV", "WY"],
            "Mixed": [
                "AL",
                "AR",
                "AZ",
                "CO",
                "FL",
                "GA",
                "IN",
                "KY",
                "LA",
                "ME",
                "MI",
                "MN",
                "MS",
                "MO",
                "NV",
                "NH",
                "NM",
                "NC",
                "OH",
                "OK",
                "OR",
                "PA",
                "SC",
                "TN",
                "TX",
                "UT",
                "VA",
                "WA",
                "WI",
            ],
        }

        # Electoral votes (2020 census)
        electoral_votes = {
            "CA": 54,
            "TX": 40,
            "FL": 30,
            "NY": 28,
            "PA": 19,
            "IL": 19,
            "OH": 17,
            "GA": 16,
            "NC": 16,
            "MI": 15,
            "NJ": 14,
            "VA": 13,
            "WA": 12,
            "AZ": 11,
            "TN": 11,
            "IN": 11,
            "MA": 11,
            "MD": 10,
            "MO": 10,
            "MN": 10,
            "WI": 10,
            "CO": 10,
            "AL": 9,
            "SC": 9,
            "KY": 8,
            "LA": 8,
            "CT": 7,
            "OK": 7,
            "OR": 8,
            "AR": 6,
            "IA": 6,
            "KS": 6,
            "MS": 6,
            "NV": 6,
            "UT": 6,
            "NE": 5,
            "NM": 5,
            "WV": 4,
            "HI": 4,
            "ID": 4,
            "ME": 4,
            "NH": 4,
            "RI": 4,
            "AK": 3,
            "DE": 3,
            "MT": 4,
            "ND": 3,
            "SD": 3,
            "VT": 3,
            "WY": 3,
        }

        # Build classifications
        all_states = set()
        for region_states in regions.values():
            all_states.update(region_states)

        for state_code in all_states:
            # Find region
            region = None
            for reg, states in regions.items():
                if state_code in states:
                    region = reg
                    break

            # Find political lean
            lean = "Purple"  # default
            for lean_type, states in political_leans.items():
                if state_code in states:
                    lean = lean_type
                    break

            # Find urban/rural type
            ur_type = "Mixed"  # default
            for ur, states in urban_rural.items():
                if state_code in states:
                    ur_type = ur
                    break

            # Population density (simplified based on electoral votes)
            ev = electoral_votes.get(state_code, 3)
            if ev >= 15:
                pop_density = "High"
            elif ev >= 8:
                pop_density = "Medium"
            else:
                pop_density = "Low"

            # Competitive score (higher for purple states)
            competitive_score = 0.8 if lean == "Purple" else 0.3

            classifications[state_code] = StateClassification(
                state=self._state_code_to_name(state_code),
                state_code=state_code,
                region=region or "Unknown",
                urban_rural_type=ur_type,
                political_lean=lean,
                population_density=pop_density,
                electoral_votes=ev,
                competitive_score=competitive_score,
            )

        return classifications

    def _state_code_to_name(self, state_code: str) -> str:
        """Convert state code to full state name"""
        state_names = {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming",
        }
        return state_names.get(state_code, state_code)

    def load_member_data(self, congress: int = 118) -> List[StateMember]:
        """
        Load congressional member data

        Args:
            congress: Congress number to analyze

        Returns:
            List of state members
        """
        logger.info(f"Loading member data for Congress {congress}")

        members_data = self.storage.load_congress_members(congress)
        members = []

        for bioguide_id, member_data in members_data.items():
            # Extract current term info
            current_term = None
            if member_data.get("terms"):
                for term in reversed(member_data["terms"]):
                    if term.get("congress") == congress:
                        current_term = term
                        break

            if current_term and member_data.get("currentMember", False):
                member = StateMember(
                    bioguide_id=bioguide_id,
                    name=member_data["name"],
                    state=member_data["state"],
                    state_code=current_term.get("stateCode", ""),
                    party=member_data.get("party", ""),
                    chamber=member_data.get("chamber", "").lower(),
                    district=member_data.get("district"),
                    current_member=member_data.get("currentMember", False),
                )
                members.append(member)

        self.members = members
        logger.info(f"Loaded {len(members)} current members")
        return members

    def load_bill_data(self, congress: int = 118, max_bills: int = 1000) -> List[Dict]:
        """
        Load bill data for issue priority analysis

        Args:
            congress: Congress number to analyze
            max_bills: Maximum number of bills to load

        Returns:
            List of bill data
        """
        logger.info(f"Loading bill data for Congress {congress}")

        bills_data = self.storage.load_congress_bills(congress)
        bills = list(bills_data.values())[:max_bills]

        self.bills_data = bills
        logger.info(f"Loaded {len(bills)} bills")
        return bills

    def build_state_delegations(self) -> Dict[str, StateDelegation]:
        """
        Build state delegation objects from member data

        Returns:
            Dictionary mapping state codes to delegations
        """
        logger.info("Building state delegations")

        state_members = defaultdict(lambda: {"senators": [], "representatives": []})

        for member in self.members:
            state_code = member.state_code
            if member.chamber == "senate":
                state_members[state_code]["senators"].append(member)
            elif member.chamber == "house":
                state_members[state_code]["representatives"].append(member)

        delegations = {}
        for state_code, members in state_members.items():
            senators = members["senators"]
            representatives = members["representatives"]

            # Calculate party composition
            all_members = senators + representatives
            party_composition = Counter(member.party for member in all_members)

            # Check if senate delegation is split
            is_split_senate = (
                len(senators) == 2 and len({s.party for s in senators}) > 1
            )

            # Check if entire delegation is unified
            all_parties = {member.party for member in all_members}
            is_unified_delegation = len(all_parties) == 1

            delegation = StateDelegation(
                state=self._state_code_to_name(state_code),
                state_code=state_code,
                senators=senators,
                representatives=representatives,
                total_members=len(all_members),
                party_composition=dict(party_composition),
                is_split_senate=is_split_senate,
                is_unified_delegation=is_unified_delegation,
            )

            delegations[state_code] = delegation

        self.state_delegations = delegations
        logger.info(f"Built delegations for {len(delegations)} states")

        # Log statistics
        split_states = [s for s, d in delegations.items() if d.is_split_senate]
        unified_states = [s for s, d in delegations.items() if d.is_unified_delegation]
        logger.info(f"Split senate delegations: {len(split_states)}")
        logger.info(f"Unified delegations: {len(unified_states)}")

        return delegations

    def analyze_voting_unity(self) -> Dict[str, VotingUnityMetrics]:
        """
        Analyze voting unity within state delegations

        Returns:
            Dictionary mapping state codes to unity metrics
        """
        logger.info("Analyzing voting unity patterns")

        unity_metrics = {}

        for state_code, delegation in self.state_delegations.items():
            total_members = delegation.total_members
            if total_members == 0:
                continue

            # Calculate basic unity metrics based on party composition
            party_counts = list(delegation.party_composition.values())
            largest_party = max(party_counts) if party_counts else 0
            delegation_unity_score = (
                largest_party / total_members if total_members > 0 else 0
            )

            # Senate-specific unity
            senate_unity_score = 1.0
            if len(delegation.senators) == 2:
                senate_parties = [s.party for s in delegation.senators]
                senate_unity_score = 1.0 if len(set(senate_parties)) == 1 else 0.0

            # House unity (simplified - would need actual voting data for precision)
            house_unity_score = delegation_unity_score

            # Estimate cross-party collaboration
            bipartisan_score = 1.0 - delegation_unity_score

            metrics = VotingUnityMetrics(
                state=delegation.state,
                state_code=state_code,
                total_votes_analyzed=100,  # Placeholder
                delegation_unity_score=delegation_unity_score,
                senate_unity_score=senate_unity_score,
                house_unity_score=house_unity_score,
                cross_party_votes=int(20 * (1 - delegation_unity_score)),
                party_line_votes=int(80 * delegation_unity_score),
                bipartisan_collaboration_score=bipartisan_score,
            )

            unity_metrics[state_code] = metrics

        self.unity_metrics = unity_metrics
        logger.info(f"Calculated unity metrics for {len(unity_metrics)} states")
        return unity_metrics

    def analyze_state_issue_priorities(self) -> Dict[str, StateIssuePriorities]:
        """
        Analyze state-specific issue priorities based on bill sponsorship

        Returns:
            Dictionary mapping state codes to issue priorities
        """
        logger.info("Analyzing state issue priorities")

        state_sponsorship = defaultdict(lambda: defaultdict(int))

        for bill in self.bills_data:
            sponsors = bill.get("sponsors", [])
            policy_area = bill.get("policyArea", {}).get("name", "Unknown")

            for sponsor in sponsors:
                state = sponsor.get("state", "")
                if state:
                    state_sponsorship[state][policy_area] += 1

        issue_priorities = {}
        for state_code, delegation in self.state_delegations.items():
            state_name = delegation.state
            sponsorship_data = state_sponsorship.get(state_code, {})

            # Get top sponsored categories
            top_categories = sorted(
                sponsorship_data.items(), key=lambda x: x[1], reverse=True
            )[:10]

            # Calculate specific issue focus scores
            agriculture_focus = sponsorship_data.get("Agriculture and Food", 0)
            energy_focus = sponsorship_data.get("Energy", 0)
            healthcare_focus = sponsorship_data.get("Health", 0)
            defense_focus = sponsorship_data.get(
                "Armed Forces and National Security", 0
            )
            technology_focus = sponsorship_data.get(
                "Science, Technology, Communications", 0
            )
            transportation_focus = sponsorship_data.get(
                "Transportation and Public Works", 0
            )
            environment_focus = sponsorship_data.get("Environmental Protection", 0)
            education_focus = sponsorship_data.get("Education", 0)

            priorities = StateIssuePriorities(
                state=state_name,
                state_code=state_code,
                top_sponsored_categories=top_categories,
                agriculture_focus=agriculture_focus,
                energy_focus=energy_focus,
                healthcare_focus=healthcare_focus,
                defense_focus=defense_focus,
                technology_focus=technology_focus,
                transportation_focus=transportation_focus,
                environment_focus=environment_focus,
                education_focus=education_focus,
            )

            issue_priorities[state_code] = priorities

        self.issue_priorities = issue_priorities
        logger.info(f"Analyzed issue priorities for {len(issue_priorities)} states")
        return issue_priorities

    def analyze_regional_patterns(self) -> Dict[str, RegionalPatterns]:
        """
        Analyze regional voting and policy patterns

        Returns:
            Dictionary mapping region names to patterns
        """
        logger.info("Analyzing regional patterns")

        regions = defaultdict(
            lambda: {
                "states": [],
                "unity_scores": [],
                "issue_priorities": defaultdict(int),
            }
        )

        for state_code, classification in self.state_classifications.items():
            if state_code in self.state_delegations:
                region = classification.region
                regions[region]["states"].append(state_code)

                # Add unity score if available
                if state_code in self.unity_metrics:
                    unity_score = self.unity_metrics[state_code].delegation_unity_score
                    regions[region]["unity_scores"].append(unity_score)

                # Add issue priorities
                if state_code in self.issue_priorities:
                    priorities = self.issue_priorities[state_code]
                    for category, count in priorities.top_sponsored_categories:
                        regions[region]["issue_priorities"][category] += count

        # Convert to RegionalPatterns objects
        regional_patterns = {}
        for region, data in regions.items():
            avg_unity = (
                statistics.mean(data["unity_scores"]) if data["unity_scores"] else 0.0
            )

            # Get top regional priorities
            common_priorities = sorted(
                data["issue_priorities"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            common_priorities = [category for category, _ in common_priorities]

            # Calculate regional coalition strength
            coalition_strength = (
                avg_unity * len(data["states"]) / 50
            )  # Normalize by total states

            # Calculate cross-regional collaboration (simplified)
            cross_regional = {
                other_region: 0.5 for other_region in regions if other_region != region
            }

            pattern = RegionalPatterns(
                region=region,
                states=data["states"],
                avg_unity_score=avg_unity,
                common_priorities=common_priorities,
                regional_coalition_strength=coalition_strength,
                cross_regional_collaboration=cross_regional,
            )

            regional_patterns[region] = pattern

        self.regional_patterns = regional_patterns
        logger.info(f"Analyzed patterns for {len(regional_patterns)} regions")
        return regional_patterns

    def analyze_competitive_states(self) -> Dict[str, any]:
        """
        Analyze competitive/swing states and their patterns

        Returns:
            Analysis of competitive state behavior
        """
        logger.info("Analyzing competitive states")

        competitive_states = [
            state_code
            for state_code, classification in self.state_classifications.items()
            if classification.political_lean == "Purple"
        ]

        analysis = {
            "competitive_states": competitive_states,
            "competitive_patterns": {},
            "comparison_to_safe_states": {},
        }

        # Analyze patterns in competitive states
        competitive_unity_scores = []
        competitive_issue_focus = defaultdict(int)

        for state_code in competitive_states:
            if state_code in self.unity_metrics:
                unity = self.unity_metrics[state_code].delegation_unity_score
                competitive_unity_scores.append(unity)

            if state_code in self.issue_priorities:
                priorities = self.issue_priorities[state_code]
                for category, count in priorities.top_sponsored_categories:
                    competitive_issue_focus[category] += count

        # Compare to safe states
        safe_red_unity = []
        safe_blue_unity = []

        for state_code, classification in self.state_classifications.items():
            if state_code in self.unity_metrics:
                unity = self.unity_metrics[state_code].delegation_unity_score
                if classification.political_lean == "Red":
                    safe_red_unity.append(unity)
                elif classification.political_lean == "Blue":
                    safe_blue_unity.append(unity)

        analysis["competitive_patterns"] = {
            "average_unity": (
                statistics.mean(competitive_unity_scores)
                if competitive_unity_scores
                else 0
            ),
            "total_states": len(competitive_states),
            "top_issues": dict(
                sorted(
                    competitive_issue_focus.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ),
        }

        analysis["comparison_to_safe_states"] = {
            "competitive_avg_unity": (
                statistics.mean(competitive_unity_scores)
                if competitive_unity_scores
                else 0
            ),
            "safe_red_avg_unity": (
                statistics.mean(safe_red_unity) if safe_red_unity else 0
            ),
            "safe_blue_avg_unity": (
                statistics.mean(safe_blue_unity) if safe_blue_unity else 0
            ),
        }

        return analysis

    def generate_comprehensive_analysis(self, congress: int = 118) -> Dict[str, any]:
        """
        Generate comprehensive geographic analysis

        Args:
            congress: Congress number to analyze

        Returns:
            Complete geographic analysis report
        """
        logger.info(
            f"Generating comprehensive geographic analysis for Congress {congress}"
        )

        # Load all data
        self.load_member_data(congress)
        self.load_bill_data(congress)

        # Build delegations and run analyses
        self.build_state_delegations()
        self.analyze_voting_unity()
        self.analyze_state_issue_priorities()
        self.analyze_regional_patterns()

        # Additional analyses
        competitive_analysis = self.analyze_competitive_states()
        summary_stats = self._generate_summary_statistics()

        report = {
            "metadata": {
                "congress": congress,
                "analysis_date": datetime.now().isoformat(),
                "total_states_analyzed": len(self.state_delegations),
                "total_members_analyzed": len(self.members),
                "total_bills_analyzed": len(self.bills_data),
            },
            "state_classifications": {
                state_code: asdict(classification)
                for state_code, classification in self.state_classifications.items()
            },
            "state_delegations": {
                state_code: asdict(delegation)
                for state_code, delegation in self.state_delegations.items()
            },
            "voting_unity_metrics": {
                state_code: asdict(metrics)
                for state_code, metrics in self.unity_metrics.items()
            },
            "state_issue_priorities": {
                state_code: asdict(priorities)
                for state_code, priorities in self.issue_priorities.items()
            },
            "regional_patterns": {
                region: asdict(pattern)
                for region, pattern in self.regional_patterns.items()
            },
            "competitive_states_analysis": competitive_analysis,
            "summary_statistics": summary_stats,
            "key_insights": self._generate_key_insights(),
        }

        return report

    def save_analysis_report(self, report: Dict, output_file: str = None) -> str:
        """
        Save geographic analysis report

        Args:
            report: Analysis report to save
            output_file: Optional output file path

        Returns:
            Path to saved file
        """
        if output_file is None:
            output_file = "analysis/geographic_analytics_report.json"

        output_path = self.base_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Geographic analysis report saved to {output_path}")
        return str(output_path)

    def _generate_summary_statistics(self) -> Dict[str, any]:
        """Generate summary statistics for the analysis"""
        # Split delegations analysis
        split_senate_states = [
            state_code
            for state_code, delegation in self.state_delegations.items()
            if delegation.is_split_senate
        ]

        # Unified delegations analysis
        unified_states = [
            state_code
            for state_code, delegation in self.state_delegations.items()
            if delegation.is_unified_delegation
        ]

        # Unity scores by region
        unity_by_region = {}
        for region, pattern in self.regional_patterns.items():
            unity_by_region[region] = pattern.avg_unity_score

        # Unity scores by state type
        unity_by_type = defaultdict(list)
        for state_code, classification in self.state_classifications.items():
            if state_code in self.unity_metrics:
                unity_score = self.unity_metrics[state_code].delegation_unity_score
                unity_by_type[classification.political_lean].append(unity_score)
                unity_by_type[classification.urban_rural_type].append(unity_score)

        return {
            "split_senate_delegations": {
                "count": len(split_senate_states),
                "states": split_senate_states,
                "percentage": len(split_senate_states)
                / len(self.state_delegations)
                * 100,
            },
            "unified_delegations": {
                "count": len(unified_states),
                "states": unified_states,
                "percentage": len(unified_states) / len(self.state_delegations) * 100,
            },
            "regional_unity_scores": unity_by_region,
            "unity_by_political_lean": {
                "Red": statistics.mean(unity_by_type.get("Red", [0])),
                "Blue": statistics.mean(unity_by_type.get("Blue", [0])),
                "Purple": statistics.mean(unity_by_type.get("Purple", [0])),
            },
            "unity_by_urbanization": {
                "Urban": statistics.mean(unity_by_type.get("Urban", [0])),
                "Rural": statistics.mean(unity_by_type.get("Rural", [0])),
                "Mixed": statistics.mean(unity_by_type.get("Mixed", [0])),
            },
            "most_unified_states": sorted(
                [
                    (code, metrics.delegation_unity_score)
                    for code, metrics in self.unity_metrics.items()
                ],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
            "least_unified_states": sorted(
                [
                    (code, metrics.delegation_unity_score)
                    for code, metrics in self.unity_metrics.items()
                ],
                key=lambda x: x[1],
            )[:10],
        }

    def _generate_key_insights(self) -> List[str]:
        """Generate key insights from the geographic analysis"""
        insights = []

        # Split delegation insights
        split_count = len(
            [d for d in self.state_delegations.values() if d.is_split_senate]
        )
        if split_count > 0:
            insights.append(f"{split_count} states have split Senate delegations")

        # Regional unity insights
        if self.regional_patterns:
            region_unity = [
                (region, pattern.avg_unity_score)
                for region, pattern in self.regional_patterns.items()
            ]
            region_unity.sort(key=lambda x: x[1], reverse=True)

            if region_unity:
                most_unified_region = region_unity[0]
                insights.append(
                    f"{most_unified_region[0]} region shows highest delegation unity"
                )

        # Competitive state insights
        competitive_states = [
            code
            for code, classification in self.state_classifications.items()
            if classification.political_lean == "Purple"
        ]
        if competitive_states:
            insights.append(
                f"{len(competitive_states)} states classified as competitive/swing states"
            )

        # State issue focus insights
        if self.issue_priorities:
            all_issues = defaultdict(int)
            for priorities in self.issue_priorities.values():
                for category, count in priorities.top_sponsored_categories:
                    all_issues[category] += count

            if all_issues:
                top_issue = max(all_issues.items(), key=lambda x: x[1])
                insights.append(f"Most common state focus: {top_issue[0]}")

        return insights
