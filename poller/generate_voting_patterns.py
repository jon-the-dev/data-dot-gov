#!/usr/bin/env python3
"""Generate voting pattern analysis for Party Comparison page"""
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # Load existing voting records analysis
    voting_data_path = Path("../data/analysis/voting_records_analysis.json")
    if not voting_data_path.exists():
        logger.error(
            "voting_records_analysis.json not found. Run voting analysis first."
        )
        return

    with open(voting_data_path) as f:
        voting_data = json.load(f)

    # Calculate party unity scores
    members = voting_data.get("members", {})

    republican_unity_scores = []
    democratic_unity_scores = []

    for member_id, member_data in members.items():
        party_line_pct = member_data.get("party_line_percentage", 0)
        party = member_data.get("party", "")

        if party == "R":
            republican_unity_scores.append(party_line_pct)
        elif party == "D":
            democratic_unity_scores.append(party_line_pct)

    # Calculate averages
    republican_unity = (
        round(sum(republican_unity_scores) / len(republican_unity_scores), 1)
        if republican_unity_scores
        else 0
    )
    democratic_unity = (
        round(sum(democratic_unity_scores) / len(democratic_unity_scores), 1)
        if democratic_unity_scores
        else 0
    )

    # Find cross-party votes (members with lower party line percentages)
    cross_party_members = []
    for member_id, member_data in members.items():
        if member_data.get("defection_percentage", 0) > 15:  # More than 15% defection
            cross_party_members.append(
                {
                    "name": member_data.get("name"),
                    "party": member_data.get("party"),
                    "state": member_data.get("state"),
                    "defection_rate": member_data.get("defection_percentage"),
                    "party_line_rate": member_data.get("party_line_percentage"),
                }
            )

    # Sort by defection rate
    cross_party_members = sorted(
        cross_party_members, key=lambda x: x["defection_rate"], reverse=True
    )[:10]

    # Generate voting patterns structure
    voting_patterns = {
        "republican_unity": republican_unity,
        "democratic_unity": democratic_unity,
        "cross_party_votes": [
            {
                "title": f"{m['name']} ({m['party']}-{m['state']})",
                "republicans_for": int(m["defection_rate"]) if m["party"] == "R" else 0,
                "democrats_for": int(m["defection_rate"]) if m["party"] == "D" else 0,
                "description": f"Votes with party {m['party_line_rate']:.0f}% of the time",
            }
            for m in cross_party_members[:5]
        ],
        "contested_votes": [],  # Would need actual vote data to populate
    }

    # Load existing comprehensive report
    comp_report_path = Path("../data/analysis/comprehensive_report.json")
    if comp_report_path.exists():
        with open(comp_report_path) as f:
            comp_report = json.load(f)
    else:
        comp_report = {
            "generated_date": "2025-09-23",
            "data_location": "data",
            "analyses": {},
        }

    # Update comprehensive report with voting patterns
    comp_report["voting_patterns"] = voting_patterns

    # Save updated comprehensive report
    with open(comp_report_path, "w") as f:
        json.dump(comp_report, f, indent=2)

    logger.info(
        f"Generated voting patterns: R unity={republican_unity}%, D unity={democratic_unity}%"
    )
    logger.info(
        f"Found {len(cross_party_members)} members with >15% cross-party voting"
    )
    logger.info("Updated comprehensive_report.json with voting patterns")


if __name__ == "__main__":
    main()
