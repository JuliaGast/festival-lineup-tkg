import sys
import os.path as osp
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__)))) 

from counttrucola.rule_based.rule_dataset import RuleDataset


import psutil
process = psutil.Process()

from eval_mrr import evaluate as evaluate_mrr
from eval_r_prec import evaluate_r_prec

import os
import json




if __name__ == "__main__":
    dataset_name = "tkgl-concert" # tkgl-concertperformanceonly tkgl-concertwithshortcuts
    log_info= []
    ruledataset = RuleDataset(name=dataset_name, large_data_hardcode_flag=False)
        
    
    all_paths = []
    ## Recurrency baseline
    ## specify the path to the model rankings here, and append them to all_paths.
    # path_rankings = osp.join("..", "recurrency_baseline", "rankings", dataset_name, "rankings_0_True_rels_0_1_test.txt")  
    # all_paths.append(path_rankings)
    ## counttrucola
    # path_rankings = osp.join(osp.dirname(__file__), "..", "counttrucola", "files", "rankings", "tkgl_concert"+"_test.txt")
    # all_paths.append(path_rankings)
    # # tlogic 
    # path_rankings = osp.join(osp.dirname(__file__), "..", "tlogic", "rankings", dataset_name, "rankings_30_10_10_1_2_3_rels_0_1_test.txt") 
    path_rankings = osp.join(osp.dirname(__file__), "..", "tlogic", "rankings", dataset_name, "rankings_30_10_10_1_2_rels_0_29_test.txt") 
    all_paths.append(path_rankings)
    # # # cogntke - performance only
    # path_rankings = osp.join(osp.dirname(__file__), "..", "counttrucola", "files", "rankings", "tkgl_concertperformanceonly"+"_test.txt")
    # all_paths.append(path_rankings)
    # # regcn- performance only
    # path_rankings = osp.join(osp.dirname(__file__), "..", "regcn", "rankings", dataset_name+"_test.txt")
    # all_paths.append(path_rankings)
    # # cen - performance only
    # path_rankings = osp.join(osp.dirname(__file__), "..", "cen", "rankings", dataset_name+"_cen_test.txt")
    # all_paths.append(path_rankings)


    # rankings_name = dataset_name.replace("-", "_")
    rels_of_interest_list = []
    if dataset_name == "tkgl-concertperformanceonly":
        rels_of_interest_list = [[0], [1], [0,1]]
    elif dataset_name == "tkgl-concertwithshortcuts":
        rels_of_interest_list = [[0], [29], [0,29]]
    else:
        rels_of_interest_list = [[0], [23], [0,23]]

    for path_rankings in all_paths:
        for rels_of_interest in rels_of_interest_list:
            print(f"Evaluating {path_rankings} for rels {rels_of_interest} on dataset {dataset_name}")

            scores = evaluate_mrr(ruledataset, path_rankings, progressbar_percentage=0.01, evaluation_mode='test', eval_type='random', rels_of_interest=rels_of_interest)
            valmrr, valhits10, valhits1, valhits3, valhits100, valmrrperrel,valhits1perrel, valmrrperts, valhits1perts = scores
            print(scores)

            # append & write to a file which is in the same folder as this script, named "results_summary.txt the following"
            # path_rankings,dataset_name, rels_of_interest, scores
            with open(osp.join(osp.dirname(__file__),"results_summary.txt"), "a") as f:
                f.write(f"{path_rankings},\n {dataset_name}, \n{rels_of_interest} \n")
                f.write(f'mrr: {valmrr}, hits@10: {valhits10}, hits@1: {valhits1}, hits@3: {valhits3}, hits@100: {valhits100}\n')
                f.write(f'mrr per rel: {valmrrperrel}\nhits@1 per rel: {valhits1perrel}\nmrr per ts: {valmrrperts}\nhits@1 per ts: {valhits1perts}\n')
                f.write(f' ------------------------------------- \n')
                

            scores = evaluate_r_prec(ruledataset, path_rankings, evaluation_mode='test', eval_type='random', rels_of_interest=rels_of_interest, detailed_results_flag=True)
            mean_r_prec, mean_weighted_r_prec,mean_normalized_ten_prec, mean_weighted_normalized_ten_prec, mean_ten_prec, r_prec_per_rel, weighted_r_prec_per_rel, r_prec_tracker,r_prec_tracker_string, good_queries, bad_queries, r_prec_bad_queries, r_prec_good_queries, nodes_of_interest_dict = scores
            log_info.append(['2025', path_rankings, valmrr, valhits1, valhits10, mean_r_prec,  mean_normalized_ten_prec, rels_of_interest])
            
            summary_path = os.path.join(osp.dirname(__file__),  "summary_overview_" + dataset_name + ".txt")
            with open(summary_path, 'w') as f:
                f.write("Evaluation Summary:\n")
                f.write("Year\tREL\tRankings Name\tMRR\tH@1\tH@10\tPrec_R\tPrec_N10\n")
                for info in log_info:
                    
                    f.write(f"{info[0]}\t{info[7]}\t{info[1]}\t{info[2]*100:.1f}\t{info[3]*100:.1f}\t{info[4]*100:.1f}\t{info[5]*100:.1f}\t{info[6]*100:.1f}\n")  
        
            
            # append & write to a file which is in the same folder as this script, named "results_summary.txt the following"
            # path_rankings,dataset_name, rels_of_interest, scores
            with open(osp.join(osp.dirname(__file__),"results_summary.txt"), "a") as f:
                f.write(f"{path_rankings},\n {dataset_name}, \n{rels_of_interest} \n")
                f.write(f'mean_r_prec: {mean_r_prec}, mean_weighted_r_prec: {mean_weighted_r_prec}\n')
                f.write(f'mean_normalized_ten_prec: {mean_normalized_ten_prec}, mean_weighted_normalized_ten_prec: {mean_weighted_normalized_ten_prec}, mean_ten_prec: {mean_ten_prec}\n')
                f.write(f'r-prec per rel: {r_prec_per_rel}\nweighted r-prec per rel: {weighted_r_prec_per_rel}\n')
                f.write(f' ------------------------------------- \n')
                


        

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
