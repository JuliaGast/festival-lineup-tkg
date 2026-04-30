    
import sys
import os.path as osp
sys.path.append(osp.dirname(osp.dirname(osp.dirname(osp.abspath(__file__)))) )


from counttrucola.rule_based.rule_dataset import RuleDataset
import eval_r_prec
import eval

import psutil
import json
import os


process = psutil.Process()
dataset_name = "tkgl-concertperformanceonly"
dataset_name_folder = dataset_name.replace("-", "_")

# evaluate for all rankings in the specified folder, which is "files/rankings/dataset_name"
rankings = os.listdir(osp.join(osp.dirname(__file__), "..", "files", "rankings", dataset_name))


# rankings = ["ranking-a-10-Meta-Llama-70Bt2023.txt", "ranking-a-10-Meta-Llama-70Bt2024.txt", "ranking-a-10-Meta-Llama-70Bt2025.txt", 
#             "ranking-a-all-Meta-Llama-70Bt2023.txt", "ranking-a-all-Meta-Llama-70Bt2024.txt", "ranking-a-all-Meta-Llama-70Bt2025.txt", 
#             "ranking-f-10-Meta-Llama-70Bt2023.txt", "ranking-f-10-Meta-Llama-70Bt2024.txt", "ranking-f-10-Meta-Llama-70Bt2025.txt", 
#             "ranking-f-all-Meta-Llama-70Bt2023.txt", "ranking-f-all-Meta-Llama-70Bt2024.txt", "ranking-f-all-Meta-Llama-70Bt2025.txt"]

log_info = []
log_info2 = []
ruledataset = RuleDataset(name=dataset_name, large_data_hardcode_flag=False)

for rankings_name in rankings:
    # if 'pre-experiment' in rankings_name:
    #     continue
    # if 'old' in rankings_name:
    #     continue
    # if not 'both' in rankings_name:
    #     continue
    # if 'GPT' in rankings_name:
    #     continue
    year = rankings_name.lower().split("-")[-1].split("bt")[-1].split(".")[0]

    print('rankings_name:', rankings_name)
    print('year:', year)

    if 'ranking-a-' in rankings_name:
        rel_list = ['inv_performs_at_festival']
    elif 'ranking-f-' in rankings_name:
        rel_list = ['performs_at_festival']
    elif 'ranking-both' in rankings_name:
        rel_list = ['inv_performs_at_festival', 'performs_at_festival']
    # year = '2025'

    ## option1: for the subset experiments:
    # get the test queries for the specified nodes, relations, and timestamp
    # if rel_list[0] == 'performs_at_festival':
    #     nodes_of_interest_file = "202320242025_artist_test_subset.txt"
    # else:
    #     nodes_of_interest_file = "202320242025_festival_location_test_subset.txt"
    # nodes_of_interest_path = osp.join(osp.dirname(__file__), "..", "tgb", "datasets", dataset_name_folder, nodes_of_interest_file)
    # nodes_of_interest = utils.read_nodes_of_interest(nodes_of_interest_path)
    # rel_of_interest_list = [ruledataset.rels_string_to_id[rel] for rel in rel_list]
    # timestamp_of_interest = ruledataset.timestamp_setlist_to_id[year]
    # eval_rel_head_t_tail = ruledataset.get_all_queries_for_nodes_rels_timestamps_of_interest(nodes_of_interest, rel_of_interest_list, timestamp_of_interest)
    # path_rankings = osp.join(osp.dirname(__file__), "..", "files","rankings", dataset_name, "pre-experiment", rankings_name)

    ## option2: for the full evaluation:
    rels_of_interest= []
    for rel in rel_list:
        rels_of_interest.append(ruledataset.rels_string_to_id[rel])
    test_queries_of_interest = {}
    if rels_of_interest is not None:
        for rel in rels_of_interest:
            if rel in ruledataset.rel_head_t_tail['test']:
                test_queries_of_interest[rel]= ruledataset.rel_head_t_tail['test'][rel]
    else:
        test_queries_of_interest = ruledataset.rel_head_t_tail['test']
    eval_rel_head_t_tail = test_queries_of_interest
    path_rankings = osp.join(osp.dirname(__file__), "..", "files","rankings", dataset_name, rankings_name)

    

    ## run the evaluation
    # R_PREC
    scores = eval_r_prec.evaluate_r_prec(ruledataset, path_rankings, evaluation_mode='test', eval_type='random',eval_rel_head_t_tail=eval_rel_head_t_tail, detailed_results_flag=True)
    mean_r_prec, mean_weighted_r_prec, mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, r_prec_per_rel, weighted_r_prec_per_rel, r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict = scores
    log_info.append([rankings_name, mean_r_prec, mean_weighted_r_prec, mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, year])
    
    ## store all sorts of things
    # Create directory if it doesn't exist
    output_dir = osp.join(osp.dirname(__file__), "..", "files",  "results", "r_prec", rankings_name + "_" + dataset_name)
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

    ## MRR
    scores_mrr_and_co = eval.evaluate(ruledataset, path_rankings,progressbar_percentage=0.01, evaluation_mode='test', eval_type='random', rels_of_interest=rels_of_interest)
    valmrr, valhits10, valhits1, valhits3, valhits100, valmrrperrel,valhits1perrel, valmrrperts, valhits1perts = scores_mrr_and_co
    log_info2.append([year, rankings_name, valmrr, valhits1, valhits3, valhits10, valhits100, mean_r_prec, mean_weighted_r_prec,mean_ten_prec, mean_normalized_ten_prec])
    print(scores_mrr_and_co)

    # append & write to a file which is in the same folder as this script, named "results_summary.txt the following"
    # path_rankings,dataset_name, rels_of_interest, scores
    with open(osp.join(osp.dirname(__file__),"results_summary.txt"), "a") as f:
        f.write(f"{path_rankings},\n {dataset_name}, \n{rels_of_interest} \n")
        f.write(f'mrr: {valmrr}, hits@10: {valhits10}, hits@1: {valhits1}, hits@3: {valhits3}, hits@100: {valhits100}\n')
        f.write(f'mrr per rel: {valmrrperrel}\nhits@1 per rel: {valhits1perrel}\nmrr per ts: {valmrrperts}\nhits@1 per ts: {valhits1perts}\n')
        f.write(f' ------------------------------------- \n')
    # append & write to a file which is in the same folder as this script, named "results_summary.txt the following"
    # path_rankings,dataset_name, rels_of_interest, scores
    with open(osp.join(osp.dirname(__file__),"results_summary.txt"), "a") as f:
        f.write(f"{path_rankings},\n {dataset_name}, \n{rels_of_interest} \n")
        f.write(f'mean_r_prec: {mean_r_prec}, mean_weighted_r_prec: {mean_weighted_r_prec}\n')
        f.write(f'mean_normalized_ten_prec: {mean_normalized_ten_prec}, mean_weighted_normalized_ten_prec: {mean_weighted_normalized_ten_prec}, mean_ten_prec: {mean_ten_prec}\n')
        f.write(f'r-prec per rel: {r_prec_per_rel}\nweighted r-prec per rel: {weighted_r_prec_per_rel}\n')
        f.write(f' ------------------------------------- \n')
              
# Print log info
print("\nEvaluation Summary:")
print("Year\tRankings Name\tMean R-Prec\tMean Weighted R-Prec\tMean Normalized Ten-Prec\tMean Weighted Normalized Ten-Prec\tMean Ten-Prec")
for info in log_info:
    print(f"{info[6]}\t{info[0]}\t{info[1]:.4f}\t{info[2]:.4f}\t{info[3]:.4f}\t{info[4]:.4f}\t{info[5]:.4f}")

# Write summary to file
if 'pre-experiment' in rankings_name:
    summary_path = os.path.join(osp.dirname(__file__), "..", "files",  "results", "r_prec", "pre-exp_summary.txt")
else:
    summary_path = os.path.join(osp.dirname(__file__), "..", "files",  "results", "r_prec", "summary.txt")
with open(summary_path, 'w') as f:
    f.write("Evaluation Summary:\n")
    # f.write("Year\tRankings Name\tMean R-Prec\tMean Weighted R-Prec\tMean Normalized Ten-Prec\tMean Weighted Normalized Ten-Prec\tMean Ten-Prec\n")
    f.write("Year\tRankings Name\tMRR\tH@1\tH@3\tH@10\tH@100\tPrec_R\tPrec_{R,weight}\tPrec_10\tPrec_N10\n")
    # for info in log_info:
    #     f.write(f"{info[6]}\t{info[0]}\t{info[1]:.4f}\t{info[2]:.4f}\t{info[3]:.4f}\t{info[4]:.4f}\t{info[5]:.4f}\n")
    for info in log_info2:
        f.write(f"{info[0]}\t{info[1]}\t{info[2]*100:.1f}\t{info[3]*100:.1f}\t{info[4]*100:.1f}\t{info[5]*100:.1f}\t{info[6]*100:.1f}\t{info[7]*100:.1f}\t{info[8]*100:.1f}\t{info[9]*100:.1f}\t{info[10]*100:.1f}\n")  
 
