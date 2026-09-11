"""
FHIR Bundle parser — extracts structured data from raw FHIR Bundle dicts.

Why this exists:
  FHIR Bundles are deeply nested JSON. A Bundle contains entries, each entry
  has a resource, each resource has a type. This parser hides that complexity
  and gives clean Python objects to the rest of the system.

Learning note:
  A Bundle is like a envelope containing many letters (resources).
  Each letter has a type written on it (resourceType).
  This parser opens the envelope and sorts the letters by type.
"""

from datetime import datetime


def extract_resource_type(entry: dict) -> str:
    """Get the resourceType from a Bundle entry."""
    return entry.get("resource", {}).get("resourceType", "Unknown")


def parse_patient(bundle: dict) -> dict:
    """
    Extract patient demographics from a Bundle.

    Returns a clean dict with the patient's key details.
    In a real hospital, this ties every observation to a specific person.

    Args:
        bundle: Raw FHIR Bundle dict from client.py

    Returns:
        Dict with patient demographics, or empty dict if not found
    """
    for entry in bundle.get("entry", []):
        if extract_resource_type(entry) == "Patient":
            resource = entry["resource"]

            # Extract name — FHIR stores names as a list of name objects
            name = ""
            if resource.get("name"):
                name_obj = resource["name"][0]
                given = " ".join(name_obj.get("given", []))
                family = name_obj.get("family", "")
                name = f"{given} {family}".strip()

            # Extract age from birthDate
            age = None
            if resource.get("birthDate"):
                birth_year = int(resource["birthDate"][:4])
                age = datetime.now(tz=timezone.utc).year - birth_year

            return {
                "id": resource.get("id", ""),
                "name": name,
                "gender": resource.get("gender", "unknown"),
                "birth_date": resource.get("birthDate", ""),
                "age": age,
            }

    return {}


def parse_observations(bundle: dict) -> list[dict]:
    """
    Extract all Observation resources from a Bundle.

    Observations are the most important resource for our AI —
    they contain every vital sign and lab result. Each Observation
    has a LOINC code identifying WHAT was measured, and a value
    showing the result.

    Args:
        bundle: Raw FHIR Bundle dict

    Returns:
        List of observation dicts, each with code, value, unit, timestamp
    """
    observations = []

    for entry in bundle.get("entry", []):
        if extract_resource_type(entry) != "Observation":
            continue

        resource = entry["resource"]

        # Extract the LOINC code — this tells us WHAT was measured
        loinc_code = ""
        display = ""
        if resource.get("code", {}).get("coding"):
            coding = resource["code"]["coding"][0]
            loinc_code = coding.get("code", "")
            display = coding.get("display", "")

        # Extract the value — can be a quantity, string, or coded value
        value = None
        unit = ""

        if resource.get("valueQuantity"):
            value = resource["valueQuantity"].get("value")
            unit = resource["valueQuantity"].get("unit", "")

        elif resource.get("valueCodeableConcept"):
            # Some observations are coded (e.g. blood type = "A+")
            codings = resource["valueCodeableConcept"].get("coding", [])
            if codings:
                value = codings[0].get("display", "")

        elif resource.get("valueString"):
            value = resource["valueString"]

        # Extract timestamp
        timestamp = (
            resource.get("effectiveDateTime")
            or resource.get("issued")
            or ""
        )

        # Only include observations that have a value
        if value is not None:
            observations.append({
                "loinc_code": loinc_code,
                "display": display,
                "value": value,
                "unit": unit,
                "timestamp": timestamp,
                "status": resource.get("status", ""),
            })

    return observations


def parse_conditions(bundle: dict) -> list[dict]:
    """
    Extract Condition resources (diagnoses) from a Bundle.

    Conditions use ICD-10 codes — the international disease classification.
    For our AI, conditions give historical context:
    a patient with diabetes has different risk profiles than one without.

    Args:
        bundle: Raw FHIR Bundle dict

    Returns:
        List of condition dicts with ICD-10 codes and descriptions
    """
    conditions = []

    for entry in bundle.get("entry", []):
        if extract_resource_type(entry) != "Condition":
            continue

        resource = entry["resource"]

        # Extract ICD-10 code and description
        icd_code = ""
        display = ""
        if resource.get("code", {}).get("coding"):
            coding = resource["code"]["coding"][0]
            icd_code = coding.get("code", "")
            display = coding.get("display", "")

        # Clinical status — active, resolved, inactive
        status = ""
        if resource.get("clinicalStatus", {}).get("coding"):
            status = resource["clinicalStatus"]["coding"][0].get("code", "")

        conditions.append({
            "icd_code": icd_code,
            "display": display,
            "status": status,
            "onset_date": resource.get("onsetDateTime", ""),
        })

    return conditions


def parse_bundle_summary(bundle: dict) -> dict:
    """
    Parse a full Bundle and return a structured summary.

    This is the main function your pipeline will call —
    it runs all parsers and returns everything in one clean dict.

    Args:
        bundle: Raw FHIR Bundle dict from client.py

    Returns:
        Dict containing patient, observations, conditions, and counts
    """
    patient = parse_patient(bundle)
    observations = parse_observations(bundle)
    conditions = parse_conditions(bundle)

    return {
        "patient": patient,
        "observations": observations,
        "conditions": conditions,
        "summary": {
            "total_entries": len(bundle.get("entry", [])),
            "observation_count": len(observations),
            "condition_count": len(conditions),
            "has_vitals": any(
                obs["loinc_code"] in ["8480-6", "8867-4", "9279-1", "59408-5"]
                for obs in observations
            ),
        },
    }
