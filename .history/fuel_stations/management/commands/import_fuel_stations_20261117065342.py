import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from fuel_stations.models import FuelStation


class Command(BaseCommand):
    help = "Import fuel station records from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/fuel-prices-for-be-assessment.csv",
            help="Path to the fuel prices CSV file.",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of records to insert per batch.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        batch_size = options["batch_size"]

        if batch_size < 1:
            raise CommandError("Batch size must be greater than zero.")

        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path

        if not file_path.exists():
            raise CommandError(
                f"CSV file not found: {file_path}"
            )

        self.stdout.write(
            self.style.NOTICE("Starting fuel station import...")
        )

        stations = []
        seen_records = set()

        imported = 0
        duplicates = 0
        invalid = 0

        expected_columns = {
            "OPIS Truckstop ID",
            "Truckstop Name",
            "Address",
            "City",
            "State",
            "Rack ID",
            "Retail Price",
        }

        try:
            with file_path.open(
                mode="r",
                encoding="utf-8-sig",
                newline="",
            ) as csv_file:

                reader = csv.DictReader(csv_file)

                if not reader.fieldnames:
                    raise CommandError("CSV file has no header.")

                missing_columns = expected_columns - set(reader.fieldnames)

                if missing_columns:
                    raise CommandError(
                        f"Missing CSV columns: {', '.join(sorted(missing_columns))}"
                    )

                with transaction.atomic():

                    for row_number, row in enumerate(reader, start=2):
                        try:
                            opis_id = int(row["OPIS Truckstop ID"])
                            rack_id = int(row["Rack ID"])

                            name = row["Truckstop Name"].strip()
                            address = row["Address"].strip()
                            city = row["City"].strip()
                            state = row["State"].strip().upper()

                            price = Decimal(
                                row["Retail Price"].strip()
                            )

                            if (
                                not name
                                or not address
                                or not city
                                or len(state) != 2
                                or not price.is_finite()
                                or price <= 0
                                or opis_id < 0
                                or rack_id < 0
                            ):
                                raise ValueError("Invalid field values.")

                            record_key = (
                                opis_id,
                                name,
                                address,
                                city,
                                state,
                                rack_id,
                                price,
                            )

                            if record_key in seen_records:
                                duplicates += 1
                                continue

                            seen_records.add(record_key)

                            stations.append(
                                FuelStation(
                                    opis_truckstop_id=opis_id,
                                    name=name,
                                    address=address,
                                    city=city,
                                    state=state,
                                    rack_id=rack_id,
                                    retail_price=price,
                                )
                            )

                            if len(stations) >= batch_size:
                                FuelStation.objects.bulk_create(
                                    stations,
                                    batch_size=batch_size,
                                )

                                imported += len(stations)
                                stations.clear()

                        except (
                            ValueError,
                            InvalidOperation,
                            TypeError,
                        ):
                            invalid += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Skipping invalid row {row_number}"
                                )
                            )

                    if stations:
                        FuelStation.objects.bulk_create(
                            stations,
                            batch_size=batch_size,
                        )

                        imported += len(stations)

        except OSError as exc:
            raise CommandError(f"Could not read CSV file: {exc}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("Fuel station import completed!")
        )

        self.stdout.write(f"Imported records: {imported}")
        self.stdout.write(f"Duplicate records skipped: {duplicates}")
        self.stdout.write(f"Invalid records skipped: {invalid}")
        self.stdout.write(
            f"Total database records: {FuelStation.objects.count()}"
        )