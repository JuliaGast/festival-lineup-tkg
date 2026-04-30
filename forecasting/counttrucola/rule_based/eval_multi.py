    
import numpy as np
import time
import rule_utils

import sys
import os.path as osp
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__)))) 

from forecasting.tgb.linkproppred.evaluate import Evaluator
from rule_dataset import RuleDataset
import eval_r_prec_subset

import psutil
import json
import os


process = psutil.Process()


rankings = ["tkgl-concert220-rankings_test_conf_0_corr_conf_0_noisyor_crules_frules_zrules_pvalue_10_num_top_rules_5_multi.txt", 
            "tkgl-concert420-rankings_test_conf_0_corr_conf_0_noisyor_crules_frules_zrules_pvalue_10_num_top_rules_5_multi.txt",
            "tkgl-concert520-rankings_test_conf_0_corr_conf_0_noisyor_crules_frules_zrules_pvalue_10_num_top_rules_5_multi.txt"]

year_dict = {'tkgl-concert2': '2025', 'tkgl-concert4': '2024', 'tkgl-concert5': '2023'}
log_info = []


for rankings_name in rankings:
    dataset_name = rankings_name.split("-rankings")[0]
    dataset_name = dataset_name.split("20")[0]
    dataset_name_folder = dataset_name.replace("-", "_")
    ruledataset = RuleDataset(name=dataset_name, large_data_hardcode_flag=False)
    year = year_dict[dataset_name]

    print('rankings_name:', rankings_name)
    print('year:', year)

    rels_possible = ['performs_at_festival', 'inv_performs_at_festival']
    for rel in rels_possible:
        rel_list = [rel]

        if rel_list[0] == 'performs_at_festival':
            nodes_of_interest_file = "202320242025_artist_test_subset.txt"
        else:
            nodes_of_interest_file = "202320242025_festival_location_test_subset.txt"

    
        ## get the test queries for the specified nodes, relations, and timestamp
        nodes_of_interest_path = osp.join(osp.dirname(__file__), "..", "tgb", "datasets", dataset_name_folder, nodes_of_interest_file)
        nodes_of_interest = rule_utils.read_nodes_of_interest(nodes_of_interest_path)
        rel_of_interest_list = [ruledataset.rels_string_to_id[rel] for rel in rel_list]
        timestamp_of_interest = ruledataset.timestamp_setlist_to_id[year]
        eval_rel_head_t_tail = ruledataset.get_all_queries_for_nodes_rels_timestamps_of_interest(nodes_of_interest, rel_of_interest_list, timestamp_of_interest)

        path_rankings = osp.join(osp.dirname(__file__), "..", "files","rankings", dataset_name, rankings_name)

        ## run the evaluation
        scores = eval_r_prec_subset.evaluate_r_prec(ruledataset, path_rankings, evaluation_mode='test', eval_type='random',eval_rel_head_t_tail=eval_rel_head_t_tail, detailed_results_flag=True)
        mean_r_prec, mean_weighted_r_prec, mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, r_prec_per_rel, weighted_r_prec_per_rel, r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict = scores
        log_info.append([rankings_name+'_'+rel_list[0], mean_r_prec, mean_weighted_r_prec, mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, year])
        ## store all sorts of things
        # Create directory if it doesn't exist
        output_dir = osp.join(osp.dirname(__file__), "..", "files",  "results", "r_prec",  dataset_name, rel_list[0])
        if not osp.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        # Save r_prec_tracker_string to JSON
        output_path = os.path.join(output_dir, "r_prec_tracker_string.json")
        with open(output_path, 'w') as f:
            json.dump(r_prec_tracker_string, f, indent=2)

        output_path = os.path.join(output_dir, "r_prec_tracker.json")
        with open(output_path, 'w') as f:
            json.dump(r_prec_tracker, f, indent=2)

        output_path = os.path.join(output_dir, "r_prec_tracker_string_good_queries.json")
        with open(output_path, 'w') as f:
            json.dump(r_prec_good_queries, f, indent=2)

        output_path = os.path.join(output_dir, "r_prec_tracker_string_bad_queries.json")
        with open(output_path, 'w') as f:
            json.dump(r_prec_bad_queries, f, indent=2)

        output_path = os.path.join(output_dir, "good_queries.txt")
        with open(output_path, 'w') as f:
            for query in good_queries:
                for k in query:
                    f.write(f"{k} ")
                f.write(f"\n")
        output_path = os.path.join(output_dir, "bad_queries.txt")
        with open(output_path, 'w') as f:
            for query in bad_queries:
                for k in query:
                    f.write(f"{k} ")
                f.write(f"\n")

        output_path = os.path.join(output_dir, "nodes_of_interest_dict.json")
        with open(output_path, 'w') as f:
            json.dump(nodes_of_interest_dict, f, indent=2)

# Print log info
print("\nEvaluation Summary:")
print("Year\tRankings Name\tMean R-Prec\tMean Weighted R-Prec\tMean Normalized Ten-Prec\tMean Weighted Normalized Ten-Prec\tMean Ten-Prec")
for info in log_info:
    print(f"{info[6]}\t{info[0]}\t{info[1]:.4f}\t{info[2]:.4f}\t{info[3]:.4f}\t{info[4]:.4f}\t{info[5]:.4f}")

# Write summary to file
summary_path = os.path.join(osp.dirname(__file__), "..", "files",  "results", "r_prec", "summary.txt")
with open(summary_path, 'w') as f:
    f.write("Evaluation Summary:\n")
    f.write("Year\tRankings Name\tMean R-Prec\tMean Weighted R-Prec\tMean Normalized Ten-Prec\tMean Weighted Normalized Ten-Prec\tMean Ten-Prec\n")
    for info in log_info:
        f.write(f"{info[6]}\t{info[0]}\t{info[1]:.4f}\t{info[2]:.4f}\t{info[3]:.4f}\t{info[4]:.4f}\t{info[5]:.4f}\n")