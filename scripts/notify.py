from __future__ import annotations

import os
from typing import Any

import requests

RESEND_URL = "https://api.resend.com/emails"
TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def _permalink(base_url: str, year: str, month: str, day: str, slot: str) -> str:
    return f"{base_url.rstrip('/')}/{year}/{month}/{day}-{slot}"


def send_email(cfg: dict[str, Any], subject: str, html: str, text: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set.")
    recipients = cfg.get("recipients") or []
    if not recipients:
        return
    requests.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": cfg["from"],
            "to": recipients,
            "subject": subject,
            "html": html,
            "text": text,
        },
        timeout=30,
    ).raise_for_status()


def send_sms(cfg: dict[str, Any], body: str) -> None:
    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    if not sid or not token:
        raise RuntimeError("TWILIO_SID / TWILIO_TOKEN are not set.")
    for to in cfg.get("recipients") or []:
        requests.post(
            TWILIO_URL.format(sid=sid),
            auth=(sid, token),
            data={"From": cfg["from"], "To": to, "Body": body},
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
    sms = f"Daily Bread ({today:%-m/%-d} {slot[:3].upper()}): {reference} — {link}"

    if cfg.get("email", {}).get("enabled"):
        send_email(cfg["email"], subject, html, text)
    if cfg.get("sms", {}).get("enabled"):
        send_sms(cfg["sms"], sms)
