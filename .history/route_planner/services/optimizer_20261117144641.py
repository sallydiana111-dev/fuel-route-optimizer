import math
from decimal import Decimal


MAX_RANGE_MILES = 500
MILES_PER_GALLON = 10

TANK_CAPACITY_GALLONS = (
    MAX_RANGE_MILES / MILES_PER_GALLON
)


class FuelOptimizationError(Exception):
    """Raised when a valid fuel strategy cannot be calculated."""


def optimize_fuel_stops(
    route_distance_miles,
    stations,
    starting_fuel_gallons=50,
):
    """
    Find a cost-effective fuel strategy along a route.

    Each station must contain:
        - id
        - name
        - distance_from_start_miles
        - retail_price
        - latitude
        - longitude

    Assumptions:
        - The vehicle starts with the specified fuel quantity.
        - Tank capacity is 50 gallons.
        - Fuel consumption is 10 miles per gallon.
        - Initial fuel is already in the vehicle.
        - The reported cost covers fuel purchased along the route.
    """

    if route_distance_miles <= 0:
        raise FuelOptimizationError(
            "Route distance must be greater than zero."
        )

    if starting_fuel_gallons < 0:
        raise FuelOptimizationError(
            "Starting fuel cannot be negative."
        )

    if starting_fuel_gallons > TANK_CAPACITY_GALLONS:
        raise FuelOptimizationError(
            "Starting fuel exceeds tank capacity."
        )

    # Keep only stations with verified prices and valid positions.
    valid_stations = []

    for station in stations:

        price = station.get("retail_price")
        position = station.get("distance_from_start_miles")

        if price is None or position is None:
            continue

        price = Decimal(str(price))

        if price <= 0:
            continue

        if not 0 < position < route_distance_miles:
            continue

        valid_stations.append({
            **station,
            "retail_price": price,
            "distance_from_start_miles": float(position),
        })

    valid_stations.sort(
        key=lambda item: item["distance_from_start_miles"]
    )

    # Add the starting point and destination.
    nodes = [
        {
            "type": "start",
            "distance": 0,
        }
    ]

    for station in valid_stations:
        nodes.append({
            "type": "station",
            "distance": station["distance_from_start_miles"],
            "station": station,
        })

    nodes.append({
        "type": "destination",
        "distance": float(route_distance_miles),
    })

    # Fuel quantities are represented in whole gallons.
    capacity = int(TANK_CAPACITY_GALLONS)

    initial_fuel = int(starting_fuel_gallons)

    # Each state represents the cheapest cost of arriving
    # at a node with a particular quantity of fuel.
    infinity = float("inf")

    costs = [
        [infinity] * (capacity + 1)
        for _ in nodes
    ]

    previous = [
        [None] * (capacity + 1)
        for _ in nodes
    ]

    costs[0][initial_fuel] = 0

    # Dynamic programming.
    for i, current in enumerate(nodes):

        if current["type"] == "destination":
            continue

        for fuel in range(capacity + 1):

            current_cost = costs[i][fuel]

            if current_cost == infinity:
                continue

            station_price = None

            if current["type"] == "station":
                station_price = current["station"]["retail_price"]

            max_purchase = (
                capacity - fuel
                if station_price is not None
                else 0
            )

            for purchase in range(max_purchase + 1):

                available_fuel = fuel + purchase

                purchase_cost = 0

                if purchase > 0:
                    purchase_cost = float(
                        station_price * purchase
                    )

                total_cost = (
                    current_cost + purchase_cost
                )

                # Try travelling to every reachable later node.
                for j in range(i + 1, len(nodes)):

                    next_node = nodes[j]

                    distance = (
                        next_node["distance"]
                        - current["distance"]
                    )

                    required_fuel = math.ceil(
                        distance / MILES_PER_GALLON
                    )

                    if required_fuel > available_fuel:
                        break

                    remaining_fuel = (
                        available_fuel - required_fuel
                    )

                    if total_cost < costs[j][remaining_fuel]:

                        costs[j][remaining_fuel] = total_cost

                        previous[j][remaining_fuel] = {
                            "previous_node": i,
                            "previous_fuel": fuel,
                            "purchase": purchase,
                        }

    # Find the cheapest state at the destination.
    destination_index = len(nodes) - 1

    best_fuel = min(
        range(capacity + 1),
        key=lambda fuel: costs[destination_index][fuel],
    )

    best_cost = costs[destination_index][best_fuel]

    if best_cost == infinity:
        raise FuelOptimizationError(
            "No feasible fuel strategy was found. "
            "More verified fuel stations may be required."
        )

    # Reconstruct the selected refuelling stops.
    selected_stops = []

    current_node = destination_index
    current_fuel = best_fuel

    while current_node != 0:

        step = previous[current_node][current_fuel]

        if step is None:
            raise FuelOptimizationError(
                "Could not reconstruct the fuel strategy."
            )

        previous_node = step["previous_node"]
        previous_fuel = step["previous_fuel"]
        purchase = step["purchase"]

        if purchase > 0:

            station = nodes[previous_node]["station"]

            selected_stops.append({
                "station_id": station.get("id"),
                "station_name": station.get("name"),
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
                "distance_from_start_miles": (
                    station["distance_from_start_miles"]
                ),
                "fuel_price_per_gallon": float(
                    station["retail_price"]
                ),
                "gallons_to_purchase": purchase,
                "purchase_cost": round(
                    float(
                        station["retail_price"] * purchase
                    ),
                    2,
                ),
            })

        current_node = previous_node
        current_fuel = previous_fuel

    selected_stops.reverse()

    return {
        "route_distance_miles": round(
            float(route_distance_miles), 2
        ),
        "fuel_consumption_mpg": MILES_PER_GALLON,
        "maximum_range_miles": MAX_RANGE_MILES,
        "tank_capacity_gallons": TANK_CAPACITY_GALLONS,
        "starting_fuel_gallons": starting_fuel_gallons,
        "fuel_stops": selected_stops,
        "number_of_stops": len(selected_stops),
        "fuel_purchase_cost": round(best_cost, 2),
        "cost_scope": (
            "Fuel purchased along the route. "
            "Fuel already in the vehicle at departure is excluded."
        ),
    }