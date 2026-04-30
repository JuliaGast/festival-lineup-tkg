import numpy as np
import time
import utils

import sys
import os.path as osp
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__)))) 

from tgb.linkproppred.evaluate import Evaluator
from rule_dataset import RuleDataset

import psutil
import json
import os
process = psutil.Process()




def detailed_analysis_r_prec(rule_dataset, head, rel, t, sorted_indices, ground_truth_tails, r_prec, R, top_R_predictions, num_correct_in_top_R, r_prec_tracker, r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict):
    """ conduct all sorts of detailed analysis when we compute the r-prec for a query.
    create the following stuff:
    r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict
    """
                    
    correct_nodes = [rule_dataset.nodes_id_to_string[tail][0] for tail in ground_truth_tails if tail in top_R_predictions]
    missing_nodes = [rule_dataset.nodes_id_to_string[tail][0] for tail in ground_truth_tails if tail not in top_R_predictions]
    false_positives = [rule_dataset.nodes_id_to_string.get(tail, ['wrong'])[0] for tail in top_R_predictions if tail not in ground_truth_tails]

    nodes_of_interest_ids = [int(tail) for tail in ground_truth_tails if tail in top_R_predictions] + [int(tail) for tail in ground_truth_tails if tail not in top_R_predictions] + [int(tail) for tail in top_R_predictions if tail not in ground_truth_tails]
    nodes_of_interest_dict[str((head, rel, t))] = nodes_of_interest_ids # nodes that are correctly predicted, nodes that are missed, and false positives, for this query. We can use this to show the explanations for these nodes in the explainer, if we want to.

    prev_occurences_festival = 0
    prev_ts_festival = 0
    for ts_prev_head in rule_dataset.all_head_t[head]:
        if ts_prev_head < t:
            prev_occurences_festival += 1
    for ts_prev_head in rule_dataset.all_head_t_set[head]:
        if ts_prev_head < t:
            prev_ts_festival += 1
    missing_nodes_and_ranks = {}

    
    for tail in ground_truth_tails: 
        if tail not in top_R_predictions:
            num_prev_occurences = 0
            num_prev_ts= 0
            for ts_prev in rule_dataset.all_head_t[tail]:
                if ts_prev < t:
                    num_prev_occurences += 1
            for ts_prev in rule_dataset.all_head_t_set[tail]:
                if ts_prev < t:
                    num_prev_ts = num_prev_ts + 1
            
            rank_missing = np.where(sorted_indices == tail)[0][0] + 1 # add 1 to get the rank (starting from 1 instead of 0)
            missing_nodes_and_ranks[rule_dataset.nodes_id_to_string[tail][0]] = {'rank': int(rank_missing), 'num_of_prev_occurences': int(num_prev_occurences), 'num_of_prev_timestamps': int(num_prev_ts)}

    if rel not in r_prec_tracker:
        r_prec_tracker[rel] = {}
    if t not in r_prec_tracker[rel]:
        r_prec_tracker[rel][t] = {}
    if head not in r_prec_tracker[rel][t]:
        r_prec_tracker[rel][t][head] = {}
    if not rule_dataset.rels_id_to_string[rel] in r_prec_tracker_string:
        r_prec_tracker_string[rule_dataset.rels_id_to_string[rel]] = {}
    if t not in r_prec_tracker_string[rule_dataset.rels_id_to_string[rel]]:
        r_prec_tracker_string[rule_dataset.rels_id_to_string[rel]][t] = {}
    if not rule_dataset.nodes_id_to_string[head][0] in r_prec_tracker_string[rule_dataset.rels_id_to_string[rel]][t]:
        r_prec_tracker_string[rule_dataset.rels_id_to_string[rel]][t][rule_dataset.nodes_id_to_string[head][0]] ={}
    r_prec_tracker[rel][t][head] = [r_prec, num_correct_in_top_R, R]
    r_prec_tracker_string[rule_dataset.rels_id_to_string[rel]][t][rule_dataset.nodes_id_to_string[head][0]] = {'number_of_prev_occurences_festival': prev_occurences_festival, 'num_of_prev_timestamps': prev_ts_festival, 'rprec': r_prec, 'correct': num_correct_in_top_R, 
                                                'R': R, 'correct_nodes': correct_nodes, 'missing_nodes': missing_nodes_and_ranks, 'false_positives': false_positives}

    
    if r_prec < 0.1:
        bad_queries.append([head, rel, 'x', t])

        if not rule_dataset.rels_id_to_string[rel] in r_prec_bad_queries:
            r_prec_bad_queries[rule_dataset.rels_id_to_string[rel]] = {}
        if t not in r_prec_bad_queries[rule_dataset.rels_id_to_string[rel]]:
            r_prec_bad_queries[rule_dataset.rels_id_to_string[rel]][t] = {}
        if not rule_dataset.nodes_id_to_string[head][0] in r_prec_bad_queries[rule_dataset.rels_id_to_string[rel]][t]:
            r_prec_bad_queries[rule_dataset.rels_id_to_string[rel]][t][rule_dataset.nodes_id_to_string[head][0]] ={}
        r_prec_bad_queries[rule_dataset.rels_id_to_string[rel]][t][rule_dataset.nodes_id_to_string[head][0]] = {'number_of_prev_occurences_festival': prev_occurences_festival, 'num_of_prev_timestamps': prev_ts_festival, 'rprec': r_prec, 'correct': num_correct_in_top_R, 
                                                'R': R, 'correct_nodes': correct_nodes, 'missing_nodes': missing_nodes_and_ranks, 'false_positives': false_positives}

    if r_prec > 0.5:
        good_queries.append([head, rel, 'x', t])

        if not rule_dataset.rels_id_to_string[rel] in r_prec_good_queries:
            r_prec_good_queries[rule_dataset.rels_id_to_string[rel]] = {}
        if t not in r_prec_good_queries[rule_dataset.rels_id_to_string[rel]]:
            r_prec_good_queries[rule_dataset.rels_id_to_string[rel]][t] = {}
        if not rule_dataset.nodes_id_to_string[head][0] in r_prec_good_queries[rule_dataset.rels_id_to_string[rel]][t]:
            r_prec_good_queries[rule_dataset.rels_id_to_string[rel]][t][rule_dataset.nodes_id_to_string[head][0]] ={}
        r_prec_good_queries[rule_dataset.rels_id_to_string[rel]][t][rule_dataset.nodes_id_to_string[head][0]] = {'number_of_prev_occurences_festival': prev_occurences_festival, 'num_of_prev_timestamps': prev_ts_festival, 'rprec': r_prec, 'correct': num_correct_in_top_R, 
                                                'R': R, 'correct_nodes': correct_nodes, 'missing_nodes': missing_nodes_and_ranks, 'false_positives': false_positives}
        
    return r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict

def evaluate_r_prec(rule_dataset, path_rankings, evaluation_mode="test", eval_type='average', eval_rel_head_t_tail={}, detailed_results_flag=False):
    """ evaluate using tgb evaluation framework.
    """
    #print("MEM when eval starts: " +  str(process.memory_info().rss//1000000))
    start3 = time.time()

    num_nodes = rule_dataset.dataset.num_nodes

    
    #print("MEM after init evaluator : " +  str(process.memory_info().rss//1000000))

    if eval_type == 'random':
        # add an order to break ties
        rankings = utils.read_rankings_random(path_rankings, num_nodes, rule_dataset.nodes_string_to_id, rule_dataset.rels_string_to_id, rule_dataset.timestamp_setlist_to_id)

    else:
        print('not implemented')
        rankings = utils.read_rankings(path_rankings)


    test_queries_of_interest = eval_rel_head_t_tail


    r_prec_tracker = {}
    r_prec_tracker_string = {}
    r_prec_bad_queries = {}
    r_prec_good_queries = {}
    r_prec_per_rel = {}
    weighted_r_prec_per_rel = {}
    r_prec_list = []
    weighted_r_prec_list = []
    normalized_ten_prec_list = []
    weighted_normalized_ten_prec_list = []
    ten_prec_list = []

    bad_queries = []
    good_queries = []

    nodes_of_interest_dict = {}
    total_R = 0
    total_TenOrLess = 0
    higher_counter =0
    for rel in test_queries_of_interest:
        # print(f"number of test queries for relation {rel}: {len(test_queries_of_interest[rel])}")
        if not rel in r_prec_per_rel:
            r_prec_per_rel[rel] = -1
        if not rel in weighted_r_prec_per_rel:
            weighted_r_prec_per_rel[rel] = -1
        r_prec_per_rel_list = []
        weighted_r_prec_per_rel_list = []
       
        R_per_rel = 0
        for head in test_queries_of_interest[rel]:
            for t in test_queries_of_interest[rel][head]:
                # print(f"number of test queries for relation {rel}, head {head}, timestamp {t}: {len(test_queries_of_interest[rel][head][t])}")

                ground_truth_tails = test_queries_of_interest[rel][head][t]
                R = len(ground_truth_tails) # how many different tails do we have for this rel, head, timestamp combination in the test set? this is the R in R-precision
                TenOrLess = min(10, R)
                if R > 0:
                    if len(rankings[(head, rel,t)]) == 0:
                        a =1
                    scores_array, higher_counter =utils.create_scores_array(rankings[(head, rel,t)], num_nodes, higher_counter)

                    # get the scores for all nodes and sort them in descending order
                    sorted_indices = np.argsort(scores_array)[::-1] # sort in descending order
                    # check if the ground truth tails are in the top R predictions
                    top_R_predictions = sorted_indices[:R]
                    top_Ten_predictions = sorted_indices[:10]
                    # top_TenOrLess_predictions = sorted_indices[:TenOrLess]
                    num_correct_in_top_R = sum([1 for tail in ground_truth_tails if tail in top_R_predictions])
                    num_correct_checker = sum([1 for tail in top_R_predictions if tail in ground_truth_tails])
                    
                    assert num_correct_in_top_R == num_correct_checker, "num_correct_in_top_R and num_correct_checker should be the same"

                    num_correct_in_top_ten = sum([1 for tail in top_Ten_predictions if tail in ground_truth_tails])
                    # num_correct_in_top_tenorless = sum([1 for tail in top_TenOrLess_predictions if tail in ground_truth_tails])
                    r_prec = num_correct_in_top_R / R
                    r_prec_list.append(r_prec)

                    normalized_ten_prec = num_correct_in_top_ten / TenOrLess
                    normalized_ten_prec_list.append(normalized_ten_prec)

                    ten_prec = num_correct_in_top_ten / 10
                    ten_prec_list.append(ten_prec)


                    ## all sorts of more detailed dicts that contain finegrained stuff:
                    if detailed_results_flag:
                        detailed_results = detailed_analysis_r_prec(rule_dataset, head, rel, t, sorted_indices, ground_truth_tails, r_prec, R, top_R_predictions, num_correct_in_top_R, 
                                                r_prec_tracker, r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict)
                        r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict = detailed_results

                    weighted_r_prec_list.append(r_prec*R)
                    total_R += R

                    weighted_normalized_ten_prec_list.append(normalized_ten_prec*TenOrLess)
                    total_TenOrLess += TenOrLess
                    

                    r_prec_per_rel_list.append(r_prec)
                    weighted_r_prec_per_rel_list.append(r_prec*R)
                    R_per_rel += R
        mean_r_prec = float(np.mean(r_prec_per_rel_list)) if len(r_prec_per_rel_list) > 0 else 0.0
        mean_weighted_r_prec = float(np.sum(weighted_r_prec_per_rel_list)/R_per_rel) if R_per_rel > 0 else 0.0
        

        
        r_prec_per_rel[rel] = mean_r_prec
        weighted_r_prec_per_rel[rel] = mean_weighted_r_prec


    mean_normalized_ten_prec = float(np.mean(normalized_ten_prec_list)) if len(normalized_ten_prec_list) > 0 else 0.0
    mean_weighted_normalized_ten_prec = float(np.sum(weighted_normalized_ten_prec_list)/total_TenOrLess) if total_TenOrLess > 0 else 0.0
    mean_ten_prec = float(np.mean(ten_prec_list)) if len(ten_prec_list) > 0 else 0.0
    

    mean_r_prec = float(np.mean(r_prec_list))
    mean_weighted_r_prec = float(np.sum(weighted_r_prec_list)/total_R) if total_R > 0 else 0.0
        

    # Print evaluation results
    # print('eval mode:', evaluation_mode)
    print('mean r-prec:', mean_r_prec)
    print('mean weighted r-prec:', mean_weighted_r_prec)
    print('mean normalized ten prec:', mean_normalized_ten_prec)
    print('mean weighted normalized ten prec:', mean_weighted_normalized_ten_prec)
    print('mean ten prec:', mean_ten_prec)

    return mean_r_prec, mean_weighted_r_prec, mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, r_prec_per_rel, weighted_r_prec_per_rel, r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict

# for quick test purposes /quick evaluations
if __name__ == "__main__":
    ## preparations. user sets all sorts of things here, such as the dataset name, the path to the rankings, etc.
    dataset_name = "tkgl-concertperformanceonly"
    dataset_name_folder = dataset_name.replace("-", "_")
    
    rankings = ["ranking-a-10-Meta-Llama-70Bt2023.txt"]
    # , "ranking-a-10-Meta-Llama-70Bt2024.txt", "ranking-a-10-Meta-Llama-70Bt2025.txt", 
                # "ranking-a-all-Meta-Llama-70Bt2023.txt", "ranking-a-all-Meta-Llama-70Bt2024.txt", "ranking-a-all-Meta-Llama-70Bt2025.txt", 
                # "ranking-f-10-Meta-Llama-70Bt2023.txt", "ranking-f-10-Meta-Llama-70Bt2024.txt", "ranking-f-10-Meta-Llama-70Bt2025.txt", 
                # "ranking-f-all-Meta-Llama-70Bt2023.txt", "ranking-f-all-Meta-Llama-70Bt2024.txt", "ranking-f-all-Meta-Llama-70Bt2025.txt"]

    # rankings_name = "ranking-a-10-Meta-Llama-70Bt2023.txt"
    # rankings_name = "ranking-a-10-Meta-Llama-70Bt2024.txt"
    # rankings_name = "ranking-a-10-Meta-Llama-70Bt2025.txt"
    # rankings_name = "ranking-a-all-Meta-Llama-70Bt2023.txt"
    # rankings_name = "ranking-a-all-Meta-Llama-70Bt2024.txt"
    # rankings_name = "ranking-a-all-Meta-Llama-70Bt2025.txt"
    # rankings_name = "ranking-f-10-Meta-Llama-70Bt2023.txt"
    # rankings_name = "ranking-f-10-Meta-Llama-70Bt2024.txt"
    # rankings_name = "ranking-f-10-Meta-Llama-70Bt2025.txt"
    # rankings_name = "ranking-f-all-Meta-Llama-70Bt2023.txt"
    # rankings_name = "ranking-f-all-Meta-Llama-70Bt2024.txt"
    # rankings_name = "ranking-f-all-Meta-Llama-70Bt2025.txt"
    rankings_name = rankings[0]

    year = rankings_name.lower().split("-")[-1].split("bt")[-1].split(".")[0]
    print('rankings_name:', rankings_name)
    print('year:', year)


    if 'ranking-a-' in rankings_name:
        rel_list = ['inv_performs_at_festival']
    else:
        rel_list = ['performs_at_festival']
    
    if rel_list[0] == 'performs_at_festival':
        nodes_of_interest_file = "202320242025_artist_test_subset.txt"
    else:
        nodes_of_interest_file = "202320242025_festival_location_test_subset.txt"

    ruledataset = RuleDataset(name=dataset_name, large_data_hardcode_flag=False)

    ## get the test queries for the specified nodes, relations, and timestamp
    nodes_of_interest_path = osp.join(osp.dirname(__file__), "..", "tgb", "datasets", dataset_name_folder, nodes_of_interest_file)
    nodes_of_interest = utils.read_nodes_of_interest(nodes_of_interest_path)
    rel_of_interest_list = [ruledataset.rels_string_to_id[rel] for rel in rel_list]
    timestamp_of_interest = ruledataset.timestamp_setlist_to_id[year]
    eval_rel_head_t_tail = ruledataset.get_all_queries_for_nodes_rels_timestamps_of_interest(nodes_of_interest, rel_of_interest_list, timestamp_of_interest)

    path_rankings = osp.join(osp.dirname(__file__), "..","files", "rankings", dataset_name, rankings_name)
    
    ## run the evaluation
    scores = evaluate_r_prec(ruledataset, path_rankings, evaluation_mode='test', eval_type='random',eval_rel_head_t_tail=eval_rel_head_t_tail, detailed_results_flag=True)
    mean_r_prec, mean_weighted_r_prec, mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, r_prec_per_rel, weighted_r_prec_per_rel, r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict = scores
    
    ## store all sorts of things
    # Create directory if it doesn't exist
    output_dir = osp.join(osp.dirname(__file__), "..", "files",  "results", "r_prec", dataset_name)
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

    # print(scores)



