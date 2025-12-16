#!/usr/bin/env python3
"""
Test script for Member Consistency Analysis System

This script runs basic tests to verify the analysis system is working correctly.
"""

import json
import logging
import sys
from pathlib import Path

from analyze_member_consistency import MemberConsistencyAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_analysis():
    """Test basic analysis functionality"""
    logger.info("Testing basic analysis functionality...")

    try:
        # Initialize analyzer
        analyzer = MemberConsistencyAnalyzer(data_dir="data")

        # Load data
        analyzer.load_member_data()
        analyzer.load_voting_data()

        # Run analysis components
        analyzer.calculate_party_unity_scores()
        analyzer.identify_major_defections()
        analyzer.analyze_bipartisan_collaboration()
        analyzer.calculate_advanced_metrics()

        # Check results
        members_with_votes = [
            member
            for member in analyzer.members.values()
            if member.total_votes >= analyzer.min_votes_for_analysis
        ]

        logger.info(
            f"✓ Analyzed {len(members_with_votes)} members with sufficient voting data"
        )

        # Test rankings
        rankings = analyzer.generate_rankings()
        logger.info(f"✓ Generated {len(rankings)} ranking categories")

        return True

    except Exception as e:
        logger.error(f"✗ Basic analysis test failed: {e}")
        return False


def test_data_integrity():
    """Test data integrity and validation"""
    logger.info("Testing data integrity...")

    try:
        # Check required directories
        data_dir = Path("data")
        required_dirs = [
            data_dir / "members" / "118",
            data_dir / "member_consistency",
            data_dir / "analysis",
        ]

        for directory in required_dirs:
            if not directory.exists():
                logger.error(f"✗ Required directory missing: {directory}")
                return False

        logger.info("✓ All required directories exist")

        # Check member data
        members_dir = data_dir / "members" / "118"
        member_files = list(members_dir.glob("*.json"))

        if len(member_files) < 100:  # Expect at least 100 members
            logger.warning(f"⚠ Only {len(member_files)} member files found")
        else:
            logger.info(f"✓ Found {len(member_files)} member files")

        # Validate sample member file
        if member_files:
            with open(member_files[0]) as f:
                member_data = json.load(f)

            required_fields = ["bioguideId", "name", "party", "state", "chamber"]
            for field in required_fields:
                if field not in member_data:
                    logger.error(f"✗ Missing required field '{field}' in member data")
                    return False

            logger.info("✓ Member data structure validation passed")

        return True

    except Exception as e:
        logger.error(f"✗ Data integrity test failed: {e}")
        return False


def test_output_generation():
    """Test output file generation"""
    logger.info("Testing output generation...")

    try:
        # Check if analysis output exists
        analysis_file = Path("data/analysis/member_consistency_analysis.json")

        if not analysis_file.exists():
            logger.error("✗ Analysis output file not found")
            return False

        # Validate analysis file structure
        with open(analysis_file) as f:
            analysis_data = json.load(f)

        required_sections = ["metadata", "aggregate_statistics", "rankings"]
        for section in required_sections:
            if section not in analysis_data:
                logger.error(f"✗ Missing section '{section}' in analysis output")
                return False

        logger.info("✓ Analysis output structure validation passed")

        # Check member profiles
        profiles_dir = Path("data/member_consistency")
        profile_files = list(profiles_dir.glob("*_consistency_profile.json"))

        if len(profile_files) < 50:  # Expect at least 50 profiles
            logger.warning(f"⚠ Only {len(profile_files)} member profiles generated")
        else:
            logger.info(f"✓ Generated {len(profile_files)} member profiles")

        # Validate sample profile
        if profile_files:
            with open(profile_files[0]) as f:
                profile_data = json.load(f)

            required_fields = [
                "bioguide_id",
                "name",
                "party",
                "party_unity_score",
                "maverick_score",
                "consistency_rating",
            ]
            for field in required_fields:
                if field not in profile_data:
                    logger.error(f"✗ Missing field '{field}' in member profile")
                    return False

            logger.info("✓ Member profile structure validation passed")

        return True

    except Exception as e:
        logger.error(f"✗ Output generation test failed: {e}")
        return False


def test_consistency_calculations():
    """Test consistency calculation logic"""
    logger.info("Testing consistency calculations...")

    try:
        # Load a sample profile for validation
        profiles_dir = Path("data/member_consistency")
        profile_files = list(profiles_dir.glob("*_consistency_profile.json"))

        if not profile_files:
            logger.error("✗ No member profiles found for testing")
            return False

        # Test calculation logic
        valid_profiles = 0

        for profile_file in profile_files[:10]:  # Test first 10 profiles
            with open(profile_file) as f:
                profile = json.load(f)

            # Validate score ranges
            party_unity = profile.get("party_unity_score", 0)
            maverick_score = profile.get("maverick_score", 0)
            bipartisan_score = profile.get("bipartisan_score", 0)

            # Check score ranges (0.0 to 1.0)
            if not (0.0 <= party_unity <= 1.0):
                logger.error(f"✗ Invalid party unity score: {party_unity}")
                return False

            if not (0.0 <= maverick_score <= 1.0):
                logger.error(f"✗ Invalid maverick score: {maverick_score}")
                return False

            if not (0.0 <= bipartisan_score <= 1.0):
                logger.error(f"✗ Invalid bipartisan score: {bipartisan_score}")
                return False

            # Check score relationship (unity + maverick should approximately equal 1.0)
            score_sum = party_unity + maverick_score
            if not (0.99 <= score_sum <= 1.01):  # Allow small floating point errors
                logger.error(
                    f"✗ Unity and maverick scores don't sum correctly: {score_sum}"
                )
                return False

            valid_profiles += 1

        logger.info(f"✓ Validated calculations for {valid_profiles} member profiles")
        return True

    except Exception as e:
        logger.error(f"✗ Consistency calculations test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests and provide summary"""
    logger.info("=" * 60)
    logger.info("MEMBER CONSISTENCY ANALYSIS SYSTEM - COMPREHENSIVE TEST")
    logger.info("=" * 60)

    tests = [
        ("Data Integrity", test_data_integrity),
        ("Basic Analysis", test_basic_analysis),
        ("Output Generation", test_output_generation),
        ("Consistency Calculations", test_consistency_calculations),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} test...")
        try:
            if test_func():
                logger.info(f"✓ {test_name} test PASSED")
                passed_tests += 1
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test ERROR: {e}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Passed: {passed_tests}/{total_tests} tests")

    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - System is working correctly!")
        return True
    else:
        logger.error(f"❌ {total_tests - passed_tests} tests failed - Check logs above")
        return False


def main():
    """Main test execution"""
    success = run_comprehensive_test()

    if success:
        print("\n✅ Member Consistency Analysis System is working correctly!")
        print("You can now use the system with confidence.")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
        print("Fix any issues before using the system.")
        sys.exit(1)


if __name__ == "__main__":
    main()
