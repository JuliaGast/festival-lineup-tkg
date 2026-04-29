"""
Read a json and construct quadruples from it
For now: read very_large_festivals_info_germany.json, and construct quadruples of the form
artist - performs_at_festival - festival - date
"""

import json
import os
import make_quads_utils 

output_name = "very_large_festivals_germany"
COUNTRY = "Germany"
granularity = "year" # month, year, day
output_name += "_" + granularity

# for creating the default dataset concert, as used in our paper, set the following to True, and all other to False:
# True: include_happens_in, include_performs_at_festival, include_performs_concert_at, include_releases, include_genretags, include_releasegenre, include_areas, include_type, include_labelinfo, include_venue_area
# False: include_triangles

# for creating the peformance only datast (concert_perform), set the following to True, and all other to False:
# True: include_performs_at_festival
# False: all others

# for creating the dataset with shortcuts (concert_shortcut), set the following to True, and all other to False:
# True: all
# False: None

include_happens_in= True  # if true, we will also add quads of the form festival - happens_in_venue - venue - date
include_performs_at_festival = True  # if true, we will add quads of the form artist - performs_at_festival - festival - date
include_performs_concert_at= True  #True #True #True # if true, we will add quads of the form artist - performs_at_festival - concertvenue - date
include_releases= True  #True #True
include_genretags= True  #True #True # will only be added if include_releases is True, as they are genre tags for the releases
include_releasegenre= True  #True # True
include_areas= True  #True #artist areas, e.g. birth place, founding place, area of activity
include_type= True  #True
include_labelinfo= True  #True # True #True # if true, we will add quads of the form artist - signed_to_label - label - date TODO
include_venue_area= True 
include_triangles = False #True  # we add additional relations between artist and country and so on (concert-shortcut)

if include_happens_in:
    output_name += "_happensin"
if include_performs_at_festival:
    output_name += "_performsat"
if include_performs_concert_at:
    output_name += "_performsconcertat"
if include_releases:
    output_name += "_releases"
if include_genretags:
    output_name += "_genretags"
if include_releasegenre:
    output_name += "_releasegenre"
if include_areas:
    output_name += "_areas"
if include_type:
    output_name += "_type"
if include_labelinfo:
    output_name += "_labelinfo"
if include_venue_area:
    output_name += "_venuearea"
if include_triangles:
    output_name += "_triangles"

INPUT_FILE = os.path.join("data","very_large_festivals_info_germany.json")
INPUT_FILE_ARTISTS = os.path.join("data","very_large_festival_artists_info_germany.json")
INPUT_FILE_METAINFOS = os.path.join("data","very_large_festival_artists_metainfo_germany.json")
INPUT_FILE_LARGE_VENUES = os.path.join("data","large_venues5.txt")
OUTPUT_FILE_IDS = os.path.join("data","quads", output_name,  "quads.txt")
OUTPUT_FILE_STRINGS = os.path.join("data","quads", output_name,  "quads_strings.txt")
OUTPUT_FILE_KEYDICT = os.path.join("data","quads", output_name, "keydict.json")
ENTITY_TO_ID_FILE = os.path.join("data","quads", output_name, "entity2id.txt")
RELATION_TO_ID_FILE = os.path.join("data","quads", output_name, "relation2id.txt")
TIMESTAMP_TO_INT_FILE = os.path.join("data","quads", output_name, "timestamp2int.txt")
OUTPUT_FILE_EDGELIST_TGB = os.path.join("data","quads", output_name, "tkgl-concert5_edgelist.csv")


if not os.path.exists(os.path.join("data","quads", output_name)):
    os.makedirs(os.path.join("data","quads", output_name))


def main():
    ## open all sorts of files
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with open(INPUT_FILE_ARTISTS, "r", encoding="utf-8") as f:
        artist_data = json.load(f)
    
    with open(INPUT_FILE_METAINFOS, "r", encoding="utf-8") as f:
        metainfos = json.load(f)

    # read a file that contains info on the large venues. we do only add "large venues" as have been extracted with filter_out_small_venues.py
    large_venues = make_quads_utils.read_large_venues(INPUT_FILE_LARGE_VENUES)
        
    ## initialize the relation_id_to_string dictionary based on the included relations
    relation_id_to_string = make_quads_utils.initialize_relation_id_to_string(include_happens_in, include_performs_at_festival, include_performs_concert_at, include_releases, include_genretags, include_releasegenre, include_areas, include_type, include_venue_area, include_triangles)
       
    quads = []
    mbid_to_string ={}
    ## extract the quads from the different information sources and add them to the list of quads, and also fill the mbid_to_string and relation_id_to_string dictionaries
    quads, mbid_to_string = make_quads_utils.include_festival_quads_method(data, quads, mbid_to_string, include_happens_in, include_venue_area, include_performs_at_festival, include_triangles, output_name, country=COUNTRY)
    quads, mbid_to_string = make_quads_utils.include_concert_quads_method(artist_data, quads, metainfos, mbid_to_string, large_venues, include_performs_concert_at, include_venue_area, include_triangles)
    quads, mbid_to_string, relation_id_to_string  = make_quads_utils.include_meta_info_method(metainfos, quads, mbid_to_string, relation_id_to_string, include_releases, include_releasegenre, include_areas, include_type, include_labelinfo, include_genretags, include_triangles, granularity=granularity)
    
    print(len(quads), 'quads before adjusting timestamps for granularity')

    # adjust timestamps for granularity
    quads = make_quads_utils.granularity_quads(granularity, quads)
    # remove duplicates
    quads = list(set(tuple(x) for x in quads))
    # sort by last column (date)
    sorted_quads = sorted(quads, key=lambda x: x[-1])

    timestamp_ints, timestamps_int_map = make_quads_utils.make_timestamp_ints(sorted_quads, granularity=granularity)

    # get the string representations of the quads for easier readability in output_file_strings, and also create the edgelist for tgb format (timestamp, head, tail, relation
    # careful: the string representations quads_strings are not unique, e.g. releases with title "greatest hits"
    sorted_quads_strings = []
    edgelist_tgb = []
    for quad in sorted_quads:
        sorted_quads_strings.append((mbid_to_string[quad[0]], relation_id_to_string[quad[1]], mbid_to_string[quad[2]], quad[3]))
        edgelist_tgb.append((str(timestamps_int_map[quad[3]]), quad[0], quad[2], quad[1])) # timestamp, head, tail, relation_type

    print('We have the following number of quads:')
    print(len(sorted_quads_strings))
    print(len(sorted_quads))
    
    ## write all sort of files
    with open(OUTPUT_FILE_IDS, "w", encoding="utf-8") as f:
        # open in write mode to overwrite if file exists
        for quad in sorted_quads:
            f.write(",".join(quad) + "\n")

    with open(OUTPUT_FILE_STRINGS, "w", encoding="utf-8") as f:
        for quad in sorted_quads_strings:
            f.write(",".join(quad) + "\n")
        
    with open(OUTPUT_FILE_KEYDICT, "w", encoding="utf-8") as f:
        json.dump(mbid_to_string, f, indent=4)

    with open(OUTPUT_FILE_EDGELIST_TGB, "w", encoding="utf-8") as f:
        f.write("timestamp,head,tail,relation_type\n")
        for edge in edgelist_tgb:
            f.write(",".join(edge) + "\n")

    
    with open(ENTITY_TO_ID_FILE, "w", encoding="utf-8") as f:
        for entity, id in mbid_to_string.items():
            f.write(f"{entity}\t{id}\n")
    
    
    with open(RELATION_TO_ID_FILE, "w", encoding="utf-8") as f:
            for relation, id in relation_id_to_string.items():
                f.write(f"{relation}\t{id}\n")
    
    
    with open(TIMESTAMP_TO_INT_FILE, "w", encoding="utf-8") as f:
        for timestamp, id in timestamps_int_map.items():
            f.write(f"{id}\t{timestamp}\n")

if __name__ == "__main__":
    main()