#!/usr/bin/env python3
"""Fetch member data from Congress.gov API"""

import json
import logging
import os
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_members_from_api(limit=250, offset=0):
    """Fetch members from Congress.gov API"""
    api_key = os.getenv("DATA_GOV_API_KEY")

    url = "https://api.congress.gov/v3/member"
    params = {"limit": limit, "offset": offset, "format": "json"}

    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("members", [])
    except Exception as e:
        logger.error(f"Error fetching members: {e}")
        return []


def main():

    # Set congress number
    congress = 118

    # Create output directory
    output_dir = Path("data/members") / str(congress)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching members for {congress}th Congress...")

    try:
        all_members = []
        offset = 0
        limit = 250  # Max allowed by API

        while True:
            logger.info(f"Fetching members (offset: {offset})...")
            members = fetch_members_from_api(limit=limit, offset=offset)

            if not members:
                break

            all_members.extend(members)
            logger.info(f"Fetched {len(members)} members (total: {len(all_members)})")

            if len(members) < limit:
                break  # No more pages

            offset += limit
            time.sleep(0.5)  # Rate limiting

        logger.info(f"Found {len(all_members)} total members")

        # Save all members (they should be current members)
        saved_count = 0
        congress_members = []
        for member in all_members:
            member_id = member.get("bioguideId")
            if member_id:
                # Fetch detailed info for this member
                detail_url = member.get("url")
                if detail_url:
                    # Extract member detail from URL
                    member_file = output_dir / f"{member_id}.json"
                    with open(member_file, "w") as f:
                        json.dump(member, f, indent=2)
                    saved_count += 1
                    if saved_count % 10 == 0:
                        logger.info(f"Saved {saved_count} members...")
                congress_members.append(member)

        # Create summary file
        summary = {
            "congress": congress,
            "total": len(congress_members),
            "members": [
                {
                    "bioguideId": m.get("bioguideId"),
                    "name": m.get("name"),
                    "party": m.get("partyName"),
                    "state": m.get("state"),
                    "district": m.get("district"),
                    "chamber": "house" if m.get("district") else "senate",
                }
                for m in congress_members
            ],
        }

        summary_file = output_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Saved summary to {summary_file}")
        logger.info(f"Successfully fetched {saved_count} members")

    except Exception as e:
        logger.error(f"Error fetching members: {e}")
        raise


if __name__ == "__main__":
    main()
