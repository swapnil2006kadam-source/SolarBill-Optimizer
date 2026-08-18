import json
import os
from datetime import datetime


# =========================================================
# PATH
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_FILE = os.path.join(
    BASE_DIR,
    "solar_data",
    "solar_data.json"
)


# =========================================================
# LOAD DATA
# =========================================================

def load_solar_data():

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Solar data file not found: {DATA_FILE}"
        )

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# GET MSEDCL PRICING
# =========================================================

def get_msedecl_pricing():
    """
    Return the currently stored MSEDCL reference pricing.

    IMPORTANT:
    This function does not invent or automatically modify
    pricing. It only reads the verified values stored in
    solar_data.json.
    """

    data = load_solar_data()

    installation_data = data.get(
        "installation_cost",
        {}
    )

    maharashtra = installation_data.get(
        "Maharashtra"
    )

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


# =========================================================
# CHECK DATA FRESHNESS
# =========================================================

def get_pricing_status():

    pricing = get_msedecl_pricing()

    last_checked = pricing.get(
        "last_checked"
    )

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

        current_time = datetime.now()

        age_hours = (
            current_time - checked_time
        ).total_seconds() / 3600

    except ValueError:

        return {
            "status": "UNKNOWN",
            "message": "Invalid last_checked timestamp."
        }


    # -----------------------------------------------------
    # Fresh
    # -----------------------------------------------------

    if age_hours <= 24:

        return {
            "status": "FRESH",
            "message": "MSEDCL pricing was checked within the last 24 hours.",
            "age_hours": round(age_hours, 2)
        }


    # -----------------------------------------------------
    # Older than 24 hours
    # -----------------------------------------------------

    return {
        "status": "OLD",
        "message": "MSEDCL pricing should be checked again.",
        "age_hours": round(age_hours, 2)
    }


# =========================================================
# DISPLAY PRICING
# =========================================================

def show_pricing():

    pricing = get_msedecl_pricing()

    status = get_pricing_status()

    print()
    print("☀️ MSEDCL INSTALLATION PRICING")
    print("========================================")

    print(
        "1–3 kW:",
        f"₹{pricing['up_to_3kw_per_kw']:,.2f}/kW"
    )

    print(
        ">3–10 kW:",
        f"₹{pricing['above_3kw_to_10kw_per_kw']:,.2f}/kW"
    )

    print(
        "DISCOM:",
        pricing.get(
            "discom",
            "Unknown"
        )
    )

    print(
        "Source:",
        pricing.get(
            "source",
            "Unknown"
        )
    )

    print(
        "Last checked:",
        pricing.get(
            "last_checked",
            "Not available"
        )
    )

    print(
        "Status:",
        status["status"]
    )

    print(
        status["message"]
    )

    print("========================================")
    print()


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    show_pricing()