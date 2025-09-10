from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr


class EmailRequest(BaseModel):
    """Request to send email notification."""

    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (text)")
    dry_run: bool = Field(False, description="If true, do not send; only log")


class EmailResponse(BaseModel):
    """Response indicating result of send operation."""

    sent: bool = Field(..., description="Whether the email was sent (or dry-run successful)")
    message_id: str = Field(..., description="Message ID or reference")
