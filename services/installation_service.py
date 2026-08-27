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


def calculate_installation_cost(
    solar_kw,
    state="Maharashtra"
):
    """Calculate estimated solar installation cost."""

    data = load_solar_data()

    state_data = data.get(
        "installation_cost",
        {}
    ).get(state)

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

    if up_to_3kw_rate is None or above_3kw_rate is None:
        raise ValueError(
            "Installation cost data is incomplete."
        )

    if solar_kw <= 0:
        return 0

    if solar_kw <= 3:
        cost = solar_kw * up_to_3kw_rate

    elif solar_kw <= 10:
        cost = (
            3 * up_to_3kw_rate
            + (solar_kw - 3) * above_3kw_rate
        )

    else:
        raise ValueError(
            "Installation cost data currently supports "
            "systems up to 10 kW."
        )

    return round(cost, 2)


def get_installation_info(
    state="Maharashtra"
):
    """Return installation information for a state."""

    data = load_solar_data()

    return data.get(
        "installation_cost",
        {}
    ).get(state, {})