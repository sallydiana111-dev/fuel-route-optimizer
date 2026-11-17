from django.utils import timezone

from fuel_stations.models import FuelStation
from fuel_stations.services.geoapify import search_fuel_stations
from fuel_stations.services.matching import compare_station


def geocode_station(station, radius=5000):
    """
    Find possible geographic matches for a fuel station.

    Only sufficiently strong matches are saved automatically.
    Uncertain matches are marked for review.
    """

    # Use the city and state to search for candidates.
    # This is a search origin, not proof of station identity.
    from fuel_stations.services.geoapify import (
        search_geocoding_location,
    )

    location = search_geocoding_location(
        station.city,
        station.state
    )

    if not location:
        station.geocoding_status = (
            FuelStation.GeocodingStatus.UNMATCHED
        )
        station.geocoding_notes = (
            "Could not determine the city search location."
        )
        station.save()
        return None

    candidates = search_fuel_stations(
        latitude=location["lat"],
        longitude=location["lon"],
        radius=radius,
        limit=20,
    )

    if not candidates:
        station.geocoding_status = (
            FuelStation.GeocodingStatus.UNMATCHED
        )
        station.geocoding_notes = (
            "No nearby fuel station candidates found."
        )
        station.save()
        return None

    matches = [
        compare_station(station, candidate)
        for candidate in candidates
    ]

    best_match = max(
        matches,
        key=lambda item: (
            item["name_similarity"],
            item["address_similarity"],
        ),
    )

    if best_match["status"] == "EXACT":
        station.latitude = best_match["latitude"]
        station.longitude = best_match["longitude"]
        station.geocoding_status = (
            FuelStation.GeocodingStatus.EXACT
        )
        station.geocoding_source = "Geoapify"
        station.geocoding_notes = "Exact match accepted."
        station.geocoded_at = timezone.now()

    else:
        station.geocoding_status = (
            FuelStation.GeocodingStatus.REVIEW
        )
        station.geocoding_notes = (
            f"Candidate requires manual review: "
            f"{best_match['candidate_name']}."
        )

    station.save()

    return best_match