
# Part 2: Forecasting and Evaluation

## Preliminaries

Install the required dependencies before running any experiments:
- For CEN, RE-GCN, TLogic, and evaluation: install `forecasting/requirements.txt`
- For CountTRUCOLA only: install `forecasting/counttrucola/requirements.txt`

## Preprocessing

If you did not create or modify the datasets yourself, no preprocessing is needed — you will be prompted to download the datasets automatically from [MADATA](https://madata.bib.uni-mannheim.de/822/) when running the forecasting methods.

If you modified or created your own dataset version, follow these steps:

1. We use the same structure and dataset loaders as [TGB 2.0](https://tgb.complexdatalab.com/). Datasets need to be preprocessed accordingly for all forecasting models except CogNTKE.
2. Put the output from Part 1 (data creation) in `forecasting/tgb/datasets/tkgl_concert/` (or `tkgl_concertperformanceonly`, `tkgl_concertwithshortcuts`, or your own folder, depending on which variant you use). You need `tkgl-concert_edgelist.csv`, `relation2id.txt`, `entity2id.txt`, and `timestamp2int.txt`.
3. Run `tkglc_concert_ns_gen.py` (in the same folder) to produce `tkgl-concert_val_ns.pkl` and `tkgl-concert_test_ns.pkl`, which are required for evaluation.
4. To get quadruple representations as txt files (e.g., with train/val/test splits), run `forecasting/tgb/datasets/make_readable_edgelist.py`. You can configure whether to use IDs or string labels in the output.

Train/val/test splits are applied automatically, currently set to 1971–2023 / 2024 / 2025. This ensures the test set contains only one year (2025) and avoids placing the COVID years (2020–2022) in the val or test splits. Splits can be adjusted manually in `tgb/linkproppred/dataset.py` in the `pre_process()` method.

## TKG Forecasting Models

Each model has its own subfolder. To run a model, follow the README in its folder if present; otherwise run the main script directly, e.g.:

```bash
python regcn/regcn.py
```

Parameters for RE-GCN and CEN are set in `modules/tkg_utils.py`.

When running a model for the first time, you will be prompted to download the dataset from MADATA. If you agree, it will be downloaded and extracted automatically.

**Exception — CogNTKE:** datasets are not downloaded automatically. Download them manually from [MADATA](https://madata.bib.uni-mannheim.de/822/) and place the contents of the relevant `quadruples` folder in `cogntke/data/dataset_name/`, e.g. `cogntke/data/tkgl_concert/`.

Each model automatically produces a rankings file in its own folder, which is used as input for evaluation.

## Evaluation

### Input format

Each model produces a rankings file in the following format:
```
23377 0 ? 54
6224 0.3708296931753017 2680 0.30341860664053366 279 0.3033302071881444 5069 0.29898289389656185 1183 0.282103998553195 5641 0.2762588128866934 6892 0.24455386243057708 13599 0.23862076951783828 1751 0.21601323764007263 5712 0.17059496504256488 1171 0.1677454540749337  [...]
18904 0 ? 54
1895 0.45089842051271123 11017 0.29691586905569234 3067 0.2945832064399847 9989 0.2919881150387693 10217 0.2692707044930819 5596 0.2616726568876996 6018 0.15812885572524826 2065 0.14241617234839854 1741 0.1264015223893663 2331 0.12382827557498521 1 0.10442513652636742 5069 0.10316755940670141 1751 0.08945366159552492 1183 0.08582317052951716 636 0.08527775943809635 279 0.08362675855432378 2035 0.07431275741938781 1382 0.07054545117086031 6181 0.07002439078789857 226 0.06587563790898832
[...]
```
Each query is on one line: `subject_node_id rel_id ? timestamp`, followed by a line of `predicted_node_id score` pairs in decreasing order of score. Scores do not need to cover all nodes. If two nodes share the same score, they are assigned ranks randomly. Node and relation IDs correspond to the `tgb_id` column in `node_mapping.csv` and `rel_mapping.csv` in `tgb/datasets/dataset_name/`.

### Evaluation scripts

- **MRR and Hits@k:** `evaluation/eval_mrr.py` — set the rankings filename and directory at the top of the script.
- **R-Precision and Normalized 10-Precision:** `evaluation/eval_r_prec.py` — same configuration.
- **All metrics at once:** `evaluation/eval_allmetrics.py` — set multiple rankings files and directories; outputs a `results_summary.txt` file.

## LLM Experiments

### Preparing inputs

We extract all nodes that are subjects or objects of quadruples `(s, performs_at_festival, o, t)` in 2025:
- Subjects (artists) → `artists_test.txt`
- Objects (festivals) → `festival_test.txt`

Both files are in `llm/prompts/`. To regenerate them, run `forecasting/tgb/datasets/tkgl_concert/make_readable_edgelists_LLM.py`.

- Artists are used for queries of the form: *artist A performs at which festival in 2025?*
- Festivals are used for queries of the form: *which artists perform at festival F in 2025?*

For festival queries, location information is also needed. Run `make_readable_edgelists_LLM.py` with `musicbrainz_flag=True` to generate the MusicBrainz-enriched version of `quads.txt`, then run `add_festival_venues.py` to append country and city to each festival.

### Prompting

See `llm/prompts/LLMTKG.ipynb` for the prompting code and inputs.

### Matching outputs and creating rankings

Use `llm/matching/convert.py` to match LLM outputs back to nodes in the TKG.

To run it, place LLM outputs from previous step at:
`files/All_tests_LLM/prompt_output_{LLM_ID}{YEAR}_alltests_CM.csv`
or adjust the path in the script accordingly.

This produces two rankings files per LLM:
`files/rankings/ranking-f-all-{LLM_ID}{YEAR}.txt   # festival queries`
`files/rankings/ranking-a-all-{LLM_ID}{YEAR}.txt   # artist queries`
To compute aggregated scores across both query directions, create a combined `ranking-both-all.txt` by concatenating the contents of the `a-all` and `f-all` files.

### Evaluation

Evaluation scripts for LLMs are in `llm/eval_code/` and follow the same structure as described above for TKG models.

### Subset experiments (test set leakage / knowledge cutoff analysis)

To run experiments on a filtered subset of nodes:

1. Run `make_readable_edgelists_LLM.py` with `min_timestamps=[2023, 2024, 2025]`. This restricts the node pool to artists and festivals that appear in quadruples from those years.
2. Run the same script with `musicbrainz_flag=True`, then run `add_festival_venues.py`.
3. Run `randomly_select_testnodes.py` to sample 50 artists and 50 festivals. This produces:
   - `202320242025artist_test_subset.txt`
   - `festival_test_subset.txt`
   - `2025_quads_test_subset_festivalswhichartists.txt` — queries of the form *which artists perform at festival F?*
   - `2025_quads_test_subset_artistswhichfestivals.txt` — queries of the form *which festivals does artist A perform at?*

   These two test files are not symmetric: the festivals file may include artists in the ground truth who did not appear in 2023–2024, and vice versa. Subset files are in `llm/prompts/sub_testquads_per_year/`.

> **Note:** These experiments are run on the `concertperformanceonly` variant. Artists who released an album in 2023 but did not perform at a festival are excluded.