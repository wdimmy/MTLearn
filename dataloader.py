import numpy as np 
import json 

class DataLoader(object):
    def __init__(self, dataset_dir):

        """
        Store the information about the graph (train/valid/test set).
        Assume that the file contains each line in the format of "subject \t relation \t object  \t timepoint".

        Parameters:
            dataset_dir (str): path to the graph dataset directory
        
        Returns:
             None 
        """

        self.dataset_dir = dataset_dir
        self.entity2id = json.load(open(f"{dataset_dir}/entity2id.json"))
        self.relation2id = json.load(open(f"{dataset_dir}/relation2id.json"))

        # build the time to id 
        self.create_time2id()
    

        self.train = self.load_data("train")
        self.valid = self.load_data("valid")
        self.test = self.load_data("test")
        self.total = self.train | self.valid | self.test


    def load_data(self, data_type):
        """
        Load the data from the file. 
        """
        data = {}
        with open(f"{self.dataset_dir}/{data_type}.txt") as f:
            lines = f.readlines()
            for line in lines:
                subject, relation, object, timepoint = line.strip().split("\t")
                data.setdefault(self.time2id[timepoint], []).append((self.entity2id[subject], self.relation2id[relation], self.entity2id[object]))
        
        return data
    
    def construct_window_data(self, cur_t, window_size, mode="extrapolation"):
        if mode == "extra":
            chunked_data = []
            for t in range(cur_t-1, max(cur_t-window_size-1, 0), -1):
                data = self.total[t]
                for triplet in data:
                    chunked_data.append("relation_{}(entity_{},entity_{})@{}".format(triplet[1], triplet[0], triplet[2], t))
            return chunked_data
        else: # chunk data contains cur_t - window_size, ..., cur_t, ....,  cur_t + window_size
            chunked_data = []
            for t in range(max(cur_t-window_size-1, 0), min(cur_t+window_size, len(self.time2id))):
                data = self.total[t]
                for triplet in data:
                    chunked_data.append("relation_{}(entity_{},entity_{})@{}".format(triplet[1], triplet[0], triplet[2], t))
            return chunked_data

    
    def create_time2id(self):
        """
        Create a mapping from timepoint to id. 
        """
        self.time2id = {}
        timepoints = set() 
        with open(f"{self.dataset_dir}/train.txt") as f:
            lines = f.readlines()
            for line in lines:
                _, _, _, timepoint = line.strip().split("\t")
                timepoints.add(timepoint)
        with open(f"{self.dataset_dir}/valid.txt") as f:
            lines = f.readlines()
            for line in lines:
                _, _, _, timepoint = line.strip().split("\t")
                timepoints.add(timepoint)
        with open(f"{self.dataset_dir}/test.txt") as f:
            lines = f.readlines()
            for line in lines:
                _, _, _, timepoint = line.strip().split("\t")
                timepoints.add(timepoint)
        
        timepoints = sorted(list(timepoints))
        for i in range(len(timepoints)):
            self.time2id[timepoints[i]] = i
        
        

    