import requests

OSRM_BASE_URL = "https://router.project-osrm.org"


class RoutingError(Exception):
    """Raised when route calculation fails."""


def get_route(start_lat, start_lon, end_lat, end_lon):
    """
    Calculate a driving route between two coordinates.

    Returns route distance, duration and GeoJSON geometry.
    Uses one OSRM API request.
    """

    coordinates = [start_lat, start_lon, end_lat, end_lon]

    if not all(
        isinstance(value, (int, float))
        for value in coordinates
    ):
        raise ValueError("Coordinates must be numeric.")

    if not -90 <= start_lat <= 90:
        raise ValueError("Invalid starting latitude.")

    if not -90 <= end_lat <= 90:
        raise ValueError("Invalid destination latitude.")

    if not -180 <= start_lon <= 180:
        raise ValueError("Invalid starting longitude.")

    if not -180 <= end_lon <= 180:
        raise ValueError("Invalid destination longitude.")

    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
        "alternatives": "false",
    }

    headers = {
        "User-Agent": "FuelRouteOptimizer/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        raise RoutingError(
            f"Routing request failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise RoutingError(
            "Routing service returned invalid JSON."
        ) from exc

    if data.get("code") != "Ok":
        raise RoutingError(
            f"Could not calculate route: {data.get('code')}"
        )

    routes = data.get("routes", [])

    if not routes:
        raise RoutingError("No route was returned.")

    route = routes[0]

    distance_meters = route["distance"]
    duration_seconds = route["duration"]

    return {
        "distance_miles": round(
            distance_meters / 1609.344, 2
        ),
        "duration_hours": round(
            duration_seconds / 3600, 2
        ),
        "geometry": route["geometry"],
    }