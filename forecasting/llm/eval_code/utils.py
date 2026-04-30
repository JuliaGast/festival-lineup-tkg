import numpy as np
from copy import copy
def read_rankings_random(path_rankings, num_nodes, node_to_id_dict, rel_to_id_dict, time_to_id_dict):
    '''
    Returns the rankings that are saved before in a text randomly sort the ties
    Instead of dircetly using the scores, we add 
    * randomly shuffle the order of the candidates with the same score
    * add an order to break ties, i.e. the first element in the list has the highest score, second element the second highest score, etc.
    :param path_rankings: the path of the file where the rankings should be loaded from
    :return rankings: rankings is a dictionary of the following format rankings[(sub, rel, obj, t)][candidate] = score of the candidate
    '''
    rankings = {}
    scores = np.linspace(1, 1/num_nodes, num_nodes).tolist() # we need maximum as many scores as we have nodes
    with open(path_rankings, "r", encoding="utf-8") as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            new_max_node = copy(num_nodes)
            outside_counter = 0
            sub_string, rel_string, _, t_string = lines[i].split("\t")

            t_string = t_string.strip() # remove newline character
            sub = node_to_id_dict.get(sub_string, None)
            rel = rel_to_id_dict.get(rel_string, None)
            t = time_to_id_dict.get(t_string, None)

            if sub is None:
                if not 'notfound:' in sub_string:
                    if not 'wrong:' in sub_string:
                        if not 'xxlfound:' in sub_string:
                            print(f"Warning: subject {sub_string} not found in node_to_id_dict. BUG?")
                            exit()
            if rel is None:
                print(f"Warning: relation {rel_string} not found in rel_to_id_dict. BUG?")
            if t is None:
                print(f"Warning: timestamp {t_string} not found in time_to_id_dict. BUG?")
                exit()
            tuples_candidates_with_scores = {}

            if lines[i+1] != "\n":
                candidates = lines[i+1].split("\t")
                tokens = []
                for x in range(0, len(candidates), 2):
                    candidate_string = candidates[x]
                    # if we could not find the candidate, i.e it is a not found or wrong candidate, we do not add it to the list 
                    # of candidates with scores, 
                    candidate_id = node_to_id_dict.get(candidate_string, new_max_node)
                    if candidate_id==new_max_node:
                        outside_counter += 1
                        if not candidate_string.startswith("notfound:") and not candidate_string.startswith("wrong:") and not candidate_string.startswith("xxlfound:"):

                            # if the candidate is still none, this is an indicator that there is some sort of bug.
                            print(f"Warning: candidate {candidate_string} not found in node_to_id_dict. BUG?")
                            exit()
                        new_max_node += 1 # we increase the max node id for the next not found candidate
                    tokens.append((candidate_id, float(candidates[x+1]))) # candidate and score
                if tokens == []:
                    print(f"Warning: no candidates found for {(sub_string, rel_string, t_string)}. BUG?")
                    a =1
                # tokens = [(int(candidates[x]), float(candidates[x+1])) for x in range(0, len(candidates), 2)] # candidate and score
                if outside_counter > 0:
                    # print(f"Warning: {outside_counter} candidates were not found in node_to_id_dict. They are assigned new ids starting from {num_nodes}.")
                    # print(f"to {new_max_node}. ")
                    wrong_counter = 0
                    notfound_counter = 0
                    for x in candidates:
                        if x.startswith("notfound:"):
                            notfound_counter += 1
                        elif x.startswith("wrong:"):
                            wrong_counter += 1
                    # print(f"Out of the {outside_counter} candidates, {notfound_counter} were not found and {wrong_counter} were wrong. ")
                rankings_shuffled = []
                tie_rankings = []
                latest_score= 0.0

                for node_score in tokens:
                    if not(node_score[1] == latest_score) and latest_score != 0.0: # at the end of same score tokens                        
                        np.random.shuffle(tie_rankings) # shuffle the tie groups
                        for sr in tie_rankings:
                            rankings_shuffled.append(sr)
                        tie_rankings = []
                    tie_rankings.append(node_score) # collect all tokens with the same score (tie groups)
                    latest_score = node_score[1]

                np.random.shuffle(tie_rankings) # shuffle the same score tokens

                for sr in tie_rankings:
                    rankings_shuffled.append(sr) # append all the tie rankings to a list

                # we add an order to break ties, i.e. the first element in the list has the highest score, 
                # second element the second highest score, etc.
                cou = 0
                for x in range(0, len(rankings_shuffled)):
                    tuples_candidates_with_scores[int(rankings_shuffled[x][0])] = float(scores[cou]) 
                    cou+=1
            
            rankings[(np.int64(sub), np.int64(rel), np.int64(t))] = tuples_candidates_with_scores

            for key in rankings:
                if len(rankings[key]) == 0:
                    print(f"Warning: no candidates with scores found for key {key}. BUG?")
    return rankings


def create_scores_array(predictions_dict, num_nodes, higher_counter=0):
    """ 
    Create an array of scores from a dictionary of predictions.
    predictions_dict: a dictionary mapping indices to values
    num_nodes: the size of the array
    returns: predictions an array of scores of len num_nodes
    """
    keys_array = np.fromiter(predictions_dict.keys(), dtype=int)
    values_array = np.fromiter(predictions_dict.values(), dtype=np.float64)
    
    len_predictions = max(num_nodes, max(keys_array) + 1)
    if len_predictions > num_nodes:
        higher_counter +=1


    predictions = np.zeros(len_predictions, dtype=np.float64)
    predictions[keys_array] = values_array
 
    return predictions, higher_counter

def read_nodes_of_interest(nodes_of_interest_path):
    
    nodes_of_interest = []
    with open(nodes_of_interest_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            nodes_line = line.strip().split(";")[0] # remove newline character and split by comma
            nodes_of_interest.append(nodes_line)

    if not len(nodes_of_interest) == 50:
        print(f"Warning: expected 50 lines in nodes_of_interest file, but got {len(nodes_of_interest)}. BUG?")
        print(f"nodes_of_interest: {nodes_of_interest}" )
        exit()
    return nodes_of_interest