#!/usr/bin/env python3
"""Generate members summary from individual member files"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    members_dir = Path("data/members/118")
    output_file = Path("data/members_summary.json")

    all_members = []
    by_party = {}
    by_chamber = {"senate": {}, "house": {}}
    by_state = {}

    # Read all member files
    for member_file in members_dir.glob("*.json"):
        if member_file.name == "summary.json":
            continue

        try:
            with open(member_file) as f:
                member = json.load(f)

                # Add to all members list
                all_members.append(member)

                # Get party
                party = member.get("partyName", "Unknown")
                by_party[party] = by_party.get(party, 0) + 1

                # Get chamber
                chamber = "house" if member.get("district") else "senate"
                if party:
                    by_chamber[chamber][party] = by_chamber[chamber].get(party, 0) + 1

                # Get state
                state = member.get("state")
                if state:
                    if state not in by_state:
                        by_state[state] = {}
                    by_state[state][party] = by_state[state].get(party, 0) + 1

        except Exception as e:
            logger.warning(f"Error reading {member_file}: {e}")

    # Create summary
    summary = {
        "members": all_members,
        "total": len(all_members),
        "by_party": by_party,
        "by_chamber": by_chamber,
        "by_state": by_state,
        "generated": True,
    }

    # Save summary
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Generated summary with {len(all_members)} members")
    logger.info(f"By party: {by_party}")
    logger.info(f"Saved to {output_file}")


if __name__ == "__main__":
    main()
