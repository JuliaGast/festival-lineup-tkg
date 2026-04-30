
# Part 2: Forecasting and Evaluation


## C. Preprocessing to run the forecasting experiments 
If you did not create or modify the datasets yourself, you do not need to do anything, you will be prompted to download the datasets automatically from Madata when running the forecating methods. If you modify or created your own dataset versions however, you need to conduct the following steps.
* We use the same structure and dataset loaders as in TGB 2.0 (https://tgb.complexdatalab.com/). This means, datasets need to be in the same preprocessed way for most forecasting models  (all except cogntke) that we test on in tgb. 
* put the output from step B above in the folder `forecasting/tgb/datasets/tkgl_concert/` (or tkgl_concertperformanceonly, or tkgl_concertwithshortcuts, depending on which variant you use). You need `tkgl-concert_edgelist.csv` and `relation2id.txt`, `entity2id.txt`, `timestamp2int.txt`.
* run `tkglc_concert_ns_gen.py` (in the same folder), which produces e.g. tkgl-concert_val_ns.pkl, and _test_ns.pkl, which are needed for testing.
* if you want the quadruple representation as txt files, e.g. with train val test splits, you need to run `forecasting/tgb/datasets/make_readable_edgelist.py`. There you can set if you want the ids, or the strings in the txt files.
* the train/valid/test splits are conducted automatically. currently we set them to 1971-2023/2024/2025, to ensure that the test set only contains one year (2025), and to not get any problems with the covid years (2020-2021 and 2022) being in the valid or test splits. the splits can be changed manually in `tgb/linkproppred/dataset.py` in method `pre_process()`


## Evaluation
Input:
* For evaluation of the models, you need a txt file with rankings. It will be automatically produced by each model in this repo. If you want to add a new model, and evaluate it, it needs to produce its own ranking file.
* A ranking file looks like this:
```
23377 0 ? 54
6224 0.3708296931753017 2680 0.30341860664053366 279 0.3033302071881444 5069 0.29898289389656185 1183 0.282103998553195 5641 0.2762588128866934 6892 0.24455386243057708 13599 0.23862076951783828 1751 0.21601323764007263 5712 0.17059496504256488 1171 0.1677454540749337  [...]
18904 0 ? 54
1895 0.45089842051271123 11017 0.29691586905569234 3067 0.2945832064399847 9989 0.2919881150387693 10217 0.2692707044930819 5596 0.2616726568876996 6018 0.15812885572524826 2065 0.14241617234839854 1741 0.1264015223893663 2331 0.12382827557498521 1 0.10442513652636742 5069 0.10316755940670141 1751 0.08945366159552492 1183 0.08582317052951716 636 0.08527775943809635 279 0.08362675855432378 2035 0.07431275741938781 1382 0.07054545117086031 6181 0.07002439078789857 226 0.06587563790898832
[...]
```
* It contains each test (or validation) query, in the form: `subject_node_id rel_id ? timestamp`, and then a new line with `predicted_object_node predicted_score predicted_object_node predicted_score ...` for each predicted object node that is assigned a score. that can be all nodes in the dataset, but do not have to be. The scores should be sorted in decreasing order (If two nodes have the same order, they will get a random rank assigned, i.e. if the second and third node have the same score they will be assigned ranks (2,3) randomly) The ids are the ones that you can find in the second column (tgb_id) of node_mapping.csv and rel_mapping.csv in folder `tgb/datasets/dataset_name/`. 
Evaluation Code:
* The code for computing the MRR and Hits is in `evaluation/eval_mrr.py`. It is based on the code presented in TGB2.0. you have to set the filename and directoriy of the rankings file of interest.
* The code for computing the RPrecision and Normalized 10Precision is in `evaluation/eval_r_prec.py`.  you have to set the filename and directoriy of the rankings file of interest.
* You can also automatically compute all evaluation metrics for multiple methods using `evaluation/eval_allmetrics.py`. There you have to set the filenames and directories of the rankings files of interest. It will produce a file `results_summary.txt` that contains results for the relevant metrics. 

## LLM experiments
* You can create the data for the LLMs with `forecasting/tgb/datasets/tkgl_concert/make_readable_edgelists_LLM.py`. 
* to prepare for the LLM experiments, we extract all nodes that are subjects or objects to quadruples (S, performs_at_festival, o, t) in the year 2025. 
* We store the subjects in artists_test.txt and the objects in festival_test.txt.
* The artists will be used for llm queries artist a performs at which festival 2025?, the festivals will be used for llm queries which artist performs at festival f 2025?.
* for the festivals we additionally need the information on the location. for this, we need to run make_readable_edgelists_LLM.py, with musicbrainz_flag=True so that also the musicbrainz_flag version of the quads.txt is created. Then, run add_festival_venues.py, which adds the country and city to each festival.

LLM experiments with only a subset of nodes, to understand the impact of test set leakage/cutoff date.
* first, run make_readable_edgelists_LLM.py, and set  min_timestamps=[2023,2024,2025]. this ensures that only artists and festivals are extracted from quadruples where both the artist was playing somewhere in those timestamps, and the festival was happening in those years.
* second, run as above the same with musicbrainz_flag=True, and add_festival_venues.py
* third, run randomly_select_testnodes.py. This randomly selects 50 artists and 50 festivals and stores them in artist_test_subset.txt and festival_test_subset.txt. This also extracts the subset from the testset that can be used for testing 2025_quads_test_subset_festivalswhichartists.txt (to test queries of ?, performs at, festival f) and 2025_quads_test_subset_artistswhichfestivals.txt (other way round) for each year. note that these are not the same, since 2025_quads_test_subset_festivalswhichartists.txt only contains festivals that have happened in 2023,2024,2025 but might include artists in the ground truth that have not appeared in 2023 or 2024, and the other way round.
* Note: I run this on concert2, which is a kg that only contains festivals and their artists, and festivals and their locations. this means, if an artist released an album in 2023 but did not play at a festival, it is not included in the llm subset experiments.
