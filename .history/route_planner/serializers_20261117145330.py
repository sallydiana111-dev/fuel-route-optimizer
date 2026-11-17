from rest_framework import serializers


class RoutePlanningSerializer(serializers.Serializer):

    start_latitude = serializers.FloatField(
        min_value=-90,
        max_value=90,
    )

    start_longitude = serializers.FloatField(
        min_value=-180,
        max_value=180,
    )

    end_latitude = serializers.FloatField(
        min_value=-90,
        max_value=90,
    )

    end_longitude = serializers.FloatField(
        min_value=-180,
        max_value=180,
    )

    starting_fuel_gallons = serializers.FloatField(
        min_value=0,
        max_value=50,
        default=50,
    )