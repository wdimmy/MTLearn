import argparse
import os 
from pathlib import Path
from collections import defaultdict
from dataloader import DataLoader
# AnyBURL could be used on any dataset that comes as a set of triplets. 
# The triplets are stored in a text file, where each line contains a triplet in the form of <head> <relation> <tail>.
# The triplets are separated by a tab character.

parser = argparse.ArgumentParser(description='Convert data to a format that can be used by the model.')
parser.add_argument('--data_dir',    type=str, default='data/extrapolation/icews14', help='Path to the data file.')
parser.add_argument('--window_size', type=int, default=8, help='Size of window')
args = parser.parse_args()

dataloader = DataLoader(args.data_dir)

Path(args.data_dir+"/train").mkdir(parents=True, exist_ok=True)
for cur_t in range(args.window_size, len(dataloader.train)):
    chunked_data = []
    for t in range(cur_t-args.window_size, cur_t):
        data = dataloader.train[t]
        for triplet in data:
            chunked_data.append("entity_{}\trelation_{}_{}\tentity_{}\n".format(triplet[0], triplet[1], t, triplet[2]))
    tmp = args.data_dir+"/train/{}.txt".format(cur_t)
    writer = open(tmp, "w")
    writer.writelines(chunked_data)
    writer.close()


if __name__ == "__main__":
    pass 














