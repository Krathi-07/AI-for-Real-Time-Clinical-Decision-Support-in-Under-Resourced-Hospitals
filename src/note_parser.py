"""
note_parser.py — Phase 2: NLP Pipeline for Clinical Notes

WHAT THIS FILE DOES:
--------------------
Doctors write free-text notes like:
  "65F with fever, tachycardia. Suspect sepsis. No chest pain.
   Started piperacillin-tazobactam. Hx of T2DM and CKD stage 3."

This module converts that unstructured text into a structured dictionary
that the rest of the AI system can use — linking it with the FHIR feature
vectors from Phase 1.

KEY CONCEPTS:
-------------
1. NER (Named Entity Recognition): spaCy + scispaCy identify medical spans
   in the text and label them as DISEASE or CHEMICAL.

2. Negation detection (NegEx algorithm, implemented directly):
   Detects when an entity is negated — "no chest pain" should NOT be
   extracted as a symptom. We implement NegEx ourselves (no negspacy
   dependency) by looking for trigger words within a token window around
   each entity.

3. Vital sign extraction: Regex patterns catch values like "HR 118 bpm",
   "Temp 38.9C", "BP 90/60" mentioned in narrative text.

4. Abbreviation expansion: Medical notes are dense with abbreviations.
   We maintain a lookup table (T2DM -> type 2 diabetes mellitus) so
   downstream models see consistent terminology.

WHY scispaCy over general spaCy:
---------------------------------
General spaCy (en_core_web_sm) was trained on news/web text. It would
completely miss "piperacillin-tazobactam" as a meaningful entity.
scispaCy's en_ner_bc5cdr_md was trained on biomedical literature and
correctly identifies drugs (CHEMICAL) and diseases (DISEASE).
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field

import spacy

# Suppress the minor version compatibility warning from scispaCy model.
warnings.filterwarnings("ignore", message=".*W095.*")
warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class VitalMention:
    """A vital sign extracted from narrative text (not from FHIR Observation).

    Example: "HR was 118 bpm" -> VitalMention("heart_rate", 118.0, "bpm")
    """
    vital_type: str
    value: float
    unit: str
    raw_text: str


@dataclass
class ClinicalNoteParseResult:
    """
    Structured output of parsing one clinical note.
    This is the contract between Phase 2 (NLP) and Phase 3 (Multimodal Fusion).
    """
    diseases: list[str] = field(default_factory=list)
    chemicals: list[str] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    diagnoses: list[str] = field(default_factory=list)
    negated_entities: list[str] = field(default_factory=list)
    vitals_mentioned: list[VitalMention] = field(default_factory=list)
    entity_count: int = 0
    note_length_chars: int = 0
    confidence: str = "low"

    def to_dict(self) -> dict:
        return {
            "diseases": self.diseases,
            "chemicals": self.chemicals,
            "symptoms": self.symptoms,
            "medications": self.medications,
            "diagnoses": self.diagnoses,
            "negated_entities": self.negated_entities,
            "vitals_mentioned": [
                {
                    "vital_type": v.vital_type,
                    "value": v.value,
                    "unit": v.unit,
                    "raw_text": v.raw_text,
                }
                for v in self.vitals_mentioned
            ],
            "entity_count": self.entity_count,
            "note_length_chars": self.note_length_chars,
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# MEDICAL ABBREVIATION LOOKUP
# ---------------------------------------------------------------------------

ABBREVIATION_MAP: dict[str, str] = {
    "T2DM":     "type 2 diabetes mellitus",
    "T1DM":     "type 1 diabetes mellitus",
    "DM":       "diabetes mellitus",
    "HTN":      "hypertension",
    "CAD":      "coronary artery disease",
    "COPD":     "chronic obstructive pulmonary disease",
    "CKD":      "chronic kidney disease",
    "AKI":      "acute kidney injury",
    "UTI":      "urinary tract infection",
    "MI":       "myocardial infarction",
    "CVA":      "cerebrovascular accident",
    "DVT":      "deep vein thrombosis",
    "PE":       "pulmonary embolism",
    "CHF":      "congestive heart failure",
    "ARDS":     "acute respiratory distress syndrome",
    "SOB":      "shortness of breath",
    "CP":       "chest pain",
    "N/V":      "nausea and vomiting",
    "N/V/D":    "nausea vomiting diarrhea",
    "Hx":       "history",
    "PMHx":     "past medical history",
    "h/o":      "history of",
    "r/o":      "rule out",
    "pip-tazo": "piperacillin-tazobactam",
    "vanco":    "vancomycin",
}

MEDICATION_KEYWORDS = {
    "cillin", "mycin", "cycline", "floxacin", "oxacin", "azole",
    "prazole", "sartan", "pril", "olol", "statin", "vir",
    "metformin", "insulin", "warfarin", "heparin", "aspirin",
    "metoprolol", "amlodipine", "lisinopril", "atorvastatin",
    "vancomycin", "levofloxacin", "ceftriaxone", "meropenem",
    "piperacillin", "tazobactam", "gentamicin", "azithromycin",
    "dexamethasone", "prednisolone", "morphine", "fentanyl",
    "midazolam", "propofol", "norepinephrine", "dopamine",
    "paracetamol", "acetaminophen", "ibuprofen", "amoxicillin",
}

SYMPTOM_KEYWORDS = {
    "fever", "pain", "dyspnea", "tachycardia", "bradycardia",
    "hypotension", "hypertension", "nausea", "vomiting", "diarrhea",
    "confusion", "altered", "drowsiness", "fatigue", "weakness",
    "cough", "sputum", "wheeze", "edema", "swelling", "rash",
    "pallor", "jaundice", "cyanosis", "diaphoresis", "rigors",
    "chills", "malaise", "anorexia", "oliguria", "dysuria",
    "palpitation", "syncope", "tremor", "seizure", "headache",
    "dizziness", "vertigo", "tachypnea",
}


# ---------------------------------------------------------------------------
# VITAL SIGN REGEX PATTERNS
# ---------------------------------------------------------------------------

VITAL_PATTERNS: list[tuple[str, str, str]] = [
    ("heart_rate",
     r"\b(?:HR|heart rate|pulse)\s*[:\-]?\s*(\d{2,3})\s*(?:bpm|beats?(?:/min)?)?",
     "bpm"),
    ("systolic_bp",
     r"\b(?:BP|blood pressure)\s*[:\-]?\s*(\d{2,3})\s*/\s*\d{2,3}",
     "mmHg"),
    ("diastolic_bp",
     r"\b(?:BP|blood pressure)\s*[:\-]?\s*\d{2,3}\s*/\s*(\d{2,3})",
     "mmHg"),
    ("temperature",
     r"\b(?:Temp?|temperature)\s*[:\-]?\s*(\d{2}(?:\.\d)?)\s*[°]?\s*[CF]",
     "C"),
    ("respiratory_rate",
     r"\b(?:RR|resp(?:iratory)? rate)\s*[:\-]?\s*(\d{1,2})\s*(?:/min)?",
     "/min"),
    ("spo2",
     r"\b(?:SpO2|O2 sat|oxygen sat(?:uration)?)\s*[:\-]?\s*(\d{2,3})\s*%?",
     "%"),
]


# ---------------------------------------------------------------------------
# MAIN PARSER CLASS
# ---------------------------------------------------------------------------

class ClinicalNoteParser:
    """
    NLP pipeline for extracting structured clinical entities from free-text notes.

    The spaCy model is loaded once in __init__ and reused across many notes —
    loading takes ~2 seconds, so we never load it per-call.

    Usage:
        parser = ClinicalNoteParser()
        result = parser.parse("65F with fever and tachycardia. Suspect sepsis.")
        print(result.to_dict())
    """

    # NegEx negation triggers (Chapman et al. 2001)
    # Words/phrases indicating the nearby entity is negated
    NEGATION_TRIGGERS: ClassVar[set] = {
        "no", "not", "without", "denies", "deny", "denying",
        "absent", "absence", "negative", "negative for",
        "rules out", "ruled out", "rule out", "r/o",
        "unremarkable for", "free of", "unlikely",
        "never", "neither", "nor",
    }

    def __init__(self, model_name: str = "en_ner_bc5cdr_md"):
        """Load the scispaCy NER model and add sentence boundary detection."""
        print(f"Loading scispaCy model: {model_name}...")
        self.nlp = spacy.load(model_name)

        # Sentencizer splits text into sentences so negation detection
        # doesn't bleed across sentence boundaries.
        # "No fever. Patient has tachycardia." — negation in sentence 1
        # must NOT affect tachycardia in sentence 2.
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer", first=True)

        print(f"Pipeline ready. Components: {self.nlp.pipe_names}")

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def parse(self, note_text: str) -> ClinicalNoteParseResult:
        """
        Parse a clinical note and return structured entities.

        Args:
            note_text: Raw free-text clinical note

        Returns:
            ClinicalNoteParseResult with entities classified by type
            and negation status.
        """
        if not note_text or not note_text.strip():
            return ClinicalNoteParseResult(confidence="insufficient_data")

        # Step 1: Expand abbreviations so NER sees full medical terms
        expanded_text = self._expand_abbreviations(note_text)

        # Step 2: Run scispaCy NER
        doc = self.nlp(expanded_text)

        # Step 3: Collect and classify entities
        result = ClinicalNoteParseResult(note_length_chars=len(note_text))

        for ent in doc.ents:
            entity_text = ent.text.strip().lower()

            # Check negation using our own NegEx implementation
            if self._is_negated(ent):
                result.negated_entities.append(entity_text)
                continue  # Negated — do NOT add to positive lists

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

        # Step 4: Extract vitals from narrative text using regex
        result.vitals_mentioned = self._extract_vitals(note_text)

        # Step 5: Deduplicate
        result.diseases         = list(dict.fromkeys(result.diseases))
        result.chemicals        = list(dict.fromkeys(result.chemicals))
        result.symptoms         = list(dict.fromkeys(result.symptoms))
        result.medications      = list(dict.fromkeys(result.medications))
        result.diagnoses        = list(dict.fromkeys(result.diagnoses))
        result.negated_entities = list(dict.fromkeys(result.negated_entities))

        # Step 6: Summary stats
        result.entity_count = len(result.diseases) + len(result.chemicals)
        result.confidence   = self._compute_confidence(result)

        return result

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _expand_abbreviations(self, text: str) -> str:
        """Replace known medical abbreviations with full terms."""
        for abbrev, expansion in ABBREVIATION_MAP.items():
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            text = re.sub(pattern, expansion, text)
        return text

    def _is_negated(self, ent) -> bool:
        """
        NegEx negation detection — implemented without negspacy library.

        Algorithm:
        - Look 5 tokens BEFORE the entity for negation triggers
        - Look 3 tokens AFTER the entity for negation triggers
        - Stay within sentence boundaries
        - Check both single words and two-word phrases
        """
        sent = ent.sent
        trigger_set = self.NEGATION_TRIGGERS

        # Tokens before the entity (within same sentence)
        pre_start  = max(sent.start, ent.start - 5)
        pre_tokens = [t.text.lower() for t in ent.doc[pre_start:ent.start]]

        # Tokens after the entity (within same sentence)
        post_end    = min(sent.end, ent.end + 3)
        post_tokens = [t.text.lower() for t in ent.doc[ent.end:post_end]]

        all_tokens = pre_tokens + post_tokens

        # Single-word triggers
        for token in all_tokens:
            if token in trigger_set:
                return True

        # Two-word phrase triggers ("negative for", "ruled out", etc.)
        for i in range(len(all_tokens) - 1):
            phrase = all_tokens[i] + " " + all_tokens[i + 1]
            if phrase in trigger_set:
                return True

        return False

    def _is_symptom(self, entity_text: str) -> bool:
        """Classify a DISEASE entity as symptom vs. diagnosis."""
        return any(kw in entity_text for kw in SYMPTOM_KEYWORDS)

    def _is_medication(self, entity_text: str) -> bool:
        """Classify a CHEMICAL entity as a medication."""
        return any(kw in entity_text for kw in MEDICATION_KEYWORDS)

    def _extract_vitals(self, text: str) -> list[VitalMention]:
        """Extract vital signs mentioned in narrative text using regex."""
        vitals = []
        for vital_type, pattern, unit in VITAL_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    value = float(match.group(1))
                    vitals.append(VitalMention(
                        vital_type=vital_type,
                        value=value,
                        unit=unit,
                        raw_text=match.group(0),
                    ))
                except (ValueError, IndexError):
                    continue
        return vitals

    def _compute_confidence(self, result: ClinicalNoteParseResult) -> str:
        """Estimate parse confidence based on how much was extracted."""
        total = result.entity_count + len(result.vitals_mentioned)
        if total == 0:
            return "low"
        elif total <= 3:
            return "medium"
        else:
            return "high"


# ---------------------------------------------------------------------------
# SMOKE TEST  (run with: uv run python src/nlp/note_parser.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    parser = ClinicalNoteParser()

    # Test Case 1: Sepsis presentation
    note_1 = """
    65F presenting with fever (Temp 38.9C), tachycardia (HR 118 bpm),
    and confusion. BP 88/56. RR 24/min. SpO2 94%.
    Suspect sepsis. No chest pain. No shortness of breath.
    Started piperacillin-tazobactam and vancomycin IV.
    PMHx: T2DM, CKD stage 3. Denies recent travel.
    """

    print("=" * 60)
    print("TEST CASE 1: Sepsis presentation")
    print("=" * 60)
    result_1 = parser.parse(note_1)
    print(json.dumps(result_1.to_dict(), indent=2))

    # Test Case 2: Negation check
    note_2 = """
    Patient denies fever or chills. No nausea or vomiting.
    No history of hypertension. Currently on metformin for diabetes mellitus.
    Chest X-ray negative for pneumonia.
    """

    print("\n" + "=" * 60)
    print("TEST CASE 2: Negation detection")
    print("=" * 60)
    result_2 = parser.parse(note_2)
    print(json.dumps(result_2.to_dict(), indent=2))

    # Test Case 3: Minimal rural hospital note
    note_3 = "Patient unwell. High fever. Give paracetamol."

    print("\n" + "=" * 60)
    print("TEST CASE 3: Minimal rural hospital note")
    print("=" * 60)
    result_3 = parser.parse(note_3)
    print(json.dumps(result_3.to_dict(), indent=2))

    # Negation integrity check
    print("\n" + "=" * 60)
    print("NEGATION INTEGRITY CHECK")
    print("=" * 60)
    negated  = set(result_2.negated_entities)
    positive = set(result_2.diseases + result_2.symptoms + result_2.diagnoses)
    leaked   = negated & positive
    if leaked:
        print(f"FAIL - negated entities leaked into positive lists: {leaked}")
    else:
        print("PASS - no negated entities in positive disease lists")
        print(f"   Negated:          {result_2.negated_entities}")
        print(f"   Positive diseases: {result_2.diseases}")

        