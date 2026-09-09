# src/federated/fl_client.py
"""
Federated Learning Client -- Hospital Node
==========================================
Each participating hospital runs one instance of this client.
It wraps our XGBoost sepsis model and speaks the Flower FL protocol.

HOW FL WORKS (one round):
  1. Server sends global model weights to this client
  2. Client calls fit() -- loads weights, trains locally, returns updated weights
  3. Server aggregates weights from all clients (FedAvg)
  4. Repeat for N rounds

REAL ATTRIBUTE NAMES on EarlyWarningSepsis:
  _xgb         -- the XGBoost classifier (CalibratedClassifierCV)
  _is_trained  -- bool flag, True after train_on_synthetic_data() or train_on_real_data()
  _val_auc     -- validation AUC after training
"""

from __future__ import annotations

import logging
from typing import Any

import flwr as fl
import numpy as np
from flwr.common import Scalar

from src.models.early_warning import EarlyWarningSepsis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Weight serialisation helpers
# ---------------------------------------------------------------------------
# XGBoost tree models cannot be averaged like neural network weights.
# We serialise the model to JSON bytes and treat it as one opaque blob.
# FedAvg on the server side will handle aggregation via a custom strategy.
# For a production deployment, swap to FedXgbBagging (see fl_server.py).

def model_to_ndarrays(model: EarlyWarningSepsis) -> list[np.ndarray]:
    """Serialise EarlyWarningSepsis to a list of numpy arrays for Flower."""
    import json
    # Access the underlying XGBoost booster via _xgb (CalibratedClassifierCV)
    # _xgb.estimator is the raw XGBClassifier; get_booster() returns the Booster
    try:
        booster = model._xgb.estimator.get_booster()
        config_str = booster.save_config()
    except (AttributeError, RuntimeError):
        # Fallback: return a dummy byte array so Flower can initialise
        config_str = json.dumps({"stub": True})
    byte_array = np.frombuffer(config_str.encode("utf-8"), dtype=np.uint8)
    return [byte_array]


def ndarrays_to_model(ndarrays: list[np.ndarray]) -> EarlyWarningSepsis:
    """Deserialise Flower numpy arrays back into an EarlyWarningSepsis instance."""
    # Stub: reconstruct a locally-trained model.
    # TODO: replace with real weight loading when MIMIC-IV is available.
    instance = EarlyWarningSepsis()
    instance.train_on_synthetic_data()
    logger.info("ndarrays_to_model: returning synthetic base model (stub)")
    return instance


# ---------------------------------------------------------------------------
# Flower Client
# ---------------------------------------------------------------------------

class SepsisFlowerClient(fl.client.NumPyClient):
    """
    A Flower NumPyClient that wraps our XGBoost sepsis early-warning model.

    In production each hospital deploys one of these, pointed at its own
    local patient database.  In the simulation, we instantiate three of
    these on one machine with different synthetic data slices.
    """

    def __init__(self, hospital_id: str, data_slice_seed: int = 42) -> None:
        self.hospital_id = hospital_id
        self.data_slice_seed = data_slice_seed
        self.model = EarlyWarningSepsis()

        # ----------------------------------------------------------------
        # LOCAL DATA LOADING
        # STUB: generate synthetic data seeded per hospital.
        # TODO: replace with real MIMIC-IV loader:
        #   X_train, y_train = load_mimic_for_hospital(hospital_id)
        # ----------------------------------------------------------------
        self.X_train, self.y_train = self._load_local_data()
        logger.info(
            "Hospital %s: loaded %d training samples",
            hospital_id,
            len(self.y_train),
        )

    def _load_local_data(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns local training data for this hospital.
        Each hospital gets a different seed so their data differs slightly
        -- this simulates real-world non-IID data across hospitals.
        Replace with a real MIMIC-IV loader when available.
        """
        rng = np.random.default_rng(self.data_slice_seed)
        n_per_class = 500

        X_healthy = rng.normal(
            loc=[80, 70, 16, 37.0, 98, -1, 7.5, 1.0, 8.0, 1.0, 13.5, -1],
            scale=[10, 8, 2, 0.4, 1.5, 0.5, 0.8, 0.2, 2.0, 0.2, 1.5, 0.3],
            size=(n_per_class, 12),
        )
        y_healthy = np.zeros(n_per_class)

        X_septic = rng.normal(
            loc=[118, 45, 24, 38.9, 94, 3.8, 6.5, 2.8, 14.0, 0.7, 10.5, -1],
            scale=[15, 10, 4, 0.8, 3.0, 1.5, 0.9, 0.6, 3.5, 0.2, 2.0, 0.3],
            size=(n_per_class, 12),
        )
        y_septic = np.ones(n_per_class)

        X = np.vstack([X_healthy, X_septic])
        y = np.concatenate([y_healthy, y_septic])
        idx = rng.permutation(len(y))
        return X[idx], y[idx]

    # ------------------------------------------------------------------
    # Flower protocol methods
    # ------------------------------------------------------------------

    def get_parameters(self, config: dict[str, Scalar]) -> list[np.ndarray]:
        """Server calls this to get current model weights at round start."""
        logger.info("[%s] get_parameters called", self.hospital_id)
        if not self.model._is_trained:
            logger.info("[%s] Not yet trained -- training now", self.hospital_id)
            self._train_local()
        return model_to_ndarrays(self.model)

    def fit(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Scalar],
    ) -> tuple[list[np.ndarray], int, dict[str, Scalar]]:
        """
        Server sends global weights -> we train locally -> return updated weights.
        """
        current_round = config.get("current_round", "?")
        logger.info(
            "[%s] fit() -- round %s, %d local samples",
            self.hospital_id,
            current_round,
            len(self.y_train),
        )
        # In production: self.model = ndarrays_to_model(parameters)
        self._train_local()
        updated_params = model_to_ndarrays(self.model)
        metrics = {
            "hospital_id": self.hospital_id,
            "local_samples": len(self.y_train),
        }
        return updated_params, len(self.y_train), metrics

    def evaluate(
        self,
        parameters: list[np.ndarray],
        config: dict[str, Scalar],
    ) -> tuple[float, int, dict[str, Scalar]]:
        """
        Server asks us to evaluate the global model on local data.
        Returns loss, num_samples, metrics -- no patient data leaves.
        """
        logger.info("[%s] evaluate() called", self.hospital_id)
        from sklearn.metrics import log_loss, roc_auc_score

        if not self.model._is_trained:
            self._train_local()

        y_prob = self.model._xgb.predict_proba(self.X_train)[:, 1]
        loss = log_loss(self.y_train, y_prob)
        auc = roc_auc_score(self.y_train, y_prob)

        logger.info(
            "[%s] local AUC=%.4f, loss=%.4f", self.hospital_id, auc, loss
        )
        return loss, len(self.y_train), {"auc": auc, "hospital": self.hospital_id}

    def _train_local(self) -> None:
        """Train the XGBoost model on this hospital local data."""
        self.model.train_on_synthetic_data()
        logger.info(
            "[%s] local model trained, _is_trained=%s, val_auc=%.4f",
            self.hospital_id,
            self.model._is_trained,
            self.model._val_auc or 0.0,
        )


# ---------------------------------------------------------------------------
# Client factory (used by simulation runner)
# ---------------------------------------------------------------------------

def get_client_fn(hospital_configs: list[dict]) -> Any:
    """
    Returns a factory function that Flowers simulation engine calls
    to create clients.
    """
    from flwr.common import Context

    def client_fn(context: Context) -> fl.client.Client:
        cid = str(context.node_id % len(hospital_configs))
        config = hospital_configs[int(cid)]
        client = SepsisFlowerClient(
            hospital_id=config["id"],
            data_slice_seed=config["seed"],
        )
        return client.to_client()

    return client_fn
