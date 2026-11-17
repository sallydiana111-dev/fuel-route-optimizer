import math


EARTH_RADIUS_MILES = 3958.7613


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two geographic coordinates."""

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_MILES
        * math.asin(math.sqrt(a))
    )


def project_point_onto_segment(
    point_lat,
    point_lon,
    start_lat,
    start_lon,
    end_lat,
    end_lon,
):
    """Find the closest point on a route segment."""

    reference_lat = math.radians(point_lat)

    scale_x = math.cos(reference_lat)

    px = math.radians(point_lon) * scale_x
    py = math.radians(point_lat)

    ax = math.radians(start_lon) * scale_x
    ay = math.radians(start_lat)

    bx = math.radians(end_lon) * scale_x
    by = math.radians(end_lat)

    dx = bx - ax
    dy = by - ay

    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        t = 0
    else:
        t = (
            (px - ax) * dx + (py - ay) * dy
        ) / length_squared

        t = max(0, min(1, t))

    projected_lat = start_lat + t * (
        end_lat - start_lat
    )

    projected_lon = start_lon + t * (
        end_lon - start_lon
    )

    distance = haversine_distance(
        point_lat,
        point_lon,
        projected_lat,
        projected_lon,
    )

    return t, distance


def locate_stations_on_route(
    route_geometry,
    stations,
    max_distance_miles=1.25,
):
    """
    Calculate each station's approximate position along a route.

    GeoJSON coordinates use [longitude, latitude].

    Returns stations with:
        distance_from_start_miles
        distance_from_route_miles
    """

    coordinates = route_geometry.get("coordinates", [])

    if len(coordinates) < 2:
        raise ValueError(
            "Route must contain at least two coordinates."
        )

    route_segments = []
    cumulative_distance = 0.0

    for index in range(len(coordinates) - 1):

        lon1, lat1 = coordinates[index][:2]
        lon2, lat2 = coordinates[index + 1][:2]

        segment_distance = haversine_distance(
            lat1,
            lon1,
            lat2,
            lon2,
        )

        route_segments.append({
            "start_lat": lat1,
            "start_lon": lon1,
            "end_lat": lat2,
            "end_lon": lon2,
            "start_distance": cumulative_distance,
            "segment_distance": segment_distance,
        })

        cumulative_distance += segment_distance

    located_stations = []

    for station in stations:

        latitude = station.get("lat")
        longitude = station.get("lon")

        if latitude is None or longitude is None:
            continue

        best_distance = float("inf")
        best_route_position = None

        for segment in route_segments:

            t, distance_from_route = (
                project_point_onto_segment(
                    latitude,
                    longitude,
                    segment["start_lat"],
                    segment["start_lon"],
                    segment["end_lat"],
                    segment["end_lon"],
                )
            )

            if distance_from_route < best_distance:

                best_distance = distance_from_route

                best_route_position = (
                    segment["start_distance"]
                    + t * segment["segment_distance"]
                )

        if (
            best_route_position is None
            or best_distance > max_distance_miles
        ):
            continue

        located_stations.append({
            **station,
            "distance_from_start_miles": round(
                best_route_position, 2
            ),
            "distance_from_route_miles": round(
                best_distance, 3
            ),
        })

    located_stations.sort(
        key=lambda station: (
            station["distance_from_start_miles"]
        )
    )

    return located_stations