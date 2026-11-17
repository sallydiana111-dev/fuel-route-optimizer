from django.db import models
from django.utils import timezone


class FuelStation(models.Model):

    class GeocodingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        EXACT = "EXACT", "Exact match"
        APPROXIMATE = "APPROXIMATE", "Approximate match"
        REVIEW = "REVIEW", "Needs review"
        UNMATCHED = "UNMATCHED", "Unmatched"

    opis_truckstop_id = models.PositiveBigIntegerField()

    name = models.CharField(max_length=255)

    address = models.CharField(max_length=255)

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=2)

    rack_id = models.PositiveIntegerField()

    retail_price = models.DecimalField(
        max_digits=12,
        decimal_places=8
    )

    # Geographic coordinates
    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )

    # Geocoding information
    geocoding_status = models.CharField(
        max_length=20,
        choices=GeocodingStatus.choices,
        default=GeocodingStatus.PENDING
    )

    geocoding_source = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    geocoding_place_id = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    geocoding_confidence = models.FloatField(
        null=True,
        blank=True
    )

    geocoding_notes = models.TextField(
        blank=True,
        default=""
    )

    geocoded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fuel_stations"

        indexes = [
            models.Index(fields=["state", "city"]),
            models.Index(fields=["retail_price"]),
            models.Index(fields=["geocoding_status"]),
        ]

        ordering = ["retail_price"]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"