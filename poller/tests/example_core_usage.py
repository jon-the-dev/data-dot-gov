#!/usr/bin/env python3
"""
Example script demonstrating the new core package usage.

This shows how to use the unified API classes and storage utilities
from the new core package for congressional data collection.
"""

import logging

from core import CongressGovAPI, FileStorage, SenateGovAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate core package usage"""
    print("🏛️  Senate.gov Data Collection Platform - Core Package Demo")
    print("=" * 60)

    # Initialize file storage
    storage = FileStorage("data")
    print(f"📁 Initialized storage: {storage.base_dir}")

    # Initialize APIs
    print("\n🔗 Initializing APIs...")
    congress_api = CongressGovAPI(max_workers=3)
    senate_api = SenateGovAPI()

    print(f"✓ Congress.gov API: {congress_api.get_stats()['name']}")
    print(f"✓ Senate.gov API: {senate_api.get_stats()['name']}")

    # Example 1: Fetch recent bills
    print("\n📋 Fetching recent bills...")
    try:
        bills = congress_api.get_bills(congress=118, max_results=5)
        print(f"✓ Retrieved {len(bills)} bills")

        for bill in bills[:3]:
            title = bill.get("title", "No title")[:50]
            bill_id = f"{bill.get('type', 'Unknown')} {bill.get('number', 'N/A')}"
            print(f"   • {bill_id}: {title}...")

    except Exception as e:
        logger.error(f"Error fetching bills: {e}")

    # Example 2: Fetch lobbying filings
    print("\n📊 Fetching lobbying filings...")
    try:
        filings = senate_api.get_filings(filing_type="LD-1", max_results=3)
        print(f"✓ Retrieved {len(filings)} LD-1 filings")

        for filing in filings[:2]:
            client = filing.get("client_name", "Unknown client")[:30]
            registrant = filing.get("registrant_name", "Unknown registrant")[:30]
            print(f"   • {client} via {registrant}")

    except Exception as e:
        logger.error(f"Error fetching filings: {e}")

    # Example 3: Storage statistics
    print("\n💾 Storage statistics:")
    stats = storage.get_stats()
    print(f"✓ Base directory: {stats['base_dir']}")
    print(f"✓ Total records: {stats['total_records']}")
    print(f"✓ Record types: {len(stats['record_types'])}")

    for record_type, count in stats["record_types"].items():
        print(f"   • {record_type}: {count} records")

    # Example 4: Rate limiter stats
    print("\n⏱️  Rate limiter statistics:")
    congress_stats = congress_api.rate_limiter.get_stats()
    senate_stats = senate_api.rate_limiter.get_stats()

    print(
        f"✓ Congress API: {congress_stats['current_requests']}/{congress_stats['max_requests']} requests"
    )
    print(
        f"✓ Senate API: {senate_stats['current_requests']}/{senate_stats['max_requests']} requests"
    )

    print("\n✅ Core package demo completed successfully!")
    print("\n💡 Tips:")
    print("   • Use the core package for new scripts")
    print("   • Existing scripts have backward compatibility")
    print("   • Check rate limiter stats to avoid API limits")
    print("   • Use FileStorage for consistent data organization")


if __name__ == "__main__":
    main()
