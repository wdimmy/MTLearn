import argparse
import os 
from pathlib import Path
from collections import defaultdict
from meteor_reasoner.utils.loader import load_program, load_dataset
from meteor_reasoner.materialization.materialize import coalescing_d, naive_immediate_consequence_operator
from meteor_reasoner.materialization.materialize import build_index
from meteor_reasoner.utils.parser import parse_rule
from dataloader import DataLoader
import numpy as np 


parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', type=str, default='data/demo')
parser.add_argument('--rulefile_path', type=str, default='data/demo/DatalogMTL/temporal_rules.txt', help='Path to the rule file.')
parser.add_argument('--window_size', type=int, default=3, help='Size of window')
parser.add_argument('--target', type=str, default="test", help='test or valid')
parser.add_argument('--mode', type=str, default="extrapolation", help='by default, it is extrapolation, otherwise it is interpolation.')
parser.add_argument('--RQ', type=int, default=0, help='whether use the RQ metric')
parser.add_argument('--goldrules_path', type=str, default="data/demo/gold_rules.txt", help='benchmark rules if using RQ metric')
args = parser.parse_args()


# Disclaimer: part of the evaluation code was taken from from TLogic
def filter_candidates(test_query, candidates, test_data):
    other_answers = test_data[
        (test_data[:, 0] == test_query[0])
        * (test_data[:, 1] == test_query[1])
        * (test_data[:, 2] != test_query[2])
        * (test_data[:, 3] == test_query[3])
    ]

    if len(other_answers):
        objects = other_answers[:, 2]
        for obj in objects:
            candidates.pop(obj, None)

    return candidates


def calculate_rank(test_query_answer, candidates, num_entities, setting="best"):
   
    rank = num_entities
    if test_query_answer in candidates:
        conf = candidates[test_query_answer]
        all_confs = list(candidates.values())
        ranks = [idx for idx, x in enumerate(all_confs) if x == conf]
        if setting == "average":
            rank = (ranks[0] + ranks[-1]) // 2 + 1
        elif setting == "best":
            rank = ranks[0] + 1
        elif setting == "worst":
            rank = ranks[-1] + 1

    return rank


def calculate_rq(rulefile_path, goldrules_path):
    """
    Args:
        rulefile_path: path to the rule file or a list of rules
        goldrules_path: path to the gold rules or a list of rules
    Returns: a float number
    """
    if isinstance(rulefile_path, str):
        with open(Path(rulefile_path), "r") as f:
            rules = []
            for line in f:
                _, rule = line.strip().split("\t") # do not need the rule score 
                rule = parse_rule(rule)
                rules.append(rule)
    else:
        rules = []
        for line in rulefile_path:
            rule = parse_rule(line.strip())
            rules.append(rule)
    if isinstance(goldrules_path, str):
        with open(Path(goldrules_path), "r") as f:
            goldrules = []
            for line in f:
                rule = parse_rule(line.strip())
                goldrules.append(rule)
    else:
        goldrules = []
        for line in goldrules_path:
            rule = parse_rule(line.strip())
            goldrules.append(rule)
    
    match = 0 
    for rule in goldrules:
        cnt = 0 
        new_dataset = []
        groundings = {}
        head_atom = rule.head 
        target_predicate = head_atom.get_predicate()
        target_t = 10 # your can specify any natural number here 
        body_atom = rule.body
        for atom in body_atom:
            for ent in atom.get_entity():
                if ent.type == "variable":
                    cnt += 1
                    groundings[ent.name] = "new_{cnt}"

            operators = atom.operators
            if len(operators) > 0:
                operator = operators[0]
                interval_val = operator.interval.left_value 
                new_dataset.append("{}({})@{}".format(atom.get_predicate(), ",".join([groundings[ent.name] if ent.type=="variable" else ent.name for ent in atom.get_entity()]), target_t-interval_val))
            else:
                 new_dataset.append("{}({})@{}".format(atom.get_predicate(), ",".join([groundings[ent.name] if ent.type=="variable" else ent.name for ent in atom.get_entity()]), target_t))


        ground_ents = []
        for ent in head_atom.get_entity():
            if ent.type == "variable":
                ent.type = "constant"
                ent.name = groundings[ent.name]
                ground_ents.append(ent)
            else:
                ground_ents.append(ent)
        target_entity = tuple(ground_ents)
        D = load_dataset(new_dataset)
        coalescing_d(D)
        D_index = build_index(D)
        derived_facts_dict = naive_immediate_consequence_operator(rules, D, D_index) 

        if target_predicate in derived_facts_dict and target_entity in derived_facts_dict[target_predicate]:
              for interval in derived_facts_dict[target_predicate][target_entity]:
                    if int(interval.left_value) <= target_t <= int(interval.right_value):
                         match += 1

    return round(match/len(goldrules), 3)


predictions = defaultdict(list)
golds = defaultdict(list)
valid = defaultdict(list)
valid_t = set()

dataloader = DataLoader(args.data_dir)
program = load_program(dataloader.rule_path)

hits_1 = 0
hits_3 = 0
hits_10 = 0
mrr = 0

num_samples = 2 * len(dataloader.test) # the number of triplets in the test set

if args.target == "valid":
    dataset = dataloader.valid
else:
    dataset = dataloader.test # dict: key is the timestamp and the value is the list of triplets
quadruples = []
for t, triplets in dataset.items():
    for triplet in triplets:
        quadruples.extend((triplet[0], triplet[1], triplet[2], t))
test_numpy_data = np.array(quadruples)

for t, data in dataset.items():
    # obtain the required dataset
    chunked_data = dataloader.construct_window_data(window_size=args.window_size, cur_t=t, mode=args.mode)
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
                        if int(interval.left_value) == t:
                            predictions[(entity[0].split("_")[1], predicate.split("_")[1], int(interval.left_value))].append((rule_score, str(entity[1]).split("_")[1])) 
                            predictions[(entity[1].split("_")[1], predicate.split("_")[1], int(interval.left_value))].append((rule_score, str(entity[0]).split("_")[1])) 
       
        for triplet in data:
            test_query = np.array([triplet[0], triplet[1], triplet[2], t])
            candidates = dict()
            if (triplet[0], triplet[1], t) in predictions: # the object entity
                for item in predictions[(triplet[0], triplet[1], t)]:
                        candidates[item[1]] = max(candidates[item[1]], item[0]) # take the highest score as we described in the paper 
                
                candidates = filter_candidates(test_query, candidates, test_numpy_data)
                rank = calculate_rank(test_query[2], candidates, len(dataloader.entity2id))

                if rank:
                        if rank <= 10:
                            hits_10 += 1
                            if rank <= 3:
                                hits_3 += 1
                                if rank == 1:
                                    hits_1 += 1
                        mrr += 1 / rank

            if (triplet[2], triplet[1], t) in predictions: # the subject entity 
                for item in predictions[(triplet[2], triplet[1], t)]:
                        candidates[item[1]] = max(candidates[item[1]], item[0]) # take the highest score as we described in the paper 
                
                candidates = filter_candidates(test_query, candidates, test_numpy_data)
                rank = calculate_rank(test_query[0], candidates, len(dataloader.entity2id))

                if rank:
                        if rank <= 10:
                            hits_10 += 1
                            if rank <= 3:
                                hits_3 += 1
                                if rank == 1:
                                    hits_1 += 1
                        mrr += 1 / rank
                    

hits_1 /= num_samples
hits_3 /= num_samples
hits_10 /= num_samples
mrr /= num_samples

print("Hits@1: ", round(hits_1, 6))
print("Hits@3: ", round(hits_3, 6))
print("Hits@10: ", round(hits_10, 6))
print("MRR: ", round(mrr, 6))

if args.RQ == 1 and os.path.exists(args.goldrules_path):
    rq_value = calculate_rq(args.rulefile_path, args.goldrules_path)
    print("RQ: ", rq_value)