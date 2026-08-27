import requests
import time


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_TIMEOUT = 5
PERFORMANCE_RATIO = 0.80
CACHE_DURATION = 60 * 60 * 6


MAHARASHTRA_CITIES = {
    "mumbai": {
        "name": "Mumbai",
        "state": "Maharashtra",
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "thane": {
        "name": "Thane",
        "state": "Maharashtra",
        "latitude": 19.2183,
        "longitude": 72.9781
    },
    "navi mumbai": {
        "name": "Navi Mumbai",
        "state": "Maharashtra",
        "latitude": 19.0330,
        "longitude": 73.0297
    },
    "pune": {
        "name": "Pune",
        "state": "Maharashtra",
        "latitude": 18.5204,
        "longitude": 73.8567
    },
    "nagpur": {
        "name": "Nagpur",
        "state": "Maharashtra",
        "latitude": 21.1458,
        "longitude": 79.0882
    },
    "nashik": {
        "name": "Nashik",
        "state": "Maharashtra",
        "latitude": 20.0059,
        "longitude": 73.7797
    },
    "chhatrapati sambhajinagar": {
        "name": "Chhatrapati Sambhajinagar",
        "state": "Maharashtra",
        "latitude": 19.8762,
        "longitude": 75.3433
    },
    "aurangabad": {
        "name": "Chhatrapati Sambhajinagar",
        "state": "Maharashtra",
        "latitude": 19.8762,
        "longitude": 75.3433
    },
    "solapur": {
        "name": "Solapur",
        "state": "Maharashtra",
        "latitude": 17.6599,
        "longitude": 75.9064
    },
    "kolhapur": {
        "name": "Kolhapur",
        "state": "Maharashtra",
        "latitude": 16.7050,
        "longitude": 74.2433
    },
    "sangli": {
        "name": "Sangli",
        "state": "Maharashtra",
        "latitude": 16.8524,
        "longitude": 74.5815
    },
    "satara": {
        "name": "Satara",
        "state": "Maharashtra",
        "latitude": 17.6805,
        "longitude": 74.0183
    },
    "ahmednagar": {
        "name": "Ahilyanagar",
        "state": "Maharashtra",
        "latitude": 19.0948,
        "longitude": 74.7480
    },
    "ahilyanagar": {
        "name": "Ahilyanagar",
        "state": "Maharashtra",
        "latitude": 19.0948,
        "longitude": 74.7480
    },
    "amravati": {
        "name": "Amravati",
        "state": "Maharashtra",
        "latitude": 20.9374,
        "longitude": 77.7796
    },
    "akola": {
        "name": "Akola",
        "state": "Maharashtra",
        "latitude": 20.7002,
        "longitude": 77.0082
    },
    "nanded": {
        "name": "Nanded",
        "state": "Maharashtra",
        "latitude": 19.1383,
        "longitude": 77.3210
    },
    "jalgaon": {
        "name": "Jalgaon",
        "state": "Maharashtra",
        "latitude": 21.0077,
        "longitude": 75.5626
    },
    "latur": {
        "name": "Latur",
        "state": "Maharashtra",
        "latitude": 18.4088,
        "longitude": 76.5604
    },
    "dhule": {
        "name": "Dhule",
        "state": "Maharashtra",
        "latitude": 20.9042,
        "longitude": 74.7749
    },
    "ratnagiri": {
        "name": "Ratnagiri",
        "state": "Maharashtra",
        "latitude": 16.9902,
        "longitude": 73.3120
    },
    "chandrapur": {
        "name": "Chandrapur",
        "state": "Maharashtra",
        "latitude": 19.9700,
        "longitude": 79.3000
    },
    "parbhani": {
        "name": "Parbhani",
        "state": "Maharashtra",
        "latitude": 19.2600,
        "longitude": 76.7700
    },
    "beed": {
        "name": "Beed",
        "state": "Maharashtra",
        "latitude": 18.9891,
        "longitude": 75.7601
    },
    "yavatmal": {
        "name": "Yavatmal",
        "state": "Maharashtra",
        "latitude": 20.3899,
        "longitude": 78.1307
    },
    "buldhana": {
        "name": "Buldhana",
        "state": "Maharashtra",
        "latitude": 20.5293,
        "longitude": 76.1843
    },
    "wardha": {
        "name": "Wardha",
        "state": "Maharashtra",
        "latitude": 20.7453,
        "longitude": 78.6022
    },
    "gondia": {
        "name": "Gondia",
        "state": "Maharashtra",
        "latitude": 21.4624,
        "longitude": 80.2209
    },
    "washim": {
        "name": "Washim",
        "state": "Maharashtra",
        "latitude": 20.1113,
        "longitude": 77.1330
    },
    "dharashiv": {
        "name": "Dharashiv",
        "state": "Maharashtra",
        "latitude": 18.1853,
        "longitude": 76.0419
    },
    "osmanabad": {
        "name": "Dharashiv",
        "state": "Maharashtra",
        "latitude": 18.1853,
        "longitude": 76.0419
    },
    "hingoli": {
        "name": "Hingoli",
        "state": "Maharashtra",
        "latitude": 19.7161,
        "longitude": 77.1494
    },
    "palghar": {
        "name": "Palghar",
        "state": "Maharashtra",
        "latitude": 19.6967,
        "longitude": 72.7653
    },
    "raigad": {
        "name": "Raigad",
        "state": "Maharashtra",
        "latitude": 18.5158,
        "longitude": 73.1822
    }
}


SOLAR_CACHE = {}


def get_city_coordinates(city):
    if not city:
        return None

    location = MAHARASHTRA_CITIES.get(city.strip().lower())

    if not location:
        print(f"⚠️ Maharashtra city not found: {city}")
        return None

    print(f"📍 Coordinates found locally for {location['name'].upper()}")
    return location.copy()


def get_fallback_solar(latitude=None):
    radiation = 5.0

    if latitude is not None:
        latitude = abs(float(latitude))

        if latitude < 17:
            radiation = 5.3
        elif latitude < 19:
            radiation = 5.2
        elif latitude < 21:
            radiation = 5.1
        elif latitude < 23:
            radiation = 5.0
        else:
            radiation = 4.8

    print(f"☀️ Using location-based fallback: {radiation} kWh/m²/day")

    return {
        "average_daily_radiation_mj": round(radiation * 3.6, 2),
        "average_daily_radiation_kwh": radiation,
        "days_used": 30,
        "source": "Location-based fallback estimate"
    }


def get_solar_radiation(latitude, longitude):
    cache_key = (round(latitude, 3), round(longitude, 3))
    cached = SOLAR_CACHE.get(cache_key)

    if cached and time.time() - cached["timestamp"] < CACHE_DURATION:
        print("☀️ Solar radiation loaded from cache.")
        return cached["data"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "past_days": 30,
        "forecast_days": 0,
        "daily": "shortwave_radiation_sum",
        "timezone": "auto"
    }

    print("☀️ Fetching solar radiation from Open-Meteo...")

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=OPEN_METEO_TIMEOUT
        )
        response.raise_for_status()

        daily = response.json().get("daily", {})
        radiation_values = [
            value
            for value in daily.get("shortwave_radiation_sum", [])
            if value is not None
        ]

        if not radiation_values:
            raise ValueError("No solar radiation data returned.")

        average_mj = sum(radiation_values) / len(radiation_values)
        average_kwh = average_mj / 3.6

        result = {
            "average_daily_radiation_mj": round(average_mj, 2),
            "average_daily_radiation_kwh": round(average_kwh, 2),
            "days_used": len(radiation_values),
            "source": "Open-Meteo"
        }

        SOLAR_CACHE[cache_key] = {
            "timestamp": time.time(),
            "data": result
        }

        print("☀️ Solar radiation cached.")
        return result

    except Exception as e:
        print("⚠️ SOLAR API ERROR:", repr(e))
        print("⚠️ Open-Meteo unavailable.")
        return get_fallback_solar(latitude)


def estimate_solar_generation(solar_kw, city):
    if solar_kw <= 0:
        raise ValueError("Solar system size must be greater than zero.")

    location = get_city_coordinates(city)

    if not location:
        raise ValueError(f"{city.title()} is currently not supported.")

    radiation = get_solar_radiation(
        location["latitude"],
        location["longitude"]
    )

    daily_generation = (
        solar_kw *
        radiation["average_daily_radiation_kwh"] *
        PERFORMANCE_RATIO
    )

    monthly_generation = daily_generation * 30
    yearly_generation = daily_generation * 365

    return {
        "city": location["name"],
        "state": location["state"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "solar_kw": solar_kw,
        "average_daily_radiation": radiation["average_daily_radiation_kwh"],
        "days_used": radiation["days_used"],
        "source": radiation["source"],
        "daily_generation_kwh": round(daily_generation, 2),
        "monthly_generation_kwh": round(monthly_generation, 2),
        "yearly_generation_kwh": round(yearly_generation, 2),
        "performance_ratio": PERFORMANCE_RATIO
    }


if __name__ == "__main__":
    print("\n☀️ SOLAR GENERATION SERVICE TEST")
    print("----------------------------------------")

    test_cities = [
        "Mumbai",
        "Pune",
        "Nagpur",
        "Sangli",
        "Kolhapur",
        "Satara",
        "Nashik",
        "Solapur"
    ]

    for city in test_cities:
        try:
            result = estimate_solar_generation(
                solar_kw=2,
                city=city
            )

            print(f"\nCity: {result['city']}")
            print(f"State: {result['state']}")
            print(
                "Coordinates:",
                result["latitude"],
                result["longitude"]
            )
            print(
                "Radiation:",
                f"{result['average_daily_radiation']} kWh/m²/day"
            )
            print("Source:", result["source"])
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

        except Exception as e:
            print(f"{city} → ❌ ERROR:", e)

    print("\n----------------------------------------")