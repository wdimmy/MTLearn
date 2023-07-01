from pathlib import Path
from collections import defaultdict
from meteor_reasoner.utils.loader import load_program, load_dataset
from meteor_reasoner.materialization.materialize import coalescing_d, naive_immediate_consequence_operator
from meteor_reasoner.materialization.materialize import build_index
from meteor_reasoner.utils.parser import parse_rule

def calculate_hit(predictions, golds, hit=3):
    """
    Args:
        predictions: {
                       ("a", "r1", 21)] : ["b", "c"],
                       ("b", "r2", 1)] :  ["d", "f"]
                     }
        golds: {
                    21: [("a", "r1", "c")],
                    23: [("b", "r2", "k")]
                }
        hit: 3
    Returns: a float number
    """
    total_cnt = 0
    hit_cnt = 0
    for timestamp in golds:
        for head, relation, tail in golds[timestamp]:
            total_cnt += 1
            if (head, relation, timestamp) in predictions:
                candidates = predictions[(head, relation, timestamp)][:hit]
                if tail in candidates:
                    hit_cnt += 1
    return round(hit_cnt / total_cnt, 3)


def calculate_mrr(predictions, golds):
    """
    Args:
        predictions: {
                       ("a", "r1", 21)] : ["b", "c"],
                       ("b", "r2", 1)] :  ["d", "f"]
                     }
        golds: {
                    21: [("a", "r1", "c")],
                    23: [("b", "r2", "k")]
                }
        hit: 3
    Returns: a float number
    """
    total_cnt = 0
    ranks = 0
    for timestamp in golds:
        for head, relation, tail in golds[timestamp]:
            total_cnt += 1
            if (head, relation, timestamp) in predictions:
                candidates = predictions[(head, relation, timestamp)]
                if tail in candidates:
                    ranks += 1/(candidates.index(tail)+1)
    return round(ranks / total_cnt, 3)


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


if __name__ == "__main__":
    goldrules = ["A(X,Y):- Boxminus[1,1]B(X,Y), C(X,Y)"]
    rules = ["A(X,Y):- Boxminus[1,1]B(X,Y)", "B(X,ab):- C(X,Y)"]
    print(calculate_rq(rules, goldrules))