import re
from difflib import SequenceMatcher
from math import radians, sin, cos, sqrt, atan2


def normalize_text(value):
    """Normalize text for comparison."""

    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    return " ".join(value.split())


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two geographic coordinates in km."""

    earth_radius = 6371

    lat1, lon1, lat2, lon2 = map(
        radians,
        [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def compare_station(station, candidate):
    """
    Compare a database station with a Geoapify candidate.

    Returns a score and matching information.
    This function does not modify the database.
    """

    candidate_city = candidate.get("city", "")
    candidate_state = candidate.get("state_code", "")
    candidate_name = candidate.get("name", "")
    candidate_address = candidate.get("formatted", "")

    database_name = normalize_text(station.name)
    candidate_name = normalize_text(candidate_name)

    name_similarity = SequenceMatcher(
        None,
        database_name,
        candidate_name
    ).ratio()

    database_address = normalize_text(station.address)
    candidate_address = normalize_text(candidate_address)

    address_similarity = SequenceMatcher(
        None,
        database_address,
        candidate_address
    ).ratio()

    city_matches = (
        normalize_text(station.city)
        == normalize_text(candidate_city)
    )

    state_matches = (
        station.state.upper()
        == candidate_state.upper()
    )

    score = 0

    score += name_similarity * 50
    score += address_similarity * 20

    if city_matches:
        score += 15

    if state_matches:
        score += 15

    return {
        "station_id": station.id,
        "station_name": station.name,
        "candidate_name": candidate.get("name"),
        "name_similarity": round(name_similarity, 3),
        "address_similarity": round(address_similarity, 3),
        "city_matches": city_matches,
        "state_matches": state_matches,
        "score": round(score, 2),
        "latitude": candidate.get("lat"),
        "longitude": candidate.get("lon"),
        "candidate_address": candidate.get("formatted"),
    }