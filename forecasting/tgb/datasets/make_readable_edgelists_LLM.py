import csv
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(sys.path[0], '..')))
sys.path.insert(0, os.path.abspath(os.path.join(sys.path[0], '..')))
from counttrucola.rule_based.rule_dataset import RuleDataset 


dataset = 'concertperformanceonly'
dataset_name = 'tkgl_'+dataset
dataset_name2 = 'tkgl-'+dataset

if 'gdelt' in dataset:
    ts_size = 15
elif 'icews14' in dataset or 'icews18' in dataset: 
    ts_size = 24
else:
    ts_size = 1


if 'smallpedia' or 'wikidata' or 'concert' in dataset:
    rel_mapping_index = 1
    node_mapping_index = 0
else:
    rel_mapping_index = 0
    node_mapping_index = 0

print("Current sys.path:", sys.path)
this_file_path = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
print("Current file path:", this_file_path)
# File paths
edgelist_path = os.path.join(this_file_path, dataset_name, dataset_name2+'_edgelist.csv')
rel_mapping_path = os.path.join(this_file_path,dataset_name, 'rel_mapping.csv')
node_mapping_path = os.path.join(this_file_path,dataset_name, 'node_mapping.csv')
timestamp_mapping_path = os.path.join(this_file_path,dataset_name, 'timestamp2int.txt')
# festival_country_venue_path = os.path.join(this_file_path, dataset_name, 'festival_country_venue.txt')

## only set this, if you only want to extract festivals and artsits that were active in at least these years for the preliminary llm experiments
## otherwise leave empty to include all festivals and artists
min_timestamps = [] # [2023, 2024, 2025] # the festival needs to have been in at least these years to be included in the dataset for the prel. llm experiments

type_of_output = 'tgbid' # 'string' #'tgbid'  # or 'string' Type of output to generate

include_inverse_flags = False  # Set to True if you want to include inverse relations
split_train_val_test_flag =  True

musicbrainz_flag = False # True # if true: llog the musicbrainz ids of the selected artists and festivals, if false: log the names of the selected artists and festivals
    

if type_of_output == 'tgbid':
    node_index = 1 + node_mapping_index
    rel_index = 0 + rel_mapping_index
    output_string_name = 'tgbid_edgelist.txt'
    output_string_name_mbid = 'mbid_' + output_string_name
    if split_train_val_test_flag:
        output_string_name_train = 'tgbid_edgelist_train.txt'
        output_string_name_val = 'tgbid_edgelist_val.txt'
        output_string_name_test = 'tgbid_edgelist_test.txt'
        
    if split_train_val_test_flag:
        output_string_name_train_mbid = 'mbid_' + output_string_name_train
        output_string_name_val_mbid = 'mbid_' + output_string_name_val
        output_string_name_test_mbid = 'mbid_' + output_string_name_test
elif type_of_output == 'string':
    node_index = 2 + node_mapping_index
    rel_index = 1  + rel_mapping_index
    output_string_name = 'string_edgelist.txt'
    output_string_name_mbid = 'mbid_' + output_string_name
    if split_train_val_test_flag:
        output_string_name_train = 'string_edgelist_train.txt'
        output_string_name_val = 'string_edgelist_val.txt'
        output_string_name_test = 'string_edgelist_test.txt'
        
    if split_train_val_test_flag:
        output_string_name_train_mbid = 'mbid_' + output_string_name_train
        output_string_name_val_mbid = 'mbid_' + output_string_name_val
        output_string_name_test_mbid = 'mbid_' + output_string_name_test
if include_inverse_flags:
    # ruledataset = RuleDataset(name=dataset_name2, threshold=1, large_data_hardcode_flag=False)
    output_string_name = 'incl_inverse_' + output_string_name
    output_string_name_mbid = 'incl_inverse' + output_string_name_mbid
    if split_train_val_test_flag:
        output_string_name_train = 'incl_inverse_' + output_string_name_train
        output_string_name_val = 'incl_inverse_' + output_string_name_val
        output_string_name_test = 'incl_inverse_' + output_string_name_test
    
        output_string_name_train_mbid = 'incl_inverse_' + output_string_name_train_mbid
        output_string_name_val_mbid = 'incl_inverse_' + output_string_name_val_mbid
        output_string_name_test_mbid = 'incl_inverse_' + output_string_name_test_mbid

output_dir = os.path.join(sys.path[0],dataset_name,'llm')
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, output_string_name)


artist_output_path = os.path.join(output_dir, 'artist_test.txt')
festival_output_path = os.path.join(output_dir, 'festival_test.txt')

output_path_mbid = os.path.join(output_dir, output_string_name_mbid)

if split_train_val_test_flag:
    output_path_train = os.path.join(output_dir, output_string_name_train)
    output_path_val = os.path.join(output_dir, output_string_name_val)
    output_path_test = os.path.join(output_dir, output_string_name_test)
    if not os.path.exists(output_path_train):
        open(output_path_train, 'w').close()
    if not os.path.exists(output_path_val):
        open(output_path_val, 'w').close()
    if not os.path.exists(output_path_test):
        open(output_path_test, 'w').close()
    output_path_mbid_train = os.path.join(output_dir, output_string_name_train_mbid)
    output_path_mbid_val = os.path.join(output_dir, output_string_name_val_mbid)
    output_path_mbid_test = os.path.join(output_dir, output_string_name_test_mbid)
    if not os.path.exists(output_path_mbid_train):
        open(output_path_mbid_train, 'w').close()
    if not os.path.exists(output_path_mbid_val):
        open(output_path_mbid_val, 'w').close()
    if not os.path.exists(output_path_mbid_test):
        open(output_path_mbid_test, 'w').close()




if not os.path.exists(rel_mapping_path) or include_inverse_flags==True or split_train_val_test_flag==True:

    ruledataset = RuleDataset(name=dataset_name2, large_data_hardcode_flag=False)
    # output_string_name = 'incl_inverse_' + output_striny_name

    ruledataset.nodes_string_to_id = {}
    for node_id, node_str in ruledataset.nodes_id_to_string.items():
        ruledataset.nodes_string_to_id[str(node_str[1])] = node_id

if split_train_val_test_flag:
    max_train_ts = ruledataset.train_data[:,3].max()
    max_val_ts = ruledataset.val_data[:,3].max()
    max_test_ts = ruledataset.test_data[:,3].max()
    print(f"Max train ts: {max_train_ts}, Max val ts: {max_val_ts}, Max test ts: {max_test_ts}")

    timestamp_orig2id = {ruledataset.timestamp_id2orig[i]: i for i in ruledataset.timestamp_id2orig.keys()}
    timestamp_id2orig = {}


if os.path.exists(timestamp_mapping_path):
    with open(timestamp_mapping_path, 'r', encoding='utf-8') as file:
        timestamp_orig2id = {}
        for line in file:
            line = line.strip()
            if line:
                tgb_id, timestamp_year = line.split('\t')
                timestamp_id2orig[int(tgb_id)] = int(timestamp_year)
                timestamp_orig2id[int(timestamp_year)] = int(tgb_id)
min_timestamps_int = [timestamp_orig2id[t] for t in min_timestamps]

max_line = 1e100 #90730 #2278405 # 610153
min_line = 0

# Load mappings
with open(rel_mapping_path, 'r', encoding='utf-8') as f:
    rel_mapping = {row[0]: row[rel_index] for i, row in enumerate(csv.reader(f, delimiter=';')) if i > 0}

with open(node_mapping_path, 'r', encoding='utf-8') as f:
    node_mapping = {row[node_mapping_index]: row[node_index]  for i, row in enumerate(csv.reader(f, delimiter=';')) if i > 0}


artist_set = set()
festival_set = set()
# Process edgelist and write output
with open(edgelist_path, 'r', encoding="utf-8") as edgelist_file, \
    open(output_path, 'w', encoding="utf-8") as output_file_all, \
    open(output_path_train, 'w', encoding="utf-8") as output_file_train, \
    open(output_path_val, 'w', encoding="utf-8") as output_file_val, \
    open(output_path_test, 'w', encoding="utf-8") as output_file_test , \
    open(output_path_mbid, 'w', encoding="utf-8") as output_file_mbid_all, \
    open(output_path_mbid_train, 'w', encoding="utf-8") as output_file_mbid_train, \
    open(output_path_mbid_val, 'w', encoding="utf-8") as output_file_mbid_val, \
    open(output_path_mbid_test, 'w', encoding="utf-8") as output_file_mbid_test: 
    # write to output_file_train, output_file_val, and output_file_test in parallel
    
    reader = csv.reader(edgelist_file)
    for i, row in enumerate(reader):
        first_open = True
        if i >= max_line:
            break
        if i > min_line:
            # timestep, head, tail, rel = map(int, row) # ts,head,tail,relation_type        
            timestep, head, tail, rel = row

            # if rel not in ['performs_at_festival', 'inv_performs_at_festival', 6]:
            #     continue
            head_id = ruledataset.nodes_string_to_id.get(head, None)
            tail_id = ruledataset.nodes_string_to_id.get(tail, None)
            timesteps_for_head = set(ruledataset.all_head_t[head_id])
            timesteps_for_tail = set(ruledataset.all_head_t[tail_id])

            ## the festival and the artist need to have been active in at least the min_timestamps for the edge to be included in the dataset for the preliminary llm experiments
            add_edge = True
            if len(min_timestamps_int) > 0:
                for tmin in min_timestamps_int:                
                    if not tmin in timesteps_for_head:
                        add_edge = False
                    if not tmin in timesteps_for_tail:
                        add_edge = False


            timestep = int(timestep)
            timestep_mapped = timestamp_id2orig[int(timestep)] if split_train_val_test_flag else timestep
            # if timestep_mapped < 2025:
            #     continue    
            # if timestep_mapped > 2025:
            #     continue
            if split_train_val_test_flag:
                if timestep <= max_train_ts:
                    output_file = output_file_train
                    output_file_mbid = output_file_mbid_train
                elif timestep <= max_val_ts:
                    output_file = output_file_val
                    output_file_mbid = output_file_mbid_val
                else:
                    output_file = output_file_test
                    output_file_mbid = output_file_mbid_test

            rel_str = rel_mapping.get(rel, f'unknown_{rel}')
            head_str = head                     
            tail_str = tail
            # if musicbrainz_flag == False: # log the proper name
            head_str = node_mapping.get(head, f'unknown_{head}')
            tail_str = node_mapping.get(tail, f'unknown_{tail}')

            if timestep_mapped == 2025:
                if add_edge:
                    if rel in ['performs_at_festival', 6]:
                        if head not in artist_set:
                            artist_set.add(head+";"+node_mapping.get(head, f'unknown_{head}'))
                        if tail not in festival_set:
                            festival_set.add(tail+";"+node_mapping.get(tail, f'unknown_{tail}'))
            # if split_train_val_test_flag:
            #     timestep = timestep_mapped
            # else:
            #     timestep = timestep // ts_size  # Adjust timestep based on ts_size
            output_file.write(f"{head_str}\t{rel_str}\t{tail_str}\t{timestep}\n")
            output_file_all.write(f"{head_str}\t{rel_str}\t{tail_str}\t{timestep}\n")
            output_file_mbid.write(f"{head}\t{rel}\t{tail}\t{timestep}\n")
            output_file_mbid_all.write(f"{head}\t{rel}\t{tail}\t{timestep}\n")


            if include_inverse_flags:
                if type_of_output == 'tgbid':
                    inverse_rel = ruledataset.get_inv_rel_id(rel)
                    
                elif type_of_output == 'string':
                    inverse_rel = 'inv_' + rel_str
                output_file.write(f"{tail_str}\t{inverse_rel}\t{head_str}\t{timestep}\n")

print(f"Processed {i - min_line} lines from the edgelist and saved to {output_path}")
print(f"Unique artists: {len(artist_set)}, Unique festivals: {len(festival_set)}")


# if not os.path.exists(artist_output_path):
#     os.makedirs(os.path.dirname(artist_output_path), exist_ok=True)

if musicbrainz_flag == False:
    with open(artist_output_path, 'w', encoding='utf-8') as f:
        for artist in sorted(artist_set):
            f.write(f"{artist}\n")
    with open(festival_output_path, 'w', encoding='utf-8') as f:
        for festival in sorted(festival_set):
            f.write(f"{festival}\n")


print('Finished writing artist and festival files.')