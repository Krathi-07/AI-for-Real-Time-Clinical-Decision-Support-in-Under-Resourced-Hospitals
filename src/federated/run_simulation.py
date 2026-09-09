# src/federated/run_simulation.py
"""
Federated Learning Simulation
==============================
Simulates 3 hospitals training a shared sepsis model without sharing
patient data.  Uses Flower's in-process simulation — no real network needed.

Run with:
    uv run python -m src.federated.run_simulation

What you will see:
  - Round 1: Each hospital trains on its local synthetic data, sends weights
  - Round 2: Global model improves as more hospitals contribute
  - Round 3: Weighted AUC reported per hospital and globally

In production, replace this file with:
  - A deployed fl_server.py on a central coordinator machine
  - One fl_client.py process per hospital, pointed at real MIMIC-IV data
"""

from __future__ import annotations

import logging

import flwr as fl

from src.federated.fl_client import get_client_fn
from src.federated.fl_server import build_strategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hospital configuration
# ---------------------------------------------------------------------------
# Each dict represents one hospital in the federation.
# seed differentiates their synthetic data — simulates real-world
# data heterogeneity (non-IID data across hospitals).
#
# TODO: replace seeds with real MIMIC-IV hospital/site IDs when available.

HOSPITAL_CONFIGS = [
    {"id": "hospital_pune",       "seed": 42},
    {"id": "hospital_nagpur",     "seed": 77},
    {"id": "hospital_coimbatore", "seed": 123},
]

NUM_ROUNDS = 3   # FL aggregation rounds (use 10-50 for real convergence)


# ---------------------------------------------------------------------------
# Simulation entry point
# ---------------------------------------------------------------------------

def run() -> None:
    logger.info("=" * 60)
    logger.info("Federated Learning Simulation — Sepsis Early Warning")
    logger.info("Hospitals : %s", [h["id"] for h in HOSPITAL_CONFIGS])
    logger.info("FL Rounds : %d", NUM_ROUNDS)
    logger.info("=" * 60)

    # Build the client factory — Flower calls this to create each hospital client
    client_fn = get_client_fn(HOSPITAL_CONFIGS)

    # Build the aggregation strategy (FedAvg)
    strategy = build_strategy(min_clients=len(HOSPITAL_CONFIGS))

    # Run the simulation — all clients + server in one process
    history = fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=len(HOSPITAL_CONFIGS),
        config=fl.server.ServerConfig(num_rounds=NUM_ROUNDS),
        strategy=strategy,
    )

    # ------------------------------------------------------------------
    # Results summary
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Simulation complete.")

    if history.metrics_distributed:
        logger.info("Per-round distributed metrics:")
        for round_num, metrics in history.metrics_distributed.items():
            logger.info("  Round %s: %s", round_num, metrics)
    else:
        logger.info("(No distributed metrics recorded — evaluate() not triggered)")

    if history.losses_distributed:
        logger.info("Per-round losses:")
        for round_num, loss in history.losses_distributed:
            logger.info("  Round %s: loss=%.4f", round_num, loss)

    logger.info("=" * 60)
    logger.info("FL stub complete. Next steps:")
    logger.info("  1. Replace _load_local_data() with real MIMIC-IV loader")
    logger.info("  2. Swap FedAvg for FedXgbBagging in fl_server.py")
    logger.info("  3. Deploy fl_server.py to a coordinator machine")
    logger.info("  4. Deploy fl_client.py to each hospital")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
    