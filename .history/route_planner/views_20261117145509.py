from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)

from route_planner.serializers import (
    RoutePlanningSerializer,
)

from route_planner.services.planner import (
    plan_fuel_route,
)

from route_planner.services.routing import RoutingError

from fuel_stations.services.geoapify import GeoapifyError

from route_planner.services.optimizer import (
    FuelOptimizationError,
)


class RoutePlanningView(APIView):

    @extend_schema(
        request=RoutePlanningSerializer,
        responses={
            200: OpenApiResponse(
                description="Route and fuel optimization results."
            ),
            400: OpenApiResponse(
                description="Invalid request or infeasible fuel plan."
            ),
            502: OpenApiResponse(
                description="External routing or geocoding service failure."
            ),
        },
        description="Calculate a driving route and optimize fuel stops.",
    )
    def post(self, request):

        serializer = RoutePlanningSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:

            result = plan_fuel_route(
                start_lat=data["start_latitude"],
                start_lon=data["start_longitude"],
                end_lat=data["end_latitude"],
                end_lon=data["end_longitude"],
                starting_fuel_gallons=data[
                    "starting_fuel_gallons"
                ],
            )

            distance = result["route"]["distance_miles"]

            result["fuel_consumption"] = {
                "miles_per_gallon": 10,
                "estimated_gallons_consumed": round(
                    distance / 10,
                    2,
                ),
                "fuel_purchase_cost_excludes_initial_tank": True,
            }

            return Response(
                result,
                status=status.HTTP_200_OK,
            )

        except FuelOptimizationError as exc:

            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except (RoutingError, GeoapifyError) as exc:

            return Response(
                {"error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )