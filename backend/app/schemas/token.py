"""Token schema definitions."""

from pydantic import BaseModel, Field


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str = Field(..., min_length=1)
