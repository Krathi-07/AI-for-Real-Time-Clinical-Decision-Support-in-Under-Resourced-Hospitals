# src/alerts/alert_manager.py
"""
Clinical Alert System
=====================
Receives a PatientSnapshot from the clinical engine and dispatches
real-time alerts to configured channels when risk is HIGH or CRITICAL.

ARCHITECTURE:
  AlertManager
    |- FileAlertChannel     -- structured JSON log (always on, auditable)
    +- WebhookAlertChannel  -- HTTP POST to Slack / PagerDuty / hospital system

ALERT RULES:
  CRITICAL -> fire immediately on all channels
  HIGH     -> fire with 5-minute deduplication per patient
  MODERATE -> log only, no active alert
  LOW      -> silent

REGULATORY NOTE (DISHA / HIPAA):
  All alerts are logged with timestamp, patient ID, risk level, and
  model version. The file channel writes to an append-only JSON-lines
  file -- one JSON object per line -- easy to ship to a SIEM or audit store.
  Patient names are never included -- only de-identified patient_id.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ClinicalAlert:
    """One fired alert -- de-identified, minimal, actionable."""
    patient_id: str
    risk_level: str
    risk_score: float
    alert_text: str
    top_drivers: list[str]
    hitl_required: bool
    model_version: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "patient_id": self.patient_id,
            "risk_level": self.risk_level,
            "risk_score": round(self.risk_score, 4),
            "alert_text": self.alert_text,
            "top_drivers": self.top_drivers,
            "hitl_required": self.hitl_required,
            "model_version": self.model_version,
        }


class BaseAlertChannel(ABC):
    """Interface all alert channels must implement."""

    @abstractmethod
    def send(self, alert: ClinicalAlert) -> bool:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class FileAlertChannel(BaseAlertChannel):
    """
    Appends every alert to a JSON-lines file.
    One JSON object per line -- the audit trail required by DISHA / HIPAA.
    """

    def __init__(self, log_path: Path | str = "logs/clinical_alerts.jsonl") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return f"FileChannel({self.log_path})"

    def send(self, alert: ClinicalAlert) -> bool:
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict()) + "\n")
            logger.info(
                "ALERT LOGGED | patient=%s | risk=%s | file=%s",
                alert.patient_id, alert.risk_level, self.log_path,
            )
            return True
        except OSError as e:
            logger.error("FileAlertChannel failed: %s", e)
            return False


class WebhookAlertChannel(BaseAlertChannel):
    """
    POSTs alert JSON to any HTTP endpoint.
    Works with Slack, PagerDuty, or any hospital integration engine.
    In production set webhook_url from an environment variable.
    """

    def __init__(self, webhook_url: str, timeout_seconds: int = 5) -> None:
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return f"WebhookChannel({self.webhook_url[:40]}...)"

    def send(self, alert: ClinicalAlert) -> bool:
        try:
            import urllib.request
            payload = json.dumps(alert.to_dict()).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                status = resp.status
            logger.info(
                "ALERT WEBHOOK | patient=%s | risk=%s | http_status=%d",
                alert.patient_id, alert.risk_level, status,
            )
            return status < 300
        except Exception as e:  # noqa: BLE001
            logger.warning("WebhookAlertChannel failed (non-fatal): %s", e)
            return False


ALERT_THRESHOLD = {"CRITICAL", "HIGH"}
DEDUP_WINDOW_SECONDS = 300  # 5 minutes -- suppress repeated HIGH alerts


class AlertManager:
    """
    Central alert dispatcher.

    Usage:
        manager = AlertManager()
        manager.add_channel(FileAlertChannel())
        manager.process(patient_snapshot)
    """

    def __init__(self) -> None:
        self._channels: list[BaseAlertChannel] = []
        self._last_alerted: dict[str, float] = {}

    def add_channel(self, channel: BaseAlertChannel) -> None:
        self._channels.append(channel)
        logger.info("AlertManager: registered channel %s", channel.name)

    def process(self, snapshot: Any) -> ClinicalAlert | None:
        """Evaluate a PatientSnapshot and fire alerts if warranted."""
        risk_level = getattr(snapshot, "risk_level", "LOW")
        risk_score = getattr(snapshot, "risk_score", 0.0)
        patient_id = getattr(snapshot, "patient_id", "unknown")
        alert_text = getattr(snapshot, "alert_text", "")
        model_version = getattr(snapshot, "model_version", "unknown")
        hitl_required = getattr(snapshot, "hitl_required", False)

        explanations = getattr(snapshot, "top_drivers", [])
        top_driver_names = [
            getattr(e, "feature_name", str(e)) for e in explanations[:3]
        ]

        if risk_level not in ALERT_THRESHOLD:
            logger.debug("AlertManager: risk=%s below threshold, no alert", risk_level)
            return None

        now = time.time()
        last = self._last_alerted.get(patient_id, 0.0)
        if risk_level == "HIGH" and (now - last) < DEDUP_WINDOW_SECONDS:
            logger.info(
                "AlertManager: dedup suppressed HIGH alert for patient %s "
                "(last alert %.0fs ago)", patient_id, now - last,
            )
            return None

        alert = ClinicalAlert(
            patient_id=patient_id,
            risk_level=risk_level,
            risk_score=risk_score,
            alert_text=alert_text,
            top_drivers=top_driver_names,
            hitl_required=hitl_required,
            model_version=model_version,
        )

        self._last_alerted[patient_id] = now
        self._dispatch(alert)
        return alert

    def _dispatch(self, alert: ClinicalAlert) -> None:
        """Send to every channel. Failures are non-fatal."""
        if not self._channels:
            logger.warning(
                "AlertManager: no channels registered | patient=%s risk=%s",
                alert.patient_id, alert.risk_level,
            )
            return

        for channel in self._channels:
            try:
                success = channel.send(alert)
                if not success:
                    logger.warning(
                        "Channel %s returned failure for patient %s",
                        channel.name, alert.patient_id,
                    )
            except Exception as e:  # noqa: BLE001
                logger.error("Channel %s raised unexpectedly: %s", channel.name, e)
