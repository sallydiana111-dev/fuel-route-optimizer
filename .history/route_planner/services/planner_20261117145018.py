from fuel_stations.models import FuelStation

from fuel_stations.services.matching import compare_station
from fuel_stations.services.geoapify import (
    search_fuel_stations_along_route,
)

from route_planner.services.routing import get_route
from route_planner.services.route_geometry import (
    locate_stations_on_route,
)

from route_planner.services.optimizer import (
    optimize_fuel_stops,
)


def match_route_stations(located_stations):
    """
    Match discovered Geoapify stations against database records.

    Only exact matches are accepted for fuel-price optimization.
    """

    verified_stations = []

    for candidate in located_stations:

        city = candidate.get("city")
        state = candidate.get("state_code")

        if not city or not state:
            continue

        database_stations = FuelStation.objects.filter(
            city__iexact=city,
            state__iexact=state,
        )

        best_match = None

        for station in database_stations:

            match = compare_station(
                station,
                candidate,
            )

            if match["status"] == "EXACT":
                best_match = station
                break

        if best_match is None:
            continue

        verified_stations.append({
            "id": best_match.id,
            "name": best_match.name,
            "latitude": candidate.get("lat"),
            "longitude": candidate.get("lon"),
            "distance_from_start_miles": (
                candidate["distance_from_start_miles"]
            ),
            "retail_price": best_match.retail_price,
            "geocoding_status": "EXACT",
        })

    return verified_stations


def plan_fuel_route(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    starting_fuel_gallons=50,
):
    """
    Calculate a driving route and its fuel optimization.
    """

    # 1. Calculate the driving route.
    route = get_route(
        start_lat,
        start_lon,
        end_lat,
        end_lon,
    )

    # 2. Discover fuel stations along the route.
    discovered_stations = search_fuel_stations_along_route(
        route_geometry=route["geometry"],
        buffer=2000,
        limit=100,
    )

    # 3. Locate discovered stations along the route.
    located_stations = locate_stations_on_route(
        route_geometry=route["geometry"],
        stations=discovered_stations,
    )

    # 4. Match stations against the fuel-price database.
    verified_stations = match_route_stations(
        located_stations
    )

    # 5. Optimize fuel purchases.
    optimization = optimize_fuel_stops(
        route_distance_miles=route["distance_miles"],
        stations=verified_stations,
        starting_fuel_gallons=starting_fuel_gallons,
    )

    return {
        "route": {
            "distance_miles": route["distance_miles"],
            "duration_hours": route["duration_hours"],
            "geometry": route["geometry"],
        },
        "station_summary": {
            "discovered": len(discovered_stations),
            "located": len(located_stations),
            "verified_price_matches": len(verified_stations),
        },
        "verified_stations": verified_stations,
        "optimization": optimization,
    }