# MTLearn: Extracting Temporal Rules Using Datalog Rule Learners

[Under Review] This repository contains the code for the paper submitted for KR 2024.

## Quick Links
- [Installation](#Installation)
- [Datalog Rule Learners](#Datalog-Rule-Learners)
- [Datasets](#Datasets)
- [How to Run](#How-to-Run)

## Installation
We suggest to create a conda environment:
```bash
conda create -n mtlearn python=3.8 numpy
conda activate mtlearn
```
## Datalog Rule Learners
In this paper, we have tried the other two different kinds of Datalog Rule Learner, whose information are provided as follows:

| Baselines   | Code                                                                      | 
|-------------|---------------------------------------------------------------------------|
| AMIE+ ([Luis Galárraga et al., 2015](https://link.springer.com/article/10.1007/s00778-015-0394-1))    | https://github.com/dig-team/amie                                  | 
| Popper([A Cropper et al., 2020](https://link.springer.com/article/10.1007/s10994-020-05934-z))      | https://github.com/logic-and-learning-lab/Popper   | 

## Datasets
The three benchmarks (icews14, icews18 and icews0515) for the extrapolation experiments could be downloaded from [here](https://github.com/liu-yushan/TLogic/tree/main/data); and the three benchmarks (icews14<sup>I</sup> and icews0515<sup>I</sup>) for the interpolation experiments could be downloaded from [here](https://github.com/soledad921/ATISE); and tLUBM and weather benchmarks are contructed following the steps described in [here](https://github.com/wdimmy/MeTeoR), in which the 46 manually contructed rules are provided in the current repo (/programs/tLUBM.txt). For the iTemporal(1-5), we provide their configurations, so that the rules and the datasets could be generated by loading the configuration files into the [iTemporal Web Interface](https://github.com/kglab-tuwien/iTemporal). All downloaded datasets should be put in the data folder.

## How to Run
Before running, the user should preprocess datasets.
First, we need to preprocess the data and make them suitable as the input for the Datalog rule learner. Assume you have temporal benchmark stored in data/extrapolation/icews14, which contains train.txt, valid.txt and test.txt, each of file comes as a set of quaduple，e.g., anne visit US 2019, and the separator can be blank or tab, then we run the following command to handle the data

```bash
python data_converter.py --data_dir data/extrapolation/icews14 --window_size 8
```
where the two required arguments 'data_dir' and 'window_size' represent the data path and the window size we want to split. After this, we can see three folders~(train, valid and test) are created under 'data/YAGO', which contain the processed results.


Next, we can use the Datalog rule learner to learn the static rules, and we can run the following command

```bash
python generate_rules.py --data_dir data/extrapolation/icews14
```
After this, we can see a new folder 'Datalog', which obtain many files containing 'Datalog' rules together with their confidence scores, and the number of files equals to the number of windows. 


Next, we need to conver the Datalog rules into DatalogMTL, and we can run the following command 

```bash
python rule_converter.py -data_dir data/extrapolation/icews14
```

After this, we can see a new folder 'DatalogMTL', which obtain many files containing 'DatalogMTL' rules together with their confidence scores, and the number of files equals to the number of windows. 

Finally, we use the specified scoring strategy to generate a final set of DatalogMTL rules.

```bash
python scoring.py --data_dir data/extrapolation/icews14 --strategy maximum
```

where --strategy could be any of the following choices:
- maximum
- weighted maximum
- average
- weighted average
- meteor

In particular, if you use the 'meteor' scoring strategy, you can specify another argument --beta (the default value is 0.5).

Now, we are ready to evaluate

```bash
python evaluate.py --data_dir  data/extrapolation/icews14 --rulefile_path data/extrapolation/icews14/DatalogMTL.txt --window_size 8 
```
where 'datafile_path' denotes the path of the evaluated temporal dataset file, the 'rulefile_path' represents the path of our generated DatalogMTL rule file. 

In particular, if you want to use 'RQ' evaluation metric, you can add the two additional arguments: '-RQ' and '--goldrules_path ', where the argument 'goldrules_path' denotes the path to the benchmark DatalogMTL rule. 
