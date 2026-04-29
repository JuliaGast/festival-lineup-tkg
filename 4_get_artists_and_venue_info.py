# if it doesn't exist, create file data/all_artists_info.json
# open data/all_artists_info.json
# open the respective artist file, e.g. data/very_large_festival_artists_germany.csv
# it contains artist_id,artist_name, e.g.:
# 80ccbf0d-66eb-4c70-b89e-c08dc601a0de,Hiraes
# for each artist_id in the csv, check if it exists in all_artists_info.json
# if not, fetch information from the API
# store the artist info in all_artists_info.json, and in  a file that belongs to the festival size category, e.g. data/very_large_festival_artists_info_germany.json

import setlist_utils
import os
from pathlib import Path
import yaml
import json
import csv
from pathlib import Path
from typing import Dict, Set
import argparse
import datetime
import time

config_path = Path(__file__).resolve().parent / "config.yaml"

if not config_path.exists():
    raise FileNotFoundError(f"config.yaml not found at {config_path}")

with config_path.open("r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}

API_KEY = cfg.get("API_KEY") or cfg.get("api_key")
if not API_KEY:
    raise KeyError("API_KEY not found in config.yaml (expected key 'API_KEY' or 'api_key')")

HEADERS = [{
    "Accept": "application/json",
    "x-api-key": API_KEY
}]

# do we have multiple API keys (to rotate in case of rate limits)?
if 'API_KEYS' in cfg:
    API_KEYS = cfg['API_KEYS']
    if not isinstance(API_KEYS, list) or not all(isinstance(key, str) for key in API_KEYS):
        print('only one API key found in config.yaml, using that one')
    else:
        print(f"Multiple API keys found in config.yaml, using all {len(API_KEYS)} keys in rotation")
        HEADERS = []
        for key in API_KEYS:
            h = {
                "Accept": "application/json",
                "x-api-key": key
            }
            HEADERS.append(h)
else:
    print('only one API key found in config.yaml, using that one')

def write_json(artists_dict, counter):
    if os.path.exists(ARTISTS_OUTPUT):
        with open(ARTISTS_OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.update(artists_dict)
    setlist_utils.safe_write_json(ARTISTS_OUTPUT, data)
    print(f"Intermediate write to {ARTISTS_OUTPUT} after {counter} artists.")

def write_backup(artists_dict, counter):
    # read the backup file if it exists
    backup_data = setlist_utils.safe_load_json(ARTISTS_OUTPUT_BACKUP)
    if not backup_data:
        backup_data = {}

    # read the main file if it exists
    main_data = setlist_utils.safe_load_json(ARTISTS_OUTPUT)
    if not main_data:
        main_data = {}

    # check which is larger
    if len(backup_data) >= len(main_data):
        larger_data = backup_data
        print("Using backup as larger data for merging.")
    else:
        larger_data = main_data

    # update the larger one with new data
    larger_data.update(artists_dict)

    # write it to backup file
    print(f"Creating backup at {ARTISTS_OUTPUT_BACKUP} after {counter} artists.")
    setlist_utils.safe_write_json(ARTISTS_OUTPUT_BACKUP, larger_data)

    # write it to main file
    setlist_utils.safe_write_json(ARTISTS_OUTPUT, larger_data)

def extract_artists_infos(artists,all_artists_info):
    counter = 0
    artists_dict ={}
    api_request_counters = 0
    starttime = datetime.datetime.now()
    for ARTIST_MBID in artists:
        counter+=1
        if counter % 10 ==0:
            print(f"Fetched info for {counter} artists")

        if ARTIST_MBID in all_artists_info:
            artists_dict[ARTIST_MBID] = all_artists_info[ARTIST_MBID]
        else:
            all_setlists, api_request_counters = setlist_utils.get_setlists_for_artist(ARTIST_MBID, HEADERS, api_request_counters)
            event_dict, artist_name, artist_mbid = setlist_utils.extract_setlist_data(all_setlists)
            # setlist_utils.save_events_to_csv(rows_actor, fieldnames_actor, filename=output_file)
            artists_dict[ARTIST_MBID] = {}
            artists_dict[ARTIST_MBID]["artist_name"] = artist_name
            artists_dict[ARTIST_MBID]["events"] = event_dict


        if counter % 5 ==0:
            write_json(artists_dict, counter)

        if BACKUP_EVERY and counter % BACKUP_EVERY == 0:
            write_backup(artists_dict, counter)

    return artists_dict# todo modify


data_dir = Path(__file__).resolve().parent / "data"
data_dir.mkdir(exist_ok=True)


parser = argparse.ArgumentParser()
parser.add_argument("--country", "-c", default='usa', type=str)
parser.add_argument("--infooutput", "-if", default="all_artists_info.json", type=str)
# parser.add_argument("--dailylimit", "-lim", default=1400, type=int) # hopefully will be changed to 50000 soon
args = parser.parse_args()

country = args.country
artistinput ="very_large_festival_artists_"+country+".csv"
artistoutput = "very_large_festival_artists_info_"+country+".json"
ARTISTS_INPUT = data_dir / artistinput
ARTISTS_OUTPUT= data_dir / artistoutput
output_path_backup = 'backup_' + artistoutput
ARTISTS_OUTPUT_BACKUP= data_dir / output_path_backup
ALL_ARTISTS_INFO_FILE = data_dir / args.infooutput
BACKUP_EVERY = 50  # how often to backup intermediate results
# REQUEST_LIMIT_PER_DAY = args.dailylimit -300 # -300 is for puffer

all_artists_info = {}
if ALL_ARTISTS_INFO_FILE.exists():
    with open(ALL_ARTISTS_INFO_FILE, "r", encoding="utf-8") as f:
        all_artists_info = json.load(f)

if ARTISTS_OUTPUT.exists():
    with open(ARTISTS_OUTPUT, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
    print(f"Merging existing data from {ARTISTS_OUTPUT} into all_artists_info")
    print(f"Existing data has info for {len(existing_data)} artists")
    all_artists_info.update(existing_data)
    print(f"After merging, all_artists_info has info for {len(all_artists_info)} artists")

if ARTISTS_OUTPUT_BACKUP.exists():
    with open(ARTISTS_OUTPUT_BACKUP, "r", encoding="utf-8") as f:
        backup_data = json.load(f)
    print(f"Merging existing data from {ARTISTS_OUTPUT_BACKUP} into all_artists_info")
    print(f"Backup data has info for {len(backup_data)} artists")
    print(f"Existing data has info for {len(existing_data)} artists")
    all_artists_info.update(backup_data)
    print(f"After merging, all_artists_info has info for {len(all_artists_info)} artists")



with open(ARTISTS_INPUT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    artists_to_fetch = []
    artists_of_importance = []
    for row in reader:
        artist_id = row["artist_id"]
        artists_of_importance.append(artist_id)
        if artist_id not in all_artists_info:
            artists_to_fetch.append(artist_id)
artists_to_fetch = list(set(artists_to_fetch))  # unique artist ids
print(f"needing info for in total {len(artists_of_importance)} artists")
print(f"among them, we already have some infos in all_artists_info. We need to fetch info for {len(artists_to_fetch)} artists.")

artists_dict = extract_artists_infos(artists_to_fetch, all_artists_info)

all_artists_info.update(artists_dict)

for artist_id in artists_of_importance:  # for output file, we want all artists of importance info, not only the ones we just fetched
    if artist_id not in artists_dict:
        if artist_id in all_artists_info:
            artists_dict[artist_id] = all_artists_info[artist_id]

# artists_dict = all_artists_info # for output file, we want all artists info, not only the ones we just fetched
with open(ALL_ARTISTS_INFO_FILE, "w", encoding="utf-8") as f:
    json.dump(all_artists_info, f, indent=2, ensure_ascii=False)
with open(ARTISTS_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(artists_dict, f, indent=2, ensure_ascii=False)


with open('done.txt', 'w', encoding='utf-8') as f:
    f.write("DONE")


print("in ARTISTS_OUTPUT we have info for this number of artists:", len(artists_dict))
print("in total we found this many events for these artists:", sum(len(artist_info["events"]) for artist_info in artists_dict.values()))
print("in total we have this many unique venues for these artists:", len(set(venue_info["venue_name"] for artist_info in artists_dict.values() for venue_info in artist_info["events"].values())))
print("in total we have this many unique countries for these artists:", len(set(venue_info["country"] for artist_info in artists_dict.values() for venue_info in artist_info["events"].values())))
print("in total we have this many unique cities for these artists:", len(set(venue_info["city"] for artist_info in artists_dict.values() for venue_info in artist_info["events"].values())))

print("Done")
