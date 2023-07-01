import argparse
import os 
from pathlib import Path
from collections import defaultdict
# AnyBURL could be used on any dataset that comes as a set of triplets. 
# The triplets are stored in a text file, where each line contains a triplet in the form of <head> <relation> <tail>.
# The triplets are separated by a tab character.

parser = argparse.ArgumentParser(description='Convert data to a format that can be used by the model.')
parser.add_argument('--data_dir',    type=str, default='data/demo', help='Path to the data file.')
parser.add_argument('--window_size', type=int, default=2, help='Size of window')
parser.add_argument('--data_format', type=str, default="quadruple", help='quadrupe or p(a,b)@t')
args = parser.parse_args()


print("=======Begin to group the triplets by timepoints.============\n")
train_t = set()
train = defaultdict(list)
with open(Path(args.data_dir) / f"train.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        items = line.strip().split("\t")
        t = int(items[3])
        train[t].append((items[0], items[1], items[2]))
        train_t.add(t)
train_t = sorted(list(train_t))

valid = defaultdict(list)
valid_t = set()

with open(Path(args.data_dir) / f"valid.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        items = line.strip().split("\t")
        t = int(items[3])
        valid[t].append((items[0], items[1], items[2]))
        valid_t.add(t)

valid_t = sorted(list(valid_t))

test = defaultdict(list)
test_t = set()
with open(Path(args.data_dir) / f"test.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        items = line.strip().split("\t")
        t = int(items[3])
        test[t].append((items[0], items[1], items[2]))
        test_t.add(t)
test_t = sorted(list(test_t))

timepoitns = sorted(train_t + valid_t + test_t)
time_mapping = {}
for i, t in enumerate(timepoitns):
    time_mapping[t] = i


print("=======End of grouping the triplets by timepoints.============\n")
Path(args.data_dir+"/train").mkdir(parents=True, exist_ok=True)
for i in range(args.window_size,len(train_t)):
    i = train_t[i]
    needed_timepoints = [i-j for j in range(args.window_size)]
    chunked_data = []
    for j, t in enumerate(needed_timepoints):
        data = train[t]
        for triplet in data:
            chunked_data.append("{}\t{}_{}\t{}\n".format(triplet[0], triplet[1], time_mapping[t], triplet[2]))
    tmp = args.data_dir+"/train/{}.txt".format(i)
    writer = open(tmp, "w")
    writer.writelines(chunked_data)
    writer.close()

Path(args.data_dir+"/valid").mkdir(parents=True, exist_ok=True)
for i in range(len(train_t)+args.window_size, len(valid_t)):
    i = valid_t[i]
    needed_timepoints = [i-j for j in range(args.window_size)]
    chunked_data = []
    for j, t in enumerate(needed_timepoints):
        data = valid[t]
        for triplet in data:
            chunked_data.append("{}\t{}_{}\t{}\n".format(triplet[0], triplet[1], time_mapping[t], triplet[2]))
    tmp = args.data_dir+"/valid/{}.txt".format(i)
    writer = open(tmp, "w")
    writer.writelines(chunked_data)
    writer.close()

Path(args.data_dir+"/test").mkdir(parents=True, exist_ok=True)
for i in range(len(valid_t)+args.window_size, len(test_t)):
    i = test_t[i]
    needed_timepoints = [i-j for j in range(args.window_size)]
    chunked_data = []
    for j, t in enumerate(needed_timepoints):
        data = test[t]
        for triplet in data:
            chunked_data.append("{}\t{}_{}\t{}\n".format(triplet[0], triplet[1], time_mapping[t], triplet[2]))
    tmp = args.data_dir+"/test/{}.txt".format(i)
    writer = open(tmp, "w")
    writer.writelines(chunked_data)
    writer.close()


if __name__ == "__main__":
    pass 














