## GetRelCols.py
## 1. Reads SUBJECTID_clean_eprime.csv into pandas dataframe
## 2. Gets list of columns that are relevant to the task
## 3. Reads in subset of task-specific columns from eprime data file
## 4. Saves task-specific behavioral data to file

import pandas as pd
import numpy as np
import argparse
import csv
import os


#Pull the data in based on a parameter entered at the command line
parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', required=True, help='Name of clean eprime file')
parser.add_argument('--task', '-t', required=True, help='Name of task')
args = parser.parse_args()
infile = args.input
task = args.task

#Gets list of columns that are relevant to the task
colfile = '/mnt/stressdevlab/dep_threat_pipeline/bin/eprimeparser/' + task + 'SaveCols.csv'
cols = pd.read_csv(colfile, sep=',', low_memory = False)
taskcols = cols.columns.values

#Only read in the relevant columns (this helps immensely with readability of the data files!)
data = pd.read_csv(infile, sep=',', usecols = taskcols, low_memory = False)

#Filter rows to specific task
subset = data[data['ProcedureBlock'].str.contains(task)]
print 'Shape of data for ' + task + ': ' + str(subset.shape)

#Write output to the behavior directory
outfile = os.path.dirname(infile) + '/' + task + '-eprime.csv'
subset.to_csv(outfile, header = True, index = False)

