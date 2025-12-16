#!/usr/bin/env python3
"""
Sync analysis data from main data directory to viewer's public directory
"""

import json
import shutil
from pathlib import Path


def sync_viewer_data():
    """Copy analysis data to the viewer's public directory"""

    # Define source and destination paths
    data_dir = Path("data")
    analysis_dir = data_dir / "analysis"
    viewer_public = Path("congress-viewer/public/data")

    # Create viewer data directory if it doesn't exist
    viewer_public.mkdir(parents=True, exist_ok=True)

    # Files to sync from analysis directory
    analysis_files = [
        "party_voting_analysis.json",
        "bill_categories_analysis.json",
        "bill_sponsors_analysis.json",
        "comprehensive_report.json",
        "member_consistency_analysis.json",
        "state_patterns_analysis.json",
        "timeline_analysis.json",
        "voting_records_analysis.json",
        "data_summary.json",
    ]

    copied_files = []

    # Copy analysis files
    for filename in analysis_files:
        src = analysis_dir / filename
        if src.exists():
            dst = viewer_public / filename
            shutil.copy2(src, dst)
            copied_files.append(filename)
            print(f"✓ Copied {filename}")
        else:
            print(f"⚠ Skipping {filename} (not found)")

    # Create members summary from members data
    members_dir = data_dir / "members" / "118"
    if members_dir.exists():
        members_summary = {"congress": 118, "members": [], "party_breakdown": {}}

        for member_file in members_dir.glob("*.json"):
            if member_file.name != "summary.json" and member_file.name != "index.json":
                with open(member_file) as f:
                    member = json.load(f)
                    # Extract key fields for summary
                    # Handle different member data structures
                    current_member = member.get("currentMember", {})
                    if isinstance(current_member, dict):
                        party = current_member.get("party")
                    else:
                        party = member.get("party")

                    summary_member = {
                        "bioguideId": member.get("bioguideId"),
                        "name": member.get("name"),
                        "party": party,
                        "state": member.get("state"),
                        "district": member.get("district"),
                    }
                    members_summary["members"].append(summary_member)

                    # Count party breakdown
                    party = summary_member.get("party", "Unknown")
                    members_summary["party_breakdown"][party] = (
                        members_summary["party_breakdown"].get(party, 0) + 1
                    )

        # Save members summary
        with open(viewer_public / "members_summary.json", "w") as f:
            json.dump(members_summary, f, indent=2)
        print("✓ Generated members_summary.json")

    # Create bills index from congress_bills data
    bills_dir = data_dir / "congress_bills" / "118"
    if bills_dir.exists():
        bills_index = {"congress": 118, "bills": []}

        for bill_file in bills_dir.glob("*.json"):
            if bill_file.name != "index.json":
                with open(bill_file) as f:
                    bill = json.load(f)
                    # Extract key fields for index
                    index_bill = {
                        "bill_id": f"{bill.get('number', '')}",
                        "title": bill.get("title"),
                        "type": bill.get("type"),
                        "originChamber": bill.get("originChamber"),
                        "updateDate": bill.get("updateDate"),
                        "latestAction": bill.get("latestAction", {}),
                    }
                    bills_index["bills"].append(index_bill)

        # Sort by update date
        bills_index["bills"].sort(key=lambda x: x.get("updateDate", ""), reverse=True)

        # Save bills index
        with open(viewer_public / "bills_index.json", "w") as f:
            json.dump(bills_index, f, indent=2)
        print("✓ Generated bills_index.json")

    print(f"\n✅ Data sync complete! Copied {len(copied_files)} analysis files")
    print(f"📁 Viewer data directory: {viewer_public.absolute()}")

    return copied_files


if __name__ == "__main__":
    sync_viewer_data()
