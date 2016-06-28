## CleanEprime.py
## 1. Removes bad characters ([ ] .) from header names in reformatted eprime file
## 2. Pulls rest of eprime data file into pandas dataframe (uses clean header names from step 1)
## 3. Prints dimensions of eprime dataframe (could add check here for number of columns)
## 4. Recodes accuracy for GNG trials (updates GNGCueACC and JitteredITIACC and creates GNGACC column)
## 5. Writes new dataframe to comma-delimited file (SUBJECTID_clean_eprime.csv)

import pandas as pd
import numpy as np
import argparse
import csv
import os
import re


#Pull the data in based on a parameter entered at the command line
parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', required=True, help='Name of reformatted eprime file')
args = parser.parse_args()
infile = args.input
#infile = '/mnt/stressdevlab/dep_threat_pipeline/999/behavior/999_reformatted_eprime.csv'

#Remove bad characters from header names ([,],.)
hdr = pd.read_csv(infile, sep = '\t', nrows = 1)
hdr.rename(columns=lambda x: re.sub('[\[\].]','',x), inplace=True)

#Get rest of the datafile with cleanheader
data = pd.read_csv(infile, sep = '\t', skiprows = [0], names = hdr, low_memory = False)

#Change ProcedureBlock values, so that GNGRun2and3 is split correctly into GNGRun2 and GNGRun3
data.loc[data['Block'] == 8, 'ProcedureBlock'] = 'GNGRun2'
data.loc[data['Block'] == 9, 'ProcedureBlock'] = 'GNGRun3'

print data[(data['ProcedureBlock'] == 'GNGRun2')].shape
print data[(data['ProcedureBlock'] == 'GNGRun3')].shape

#Recode accuracy for GNG trials

#Go trials
data.loc[(data['ConditionLogLevel5'] == 'Go') & (data['GNGCueRT'] > 0), 'GNGCueACC'] = 1
data.loc[(data['ConditionLogLevel5'] == 'Go') & (data['GNGCueRT'] == 0), 'GNGCueACC'] = 0
data.loc[(data['ConditionLogLevel5'] == 'Go') & (data['JitteredITIRT'] > 0), 'JitteredITIACC'] = 1
data.loc[(data['ConditionLogLevel5'] == 'Go') & (data['JitteredITIRT'] == 0), 'JitteredITIACC'] = 0

#NoGo trials
data.loc[(data['ConditionLogLevel5'] == 'NoGo') & (data['GNGCueRT'] > 0), 'GNGCueACC'] = 0
data.loc[(data['ConditionLogLevel5'] == 'NoGo') & (data['GNGCueRT'] == 0), 'GNGCueACC'] = 1
data.loc[(data['ConditionLogLevel5'] == 'NoGo') & (data['JitteredITIRT'] > 0), 'JitteredITIACC'] = 0
data.loc[(data['ConditionLogLevel5'] == 'NoGo') & (data['JitteredITIRT'] == 0), 'JitteredITIACC'] = 1

#GNGCueACC + JitteredITIACC should be > 0 for accurate trials (GNGACC = 1)
data['GNGCombinedACC'] = data['GNGCueACC'] + data['JitteredITIACC']
data.loc[(data['GNGCombinedACC'] > 0), 'GNGACC'] = 1
data.loc[(data['GNGCombinedACC'] == 0), 'GNGACC'] = 0

#This function renames column so that name structure follows pattern : ColNameRunNum
def RenameColumnToMatchPattern (origName):
    RunNum = str(re.findall('\d+', str(origName)))[2]
    loc = origName.split(str(RunNum))
    newName = loc[0] + loc[1] + str(RunNum)
    return newName

#Rename a few column names to make pattern-matching more straight-forward
for prefix in ['prep2', 'probe2', 'ReactivityITI2', 'CSImageRecall2', 'RecallITI2', 'Threat2', 'ThreatResp2']:
    for cName in data.filter(like=str(prefix)).columns.values:
        newName = RenameColumnToMatchPattern(cName)
        data.rename(columns = {str(cName):str(newName)}, inplace = True)
        
#Write to file
outfile = os.path.dirname(infile) + '/' + os.path.basename(infile).split('_')[0] + '_clean_eprime.csv'
data.to_csv(outfile, sep=',')
