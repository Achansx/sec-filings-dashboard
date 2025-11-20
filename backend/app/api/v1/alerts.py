"""API routes for alert operations."""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_alerts():
    """
    Get list of user alerts.

    Note: This is a placeholder endpoint.
    Full implementation will be added in Phase 2.
    """
    return {
        "message": "Alerts endpoint - To be implemented in Phase 2",
        "items": [],
    }


@router.post("")
async def create_alert():
    """
    Create a new alert.

    Note: This is a placeholder endpoint.
    Full implementation will be added in Phase 2.
    """
    return {
        "message": "Create alert endpoint - To be implemented in Phase 2",
    }
