from collections import defaultdict
import os
from pathlib import Path
import argparse

# AnyBURL configuration file
template_properties = """
PATH_TRAINING = {}

PATH_OUTPUT   = {}

SNAPSHOTS_AT = {}

WORKER_THREADS = 7

"""

parser = argparse.ArgumentParser()
parser.add_argument('--data_dir',   type=str, default='data/demo', help='Path to the data file.')
parser.add_argument('--runtime', type=int, default=20, help='Time span in AnyBURL')
args = parser.parse_args()

Path(args.data_dir+"/Datalog").mkdir(parents=True, exist_ok=True)
for filename in os.listdir(args.data_dir+"/train"):
    print("Handline the file: ", filename)
    timepoint = filename.split(".")[0]
    writer = open("config-learn.properties", "w")
    writer.write(template_properties.format(f"{args.data_dir}/train/{filename}", f"{args.data_dir}/Datalog/{timepoint}", args.runtime))
    writer.close()
    stream = os.popen('java -Xmx12G -cp AnyBURL-23-1.jar de.unima.ki.anyburl.Learn config-learn.properties')
    stream.read()







