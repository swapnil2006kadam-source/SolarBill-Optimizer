import json
import os


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


def calculate_central_subsidy(solar_kw):
    """Calculate the applicable central solar subsidy."""

    data = load_solar_data()

    subsidy_data = data.get("subsidy", {})

    first_2kw_rate = subsidy_data.get("first_2kw_per_kw")
    additional_1kw_rate = subsidy_data.get("additional_1kw_per_kw")
    maximum_subsidy = subsidy_data.get("maximum_central_subsidy")

    if (
        first_2kw_rate is None
        or additional_1kw_rate is None
        or maximum_subsidy is None
    ):
        raise ValueError("Subsidy data is incomplete.")

    if solar_kw <= 0:
        return 0

    if solar_kw <= 2:
        subsidy = solar_kw * first_2kw_rate

    elif solar_kw <= 3:
        subsidy = (
            2 * first_2kw_rate
            + (solar_kw - 2) * additional_1kw_rate
        )

    else:
        subsidy = maximum_subsidy

    subsidy = min(subsidy, maximum_subsidy)

    return round(subsidy, 2)


def get_subsidy_info():
    """Return stored subsidy information."""

    data = load_solar_data()

    return data.get("subsidy", {})