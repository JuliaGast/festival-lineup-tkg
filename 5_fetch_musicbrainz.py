import json
import musicbrainzngs
from pathlib import Path
import argparse
import csv
import os
import setlist_utils
import timeit




musicbrainzngs.set_useragent(
    "python-musicbrainzngs-example",
    "0.1",
    "emailadress@test.de", # set email adress here
)


def extract_artist_metainfo(artist_id, artists_dict):
    """
    extract_artist_metainfo: given in artist_id (musicbrainz id), fetches the metainfo for the artist and saves it in artists_dict, with key: artist_id. 
    The metainfo is stored under the key 'metainfo' in the dict for the artist.
    The metainfo includes the result of musicbrainzngs.get_artist_by_id with includes=["release-groups", "label-rels", 'tags'], release_type=["album", "ep"]. We also
    exclude certain keys that are not relevant for our analysis and take up a lot of space (e.g. ipi-list, isni-list, release-group-count, id)
    """
    result = {}
    # result['artist'] = {}
    try:
        result = musicbrainzngs.get_artist_by_id(artist_id,
              includes=["release-groups", "label-rels", 'tags'], release_type=["album", "ep"])

    except musicbrainzngs.WebServiceError as exc:
        print("Something went wrong with the request: %s" % exc)
        print(f"Error fetching info for artist_id {artist_id}, skipping this artist.")

    if len(result) >0:
        for key_to_remove in ['ipi-list', 'isni-list', 'release-group-count', 'id']:
            if key_to_remove in result['artist']:
                result['artist'].pop(key_to_remove)

            if not artist_id in artists_dict:
                artists_dict[artist_id] = {}
            artists_dict[artist_id]['metainfo'] = result['artist']


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

data_dir = Path(__file__).resolve().parent / "data"
data_dir.mkdir(exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--artistinput", "-i", default="very_large_festival_artists_germany.csv", type=str)
parser.add_argument("--artistoutput", "-o", default="very_large_festival_artists_metainfo_germany.json", type=str)
parser.add_argument("--infooutput", "-if", default="very_large_festival_artists_metainfo_germany_all.json", type=str)
# parser.add_argument("--dailylimit", "-lim", default=1400, type=int) # hopefully will be changed to 50000 soon
args = parser.parse_args()

ARTISTS_INPUT = data_dir / args.artistinput
ARTISTS_OUTPUT= data_dir / args.artistoutput
output_path_backup = 'backup_' + args.artistoutput
ARTISTS_OUTPUT_BACKUP= data_dir / output_path_backup
ALL_ARTISTS_INFO_FILE = data_dir / args.infooutput
BACKUP_EVERY = 50  # how often to backup intermediate results

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
    for row in reader:
        artist_id = row["artist_id"]
        if artist_id not in all_artists_info:
            artists_to_fetch.append(artist_id)
artists_to_fetch = list(set(artists_to_fetch))  # unique artist ids  #changes order of csv potentially, but should be ok since we are not relying on the order of the csv for anything.
print(f"Fetching info for in total {len(artists_to_fetch)} artists")

artists_dict = {}

counter = 0
starttime = timeit.default_timer()

for artist_id in artists_to_fetch:      
    extract_artist_metainfo(artist_id, artists_dict)
    if counter % 10 == 0:
        elapsed = timeit.default_timer() - starttime
        if counter >0:
            print(f"Fetched info for {counter} artists so far. it took in total {elapsed:.2f} seconds, which is {(elapsed/counter):.2f} seconds per artist on average.")
    if counter % 5 ==0:
        write_json(artists_dict, counter)

    if BACKUP_EVERY and counter % BACKUP_EVERY == 0:
        write_backup(artists_dict, counter)
    counter+=1

write_json(artists_dict, counter)
write_backup(artists_dict, counter)

all_artists_info.update(artists_dict)
with open(ALL_ARTISTS_INFO_FILE, "w", encoding="utf-8") as f:
    json.dump(all_artists_info, f, indent=2, ensure_ascii=False)

with open('done_metainfo.txt', 'w', encoding='utf-8') as f:
    f.write("DONE")
print(f"in {ARTISTS_OUTPUT} we have info for this number of artists:", len(artists_dict))

print("Done")


