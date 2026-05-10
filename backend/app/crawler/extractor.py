from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from backend.app.models import FormField, FormInfo, LinkInfo


RISK_TERM_CATEGORIES = {
    "financial_crypto": {
        "high": {"bitcoin", "crypto", "ethereum", "forex", "metamask", "staking", "wallet"},
        "medium": {"airdrop", "broker", "deposit", "investment", "loan", "nft", "trading", "withdraw"},
    },
    "earnings_claims": {
        "high": {"double your money", "earn daily", "guaranteed return", "return on investment"},
        "medium": {"profit"},
    },
    "payment": {
        "high": {"credit card"},
        "medium": {"billing", "checkout", "payment", "subscription"},
    },
    "reward_pressure": {
        "medium": {"free trial", "limited offer", "urgent"},
        "low": {"bonus", "claim"},
    },
    "adult_sensitive": {
        "high": {"escort", "explicit", "porn", "xxx"},
        "medium": {"adult", "cam", "sex"},
    },
}

TERM_CONFIDENCE = {"high": 0.9, "medium": 0.7, "low": 0.45}

DOWNLOAD_EXTENSIONS = (
    ".apk",
    ".dmg",
    ".exe",
    ".msi",
    ".pkg",
    ".zip",
    ".rar",
    ".7z",
    ".scr",
)


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def extract_hidden_text(soup: BeautifulSoup) -> list[str]:
    hidden: list[str] = []
    selectors = [
        "[hidden]",
        "[aria-hidden='true']",
        "[style*='display:none']",
        "[style*='display: none']",
        "[style*='visibility:hidden']",
        "[style*='visibility: hidden']",
        "[style*='opacity:0']",
        "[style*='opacity: 0']",
    ]
    for node in soup.select(",".join(selectors)):
        text = clean_text(node.get_text(" ", strip=True))
        if text and text not in hidden:
            hidden.append(text)
    return hidden[:50]


def extract_links(soup: BeautifulSoup, base_url: str) -> list[LinkInfo]:
    links: list[LinkInfo] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, str(anchor.get("href")))
        text = clean_text(anchor.get_text(" ", strip=True))
        links.append(LinkInfo(text=text[:160], href=href))
    return links[:300]


def _label_for_field(field: Tag) -> str | None:
    field_id = field.get("id")
    if field_id:
        label = field.find_parent().find("label", attrs={"for": field_id}) if field.find_parent() else None
        if label:
            return clean_text(label.get_text(" ", strip=True))
    parent_label = field.find_parent("label")
    if parent_label:
        return clean_text(parent_label.get_text(" ", strip=True))
    return None


def extract_forms(soup: BeautifulSoup, base_url: str) -> list[FormInfo]:
    forms: list[FormInfo] = []
    for form in soup.find_all("form"):
        fields: list[FormField] = []
        for field in form.find_all(["input", "textarea", "select"]):
            field_type = str(field.get("type") or field.name or "text").lower()
            if field_type in {"hidden", "submit", "button", "image", "reset"}:
                continue
            fields.append(
                FormField(
                    name=field.get("name"),
                    field_type=field_type,
                    label=_label_for_field(field),
                    placeholder=field.get("placeholder"),
                )
            )
        forms.append(
            FormInfo(
                action=urljoin(base_url, str(form.get("action"))) if form.get("action") else None,
                method=str(form.get("method") or "get").upper(),
                fields=fields,
            )
        )
    return forms


def has_download_cta(soup: BeautifulSoup, base_url: str) -> bool:
    text_pattern = re.compile(r"\b(download|install|get app|apk|claim file)\b", re.I)
    for element in soup.find_all(["a", "button"]):
        text = clean_text(element.get_text(" ", strip=True))
        href = urljoin(base_url, str(element.get("href") or ""))
        if text_pattern.search(text) or href.lower().endswith(DOWNLOAD_EXTENSIONS):
            return True
    return False


def matched_risk_terms(text: str) -> list[str]:
    categories = matched_risk_term_categories(text)
    return sorted({term for terms in categories.values() for term in terms})


def matched_risk_term_categories(text: str) -> dict[str, list[str]]:
    evidence = matched_risk_term_evidence(text)
    return {
        category: sorted({item["term"] for item in items})
        for category, items in evidence.items()
    }


def _snippet(text: str, start: int, end: int, window: int = 80) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return clean_text(text[left:right])


def _is_negated_context(text: str, start: int) -> bool:
    prefix = text[max(0, start - 35) : start].lower()
    return bool(re.search(r"\b(no|not|without|avoid|禁止|不含|没有)\s+$", prefix))


def matched_risk_term_evidence(text: str) -> dict[str, list[dict]]:
    matches: dict[str, list[dict]] = {}
    lowered = text.lower()
    for category, tiers in RISK_TERM_CATEGORIES.items():
        category_matches: list[dict] = []
        for tier, terms in tiers.items():
            for term in terms:
                pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
                match = re.search(pattern, lowered)
                if not match:
                    continue
                if _is_negated_context(text, match.start()):
                    continue
                category_matches.append(
                    {
                        "term": term,
                        "tier": tier,
                        "confidence": TERM_CONFIDENCE[tier],
                        "context": _snippet(text, match.start(), match.end()),
                    }
                )
        if category_matches:
            matches[category] = sorted(category_matches, key=lambda item: (item["tier"], item["term"]))
    return matches


def field_flags(forms: list[FormInfo]) -> tuple[bool, bool]:
    has_password = False
    has_phone = False
    phone_pattern = re.compile(r"phone|mobile|tel|whatsapp|sms", re.I)
    for form in forms:
        for field in form.fields:
            joined = " ".join(
                part
                for part in [field.name, field.field_type, field.label, field.placeholder]
                if part
            )
            has_password = has_password or field.field_type == "password"
            has_phone = has_phone or bool(phone_pattern.search(joined))
    return has_password, has_phone
