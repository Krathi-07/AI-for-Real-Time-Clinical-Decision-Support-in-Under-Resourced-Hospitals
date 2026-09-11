from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertChannel(ABC):
    """Base class for all alert delivery channels."""

    @abstractmethod
    def send(self, alert: dict) -> None:
        ...


class FileAlertChannel(AlertChannel):
    """Writes alerts to a JSONL file — default channel for compliance logging."""

    def __init__(self, path: str = "logs/clinical_alerts.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, alert: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(alert) + "\n")
        logger.warning(
            "ALERT [%s] Patient %s — %s risk (%.1f%%)",
            alert["channel"],
            alert["patient_id"],
            alert["risk_level"],
            alert["risk_score"] * 100,
        )


class AlertManager:
    """Processes a PatientSnapshot and fans out to all registered channels."""

    ALERT_LEVELS = {"HIGH", "CRITICAL"}

    def __init__(self):
        self._channels: list[AlertChannel] = []

    def add_channel(self, channel: AlertChannel) -> None:
        self._channels.append(channel)

    def process(self, snapshot) -> None:
        risk_level = getattr(snapshot, "risk_level", "LOW")
        if risk_level not in self.ALERT_LEVELS:
            return

        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": type(self._channels[0]).__name__ if self._channels else "none",
            "patient_id": getattr(snapshot, "patient_id", "unknown"),
            "risk_level": risk_level,
            "risk_score": round(float(getattr(snapshot, "risk_score", 0.0)), 4),
            "hitl_required": getattr(snapshot, "hitl_required", False),
        }

        for channel in self._channels:
            try:
                channel.send(alert)
            except Exception as e:
                logger.error("Alert channel %s failed: %s", type(channel).__name__, e)
