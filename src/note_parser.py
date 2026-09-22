from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import ClassVar

import spacy

warnings.filterwarnings("ignore", message=".*W095.*")
warnings.filterwarnings("ignore", category=FutureWarning)

@dataclass
class VitalMention:
    vital_type: str
    value: float
    unit: str
    raw_text: str

@dataclass
class ClinicalNoteParseResult:
    diseases: list = field(default_factory=list)
    chemicals: list = field(default_factory=list)
    symptoms: list = field(default_factory=list)
    medications: list = field(default_factory=list)
    diagnoses: list = field(default_factory=list)
    negated_entities: list = field(default_factory=list)
    vitals_mentioned: list = field(default_factory=list)
    entity_count: int = 0
    note_length_chars: int = 0
    confidence: str = "low"

    def to_dict(self):
        return {
            "diseases": self.diseases,
            "chemicals": self.chemicals,
            "symptoms": self.symptoms,
            "medications": self.medications,
            "diagnoses": self.diagnoses,
            "negated_entities": self.negated_entities,
            "vitals_mentioned": [{"vital_type": v.vital_type, "value": v.value, "unit": v.unit, "raw_text": v.raw_text} for v in self.vitals_mentioned],
            "entity_count": self.entity_count,
            "note_length_chars": self.note_length_chars,
            "confidence": self.confidence,
        }

ABBREVIATION_MAP = {
    "T2DM": "type 2 diabetes mellitus", "T1DM": "type 1 diabetes mellitus",
    "DM": "diabetes mellitus", "HTN": "hypertension", "CAD": "coronary artery disease",
    "COPD": "chronic obstructive pulmonary disease", "CKD": "chronic kidney disease",
    "AKI": "acute kidney injury", "UTI": "urinary tract infection",
    "MI": "myocardial infarction", "CHF": "congestive heart failure",
    "SOB": "shortness of breath", "CP": "chest pain",
    "N/V": "nausea and vomiting", "Hx": "history", "h/o": "history of",
    "r/o": "rule out", "vanco": "vancomycin",
}

MEDICATION_KEYWORDS = {
    "cillin", "mycin", "cycline", "floxacin", "azole", "prazole",
    "sartan", "pril", "olol", "statin", "metformin", "insulin",
    "warfarin", "heparin", "aspirin", "vancomycin", "levofloxacin",
    "ceftriaxone", "meropenem", "piperacillin", "tazobactam",
    "dexamethasone", "prednisolone", "morphine", "fentanyl",
    "paracetamol", "acetaminophen", "ibuprofen", "amoxicillin",
}

SYMPTOM_KEYWORDS = {
    "fever", "pain", "dyspnea", "tachycardia", "bradycardia",
    "hypotension", "nausea", "vomiting", "diarrhea", "confusion",
    "fatigue", "weakness", "cough", "edema", "swelling", "rash",
    "pallor", "jaundice", "cyanosis", "chills", "malaise",
    "oliguria", "palpitation", "syncope", "headache", "dizziness",
    "tachypnea", "rigors", "diaphoresis",
}

VITAL_PATTERNS = [
    ("heart_rate", r"\b(?:HR|heart rate|pulse)\s*[:\-]?\s*(\d{2,3})\s*(?:bpm|beats?(?:/min)?)?", "bpm"),
    ("systolic_bp", r"\b(?:BP|blood pressure)\s*[:\-]?\s*(\d{2,3})\s*/\s*\d{2,3}", "mmHg"),
    ("diastolic_bp", r"\b(?:BP|blood pressure)\s*[:\-]?\s*\d{2,3}\s*/\s*(\d{2,3})", "mmHg"),
    ("temperature", r"\b(?:Temp?|temperature)\s*[:\-]?\s*(\d{2}(?:\.\d)?)\s*[o]?\s*[CF]", "C"),
    ("respiratory_rate", r"\b(?:RR|resp(?:iratory)? rate)\s*[:\-]?\s*(\d{1,2})\s*(?:/min)?", "/min"),
    ("spo2", r"\b(?:SpO2|O2 sat|oxygen sat(?:uration)?)\s*[:\-]?\s*(\d{2,3})\s*%?", "%"),
]

class ClinicalNoteParser:
    NEGATION_TRIGGERS: ClassVar[set] = {
        "no", "not", "without", "denies", "deny", "denying",
        "absent", "absence", "negative", "negative for",
        "rules out", "ruled out", "rule out",
        "free of", "unlikely", "never", "neither", "nor",
    }

    def __init__(self, model_name="en_ner_bc5cdr_md"):
        print(f"Loading scispaCy model: {model_name}...")
        self.nlp = spacy.load(model_name)
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer", first=True)
        print(f"Pipeline ready. Components: {self.nlp.pipe_names}")

    def parse(self, note_text):
        if not note_text or not note_text.strip():
            return ClinicalNoteParseResult(confidence="insufficient_data")
        expanded_text = self._expand_abbreviations(note_text)
        doc = self.nlp(expanded_text)
        result = ClinicalNoteParseResult(note_length_chars=len(note_text))
        for ent in doc.ents:
            entity_text = ent.text.strip().lower()
            if self._is_negated(ent):
                result.negated_entities.append(entity_text)
                continue
            if ent.label_ == "DISEASE":
                result.diseases.append(entity_text)
                if self._is_symptom(entity_text):
                    result.symptoms.append(entity_text)
                else:
                    result.diagnoses.append(entity_text)
            elif ent.label_ == "CHEMICAL":
                result.chemicals.append(entity_text)
                if self._is_medication(entity_text):
                    result.medications.append(entity_text)
        result.vitals_mentioned = self._extract_vitals(note_text)
        result.diseases = list(dict.fromkeys(result.diseases))
        result.chemicals = list(dict.fromkeys(result.chemicals))
        result.symptoms = list(dict.fromkeys(result.symptoms))
        result.medications = list(dict.fromkeys(result.medications))
        result.diagnoses = list(dict.fromkeys(result.diagnoses))
        result.negated_entities = list(dict.fromkeys(result.negated_entities))
        result.entity_count = len(result.diseases) + len(result.chemicals)
        result.confidence = self._compute_confidence(result)
        return result

    def _expand_abbreviations(self, text):
        for abbrev, expansion in ABBREVIATION_MAP.items():
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            text = re.sub(pattern, expansion, text)
        return text

    def _is_negated(self, ent):
        sent = ent.sent
        triggers = self.NEGATION_TRIGGERS
        pre_start = max(sent.start, ent.start - 5)
        pre_tokens = [t.text.lower() for t in ent.doc[pre_start:ent.start]]
        post_end = min(sent.end, ent.end + 3)
        post_tokens = [t.text.lower() for t in ent.doc[ent.end:post_end]]
        all_tokens = pre_tokens + post_tokens
        for token in all_tokens:
            if token in triggers:
                return True
        for i in range(len(all_tokens) - 1):
            phrase = all_tokens[i] + " " + all_tokens[i+1]
            if phrase in triggers:
                return True
        return False

    def _is_symptom(self, text):
        return any(kw in text for kw in SYMPTOM_KEYWORDS)

    def _is_medication(self, text):
        return any(kw in text for kw in MEDICATION_KEYWORDS)

    def _extract_vitals(self, text):
        vitals = []
        for vital_type, pattern, unit in VITAL_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    vitals.append(VitalMention(vital_type=vital_type, value=float(match.group(1)), unit=unit, raw_text=match.group(0)))
                except (ValueError, IndexError):
                    continue
        return vitals

    def _compute_confidence(self, result):
        total = result.entity_count + len(result.vitals_mentioned)
        if total == 0:
            return "low"
        elif total <= 3:
            return "medium"
        else:
            return "high"

if __name__ == "__main__":
    import json
    parser = ClinicalNoteParser()

    note_1 = "65F presenting with fever (Temp 38.9C), tachycardia (HR 118 bpm), and confusion. BP 88/56. RR 24/min. SpO2 94%. Suspect sepsis. No chest pain. Started piperacillin-tazobactam and vancomycin IV. Hx: T2DM, CKD stage 3."
    print("=" * 60)
    print("TEST CASE 1: Sepsis presentation")
    print("=" * 60)
    print(json.dumps(parser.parse(note_1).to_dict(), indent=2))

    note_2 = "Patient denies fever or chills. No nausea or vomiting. No history of hypertension. Currently on metformin for diabetes mellitus. Chest X-ray negative for pneumonia."
    print("\n" + "=" * 60)
    print("TEST CASE 2: Negation detection")
    print("=" * 60)
    r2 = parser.parse(note_2)
    print(json.dumps(r2.to_dict(), indent=2))

    note_3 = "Patient unwell. High fever. Give paracetamol."
    print("\n" + "=" * 60)
    print("TEST CASE 3: Minimal rural note")
    print("=" * 60)
    print(json.dumps(parser.parse(note_3).to_dict(), indent=2))

    print("\n" + "=" * 60)
    print("NEGATION INTEGRITY CHECK")
    print("=" * 60)
    negated = set(r2.negated_entities)
    positive = set(r2.diseases + r2.symptoms + r2.diagnoses)
    leaked = negated & positive
    if leaked:
        print(f"FAIL - leaked: {leaked}")
    else:
        print("PASS - no negated entities in positive lists")
        print(f"   Negated:  {r2.negated_entities}")
        print(f"   Positive: {r2.diseases}")




