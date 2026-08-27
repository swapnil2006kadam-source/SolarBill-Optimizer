import hashlib
import json
import os
from datetime import datetime

import requests


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(
    BASE_DIR,
    "solar_data",
    "solar_data.json"
)

REQUEST_TIMEOUT = 30

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "Chrome/142.0 Safari/537.36"
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
        "url": (
            "https://mnre.gov.in/notice/"
            "operational-guidelines-for-implementation-of-the-component-"
            "central-financial-assistance-to-residential-consumers-of-"
            "pm-surya-ghar-muft-bijli-yojana/"
        )
    },

    "mnre_cfa_amendment": {
        "name": "MNRE PM Surya Ghar CFA Amendment",
        "url": (
            "https://mnre.gov.in/en/notice/"
            "amendment-in-guidelines-for-implementation-of-pm-surya-"
            "ghar-muft-bijli-yojana-for-the-component-of-cfa-to-"
            "residential-consumers/"
        )
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
    """Load solar data from the JSON database."""

    if not os.path.exists(DATA_FILE):
        return {
            "subsidy": {},
            "discoms": {},
            "sources": {}
        }

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# =========================================================
# SAVE DATA
# =========================================================

def save_data(data):
    """Save solar data to the JSON database."""

    os.makedirs(
        os.path.dirname(DATA_FILE),
        exist_ok=True
    )

    with open(DATA_FILE, "w", encoding="utf-8") as file:
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
    """Download content from an official source."""

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    return response.content


# =========================================================
# CREATE HASH
# =========================================================

def create_hash(content):
    """Create SHA-256 hash of downloaded content."""

    return hashlib.sha256(content).hexdigest()


# =========================================================
# CHECK SOURCE
# =========================================================

def check_source(source_id, source_info, data):
    """Check whether an official source has changed."""

    print()
    print("========================================")
    print("🔎 Checking:", source_info["name"])
    print("========================================")

    try:
        content = download_source(source_info["url"])
        new_hash = create_hash(content)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        old_source = data.get(
            "sources",
            {}
        ).get(
            source_id,
            {}
        )

        old_hash = old_source.get("content_hash")

        if not old_hash:
            print("🆕 First time checking this source.")

            changed = False
            last_changed = now

        elif old_hash != new_hash:
            print("⚠️ SOURCE HAS CHANGED!")

            changed = True
            last_changed = now

        else:
            print("✅ No change detected.")

            changed = False
            last_changed = old_source.get("last_changed")

        data.setdefault("sources", {})

        data["sources"][source_id] = {
            "name": source_info["name"],
            "url": source_info["url"],
            "content_hash": new_hash,
            "last_checked": now,
            "last_changed": last_changed,
            "changed": changed,
            "status": "success"
        }

        return changed

    except Exception as error:
        print("❌ Could not check source:", repr(error))

        data.setdefault("sources", {})

        old_source = data["sources"].get(
            source_id,
            {}
        )

        data["sources"][source_id] = {
            "name": source_info["name"],
            "url": source_info["url"],
            "content_hash": old_source.get("content_hash"),
            "last_checked": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "last_changed": old_source.get("last_changed"),
            "changed": False,
            "status": "failed",
            "error": str(error)
        }

        return None


# =========================================================
# UPDATE ALL SOURCES
# =========================================================

def update_sources():
    """Check all official sources and update source metadata."""

    print()
    print("☀️ SOLAR DATA UPDATE STARTED")
    print(
        "Time:",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    data = load_data()

    changed_sources = []
    failed_sources = []

    for source_id, source_info in SOURCES.items():

        changed = check_source(
            source_id,
            source_info,
            data
        )

        if changed is None:
            failed_sources.append(
                source_info["name"]
            )

        elif changed:
            changed_sources.append(
                source_info["name"]
            )

        # Update MSEDCL verification timestamp
        if source_id == "msedcl_ismart":

            source_status = data.get(
                "sources",
                {}
            ).get(
                "msedcl_ismart",
                {}
            )

            installation_cost = data.get(
                "installation_cost",
                {}
            )

            maharashtra_data = installation_cost.get(
                "Maharashtra"
            )

            if (
                source_status.get("status") == "success"
                and maharashtra_data
            ):
                maharashtra_data["last_checked"] = (
                    source_status.get("last_checked")
                )

    save_data(data)

    print()
    print("========================================")

    if changed_sources:

        print("⚠️ CHANGES DETECTED:")

        for source in changed_sources:
            print("   •", source)

        print()
        print(
            "⚠️ Manual verification is required "
            "before changing calculator values."
        )

    if failed_sources:

        print()
        print("❌ SOURCES COULD NOT BE CHECKED:")

        for source in failed_sources:
            print("   •", source)

    if not changed_sources and not failed_sources:

        print("✅ All official sources checked.")
        print("✅ No changes detected.")

    elif not changed_sources and failed_sources:

        print()
        print(
            "⚠️ No changes detected in the "
            "sources that were successfully checked."
        )
        print("⚠️ Some sources could not be verified.")

    print("========================================")
    print()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    update_sources()