import requests

from django.conf import settings


GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

FUEL_CATEGORY = "service.vehicle.fuel"


class GeoapifyError(Exception):
    """Raised when a Geoapify request fails."""


def search_fuel_stations(latitude, longitude, radius=5000, limit=20):
    """
    Find fuel stations around a geographic location.

    Args:
        latitude: Search center latitude.
        longitude: Search center longitude.
        radius: Search radius in meters.
        limit: Maximum number of results.

    Returns:
        A list of Geoapify place properties.
    """

    api_key = settings.GEOAPIFY_API_KEY

    if not api_key:
        raise GeoapifyError("Geoapify API key is not configured.")

    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude.")

    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude.")

    if not 1 <= radius <= 50000:
        raise ValueError("Radius must be between 1 and 50000 meters.")

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    params = {
        "categories": FUEL_CATEGORY,
        "filter": f"circle:{longitude},{latitude},{radius}",
        "limit": limit,
        "apiKey": api_key,
    }

    try:
        response = requests.get(
            GEOAPIFY_PLACES_URL,
            params=params,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exc:
        raise GeoapifyError(
            f"Geoapify request failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise GeoapifyError(
            "Geoapify returned an invalid JSON response."
        ) from exc

    return [
        feature.get("properties", {})
        for feature in data.get("features", [])
    ]

def search_geocoding_location(city, state):
    """
    Find the geographic coordinates of a US city.

    These coordinates are only used as a search origin
    for discovering nearby fuel stations.
    """

    api_key = settings.GEOAPIFY_API_KEY

    if not api_key:
        raise GeoapifyError(
            "Geoapify API key is not configured."
        )

    url = "https://api.geoapify.com/v1/geocode/search"

    params = {
        "text": f"{city}, {state}, USA",
        "filter": "countrycode:us",
        "limit": 1,
        "apiKey": api_key,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        raise GeoapifyError(
            f"Geocoding request failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise GeoapifyError(
            "Geoapify returned invalid JSON."
        ) from exc

    features = data.get("features", [])

    if not features:
        return None

    properties = features[0].get("properties", {})

    result_city = properties.get("city", "")
    result_state = properties.get("state_code", "")

    if result_city.lower() != city.lower():
        return None

    if result_state.upper() != state.upper():
        return None

    return {
        "lat": properties.get("lat"),
        "lon": properties.get("lon"),
        "city": result_city,
        "state": result_state,
    }