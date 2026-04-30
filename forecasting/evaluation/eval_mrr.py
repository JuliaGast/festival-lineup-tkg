import numpy as np
import time

from tqdm import tqdm
import sys
import os.path as osp
sys.path.append(osp.dirname(osp.dirname(osp.abspath(__file__)))) 

from tgb.linkproppred.evaluate import Evaluator
from counttrucola.rule_based.rule_dataset import RuleDataset
import eval_utils

import psutil
process = psutil.Process()




def evaluate(rule_dataset, path_rankings, progressbar_percentage, evaluation_mode="test", eval_type='average', special_evalquads=None, rels_of_interest=None):
    """ evaluate using code from the tgb evaluation framework.
    https://github.com/shenyangHuang/TGB
    """
    #print("MEM when eval starts: " +  str(process.memory_info().rss//1000000))
    start3 = time.time()
    dataset = rule_dataset.dataset
    num_nodes = rule_dataset.dataset.num_nodes
    split_mode = evaluation_mode
    evaluator = Evaluator(name=dataset.name, k_value=[1, 3, 10,100])
    neg_sampler = dataset.negative_sampler  
    
    #print("MEM after init evaluator : " +  str(process.memory_info().rss//1000000))

    if evaluation_mode == "val":
        testdata = rule_dataset.val_data
        print("loading negative val samples")
        dataset.load_val_ns() # load negative samples, i.e. the nodes that are not used for time aware filter mrr
    elif evaluation_mode == "test":
        testdata = rule_dataset.test_data
        print("loading negative test samples")
        dataset.load_test_ns() # load negative samples, i.e. the nodes that are not used for time aware filter mrr
    if special_evalquads is not None:
        testdata = np.array(special_evalquads)

    #print("MEM after loading negative samples: " +  str(process.memory_info().rss//1000000))

    perf_list = np.zeros(len(testdata))
    hits10_list = np.zeros(len(testdata))
    hits1_list = np.zeros(len(testdata))
    hits3_list = np.zeros(len(testdata))
    hits100_list = np.zeros(len(testdata))

    if eval_type == 'random':
        # add an order to break ties
        rankings = eval_utils.read_rankings_random(path_rankings, num_nodes)
        # rankings = rule_utils.read_rankings_order(path_rankings, num_nodes)
    else:
        rankings = eval_utils.read_rankings(path_rankings)

    #print("MEM after reading rankings: " +  str(process.memory_info().rss//1000000))

    print('>>> starting evaluation for every triple, in the ', evaluation_mode, 'set')
    total_iterations = len(testdata)
    # result_ranks = "result_ranks_"+dataset.name+ ".txt"
    # file_save_mrr = open(result_ranks, "w")
    result_ranks = "hits1"+dataset.name+ ".txt"
    file_hits = open(result_ranks, "w")
    # i_list = []

    increment = int(total_iterations*progressbar_percentage) if int(total_iterations*progressbar_percentage) >=1 else 1
    remaining = total_iterations
    mrr_per_rel = {}
    hit1_per_rel = {}
    mrr_per_ts = {}
    hit1_per_ts = {}
    with tqdm(total=total_iterations) as pbar:
        counter = 0
        num_evaluted = 0
        for i, (src, dst, t, rel) in enumerate(zip(testdata[:,0], testdata[:,2], testdata[:,3], testdata[:,1])):
            # Update progress bar
            counter += 1
            if rels_of_interest is not None and rel not in rels_of_interest:
                continue

            if counter % increment == 0:
                remaining -= increment
                pbar.update(increment)
            if remaining < increment:
                pbar.update(remaining)

            
                
            original_t = rule_dataset.timestamp_id2orig[t]

            # Query negative batch list - all negative samples for the given positive edge that are not temporal conflicts (time aware mrr)
            neg_batch_list = neg_sampler.query_batch(np.array([src]), np.array([dst]), np.array([original_t]), edge_type=np.array([rel]), split_mode=split_mode)

            # Make predictions for given src, rel, t
            # Compute a score for each node in neg_batch_list and for actual correct node dst
            scores_array =eval_utils.create_scores_array(rankings[(src, rel,t)], num_nodes)

            predictions_neg = scores_array[neg_batch_list[0]]
            predictions_pos = np.array(scores_array[dst])

            # Evaluate the predictions
            input_dict = {
                "y_pred_pos": predictions_pos,
                "y_pred_neg": predictions_neg,
                "eval_metric": ['mrr'], 
            }

            predictions = evaluator.eval(input_dict)
            perf_list[i] = float(predictions['mrr'])
            hits10_list[i] = float(predictions['hits@10'])
            hits1_list[i] = float(predictions['hits@1'])
            hits3_list[i] = float(predictions['hits@3'])
            hits100_list[i] = float(predictions['hits@100'])

            num_evaluted += 1
            if float(predictions['hits@1']) > 0:
                file_hits.write(str(src) + "\t" + str(rel) + "\t" + str(dst) + "\t" + str(t) + '\n')

            if rel not in mrr_per_rel:
                mrr_per_rel[rel] = (float(predictions['mrr']), 1)
                hit1_per_rel[rel] = (float(predictions['hits@1']), 1)
            else:
                mrr_per_rel[rel] = (mrr_per_rel[rel][0] + float(predictions['mrr']), mrr_per_rel[rel][1] + 1)
                hit1_per_rel[rel] = (hit1_per_rel[rel][0] + float(predictions['hits@1']), hit1_per_rel[rel][1] + 1)

            if t not in mrr_per_ts:
                mrr_per_ts[t] = (float(predictions['mrr']), 1)
                hit1_per_ts[t] = (float(predictions['hits@1']), 1)
            else:
                mrr_per_ts[t] = (mrr_per_ts[t][0] + float(predictions['mrr']), mrr_per_ts[t][1] + 1)
                hit1_per_ts[t] = (hit1_per_ts[t][0] + float(predictions['hits@1']), hit1_per_ts[t][1] + 1)

    for rel in mrr_per_rel:
        mrr_per_rel[rel] = (mrr_per_rel[rel][0] / mrr_per_rel[rel][1], mrr_per_rel[rel][1])
        hit1_per_rel[rel] = (hit1_per_rel[rel][0] / hit1_per_rel[rel][1], hit1_per_rel[rel][1])

    for t in mrr_per_ts:
        mrr_per_ts[t] = (mrr_per_ts[t][0] / mrr_per_ts[t][1], mrr_per_ts[t][1])
        hit1_per_ts[t] = (hit1_per_ts[t][0] / hit1_per_ts[t][1], hit1_per_ts[t][1])

    counter = 0
    result_ranks = "hits1"+dataset.name+ ".txt"


    # Calculate mean MRR and mean hits@10
    if num_evaluted > 0:
        mrr = float(perf_list.sum()/num_evaluted)
        hits10 = float(hits10_list.sum()/num_evaluted)
        hits1 = float(hits1_list.sum()/num_evaluted)
        hits3 = float(hits3_list.sum()/num_evaluted)
        hits100 = float(hits100_list.sum()/num_evaluted)
    else:
        mrr, hits10, hits1, hits3, hits100 = 0.0, 0.0, 0.0, 0.0, 0.0

    # mrr = float(np.mean(perf_list))
    # hits10 = float(np.mean(hits10_list))
    # hits1 = float(np.mean(hits1_list))
    # hits3 = float(np.mean(hits3_list))
    # hits100 = float(np.mean(hits100_list))

    # Print evaluation results
    print('eval mode:', split_mode)
    print('mean mrr:', mrr)
    print('mean hits@1:', hits1)
    print('mean hits@3:', hits3)
    print('mean hits@10:', hits10)
    print('mean hits@100:', hits100)
    print('time to evaluate:', time.time()-start3)
    return mrr, hits10, hits1, hits3, hits100, mrr_per_rel, hit1_per_rel, mrr_per_ts, hit1_per_ts
# for quick test purposes /quick evaluations
if __name__ == "__main__":
    dataset_name = "tkgl-concert"
    ruledataset = RuleDataset(name=dataset_name, large_data_hardcode_flag=False)
    rels_of_interest =[0,23]
    path_rankings = osp.join(osp.dirname(__file__), "..", "recurrency_baseline", "rankings", dataset_name, "rankings_0_True_rels_0_23_test.txt")



    scores = evaluate(ruledataset, path_rankings, progressbar_percentage=0.01, evaluation_mode='test', eval_type='random', rels_of_interest=rels_of_interest)
    valmrr, valhits10, valhits1, valhits3, valhits100, valmrrperrel,valhits1perrel, valmrrperts, valhits1perts = scores
    print(scores)

    # append & write to a file which is in the same folder as this script, named "results_summary.txt the following"
    # path_rankings,dataset_name, rels_of_interest, scores
    with open(osp.join(osp.dirname(__file__),"results_summary.txt"), "a") as f:
        f.write(f"{path_rankings},\n {dataset_name}, \n{rels_of_interest} \n")
        f.write(f'mrr: {valmrr}, hits@10: {valhits10}, hits@1: {valhits1}, hits@3: {valhits3}, hits@100: {valhits100}\n')
        f.write(f'mrr per rel: {valmrrperrel}\nhits@1 per rel: {valhits1perrel}\nmrr per ts: {valmrrperts}\nhits@1 per ts: {valhits1perts}\n')
        f.write(f' ------------------------------------- \n')
        



