"""  
read a file entity2id.txt, which contains the mapping from entity name to entity id, and create a dict out of it, with the key being the entity id and the value being the entity name.


read a file, in the same folder as this, which is called festival_test.txt
for each line, it contains the name of the festival and the unique id of the festival in the dataset, separated by a semicolon. 
create a dict out of it, with the key being the unique id of the festival and the value being the name of the festival.

then read a file, in the same folder as this, which is called string_edgelist_test.txt, which is the test set of the edgelist with string node and relation names
for each line, it contains the head, relation, tail, and timestamp of an edge, separated by tabs.
if the relation is happens_in_venue, write it to a dict, with the key bein the head, and the value being the tail, if the timestamp is 2025.
if the key is alreay in the dict, print a warning.
"""

import os
import sys
from pathlib import Path
# Get the directory of the current script
script_dir = Path(__file__).parent
dataset_name = 'tkgl_concert2'
data_dir = script_dir / dataset_name
script_dir = script_dir / dataset_name / 'llm'

max_num = 50

# Read entity2id.txt and create entity dict
entity_dict = {}
with open(data_dir / "entity2id.txt", "r", encoding="utf-8") as f:
    for line in f:
        entity_id, entity_name  = line.strip().split("\t")
        entity_dict[entity_id] = entity_name

# Read festival_test.txt and create festival dict
festival_dict = {}
festival_dict_name2id = {}
with open(script_dir / "festival_test.txt", "r", encoding="utf-8") as f:
    for line in f:
        festival_id, name = line.strip().split(";")
        festival_dict[festival_id] = name
        if name in festival_dict_name2id:
            print(f"Warning: {name} already in festival_dict_name2id")
        festival_dict_name2id[name] = festival_id # also add the reverse mapping for convenience

# Read string_edgelist_test.txt and create venue dict
venue_dict = {}
with open(script_dir / "mbid_string_edgelist_test.txt", "r", encoding="utf-8") as f:
    for line in f:
        head, relation, tail, timestamp = line.strip().split("\t")
        if relation == "happens_in_venue" and timestamp == "2025":
            if head in venue_dict:
                print(f"Warning: {head} already in venue_dict")
            venue_dict[head] = tail

out_file = script_dir / "festival_location_test.txt"
with open(out_file, "w", encoding="utf-8") as f:
    for festival_id, festival_name in festival_dict.items():
        if festival_id in venue_dict:
            venue = venue_dict[festival_id]
            venue = entity_dict.get(venue, f'unknown_{venue}') 
            if '_' in venue:
                venue = venue.split('_')[-2] # take the second last part of the venue name before the underscore, which is usually the city name             
            if '-' in venue:
                a= venue.split('-')
                if 'rhein' in a:
                    venue = ''
                    for part in a[-5:-2]: # for venues with 'rhein' in the name, take the part of the venue name before the last dash, which is usually the city name
                        venue += part + '-'
 # for venues with 'rhein' in the name, take the second last part of the venue name before the dash, which is usually the city name
                else:
                    if len(a) >= 3:
                        venue = venue.split('-')[-3] # take the part of the venue name after the last dash, which is usually the city name
            f.write(f"{festival_id};{festival_name};Germany;{venue}\n")
        else:
            f.write(f"{festival_id};{festival_name};Germany;\n")

print(f"Saved festival locations to {out_file}")
print(f"Unique festivals: {len(festival_dict)}, Unique venues: {len(venue_dict)}")