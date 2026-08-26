import requests
import time
from functools import lru_cache


# =========================================================
# SOLAR GENERATION SERVICE
# =========================================================
# Uses:
# Open-Meteo Geocoding API
# Open-Meteo Solar Radiation / Weather API
#
# Includes:
# • API retry handling
# • 429 rate-limit handling
# • In-memory caching
# • Request timeout
#
# The result is an ESTIMATE, not a guaranteed production value.
# =========================================================


# =========================================================
# CONFIGURATION
# =========================================================

OPEN_METEO_TIMEOUT = 20

# Cache solar radiation data for 6 hours.
# This prevents repeated API calls for the same location.
SOLAR_CACHE_SECONDS = 6 * 60 * 60

# Cache city coordinates for 24 hours.
GEOCODE_CACHE_SECONDS = 24 * 60 * 60

HEADERS = {
    "User-Agent": "SolarBillOptimizer/1.0"
}


# =========================================================
# SIMPLE IN-MEMORY CACHE
# =========================================================

_solar_cache = {}
_geocode_cache = {}


def get_cached(cache, key, max_age):

    item = cache.get(key)

    if not item:
        return None

    timestamp, value = item

    if time.time() - timestamp > max_age:

        # Remove expired item
        cache.pop(key, None)

        return None

    return value


def set_cached(cache, key, value):

    cache[key] = (
        time.time(),
        value
    )


# =========================================================
# REQUEST HELPER
# =========================================================

def make_request(
    url,
    params,
    timeout=OPEN_METEO_TIMEOUT,
    retries=3
):

    last_error = None

    for attempt in range(retries):

        try:

            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=timeout
            )

            # -------------------------------------------------
            # Rate limit
            # -------------------------------------------------

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:
                        wait_time = float(
                            retry_after
                        )

                    except ValueError:

                        wait_time = (
                            5 * (attempt + 1)
                        )

                else:

                    # 5 sec → 10 sec → 15 sec
                    wait_time = (
                        5 * (attempt + 1)
                    )

                print(
                    f"⚠️ Open-Meteo rate limit "
                    f"(429). "
                    f"Retrying in {wait_time:.0f}s..."
                )

                if attempt < retries - 1:

                    time.sleep(
                        wait_time
                    )

                    continue

                raise requests.HTTPError(
                    "Open-Meteo API rate limit "
                    "persisted after retries."
                )

            # -------------------------------------------------
            # Other HTTP errors
            # -------------------------------------------------

            response.raise_for_status()

            return response

        except requests.RequestException as e:

            last_error = e

            print(
                f"⚠️ Open-Meteo request failed "
                f"(attempt {attempt + 1}/{retries}):",
                repr(e)
            )

            if attempt < retries - 1:

                wait_time = (
                    2 ** attempt
                )

                print(
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(
                    wait_time
                )

            else:

                raise last_error


# =========================================================
# GEOCODE CITY
# =========================================================

def get_city_coordinates(city):

    if not city:
        return None

    # -----------------------------------------------------
    # Normalize city
    # -----------------------------------------------------

    city_key = city.strip().lower()

    # -----------------------------------------------------
    # Check cache
    # -----------------------------------------------------

    cached_location = get_cached(
        _geocode_cache,
        city_key,
        GEOCODE_CACHE_SECONDS
    )

    if cached_location:

        print(
            f"📍 Using cached coordinates for {city}"
        )

        return cached_location

    # -----------------------------------------------------
    # Open-Meteo Geocoding API
    # -----------------------------------------------------

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

    response = make_request(
        url,
        params,
        timeout=15,
        retries=3
    )

    data = response.json()

    results = data.get(
        "results",
        []
    )

    if not results:

        return None

    location = results[0]

    result = {

        "name": location.get(
            "name"
        ),

        "latitude": location.get(
            "latitude"
        ),

        "longitude": location.get(
            "longitude"
        ),

        "state": location.get(
            "admin1"
        ),

        "country": location.get(
            "country"
        )
    }

    # -----------------------------------------------------
    # Save to cache
    # -----------------------------------------------------

    set_cached(
        _geocode_cache,
        city_key,
        result
    )

    print(
        f"📍 Coordinates fetched for {city}"
    )

    return result


# =========================================================
# GET SOLAR RADIATION
# =========================================================

def get_solar_radiation(
    latitude,
    longitude
):

    # -----------------------------------------------------
    # Cache key
    # -----------------------------------------------------

    cache_key = (
        round(float(latitude), 4),
        round(float(longitude), 4)
    )

    # -----------------------------------------------------
    # Check cache
    # -----------------------------------------------------

    cached_radiation = get_cached(
        _solar_cache,
        cache_key,
        SOLAR_CACHE_SECONDS
    )

    if cached_radiation:

        print(
            "☀️ Using cached solar radiation data"
        )

        return cached_radiation

    # -----------------------------------------------------
    # Open-Meteo Solar API
    # -----------------------------------------------------

    url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    params = {

        "latitude": latitude,

        "longitude": longitude,

        # Last 30 days of solar radiation
        "past_days": 30,

        # We don't need future forecast
        "forecast_days": 0,

        "daily": (
            "shortwave_radiation_sum"
        ),

        "timezone": "auto"
    }

    print(
        "☀️ Fetching solar radiation "
        "from Open-Meteo..."
    )

    response = make_request(
        url,
        params,
        timeout=20,
        retries=3
    )

    data = response.json()

    daily = data.get(
        "daily",
        {}
    )

    radiation_values = daily.get(
        "shortwave_radiation_sum",
        []
    )

    # -----------------------------------------------------
    # Remove missing values
    # -----------------------------------------------------

    radiation_values = [

        value

        for value in radiation_values

        if value is not None
    ]

    if not radiation_values:

        return None

    # -----------------------------------------------------
    # Average daily solar radiation
    # -----------------------------------------------------

    average_mj = (

        sum(radiation_values)

        /

        len(radiation_values)
    )

    # -----------------------------------------------------
    # Convert MJ/m² → kWh/m²
    # -----------------------------------------------------

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
            len(
                radiation_values
            )
    }

    # -----------------------------------------------------
    # Save result to cache
    # -----------------------------------------------------

    set_cached(
        _solar_cache,
        cache_key,
        result
    )

    print(
        "☀️ Solar radiation data cached "
        "successfully."
    )

    return result


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

    # -----------------------------------------------------
    # Final result
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
            PERFORMANCE_RATIO
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()

    print(
        "☀️ SOLAR GENERATION SERVICE TEST"
    )

    print(
        "----------------------------------------"
    )

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

    print(
        "----------------------------------------"
    )