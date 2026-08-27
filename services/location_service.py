# =========================================================
# LOCATION SERVICE
# City → State → DISCOM
# Maharashtra Only
# =========================================================


CITY_DATA = {

    # -----------------------------------------------------
    # MAHARASHTRA
    # -----------------------------------------------------

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


# =========================================================
# GET LOCATION INFORMATION
# =========================================================

def get_location_info(city):

    if not city:
        return None

    city_key = city.strip().lower()

    return CITY_DATA.get(city_key)


# =========================================================
# VALIDATE CITY
# =========================================================

def is_supported_city(city):

    return get_location_info(city) is not None


# =========================================================
# GET SUPPORTED CITIES
# =========================================================

def get_supported_cities():

    return sorted(CITY_DATA.keys())


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("📍 LOCATION SERVICE TEST")
    print("----------------------------------------")

    test_cities = [
        "Mumbai",
        "Pune",
        "Nagpur",
        "Nashik",
        "Sangli",
        "Kolhapur",
        "Satara",
        "Solapur",
        "Navi Mumbai",
        "Delhi"
    ]

    for city in test_cities:

        location = get_location_info(city)

        if location:

            print(
                f"{city} → "
                f"{location['state']} → "
                f"{location['discom']}"
            )

        else:

            print(
                f"{city} → ❌ City not supported"
            )

    print("----------------------------------------")

    print()
    print("✅ Total supported cities:", len(CITY_DATA))

    print()
    print("Supported Maharashtra cities:")

    for city in get_supported_cities():

        print("•", city)

    print()