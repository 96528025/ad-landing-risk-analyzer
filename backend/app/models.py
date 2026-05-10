from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class ScanRequest(BaseModel):
    url: HttpUrl
    dynamic: bool = Field(default=False, description="Run controlled browser automation.")
    use_llm: bool = Field(default=False, description="Use LLM semantic reasoning when OPENAI_API_KEY is configured.")
    cloaking: bool = Field(default=False, description="Run multi-environment cloaking detection.")


class LinkInfo(BaseModel):
    text: str
    href: str


class FormField(BaseModel):
    name: str | None = None
    field_type: str
    label: str | None = None
    placeholder: str | None = None


class FormInfo(BaseModel):
    action: str | None = None
    method: str
    fields: list[FormField]


class PageSignals(BaseModel):
    requested_url: str
    final_url: str
    title: str
    visible_text: str
    hidden_text: list[str]
    links: list[LinkInfo]
    redirect_chain: list[str]
    has_download_button: bool
    has_form: bool
    has_password_field: bool
    has_phone_field: bool
    has_forced_download: bool
    matched_risk_terms: list[str]
    risk_term_categories: dict[str, list[str]] = Field(default_factory=dict)
    risk_term_evidence: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    forms: list[FormInfo]
    screenshot_path: str | None = None
    automation_signals: list[str] = Field(default_factory=list)
    automation_steps: list[dict[str, Any]] = Field(default_factory=list)
    cloaking_analysis: dict[str, Any] | None = None


class RiskResult(BaseModel):
    score: int
    level: str
    reasons: list[str]
    signal_weights: dict[str, int]
    policy_labels: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    false_positive_notes: list[str] = Field(default_factory=list)
    llm_analysis: dict[str, Any] | None = None
    final_score: int | None = None
    final_level: str | None = None


class ScanResult(BaseModel):
    id: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    signals: PageSignals
    risk: RiskResult
