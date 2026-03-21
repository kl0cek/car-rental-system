import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def _build_verification_message(to_email: str, token: str) -> EmailMessage:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "DriveEase - Verify your email"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"Welcome to DriveEase!\n\n"
        f"Please verify your email by clicking the link below:\n"
        f"{verify_url}\n\n"
        f"This link expires in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hours."
    )
    return msg


def send_verification_email(to_email: str, token: str) -> None:
    msg = _build_verification_message(to_email, token)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Verification email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
