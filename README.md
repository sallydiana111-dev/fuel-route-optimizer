# Fuel Route Optimizer API

A Django REST Framework application that calculates driving routes, discovers fuel stations along the route, and identifies cost-effective refuelling opportunities.

## Features

- Driving route calculation using OSRM.
- Fuel station discovery using Geoapify.
- Fuel station matching against a supplied fuel-price dataset.
- Fuel-stop optimization using dynamic programming.
- Maximum vehicle range of 500 miles.
- Fuel consumption assumption of 10 miles per gallon.
- REST API with Swagger and ReDoc documentation.
- Conservative station matching to avoid assigning incorrect fuel prices.

## Technology Stack

- Python 3.13
- Django
- Django REST Framework
- SQLite
- Geoapify Places API
- OSRM Routing API
- drf-spectacular

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd fuel-route-optimizer
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEOAPIFY_API_KEY=your_geoapify_api_key
```

Run database migrations:

```bash
python manage.py migrate
```

Import the supplied fuel-price dataset:

```bash
python manage.py import_fuel_stations --file data/fuel-prices-for-be-assessment.csv
```

Start the development server:

```bash
python manage.py runserver
```

## API Endpoint

**POST** `/api/v1/routes/plan/`

Example request:

```json
{
    "start_latitude": 32.7767,
    "start_longitude": -96.7970,
    "end_latitude": 30.2672,
    "end_longitude": -97.7431,
    "starting_fuel_gallons": 50
}
```

## API Documentation

Swagger:

`/api/docs/`

ReDoc:

`/api/redoc/`

OpenAPI schema:

`/api/schema/`

## Fuel Optimization Assumptions

- Maximum vehicle range: 500 miles.
- Fuel consumption: 10 MPG.
- Tank capacity: 50 gallons.
- Starting fuel defaults to a full tank.
- Initial fuel cost is excluded from additional fuel purchases.
- Only exact station-price matches are used automatically.
- Uncertain matches are returned for review.

## External Services

- OSRM: Driving route calculation.
- Geoapify: Fuel station discovery and geocoding.

## Limitations

- Station coordinates and matching confidence depend on available map data.
- Fuel prices depend on the supplied dataset and may not represent live prices.
- The public OSRM demo server is intended for reasonable-use testing, not production workloads.
- Station positions along the route are approximate.
- Unverified station prices are not used in automatic optimization.