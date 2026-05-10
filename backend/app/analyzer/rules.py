from __future__ import annotations

from urllib.parse import urlparse

from backend.app.models import PageSignals, RiskResult


SUSPICIOUS_TLDS = {
    ".click",
    ".country",
    ".download",
    ".gq",
    ".info",
    ".loan",
    ".pw",
    ".rest",
    ".ru",
    ".stream",
    ".tk",
    ".top",
    ".win",
    ".xyz",
    ".zip",
}

SUSPICIOUS_HOST_TOKENS = {
    "bonus",
    "claim",
    "freegift",
    "giveaway",
    "login-verify",
    "secure-update",
    "wallet",
}


def _is_suspicious_domain(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        return True
    return any(token in host for token in SUSPICIOUS_HOST_TOKENS)


def score_signals(signals: PageSignals) -> RiskResult:
    score = 0
    reasons: list[str] = []
    weights: dict[str, int] = {}
    policy_labels: list[str] = []
    findings: list[dict] = []
    false_positive_notes: list[str] = []

    def add(
        key: str,
        points: int,
        reason: str,
        label: str,
        evidence: list[str] | None = None,
        severity: str = "medium",
        confidence: float = 0.7,
    ) -> None:
        nonlocal score
        score += points
        weights[key] = points
        reasons.append(reason)
        if label not in policy_labels:
            policy_labels.append(label)
        findings.append(
            {
                "key": key,
                "policy_label": label,
                "severity": severity,
                "score_impact": points,
                "confidence": round(confidence, 2),
                "reason": reason,
                "evidence": evidence or [],
            }
        )

    def category_evidence(category: str) -> list[dict]:
        return signals.risk_term_evidence.get(category, [])

    def category_terms(category: str) -> list[str]:
        return [item["term"] for item in category_evidence(category)] or signals.risk_term_categories.get(category, [])

    def category_confidence(category: str) -> float:
        items = category_evidence(category)
        if not items:
            return 0.55 if signals.risk_term_categories.get(category) else 0.0
        return max(float(item.get("confidence", 0.5)) for item in items)

    def evidence_lines(category: str) -> list[str]:
        lines = []
        for item in category_evidence(category):
            context = item.get("context", "")
            line = f"{item['term']} ({item.get('tier', 'unknown')}, confidence {item.get('confidence', 0.0)}): {context}"
            lines.append(line)
        return lines or category_terms(category)

    if len(signals.redirect_chain) > 2:
        add(
            "multiple_redirects",
            20,
            "Multiple redirects detected",
            "Misleading Redirect Chain",
            evidence=signals.redirect_chain,
            severity="medium",
            confidence=0.85,
        )

    if signals.has_password_field:
        password_fields = []
        for form in signals.forms:
            for field in form.fields:
                if field.field_type == "password":
                    password_fields.append(field.name or field.placeholder or "password field")
        add(
            "password_field",
            25,
            "Page contains a password field",
            "Account Credential Collection",
            evidence=password_fields[:5],
            severity="high",
            confidence=0.9,
        )

    categories = signals.risk_term_categories
    if categories.get("financial_crypto"):
        confidence = category_confidence("financial_crypto")
        add(
            "financial_crypto_terms",
            20 if confidence >= 0.75 else 12,
            "Page contains financial or crypto wording",
            "Financial / Crypto Promotion",
            evidence=evidence_lines("financial_crypto"),
            severity="high" if confidence >= 0.75 else "medium",
            confidence=confidence,
        )

    if categories.get("earnings_claims"):
        confidence = category_confidence("earnings_claims")
        add(
            "earnings_claims",
            20 if confidence >= 0.75 else 12,
            "Page contains high-risk earning or return claims",
            "Deceptive Earnings Claim",
            evidence=evidence_lines("earnings_claims"),
            severity="high" if confidence >= 0.75 else "medium",
            confidence=confidence,
        )

    if categories.get("payment"):
        confidence = category_confidence("payment")
        add(
            "payment_terms",
            10 if confidence >= 0.75 else 6,
            "Page contains payment or billing wording",
            "Payment Collection",
            evidence=evidence_lines("payment"),
            severity="medium",
            confidence=confidence,
        )

    if categories.get("reward_pressure"):
        confidence = category_confidence("reward_pressure")
        has_supporting_risk = bool(
            categories.get("financial_crypto")
            or categories.get("earnings_claims")
            or signals.has_download_button
            or signals.has_forced_download
            or _is_suspicious_domain(signals.final_url)
        )
        if confidence >= 0.65 or has_supporting_risk:
            add(
                "reward_pressure_terms",
                10 if confidence >= 0.65 else 4,
                "Page contains reward or urgency wording",
                "Incentivized Claim",
                evidence=evidence_lines("reward_pressure"),
                severity="medium" if confidence >= 0.65 else "low",
                confidence=confidence,
            )
        else:
            false_positive_notes.append(
                "Weak reward terms such as bonus or claim were found, but not scored because no supporting scam, download, or suspicious-domain signal was present."
            )

    if categories.get("adult_sensitive"):
        confidence = category_confidence("adult_sensitive")
        add(
            "adult_sensitive_terms",
            15,
            "Page appears to contain adult or sensitive-content wording",
            "Adult / Sexual Content",
            evidence=evidence_lines("adult_sensitive"),
            severity="high" if confidence >= 0.85 else "medium",
            confidence=confidence,
        )

    if signals.hidden_text:
        add(
            "hidden_text",
            15,
            "Hidden text found in the page",
            "Hidden Content",
            evidence=[f"{len(signals.hidden_text)} hidden text block(s)"],
            severity="medium",
            confidence=0.7,
        )

    if _is_suspicious_domain(signals.final_url):
        host = urlparse(signals.final_url).hostname or signals.final_url
        add(
            "suspicious_domain",
            20,
            "Suspicious domain pattern detected",
            "Suspicious Domain",
            evidence=[host],
            severity="high",
            confidence=0.8,
        )

    if signals.has_forced_download or signals.has_download_button:
        evidence = ["content-disposition attachment"] if signals.has_forced_download else ["download call-to-action"]
        add(
            "download_behavior",
            30,
            "Download behavior or download call-to-action detected",
            "Forced or Risky Download",
            evidence=evidence,
            severity="high",
            confidence=0.9,
        )

    if signals.has_phone_field:
        phone_fields = []
        for form in signals.forms:
            for field in form.fields:
                joined = " ".join(part for part in [field.name, field.field_type, field.label, field.placeholder] if part)
                if any(token in joined.lower() for token in ["phone", "mobile", "tel", "whatsapp", "sms"]):
                    phone_fields.append(joined)
        add(
            "phone_collection",
            10,
            "Form asks for phone number",
            "Personal Data Collection",
            evidence=phone_fields[:5],
            severity="medium",
            confidence=0.75,
        )

    if signals.has_form and not signals.has_password_field and not signals.has_phone_field:
        add(
            "form_collection",
            5,
            "Page contains a user input form",
            "User Data Collection",
            evidence=[f"{len(signals.forms)} form(s) detected"],
            severity="low",
            confidence=0.55,
        )

    if "age_gate" in signals.automation_signals:
        add(
            "age_gate",
            10,
            "Dynamic flow encountered an age-restricted entry gate",
            "Age Gate / Restricted Content",
            evidence=["Automation stopped before clicking age-confirmation controls"],
            severity="medium",
            confidence=0.95,
        )

    if "login_wall" in signals.automation_signals:
        add(
            "login_wall",
            5,
            "Dynamic flow encountered a login wall",
            "Login Wall",
            evidence=["Login or account creation required during automated exploration"],
            severity="low",
            confidence=0.75,
        )

    if "cookie_consent" in signals.automation_signals:
        add(
            "cookie_consent",
            0,
            "Dynamic flow encountered a cookie consent prompt",
            "Cookie Consent",
            evidence=["Cookie or privacy preference prompt detected"],
            severity="low",
            confidence=0.7,
        )

    if categories.get("financial_crypto") and categories.get("earnings_claims"):
        add(
            "financial_earnings_combo",
            15,
            "Financial wording appears together with earning or return claims",
            "Financial Scam Pattern",
            evidence=category_terms("financial_crypto") + category_terms("earnings_claims"),
            severity="high",
            confidence=min(0.95, max(category_confidence("financial_crypto"), category_confidence("earnings_claims")) + 0.05),
        )

    if signals.has_password_field and (categories.get("adult_sensitive") or "age_gate" in signals.automation_signals):
        add(
            "restricted_content_credential_combo",
            10,
            "Restricted or sensitive content appears together with credential collection",
            "Sensitive Content Account Flow",
            evidence=["password field", *category_terms("adult_sensitive"), *signals.automation_signals],
            severity="medium",
            confidence=0.85,
        )

    if _is_suspicious_domain(signals.final_url) and (len(signals.redirect_chain) > 2 or signals.has_download_button):
        add(
            "suspicious_domain_flow_combo",
            10,
            "Suspicious domain appears together with redirect or download behavior",
            "Suspicious Downstream Flow",
            evidence=[signals.final_url],
            severity="high",
            confidence=0.85,
        )

    if signals.has_password_field:
        false_positive_notes.append("Password fields can be legitimate login flows; review form context before treating this as phishing.")
    if categories.get("payment") and not (categories.get("financial_crypto") or signals.has_forced_download):
        false_positive_notes.append("Payment wording may appear in terms, subscription pages, or ads and is lower confidence without checkout evidence.")
    if categories.get("adult_sensitive") and "age_gate" in signals.automation_signals:
        false_positive_notes.append("Adult content plus an age gate is policy-relevant, but the age gate itself can be a compliance signal rather than deception.")
    if signals.hidden_text and len(signals.hidden_text) <= 2:
        false_positive_notes.append("Small amounts of hidden text can come from accessibility labels, modals, or responsive UI.")

    capped_score = min(score, 100)
    if capped_score >= 70:
        level = "High"
    elif capped_score >= 40:
        level = "Medium"
    else:
        level = "Low"

    if not reasons:
        reasons.append("No major risk signals detected by baseline rules")

    if findings:
        confidence = round(sum(float(item.get("confidence", 0.0)) for item in findings) / len(findings), 2)
    else:
        confidence = 0.2

    return RiskResult(
        score=capped_score,
        level=level,
        reasons=reasons,
        signal_weights=weights,
        policy_labels=policy_labels,
        findings=findings,
        confidence=confidence,
        false_positive_notes=false_positive_notes,
    )
