from pathlib import Path
import setlist_utils
import os
import string

# extract all festivals from:
# url = 'https://www.setlist.fm/festivals/browse/'+letter+'/page.html'
# write in a csv file with columns: festival_name, festival_url, festival_id

data_dir = Path(__file__).resolve().parent / "data"
data_dir.mkdir(exist_ok=True)
data_path = os.path.join(data_dir, "all_festivals.csv")

festival_dict = {}
letters = list(string.ascii_lowercase) + ['0-9']

for letter in letters:
    page = 1
    print(f"=== Processing letter: {letter.upper()} ===")
    while True:
        url = f'https://www.setlist.fm/festivals/browse/{letter}/{page}.html'
        print(f"Fetching URL: {url}")
        response = setlist_utils.fetch_with_retry(url, retries=2, delay=0.5)
        if response.status_code != 200:
            print(f"Failed to fetch page {page} for letter {letter}. Status code: {response.status_code}")
            break

        festival_dict = setlist_utils.parse_festival_page(response.content, festival_dict)
        page += 1

setlist_utils.write_festival_dict_to_csv(festival_dict, data_path)

print(f"Total festivals found: {len(festival_dict)}")