"""
read festival_location_test.txt and artist_test.txt
festival_location_test.txt contains the festival name, country, and city of the festivals in the test set, separated by semicolons.
artist_test.txt contains the unique names of the artists in the test set, one per line.
randomly select a subset of the festivals and artists, and save them to a new file called festival_location_test_subset.txt and artist_test_subset.txt, respectively.
the number of festivals and artists to select can be specified by the user, and should be less than or equal to the total number of festivals and artists in the test set.
"""

import os
import random
from pathlib import Path

def main():
    num_festivals = 50
    num_artists = 50
    dataset_name = 'tkgl_concert2'
    # Get the directory of the current script
    script_dir = Path(__file__).parent


    # File paths
    festival_file = script_dir / dataset_name / "llm" / "festival_location_test.txt"
    artist_file = script_dir / dataset_name / "llm" / "artist_test.txt"
    festival_subset_file = script_dir / dataset_name / "llm" / "festival_location_test_subset.txt"
    artist_subset_file = script_dir / dataset_name / "llm" / "artist_test_subset.txt"
    all_quads_file = script_dir / dataset_name / "llm" / "string_edgelist.txt"
    all_quads_mbid_file = script_dir / dataset_name / "llm" / "mbid_string_edgelist.txt"


    # Read festival and artist data
    with open(festival_file, 'r', encoding='utf-8') as f:
        festivals = f.readlines()
    
    with open(artist_file, 'r', encoding='utf-8') as f:
        artists = [line.strip() for line in f.readlines()]
    

    
    # Validate input
    if num_festivals > len(festivals) or num_artists  > len(artists):
        print("Error: requested number exceeds available data")
        return
    
    # Randomly select subsets
    selected_festivals = random.sample(festivals, num_festivals)
    selected_artists = random.sample(artists, num_artists)
    
    selected_festivals_only_names = [line.split(';')[1] for line in selected_festivals]
    selected_artists_only_names = [line.split(';')[1] for line in selected_artists]

    # Write to output files
    with open(festival_subset_file, 'w', encoding='utf-8') as f:
        f.writelines(selected_festivals)
    
    with open(artist_subset_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(selected_artists))
    
    print(f"Saved {num_festivals} festivals to {festival_subset_file}")
    print(f"Saved {num_artists} artists to {artist_subset_file}")

    with open(all_quads_file, 'r', encoding='utf-8') as f:
        quads = f.readlines()
    with open(all_quads_mbid_file, 'r', encoding='utf-8') as f:
        quads_mbid = f.readlines()
    selected_quads_artists = []
    selected_quads_festivals = []
    for year in [2023, 2024, 2025]:
        selected_quads_artists = []
        selected_quads_festivals = []
        for quad in quads:
            head, rel, tail, timestamp = quad.strip().split('\t')
            if int(timestamp) !=  year:
                continue
            if head in selected_artists_only_names:
                selected_quads_artists.append(quad)
            if tail in selected_festivals_only_names:
                selected_quads_festivals.append(quad)
            name =  str(year) + "_quads_test_subset_artistswhichfestivals.txt"
            with open(script_dir / dataset_name / 'llm'/ name , 'w', encoding='utf-8') as f:
                f.writelines(selected_quads_artists)
            name =  str(year) + "_quads_test_subset_festivalswhichartists.txt"
            with open(script_dir / dataset_name / 'llm'/ name , 'w', encoding='utf-8') as f:
                f.writelines(selected_quads_festivals)
        selected_quads_artists_mbid = []
        selected_quads_festivals_mbid = []
        for quad in quads_mbid:
            head, rel, tail, timestamp = quad.strip().split('\t')
            if int(timestamp) !=  year:
                continue
            if head in selected_artists_only_names:
                selected_quads_artists_mbid.append(quad)
            if tail in selected_festivals_only_names:
                selected_quads_festivals_mbid.append(quad)
            name =  str(year) + "_quads_mbid_test_subset_artistswhichfestivals.txt"
            with open(script_dir / dataset_name / 'llm'/ name, 'w', encoding='utf-8') as f:
                f.writelines(selected_quads_artists_mbid)
            name =  str(year) + "_quads_mbid_test_subset_festivalswhichartists.txt"
            with open(script_dir / dataset_name / 'llm'/ name, 'w', encoding='utf-8') as f:
                f.writelines(selected_quads_festivals_mbid)

    print('done')

if __name__ == "__main__":
    main()