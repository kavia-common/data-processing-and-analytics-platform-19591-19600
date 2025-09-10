from __future__ import annotations

import smtplib
import ssl
import uuid
from email.message import EmailMessage
from typing import Tuple

from ..utils.settings import get_settings


class NotificationService:
    """
    Service to send email notifications using SMTP settings from environment.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    # PUBLIC_INTERFACE
    def send_email(self, to: str, subject: str, body: str, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Send an email. Returns (sent, message_id).
        If SMTP is not configured or dry_run=True, it logs and returns success with a generated ID.
        """
        # Basic validation
        if not to or not subject or not body:
            raise ValueError("to, subject, and body are required")

        # Dry run or missing SMTP -> simulate
        if dry_run or not (self.settings.SMTP_HOST and self.settings.SMTP_PORT and self.settings.SMTP_FROM):
            return True, f"dryrun-{uuid.uuid4()}"

        msg = EmailMessage()
        msg["From"] = self.settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        context = ssl.create_default_context()
        if self.settings.SMTP_USE_TLS:
            with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as server:
                server.starttls(context=context)
                if self.settings.SMTP_USER and self.settings.SMTP_PASSWORD:
                    server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(self.settings.SMTP_HOST, self.settings.SMTP_PORT, context=context) as server:
                if self.settings.SMTP_USER and self.settings.SMTP_PASSWORD:
                    server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                server.send_message(msg)

        return True, str(uuid.uuid4())
