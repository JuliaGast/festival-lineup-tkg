# Code for the paper Tomorrow Never Knows: A Temporal Knowledge Graph for Music Festival Lineup Forecasting
Julia Gastinger, Thilo Dieing, Christian Meilicke, Heiner Stuckenschmidt

email: first.last[at]uni-mannheim.de

Paper currently under review.

The repository contains two parts: Part 1, The dataset creation, and Part 2,the TKG forecasting experiments.
For the forecasting experiments, please refer to the folder forecasting and the README therein.

The final datasets can be found at MADATA: https://madata.bib.uni-mannheim.de/822/

The following information is for the creation of the dataset.
If you directly want to run the Forecasting experiments, you can go to folder forecasting. Since the final datasets are stored on MADATA, you do not need to re-create them.

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

# Part 1: Dataset creation

## TODO before running the data creation script

* get an API key from https://www.setlist.fm/signin
* put that API key in a file called config.yaml `'API_KEY': 'yourapikey'`
* install requirements from `requirements.txt`. Please note: we have different requirements files for Part 1 and Part 2.


## A. collect all infos from setlist.fm and musicbrainz


### 1. Find all festivals and make a list with all available festivals
`1_get_all_festivals.py` to extract all festivals from: url = https://www.setlist.fm/festivals/browse/'+letter+'/page.html
and write in a csv file with columns: festival_name, festival_url, festival_id

e.g.
```
title,href,id
Southside Festival,festivals/southside-festival-bd6bdda.html,bd6bdda
```

Output: `all_festivals.csv` which contains 75588 festivals

### 2. find editions of the festival and artists who play at the festival
`2_get_info_per_festival.py` to extract infos per festival stored in `all_festivals.csv`.

* find all editions of the festival (mostly one edition per year, e.g. https://www.setlist.fm/festival/2026/southside-festival-2026-6bd50e62.html)
* Currently: Limit this to festivals in Germany. This is set by `country_list = ["Germany"]`.
* for each festival create a dict with general info, editions, and artist per edition is created.
    ```
    "bd6bdda": {
        "general_info": {
        "festival_name": "Southside Festival",
        "festival_id": "bd6bdda",
        "festival_url": "https://www.setlist.fm/festivals/southside-festival-bd6bdda.html"
        },
        "editions": {
            "5bd59724": {
                "year": "2025",
                "start_date": "2025-06-19",
                "end_date": "2025-06-22",
                "edition_url": "festival/2025/southside-festival-2025-5bd59724.html",
                "name": "Southside Festival 2025",
                "venue": {
                "venue_url": "venue/take-off-gewerbepark-neuhausen-ob-eck-germany-7bd7ee88.html",
                "venue_name": "take-off GewerbePark, Neuhausen ob Eck, Germany",
                "venue_id": "7bd7ee88"
                },
                "artists": {
                    "8779d8dd-6a1d-483a-9402-36c1142a354e": {
                        "artist": "VICKY",
                        "url": "https://www.setlist.fm/setlist/vicky/2025/take-off-gewerbepark-neuhausen-ob-eck-germany-13441581.html",
                        "date": "2025-06-19T00:00:00"
                    },
                    "797df4ec-7574-444a-a731-7a7c107e6747": {
                        "artist": "ok.danke.tschüss",
                        "url": "https://www.setlist.fm/setlist/okdanketschuss/2025/take-off-gewerbepark-neuhausen-ob-eck-germany-1b44c5bc.html",
                        "date": "2025-06-19T00:00:00"
                    },
                    ...
                },
            "23d44877": {
                "year": "2024",
                "start_date": "2024-06-20",
                "end_date": "2024-06-23",
                "edition_url": "festival/2024/southside-festival-2024-23d44877.html",
                "name": "Southside Festival 2024",
                "venue": {
                "venue_url": "venue/take-off-gewerbepark-neuhausen-ob-eck-germany-7bd7ee88.html",
                "venue_name": "take-off GewerbePark, Neuhausen ob Eck, Germany",
                "venue_id": "7bd7ee88"
                },
                "artists": {
                    "a81cd4bd-2944-4040-8504-d373dd3b761b": {
                        "artist": "100 Kilo Herz",
                        "url": "https://www.setlist.fm/setlist/100-kilo-herz/2024/take-off-gewerbepark-neuhausen-ob-eck-germany-33572485.html",
                        "date": "2024-06-20T00:00:00"
                    },
                    "9a271000-2fa2-4c52-9925-487f4a4f0c15": {
                        "artist": "102 Boyz",
                        "url": "https://www.setlist.fm/setlist/102-boyz/2024/take-off-gewerbepark-neuhausen-ob-eck-germany-2357c05f.html",
                        "date": "2024-06-20T00:00:00"
                    },
                    ...
                    }
                }
            }
        }}
    ```
* artists contains info on all artists that played on that festival edition, with keys being the musicbrainz id
* store the results at `all_festivals_info.json` and '`all_festivals_info_backup.json`
* since the festivals are not accessible via the setlist.fm api, we webscrape the infos

### 3. Prune dataset: only the largest festivals
Reduce the festivals to contain only the more important/largest festivals with 
`3_filter_out_small_festivals.py`

Motivation:
* Taking into account all 75000 festivals (with all their multiple editions and artists) would be a bit too much for now
* Some festivals only have one edition with a very small number of artists. Assumption: These are too small and unimportant for predictions

Steps:
* make a new file `data/very_large_festivals_info_germany.json`
* only include festivals that have at least 5 editions and have at least 30 unique artists across all editions that have at least 10 artists per edition and are located in germany. This contains 380 festivals, the first one starting in 1971.
* corresponding to the above, make a file `very_large_festival_artists_germany.csv`
* include info for artists that performed at large festivals: artist id, e.g. "dcf54a6c-e09c-4980-be77-41401898fb7b", and artist name, e.g. "Right Said Fred". 
* ``` 
    artist_id,artist_name
    80ccbf0d-66eb-4c70-b89e-c08dc601a0de,Hiraes
    9a25682f-58cc-4b16-8161-a85b96c006d0,Skelfir
    ef53b1fc-aba3-410c-aa6a-5fa1eb805283,Dragonsfire
    ```

### 4. Find more (setlist.fm) infos for the bands that play on the largest festivals
For each of the artists in `very_large_festival_artists_germany.csv` find infos on events with `4_get_artists_and_venue_info.py`. 
* This can be slow, especially if you do not (yet) have the pro API from setlist.fm. Getting such a pri API can take months in our experience.
* write the output to `very_large_festival_artists_info_germany.json` and some infos to `all_artists_info.json`
* for each artist fetch infos on their events: events where they played, including event date, venue name (and mbid), city, country, latitude/longitude, and if avaiable, the tour this event belonged to
    ``` {
  "a03a1766-c951-4bc4-889e-5c46d7a21d3a": {
    "artist_name": "Eradicator",
    "events": {
      "335de845": {
        "event_date": "27-06-2025",
        "last_updated": "2025-01-13T18:58:22.430+0000",
        "venue_name": "Motorsport Arena Oschersleben",
        "venue_mbdid": "73d512bd",
        "city": "Oschersleben",
        "country": "DE",
        "latitude": 52.0333333,
        "longitude": 11.25,
        "url": "https://www.setlist.fm/setlists/eradicator-4bd7ab0e.html",
        "artist_tour": "N/A"
      },
      "734d9e69": {
        "event_date": "26-04-2025",
        "last_updated": "2025-12-16T08:43:47.770+0000",
        "venue_name": "Räucherei",
        "venue_mbdid": "2bd6d856",
        "city": "Kiel",
        "country": "DE",
        "latitude": 54.3213292610791,
        "longitude": 10.1348876953125,
        "url": "https://www.setlist.fm/setlists/eradicator-4bd7ab0e.html",
        "artist_tour": "N/A"
      },
      ...
        }
    }}
    ```

### 5. Find extended (musicbrainz) (meta)-infos for the bands that play on the largest festivals
Using `5_test_musicbrainz.py`

* For each artist from  `very_large_festival_artists_germany.csv` fetch meta-infos (e.g. genre, albums, labels) from musicbrainz via musicbrainz api
* given artist_id (musicbrainz id), fetches the metainfo for the artist and saves it in artists_dict, with key: artist_id. 
    The metainfo is stored under the key 'metainfo' in the dict for the artist.
    The metainfo includes the result of musicbrainz.get_artist_by_id with includes=["release-groups", "label-rels", 'tags'], release_type=["album", "ep"]. We also
    exclude certain keys that are not relevant for our analysis and take up a lot of space (e.g. ipi-list, isni-list, release-group-count, id)
* limit release types to EP and Album
* Example:
    ```
    "32cad9d4-06d9-417b-a37b-85950b364b06": {
        "metainfo": {
        "type": "Group",
        "name": "Trackologists",
        "sort-name": "Trackologists",
        "country": "DE",
        "area": {
            "id": "85752fda-13c4-31a3-bee5-0e5cb1f51dad",
            "name": "Germany",
            "sort-name": "Germany",
            "iso-3166-1-code-list": [
            "DE"
            ]
        },
        "begin-area": {
            "id": "20619e36-fca8-4499-bcc8-be01a3ea3e41",
            "name": "Leipzig",
            "sort-name": "Leipzig"
        },
        "life-span": {
            "begin": "2015"
        },
        "release-group-list": [
            {
            "id": "146a26f6-cce2-44ec-b9ba-ede3ee1f2465",
            "type": "Album",
            "title": "No Surrender, No Retreat",
            "first-release-date": "2016",
            "primary-type": "Album",
            "tag-list": [
                {
                "count": "1",
                "name": "electronic"
                },
                {
                "count": "1",
                "name": "industrial"
                },
                {
                "count": "1",
                "name": "rhythmic noise"
                }
            ]
            },
            {
            "id": "2418258e-be7e-4dd2-8586-89e85895f4ee",
            "type": "EP",
            "title": "Suicide With Plastic Gun - Remixes",
            "first-release-date": "2022-04-08",
            "primary-type": "EP"
            }
        ]
        }
    },
    ```

### 6. Reduce the venues
Only include venues that have at least 5 concerts with `6_filter_out_small_venues.py`. This will create a list and write it to `"data/large_venues"+str(MIN_NUMBER)+".txt"`.
in the next step, only venues that are in this list will be included in the quadruples

## B. From json to triples
Run 'make_artist_quads_from_json.py'
* User can select relation types with flags, and the extracted quadruples will be stored in a folder in data/quads/folder_name, where the folder_name includes all the relations that are included.
The output is 
* a file quads.txt with all quadruples, as well as quads_strings.txt with the textual represantion of all quadruples
* mapping files relation2id.txt, entity2id.txt, timestamp2int.txt, which maps the id (e.g. musicbrainz id) to the string representations.
* a file tkgl-concertX_edgelist.csv, which is needed as input for running the forecasting and evaluation. this contains also the quadruples in form timestamp,head,tail,relation_t
* *CAREFUL* the entity strings are not necessarily unique, there might be multiple bands with different musicbrainz ids that have the same string representations, e.g. 'ARTIST:Wolfpack' is shared by multiple nodes: ['15283004-6424-4a79-874e-5333f73b90ce', 'cd488676-5509-4ed5-b988-c220c7fe9c6f']. This is not a problem as long as you use the id representation, i.e. quads.txt or edgelist.csv





