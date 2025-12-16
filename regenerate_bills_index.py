#!/usr/bin/env python3
"""
Regenerate bills index to include all collected bill data.
This script creates an index from all bill files in the data/congress_bills directory.
"""
import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def regenerate_bills_index():
    """Regenerate the bills index from all collected bill files"""
    data_dir = Path("data")
    congress_bills_dir = data_dir / "congress_bills"

    if not congress_bills_dir.exists():
        logger.error(f"Congress bills directory not found: {congress_bills_dir}")
        return

    all_bills = []
    total_files = 0

    # Process all congress directories
    for congress_dir in congress_bills_dir.glob("*/"):
        congress_num = congress_dir.name
        logger.info(f"Processing Congress {congress_num}...")

        bill_files = list(congress_dir.glob("*.json"))
        congress_file_count = 0

        for bill_file in bill_files:
            if bill_file.name in ["index.json", "summary.json"]:
                continue

            try:
                with open(bill_file, 'r') as f:
                    bill_data = json.load(f)

                # Extract key information for the index
                bill_entry = {
                    "id": bill_data.get("billNumber", bill_file.stem),
                    "congress": int(congress_num),
                    "type": bill_data.get("billType", bill_data.get("type", "Unknown")),
                    "number": str(bill_data.get("number", bill_file.stem.split("_")[-1])),
                    "title": bill_data.get("title", "Unknown"),
                    "latest_action": bill_data.get("latestAction", {}).get("text", "No action recorded") if isinstance(bill_data.get("latestAction"), dict) else str(bill_data.get("latestAction", "No action recorded")),
                    "filepath": f"data/congress_bills/{congress_num}/{bill_file.name}"
                }

                all_bills.append(bill_entry)
                congress_file_count += 1
                total_files += 1

            except Exception as e:
                logger.warning(f"Error processing {bill_file}: {e}")

        logger.info(f"Processed {congress_file_count} bills from Congress {congress_num}")

    # Sort bills by congress and number for consistent ordering
    all_bills.sort(key=lambda x: (x["congress"], x["type"], int(x["number"]) if x["number"].isdigit() else 0, x["number"]))

    # Create the index structure
    bills_index = {
        "count": len(all_bills),
        "last_updated": datetime.now().isoformat(),
        "records": all_bills
    }

    # Write the index file
    index_file = data_dir / "bills_index.json"
    with open(index_file, 'w') as f:
        json.dump(bills_index, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully created bills index with {len(all_bills)} bills")
    logger.info(f"Index written to: {index_file}")

    # Also create a copy in the congress_bills directory for the first congress found
    if congress_bills_dir.exists():
        first_congress_dir = next(congress_bills_dir.glob("*/"), None)
        if first_congress_dir:
            congress_index_file = first_congress_dir / "index.json"
            with open(congress_index_file, 'w') as f:
                json.dump(bills_index, f, indent=2, ensure_ascii=False)
            logger.info(f"Also created index in: {congress_index_file}")

    return len(all_bills)

if __name__ == "__main__":
    logger.info("Starting bills index regeneration...")
    count = regenerate_bills_index()
    logger.info(f"Bills index regeneration complete. Total bills indexed: {count}")