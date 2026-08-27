CITY_DATA = {
    "mumbai": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "pune": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "nagpur": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "nashik": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "thane": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "aurangabad": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "chhatrapati sambhajinagar": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "navi mumbai": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "kolhapur": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "sangli": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "satara": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "solapur": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "ahmednagar": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "ahilyanagar": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "jalgaon": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "dhule": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "nanded": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "latur": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "akola": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "amravati": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "ratnagiri": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "chandrapur": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "beed": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "osmanabad": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    },
    "dharashiv": {
        "state": "Maharashtra",
        "discom": "MSEDCL"
    }
}


def get_location_info(city):
    """Return state and DISCOM information for a city."""

    if not city:
        return None

    city_key = city.strip().lower()

    return CITY_DATA.get(city_key)


def is_supported_city(city):
    """Check whether a city is supported."""

    return get_location_info(city) is not None


def get_supported_cities():
    """Return all supported cities."""

    return sorted(CITY_DATA.keys())