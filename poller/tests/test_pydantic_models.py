#!/usr/bin/env python3
"""
Test script for the new Pydantic v2 models.

Validates that all models can be imported and instantiated with sample data.
"""

import json
import sys


def test_model_imports():
    """Test that all models can be imported successfully."""
    print("Testing model imports...")

    try:
        # Test importing all models (use _ prefix to indicate they're for testing only)
        from core.models import Bill as _Bill
        from core.models import BillAction as _BillAction
        from core.models import BillSponsor as _BillSponsor
        from core.models import BillSubject as _BillSubject
        from core.models import BillType as _BillType
        from core.models import Chamber as _Chamber
        from core.models import Member as _Member
        from core.models import Party as _Party
        from core.models import Vote as _Vote
        from core.models import VotePosition as _VotePosition

        print("✅ All model imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_enum_normalization():
    """Test enum normalization functions."""
    print("\nTesting enum normalization...")

    from core.models.enums import BillType, Chamber, Party, VotePosition

    # Test Party normalization
    assert Party.normalize("D") == Party.DEMOCRATIC
    assert Party.normalize("Democratic") == Party.DEMOCRATIC
    assert Party.normalize("R") == Party.REPUBLICAN
    assert Party.normalize("Republican") == Party.REPUBLICAN
    assert Party.normalize("I") == Party.INDEPENDENT
    assert Party.normalize("invalid") == Party.UNKNOWN
    assert Party.normalize(None) == Party.UNKNOWN

    # Test Chamber normalization
    assert Chamber.normalize("house") == Chamber.HOUSE
    assert Chamber.normalize("House of Representatives") == Chamber.HOUSE
    assert Chamber.normalize("senate") == Chamber.SENATE
    assert Chamber.normalize("S") == Chamber.SENATE
    assert Chamber.normalize("invalid") == Chamber.UNKNOWN

    # Test VotePosition normalization
    assert VotePosition.normalize("Yea") == VotePosition.YEA
    assert VotePosition.normalize("yes") == VotePosition.YEA
    assert VotePosition.normalize("Nay") == VotePosition.NAY
    assert VotePosition.normalize("no") == VotePosition.NAY

    # Test BillType normalization
    assert BillType.normalize("HR") == BillType.HOUSE_BILL
    assert BillType.normalize("S") == BillType.SENATE_BILL
    assert BillType.normalize("invalid") is None

    print("✅ Enum normalization tests passed")


def test_member_model():
    """Test Member model with sample data."""
    print("\nTesting Member model...")

    from core.models import Chamber, Member, Party

    # Sample member data
    member_data = {
        "bioguideId": "B001281",
        "name": "Beatty, Joyce",
        "party": "Democratic",
        "state": "Ohio",
        "chamber": "house",
        "district": 3,
        "firstName": "Joyce",
        "lastName": "Beatty",
        "terms": [
            {
                "chamber": "House of Representatives",
                "congress": 118,
                "district": 3,
                "startYear": 2023,
                "endYear": 2025,
                "memberType": "Representative",
                "stateCode": "OH",
                "stateName": "Ohio",
            }
        ],
        "depiction": {
            "attribution": "Image courtesy of the Member",
            "imageUrl": "https://www.congress.gov/img/member/b001281_200.jpg",
        },
    }

    try:
        member = Member(**member_data)

        # Test computed properties
        assert member.party == Party.DEMOCRATIC
        assert member.chamber == Chamber.HOUSE
        assert member.is_representative
        assert not member.is_senator
        expected_display = "Rep. Beatty, Joyce (D)-Ohio-3"
        print(f"Expected: {expected_display}")
        print(f"Actual: {member.display_name}")
        assert member.display_name == expected_display
        assert member.total_years_served == 2

        print(f"✅ Member model test passed: {member.display_name}")
        return True
    except Exception as e:
        print(f"❌ Member model test failed: {e}")
        return False


def test_bill_model():
    """Test Bill model with sample data."""
    print("\nTesting Bill model...")

    from core.models import Bill, BillType, Party

    # Sample bill data
    bill_data = {
        "congress": 118,
        "type": "HR",
        "number": "10373",
        "title": "Sample Bill Title",
        "sponsors": [
            {
                "bioguideId": "T000478",
                "fullName": "Rep. Tenney, Claudia [R-NY-24]",
                "firstName": "Claudia",
                "lastName": "Tenney",
                "party": "R",
                "state": "NY",
                "district": 24,
            }
        ],
        "cosponsors": [
            {
                "bioguideId": "C001059",
                "fullName": "Rep. Costa, Jim [D-CA-21]",
                "firstName": "Jim",
                "lastName": "Costa",
                "party": "D",
                "state": "CA",
                "district": 21,
                "isOriginalCosponsor": True,
                "sponsorshipDate": "2024-12-11",
            }
        ],
        "subjects": ["Healthcare", "Budget"],
    }

    try:
        bill = Bill(**bill_data)

        # Test computed properties
        assert bill.bill_type == BillType.HOUSE_BILL
        assert bill.display_name == "HR 10373"
        assert bill.sponsor_count == 1
        assert bill.cosponsor_count == 1
        assert bill.total_sponsors == 2
        assert bill.is_bipartisan

        # Test party breakdown
        party_breakdown = bill.get_sponsors_by_party()
        assert party_breakdown[Party.REPUBLICAN] == 1
        assert party_breakdown[Party.DEMOCRATIC] == 1

        print(f"✅ Bill model test passed: {bill.display_name}")
        return True
    except Exception as e:
        print(f"❌ Bill model test failed: {e}")
        return False


def test_vote_model():
    """Test Vote model with sample data."""
    print("\nTesting Vote model...")

    from core.models import (
        Chamber,
        Party,
        Vote,
    )

    # Sample vote data
    vote_data = {
        "congress": 118,
        "chamber": "house",
        "session": 1,
        "roll_call": 500,
        "question": "On Passage of H.R. 82",
        "result": "Passed",
        "yea_count": 250,
        "nay_count": 180,
        "party_breakdown": [
            {"party": "D", "yea": 200, "nay": 15},
            {"party": "R", "yea": 50, "nay": 165},
        ],
        "member_votes": [
            {
                "bioguideId": "B001281",
                "name": "Joyce Beatty",
                "party": "D",
                "state": "OH",
                "vote_position": "Yea",
                "district": 3,
            }
        ],
    }

    try:
        vote = Vote(**vote_data)

        # Test computed properties
        assert vote.chamber == Chamber.HOUSE
        assert vote.passed
        assert vote.total_votes == 430
        assert vote.margin_of_victory == 70

        # Test party breakdown
        unity_scores = vote.get_party_unity_scores()
        assert Party.DEMOCRATIC in unity_scores
        assert Party.REPUBLICAN in unity_scores

        print(f"✅ Vote model test passed: {vote.display_name}")
        return True
    except Exception as e:
        print(f"❌ Vote model test failed: {e}")
        return False


def test_json_serialization():
    """Test JSON serialization of models."""
    print("\nTesting JSON serialization...")

    from core.models import Member

    member_data = {
        "bioguideId": "TEST001",
        "name": "Test Member",
        "party": "D",
        "state": "TX",
        "chamber": "house",
    }

    try:
        member = Member(**member_data)

        # Test model_dump
        member_dict = member.model_dump()
        assert isinstance(member_dict, dict)
        assert member_dict["bioguide_id"] == "TEST001"

        # Test JSON serialization
        json_safe_dict = member.model_dump_json_safe()
        json_str = json.dumps(json_safe_dict)

        # Test that we can deserialize
        loaded_dict = json.loads(json_str)
        new_member = Member(**loaded_dict)
        assert new_member.bioguide_id == member.bioguide_id

        print("✅ JSON serialization test passed")
        return True
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False


def run_all_tests():
    """Run all model tests."""
    print("Starting Pydantic v2 model tests...\n")

    tests = [
        test_model_imports,
        test_enum_normalization,
        test_member_model,
        test_bill_model,
        test_vote_model,
        test_json_serialization,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
