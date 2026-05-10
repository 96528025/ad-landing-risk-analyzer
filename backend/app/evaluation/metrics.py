from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

from backend.app.db.database import get_scan, list_scans
from backend.app.models import ScanResult


DEFAULT_RISK_THRESHOLD = 40


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip().lower())
    host = parsed.netloc.removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def load_labels(path: str | Path) -> dict[str, dict]:
    labels: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            url = row.get("url", "")
            if not url:
                continue
            labels[_normalize_url(url)] = {
                "is_risky": str(row.get("is_risky", "")).strip().lower() in {"1", "true", "yes", "y"},
                "policy_labels": [
                    label.strip()
                    for label in str(row.get("policy_labels", "")).split("|")
                    if label.strip()
                ],
                "reviewer": row.get("reviewer", ""),
                "notes": row.get("notes", ""),
            }
    return labels


def _prediction(result: ScanResult, threshold: int) -> bool:
    return result.risk.score >= threshold


def _latest_scan_results(limit: int = 500) -> list[ScanResult]:
    results: list[ScanResult] = []
    for row in list_scans(limit=limit):
        scan = get_scan(int(row["id"]))
        if scan:
            results.append(scan)
    return results


def compute_metrics(label_path: str | Path, threshold: int = DEFAULT_RISK_THRESHOLD) -> dict:
    labels = load_labels(label_path)
    scans = _latest_scan_results()

    matched: list[tuple[ScanResult, dict]] = []
    for scan in scans:
        keys = {
            _normalize_url(scan.signals.requested_url),
            _normalize_url(scan.signals.final_url),
        }
        label = next((labels[key] for key in keys if key in labels), None)
        if label is not None:
            matched.append((scan, label))

    tp = fp = tn = fn = 0
    label_agreements = 0
    label_comparable = 0
    risk_discoveries = 0
    downstream_depths: list[int] = []
    rows: list[dict] = []

    for scan, label in matched:
        predicted = _prediction(scan, threshold)
        actual = bool(label["is_risky"])
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and not actual:
            tn += 1
        else:
            fn += 1

        predicted_labels = set(scan.risk.policy_labels)
        actual_labels = set(label["policy_labels"])
        if actual_labels:
            label_comparable += 1
            if predicted_labels & actual_labels:
                label_agreements += 1

        dynamic_findings = [
            finding
            for finding in scan.risk.findings
            if finding["key"] in {"age_gate", "login_wall", "cookie_consent"}
        ]
        if scan.signals.automation_steps and (dynamic_findings or len(scan.signals.automation_steps) > 1):
            risk_discoveries += 1
        downstream_depths.append(max(0, len(scan.signals.automation_steps) - 1))

        rows.append(
            {
                "id": scan.id,
                "url": scan.signals.requested_url,
                "score": scan.risk.score,
                "predicted_risky": predicted,
                "actual_risky": actual,
                "risk_level": scan.risk.level,
                "policy_labels": ", ".join(scan.risk.policy_labels),
                "manual_labels": ", ".join(label["policy_labels"]),
                "downstream_depth": max(0, len(scan.signals.automation_steps) - 1),
            }
        )

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    false_positive_rate = fp / (fp + tn) if fp + tn else 0.0
    manual_review_agreement = label_agreements / label_comparable if label_comparable else 0.0
    risk_discovery_rate = risk_discoveries / len(matched) if matched else 0.0
    average_downstream_depth = sum(downstream_depths) / len(downstream_depths) if downstream_depths else 0.0

    return {
        "threshold": threshold,
        "labeled_urls": len(labels),
        "matched_scans": len(matched),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": precision,
        "recall": recall,
        "false_positive_rate": false_positive_rate,
        "manual_review_agreement": manual_review_agreement,
        "risk_discovery_rate": risk_discovery_rate,
        "average_downstream_depth": average_downstream_depth,
        "rows": rows,
    }
