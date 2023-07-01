from collections import defaultdict
import os
from pathlib import Path
import argparse
from meteor_reasoner.utils.parser import parse_rule
from  meteor_reasoner.classes.literal import Literal, Operator
from meteor_reasoner.classes.interval import Interval
from meteor_reasoner.classes.rule import Rule


parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', type=str, default='data/demo', help='Path to the data file.')
args = parser.parse_args()


def convert_to_datalogmtl(rule):
    try:
        rule = rule.replace("<=", ":-")
        rule = parse_rule(rule)
    except:
        return None 
    results = []
    head_point = int(rule.head.get_predicate().split("_")[1])

    head_atom = rule.head
    head_atom.atom.predicate = rule.head.get_predicate().split("_")[0]
    for body_atom in rule.body:
        predicate_timepoint = int(body_atom.get_predicate().split("_")[1])
        if predicate_timepoint >= head_point:
            return None 
        predicate_name = body_atom.get_predicate().split("_")[0]
        body_atom.atom.predicate = predicate_name
        operator = Operator("Boxminus", Interval(head_point - predicate_timepoint, head_point - predicate_timepoint, False, False))
        atom = Literal(body_atom.atom, [operator])
        results.append(atom)
    rule = Rule(head_atom, results)
    return rule

Path(args.data_dir+"/DatalogMTL").mkdir(parents=True, exist_ok=True)
for filename in os.listdir(args.data_dir + "/Datalog"):
    if "log" in filename:
        continue
    with open(Path(args.data_dir)/f"Datalog/{filename}", "r") as f:
        lines = f.readlines()
        print(lines)
        writer = open(Path(args.data_dir)/f"DatalogMTL/{filename}", "w")
        for line in lines:
            print(line)
            items = line.strip().split("\t")
            rule = convert_to_datalogmtl(items[-1])
            print(rule)
            if rule is None:
                continue
            writer.write("{}\t{}\n".format(items[2], rule))

        writer.close()