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


def _build_password_reset_message(to_email: str, token: str) -> EmailMessage:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "DriveEase - Reset your password"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"Hi,\n\n"
        f"We received a request to reset your password.\n"
        f"Click the link below to set a new password:\n"
        f"{reset_url}\n\n"
        f"This link expires in {settings.RESET_PASSWORD_TOKEN_EXPIRE_HOURS} hour(s).\n"
        f"If you did not request this, you can safely ignore this email."
    )
    return msg


def _send_email(msg: EmailMessage) -> None:
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent to %s", msg["To"])
    except Exception:
        logger.exception("Failed to send email to %s", msg["To"])


def send_verification_email(to_email: str, token: str) -> None:
    msg = _build_verification_message(to_email, token)
    _send_email(msg)


def send_password_reset_email(to_email: str, token: str) -> None:
    msg = _build_password_reset_message(to_email, token)
    _send_email(msg)
