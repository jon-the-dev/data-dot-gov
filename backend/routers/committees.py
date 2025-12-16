"""
Committee API Router

FastAPI router for committee-related endpoints.
Implements all endpoints required by TODO1.md Phase 6.1
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from services.committee_service import CommitteeService, MockCommitteeDataGenerator
from services.cache_service import cache_response, CachingStrategy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/committees", tags=["committees"])

# Initialize service
committee_service = CommitteeService()

@router.get("")
async def get_committees(
    congress: int = Query(118, description="Congress number"),
    chamber: Optional[str] = Query(None, description="Filter by chamber (house, senate, joint)"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get all committees with optional chamber filtering and pagination

    Returns:
    - List of committees with metadata
    - Chamber breakdown
    - Pagination info
    """
    try:
        # Get committee data
        result = await committee_service.get_all_committees(congress, chamber)

        if "error" in result:
            # Try mock data if real data not available
            logger.warning(f"Committee data not found for congress {congress}, using mock data")
            result = MockCommitteeDataGenerator.generate_mock_committees(congress)

        # Apply pagination
        all_committees = result["committees"]
        total = len(all_committees)
        paginated_committees = all_committees[offset:offset + limit]

        return {
            "committees": paginated_committees,
            "total": total,
            "by_chamber": result.get("by_chamber"),
            "limit": limit,
            "offset": offset,
            "congress": congress,
            "chamber_filter": chamber,
            "is_mock": result.get("is_mock", False)
        }

    except Exception as e:
        logger.error(f"Error in get_committees: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}")
@cache_response("committee_details", ttl=CachingStrategy.LONG_TTL, key_params=["committee_id", "congress"])
async def get_committee_details(
    committee_id: str,
    congress: int = Query(118, description="Congress number")
):
    """
    Get details for a specific committee by its ID

    Args:
        committee_id: Committee system code (e.g., 'HSAG', 'SSAG')
        congress: Congress number

    Returns:
        Detailed committee information including subcommittees
    """
    try:
        committee_data = await committee_service.get_committee_details(committee_id, congress)

        if not committee_data:
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found in congress {congress}"
            )

        return committee_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/subcommittees")
async def get_committee_subcommittees(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get subcommittees for a specific committee

    Args:
        committee_id: Parent committee system code
        congress: Congress number
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of subcommittees with pagination info
    """
    try:
        # Check if parent committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get subcommittees
        subcommittees = await committee_service.get_committee_subcommittees(committee_id, congress)

        # Apply pagination
        total = len(subcommittees)
        paginated_subcommittees = subcommittees[offset:offset + limit]

        return {
            "committee_id": committee_id,
            "subcommittees": paginated_subcommittees,
            "total": total,
            "limit": limit,
            "offset": offset,
            "congress": congress
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_subcommittees: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/members")
@cache_response("committee_members", ttl=CachingStrategy.MEDIUM_TTL, key_params=["committee_id", "congress", "limit", "offset"])
async def get_committee_members(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get members of a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of committee members with roles and metadata
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get members (currently returns placeholder)
        result = await committee_service.get_committee_members(committee_id, congress)

        # Add pagination info
        result.update({
            "limit": limit,
            "offset": offset
        })

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_members: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/bills")
@cache_response("committee_bills", ttl=CachingStrategy.MEDIUM_TTL, key_params=["committee_id", "congress", "limit", "offset"])
async def get_committee_bills(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get bills referred to or considered by a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of bills with committee status and metadata
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get bills (currently returns placeholder)
        result = await committee_service.get_committee_bills(committee_id, congress)

        # Add pagination info
        result.update({
            "limit": limit,
            "offset": offset
        })

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_bills: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/votes")
async def get_committee_votes(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get voting records for a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of committee voting records with metadata
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get votes (currently returns placeholder)
        result = await committee_service.get_committee_votes(committee_id, congress)

        # Add pagination info
        result.update({
            "limit": limit,
            "offset": offset
        })

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_votes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/analytics")
async def get_committee_analytics(
    committee_id: str,
    congress: int = Query(118, description="Congress number")
):
    """
    Get analytics for a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number

    Returns:
        Committee analytics including activity metrics and trends
    """
    try:
        analytics = await committee_service.get_committee_analytics(committee_id, congress)

        if not analytics:
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Additional endpoint for subcommittee details
@router.get("/subcommittees/{subcommittee_id}")
async def get_subcommittee_details(
    subcommittee_id: str,
    congress: int = Query(118, description="Congress number")
):
    """
    Get details for a specific subcommittee by its ID

    Args:
        subcommittee_id: Subcommittee system code
        congress: Congress number

    Returns:
        Detailed subcommittee information including parent committee info
    """
    try:
        subcommittee_data = await committee_service.get_subcommittee_details(subcommittee_id, congress)

        if not subcommittee_data:
            raise HTTPException(
                status_code=404,
                detail=f"Subcommittee {subcommittee_id} not found in congress {congress}"
            )

        return subcommittee_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_subcommittee_details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

# Committee Activity Endpoints (Phase 2)

@router.get("/{committee_id}/hearings")
async def get_committee_hearings(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get hearings for a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of committee hearings with witness lists and metadata
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get hearings
        result = await committee_service.get_committee_hearings(committee_id, congress, limit, offset)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_hearings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/meetings")
async def get_committee_meetings(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get meetings/markups for a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of committee meetings with agenda items and metadata
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get meetings
        result = await committee_service.get_committee_meetings(committee_id, congress, limit, offset)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_meetings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/documents")
async def get_committee_documents(
    committee_id: str,
    congress: int = Query(118, description="Congress number"),
    document_type: Optional[str] = Query(None, description="Filter by document type (report, print, document)"),
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip")
):
    """
    Get documents/reports for a specific committee

    Args:
        committee_id: Committee system code
        congress: Congress number
        document_type: Filter by document type
        limit: Maximum results
        offset: Results to skip

    Returns:
        List of committee documents and reports with metadata
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get documents
        result = await committee_service.get_committee_documents(
            committee_id, congress, document_type, limit, offset
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/{committee_id}/activity-summary")
async def get_committee_activity_summary(
    committee_id: str,
    congress: int = Query(118, description="Congress number")
):
    """
    Get comprehensive activity summary for a committee

    Args:
        committee_id: Committee system code
        congress: Congress number

    Returns:
        Activity summary with counts of hearings, meetings, documents, and recent activity
    """
    try:
        # Check if committee exists
        if not await committee_service.committee_exists(committee_id, congress):
            raise HTTPException(
                status_code=404,
                detail=f"Committee {committee_id} not found"
            )

        # Get activity summary
        result = await committee_service.get_committee_activity_summary(committee_id, congress)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_committee_activity_summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
