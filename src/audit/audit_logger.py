# src/audit/audit_logger.py
"""
Audit Logger
============
Appends an immutable record for every prediction made by the system.
This is separate from the alert log -- it captures ALL predictions,
not just HIGH/CRITICAL ones.

REGULATORY PURPOSE (DISHA / HIPAA):
  If a patient deteriorates and the hospital is audited, they must
  produce a complete prediction history showing:
    - What the AI predicted and when
    - Which model version made the prediction
    - What data was available (completeness score)
    - Whether a doctor review was required

FILE FORMAT: JSON-lines (one JSON object per line)
  - Append-only -- never modified after writing
  - Each line is a self-contained audit record
  - Easy to ship to a SIEM, database, or compliance store

THREAD SAFETY:
  Uses a threading.Lock so concurrent FastAPI requests
  never interleave partial writes.
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Append-only prediction audit trail.

    Usage:
        audit = AuditLogger()                      # default path
        audit.log(snapshot, source="api:/analyse") # call after every prediction
    """

    def __init__(
        self,
        log_path: Path | str = "logs/audit_trail.jsonl",
    ) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        logger.info("AuditLogger: writing to %s", self.log_path)

    def log(
        self,
        snapshot: Any,
        source: str = "unknown",
    ) -> dict[str, Any]:
        """
        Write one audit record for a completed prediction.

        Args:
            snapshot: PatientSnapshot from the clinical agent
            source:   Caller identifier e.g. "api:/analyse", "batch_job"

        Returns:
            The audit record dict (useful for testing).
        """
        record = self._build_record(snapshot, source)

        with self._lock:
            try:
                with self.log_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record) + "\n")
                logger.info(
                    "AUDIT | patient=%s | risk=%s | score=%.4f | source=%s",
                    record["patient_id"],
                    record["risk_level"],
                    record["risk_score"],
                    record["source"],
                )
            except OSError as e:
                # Log the failure but never crash the API over an audit write
                logger.error("AuditLogger write failed: %s", e)

        return record

    def _build_record(self, snapshot: Any, source: str) -> dict[str, Any]:
        """Extract fields from PatientSnapshot into a flat audit dict."""
        # Top driver names only -- no raw values (avoids PHI in audit log)
        explanations = getattr(snapshot, "top_drivers", [])
        top_driver_names = [
            getattr(e, "feature_name", str(e)) for e in explanations[:3]
        ]

        # NLP findings -- symptom names only, not full note text
        nlp = getattr(snapshot, "nlp_findings", None)
        nlp_summary = {}
        if nlp is not None:
            nlp_summary = {
                "symptoms": getattr(nlp, "symptoms", [])[:5],
                "diagnoses": getattr(nlp, "diagnoses", [])[:5],
                "negated": getattr(nlp, "negated_findings", [])[:3],
            }

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "patient_id": getattr(snapshot, "patient_id", "unknown"),
            "risk_level": getattr(snapshot, "risk_level", "UNKNOWN"),
            "risk_score": round(float(getattr(snapshot, "risk_score", 0.0)), 4),
            "model_version": getattr(snapshot, "model_version", "unknown"),
            "top_drivers": top_driver_names,
            "data_completeness": round(
                float(getattr(snapshot, "data_completeness", 0.0)), 4
            ),
            "hitl_required": bool(getattr(snapshot, "hitl_required", False)),
            "fusion_rules_fired": getattr(snapshot, "fusion_rules_fired", []),
            "nlp_summary": nlp_summary,
            "source": source,
        }

    def tail(self, n: int = 10) -> list[dict[str, Any]]:
        """
        Return the last N audit records.
        Useful for a /audit endpoint or debugging.
        """
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines[-n:] if line]
