from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    """Append-only JSONL audit trail for regulatory compliance (DISHA / HIPAA)."""

    def __init__(self, path: str = "logs/audit_trail.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, snapshot, source: str = "unknown") -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "patient_id": getattr(snapshot, "patient_id", "unknown"),
            "risk_level": getattr(snapshot, "risk_level", "unknown"),
            "risk_score": round(float(getattr(snapshot, "risk_score", 0.0)), 4),
            "hitl_required": getattr(snapshot, "hitl_required", False),
            "model_version": getattr(snapshot, "model_version", "unknown"),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def tail(self, n: int = 20) -> list[dict]:
        """Return the last n audit records, newest first."""
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        recent = lines[-n:] if len(lines) >= n else lines
        records = []
        for line in reversed(recent):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return records
