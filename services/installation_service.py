import json
import os


# =========================================================
# PATH TO SOLAR DATA
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_FILE = os.path.join(
    BASE_DIR,
    "solar_data",
    "solar_data.json"
)


# =========================================================
# LOAD SOLAR DATA
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
# CALCULATE INSTALLATION COST
# =========================================================

def calculate_installation_cost(
    solar_kw,
    state="Maharashtra"
):

    data = load_solar_data()

    cost_data = data.get(
        "installation_cost",
        {}
    )

    state_data = cost_data.get(
        state
    )

    if not state_data:

        raise ValueError(
            f"No installation cost data available for {state}."
        )


    up_to_3kw_rate = state_data.get(
        "up_to_3kw_per_kw"
    )

    above_3kw_rate = state_data.get(
        "above_3kw_to_10kw_per_kw"
    )


    if (
        up_to_3kw_rate is None
        or above_3kw_rate is None
    ):

        raise ValueError(
            "Installation cost data is incomplete."
        )


    if solar_kw <= 0:

        return 0


    # -----------------------------------------------------
    # 1 kW to 3 kW
    # -----------------------------------------------------

    if solar_kw <= 3:

        cost = solar_kw * up_to_3kw_rate


    # -----------------------------------------------------
    # Above 3 kW to 10 kW
    # -----------------------------------------------------

    elif solar_kw <= 10:

        cost = (
            3 * up_to_3kw_rate
            +
            (solar_kw - 3) * above_3kw_rate
        )


    # -----------------------------------------------------
    # Above 10 kW
    # -----------------------------------------------------

    else:

        raise ValueError(
            "Installation cost data currently supports "
            "systems up to 10 kW."
        )


    return round(
        cost,
        2
    )


# =========================================================
# GET INSTALLATION INFORMATION
# =========================================================

def get_installation_info(
    state="Maharashtra"
):

    data = load_solar_data()

    return data.get(
        "installation_cost",
        {}
    ).get(
        state,
        {}
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("☀️ INSTALLATION COST SERVICE TEST")
    print("----------------------------------------")

    test_sizes = [
        1,
        2,
        3,
        4,
        5,
        10
    ]

    for solar_kw in test_sizes:

        cost = calculate_installation_cost(
            solar_kw,
            "Maharashtra"
        )

        print(
            f"{solar_kw} kW → ₹{cost:,.2f}"
        )

    print("----------------------------------------")

    info = get_installation_info(
        "Maharashtra"
    )

    print(
        "DISCOM:",
        info.get(
            "discom",
            "Unknown"
        )
    )

    print(
        "Source:",
        info.get(
            "source",
            "Unknown"
        )
    )

    print(
        "Last checked:",
        info.get(
            "last_checked",
            "Not available"
        )
    )

    print()