from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..schemas.notifications import EmailRequest, EmailResponse
from ..services.notification_service import NotificationService
from ..utils.dependencies import get_notification_service

router = APIRouter()


@router.post(
    "/email",
    summary="Send an email notification",
    description="Send an email to notify users of processing/report completion. Uses environment-configured SMTP.",
    response_model=EmailResponse,
)
# PUBLIC_INTERFACE
def send_email(
    req: EmailRequest,
    svc: NotificationService = get_notification_service,
) -> EmailResponse:
    """
    Send an email notification. In development, if SMTP is not configured, the service performs a dry run and logs the email.
    """
    try:
        sent, message_id = svc.send_email(
            to=req.to,
            subject=req.subject,
            body=req.body,
            dry_run=req.dry_run,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return EmailResponse(sent=sent, message_id=message_id)
