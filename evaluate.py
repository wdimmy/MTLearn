import argparse
import os 
from pathlib import Path
from collections import defaultdict
from meteor_reasoner.utils.loader import load_program, load_dataset
from meteor_reasoner.materialization.materialize import coalescing_d, naive_immediate_consequence_operator
from meteor_reasoner.materialization.materialize import build_index
from meteor_reasoner.utils.parser import parse_rule
from evaluation_metrics import calculate_hit, calculate_mrr, calculate_rq


parser = argparse.ArgumentParser()
parser.add_argument('--datafile_path', type=str, default='data/demo/valid', help='Path to the data file.')
parser.add_argument('--rulefile_path', type=str, default='data/demo/DatalogMTL_rule.txt', help='Path to the rule file.')
parser.add_argument('--window_size', type=int, default=2, help='Size of window')
parser.add_argument('--hit', type=int, default=10, help='the k in hit@k')
parser.add_argument('--RQ', type=int, default=0, help='whether use the RQ metric')
parser.add_argument('--goldrules_path', type=str, default="data/demo/gold_rules.txt", help='benchmark rules if using RQ metric')
args = parser.parse_args()

predictions = defaultdict(list)
golds = defaultdict(list)
valid = defaultdict(list)
valid_t = set()

with open(Path(args.datafile_path), "r") as f:
    lines = f.readlines()
    for line in lines:
        items = line.strip().split("\t")
        t = int(items[3])
        valid[t].append((items[0], items[1], items[2], t))
        valid_t.add(t)
valid_t = sorted(list(valid_t))
for i in range(args.window_size-1, len(valid_t)):
    i = valid_t[i]
    needed_timepoints = [i-j for j in range(1, args.window_size)]
    target_data = valid[i]
    for triplet in target_data:
         # the triplet is in the format of "predicate(subject, object)@timepoint"
        #  predicate = triplet.split("(")[0]
        #  s = triplet.split("(")[1].split(",")[0]
        #  o = triplet.split("(")[1].split(",")[1].split(")")[0]
         golds[i].append((triplet[0], triplet[1], triplet[2]))
    chunked_data = []
    for j, t in enumerate(needed_timepoints):
        data = valid[t]
        for triplet in data:
            chunked_data.append("{}({},{})@{}".format(triplet[1], triplet[0], triplet[2], triplet[3]))

    D = load_dataset(chunked_data)
    coalescing_d(D)
    D_index = build_index(D)

    with open(Path(args.rulefile_path), "r") as f:
     rules = []
     for line in f:
         rule_score, rule = line.strip().split("\t")
         rule = parse_rule(rule)
         derived_facts_dict = naive_immediate_consequence_operator([rule], D, D_index) 
         for predicate in derived_facts_dict:
            for entity in derived_facts_dict[predicate]:
                for interval in derived_facts_dict[predicate][entity]:
                    if int(interval.left_value) == i:
                        predictions[(str(entity[0]), predicate, int(interval.left_value))].append((rule_score, str(entity[1]))) 

# sorted
keys = predictions.keys()
for key in keys:
    values = set(["{}_{}".format(item[0], item[1]) for item in predictions[key]]) # remove duplicates 
    values = sorted(list(values), reverse=True) # sorted by scores 
    values = [item.split("_")[1] for item in values]
    predictions[key] = values


hit_value = calculate_hit(predictions, golds, args.hit)
mrr_value = calculate_mrr(predictions, golds)

if args.RQ == 1 and os.path.exists(args.goldrules_path):
    rq_value = calculate_rq(args.rulefile_path, args.goldrules_path)


with open("MTLearn_log.txt", "a", encoding="utf-8") as fout:
     fout.write(f"The logs for the data file {args.datafile_path} based on the mined rules {args.rulefile_path}\n")
     fout.write(f"Hits@{args.hit}: {hit_value}\n")
     fout.write(f"Hits@{args.hit}: {hit_value}\n")
     if args.RQ == 1 and os.path.exists(args.goldrules_path):
        fout.write(f"RQ: {rq_value}\n")





    
    


    


