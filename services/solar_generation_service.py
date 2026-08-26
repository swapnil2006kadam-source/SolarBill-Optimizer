import requests
import time


# =========================================================
# SOLAR GENERATION SERVICE
# =========================================================
# Uses:
# • Open-Meteo Geocoding API
# • Open-Meteo Solar Radiation API
#
# Includes:
# • In-memory caching
# • 429 handling
# • API failure fallback
# • City-based solar radiation estimates
#
# IMPORTANT:
# Solar generation is an ESTIMATE.
# =========================================================


# =========================================================
# CONFIGURATION
# =========================================================

OPEN_METEO_TIMEOUT = 15

# Solar data cache: 6 hours
SOLAR_CACHE_SECONDS = 6 * 60 * 60

# Geocoding cache: 24 hours
GEOCODE_CACHE_SECONDS = 24 * 60 * 60

HEADERS = {
    "User-Agent": "SolarBillOptimizer/1.0"
}


# =========================================================
# CACHE
# =========================================================

_solar_cache = {}

_geocode_cache = {}


def get_cached(cache, key, max_age):

    item = cache.get(key)

    if not item:
        return None

    timestamp, value = item

    if time.time() - timestamp > max_age:

        cache.pop(key, None)

        return None

    return value


def set_cached(cache, key, value):

    cache[key] = (
        time.time(),
        value
    )


# =========================================================
# INDIAN CITY FALLBACK SOLAR RADIATION
# =========================================================
#
# Unit:
# kWh/m²/day
#
# These are approximate planning values.
# They are NOT live measurements.
#
# If a city isn't listed, we use a regional default.
# =========================================================

CITY_SOLAR_RADIATION = {

    # Maharashtra
    "mumbai": 5.0,
    "pune": 5.2,
    "nagpur": 5.3,
    "nashik": 5.2,
    "aurangabad": 5.3,
    "chhatrapati sambhajinagar": 5.3,
    "kolhapur": 5.0,
    "solapur": 5.4,
    "thane": 5.0,
    "navi mumbai": 5.0,

    # Karnataka
    "bengaluru": 5.2,
    "bangalore": 5.2,
    "mysore": 5.1,
    "mysuru": 5.1,
    "hubli": 5.3,
    "dharwad": 5.3,

    # Gujarat
    "ahmedabad": 5.5,
    "surat": 5.3,
    "vadodara": 5.3,
    "rajkot": 5.6,

    # Rajasthan
    "jaipur": 5.6,
    "jodhpur": 6.0,
    "udaipur": 5.7,
    "kota": 5.5,

    # Delhi / North India
    "delhi": 5.0,
    "new delhi": 5.0,
    "gurgaon": 5.0,
    "gurugram": 5.0,
    "noida": 5.0,

    # Telangana
    "hyderabad": 5.4,
    "warangal": 5.3,

    # Tamil Nadu
    "chennai": 5.2,
    "coimbatore": 5.3,
    "madurai": 5.5,
    "salem": 5.4,

    # Kerala
    "kochi": 4.8,
    "thiruvananthapuram": 4.9,
    "kozhikode": 4.8,

    # Andhra Pradesh
    "vijayawada": 5.3,
    "visakhapatnam": 5.1,
    "tirupati": 5.3,

    # West Bengal
    "kolkata": 4.7,

    # Odisha
    "bhubaneswar": 5.0,

    # Madhya Pradesh
    "bhopal": 5.4,
    "indore": 5.5,

    # Uttar Pradesh
    "lucknow": 5.0,
    "kanpur": 5.1,
    "agra": 5.3,

    # Bihar
    "patna": 4.9,

    # Punjab
    "chandigarh": 5.0,
    "amritsar": 5.0,

    # Haryana
    "faridabad": 5.0,

    # Goa
    "panaji": 5.0,
}


# =========================================================
# REGIONAL DEFAULT
# =========================================================

DEFAULT_SOLAR_RADIATION = 5.0


# =========================================================
# FALLBACK SOLAR RADIATION
# =========================================================

def get_fallback_solar_radiation(city):

    city_key = (
        city
        .strip()
        .lower()
    )

    radiation = CITY_SOLAR_RADIATION.get(
        city_key,
        DEFAULT_SOLAR_RADIATION
    )

    print(
        f"⚠️ Using fallback solar radiation "
        f"for {city}: "
        f"{radiation} kWh/m²/day"
    )

    return {

        "average_daily_radiation_mj":
            round(
                radiation * 3.6,
                2
            ),

        "average_daily_radiation_kwh":
            round(
                radiation,
                2
            ),

        "days_used":
            30,

        "source":
            "Fallback estimate"
    }


# =========================================================
# GEOCODE CITY
# =========================================================

def get_city_coordinates(city):

    if not city:
        return None

    city_key = (
        city
        .strip()
        .lower()
    )

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

    try:

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=10
        )

        # -------------------------------------------------
        # Handle rate limit
        # -------------------------------------------------

        if response.status_code == 429:

            print(
                "⚠️ Open-Meteo geocoding "
                "rate limited (429)."
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

        # -------------------------------------------------
        # Cache
        # -------------------------------------------------

        set_cached(
            _geocode_cache,
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
# GET SOLAR RADIATION FROM OPEN-METEO
# =========================================================

def get_solar_radiation(
    latitude,
    longitude
):

    cache_key = (

        round(
            float(latitude),
            4
        ),

        round(
            float(longitude),
            4
        )
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
    # Open-Meteo
    # -----------------------------------------------------

    url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    params = {

        "latitude":
            latitude,

        "longitude":
            longitude,

        "past_days":
            30,

        "forecast_days":
            0,

        "daily":
            "shortwave_radiation_sum",

        "timezone":
            "auto"
    }

    print(
        "☀️ Fetching solar radiation "
        "from Open-Meteo..."
    )

    try:

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=OPEN_METEO_TIMEOUT
        )

        # -------------------------------------------------
        # IMPORTANT:
        # Don't retry 429 anymore.
        #
        # Immediately fall back.
        # -------------------------------------------------

        if response.status_code == 429:

            print(
                "⚠️ Open-Meteo returned 429. "
                "Using fallback."
            )

            return None

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

        radiation_values = [

            value

            for value in radiation_values

            if value is not None
        ]

        if not radiation_values:

            print(
                "⚠️ No solar radiation values "
                "received from Open-Meteo."
            )

            return None

        # -------------------------------------------------
        # Average radiation
        # -------------------------------------------------

        average_mj = (

            sum(
                radiation_values
            )

            /

            len(
                radiation_values
            )
        )

        # -------------------------------------------------
        # MJ/m² → kWh/m²
        # -------------------------------------------------

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
                ),

            "source":
                "Open-Meteo"
        }

        # -------------------------------------------------
        # Cache
        # -------------------------------------------------

        set_cached(
            _solar_cache,
            cache_key,
            result
        )

        print(
            "☀️ Solar radiation data "
            "cached successfully."
        )

        return result

    except Exception as e:

        print(
            "⚠️ SOLAR API ERROR:",
            repr(e)
        )

        return None


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
    # FALLBACK
    # -----------------------------------------------------

    if not radiation:

        print(
            "⚠️ Open-Meteo unavailable."
        )

        print(
            "☀️ Switching to fallback "
            "solar radiation estimate."
        )

        radiation = (
            get_fallback_solar_radiation(
                city
            )
        )

    # -----------------------------------------------------
    # If geocoding failed, still continue
    # -----------------------------------------------------

    if not location:

        location = {

            "name":
                city.title(),

            "latitude":
                None,

            "longitude":
                None,

            "state":
                None,

            "country":
                "India"
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
                "Solar radiation:",
                f"{result['average_daily_radiation']} "
                "kWh/m²/day"
            )

            print(
                "Source:",
                result["radiation_source"]
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