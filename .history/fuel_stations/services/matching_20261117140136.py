import re
from difflib import SequenceMatcher


def normalize_text(value):
    """Normalize text for comparison."""
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    return " ".join(value.split())


def compare_station(station, candidate):
    """
    Conservatively compare a database station with a Geoapify result.

    City and state matches provide location context only.
    They cannot independently establish station identity.
    """

    database_name = normalize_text(station.name)
    candidate_name = normalize_text(candidate.get("name", ""))

    database_address = normalize_text(station.address)
    candidate_address = normalize_text(candidate.get("formatted", ""))

    name_similarity = SequenceMatcher(
        None,
        database_name,
        candidate_name
    ).ratio()

    address_similarity = SequenceMatcher(
        None,
        database_address,
        candidate_address
    ).ratio()

    city_matches = (
        normalize_text(station.city)
        == normalize_text(candidate.get("city", ""))
    )

    state_matches = (
        station.state.upper()
        == candidate.get("state_code", "").upper()
    )

    # Require meaningful business/address evidence.
    if city_matches and state_matches:
        if name_similarity >= 0.90 and address_similarity >= 0.80:
            status = "EXACT"

        elif name_similarity >= 0.75 and address_similarity >= 0.60:
            status = "APPROXIMATE"

        else:
            status = "REVIEW"
    else:
        status = "REVIEW"

    return {
        "station_id": station.id,
        "station_name": station.name,
        "candidate_name": candidate.get("name"),
        "name_similarity": round(name_similarity, 3),
        "address_similarity": round(address_similarity, 3),
        "city_matches": city_matches,
        "state_matches": state_matches,
        "status": status,
        "latitude": candidate.get("lat"),
        "longitude": candidate.get("lon"),
        "candidate_address": candidate.get("formatted"),
    }