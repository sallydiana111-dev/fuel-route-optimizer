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

def search_fuel_stations_along_route(
    route_geometry,
    buffer=2000,
    limit=100,
):
    """
    Find fuel stations near a driving route.

    route_geometry must be a GeoJSON LineString.
    Buffer is measured in meters.
    """

    api_key = settings.GEOAPIFY_API_KEY

    if not api_key:
        raise GeoapifyError(
            "Geoapify API key is not configured."
        )

    if not isinstance(route_geometry, dict):
        raise ValueError("Route geometry must be a dictionary.")

    if route_geometry.get("type") != "LineString":
        raise ValueError("Route geometry must be a LineString.")

    coordinates = route_geometry.get("coordinates", [])

    if len(coordinates) < 2:
        raise ValueError("Route must contain at least two coordinates.")

    if len(coordinates) > 10000:
        raise ValueError(
            "Route contains too many coordinates. "
            "Simplify the geometry before searching."
        )

    for coordinate in coordinates:
        if (
            not isinstance(coordinate, (list, tuple))
            or len(coordinate) < 2
        ):
            raise ValueError("Invalid route coordinate.")

        longitude, latitude = coordinate[:2]

        if not -180 <= longitude <= 180:
            raise ValueError("Invalid route longitude.")

        if not -90 <= latitude <= 90:
            raise ValueError("Invalid route latitude.")

    if not 0 < buffer <= 100000:
        raise ValueError("Buffer must be between 1 and 100000 meters.")

    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")

    payload = {
        "categories": ["service.vehicle.fuel"],
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
            params={"apiKey": api_key},
            json=payload,
            headers={"Content-Type": "application/json"},
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

def search_fuel_stations_along_route(
    route_geometry,
    buffer=2000,
    limit=100,
):
    """
    Find fuel stations near a driving route.
    Uses one Geoapify Places API request.
    """

    api_key = settings.GEOAPIFY_API_KEY

    if not api_key:
        raise GeoapifyError(
            "Geoapify API key is not configured."
        )

    if not isinstance(route_geometry, dict):
        raise ValueError("Route geometry must be a dictionary.")

    if route_geometry.get("type") != "LineString":
        raise ValueError("Route geometry must be a LineString.")

    coordinates = route_geometry.get("coordinates", [])

    if len(coordinates) < 2:
        raise ValueError("Route needs at least two coordinates.")

    if len(coordinates) > 10000:
        raise ValueError("Too many route coordinates.")

    if not 0 < buffer <= 100000:
        raise ValueError("Invalid buffer distance.")

    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")

    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            raise ValueError("Invalid route coordinate.")

        lon, lat = coordinate[:2]

        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError("Coordinates must be numeric.")

        if not -180 <= lon <= 180:
            raise ValueError("Invalid longitude.")

        if not -90 <= lat <= 90:
            raise ValueError("Invalid latitude.")

    payload = {
        "categories": ["service.vehicle.fuel"],
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
            params={"apiKey": api_key},
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
