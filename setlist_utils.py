import requests
import math
import time
import csv
import os
import yaml
from bs4 import BeautifulSoup
from pathlib import Path
import re
from datetime import datetime,timedelta
import random
import json

config_path = Path(__file__).resolve().parent / "config.yaml"
if not config_path.exists():
    raise FileNotFoundError(f"config.yaml not found at {config_path}")

with config_path.open("r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}

API_KEY = cfg.get("API_KEY") or cfg.get("api_key")
if not API_KEY:
    raise KeyError("API_KEY not found in config.yaml (expected key 'API_KEY' or 'api_key')")



def extract_setlist_data(setlists):    
    # --- EXTRACT RELEVANT FIELDS ---
    # rows = []

    
    event_dict ={}
    artist_name = None
    mbid = None
    for item in setlists:
        artist_name = item["artist"]["name"]
        event_date = item.get("eventDate")
        event_id = item.get("id")
        last_updated = item.get("lastUpdated")
        venue_name = item.get("venue", {}).get("name", "N/A")        
        if venue_name == "N/A":
            continue  # skip entries without venue info
        venue_mbdid = item.get("venue", {}).get("id", "N/A")
        city = item.get("venue", {}).get("city", {}).get("name", "N/A")
        country = item.get("venue", {}).get("city", {}).get("country", {}).get("code", "N/A")
        latitude = item.get("venue", {}).get("city", {}).get("coords", {}).get("lat", "N/A")
        longitude = item.get("venue", {}).get("city", {}).get("coords", {}).get("long", "N/A")


        setlist_url = item["artist"]["url"]
        tour = item.get("tour", {}).get("name", "N/A")
        mbid = item["artist"]["mbid"]

        event_dict[event_id] = {
            "event_date": event_date,
            "last_updated": last_updated,
            "venue_name": venue_name,
            "venue_mbdid": venue_mbdid,
            "city": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "url": setlist_url,
            "artist_tour": tour
        }

        # rows.append({
        #     "artist_name": artist_name,
        #     "artist_mbdid": mbid,
        #     "event_id": event_id,
        #     "event_date": event_date,
        #     "last_updated": last_updated,
        #     "venue_name": venue_name,
        #     "venue_mbdid": venue_mbdid,
        #     "artist_tour": tour,
        #     "city": city,
        #     "country": country,
        #     "latitude": latitude,
        #     "longitude": longitude,
        #     "url": setlist_url
        # })
    # return rows, rows[0].keys() if rows else [], event_dict, artist_name, mbid
    return event_dict, artist_name, mbid

def extract_venue_data(setlists):    
    # --- EXTRACT RELEVANT FIELDS ---
    rows = []
    for item in setlists:
        venue_id = item["venue"]["id"]
        venue_name = item["venue"]["name"]
        city = item["venue"]["city"]["name"]
        country = item["venue"]["city"]["country"]["code"]
        latitude = item["venue"]["city"]["coords"]["lat"]
        longitude = item["venue"]["city"]["coords"]["long"]
        capacity = item["venue"].get("capacity", "N/A")
        event_date = item.get("eventDate")
        artist_mbid = item["artist"]["mbid"]
        artist_name = item["artist"]["name"]
        artist_tour = item['artist'].get("tour", {})
        rows.append({
            "venue_id": venue_id,
            "venue_name": venue_name,
            "city": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "capacity": capacity,
            "event_date": event_date,
            "artist_mbid": artist_mbid,
            "artist_name": artist_name,
            "artist_tour": artist_tour,
            "artist": artist_name,
        })
    return rows, rows[0].keys() if rows else []

def fetch_with_retry(url, headers_list=[], retries=5, delay=2, session=None):
    """Fetch with exponential backoff if 429 or other transient errors.
    headers are now in a list to rotate through in case of multiple API keys."""
    header_counter =0
    headers_list_copy= headers_list.copy()
    for headers in headers_list_copy: # have multiple headers to rotate through in case of rate limits
        # print(f"Current header: {header_counter}")
        for i in range(retries):
            if session:
                response = session.get(url)
            else:
                response = requests.get(url, headers=headers)
            if response.status_code == 200:
                time.sleep(random.uniform(0.5, 2))    # slight delay to respect rate limits
                returnnum = retries+1 
                return response, returnnum
            elif response.status_code == 429:
                wait_time = delay * (2 ** i)
                print(f"Rate limit hit on {i+1}st attempt. Waiting {wait_time}s...")                
                time.sleep(wait_time)
            elif response.status_code == 404:
                print(f"Page not found (404) for URL: {url}. Skipping.")
                return response, retries+1 # return 404 response immediately without retrying
            else:
                print(f"Error {response.status_code} on attempt {i+1}/{retries}")
                time.sleep(2)
        print(f"Current header: {header_counter/len(headers_list)}, rotating to next header for next attempt.")
        header_counter+=1
        headers_list.append(headers_list.pop(0)) # reorder s.t. the first used header goes to the end of the list for next round
        # raise Exception(f"Failed after {retries} attempts ({response.status_code})")
    returnnum = retries+1
    if response.status_code == 429:
        now = datetime.now()
        
        # Set next day at 00:00:00
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        wait_seconds = (next_midnight - now).total_seconds()

        if wait_seconds > 0:
            print(f"Waiting for {wait_seconds/3600:.2f} hours until {next_midnight} to reset API limit.")
            time.sleep(wait_seconds)
        # next_day = now + timedelta(days=1)
        # wait_seconds = (next_day - now).total_seconds()
        # if wait_seconds > 0:
        #     print(f"Waiting for {wait_seconds/3600:.2f} hours until {next_day} to reset API limit.")
        #     time.sleep(wait_seconds + 10)  # wait a bit more to be safe 
    return response, returnnum # return last response and number of requests made


def fetch_with_retry_festival(url, headers=None, retries=5, delay=1, session=None):
    """Fetch with exponential backoff if 429 or other transient errors."""
    for i in range(retries):
        if session:
            response = session.get(url)
        else:
            response = requests.get(url, headers=headers)
        if response.status_code == 200:
            time.sleep(random.uniform(0.4, 0.6))    # slight delay to respect rate limits
            returnnum = retries+1 
            return response, returnnum
        elif response.status_code == 429:
            wait_time = delay * (2 ** i)  + random.uniform(0, 0.5)
            print(f"Rate limit hit on {i+1}st attempt. Waiting {wait_time}s...")
            time.sleep(wait_time)
        elif response.status_code == 404:
            print(f"Page not found (404) for URL: {url}. Skipping.")
            return response, retries+1 # return 404 response immediately without retrying
        else:
            print(f"Error {response.status_code} on attempt {i+1}/{retries}")
            time.sleep(2)
    # raise Exception(f"Failed after {retries} attempts ({response.status_code})")
    returnnum = retries+1
    if response.status_code == 429:
        now = datetime.now()
        next_day = now + timedelta(days=1)
        wait_seconds = (next_day - now).total_seconds()
        if wait_seconds > 0:
            print(f"Waiting for {wait_seconds/3600:.2f} hours until {next_day} to reset API limit.")
            time.sleep(wait_seconds + 10)  # wait a bit more to be safe 
    return response, returnnum # return last response and number of requests made

def parse_festival_page(html_content, festival_dict={}):
    """Parse festival page HTML and extract festival links and names. and put it to festival_dict"""
    soup = BeautifulSoup(html_content, 'html.parser')
    for a in soup.find_all("a", href=True, title=True):
        href = a["href"].replace("../../../", "")  # normalize
        title = a["title"]
        # Extract text between "View " and " details"
        if title.startswith("View ") and " details" in title:
            name = title.split("View ", 1)[1].split(" details", 1)[0].strip()
            festival_dict[href] = name
    return festival_dict

def make_dates(year, start_date_str, end_date_str):
    """Helper function to create ISO-format date strings for start and end dates."""
    date_formats = ["%Y %a, %b %d", "%Y %b %d", "%Y %A, %B %d"]  # allow flexible formats
    def parse_date(y, dstr):
        for fmt in date_formats:
            try:
                return datetime.strptime(f"{y} {dstr}", fmt).date().isoformat()
            except ValueError:
                pass
        
        # try next year automatically
        y2 = int(y) + 1
        for fmt in date_formats:
            try:
                return datetime.strptime(f"{y2} {dstr}", fmt).date().isoformat()
            except ValueError:
                pass

        raise ValueError(f"Could not parse date: {y} {dstr} or {y2} {dstr}")
    start_date = parse_date(year, start_date_str)
    end_date = parse_date(year, end_date_str)

    # Handle year rollover (e.g., festival runs Dec -> Jan)
    if end_date < start_date:
        end_date = parse_date(int(year) + 1, end_date_str)

    return start_date, end_date

def parse_festival_editions_page(html_content, festival_dict):
    """Parse festival page for a given festival, e.g. southside HTML and extract festival yearly editions links and names. and put it to festival_dict"""

    soup = BeautifulSoup(html_content, 'html.parser')
    for row in soup.find_all("tr"):
        year_t = row.find("td", class_="year")
        if year_t is None:
            continue
        year = year_t.get_text(strip=True)
        start_date = row.find("td", class_="start").get_text(strip=True)
        end_date = row.find("td", class_="end").get_text(strip=True)
        start_date_date, end_date_date = make_dates(year, start_date, end_date)

        link = row.find("a", class_="twoLineLink")
        href = link["href"].replace("../", "")
        name = link.find("strong").get_text(strip=True)
        # Extract ID (last part after final '-')
        match = re.search(r'-([a-z0-9]+)\.html$', href)
        fest_id = match.group(1) if match else None
        festival_dict[fest_id] = (year, href, name, start_date_date, end_date_date)

    return festival_dict

def get_musicbrainz_id_from_url(url, session):
    """Extract MusicBrainz ID from a given setlist URL, e.g. https://www.setlist.fm/setlist/ghost-light/2022/blain-picnic-grounds-blain-pa-6bb24606.html."""

    mbid = None
    resp, returnnum = fetch_with_retry_festival(url, retries=5, delay=4, session=session) # we can use the same fetch_with_retry_festival function here since the setlist.fm pages have the same rate limits as the API, and we want to be robust to that when fetching many artist pages in a row.
    if resp.status_code != 200:
        print(f"Failed to fetch page {url}. Status code: {resp.status_code}")
        return None
    soup = BeautifulSoup(resp.content, 'html.parser')
    # find the <script> tag that contains 'sfmPageAttributes'
    script = soup.find("script", id="page-attrs")

    # extract the MBID using regex
    match = re.search(r'"mbid":"([0-9a-fA-F-]+)"', script.text)
    if match:
        mbid = match.group(1)

    return mbid

def extract_venue_info(soup):

    # Find the venue <ol> section that contains the <a> tag
    venue_tag = soup.select_one("ol.listUnstyled li a[href*='/venue/']")
    if not venue_tag:
        return {"venue_url": None, "venue_name": None, "venue_id": None}  # no venue found

    # Extract venue info
    venue_url = venue_tag["href"].replace("../../", "") 
    venue_name = venue_tag.get_text(strip=True)

    # Extract ID from URL (it's the last hyphen-separated chunk before '.html')
    match = re.search(r'-([0-9a-z]{8})\.html$', venue_url)
    venue_id = match.group(1) if match else None

    return {
        "venue_url": venue_url,
        "venue_name": venue_name,
        "venue_id": venue_id
    }


def parse_festival_oneyear_page(html_content, festival_info={}, country_list=None, session=None):
    soup = BeautifulSoup(html_content, 'html.parser')
    festival_year_data = {}
    venue_dict = extract_venue_info(soup)
    is_in_country_flag = True
    if country_list != None:
        if len(country_list) > 0:
            venue_name = venue_dict.get("venue_name", "")
            if venue_name.split(",")[-1].strip() not in country_list: # we only extract the info for festivals in the specified country list, 
                #so if the venue is not in the country list, we skip this edition entirely (no artists extracted)
                is_in_country_flag=False

                return {}, venue_dict, is_in_country_flag
            


    for date_header in soup.find_all("h3", class_="FestivalSetlistsGroupedVenueDay-eventDate"):
        date_text = date_header.get_text(strip=True)
        dt = datetime.strptime(date_text, "%A, %B %d, %Y").isoformat()
        
        # The artist list container is right after the header
        list_div = date_header.find_next("div", class_="FestivalSetlistsGroupedVenueDay-list")
        # artists = []
        if list_div:
            # Each artist row is a "FestivalSetlistListItem-root"
            for item in list_div.find_all("div", class_="FestivalSetlistListItem-root"):
                artist_link = item.find("div", class_="FestivalSetlistListItem-artist").find("a")
                if artist_link:
                    name = artist_link.get_text(strip=True)
                    url = artist_link["href"]
                    artist_musicbrainz_id = get_musicbrainz_id_from_url(url, session)

                    festival_year_data[artist_musicbrainz_id] = {"artist": name, "url": url, "date": dt}

    if not festival_year_data:
        # Wacken uses <h2> for dates
        for date_header in soup.find_all("h2"):
            date_text = date_header.get_text(strip=True)

            try:
                dt = datetime.strptime(date_text, "%A, %B %d, %Y").isoformat()
            except ValueError:
                continue

            # Find the section that belongs to this date
            section = date_header.find_next("div", class_="FestivalSetlistSection-content")
            if not section:
                continue

            # Find all artist rows in that section
            for item in section.find_all("div", class_="FestivalSetlistListItem-root"):
                artist_div = item.find("div", class_="FestivalSetlistListItem-artist")
                if not artist_div:
                    continue

                artist_link = artist_div.find("a")
                if not artist_link:
                    continue

                name = artist_link.get_text(strip=True)
                url = artist_link["href"]

                artist_musicbrainz_id = get_musicbrainz_id_from_url(url, session)

                festival_year_data[artist_musicbrainz_id] = {
                    "artist": name,
                    "url": url,
                    "date": dt
                }

    if not festival_year_data:
        # New layout (like your example page)
        for date_p in soup.find_all("p", class_="FestivalSetlistsGroupedVenueDayBySubVenue-eventDate"):
            date_text = date_p.get_text(strip=True)

            try:
                dt = datetime.strptime(date_text, "%A, %B %d, %Y").isoformat()
            except ValueError:
                continue

            # The list is the next sibling div
            list_div = date_p.find_next("div", class_="FestivalSetlistList-items")
            if not list_div:
                continue

            for item in list_div.find_all("div", class_="FestivalSetlistListItem-root"):
                artist_div = item.find("div", class_="FestivalSetlistListItem-artist")
                if not artist_div:
                    continue

                artist_link = artist_div.find("a")
                if not artist_link:
                    continue

                name = artist_link.get_text(strip=True)
                url = artist_link["href"]

                artist_musicbrainz_id = get_musicbrainz_id_from_url(url, session)

                festival_year_data[artist_musicbrainz_id] = {
                    "artist": name,
                    "url": url,
                    "date": dt
                }


    return festival_year_data, venue_dict, is_in_country_flag

def write_festival_dict_to_csv(festival_dict, output_filename):
    """" writing the festival dict to a csv file with columns title, href, id"""
    print(f"Writing festival data to {output_filename}")
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['title', 'href', 'id'])
        for href, title in festival_dict.items():
            id_ = ''
            if '.html' in href and '-' in href:
                start = href.rfind('-') + 1
                end = href.rfind('.html')
                if start < end:
                    id_ = href[start:end]
            writer.writerow([title, href, id_])

def read_festival_csv_to_dict(input_filename):
    """ reading the festival csv file and returning a dict with key: festival_id, value: (festival_name, festival_url)"""
    festival_dict = {}
    with open(input_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            festival_id = row['id']
            festival_name = row['title']
            festival_url = row['href']
            festival_dict[festival_id] = (festival_name, festival_url)
    return festival_dict

def write_festival_info_dict_to_csv(all_festival_info_dict, data_path_festivals_out):

    
    pass
def get_setlists_for_artist(artist_mbid, HEADERS, api_request_counters=0):
    """Fetches *all* setlists for an artist, across all pages."""
    all_setlists = []
    page = 1

    # initial request to get total count
    url = f"https://api.setlist.fm/rest/1.0/artist/{artist_mbid}/setlists?p={page}"
    response, num_req = fetch_with_retry(url, HEADERS)
    api_request_counters += num_req
    # response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"skipping page {page} (error {response.status_code})")
        return all_setlists, api_request_counters
    
    data = response.json()
    total = data.get("total", 0)
    items_per_page = data.get("itemsPerPage", 20)
    total_pages = math.ceil(total / items_per_page)
    # print(f"Found {total} setlists across {total_pages} pages.")

    # collect first page
    all_setlists.extend(data.get("setlist", []))

    # collect remaining pages
    for page in range(2, total_pages + 1):
        url = f"https://api.setlist.fm/rest/1.0/artist/{artist_mbid}/setlists?p={page}"
        response, num_req = fetch_with_retry(url, HEADERS)
        api_request_counters += num_req
        if response.status_code != 200:
            print(f"skipping page {page} (error {response.status_code})")
            continue
        data = response.json()
        all_setlists.extend(data.get("setlist", []))
        # print(f"Page {page}/{total_pages} fetched ({len(all_setlists)} total so far)")


    return all_setlists, api_request_counters



def get_setlists_for_venue(venue_id, HEADERS, api_request_counters=0):
    """Fetch *all* setlists for a venue, across all pages."""
    all_setlists = []
    page = 1

    # first page: get total
    url = f"https://api.setlist.fm/rest/1.0/venue/{venue_id}/setlists?p={page}"
    response, num_req = fetch_with_retry(url, HEADERS)
    api_request_counters += num_req
    data = response.json()

    total = data.get("total", 0)
    items_per_page = data.get("itemsPerPage", 20)
    total_pages = math.ceil(total / items_per_page)
    print(f"Venue {venue_id} → {total} events across {total_pages} pages.")

    all_setlists.extend(data.get("setlist", []))

    # remaining pages
    for page in range(2, total_pages + 1):
        time.sleep(1.2)  # stay within rate limit
        url = f"https://api.setlist.fm/rest/1.0/venue/{venue_id}/setlists?p={page}"
        response, num_req = fetch_with_retry(url, HEADERS)
        api_request_counters += num_req
        data = response.json()
        all_setlists.extend(data.get("setlist", []))
        print(f"Page {page}/{total_pages} fetched ({len(all_setlists)} total so far)")

    return all_setlists, api_request_counters



def save_events_to_csv(events, fieldnames, filename="example.csv"):
    """Save event data to CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)
    print(f"Saved {len(events)} events to {filename}")



def safe_load_json(path):
    """Load JSON safely. Return {} if error."""
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def safe_write_json(path, data):
    """Atomic JSON write to prevent corruption."""
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)  # atomic rename
