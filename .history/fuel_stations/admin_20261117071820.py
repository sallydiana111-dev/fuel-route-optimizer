from django.contrib import admin
from .models import FuelStation


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):

    list_display = (
        "opis_truckstop_id",
        "name",
        "city",
        "state",
        "retail_price",
        "latitude",
        "longitude",
    )

    list_filter = (
        "state",
        "city",
    )

    search_fields = (
        "name",
        "city",
        "state",
        "address",
    )

    ordering = (
        "retail_price",
    )

    list_per_page = 50

    readonly_fields = (
        "created_at",
    )