from __future__ import annotations

import os
from typing import Any

import requests

RESEND_URL = "https://api.resend.com/emails"
TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def _permalink(base_url: str, year: str, month: str, day: str, slot: str) -> str:
    return f"{base_url.rstrip('/')}/{year}/{month}/{day}-{slot}"


def _wants(recipient: dict[str, Any], slot: str, channel: str) -> bool:
    slots = recipient.get("slots") or []
    if slots and slot not in slots:
        return False
    channels = recipient.get("channels") or ["email", "sms"]
    if channel not in channels:
        return False
    return bool(recipient.get(channel))


def _send_email(from_addr: str, to: str, subject: str, html: str, text: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set.")
    requests.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"from": from_addr, "to": [to], "subject": subject, "html": html, "text": text},
        timeout=30,
    ).raise_for_status()


def _send_sms(from_number: str, to: str, body: str) -> None:
    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    if not sid or not token:
        raise RuntimeError("TWILIO_SID / TWILIO_TOKEN are not set.")
    requests.post(
        TWILIO_URL.format(sid=sid),
        auth=(sid, token),
        data={"From": from_number, "To": to, "Body": body},
        timeout=30,
    ).raise_for_status()


def notify(
    cfg: dict[str, Any],
    site_cfg: dict[str, Any],
    today: Any,
    slot: str,
    title: str,
    reference: str,
) -> None:
    recipients = cfg.get("recipients") or []
    if not recipients:
        return

    link = _permalink(
        site_cfg["base_url"],
        f"{today:%Y}",
        f"{today:%m}",
        f"{today:%d}",
        slot,
    )
    subject = f"Today's Bread — {today:%B %-d}, {slot}"
    html = (
        f"<p><strong>{title}</strong></p>"
        f"<p>{reference}</p>"
        f'<p><a href="{link}">Read it here</a></p>'
    )
    text = f"{title}\n{reference}\n{link}"
    sms_body = f"Daily Bread ({today:%-m/%-d} {slot[:3].upper()}): {reference} — {link}"

    email_cfg = cfg.get("email") or {}
    sms_cfg = cfg.get("sms") or {}

    for r in recipients:
        if _wants(r, slot, "email"):
            _send_email(email_cfg["from"], r["email"], subject, html, text)
        if _wants(r, slot, "sms"):
            _send_sms(sms_cfg["from"], r["sms"], sms_body)
