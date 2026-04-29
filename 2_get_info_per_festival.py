from pathlib import Path

import requests
import setlist_utils
import os
import yaml
import json
import timeit
import time

starttime = timeit.default_timer()
print('start')
country_list = ["Germany"] #we only include festivals that have at least one edition in these countries.  allows us to filter out festivals that are not relevant for our analysis
country_string = "_".join(country_list)
data_dir = Path(__file__).resolve().parent / "data"
data_dir.mkdir(exist_ok=True)
data_path_festivals_in = os.path.join(data_dir, "all_festivals_start_ausklang.csv")
data_path_festivals_out_csv = os.path.join(data_dir, f"{country_string}_festivals_info.csv")
data_path_festivals_out_json = os.path.join(data_dir, f"{country_string}_festivals_info.json")
data_path_festivals_backup_json = os.path.join(data_dir, f"{country_string}_festivals_info_backup.json")
old_festival_info_json = os.path.join(data_dir, f"all_festivals_info_backup.json") # we save the old festival info json before overwriting it with the new data, so that we can compare the old and new data and check for any discrepancies or changes.

# config stuff, load api key
config_path = Path(__file__).resolve().parent / "config.yaml"

if not config_path.exists():
    raise FileNotFoundError(f"config.yaml not found at {config_path}")

with config_path.open("r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}

API_KEY = cfg.get("API_KEY") or cfg.get("api_key")
if not API_KEY:
    raise KeyError("API_KEY not found in config.yaml (expected key 'API_KEY' or 'api_key')")

HEADERS = {
    "Accept": "application/json",
    "x-api-key": API_KEY
}

BACKUP_EVERY = cfg.get("BACKUP_EVERY") or 200

festival_dict = setlist_utils.read_festival_csv_to_dict(data_path_festivals_in) # key: festival_id, value: (festival_name, festival_url)
a = 1
print("Loading existing JSON...")

old_festival_dict = setlist_utils.safe_load_json(old_festival_info_json)

data = setlist_utils.safe_load_json(data_path_festivals_out_json)

if not data:
    print("Main file empty or corrupted. Trying backup…")
    data = setlist_utils.safe_load_json(data_path_festivals_backup_json)

if not data:
    print("No valid backup found. Starting fresh.")
else:
    print(f"Loaded {len(data)} festivals from previous run.")

all_festival_info_dict = {}
print('starting with festivals')
# Create ONE global session
session = requests.Session()
session.headers.update(HEADERS)
    
for festival_id, (festival_name, festival_url) in festival_dict.items():
    if festival_id in data:
        continue
    festival_url_full_basic = "https://www.setlist.fm/" + festival_url # construct full URL
    print(f"Fetching festival edition page: {festival_url_full_basic}")
    # here i need to differentiate between the different editions of the festival
    # each edition has its own page (and id!), e.g. https://www.setlist.fm/festival/2025/reading-festival-2025-73d5826d.html

    festival_year_dict = {}
    for page in range(1, 20): # we try to fetch up to 20 pages of editions for each festival, but most festivals have much less than that
        # we add the info of each additonal page to the same festival_year_dict, which is then used to extract the info for each edition of the festival. 
        # if we encounter a page with no editions, we break the loop and move on to the next festival

        festival_url_full = festival_url_full_basic.replace(".html", f".html?page={page}")
        response, retries = setlist_utils.fetch_with_retry_festival(festival_url_full, retries=5, delay=1, session=session)
        if response.status_code != 200:
            # print(f"Failed to fetch page {festival_url_full}. Status code: {response.status_code}")
            break
        festival_year_dict = setlist_utils.parse_festival_editions_page(response.content, festival_year_dict) # key: festival_edition_id (for a year), value: (year, href, name)
    for festival_edition_id, (year, festival_edition_url, name, start_date_date, end_date_date) in festival_year_dict.items(): # [festival_edition_id] = (year, href, name)

        # check if we already have artists for that festival, that edition. 
        # if yes, we can skip the fetching and parsing of the edition page, and just add the edition info (year, name, dates) to the festival info dict. 
        if festival_id in old_festival_dict:
            if festival_edition_id in old_festival_dict[festival_id]["editions"]:
                artists = old_festival_dict[festival_id]["editions"][festival_edition_id].get("artists", {})
                
                if len(artists) > 0:
                    old_venue_name = old_festival_dict[festival_id]["editions"][festival_edition_id].get("venue", {}).get("venue_name", "")
                    if old_venue_name.split(",")[-1].strip() not in country_list:
                        # print(f"Skipping edition {festival_edition_id} of festival {festival_id} since venue {old_venue_name} is not in the specified country list.")
                        break # if the edition is not in the specified country list, we skip this edition entirely (no artists extracted), and also skip the rest of the editions for this festival, since we only want festivals that happen specified country list. assumption: all editions in the same country.

                    if festival_id not in all_festival_info_dict:
                        all_festival_info_dict[festival_id] = {
                            "general_info": {
                                "festival_name": festival_name,
                                "festival_id": festival_id,
                                "festival_url": festival_url_full_basic
                            },
                            "editions": {}
                        }                    
                    all_festival_info_dict[festival_id]["editions"][festival_edition_id] =  old_festival_dict[festival_id]["editions"][festival_edition_id]
                    continue

        # if we do not have artist info for that edition, we need to fetch and parse the edition page to extract the artist info.
        festival_edition_url_full = "https://www.setlist.fm/" + festival_edition_url
        resp,retries = setlist_utils.fetch_with_retry_festival(festival_edition_url_full, retries=5, delay=1, session=session)
        if resp.status_code != 200:
            print(f"Failed to fetch page {festival_edition_url_full}. Status code: {resp.status_code}")
            continue
        festival_artists, venue, is_in_country_flag = setlist_utils.parse_festival_oneyear_page(resp.content, country_list=country_list, session=session) # we only extract the artists for the edition if the edition is in the specified country list, otherwise we skip this edition entirely (no artists extracted), and also skip the rest of the editions for this festival, since we only want festivals that happen specified country list. assumption: all editions in the same country.
        if festival_artists is None:
            print(f"Failed to parse festival edition page {festival_edition_url_full} for festival {festival_id} {name}. Skipping this edition.!!!!!")

        if not is_in_country_flag:
            venue_name = venue.get("venue_name", "")
            print(f"Skipping festival edition {festival_edition_id} of festival {festival_id} since venue {venue_name} is not in the specified country list.")
            break # if the edition is not in the specified country list, we skip this edition entirely (no artists extracted), and also skip the rest of the editions for this festival, 
            #since we only want festivals that happen specified country list. assumption: all editions in the same country.
        print(f'adding info for festival edition {festival_edition_id} on {festival_edition_url_full} for festival {festival_id} to dict')
        if not festival_id in all_festival_info_dict:
            all_festival_info_dict[festival_id] = {
                "general_info": {
                    "festival_name": festival_name,
                    "festival_id": festival_id,
                    "festival_url": festival_url_full_basic
                },
                "editions": {}
            }
        all_festival_info_dict[festival_id]["editions"][festival_edition_id] = {
            "year": year,
            "start_date": start_date_date, 
            "end_date": end_date_date,
            "edition_url": festival_edition_url,
            "name": name,
            "venue": venue,
            "artists": festival_artists
        }


    if a % 30 == 0:
        if os.path.exists(data_path_festivals_out_json):
            with open(data_path_festivals_out_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data.update(all_festival_info_dict)
        setlist_utils.safe_write_json(data_path_festivals_out_json, data)
        print(f"Intermediate write to {data_path_festivals_out_json} after {a} festivals.")
        midtime = timeit.default_timer()
        print(f"time: {midtime - starttime} seconds")
        time.sleep(2)  # sleep to respect rate limits
    if BACKUP_EVERY and a % BACKUP_EVERY == 0:
        # read the backup file if it exists
        backup_data = setlist_utils.safe_load_json(data_path_festivals_backup_json)
        if not backup_data:
            backup_data = {}

        # read the main file if it exists
        main_data = setlist_utils.safe_load_json(data_path_festivals_out_json)
        if not main_data:
            main_data = {}

        # check which is larger
        if len(backup_data) >= len(main_data):
            larger_data = backup_data
            smaller_data = main_data
            print("Using backup as larger data for merging.")
        else:
            larger_data = main_data
            smaller_data = backup_data

        # update the larger one with new data
        larger_data.update(all_festival_info_dict)

        # write it to backup file
        print(f"Creating backup at {data_path_festivals_backup_json} after {a} festivals.")
        setlist_utils.safe_write_json(data_path_festivals_backup_json, larger_data)

        # write it to main file
        setlist_utils.safe_write_json(data_path_festivals_out_json, larger_data)

    a += 1

# --- WRITE JSON ---
setlist_utils.safe_write_json(data_path_festivals_out_json, all_festival_info_dict)

endtime = timeit.default_timer()
print(f"Execution time: {endtime - starttime} seconds")
# setlist_utils.write_festival_info_dict_to_csv(all_festival_info_dict, data_path_festivals_out_csv)
