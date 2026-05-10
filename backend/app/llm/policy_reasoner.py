from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.models import PageSignals, RiskResult


class LLMPolicyReasoning(BaseModel):
    status: Literal["completed", "skipped", "error"] = "completed"
    page_intent: str = Field(description="Short semantic classification of the landing page intent.")
    policy_labels: list[str] = Field(description="Policy labels inferred from semantic context.")
    llm_risk_score: int = Field(ge=0, le=100, description="Semantic risk score from 0 to 100.")
    confidence: float = Field(ge=0, le=1, description="LLM confidence from 0 to 1.")
    reviewer_summary: str = Field(description="Concise summary for a human reviewer.")
    false_positive_assessment: list[str] = Field(description="Likely false positives or weak rule matches.")
    supporting_evidence: list[str] = Field(description="Short evidence points grounded in provided signals.")
    visual_observations: list[str] = Field(
        default_factory=list,
        description="Visual observations from screenshot evidence, including visible text, buttons, warnings, or risk cues.",
    )


def _level(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _summarize_for_llm(signals: PageSignals, risk: RiskResult) -> dict:
    return {
        "requested_url": signals.requested_url,
        "final_url": signals.final_url,
        "title": signals.title,
        "visible_text_excerpt": signals.visible_text[:6000],
        "redirect_chain": signals.redirect_chain[:10],
        "forms": [form.model_dump() for form in signals.forms[:10]],
        "links_sample": [link.model_dump() for link in signals.links[:30]],
        "risk_term_evidence": signals.risk_term_evidence,
        "hidden_text_count": len(signals.hidden_text),
        "has_download_button": signals.has_download_button,
        "has_forced_download": signals.has_forced_download,
        "has_password_field": signals.has_password_field,
        "has_phone_field": signals.has_phone_field,
        "automation_signals": signals.automation_signals,
        "automation_steps": [
            {
                "label": step.get("label"),
                "url": step.get("url"),
                "clicked": step.get("clicked"),
                "action_reason": step.get("action_reason"),
                "detected_signals": step.get("detected_signals", []),
                "blocked_reason": step.get("blocked_reason"),
            }
            for step in signals.automation_steps[:8]
        ],
        "rule_score": risk.score,
        "rule_level": risk.level,
        "rule_policy_labels": risk.policy_labels,
        "rule_findings": risk.findings,
        "rule_false_positive_notes": risk.false_positive_notes,
        "screenshot_available": bool(signals.screenshot_path),
    }


def _skipped(reason: str) -> LLMPolicyReasoning:
    return LLMPolicyReasoning(
        status="skipped",
        page_intent="not_evaluated",
        policy_labels=[],
        llm_risk_score=0,
        confidence=0,
        reviewer_summary=reason,
        false_positive_assessment=[reason],
        supporting_evidence=[],
        visual_observations=[],
    )


def _image_data_url(path: str | None) -> str | None:
    if not path:
        return None
    image_path = Path(path)
    if not image_path.exists() or not image_path.is_file():
        return None
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def reason_about_policy(signals: PageSignals, risk: RiskResult) -> LLMPolicyReasoning:
    if not os.getenv("OPENAI_API_KEY"):
        return _skipped("OPENAI_API_KEY is not configured; LLM reasoning was skipped.")

    try:
        from openai import OpenAI
    except ImportError:
        return _skipped("openai package is not installed; run pip install -r requirements.txt.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI()
    payload = _summarize_for_llm(signals, risk)
    system_prompt = (
        "You are an ad landing-page risk reviewer. Judge semantic page intent and policy risk "
        "from the provided structured crawler signals. Distinguish true risk from weak keyword "
        "matches. Do not browse the web. Do not rely on brand reputation, domain familiarity, "
        "or prior knowledge about the website. Treat the URL as an unknown landing page and ground "
        "every conclusion only in the provided title, text excerpts, forms, redirects, automation "
        "steps, and rule findings. Do not infer account creation from a password field unless the "
        "provided form fields, button text, or page text explicitly says sign up, register, create "
        "account, or equivalent wording. Otherwise describe it as account access or credential "
        "collection. Return concise reviewer-facing output."
    )
    user_prompt = (
        "Review this landing-page scan. Identify page intent, semantic policy labels, likely "
        "false positives, supporting evidence, and a calibrated LLM risk score.\n\n"
        "If a screenshot is provided, inspect it for visible text, warnings, buttons, forms, "
        "image-only claims, canvas-rendered content, or other visual risk evidence that may not "
        "appear in DOM text. Keep visual observations grounded in what is visible.\n\n"
        f"SCAN_JSON:\n{payload}"
    )
    content: list[dict] = [{"type": "input_text", "text": user_prompt}]
    image_url = _image_data_url(signals.screenshot_path)
    if image_url:
        content.append({"type": "input_image", "image_url": image_url, "detail": "low"})

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            text_format=LLMPolicyReasoning,
        )
        parsed = response.output_parsed
        parsed.status = "completed"
        return parsed
    except Exception as exc:
        return LLMPolicyReasoning(
            status="error",
            page_intent="llm_error",
            policy_labels=[],
            llm_risk_score=risk.score,
            confidence=0,
            reviewer_summary=f"LLM reasoning failed: {exc}",
            false_positive_assessment=[f"LLM reasoning failed: {exc}"],
            supporting_evidence=[],
        )


def merge_rule_and_llm(risk: RiskResult, llm: LLMPolicyReasoning) -> RiskResult:
    risk.llm_analysis = llm.model_dump()
    if llm.status != "completed":
        risk.final_score = risk.score
        risk.final_level = risk.level
        return risk

    allowed_labels = _allowed_llm_labels(risk)
    accepted_labels = [label for label in llm.policy_labels if label in allowed_labels]
    rejected_labels = [label for label in llm.policy_labels if label not in allowed_labels]
    risk.llm_analysis["accepted_policy_labels"] = accepted_labels
    risk.llm_analysis["rejected_policy_labels"] = rejected_labels

    blended = round((0.6 * risk.score) + (0.4 * llm.llm_risk_score))
    if llm.confidence < 0.45:
        blended = round((0.8 * risk.score) + (0.2 * llm.llm_risk_score))

    risk.final_score = max(0, min(100, blended))
    risk.final_level = _level(risk.final_score)
    for label in accepted_labels:
        if label not in risk.policy_labels:
            risk.policy_labels.append(label)
    for label in rejected_labels:
        note = f"LLM suggested '{label}', but it was not added because no supporting rule evidence was present."
        if note not in risk.false_positive_notes:
            risk.false_positive_notes.append(note)
    if llm.false_positive_assessment:
        risk.false_positive_notes.extend(
            note for note in llm.false_positive_assessment if note not in risk.false_positive_notes
        )
    return risk


def _allowed_llm_labels(risk: RiskResult) -> set[str]:
    allowed = set(risk.policy_labels)
    finding_keys = {finding.get("key") for finding in risk.findings}

    if "password_field" in finding_keys:
        allowed.add("Account Credential Collection")
    if "phone_collection" in finding_keys:
        allowed.add("Personal Data Collection")
    if "form_collection" in finding_keys:
        allowed.add("User Data Collection")
    if "payment_terms" in finding_keys:
        allowed.add("Payment Collection")
    if "financial_crypto_terms" in finding_keys:
        allowed.add("Financial / Crypto Promotion")
    if "earnings_claims" in finding_keys:
        allowed.add("Deceptive Earnings Claim")
    if "financial_earnings_combo" in finding_keys:
        allowed.add("Financial Scam Pattern")
    if "adult_sensitive_terms" in finding_keys:
        allowed.add("Adult / Sexual Content")
    if "hidden_text" in finding_keys:
        allowed.add("Hidden Content")
    if "age_gate" in finding_keys:
        allowed.add("Age Gate / Restricted Content")
    if "login_wall" in finding_keys:
        allowed.add("Login Wall")
    if "cookie_consent" in finding_keys:
        allowed.add("Cookie Consent")
    if "restricted_content_credential_combo" in finding_keys:
        allowed.add("Sensitive Content Account Flow")
    if "download_behavior" in finding_keys:
        allowed.add("Forced or Risky Download")
    if "multiple_redirects" in finding_keys:
        allowed.add("Misleading Redirect Chain")
    if "suspicious_domain" in finding_keys:
        allowed.add("Suspicious Domain")
    if "suspicious_domain_flow_combo" in finding_keys:
        allowed.add("Suspicious Downstream Flow")

    return allowed
