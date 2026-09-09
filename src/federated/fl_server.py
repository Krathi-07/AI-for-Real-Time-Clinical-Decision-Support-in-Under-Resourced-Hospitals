# src/federated/fl_server.py
"""
Federated Learning Server — Central Coordinator
================================================
This server aggregates model updates from all participating hospitals.
It NEVER receives patient data — only serialised model weights.

AGGREGATION STRATEGY NOTE:
  FedAvg (the standard FL algorithm) averages numpy weight arrays.
  This works perfectly for neural networks (weights are real-valued vectors).

  For XGBoost (tree ensembles), two practical approaches exist:
    1. FedXgbBagging  — Flower's native XGBoost strategy. Each client sends
                        its booster trees; the server combines them into one
                        ensemble. This is what a real deployment should use.
    2. FedAvg on JSON — Serialise model config to bytes, transmit, reconstruct
                        locally. Clients effectively train independently and
                        share hyperparameter state only. Simpler to implement.

  THIS STUB uses FedAvg (approach 2) so the wiring is clear and visible.
  The TODO below shows exactly where to swap in FedXgbBagging.

REGULATORY NOTE:
  Under DISHA / HIPAA, the server must:
    - Log every aggregation event with a timestamp and participant list
    - Never store any client-side data that could be re-identified
    - Maintain a model version registry for audit purposes
  The audit_log list below is the stub for that requirement.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import flwr as fl
from flwr.common import Metrics
from flwr.server import ServerConfig
from flwr.server.strategy import FedAvg

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Audit log (stub)
# ---------------------------------------------------------------------------
# In production this writes to an append-only database table or WORM storage.
# Every aggregation event must be recorded for DISHA compliance.
# TODO: replace list with a real audit trail writer.

audit_log: list[dict] = []


def _record_audit_event(round_num: int, participants: list[str], metrics: dict) -> None:
    """Append one aggregation event to the audit log."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "round": round_num,
        "participants": participants,
        "metrics": metrics,
    }
    audit_log.append(event)
    logger.info("AUDIT | round=%d | participants=%s", round_num, participants)


# ---------------------------------------------------------------------------
# Custom metric aggregation
# ---------------------------------------------------------------------------

def weighted_average_metrics(metrics: list[tuple[int, Metrics]]) -> Metrics:
    """
    Aggregate per-hospital evaluation metrics into one global metric.

    Flower calls this after each evaluation round with:
        metrics = [(num_samples_hospital_A, {auc: 0.92, ...}),
                   (num_samples_hospital_B, {auc: 0.88, ...}), ...]

    We compute a sample-weighted average AUC so larger hospitals
    contribute proportionally more to the global metric.
    """
    total_samples = sum(n for n, _ in metrics)

    # Weighted AUC
    weighted_auc = sum(
        n * m.get("auc", 0.0) for n, m in metrics
    ) / total_samples

    # Collect participant hospital IDs for audit
    participants = [str(m.get("hospital", f"client_{i}")) for i, (_, m) in enumerate(metrics)]
    round_metrics = {"weighted_auc": weighted_auc, "total_samples": total_samples}

    # We don't have round number here — server strategy callback has it.
    # Log a lightweight event; the strategy on_fit_config populates round.
    logger.info(
        "Aggregated metrics | weighted_auc=%.4f | hospitals=%s",
        weighted_auc,
        participants,
    )
    return round_metrics


# ---------------------------------------------------------------------------
# FL Strategy
# ---------------------------------------------------------------------------

def build_strategy(min_clients: int = 2) -> FedAvg:
    """
    Build the FedAvg aggregation strategy.

    Args:
        min_clients: Minimum hospitals that must participate for a round
                     to proceed.  Set to 2 so the server waits for at
                     least 2 hospitals — prevents single-hospital rounds
                     from dominating the global model.

    TODO: swap FedAvg for FedXgbBagging for production XGBoost FL:
        from flwr.server.strategy import FedXgbBagging
        return FedXgbBagging(
            fraction_fit=1.0,
            min_fit_clients=min_clients,
            min_available_clients=min_clients,
            evaluate_metrics_aggregation_fn=weighted_average_metrics,
        )
    """
    return FedAvg(
        # fraction_fit=1.0 means: use ALL available clients each round
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
        # Called before each fit round — inject round number into client config
        on_fit_config_fn=_fit_config,
        # Called before each evaluate round
        on_evaluate_config_fn=_evaluate_config,
        # Aggregate evaluation metrics across hospitals
        evaluate_metrics_aggregation_fn=weighted_average_metrics,
    )


def _fit_config(server_round: int) -> dict[str, Any]:
    """
    Config dict sent to every client before fit().
    Clients receive this as the `config` argument in fit().
    """
    config = {
        "current_round": server_round,
        "local_epochs": 1,   # how many local training passes per round
    }
    logger.info("Sending fit config for round %d: %s", server_round, config)
    _record_audit_event(
        round_num=server_round,
        participants=["all_available"],   # real list available post-aggregation
        metrics={"phase": "fit_config"},
    )
    return config


def _evaluate_config(server_round: int) -> dict[str, Any]:
    """Config dict sent to every client before evaluate()."""
    return {"current_round": server_round}


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def start_fl_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    num_rounds: int = 3,
    min_clients: int = 2,
) -> None:
    """
    Start the Flower FL server.

    In production:
      - Each hospital's client connects over a secure gRPC channel (TLS)
      - The server address is a load-balanced endpoint
      - num_rounds is typically 10–50 for convergence

    For local simulation, run_simulation.py calls fl.simulation.start_simulation()
    instead of this function — no real network needed.

    Args:
        host:        Network interface to bind to
        port:        gRPC port (default 8080)
        num_rounds:  Number of FL aggregation rounds
        min_clients: Minimum hospitals required per round
    """
    server_address = f"{host}:{port}"
    logger.info(
        "Starting FL server at %s | rounds=%d | min_clients=%d",
        server_address,
        num_rounds,
        min_clients,
    )

    fl.server.start_server(
        server_address=server_address,
        config=ServerConfig(num_rounds=num_rounds),
        strategy=build_strategy(min_clients=min_clients),
    )

    # Print audit summary after all rounds complete
    logger.info("FL training complete. Audit log has %d events.", len(audit_log))
    for event in audit_log:
        logger.info("  %s", event)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_fl_server(num_rounds=3, min_clients=1)
    