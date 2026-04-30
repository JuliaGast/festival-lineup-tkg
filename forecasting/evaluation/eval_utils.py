import numpy as np

def read_rankings_random(path_rankings, num_nodes):
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
    with open(path_rankings, "r") as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            sub, rel, _, t = lines[i].split(" ")
            tuples_candidates_with_scores = {}

            if lines[i+1] != "\n":
                candidates = lines[i+1].split(" ")

                tokens = [(int(candidates[x]), float(candidates[x+1])) for x in range(0, len(candidates), 2)] # candidate and score

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
    return rankings


def read_rankings(path_rankings):
    '''
    Returns the rankings that are saved before in a text file
    :param path_rankings: the path of the file where the rankings should be loaded from
    :return rankings: rankings is a dictionary of the following format rankings[(sub, rel, obj, t)][candidate] = score of the candidate
    '''
    rankings = {}

    with open(path_rankings, "r") as file:
        lines = file.readlines()
        for i in range(0, len(lines), 2):
            sub, rel, obj, t = lines[i].split(" ")
            tuples_candidates_with_scores = {}
            if lines[i+1] != "\n":
                candidates = lines[i+1].split(" ")
                i = 0
                tuples_candidates_with_scores = {int(candidates[x]): float(candidates[x+1]) for x in range(0, len(candidates), 2)}

            rankings[(np.int64(sub), np.int64(rel), np.int64(t))] = tuples_candidates_with_scores
    return rankings

def create_scores_array(predictions_dict, num_nodes):
    """ 
    Create an array of scores from a dictionary of predictions.
    predictions_dict: a dictionary mapping indices to values
    num_nodes: the size of the array
    returns: predictions an array of scores of len num_nodes
    """
    keys_array = np.fromiter(predictions_dict.keys(), dtype=int)
    values_array = np.fromiter(predictions_dict.values(), dtype=np.float64)
    
    predictions = np.zeros(num_nodes, dtype=np.float64)
    predictions[keys_array] = values_array
 
    return predictions
