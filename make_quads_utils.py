"""
all sorts of utils functions to extract quadruples from json files
"""

from datetime import datetime, timedelta
import calendar
import re
import numpy as np
from dateutil.relativedelta import relativedelta  # pip install python-dateutil
import pycountry




def parse_date(value: str) -> datetime:
    value = str(value)  # handles np.str_ and similar

    if len(value) == 4:              # "YYYY"
        value = f"{value}-01-01"
    elif len(value) == 7:            # "YYYY-MM"
        value = f"{value}-01"

    return datetime.fromisoformat(value)

def parse_release_date(s):
    s = s.strip()
    if '?' in s:
        s = s[:4]
    # YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return datetime.strptime(s, "%Y-%m-%d")
    # YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}", s):
        # choose convention: first of month
        year = int(s[:4])
        month = int(s[5:7])
        last_day = calendar.monthrange(year, month)[1]  # e.g. (weekday, 30) -> 30
        return datetime.strptime(f"{year}-{month:02d}-{last_day}", "%Y-%m-%d")
    # YYYY
    if re.fullmatch(r"\d{4}", s):
        # choose convention: first of year
        return datetime.strptime(s + "-12-31", "%Y-%m-%d")
    raise ValueError(f"Unsupported date format: {s}")

def make_timestamp_list(start_date, end_date, granularity, full_flag=False):
    # 1create continuous timestamps (daily)
    full_timestamps = []
    current = start_date
    while current <= end_date:
        if granularity == "month":
            if full_flag:
                full_timestamps.append(current.strftime("%Y-%m-%dT00:00:00")) # set day to 1
            else:
                full_timestamps.append(current.strftime("%Y-%m")) # set day to 1, and we only want year and month
            current += relativedelta(months=1)
        elif granularity == "year":
            if full_flag:
                full_timestamps.append(current.strftime("%Y-%m-%dT00:00:00")) # set month and day to 1
            else:
                full_timestamps.append(current.strftime("%Y")) # set month and day to 1, and we only want the year
            current += relativedelta(years=1)
        else:
            full_timestamps.append(current.strftime("%Y-%m-%dT00:00:00"))
            current += timedelta(days=1)
    return full_timestamps

def initialize_relation_id_to_string(include_happens_in, include_performs_at_festival, include_performs_concert_at, include_releases, include_genretags, include_releasegenre, include_areas, include_type, include_venue_area, include_triangles):
    """ Initialize the relation_id_to_string dictionary based on the included relations."""
    relation_id_to_string = {}
    if include_happens_in:
        relation_id_to_string["happens_in_venue"] = "happens_in_venue"
    if include_performs_at_festival:
        relation_id_to_string["performs_at_festival"] = "performs_at_festival"
    if include_performs_concert_at:
        relation_id_to_string["performs_concert_at"] = "performs_concert_at"
    if include_releases:
        relation_id_to_string["releases_album"] = "releases_album"
        relation_id_to_string["releases_ep"] = "releases_ep"
    if include_releasegenre:        
        if include_triangles:    # we include additional triples to have shorter hops between important information such aus artist the genre of their releases 
            relation_id_to_string["releases_album_of_genre"] = "releases_album_of_genre"
            relation_id_to_string["releases_ep_of_genre"] = "releases_ep_of_genre"
    if include_genretags:
        relation_id_to_string["has_genre"] = "has_genre"
    if include_areas:
        relation_id_to_string["has_begin_area"] = "has_begin_area"
        relation_id_to_string["has_area"] = "has_area"
    if include_type:
        relation_id_to_string["has_type"] = "has_type"
    if include_venue_area:
        relation_id_to_string["venue_has_location"] = "venue_has_location"
        relation_id_to_string["location_has_country"] = "location_has_country"        
        if include_triangles: # we include additional triples to have shorter hops between important information such aus artist and performing country 
            relation_id_to_string["performs_festival_in_country"] = "performs_festival_in_country"
            relation_id_to_string["performs_festival_in_location"] = "performs_festival_in_location"
            # relation_id_to_string["venue_has_country"] = "venue_has_country"
            # relation_id_to_string["event_has_location"] = "event_has_location"
            # relation_id_to_string["event_has_country"] = "event_has_country"
    if include_venue_area and include_performs_concert_at:
        if include_triangles:
            relation_id_to_string["performs_concert_in_location"] = "performs_concert_in_location"
            relation_id_to_string["performs_concert_in_country"] = "performs_concert_in_country" 

    return relation_id_to_string

def make_timestamp_ints(quads, granularity):
    timestamps = np.array(quads)[:,3]
    start_date = min(timestamps)
    end_date = max(timestamps)
    timestamps_int_map = {}

    # known start and end
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    full_timestamps = make_timestamp_list(start_date, end_date, granularity)


    for i, ts in enumerate(full_timestamps):

        timestamps_int_map[ts] = i

    timestamp_ints = []
    for _,_,_,ts in quads:
        timestamp_ints.append(timestamps_int_map[ts])

    return timestamp_ints, timestamps_int_map

def read_large_venues(input_file_large_venues):
    # if this file does not exist: run filter_out_small_venues.py first to create it, 
    # or set include_performs_concert_at to False to not use this file
    large_venues = set()
    with open(input_file_large_venues, "r", encoding="utf-8") as f:
        for line in f:
            large_venues.add(line.strip())
    return large_venues

def get_festival_venue_area(venue, country):
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
    area_name = venue[:1].upper() + venue[1:].lower() # capitalize first letter
    country = country[:1].upper() + country[1:].lower() # capitalize first letter
    return area_name, country

def granularity_quads(granularity, quads):
    """ Adjust the timestamps of the quads according to the specified granularity (day, month, year).
    """
    if granularity != "day":

        counter = 0
        for head, relation, tail, timestamp in quads:
            if granularity == "month":
                timestamp = timestamp[:7] + "-01T00:00:00" # set day to 1
                timestamp_string = timestamp[:7] #  we only want the month and year
            elif granularity == "year":
                timestamp = timestamp[:4] + "-01-01T00:00:00" # set month and day to 1
                timestamp_string = timestamp[:4]   # we only want the year

            quads[counter] = (head, relation, tail, timestamp_string)
            # quads_strings[counter] = (mbid_to_string[head], relation, mbid_to_string[tail], timestamp_string)
            counter+=1
    print(len(quads), 'quads after adjusting timestamps for granularity')
    return quads

def include_festival_quads_method(data, quads, mbid_to_string, include_happens_in, include_venue_area,include_performs_at_festival, include_triangles, output_name, country):
    counter = 0
    for festival_key, festival_dict in data.items():
        festival_mbid = festival_key
        festival_name = festival_dict["general_info"]['festival_name']
        festival_id = festival_dict["general_info"]['festival_id']
        assert festival_mbid == festival_id

        if "SUB" in output_name:            
            if np.random.rand() > 0.2: # we only add 20% of the festivals editions that happened in 2025, to have a smaller subset for testing
                continue
            latest_date = datetime(1971, 1, 1) 
            for edition_key, edition in festival_dict["editions"].items():
                dates_end = edition['end_date']
                end = datetime.strptime(dates_end, "%Y-%m-%d")
                if end > latest_date:
                    latest_date = end
            if latest_date < datetime(2025, 1, 1): # we only add festivals that have at least one edition in 2025 for the SUB version, to have a smaller subset for testing
                continue

        if not festival_mbid in mbid_to_string:
            mbid_to_string[festival_mbid] = 'FESTIVAL:' + festival_name.replace(", ", "_") # remove commas to avoid issues in csv


        for edition_key, edition in festival_dict["editions"].items():
            dates_start = edition['start_date']
            dates_end = edition['end_date']
            start = datetime.strptime(dates_start, "%Y-%m-%d")
            end = datetime.strptime(dates_end, "%Y-%m-%d")

            if start < datetime(1971, 1, 1) or end < datetime(1971, 1, 1) or start > datetime(2025, 12, 31) or end > datetime(2025, 12, 31):
                # print(f"Warning: edition {edition_key} of festival {festival_name} has start date {start} and end date {end}, which is outside of the range 1971-01-01 to 2025-12-31. not adding quads for this edition.")
                continue




            add_venue = True
            add_venue_area = False            
            
            # do we have some sort of venue information? if not, we will not add the venue to the quads, but we will still add the artist - performs_at_festival - festival - date quads
            if edition['venue'] is None:
                add_venue = False
                print(f"Warning: No venue information for edition {edition_key} of festival {festival_name}. not adding venue.")
            if edition['venue']["venue_id"] is None:                
                if edition['venue']['venue_url'] is not None:
                    edition['venue']["venue_id"] = edition['venue']['venue_url']
                    edition['venue']["venue_name"] = edition['venue']['venue_url']
                   
                else: 
                    print(f"Warning: No venue_ID information for edition {edition_key} of festival {festival_name}. not adding venue to quads.")
                    add_venue = False

            if add_venue and include_happens_in:    
                venue = edition['venue']["venue_id"].replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv

                if not venue in mbid_to_string:
                        mbid_to_string[venue] = 'VENUE:' + edition['venue']["venue_name"].replace(", ", "_")
                if venue is not None:
                    if include_venue_area and add_venue:
                        venue_area, venue_country = get_festival_venue_area(edition['venue']['venue_url'], country)  
                        venue_area = venue_area.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                        venue_country = venue_country.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                        add_venue_area = True        
                        if not venue_area in mbid_to_string:
                            mbid_to_string[venue_area] = 'AREA:' + venue_area.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                        if not venue_country in mbid_to_string:
                            mbid_to_string[venue_country] = 'AREA:' + venue_country.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv

                date_list = []
                current = start

                while current <= end:
                    date_list.append(current.strftime("%Y-%m-%dT00:00:00"))
                    current += timedelta(days=1)

                for date in date_list:
                    venue = edition['venue']["venue_id"].replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                    quads.append((festival_mbid, "happens_in_venue", venue, date))
                    # quads_strings.append((mbid_to_string[festival_mbid], "happens_in_venue", mbid_to_string[venue], date))
                    if add_venue_area:
                        quads.append((venue, "venue_has_location", venue_area, date))
                        quads.append((venue_area, "location_has_country", venue_country, date))
                        # quads_strings.append((mbid_to_string[venue], "venue_has_location", mbid_to_string[venue_area], date))
                        # quads_strings.append((mbid_to_string[venue_area], "location_has_country", mbid_to_string[venue_country], date))
                        
                        # if include_triangles:
                            # quads.append((festival_mbid, "event_has_location", venue_area, date))
                            # quads.append((festival_mbid, "event_has_country", venue_country, date))
                            # quads_strings.append((mbid_to_string[festival_mbid], "event_has_location", mbid_to_string[venue_area], date))
                            # quads_strings.append((mbid_to_string[festival_mbid], "event_has_country", mbid_to_string[venue_country], date))

                            # quads.append((venue, "venue_has_country", venue_country, date))
                            # quads_strings.append((mbid_to_string[venue], "venue_has_country", mbid_to_string[venue_country], date))

            for artist_id, artist_info in edition["artists"].items():
                if 'Various Artists' in artist_info['artist']:
                    print(f"Warning: artist {artist_id} has name {artist_info}, which contains 'Various Artists'. This is likely a compilation album or similar, and we will not add quads for this artist." )
                    continue
                
                if not artist_id in mbid_to_string:
                    mbid_to_string[artist_id] = 'ARTIST:' + artist_info['artist'].replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                artist_date = artist_info['date']

                if include_performs_at_festival:
                    quads.append((artist_id, "performs_at_festival", festival_mbid, artist_date))
                    # quads_strings.append((mbid_to_string[artist_id], "performs_at_festival", mbid_to_string[festival_mbid], artist_date))
                    if add_venue_area:
                        if include_triangles:
                            quads.append((artist_id, "performs_festival_in_location", venue_area, artist_date))
                            quads.append((artist_id, "performs_festival_in_country", venue_country, artist_date))
                            # quads_strings.append((mbid_to_string[artist_id], "performs_festival_in_location", mbid_to_string[venue_area], artist_date))
                            # quads_strings.append((mbid_to_string[artist_id], "performs_festival_in_country", mbid_to_string[venue_country], artist_date))
        counter +=1
        if 'MINI' in output_name and counter > 4:
            break
        if 'SUB' in output_name and counter > 10:
            break
    return quads, mbid_to_string


def include_concert_quads_method(artist_data, quads, metainfos, mbid_to_string, large_venues, include_performs_concert_at, include_venue_area,include_triangles ):
 
    counter = 0
    event_not_added_counter = 0
    event_added_counter = 0

    if include_performs_concert_at:
        for artist_key, artist_dict in artist_data.items():
            
            artist_mbid = artist_key
            artist_name = artist_dict["artist_name"]
            if artist_name is None:
                # in this case we need to get the artist name from metainfo from musicbrainz
                artist_name = metainfos.get(artist_mbid, {}).get('metainfo', {}).get('name', None)
                if artist_name is None: # might be that we still have no info
                    print(f"Warning: No artist name information for artist {artist_mbid}.")
                    artist_name = artist_mbid
            
            if "Various Artists" in artist_name:
                print(f"Warning: artist {artist_mbid} has name {artist_name}, which contains 'Various Artists'. This is likely a compilation album or similar, and we will not add quads for this artist." )
                continue

            if artist_dict['events'] is None:
                print(f"Warning: No event information for artist {artist_name}. not adding quads for this artist.")
                continue

            if not artist_mbid in mbid_to_string:
                continue

            for event_key, event in artist_dict["events"].items():
                if event["venue_mbdid"] not in large_venues:
                    event_not_added_counter +=1
                    continue
                event_date = event['event_date']
                event_date =  datetime.strptime(event_date, "%d-%m-%Y")
                event_date = event_date.strftime("%Y-%m-%dT00:00:00")
                venue_area = event['city']
                venue_country_code = event['country']
                country_tmp = pycountry.countries.get(alpha_2=venue_country_code)
                venue_country = country_tmp.name if country_tmp else venue_country_code
                if event_date < "1971-01-01T00:00:00" or event_date > "2025-12-31T00:00:00":
                    # print(f"Warning: event {event_key} of artist {artist_name} has date {event_date}, which is outside of the range 1971-01-01 to 2025-12-31. not adding quads for this event.")
                    continue

                
                if include_performs_concert_at:
                    event_added_counter +=1
                    if not event["venue_mbdid"] in mbid_to_string:
                        mbid_to_string[event["venue_mbdid"]]= 'VENUE:' + event["venue_name"].replace(", ", "_").replace(" ", "_").replace(",", "_").replace(";", "_")
                    quads.append((artist_mbid, "performs_concert_at", event["venue_mbdid"], event_date))
                    # quads_strings.append((mbid_to_string[artist_mbid], "performs_concert_at", mbid_to_string[event["venue_mbdid"]], event_date))

                    if include_venue_area:
                        venue_area = venue_area.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                        venue_country = venue_country.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                        if not venue_area in mbid_to_string:
                            mbid_to_string[venue_area] = 'AREA:' + venue_area.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                        if not venue_country in mbid_to_string:
                            mbid_to_string[venue_country] = 'AREA:' + venue_country.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv

                        quads.append((event["venue_mbdid"], "venue_has_location", venue_area, event_date))
                        # quads_strings.append((mbid_to_string[event["venue_mbdid"]], "venue_has_location", mbid_to_string[venue_area], event_date))
                        quads.append((venue_area, "location_has_country", venue_country, event_date))
                        # quads_strings.append((mbid_to_string[venue_area], "location_has_country", mbid_to_string[venue_country], event_date))

                        if include_triangles:
                            quads.append((artist_mbid, "performs_concert_in_location", venue_area, event_date))
                            quads.append((artist_mbid, "performs_concert_in_country", venue_country, event_date))
                            # quads_strings.append((mbid_to_string[artist_mbid], "performs_concert_in_location", mbid_to_string[venue_area], event_date))
                            # quads_strings.append((mbid_to_string[artist_mbid], "performs_concert_in_country", mbid_to_string[venue_country], event_date))
            counter +=1

    print(f"Finished processing performs_concert_at quads. Number of quads: {len(quads)}. ")
    print(f"Number of events not added due to not being in large venue: {event_not_added_counter}.")
    print(f"Number of events added: {event_added_counter}.")

    return quads, mbid_to_string


def include_meta_info_method(metainfos, quads, mbid_to_string, relation_id_to_string, include_releases, include_releasegenre, include_areas, include_type, include_labelinfo, include_genretags, include_triangles, granularity):

    counter =0
    if include_releases or include_releasegenre or include_areas or include_type or include_labelinfo:
        for meta_key, meta_info in metainfos.items():
            artist_mbdid = meta_key

            if not artist_mbdid in mbid_to_string:
                continue

            artist_begin_date_in = meta_info['metainfo'].get('life-span', {}).get('begin', None)
            artist_end_date_in = meta_info['metainfo'].get('life-span', {}).get('end', None)
            min_date =  datetime.fromisoformat("1971-01-01T00:00:00")
            max_date = datetime.fromisoformat("2025-12-31T00:00:00")
            if artist_begin_date_in is not None:
                try:
                    artist_begin_date = parse_release_date(artist_begin_date_in)
                    if artist_begin_date < min_date:
                        artist_begin_date = min_date
                except ValueError:
                    print(f"Warning: Invalid begin date for artist {artist_mbdid}: {artist_begin_date_in}")
                    artist_begin_date = None
                    artist_begin_date_in = None

                artist_end_date = max_date # in case we don't have an end date, we will set it to the max date in our dataset, so that we can add quads for all years for this artist
            if artist_end_date_in is not None:
                try:
                    artist_end_date = parse_release_date(artist_end_date_in)
                except ValueError:
                    print(f"Warning: Invalid end date for artist {artist_mbdid}: {artist_end_date_in}")
                if artist_end_date > max_date:
                    artist_end_date = max_date
            if artist_begin_date_in is not None:
                start_to_end_list = make_timestamp_list(artist_begin_date, artist_end_date, granularity=granularity, full_flag=True)
                if include_type:
                    include_type_quads_method(quads, mbid_to_string, meta_info, artist_mbdid, start_to_end_list)
                if include_areas:
                    quads, mbid_to_string = include_area_quads_method(quads, mbid_to_string, meta_info, artist_mbdid, artist_begin_date, start_to_end_list)
                if include_labelinfo:                                                   
                    quads, relation_id_to_string, mbid_to_string = include_labelinfo_method(meta_info, quads, relation_id_to_string, mbid_to_string, artist_begin_date, artist_end_date, artist_mbdid, artist_mbdid)
                
            quads, relation_id_to_string, mbid_to_string = include_releases_and_genres_methods(meta_info, artist_mbdid, quads, mbid_to_string, relation_id_to_string, include_releases, include_releasegenre, include_genretags, include_triangles)
            counter +=1


    return quads, mbid_to_string, relation_id_to_string 


def include_labelinfo_method(meta_info, quads, relation_id_to_string, mbid_to_string, artist_begin_date, artist_end_date, artist_mbdid, granularity):
    # print(mbid_to_string[artist_mbdid])
    if 'label-relation-list' in list(meta_info['metainfo'].keys()):
        for label_metainfo in meta_info['metainfo']['label-relation-list']:
            if 'type' in label_metainfo: # only append if we have a relation type, and if we have a 'label
                rel_type = label_metainfo['type'].replace(" ", "_").replace(",", "_")
                label_direction = label_metainfo.get('direction', None)
                if not rel_type in relation_id_to_string:
                    relation_id_to_string[rel_type] = rel_type
                if 'begin' in label_metainfo:
                    label_begin_date = label_metainfo['begin']
                    label_begin_date = parse_release_date(label_begin_date)
                else:
                    label_begin_date = artist_begin_date
                if 'end' in label_metainfo:
                    label_end_date = label_metainfo['end']
                    label_end_date = parse_release_date(label_end_date)
                else:
                    label_end_date = artist_end_date
                min_date =  datetime.fromisoformat("1971-01-01T00:00:00")
                max_date = datetime.fromisoformat("2025-12-31T00:00:00")
                if label_begin_date < min_date:
                    label_begin_date = min_date
                if label_end_date < min_date:
                    continue # if the end date is before the min date, we will not add quads for this label relation, as it is outside of our date range   
                if label_end_date > max_date:
                    label_end_date = max_date
                if 'label' in label_metainfo:
                    label_name = label_metainfo['label'].get('name', None)
                    label_id = label_metainfo['label'].get('id', None).replace("; ", "_").replace(";", "_").replace(" ", "_").replace(", ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                    if label_name is None or label_id is None:
                        continue
                    if not label_id in mbid_to_string:
                        mbid_to_string[label_id] = 'LABEL:' + label_name.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
                    if 'named_after_artist' in rel_type:
                        a =1
                    start_to_end_list = make_timestamp_list(label_begin_date, label_end_date, granularity=granularity, full_flag=True)
                    for labeldate in start_to_end_list:
                        if label_direction == 'backward':
                            quads.append((label_id, rel_type, artist_mbdid, labeldate))
                        else:
                            quads.append((artist_mbdid, rel_type, label_id, labeldate))

    return quads, relation_id_to_string, mbid_to_string


def include_releases_and_genres_methods(meta_info, artist_mbdid, quads, mbid_to_string, relation_id_to_string, include_releases, include_releasegenre, include_genretags, include_triangles):
    for release in meta_info['metainfo']['release-group-list']:
        release_id = release['id']
        if ";" in release_id:
            release_id = release_id.replace("; ", "_").replace(";", "_").replace(" ", "_").replace(", ", "_").replace(",", "_")
        if not 'primary-type' in release:
            continue
        if not 'first-release-date' in release:
            continue
        release_date = parse_release_date(release['first-release-date']) 
        release_date = release_date.strftime("%Y-%m-%dT00:00:00")
        
        if release_date < "1971-01-01T00:00:00" or release_date > "2025-12-31T00:00:00":
            # print(f"Warning: release {release_id} has date {release_date}, which is outside of the range 1971-01-01 to 2025-12-31. not adding quads for this release.")
            continue
        
        if include_releases:
            if not release_id in mbid_to_string:
                mbid_to_string[release_id] = 'RELEASE:' + release['title'].replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv

            if release['primary-type'] == "Album":
                quads.append((artist_mbdid, "releases_album", release_id, release_date))
            elif release['primary-type'] == "EP":
                quads.append((artist_mbdid, "releases_ep", release_id, release_date))
            else:
                if not "releases_other" in relation_id_to_string:
                    relation_id_to_string["releases_other"] = "releases_other"
                quads.append((artist_mbdid, "releases_other", release_id, release_date))
        if include_genretags:
            if 'tag-list' in release:
                for tag in release['tag-list']:
                    tag_id = tag['name']
                    tag_id = tag_id.replace("; ", "_").replace(";", "_").replace(" ", "_").replace('""', "_").replace('"', "_").replace(", ", "_").replace(",", "_")  # remove commas and spaces to avoid issues in csv
                    if not tag_id in mbid_to_string:
                        mbid_to_string[tag_id] = 'GENRE_TAG:' + tag_id.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv     
                    quads.append((release_id, "has_genre", tag_id, release_date))
                    # quads_strings.append((mbid_to_string[release_id], "has_genre", mbid_to_string[tag_id], release_date))

        if include_releasegenre:
            if release['primary-type'] == "Album":
                genre_relation = "releases_album_of_genre"
            elif release['primary-type'] == "EP":
                genre_relation = "releases_ep_of_genre"
            else:
                genre_relation = "releases_other_of_genre"
                if not genre_relation in relation_id_to_string:
                    if include_triangles:
                        relation_id_to_string[genre_relation] = genre_relation
            if 'tag-list' in release:
                for tag in release['tag-list']:
                    tag_id = tag['name']
                    tag_id = tag_id.replace("; ", "_").replace(";", "_").replace(" ", "_").replace('""', "_").replace('"', "_").replace(", ", "_").replace(",", "_")  # remove commas and spaces to avoid issues in csv
                    if len(tag_id) < 2:
                        continue
                    if not tag_id in mbid_to_string:
                        mbid_to_string[tag_id] = 'GENRE_TAG:' + tag_id.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv             
                    if include_triangles:
                        quads.append((artist_mbdid, genre_relation, tag_id, release_date))


    return quads, relation_id_to_string, mbid_to_string


def include_area_quads_method(quads, mbid_to_string, meta_info, artist_mbdid, artist_begin_date, start_to_end_list):

    # begin area i.e. founding place or birth place
    begin_area = meta_info['metainfo'].get('begin-area', {}).get('name', None)
    if begin_area is not None:
        begin_area = begin_area.replace("; ", "_").replace(";", "_").replace(" ", "_").replace(", ", "_").replace(",", "_")  # remove commas and spaces to avoid issues in csv
        if not begin_area in mbid_to_string:
            
            mbid_to_string[begin_area] = 'AREA:' + begin_area.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv

        artist_begin_date_string = artist_begin_date.strftime("%Y-%m-%dT00:00:00")
        quads.append((artist_mbdid, "has_begin_area", begin_area, artist_begin_date_string))

    # area
    if 'area' in meta_info['metainfo']:
        artist_area = meta_info['metainfo']['area']['name']
        artist_area = artist_area.replace("; ", "_").replace(";", "_").replace(" ", "_").replace(", ", "_").replace(",", "_")  # remove commas and spaces to avoid issues in csv
        if not artist_area in mbid_to_string:
            mbid_to_string[artist_area] = 'AREA:' + artist_area.replace(", ", "_").replace(" ", "_").replace(",", "_") # remove commas and spaces to avoid issues in csv
        for date in start_to_end_list:
            quads.append((artist_mbdid, "has_area", artist_area, date))

    return quads, mbid_to_string


def include_type_quads_method(quads, mbid_to_string, meta_info, artist_mbdid, start_to_end_list):

    # type i.e. group or person
    if 'type' in meta_info['metainfo']:
        artist_type = meta_info['metainfo']['type'].replace("; ", "_").replace(";", "_").replace(" ", "_").replace(", ", "_").replace(",", "_") 
        if not artist_type in mbid_to_string:
            mbid_to_string[artist_type] = 'TYPE:' + artist_type
        for date in start_to_end_list:
            quads.append((artist_mbdid, "has_type", artist_type, date))
    return quads, mbid_to_string