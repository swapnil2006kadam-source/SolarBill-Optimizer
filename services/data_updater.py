import json
import os
import hashlib
import requests
from datetime import datetime


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_FILE = os.path.join(
    BASE_DIR,
    "solar_data",
    "solar_data.json"
)


# =========================================================
# OFFICIAL SOURCES
# =========================================================

SOURCES = {

    "pm_surya_ghar": {
        "name": "PM Surya Ghar Official Portal",
        "url": "https://pmsuryaghar.gov.in/"
    },

    "mnre_current_notices": {
        "name": "MNRE Current Notices",
        "url": "https://mnre.gov.in/en/past-notices/current-notices/"
    },

    "mnre_cfa_guidelines": {
        "name": "MNRE PM Surya Ghar CFA Guidelines",
        "url": "https://mnre.gov.in/notice/operational-guidelines-for-implementation-of-the-component-central-financial-assistance-to-residential-consumers-of-pm-surya-ghar-muft-bijli-yojana/"
    },

    "mnre_cfa_amendment": {
        "name": "MNRE PM Surya Ghar CFA Amendment",
        "url": "https://mnre.gov.in/en/notice/amendment-in-guidelines-for-implementation-of-pm-surya-ghar-muft-bijli-yojana-for-the-component-of-cfa-to-residential-consumers/"
    },

    "msedcl_ismart": {
        "name": "MSEDCL I-SMART Solar",
        "url": "https://www.mahadiscom.in/ismart/"
    }

}

# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    if not os.path.exists(DATA_FILE):

        return {
            "subsidy": {},
            "discoms": {},
            "sources": {}
        }

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# =========================================================
# SAVE DATA
# =========================================================

def save_data(data):

    os.makedirs(
        os.path.dirname(DATA_FILE),
        exist_ok=True
    )

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# DOWNLOAD SOURCE
# =========================================================

def download_source(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/142.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.content


# =========================================================
# CREATE HASH
# =========================================================

def create_hash(content):

    return hashlib.sha256(content).hexdigest()


# =========================================================
# CHECK SOURCE
# =========================================================

def check_source(source_id, source_info, data):

    print()
    print("========================================")
    print("🔎 Checking:", source_info["name"])
    print("========================================")

    try:

        # -----------------------------------------
        # Download source
        # -----------------------------------------

        content = download_source(
            source_info["url"]
        )


        # -----------------------------------------
        # Create new hash
        # -----------------------------------------

        new_hash = create_hash(content)


        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        # -----------------------------------------
        # Get old source information
        # -----------------------------------------

        old_source = data.get(
            "sources",
            {}
        ).get(
            source_id,
            {}
        )


        old_hash = old_source.get(
            "content_hash"
        )


        # -----------------------------------------
        # First time checking
        # -----------------------------------------

        if not old_hash:

            print(
                "🆕 First time checking this source."
            )

            changed = False

            last_changed = now


        # -----------------------------------------
        # Source changed
        # -----------------------------------------

        elif old_hash != new_hash:

            print(
                "⚠️ SOURCE HAS CHANGED!"
            )

            changed = True

            last_changed = now


        # -----------------------------------------
        # Source unchanged
        # -----------------------------------------

        else:

            print(
                "✅ No change detected."
            )

            changed = False

            last_changed = old_source.get(
                "last_changed"
            )


        # -----------------------------------------
        # Make sure sources exists
        # -----------------------------------------

        if "sources" not in data:

            data["sources"] = {}


        # -----------------------------------------
        # Save source information
        # -----------------------------------------

        data["sources"][source_id] = {

            "name": source_info["name"],

            "url": source_info["url"],

            "content_hash": new_hash,

            "last_checked": now,

            "last_changed": last_changed,

            "changed": changed,

            "status": "success"

        }


        # -----------------------------------------
        # Return result
        # -----------------------------------------

        return changed


    except Exception as e:

        print(
            "❌ Could not check source:",
            repr(e)
        )


        # IMPORTANT:
        # None means the source could NOT be checked.

        if "sources" not in data:

            data["sources"] = {}


        old_source = data["sources"].get(
            source_id,
            {}
        )


        data["sources"][source_id] = {

            "name": source_info["name"],

            "url": source_info["url"],

            "content_hash": old_source.get(
                "content_hash"
            ),

            "last_checked": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "last_changed": old_source.get(
                "last_changed"
            ),

            "changed": False,

            "status": "failed",

            "error": str(e)

        }


        return None


# =========================================================
# MAIN UPDATE FUNCTION
# =========================================================

def update_sources():

    print()
    print("☀️ SOLAR DATA UPDATE STARTED")

    print(
        "Time:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    data = load_data()


    changed_sources = []

    failed_sources = []


    # =====================================================
    # CHECK ALL OFFICIAL SOURCES
    # =====================================================

    for source_id, source_info in SOURCES.items():

        changed = check_source(
            source_id,
            source_info,
            data
        )


        # -------------------------------------------------
        # Source failed
        # -------------------------------------------------

        if changed is None:

            failed_sources.append(
                source_info["name"]
            )


        # -------------------------------------------------
        # Source changed
        # -------------------------------------------------

        elif changed:

            changed_sources.append(
                source_info["name"]
            )


        # -------------------------------------------------
        # MSEDCL installation-price verification
        # -------------------------------------------------

        if source_id == "msedcl_ismart":

            source_status = data.get(
                "sources",
                {}
            ).get(
                "msedcl_ismart",
                {}
            )


            # Only update installation pricing
            # when MSEDCL was successfully checked.

            if source_status.get("status") == "success":

                if "installation_cost" in data:

                    if "Maharashtra" in data["installation_cost"]:

                        data["installation_cost"]["Maharashtra"][
                            "last_checked"
                        ] = source_status.get(
                            "last_checked"
                        )

    # =====================================================
    # SAVE DATA
    # =====================================================

    save_data(data)


    # =====================================================
    # FINAL RESULT
    # =====================================================

    print()
    print("========================================")


    # -----------------------------------------
    # Changes
    # -----------------------------------------

    if changed_sources:

        print(
            "⚠️ CHANGES DETECTED:"
        )

        for source in changed_sources:

            print(
                "   •",
                source
            )

        print()

        print(
            "⚠️ Manual verification is required "
            "before changing calculator values."
        )


    # -----------------------------------------
    # Failed sources
    # -----------------------------------------

    if failed_sources:

        print()

        print(
            "❌ SOURCES COULD NOT BE CHECKED:"
        )

        for source in failed_sources:

            print(
                "   •",
                source
            )


    # -----------------------------------------
    # Everything successful
    # -----------------------------------------

    if not changed_sources and not failed_sources:

        print(
            "✅ All official sources checked."
        )

        print(
            "✅ No changes detected."
        )


    # -----------------------------------------
    # No changes but some failed
    # -----------------------------------------

    elif not changed_sources and failed_sources:

        print()

        print(
            "⚠️ No changes detected in the "
            "sources that were successfully checked."
        )

        print(
            "⚠️ Some sources could not be verified."
        )


    print(
        "========================================"
    )

    print()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    update_sources()