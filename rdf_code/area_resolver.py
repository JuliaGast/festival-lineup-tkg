### find musicbrainz area for a given area string (e.g. city, country, region)


import requests
import time
import json
import os

# -------------------------
# CONFIG
# -------------------------

MB_URL = "https://musicbrainz.org/ws/2/area/"

HEADERS = {
    "User-Agent": "KG-builder/1.0 (dummy@yahoo.de)"
}

REQUEST_DELAY = 3.0   # stable safe value for MusicBrainz

CACHE_FILE = "./rdf/area_cache.json"
OUTPUT_FILE = "./rdf/resolved_areas.json"


# -------------------------
# SESSION (IMPORTANT)
# -------------------------

session = requests.Session()
session.headers.update(HEADERS)


# -------------------------
# CACHE LOAD/SAVE
# -------------------------

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def save_output(output):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


# -------------------------
# RATE LIMIT (SMOOTH, NOT BURSTY)
# -------------------------

_last_time = 0

def rate_limit():
    global _last_time
    now = time.time()
    diff = now - _last_time

    if diff < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - diff)

    _last_time = time.time()


# -------------------------
# SAFE REQUEST (NO SSL CHAOS)
# -------------------------

def safe_request(params):
    for i in range(5):
        try:
            rate_limit()

            r = session.get(
                MB_URL,
                params=params,
                timeout=15
            )

            r.raise_for_status()
            return r.json()

        except Exception as e:
            wait = 3 ** i
            print(f"[retry {i+1}] {e} → waiting {wait}s")
            time.sleep(wait)

    return None


# -------------------------
# MUSICBRAINZ LOOKUP
# -------------------------

def resolve_from_musicbrainz(name):
    data = safe_request({
        "query": name,
        "fmt": "json"
    })

    if not data or "areas" not in data:
        return None

    areas = data["areas"]
    if not areas:
        return None

    best = areas[0]

    return {
        "name": best.get("name", name),
        "mbid": best["id"]
    }


# -------------------------
# RESOLVE ONE AREA
# -------------------------

def resolve_area(name, cache):
    key = name.strip().lower()

    if key in cache:
        return cache[key]

    result = resolve_from_musicbrainz(name)

    if result:
        entry = {
            "name": result["name"],
            "mbid": result["mbid"],
            "uri": f"https://musicbrainz.org/area/{result['mbid']}"
        }
    else:
        entry = {
            "name": name,
            "mbid": None,
            "uri": f"https://tkgconcertevaluation.org/area/{name.replace(' ', '_')}"
        }

    cache[key] = entry
    return entry


# -------------------------
# MAIN PIPELINE
# -------------------------

def resolve_all_areas(area_list):
    cache = load_cache()
    # cache = {}
    output = {}

    # remove duplicates (CRITICAL)
    unique_areas = sorted(set(area_list))

    print(f"Resolving {len(unique_areas)} areas...")

    for i, area in enumerate(unique_areas):
        print(f"[{i+1}/{len(unique_areas)}] {area}")

        entry = resolve_area(area, cache)
        output[area.lower()] = entry

        # persist continuously (crash-safe)
        save_cache(cache)
        save_output(output)

    return output


# -------------------------
# EXAMPLE RUN
# -------------------------

if __name__ == "__main__":
    area_file = './rdf/output_areas_all.csv'
    with open(area_file, 'r', encoding='utf-8') as f:
        areas = [line.strip() for line in f if line.strip()]

    resolve_all_areas(areas)

    print("\nDONE")
    print("→ resolved_areas.json")
    print("→ area_cache.json")