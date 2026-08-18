import requests


# =========================================================
# SOLAR GENERATION SERVICE
# =========================================================
# Uses:
# Open-Meteo Geocoding API
# Open-Meteo Solar Radiation / Weather API
#
# The result is an ESTIMATE, not a guaranteed production value.
# =========================================================


# =========================================================
# GEOCODE CITY
# =========================================================

def get_city_coordinates(city):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
        "countryCode": "IN"
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    results = data.get(
        "results",
        []
    )

    if not results:
        return None

    location = results[0]

    return {
        "name": location.get("name"),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "state": location.get("admin1"),
        "country": location.get("country")
    }


# =========================================================
# GET SOLAR RADIATION
# =========================================================

def get_solar_radiation(
    latitude,
    longitude
):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # Last 30 days of solar radiation
        "past_days": 30,

        # We don't need future forecast for this calculation
        "forecast_days": 0,

        "daily": "shortwave_radiation_sum",

        "timezone": "auto"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    daily = data.get(
        "daily",
        {}
    )

    radiation_values = daily.get(
        "shortwave_radiation_sum",
        []
    )

    # Remove missing values
    radiation_values = [
        value
        for value in radiation_values
        if value is not None
    ]

    if not radiation_values:
        return None

    # Average daily solar radiation
    average_mj = sum(
        radiation_values
    ) / len(
        radiation_values
    )

    # Convert MJ/m² → kWh/m²
    average_kwh = average_mj / 3.6

    return {
        "average_daily_radiation_mj": round(
            average_mj,
            2
        ),

        "average_daily_radiation_kwh": round(
            average_kwh,
            2
        ),

        "days_used": len(
            radiation_values
        )
    }


# =========================================================
# ESTIMATE SOLAR GENERATION
# =========================================================

def estimate_solar_generation(
    solar_kw,
    city
):

    # -----------------------------------------------------
    # Get coordinates
    # -----------------------------------------------------

    location = get_city_coordinates(
        city
    )

    if not location:

        raise ValueError(
            f"Could not find location for {city}."
        )


    # -----------------------------------------------------
    # Get solar radiation
    # -----------------------------------------------------

    radiation = get_solar_radiation(
        location["latitude"],
        location["longitude"]
    )

    if not radiation:

        raise ValueError(
            "Solar radiation data is unavailable."
        )


    # -----------------------------------------------------
    # Performance ratio
    # -----------------------------------------------------
    #
    # This accounts approximately for:
    #
    # inverter losses
    # wiring losses
    # temperature losses
    # dust
    # other system losses
    #
    # This is an estimate, not a manufacturer guarantee.
    # -----------------------------------------------------

    PERFORMANCE_RATIO = 0.80


    # -----------------------------------------------------
    # Daily generation
    # -----------------------------------------------------

    daily_generation = (
        solar_kw
        *
        radiation[
            "average_daily_radiation_kwh"
        ]
        *
        PERFORMANCE_RATIO
    )


    # -----------------------------------------------------
    # Monthly generation
    # -----------------------------------------------------

    monthly_generation = (
        daily_generation * 30
    )


    # -----------------------------------------------------
    # Yearly approximation
    # -----------------------------------------------------

    yearly_generation = (
        daily_generation * 365
    )


    return {

        "city": location["name"],

        "state": location["state"],

        "latitude": location["latitude"],

        "longitude": location["longitude"],

        "solar_kw": solar_kw,

        "average_daily_radiation": radiation[
            "average_daily_radiation_kwh"
        ],

        "days_used": radiation[
            "days_used"
        ],

        "daily_generation_kwh": round(
            daily_generation,
            2
        ),

        "monthly_generation_kwh": round(
            monthly_generation,
            2
        ),

        "yearly_generation_kwh": round(
            yearly_generation,
            2
        ),

        "performance_ratio": PERFORMANCE_RATIO
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("☀️ SOLAR GENERATION SERVICE TEST")
    print("----------------------------------------")

    test_cities = [
        "Mumbai",
        "Pune",
        "Nagpur"
    ]

    for city in test_cities:

        try:

            result = estimate_solar_generation(
                solar_kw=2,
                city=city
            )

            print()
            print(
                f"City: {result['city']}"
            )

            print(
                f"State: {result['state']}"
            )

            print(
                f"Coordinates: "
                f"{result['latitude']}, "
                f"{result['longitude']}"
            )

            print(
                "Average solar radiation:",
                f"{result['average_daily_radiation']} "
                "kWh/m²/day"
            )

            print(
                "Daily generation:",
                f"{result['daily_generation_kwh']} kWh"
            )

            print(
                "Monthly generation:",
                f"{result['monthly_generation_kwh']} kWh"
            )

            print(
                "Yearly generation:",
                f"{result['yearly_generation_kwh']} kWh"
            )

            print(
                "Days used:",
                result["days_used"]
            )

        except Exception as e:

            print(
                f"{city} → ❌ ERROR:",
                e
            )

    print()
    print("----------------------------------------")