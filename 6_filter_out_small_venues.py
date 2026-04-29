import json
import os

import numpy as np


INPUT_FILE_ARTISTS = os.path.join("data","very_large_festival_artists_info_germany.json")

MIN_NUMBER  = 5 # minimum number of concerts a venue must host to be included in the output file
OUTPUT_FILE_VENUES = os.path.join("data","large_venues"+str(MIN_NUMBER)+".txt")
if not os.path.exists(os.path.join("data")):
    os.makedirs(os.path.join("data"))


with open(INPUT_FILE_ARTISTS, "r", encoding="utf-8") as f:
    artist_data = json.load(f)


venue_dict = {}

for artist_key, artist_dict in artist_data.items():
    
    artist_mbid = artist_key
    artist_name = artist_dict["artist_name"]
    if artist_name is None:
        print(f"Warning: No artist name information for artist {artist_mbid}.")
        artist_name = artist_mbid
    
    if "Various Artists" in artist_name:
        print(f"Warning: artist {artist_mbid} has name {artist_name}, which contains 'Various Artists'. This is likely a compilation album or similar, and we will not add quads for this artist." )
        continue

    if artist_dict['events'] is None:
        print(f"Warning: No event information for artist {artist_name}. not adding quads for this artist.")
        continue


    for event_key, event in artist_dict["events"].items():
        if not event["venue_mbdid"] in venue_dict:
                venue_dict[event["venue_mbdid"]]= 0
        venue_dict[event["venue_mbdid"]] += 1

print(f"Number of unique venues: {len(venue_dict)}")
venues_to_include = set()
for venue_mbdid, count in venue_dict.items():
    if count >= MIN_NUMBER:
        venues_to_include.add(venue_mbdid)

print(f"Number of venues that host at least {MIN_NUMBER} concerts: {len(venues_to_include)}")
with open(OUTPUT_FILE_VENUES, "w", encoding="utf-8") as f:
    for venue_mbdid in venues_to_include:
        f.write(venue_mbdid + "\n")

print(f"List of venues that host at least {MIN_NUMBER} concerts written to {OUTPUT_FILE_VENUES}.")
