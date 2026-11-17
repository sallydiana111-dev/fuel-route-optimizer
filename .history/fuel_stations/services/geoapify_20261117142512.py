import json
import requests

from django.conf import settings


GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"

FUEL_CATEGORY = "service.vehicle.fuel"


class GeoapifyError(Exception):
    """Raised when a Geoapify request fails."""


def get_api_key():
    """Retrieve the Geoapify API key from Django settings."""

    api_key = settings.GEOAPIFY_API_KEY

    if not api_key:
        raise GeoapifyError(
            "Geoapify API key is not configured."
        )

    return api_key


def search_fuel_stations(
    latitude,
    longitude,
    radius=5000,
    limit=20
):
    """
    Find fuel stations around a geographic location.

    Returns a list of Geoapify place properties.
    """

    if not isinstance(latitude, (int, float)):
        raise ValueError("Latitude must be numeric.")

    if not isinstance(longitude, (int, float)):
        raise ValueError("Longitude must be numeric.")

    if not -90 <= latitude <= 90:
        raise ValueError("Invalid latitude.")

    if not -180 <= longitude <= 180:
        raise ValueError("Invalid longitude.")

    if not 1 <= radius <= 50000:
        raise ValueError(
            "Radius must be between 1 and 50000 meters."
        )

    if not 1 <= limit <= 100:
        raise ValueError(
            "Limit must be between 1 and 100."
        )

    params = {
        "categories": FUEL_CATEGORY,
        "filter": f"circle:{longitude},{latitude},{radius}",
        "limit": limit,
        "apiKey": get_api_key(),
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
            "Geoapify returned invalid JSON."
        ) from exc

    return [
        feature.get("properties", {})
        for feature in data.get("features", [])
    ]


def search_geocoding_location(city, state):
    """
    Find geographic coordinates for a US city.

    These coordinates are search origins only.
    They do not establish an individual fuel station's location.
    """

    if not city or not state:
        raise ValueError("City and state are required.")

    params = {
        "text": f"{city}, {state}, USA",
        "filter": "countrycode:us",
        "limit": 1,
        "apiKey": get_api_key(),
    }

    try:
        response = requests.get(
            GEOAPIFY_GEOCODING_URL,
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

    latitude = properties.get("lat")
    longitude = properties.get("lon")

    if latitude is None or longitude is None:
        return None

    return {
        "lat": latitude,
        "lon": longitude,
        "city": result_city,
        "state": result_state,
    }


def search_fuel_stations_along_route(
    route_geometry,
    buffer=2000,
    limit=100,
):
    """
    Find fuel stations near a driving route.

    Uses one Geoapify Places API POST request.

    Args:
        route_geometry: GeoJSON LineString.
        buffer: Search corridor in meters.
        limit: Maximum number of results (1-500).

    Returns:
        List of Geoapify place properties.
    """

    if not isinstance(route_geometry, dict):
        raise ValueError(
            "Route geometry must be a dictionary."
        )

    if route_geometry.get("type") != "LineString":
        raise ValueError(
            "Route geometry must be a LineString."
        )

    coordinates = route_geometry.get("coordinates", [])

    if not isinstance(coordinates, list):
        raise ValueError(
            "Route coordinates must be a list."
        )

    if len(coordinates) < 2:
        raise ValueError(
            "Route must contain at least two coordinates."
        )

    if len(coordinates) > 10000:
        raise ValueError(
            "Route exceeds the 10000-coordinate limit."
        )

    if not 0 < buffer <= 100000:
        raise ValueError(
            "Buffer must be between 1 and 100000 meters."
        )

    if not 1 <= limit <= 500:
        raise ValueError(
            "Limit must be between 1 and 500."
        )

    # Validate GeoJSON coordinates.
    for coordinate in coordinates:

        if (
            not isinstance(coordinate, (list, tuple))
            or len(coordinate) < 2
        ):
            raise ValueError(
                "Invalid route coordinate."
            )

        longitude, latitude = coordinate[:2]

        if not isinstance(longitude, (int, float)):
            raise ValueError(
                "Longitude must be numeric."
            )

        if not isinstance(latitude, (int, float)):
            raise ValueError(
                "Latitude must be numeric."
            )

        if not -180 <= longitude <= 180:
            raise ValueError("Invalid longitude.")

        if not -90 <= latitude <= 90:
            raise ValueError("Invalid latitude.")

    # Check Geoapify's inline geometry size limit.
    geometry_size = len(
        json.dumps(
            route_geometry,
            separators=(",", ":")
        ).encode("utf-8")
    )

    if geometry_size > 102400:
        raise ValueError(
            "Route geometry exceeds the 102400-byte limit."
        )

    payload = {
        "categories": [FUEL_CATEGORY],
        "filter": {
            "type": "polyline",
            "geometry": route_geometry,
            "buffer": buffer,
        },
        "limit": limit,
        "lang": "en",
    }

    try:
        response = requests.post(
            GEOAPIFY_PLACES_URL,
            params={
                "apiKey": get_api_key()
            },
            json=payload,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        raise GeoapifyError(
            f"Geoapify route search failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise GeoapifyError(
            "Geoapify returned invalid JSON."
        ) from exc

    return [
        feature.get("properties", {})
        for feature in data.get("features", [])
    ]