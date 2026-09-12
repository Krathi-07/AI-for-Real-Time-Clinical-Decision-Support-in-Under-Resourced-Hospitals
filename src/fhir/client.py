"""
FHIR REST client — connects to any FHIR R4 server and fetches patient data.

Why this exists:
  Every hospital runs a different EHR system, but all expose a FHIR R4 API.
  This client is the single point of contact — change FHIR_BASE_URL and it
  works with any hospital's server without touching any other code.
"""

import requests
from requests.exceptions import RequestException

# Free public FHIR R4 test server — use this for all development
# In production, this becomes the hospital's actual FHIR server URL
FHIR_BASE_URL = "https://hapi.fhir.org/baseR4"

# Standard headers required by all FHIR servers
# application/fhir+json tells the server we want FHIR-formatted JSON back
HEADERS = {
    "Accept": "application/fhir+json",
    "Content-Type": "application/fhir+json",
}


def fetch_patient_bundle(patient_id: str) -> dict:
    """
    Fetch everything available for a patient in one API call.

    The $everything operation is the most important FHIR endpoint —
    it returns ALL resources linked to a patient: vitals, labs,
    diagnoses, medications, allergies — in one Bundle.

    Args:
        patient_id: The FHIR patient ID (e.g. "592442")

    Returns:
        Raw Bundle as a Python dict (parsed from JSON)

    Raises:
        RuntimeError if the server is unreachable or returns an error
    """
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}/$everything"

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()  # raises exception for 4xx/5xx responses
        return response.json()

    except RequestException as e:
        raise RuntimeError(f"Failed to fetch patient {patient_id}: {e}") from e


def fetch_observations(patient_id: str) -> dict:
    """
    Fetch only Observation resources for a patient.

    More targeted than $everything — useful when you only need
    vitals and lab values, not the full record.

    Args:
        patient_id: The FHIR patient ID

    Returns:
        Bundle dict containing only Observation resources
    """
    url = f"{FHIR_BASE_URL}/Observation"
    params = {
        "patient": patient_id,
        "_count": 100,      # max results per page
        "_sort": "-date",   # most recent first
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    except RequestException as e:
        raise RuntimeError(f"Failed to fetch observations for {patient_id}: {e}") from e


def search_patients(family_name: str | None = None, count: int = 5) -> dict:
    """
    Search for patients on the FHIR server.

    Useful for development — lets us find real patient IDs
    on the HAPI test server to experiment with.

    Args:
        family_name: Optional last name filter
        count: Max number of results to return

    Returns:
        Bundle dict containing matching Patient resources
    """
    url = f"{FHIR_BASE_URL}/Patient"
    params = {"_count": count}

    if family_name:
        params["family"] = family_name

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    except RequestException as e:
        raise RuntimeError(f"Failed to search patients: {e}") from e


def check_server_health() -> bool:
    """
    Ping the FHIR server to verify it is reachable.

    Always call this first in your pipeline — fail fast if
    the server is down rather than getting cryptic errors later.

    Returns:
        True if server is healthy, False otherwise
    """
    try:
        response = requests.get(
            f"{FHIR_BASE_URL}/metadata",  # FHIR capability statement endpoint
            headers=HEADERS,
            timeout=10
        )
        return response.status_code == 200

    except RequestException:
        return False
        