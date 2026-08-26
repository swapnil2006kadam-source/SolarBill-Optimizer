import requests
import time


# =========================================================
# SOLAR GENERATION SERVICE
# =========================================================
# Uses Open-Meteo for solar radiation data.
# If Open-Meteo is unavailable/rate-limited, a fallback
# solar radiation value is used.
# =========================================================


# =========================================================
# CONFIGURATION
# =========================================================

SOLAR_CACHE_TIME = 6 * 60 * 60       # 6 hours
GEOCODE_CACHE_TIME = 24 * 60 * 60    # 24 hours

solar_cache = {}
location_cache = {}


# =========================================================
# FALLBACK SOLAR RADIATION
# =========================================================
# Approximate planning values in kWh/m²/day.
# These are used only when Open-Meteo is unavailable.
# =========================================================

FALLBACK_SOLAR = {

    "mumbai": 5.0,
    "pune": 5.2,
    "nagpur": 5.3,
    "nashik": 5.2,
    "thane": 5.0,
    "navi mumbai": 5.0,
    "aurangabad": 5.3,
    "solapur": 5.4,

    "delhi": 5.0,
    "new delhi": 5.0,

    "ahmedabad": 5.5,
    "surat": 5.3,

    "jaipur": 5.6,
    "jodhpur": 6.0,

    "hyderabad": 5.4,

    "bengaluru": 5.2,
    "bangalore": 5.2,

    "chennai": 5.2,

    "kolkata": 4.7,

    "bhopal": 5.4,
    "indore": 5.5,

    "lucknow": 5.0
}

DEFAULT_SOLAR = 5.0


# =========================================================
# CACHE HELPER
# =========================================================

def get_cache(cache, key, max_age):

    if key not in cache:
        return None

    saved_time, value = cache[key]

    if time.time() - saved_time > max_age:

        del cache[key]

        return None

    return value


def save_cache(cache, key, value):

    cache[key] = (
        time.time(),
        value
    )


# =========================================================
# GEOCODE CITY
# =========================================================

def get_city_coordinates(city):

    city_key = city.strip().lower()

    # Check cache
    cached = get_cache(
        location_cache,
        city_key,
        GEOCODE_CACHE_TIME
    )

    if cached:

        print(
            f"📍 Using cached coordinates for {city}"
        )

        return cached

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
    )

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
        "countryCode": "IN"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        # Rate limit
        if response.status_code == 429:

            print(
                "⚠️ Open-Meteo geocoding "
                "rate limited."
            )

            return None

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:
            return None

        location = results[0]

        result = {

            "name":
                location.get("name"),

            "latitude":
                location.get("latitude"),

            "longitude":
                location.get("longitude"),

            "state":
                location.get("admin1"),

            "country":
                location.get("country")
        }

        save_cache(
            location_cache,
            city_key,
            result
        )

        print(
            f"📍 Coordinates fetched for {city.upper()}"
        )

        return result

    except Exception as e:

        print(
            "⚠️ GEOCODING ERROR:",
            repr(e)
        )

        return None


# =========================================================
# GET SOLAR RADIATION
# =========================================================

def get_solar_radiation(
    latitude,
    longitude
):

    cache_key = (
        round(float(latitude), 4),
        round(float(longitude), 4)
    )

    # Check cache
    cached = get_cache(
        solar_cache,
        cache_key,
        SOLAR_CACHE_TIME
    )

    if cached:

        print(
            "☀️ Using cached solar radiation"
        )

        return cached

    url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "past_days": 30,

        "forecast_days": 0,

        "daily":
            "shortwave_radiation_sum",

        "timezone": "auto"
    }

    try:

        print(
            "☀️ Fetching solar radiation "
            "from Open-Meteo..."
        )

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        # -------------------------------------------------
        # IMPORTANT:
        # Render may receive 429.
        # Don't retry for 30 seconds.
        # Use fallback instead.
        # -------------------------------------------------

        if response.status_code == 429:

            print(
                "⚠️ Open-Meteo returned 429."
            )

            return None

        response.raise_for_status()

        data = response.json()

        values = data.get(
            "daily",
            {}
        ).get(
            "shortwave_radiation_sum",
            []
        )

        values = [
            value
            for value in values
            if value is not None
        ]

        if not values:
            return None

        # Average MJ/m²/day
        average_mj = (
            sum(values) / len(values)
        )

        # MJ/m² → kWh/m²
        average_kwh = (
            average_mj / 3.6
        )

        result = {

            "average_daily_radiation_mj":
                round(
                    average_mj,
                    2
                ),

            "average_daily_radiation_kwh":
                round(
                    average_kwh,
                    2
                ),

            "days_used":
                len(values),

            "source":
                "Open-Meteo"
        }

        save_cache(
            solar_cache,
            cache_key,
            result
        )

        print(
            "☀️ Solar radiation cached."
        )

        return result

    except Exception as e:

        print(
            "⚠️ SOLAR API ERROR:",
            repr(e)
        )

        return None


# =========================================================
# FALLBACK
# =========================================================

def get_fallback_solar(city):

    city_key = city.strip().lower()

    radiation = FALLBACK_SOLAR.get(
        city_key,
        DEFAULT_SOLAR
    )

    print(
        f"☀️ Using fallback solar radiation "
        f"for {city}: {radiation} kWh/m²/day"
    )

    return {

        "average_daily_radiation_mj":
            round(
                radiation * 3.6,
                2
            ),

        "average_daily_radiation_kwh":
            radiation,

        "days_used":
            30,

        "source":
            "Fallback estimate"
    }


# =========================================================
# ESTIMATE SOLAR GENERATION
# =========================================================

def estimate_solar_generation(
    solar_kw,
    city
):

    # -----------------------------------------------------
    # Get location
    # -----------------------------------------------------

    location = get_city_coordinates(
        city
    )

    # -----------------------------------------------------
    # Get solar radiation
    # -----------------------------------------------------

    radiation = None

    if location:

        radiation = get_solar_radiation(
            location["latitude"],
            location["longitude"]
        )

    # -----------------------------------------------------
    # Fallback if API fails
    # -----------------------------------------------------

    if not radiation:

        print(
            "⚠️ Open-Meteo unavailable."
        )

        radiation = get_fallback_solar(
            city
        )

    # -----------------------------------------------------
    # Location fallback
    # -----------------------------------------------------

    if not location:

        location = {

            "name": city.title(),

            "latitude": None,

            "longitude": None,

            "state": None,

            "country": "India"
        }

    # -----------------------------------------------------
    # Performance ratio
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
    # Yearly generation
    # -----------------------------------------------------

    yearly_generation = (
        daily_generation * 365
    )

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    return {

        "city":
            location["name"],

        "state":
            location["state"],

        "latitude":
            location["latitude"],

        "longitude":
            location["longitude"],

        "solar_kw":
            solar_kw,

        "average_daily_radiation":
            radiation[
                "average_daily_radiation_kwh"
            ],

        "days_used":
            radiation[
                "days_used"
            ],

        "daily_generation_kwh":
            round(
                daily_generation,
                2
            ),

        "monthly_generation_kwh":
            round(
                monthly_generation,
                2
            ),

        "yearly_generation_kwh":
            round(
                yearly_generation,
                2
            ),

        "performance_ratio":
            PERFORMANCE_RATIO,

        "radiation_source":
            radiation.get(
                "source",
                "Unknown"
            )
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "☀️ SOLAR GENERATION SERVICE TEST"
    )

    for city in [
        "Mumbai",
        "Pune",
        "Nagpur"
    ]:

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
                "Radiation:",
                result[
                    "average_daily_radiation"
                ],
                "kWh/m²/day"
            )

            print(
                "Source:",
                result[
                    "radiation_source"
                ]
            )

            print(
                "Daily generation:",
                result[
                    "daily_generation_kwh"
                ],
                "kWh"
            )

            print(
                "Monthly generation:",
                result[
                    "monthly_generation_kwh"
                ],
                "kWh"
            )

            print(
                "Yearly generation:",
                result[
                    "yearly_generation_kwh"
                ],
                "kWh"
            )

        except Exception as e:

            print(
                f"{city} → ❌ ERROR:",
                e
            )