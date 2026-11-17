from django.urls import path

from route_planner.views import RoutePlanningView


urlpatterns = [
    path(
        "routes/plan/",
        RoutePlanningView.as_view(),
        name="route-planning",
    ),
]