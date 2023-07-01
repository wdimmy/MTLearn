import argparse
from collections import defaultdict
from mat import DatalogMTLReasoner
import os 


parser = argparse.ArgumentParser()
parser.add_argument('--strategy', type=str, default='maximum', help='Please choose a strategy from maximum, weighted_maximum, average, weighted_average, and meteor')
parser.add_argument('--beta', type=float, default=0.5, help='Specificy the beta value if using MeTeoR')
parser.add_argument('--data_dir', type=str, default='data/demo', help='Path to the data file.')
args = parser.parse_args()


writer = open(args.data_dir+"/Datalogmtl_rules.txt", "w")
num_widnows = len(os.listdir(args.data_dir + "/DatalogMTL"))
results = defaultdict(list)
for filename in os.listdir(args.data_dir + "/DatalogMTL"):
    with open(args.data_dir + "/DatalogMTL/"+filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            items = line.strip().split("\t")
            results[items[-1]].append(float(items[-2]))

if args.strategy == "meteor":
    # tranform the data to the format of MeTeoR
    reasoner = DatalogMTLReasoner(f"{args.data_dir}/train.txt", data_type="quadruple")

for rule, scores in results.items():
    if args.strategy == "maximum":
        score = max(scores)
    elif args.strategy == "weighted_maximum":
        score = max(scores) * len(scores) / num_widnows
    elif args.strategy == "average":
        score = sum(scores) / len(scores)
    elif args.strategy == "weighted_average":
        score = sum(scores) / len(scores) * len(scores) / num_widnows
    elif args.strategy == "meteor":
        score = reasoner.apply_rules(rule, target_predicate=rule.split("(")[0], beta=args.beta)
        score = score["score"]

    writer.write("{}\t{}\n".format(score, rule))
    