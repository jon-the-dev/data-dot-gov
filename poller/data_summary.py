#!/usr/bin/env python3
"""
Data Summary Script - Shows what data has been collected and provides insights
"""

import json
from collections import defaultdict
from pathlib import Path


def analyze_collected_data(base_dir="data"):
    """Analyze all collected data and provide summary"""

    base_path = Path(base_dir)
    summary = {"bills": {}, "members": {}, "lobbyists": {}, "votes": {}, "insights": []}

    # Analyze bills
    bills_path = base_path / "congress_bills"
    if bills_path.exists():
        for congress_dir in bills_path.iterdir():
            if congress_dir.is_dir():
                bill_files = list(congress_dir.glob("*.json"))
                # Exclude index.json
                bill_files = [f for f in bill_files if f.name != "index.json"]

                summary["bills"][congress_dir.name] = {
                    "count": len(bill_files),
                    "types": defaultdict(int),
                    "recent_laws": [],
                }

                # Analyze bill types and recent laws
                for bill_file in bill_files[:100]:  # Sample first 100
                    try:
                        with open(bill_file) as f:
                            bill = json.load(f)
                            bill_type = bill.get("type", "Unknown")
                            summary["bills"][congress_dir.name]["types"][bill_type] += 1

                            # Check if it became law
                            latest_action = bill.get("latestAction", {}).get("text", "")
                            if "Became Public Law" in latest_action:
                                summary["bills"][congress_dir.name][
                                    "recent_laws"
                                ].append(
                                    {
                                        "number": f"{bill.get('type')}-{bill.get('number')}",
                                        "title": bill.get("title", "")[:80] + "...",
                                    }
                                )
                    except Exception:
                        pass

                # Convert defaultdict to dict for JSON
                summary["bills"][congress_dir.name]["types"] = dict(
                    summary["bills"][congress_dir.name]["types"]
                )

    # Analyze members
    members_path = base_path / "members"
    if members_path.exists():
        for congress_dir in members_path.iterdir():
            if congress_dir.is_dir():
                # Load summary if exists
                summary_file = congress_dir / "summary.json"
                if summary_file.exists():
                    with open(summary_file) as f:
                        member_summary = json.load(f)
                        summary["members"][congress_dir.name] = member_summary

                # Analyze individual members for more details
                member_files = list(congress_dir.glob("*.json"))
                member_files = [f for f in member_files if f.name != "summary.json"]

                state_party_breakdown = defaultdict(lambda: defaultdict(int))

                for member_file in member_files:
                    try:
                        with open(member_file) as f:
                            member = json.load(f)
                            state = member.get("state", "Unknown")
                            party = member.get("party", "Unknown")
                            state_party_breakdown[state][party] += 1
                    except Exception:
                        pass

                # Find swing states (mixed party representation)
                swing_states = []
                for state, parties in state_party_breakdown.items():
                    if len(parties) > 1 and min(parties.values()) > 0:
                        swing_states.append(state)

                if swing_states:
                    summary["members"][congress_dir.name]["swing_states"] = swing_states

    # Analyze lobbyists
    lobbyists_path = base_path / "senate_lobbyists"
    if lobbyists_path.exists():
        lobbyist_files = list(lobbyists_path.glob("*.json"))
        lobbyist_files = [f for f in lobbyist_files if f.name != "index.json"]
        summary["lobbyists"]["count"] = len(lobbyist_files)

        # Sample some lobbyists
        firms = defaultdict(int)
        for lob_file in lobbyist_files[:50]:
            try:
                with open(lob_file) as f:
                    lobbyist = json.load(f)
                    # Count by firm if available
                    firm = lobbyist.get("firm_name", "") or lobbyist.get(
                        "registrant_name", ""
                    )
                    if firm:
                        firms[firm] += 1
            except Exception:
                pass

        # Top firms
        if firms:
            summary["lobbyists"]["top_firms"] = dict(
                sorted(firms.items(), key=lambda x: x[1], reverse=True)[:5]
            )

    # Generate insights
    if summary["bills"]:
        total_bills = sum(b["count"] for b in summary["bills"].values())
        summary["insights"].append(f"📊 {total_bills} bills tracked across Congress")

        # Count laws passed
        total_laws = sum(
            len(b.get("recent_laws", [])) for b in summary["bills"].values()
        )
        if total_laws > 0:
            summary["insights"].append(f"✅ {total_laws} bills became public laws")

    if summary["members"]:
        for congress, data in summary["members"].items():
            total = data.get("total", 0)
            by_party = data.get("by_party", {})
            if by_party:
                party_str = ", ".join([f"{p}: {c}" for p, c in by_party.items()])
                summary["insights"].append(
                    f"👥 Congress {congress}: {total} members ({party_str})"
                )

            swing_states = data.get("swing_states", [])
            if swing_states:
                summary["insights"].append(
                    f"🎯 Swing states: {', '.join(swing_states[:5])}"
                )

    if summary["lobbyists"].get("count", 0) > 0:
        summary["insights"].append(
            f"💼 {summary['lobbyists']['count']} lobbyists registered"
        )

    # Calculate party balance
    for congress, member_data in summary["members"].items():
        by_party = member_data.get("by_party", {})
        if by_party:
            total = sum(by_party.values())
            dem_pct = (by_party.get("Democratic", 0) / total * 100) if total else 0
            rep_pct = (by_party.get("Republican", 0) / total * 100) if total else 0

            if abs(dem_pct - rep_pct) < 10:
                summary["insights"].append(
                    f"⚖️ Congress {congress} is closely divided (D: {dem_pct:.1f}%, R: {rep_pct:.1f}%)"
                )

    return summary


def print_summary(summary):
    """Print a formatted summary"""

    print("\n" + "=" * 80)
    print("📈 GOVERNMENT DATA COLLECTION SUMMARY")
    print("=" * 80)

    # Bills summary
    if summary["bills"]:
        print("\n📋 LEGISLATIVE ACTIVITY")
        print("-" * 40)
        for congress, data in summary["bills"].items():
            print(f"\n{congress}th Congress:")
            print(f"  • Total bills: {data['count']}")

            if data["types"]:
                print("  • Bill types:")
                for bill_type, count in data["types"].items():
                    print(f"    - {bill_type}: {count}")

            if data["recent_laws"][:3]:
                print("  • Recent laws passed:")
                for law in data["recent_laws"][:3]:
                    print(f"    - {law['number']}: {law['title']}")

    # Members summary
    if summary["members"]:
        print("\n👥 CONGRESSIONAL MEMBERS")
        print("-" * 40)
        for congress, data in summary["members"].items():
            print(f"\n{congress}th Congress:")
            print(f"  • Total members: {data.get('total', 0)}")

            by_party = data.get("by_party", {})
            if by_party:
                print("  • Party breakdown:")
                for party, count in sorted(
                    by_party.items(), key=lambda x: x[1], reverse=True
                ):
                    pct = (count / data.get("total", 1)) * 100
                    print(f"    - {party}: {count} ({pct:.1f}%)")

            by_chamber = data.get("by_chamber", {})
            if by_chamber:
                print("  • By chamber:")
                for chamber, parties in by_chamber.items():
                    print(f"    {chamber.capitalize()}: {dict(parties)}")

            swing_states = data.get("swing_states", [])
            if swing_states:
                print(
                    f"  • States with mixed representation: {', '.join(swing_states[:5])}"
                )

    # Lobbyists summary
    if summary["lobbyists"].get("count", 0) > 0:
        print("\n💼 LOBBYING ACTIVITY")
        print("-" * 40)
        print(f"  • Total lobbyists: {summary['lobbyists']['count']}")

        top_firms = summary["lobbyists"].get("top_firms", {})
        if top_firms:
            print("  • Top lobbying firms:")
            for firm, count in list(top_firms.items())[:3]:
                print(f"    - {firm[:50]}: {count} lobbyists")

    # Key insights
    if summary["insights"]:
        print("\n🔍 KEY INSIGHTS")
        print("-" * 40)
        for insight in summary["insights"]:
            print(f"  {insight}")

    print("\n" + "=" * 80)
    print("💡 WEBSITE READINESS")
    print("=" * 80)

    # Check data completeness
    has_bills = bool(summary["bills"])
    has_members = bool(summary["members"])
    has_lobbyists = summary["lobbyists"].get("count", 0) > 0
    has_votes = bool(summary["votes"])

    print("\nData Available:")
    print(f"  ✅ Bills data: {'Yes' if has_bills else 'No'}")
    print(f"  ✅ Member profiles: {'Yes' if has_members else 'No'}")
    print(f"  ✅ Lobbyist data: {'Yes' if has_lobbyists else 'No'}")
    print(
        f"  {'❌' if not has_votes else '✅'} Voting records: {'No - API endpoint issue' if not has_votes else 'Yes'}"
    )

    print("\nYou can build features for:")
    if has_members:
        print("  • Member profiles by party and state")
        print("  • Party composition analysis")
        print("  • State delegation breakdowns")

    if has_bills:
        print("  • Bill tracking and status")
        print("  • Laws passed tracking")
        print("  • Legislative activity metrics")

    if has_lobbyists:
        print("  • Lobbying activity dashboard")
        print("  • Top lobbying organizations")

    print("\nNext steps:")
    if not has_votes:
        print("  1. Debug House votes API endpoint")
    print("  2. Link bills to member sponsors")
    print("  3. Create search and filter interfaces")
    print("  4. Build party comparison visualizations")

    print("\n" + "=" * 80)


def main():
    """Main execution"""
    print("Analyzing collected data...")
    summary = analyze_collected_data()

    # Save summary
    summary_path = Path("data") / "analysis" / "data_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Summary saved to: {summary_path}")

    # Print summary
    print_summary(summary)


if __name__ == "__main__":
    main()
