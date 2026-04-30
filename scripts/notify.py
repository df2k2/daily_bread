from __future__ import annotations

import os
from datetime import date as date_t
from typing import Any

import requests

from .render import _format_date

RESEND_URL = "https://api.resend.com/emails"
TWILIO_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"

NOTIFICATION_COPY = {
    "en": {
        "subject": "Today's Bread — {date}, {slot}",
        "html": (
            "<p><strong>{title}</strong></p>"
            "<p>{reference}</p>"
            '<p><a href="{link}">Read it here</a></p>'
        ),
        "text": "{title}\n{reference}\n{link}",
        "sms": "Daily Bread ({short_date} {slot_tag}): {reference} — {link}",
        "slot_morning": "MORNING",
        "slot_evening": "EVENING",
    },
    "pt": {
        "subject": "Pão de Hoje — {date}, {slot}",
        "html": (
            "<p><strong>{title}</strong></p>"
            "<p>{reference}</p>"
            '<p><a href="{link}">Leia aqui</a></p>'
        ),
        "text": "{title}\n{reference}\n{link}",
        "sms": "Pão Diário ({short_date} {slot_tag}): {reference} — {link}",
        "slot_morning": "MANHÃ",
        "slot_evening": "NOITE",
    },
}

SLOT_LABELS = {
    "en": {"morning": "morning", "evening": "evening"},
    "pt": {"morning": "manhã", "evening": "noite"},
}


def _permalink(base_url: str, lang: str, primary_lang: str, today: date_t, slot: str) -> str:
    base = base_url.rstrip("/")
    slug = f"{today:%Y}/{today:%m}/{today:%d}-{slot}"
    if lang == primary_lang:
        return f"{base}/{slug}"
    return f"{base}/{lang}/{slug}"


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
    today: date_t,
    slot: str,
    titles_by_lang: dict[str, str],
    reference: str,
    primary_language: str,
) -> None:
    recipients = cfg.get("recipients") or []
    if not recipients:
        return

    email_cfg = cfg.get("email") or {}
    sms_cfg = cfg.get("sms") or {}

    for r in recipients:
        lang = r.get("language", primary_language)
        if lang not in NOTIFICATION_COPY:
            lang = primary_language
        copy = NOTIFICATION_COPY[lang]

        title = titles_by_lang.get(lang) or next(iter(titles_by_lang.values()))
        link = _permalink(site_cfg["base_url"], lang, primary_language, today, slot)
        slot_label = SLOT_LABELS[lang][slot]

        ctx = {
            "title": title,
            "reference": reference,
            "link": link,
            "date": _format_date(today, lang),
            "short_date": today.strftime("%-m/%-d"),
            "slot": slot_label,
            "slot_tag": copy[f"slot_{slot}"],
        }

        if _wants(r, slot, "email"):
            _send_email(
                email_cfg["from"],
                r["email"],
                copy["subject"].format(**ctx),
                copy["html"].format(**ctx),
                copy["text"].format(**ctx),
            )
        if _wants(r, slot, "sms"):
            _send_sms(sms_cfg["from"], r["sms"], copy["sms"].format(**ctx))
