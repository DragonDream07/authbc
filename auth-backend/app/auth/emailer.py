from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def _build_reset_link(raw_token: str) -> str:
    """Build the full password-reset URL from the base URL and the raw token."""
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/reset-password?token={raw_token}"


def _build_plain_text_body(reset_link: str) -> str:
    return (
        "You requested a password reset.\n\n"
        "Click the link below to reset your password:\n"
        f"{reset_link}\n\n"
        "This link will expire according to the configured reset token TTL.\n\n"
        "If you did not request this, please ignore this email."
    )


def _build_html_body(reset_link: str) -> str:
    return (
        "<html><body>"
        "<p>You requested a password reset.</p>"
        "<p>Click the link below to reset your password:</p>"
        f'<p><a href="{reset_link}">{reset_link}</a></p>'
        "<p>This link will expire according to the configured reset token TTL.</p>"
        "<p>If you did not request this, please ignore this email.</p>"
        "</body></html>"
    )


def send_reset_email(*, to_email: str, raw_token: str) -> None:
    """Send a password-reset email to *to_email* containing the reset link.

    The reset link is built as APP_BASE_URL/reset-password?token=<raw_token>.
    SMTP connection parameters are taken from the SMTP_* settings.
    """
    reset_link = _build_reset_link(raw_token)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your password"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    plain_part = MIMEText(_build_plain_text_body(reset_link), "plain", "utf-8")
    html_part = MIMEText(_build_html_body(reset_link), "html", "utf-8")

    # Attach plain first, HTML second (preferred by RFC 2046 §5.1.4)
    msg.attach(plain_part)
    msg.attach(html_part)

    if settings.SMTP_TLS:
        _send_via_ssl(msg=msg, to_email=to_email)
    else:
        _send_via_starttls_or_plain(msg=msg, to_email=to_email)


def _send_via_ssl(*, msg: MIMEMultipart, to_email: str) -> None:
    """Connect using SMTP_SSL (implicit TLS, typically port 465)."""
    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())


def _send_via_starttls_or_plain(*, msg: MIMEMultipart, to_email: str) -> None:
    """Connect using plain SMTP and upgrade with STARTTLS when SMTP_STARTTLS is set."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        if getattr(settings, "SMTP_STARTTLS", False):
            server.starttls()
            server.ehlo()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
