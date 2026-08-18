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
# CALCULATE CENTRAL SUBSIDY
# =========================================================

def calculate_central_subsidy(solar_kw):

    data = load_solar_data()

    subsidy_data = data.get(
        "subsidy",
        {}
    )

    first_2kw_rate = subsidy_data.get(
        "first_2kw_per_kw"
    )

    additional_1kw_rate = subsidy_data.get(
        "additional_1kw_per_kw"
    )

    maximum_subsidy = subsidy_data.get(
        "maximum_central_subsidy"
    )


    # -----------------------------------------------------
    # Check subsidy data
    # -----------------------------------------------------

    if (
        first_2kw_rate is None
        or additional_1kw_rate is None
        or maximum_subsidy is None
    ):

        raise ValueError(
            "Subsidy data is incomplete."
        )


    # -----------------------------------------------------
    # Invalid system size
    # -----------------------------------------------------

    if solar_kw <= 0:

        return 0


    # -----------------------------------------------------
    # Up to 2 kW
    # -----------------------------------------------------

    if solar_kw <= 2:

        subsidy = (
            solar_kw * first_2kw_rate
        )


    # -----------------------------------------------------
    # Between 2 kW and 3 kW
    # -----------------------------------------------------

    elif solar_kw <= 3:

        subsidy = (
            2 * first_2kw_rate
            +
            (solar_kw - 2)
            * additional_1kw_rate
        )


    # -----------------------------------------------------
    # Above 3 kW
    # -----------------------------------------------------

    else:

        subsidy = maximum_subsidy


    # -----------------------------------------------------
    # Maximum subsidy protection
    # -----------------------------------------------------

    subsidy = min(
        subsidy,
        maximum_subsidy
    )


    return round(
        subsidy,
        2
    )


# =========================================================
# GET SUBSIDY INFORMATION
# =========================================================

def get_subsidy_info():

    data = load_solar_data()

    return data.get(
        "subsidy",
        {}
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("☀️ SOLAR SUBSIDY SERVICE TEST")
    print("----------------------------------------")


    test_sizes = [
        1,
        2,
        2.5,
        3,
        4,
        5
    ]


    for solar_kw in test_sizes:

        subsidy = calculate_central_subsidy(
            solar_kw
        )

        print(
            f"{solar_kw} kW → ₹{subsidy:,.2f}"
        )


    print("----------------------------------------")


    info = get_subsidy_info()


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