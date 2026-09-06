from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional
from src.models.early_warning import ClinicalPrediction, EarlyWarningSepsis
from src.nlp.note_parser import ClinicalNoteParser, ClinicalNoteParseResult

logger = logging.getLogger(__name__)

SEPSIS_DIAGNOSIS_KEYWORDS = {
    "sepsis", "septicemia", "septicaemia", "bacteremia", "bacteraemia",
    "septic shock", "systemic inflammatory response", "sirs", "severe sepsis",
}
BROAD_SPECTRUM_ANTIBIOTICS = {
    "vancomycin", "piperacillin-tazobactam", "meropenem", "imipenem",
    "cefepime", "ceftriaxone", "levofloxacin", "ciprofloxacin",
    "metronidazole", "linezolid", "daptomycin",
}
RISK_ORDER = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3, "UNKNOWN": -1}
RISK_LEVELS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]

@dataclass
class PatientSnapshot:
    patient_id: str
    encounter_id: str = ""
    fhir_features: dict = field(default_factory=dict)
    note_text: str = ""
    early_warning: Optional[ClinicalPrediction] = None
    nlp_result: Optional[ClinicalNoteParseResult] = None
    fused_risk_level: str = "UNKNOWN"
    fused_risk_score: float = 0.0
    fused_confidence: str = "low"
    escalated_by_nlp: bool = False
    corroborated: bool = False
    broad_spectrum_antibiotics_noted: bool = False
    negation_conflicts: list = field(default_factory=list)
    alert_summary: str = ""
    data_sources: list = field(default_factory=list)

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "encounter_id": self.encounter_id,
            "fused_risk_level": self.fused_risk_level,
            "fused_risk_score": round(self.fused_risk_score, 4),
            "fused_confidence": self.fused_confidence,
            "escalated_by_nlp": self.escalated_by_nlp,
            "corroborated": self.corroborated,
            "broad_spectrum_antibiotics_noted": self.broad_spectrum_antibiotics_noted,
            "negation_conflicts": self.negation_conflicts,
            "alert_summary": self.alert_summary,
            "data_sources": self.data_sources,
            "early_warning": self.early_warning.to_dict() if self.early_warning else None,
            "nlp_result": self.nlp_result.to_dict() if self.nlp_result else None,
        }

class ClinicalEngine:
    def __init__(self):
        self._warning_model = None
        self._nlp_parser = None
        self._models_loaded = False

    def load_models(self):
        logger.info("Loading Early Warning model...")
        self._warning_model = EarlyWarningSepsis()
        self._warning_model.train_on_synthetic_data()
        logger.info("Loading NLP parser...")
        self._nlp_parser = ClinicalNoteParser()
        self._models_loaded = True
        logger.info("All models loaded. Engine ready.")

    def analyse(self, patient_id, fhir_features, note_text="", encounter_id=""):
        if not self._models_loaded:
            raise RuntimeError("Call engine.load_models() before analyse().")
        snapshot = PatientSnapshot(
            patient_id=patient_id, encounter_id=encounter_id,
            fhir_features=fhir_features, note_text=note_text,
        )
        if fhir_features:
            logger.info(f"[{patient_id}] Running early warning model...")
            snapshot.early_warning = self._warning_model.predict(fhir_features)
            snapshot.data_sources.append("vitals_labs")
            logger.info(f"[{patient_id}] Model risk: {snapshot.early_warning.risk_level} ({snapshot.early_warning.risk_percent:.1f}%)")
        if note_text and note_text.strip():
            logger.info(f"[{patient_id}] Running NLP parser...")
            snapshot.nlp_result = self._nlp_parser.parse(note_text)
            snapshot.data_sources.append("clinical_note")
        snapshot = self._fuse(snapshot)
        snapshot.alert_summary = self._build_alert(snapshot)
        return snapshot

    def _fuse(self, snapshot):
        if snapshot.early_warning:
            snapshot.fused_risk_level = snapshot.early_warning.risk_level
            snapshot.fused_risk_score = snapshot.early_warning.risk_score
            snapshot.fused_confidence = snapshot.early_warning.confidence
        else:
            snapshot.fused_risk_level = "UNKNOWN"
            snapshot.fused_risk_score = 0.0
            snapshot.fused_confidence = "low"
        if not snapshot.nlp_result:
            return snapshot
        nlp = snapshot.nlp_result
        found_sepsis = any(
            any(kw in d for kw in SEPSIS_DIAGNOSIS_KEYWORDS)
            for d in nlp.diagnoses
        )
        if found_sepsis:
            current = RISK_ORDER.get(snapshot.fused_risk_level, 0)
            if current < RISK_ORDER["HIGH"]:
                new_level = RISK_LEVELS[min(current + 1, 3)]
                logger.info(f"Rule 1: NLP sepsis diagnosis — escalating {snapshot.fused_risk_level} to {new_level}")
                snapshot.fused_risk_level = new_level
                snapshot.escalated_by_nlp = True
        if snapshot.early_warning:
            top_names = {d.feature_name.replace("_", " ") for d in snapshot.early_warning.top_drivers if d.direction == "increases_risk"}
            nlp_words = set(" ".join(nlp.symptoms).split())
            if top_names & nlp_words:
                snapshot.corroborated = True
                if snapshot.fused_confidence == "moderate":
                    snapshot.fused_confidence = "high"
                logger.info("Rule 2: Corroboration — model and note agree")
        found_broad = any(any(ab in med for ab in BROAD_SPECTRUM_ANTIBIOTICS) for med in nlp.medications)
        if found_broad:
            snapshot.broad_spectrum_antibiotics_noted = True
            logger.info("Rule 3: Broad-spectrum antibiotics noted")
        if snapshot.early_warning:
            top_risk = {d.feature_name for d in snapshot.early_warning.top_drivers if d.direction == "increases_risk"}
            for negated in nlp.negated_entities:
                for feat in top_risk:
                    if set(feat.replace("_", " ").split()) & set(negated.split()):
                        conflict = f"Model flagged '{feat}' as risk driver but note says '{negated}' is absent"
                        snapshot.negation_conflicts.append(conflict)
                        logger.info(f"Rule 4: Conflict — {conflict}")
        return snapshot

    def _build_alert(self, snapshot):
        lines = []
        emoji = {"LOW": "GREEN", "MODERATE": "AMBER", "HIGH": "RED", "CRITICAL": "CRITICAL", "UNKNOWN": "UNKNOWN"}
        tag = emoji.get(snapshot.fused_risk_level, "UNKNOWN")
        lines.append(f"[{tag}] SEPSIS RISK: {snapshot.fused_risk_level} ({snapshot.fused_risk_score*100:.1f}%) | Confidence: {snapshot.fused_confidence.upper()}")
        lines.append(f"Patient: {snapshot.patient_id} | Sources: {', '.join(snapshot.data_sources) or 'none'}")
        lines.append("")
        if snapshot.early_warning and snapshot.early_warning.top_drivers:
            lines.append("Vital/Lab Drivers:")
            for d in snapshot.early_warning.top_drivers:
                if d.direction == "increases_risk" and d.value > -1.0:
                    lines.append(f"   - {d.clinical_note}")
        if snapshot.nlp_result:
            nlp = snapshot.nlp_result
            if nlp.diagnoses:
                lines.append(f"\nDiagnoses in note: {', '.join(nlp.diagnoses)}")
            if nlp.symptoms:
                lines.append(f"Symptoms documented: {', '.join(nlp.symptoms)}")
            if nlp.medications:
                lines.append(f"Medications: {', '.join(nlp.medications)}")
            if nlp.negated_entities:
                lines.append(f"Absent/denied: {', '.join(nlp.negated_entities)}")
        if snapshot.escalated_by_nlp:
            lines.append("\n** Risk escalated: clinical note contains sepsis diagnosis **")
        if snapshot.corroborated:
            lines.append("** Corroborated: model and note agree on risk drivers **")
        if snapshot.broad_spectrum_antibiotics_noted:
            lines.append("** Broad-spectrum antibiotics noted **")
        for c in snapshot.negation_conflicts:
            lines.append(f"** Conflict: {c} **")
        lines.append("\nAI-generated alert. Clinical judgment always applies.")
        return "\n".join(lines)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    engine = ClinicalEngine()
    engine.load_models()

    print("\n" + "="*65)
    print("TEST 1: Septic patient — vitals + confirming note")
    print("="*65)
    snap1 = engine.analyse(
        patient_id="P001",
        fhir_features={"systolic_bp": 88.0, "diastolic_bp": 58.0, "heart_rate": 118.0, "respiratory_rate": 26.0, "body_temperature": 39.2, "spo2": 93.0, "glucose": 155.0, "creatinine": 1.8, "wbc": 16.5, "lactate": 4.2, "hemoglobin": 11.2, "pulse_pressure": 30.0},
        note_text="65F presenting with fever and tachycardia. Suspect sepsis. No chest pain. Started vancomycin and piperacillin-tazobactam. History of T2DM and CKD stage 3.",
    )
    print(snap1.alert_summary)
    print(f"\nEscalated by NLP: {snap1.escalated_by_nlp}")
    print(f"Corroborated:     {snap1.corroborated}")
    print(f"Broad-spectrum:   {snap1.broad_spectrum_antibiotics_noted}")

    print("\n" + "="*65)
    print("TEST 2: Healthy patient — vitals only")
    print("="*65)
    snap2 = engine.analyse(
        patient_id="P002",
        fhir_features={"systolic_bp": 122.0, "diastolic_bp": 78.0, "heart_rate": 72.0, "respiratory_rate": 16.0, "body_temperature": 36.8, "spo2": 99.0, "glucose": 92.0, "creatinine": 0.9, "wbc": 7.2, "lactate": 0.9, "hemoglobin": 13.5, "pulse_pressure": 44.0},
    )
    print(snap2.alert_summary)

    print("\n" + "="*65)
    print("TEST 3: Borderline vitals + escalating note")
    print("="*65)
    snap3 = engine.analyse(
        patient_id="P003",
        fhir_features={"systolic_bp": 102.0, "diastolic_bp": 68.0, "heart_rate": 98.0, "respiratory_rate": 21.0, "body_temperature": 38.5, "spo2": 96.0, "glucose": 130.0, "creatinine": 1.3, "wbc": 13.0, "lactate": 2.1, "hemoglobin": 12.0, "pulse_pressure": 34.0},
        note_text="Patient unwell, possibly early sepsis. No vomiting. Denies chest pain. Started ceftriaxone empirically.",
    )
    print(snap3.alert_summary)
    print(f"\nEscalated by NLP: {snap3.escalated_by_nlp}")
    print(f"Fused risk:       {snap3.fused_risk_level}")
    print("\nPhase 3 fusion engine smoke test complete.")
