## Python dependencies
import pandas as pd
import numpy as np
import argparse
import csv
import os

#Pull the data in based on a parameter entered at the command line
parser = argparse.ArgumentParser()
parser.add_argument('--subject', '-s', required=True, help='Name of subject to be processed')
args = parser.parse_args()
subject = args.subject

SubjectDir = '/mnt/stressdevlab/dep_threat_pipeline/' + str(subject) + '/'
InFile = SubjectDir + 'behavior/' + str(subject) + '_clean_eprime.csv'

# Emulate unix touch (create dummy text file to mark progress in getting onsets)
def Touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def FindSimpsons (data):

    Results = ['RunName', 'SimpsonOnset', 'SimpsonDuration']
    
    SimpsonChars = ['Marge','Lisa','Bart','Homer','Maggie']
    
    for Simpson in SimpsonChars:
        OnsetTime = Simpson + 'SimpsonOnsetTime'
        OnsetToOnsetTime = Simpson + 'SimpsonOnsetToOnsetTime'

        d = data.loc[(data[OnsetTime] > 0)]
        
        Task = d['ProcedureBlock']
        TriggerOn = d['TriggerWAITRTTimeBlock']
        AdjSimpsonOn = (d[OnsetTime] - TriggerOn) / float(1000)
        SimpsonDuration = d[OnsetToOnsetTime] / float(1000)
        Run = str(Task.iloc[0]).replace('Run','')
        Temp = np.hstack([Run,AdjSimpsonOn,SimpsonDuration])
        Results = np.vstack([Results, Temp])
    
    r = pd.DataFrame(Results)
    r.columns = r.iloc[0]
    r.drop(r.index[[0]], inplace=True)
    
    Runs = ['WMShapes1', 'WMShapes2', 'WMFaces1', 'WMFaces2', 'ExtinctionRecall1', 'ExtinctionRecall2', 'ThreatReactivity1', 'ThreatReactivity2']
    SimpsonRuns = r['RunName'].ravel()

    for run in Runs:
        OutName = SubjectDir + run[:-1].lower() + '/' + run + '_Simpson.txt'
        if run in SimpsonRuns:
            OutputFile = open(OutName, "w")
            writer = csv.writer(OutputFile, delimiter=' ')
            row = r.loc[(r['RunName'] == str(run))]
            writer.writerow([row['SimpsonOnset'].iloc[0], row['SimpsonDuration'].iloc[0], str(1)])
            OutputFile.close()
        else:
            OutName = str(OutName).replace('.txt','-EMPTY.txt')
            Touch(OutName)
            

data = pd.read_csv(InFile, sep = ',', low_memory = False)
FindSimpsons(data)