import json
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set
from tqdm import tqdm
DATA_DIR = Path("data")
ALL_FESTIVALS_FILE = DATA_DIR / "Germany_festivals_info.json"
LARGE_FESTIVALS_FILE = DATA_DIR / "large_festivals_info.json"
VERY_LARGE_FESTIVALS_FILE = DATA_DIR / "very_large_festivals_info.json"
VERY_LARGE_FESTIVALS_EUROPE_FILE = DATA_DIR / "very_large_festivals_info_europe.json"
LARGE_FESTIVAL_ARTISTS_FILE = DATA_DIR / "large_festival_artists.csv"
VERY_LARGE_FESTIVAL_ARTISTS_FILE = DATA_DIR / "very_large_festival_artists.csv" 
LARGE_FESTIVAL_ARTISTS_FILE_EUROPE = DATA_DIR / "large_festival_artists_europe.csv"
VERY_LARGE_FESTIVAL_ARTISTS_FILE_EUROPE = DATA_DIR / "very_large_festival_artists_europe.csv" 


EUROPEAN_COUNTRIES = ["Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Czechia", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia", "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine", "United Kingdom", "Vatican City", "Turkey", "England", "Scotland", "Wales", "Armenia", "Azerbaijan", "Cyprus", "Georgia"]
def load_all_festivals() -> Dict:
    with open(ALL_FESTIVALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f) 
    
def filter_festivals(festivals: Dict, min_editions: int, min_unique_artists: int,min_artists_per_edition:int) -> Dict:
    filtered_festivals = {}
    for fest_id, fest_data in tqdm(festivals.items(), desc=f"Filtering festivals (editions>={min_editions}, artists>={min_unique_artists})"):
        editions = fest_data.get("editions", {})
        if len(editions) < min_editions:
            continue
        unique_artists: Set[str] = set()
        for edition in editions.values():
            artists = edition.get("artists", {})
            if len(artists) < min_artists_per_edition:
                continue
            unique_artists.update(artists.keys())
        if len(unique_artists) < min_unique_artists:
            continue
        filtered_festivals[fest_id] = fest_data
    return filtered_festivals

def filter_festivals_country(festivals: Dict, min_editions: int, min_unique_artists: int,min_artists_per_edition:int, country_list:list) -> Dict:
    filtered_festivals = {}
    for fest_id, fest_data in tqdm(festivals.items(), desc=f"Filtering festivals (editions>={min_editions}, artists>={min_unique_artists})"):
        editions = fest_data.get("editions", {})
        if len(editions) < min_editions:
            continue
        unique_artists: Set[str] = set()
        for edition in editions.values():
            if edition.get("venue").get("venue_name").split(",")[-1].strip() not in country_list:
                continue
            artists = edition.get("artists", {})
            if len(artists) < min_artists_per_edition:
                continue
            unique_artists.update(artists.keys())
        if len(unique_artists) < min_unique_artists:
            continue
        filtered_festivals[fest_id] = fest_data
    return filtered_festivals

def extract_artists(festivals: Dict) -> Dict[str, str]:
    artists_dict = {}
    for fest_data in festivals.values():
        editions = fest_data.get("editions", {})
        for edition in editions.values():
            artists = edition.get("artists", {})
            for artist_id, artist_info in artists.items():
                artists_dict[artist_id] = artist_info["artist"]
    return artists_dict 

def save_festivals(festivals: Dict, filepath: Path):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(festivals, f, indent=2, ensure_ascii=False)   

def save_artists_csv(artists: Dict[str, str], filepath: Path):
    with open(filepath, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["artist_id", "artist_name"])
        for artist_id, artist_name in artists.items():
            writer.writerow([artist_id, artist_name])   
def main():     
    all_festivals = load_all_festivals()
    print(f"Total festivals loaded: {len(all_festivals)}")
    

    # very_large_festivals = filter_festivals(all_festivals, min_editions=5, min_unique_artists=30, min_artists_per_edition=10)
    # print(f"Very large festivals found: {len(very_large_festivals)}")
    # save_festivals(very_large_festivals, VERY_LARGE_FESTIVALS_FILE)
    # very_large_festival_artists = extract_artists(very_large_festivals)
    # print(f"Very large festival unique artists: {len(very_large_festival_artists)}")
    # save_artists_csv(very_large_festival_artists, VERY_LARGE_FESTIVAL_ARTISTS_FILE)

    # very_large_festivals_europe = filter_festivals_country(all_festivals, min_editions=5, min_unique_artists=30, min_artists_per_edition=10, country_list=EUROPEAN_COUNTRIES)
    # print(f"Very large festivals in Europe found: {len(very_large_festivals_europe)}")
    # save_festivals(very_large_festivals_europe, VERY_LARGE_FESTIVALS_EUROPE_FILE)
    # very_large_festival_artists_europe = extract_artists(very_large_festivals_europe)
    # print(f"Very large festival unique artists in Europe: {len(very_large_festival_artists_europe)}")
    # save_artists_csv(very_large_festival_artists_europe, VERY_LARGE_FESTIVAL_ARTISTS_FILE_EUROPE)

    # very_large_festivals_germany = filter_festivals_country(all_festivals, min_editions=5, min_unique_artists=30, min_artists_per_edition=10, country_list=["Germany"])
    # print(f"Very large festivals in Germany found: {len(very_large_festivals_germany)}")
    very_large_festivals_germany = filter_festivals_country(all_festivals, min_editions=5, min_unique_artists=30, min_artists_per_edition=10, country_list=["Germany"])
    print(f"Very large festivals in Germany found: {len(very_large_festivals_germany)}")
    save_festivals(very_large_festivals_germany, DATA_DIR / "2very_large_festivals_info_germany.json")
    very_large_festival_artists_germany = extract_artists(very_large_festivals_germany)
    print(f"Very large festival unique artists in Germany: {len(very_large_festival_artists_germany)}")
    save_artists_csv(very_large_festival_artists_germany, DATA_DIR / "2very_large_festival_artists_germany.csv")

    # large_festivals = filter_festivals(all_festivals, min_editions=3, min_unique_artists=10, min_artists_per_edition=5)
    # print(f"Large festivals found: {len(large_festivals)}")
    # save_festivals(large_festivals, LARGE_FESTIVALS_FILE)
    # large_festival_artists = extract_artists(large_festivals)
    # print(f"Large festival unique artists: {len(large_festival_artists)}")
    # save_artists_csv(large_festival_artists, LARGE_FESTIVAL_ARTISTS_FILE)
    

if __name__ == "__main__":
    main()  