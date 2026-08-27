import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_FILE = os.path.join(
    BASE_DIR,
    "solar_data",
    "solar_data.json"
)


def load_solar_data():
    """Load solar data from solar_data.json."""

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Solar data file not found: {DATA_FILE}"
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_msedcl_pricing():
    """
    Return the stored MSEDCL installation pricing.

    This function only reads pricing from solar_data.json.
    It does not modify or invent pricing.
    """

    data = load_solar_data()

    maharashtra = data.get(
        "installation_cost",
        {}
    ).get("Maharashtra")

    if not maharashtra:
        raise ValueError(
            "Maharashtra installation-cost data not found."
        )

    required_fields = [
        "up_to_3kw_per_kw",
        "above_3kw_to_10kw_per_kw",
        "source",
        "source_url",
        "last_checked"
    ]

    for field in required_fields:
        if field not in maharashtra:
            raise ValueError(
                f"Missing installation-cost field: {field}"
            )

    return maharashtra


def get_pricing_status():
    """Check how recently MSEDCL pricing was verified."""

    pricing = get_msedcl_pricing()

    last_checked = pricing.get("last_checked")

    if not last_checked:
        return {
            "status": "UNKNOWN",
            "message": "Pricing has not been checked yet."
        }

    try:
        checked_time = datetime.strptime(
            last_checked,
            "%Y-%m-%d %H:%M:%S"
        )

        age_hours = (
            datetime.now() - checked_time
        ).total_seconds() / 3600

    except ValueError:
        return {
            "status": "UNKNOWN",
            "message": "Invalid last_checked timestamp."
        }

    if age_hours <= 24:
        return {
            "status": "FRESH",
            "message": "MSEDCL pricing was checked within the last 24 hours.",
            "age_hours": round(age_hours, 2)
        }

    return {
        "status": "OLD",
        "message": "MSEDCL pricing should be checked again.",
        "age_hours": round(age_hours, 2)
    }