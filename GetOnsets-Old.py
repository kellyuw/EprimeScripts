##GetOnsets.py
## 1. Checks for Simpsons characters in each task-specific behavioral file.
## 2. Checks if corresponding image file exists in the subject's directory.
## 3. Uses functions defined in cells below to parse behavioral data for each task.

## Python dependencies
import pandas as pd
import numpy as np
import argparse
import csv
import os
import re

#Pull the data in based on a parameter entered at the command line
parser = argparse.ArgumentParser()
parser.add_argument('--subject', '-s', required=True, help='Name of subject to be processed')
parser.add_argument('--task', '-t', required=True, help='Name of task to be processed')
args = parser.parse_args()
subject = args.subject
task = args.task

SubjectDir = '/mnt/stressdevlab/dep_threat_pipeline/' + str(subject) + '/'

## Utility functions

# Emulate unix touch (create dummy text file to mark progress in getting onsets)
def Touch(path):
    with open(path, 'a'):
        os.utime(path, None)


## Check if image file exists and return helpful information about the run
def GetRunData (Run):
    Task = filter(lambda x: x.isalpha(), Run)
    RunNum = str(re.findall('\d+', str(Run)))[2]
    FullTaskDir = str(SubjectDir) + Task.lower() + '/' + Run
    runData = {'RunNum': str(RunNum), 
               'Run': str(Run), 
               'RunName': Task + 'Run' + RunNum, 
               'Task': Task,
               'FullTaskDir': str(FullTaskDir),
               'ImageFileExists': str(os.path.exists(str(FullTaskDir + '.nii.gz')))}
    return runData


# # Get behavioral data for working memory tasks (WMShapes and WMFaces)
# 
# ## WMFaces
# |Parameter | Rows | Column / value
# |--- | :---: | --- |
# | Condition 1 | ProcedureTrial = calm | 
# | Condition 2 | ProcedureTrial = angry |
# | OnsetTime | First subtrial in each block (Subtrial = 1) | prepOnsetTime
# | OffsetTime | Last subtrial in each block (Subtrial = 5) | probeOnsetTime + 1500ms
# | TriggerAdj | Rows from Onset and Offset subsets | TriggerWAITRTTimeBlock
# | Duration |  | AdjOffset - AdjOnset
# 
# 
# ## WMShapes
# |Parameter | Rows | Column / value
# |--- | :---: | --- |
# | Condition 1 | ProcedureTrial = low | 
# | Condition 2 | ProcedureTrial = high |
# | OnsetTime | First subtrial in each block (Subtrial = 1) | WMSprepOnsetTime
# | OffsetTime | Last subtrial in each block (Subtrial = 5) | WMSprobeOnsetTime + 1500ms
# | TriggerAdj | Rows from Onset and Offset subsets | TriggerWAITRTTimeBlock
# | Duration |  | AdjOffset - AdjOnset

# In[9]:

def ParseWM(data, runData):

    #Conditions are different across WM tasks.Account for that here.
    #Also adjust column names(WMSprepOnsetTime for WMShapes and prepOnsetTime for WMFaces)
	if ('Faces' in runData['RunName']):
	    Condition1 = 'calm'
	    Condition2 = 'angry'
	elif('Shapes' in runData['RunName']):
	    Condition1 = 'low'
	    Condition2 = 'high'
	else :
	    print "Error, can not determine type of WM run."

	if (runData['RunNum'] == '2'):
	    Condition1 += '2'
	    Condition2 += '2'

	#Create dict to store logical rules about which OnsetTime column should be used
	OffsetStrs = {
	    'low': 'WMSprepOnsetTime',
	    'high': 'WMSprepOnsetTime',
	    'low2': 'WMSprepOnsetTime2',
	    'high2': 'WMSprepOnsetTime2',
	    'ITI1': 'WMSfixationOnsetTime',
	    'WMSITI2': 'WMSfixation2OnsetTime',
	    'WMSimpsonsITIBlock': 'SimpsonsITI4aOnsetTime',
	    'WMFSimpsonsITIBlock': 'SimpsonsITI5aOnsetTime',
	    'angry': 'prepOnsetTime',
	    'calm': 'prepOnsetTime',
	    'angry2': 'prepOnsetTime2',
	    'calm2': 'prepOnsetTime2',
	    'ITI': 'fixationOnsetTime',
	    'ITI2': 'fixation2OnsetTime'
	}

	OnsetStrs = ['WMSprepOnsetTime', 'WMSprepOnsetTime2', 'prepOnsetTime', 'prepOnsetTime2']


	#Here we use for loop because parsing procedure should be identical across conditions
	for Condition in [str(Condition1), str(Condition2)]:
		NoIntCondition = filter(lambda x: x.isalpha(), str(Condition))

		off = data.loc[(data['ProcedureBlock'] == runData['RunName'])].loc[:,OffsetStrs.values()]
		s = off.T.groupby(level=0).first().T
		s['OFFSETS'] = s.sum(axis = 1)
		t = pd.merge(s[['OFFSETS']], data, left_index = True, right_index = True)
		on = data.loc[(data['ProcedureBlock'] == runData['RunName'])].loc[:,OnsetStrs]
		on['ONSETS'] = on.sum(axis = 1)
		d = pd.merge(on[['ONSETS']], t, left_index = True, right_index = True)
		d = d.reset_index(drop=True)

		F = d[(d['SubTrial'] == 1)]
		L = d.shift(-4)[(d['SubTrial'] == 1)]
		N = d.shift(-5)[(d['SubTrial'] == 1)]

		N['DURATION'] = (N['OFFSETS'] - F['ONSETS']) / float(1000)

		#print N.DURATION
		        
		F['ADJONSETS'] = (F['ONSETS'] - F['TriggerWAITRTTimeBlock']) / float(1000)
		#print F['ADJONSETS']

		BlockOnsets = F.loc[(d['ProcedureBlock'] == runData['RunName']) & (d['ProcedureTrial'] == Condition)]['ADJONSETS']
		BlockDurations = N.loc[(d['ProcedureBlock'] == runData['RunName']) & (d['ProcedureTrial'] == Condition)]['DURATION']

		print runData['RunName']
		print BlockOnsets
		print BlockDurations
		WMOutput(NoIntCondition, runData, BlockOnsets, BlockDurations)

def WMOutput (Condition, runData, BlockOnsets, BlockDurations):
    OutName = str(runData['FullTaskDir'] + '_' + Condition + '.txt')
    print OutName
    if (len(BlockOnsets) > 0):
        OutputFile = open(OutName, "w")
        writer = csv.writer(OutputFile, delimiter=' ')
        for row in range(0,len(BlockOnsets)):
            print str(BlockOnsets.iloc[row]) + '\t' + str(BlockDurations.iloc[row]) + '\t' + str(1)
            writer.writerow([str(BlockOnsets.iloc[row]), str(BlockDurations.iloc[row]), str(1)])
        OutputFile.close()
    else:
        OutName = str(os.path.dirname(OutName) + '/' + os.path.basename(OutName).split('.txt')[0] + '-EMPTY.txt')
        Touch(OutName)
    print '\n'
    

#for runname in ['WMShapes1','WMShapes2','WMFaces1','WMFaces2']:
#    runData = GetRunData(runname)
#    data = pd.read_csv(str(SubjectDir) + 'behavior/' + runData['Task'] + '-eprime.csv')
#    ParseWM(data, runData)
#    Touch(str(runData['FullTaskDir'] + 'Onsets.txt'))


# # Get behavioral data for ThreatReactivity task
# 
# |Parameter | Row criteria | Column criteria
# |--- | :---: | --- |
# | Condition 1 | Emotion = 'C' | 
# | Condition 2 | Emotion = 'S' |
# | Condition 3 | Emotion = 'F' |
# | OnsetTime | First subtrial in each block (Subtrial = 1) | ReactivityITIOnsetTime
# | OffsetTime | Last subtrial in each block (Subtrial = 36) | ReactivityITIOnsetTime + 500 ms
# | TriggerAdj | Rows from Onset and Offset subsets | TriggerWAITRTTimeBlock
# | Duration |  | OnsetTime - OffsetTime


def ParseThreatReactivity (data, runData):
    
    #The column name needs to be adjusted when run number = 2
    ReactivityITIStr = 'ReactivityITIOnsetTime'
    if (runData['RunNum'] == '2'):
        ReactivityITIStr += '2'

    for Condition in ['C','S','F']:

        FirstSubtrials = data[(data['ProcedureBlock'] == runData['RunName']) & (data['Emotion'] == Condition) & (data['SubTrial'] == 1)]
        LastSubtrials = data[(data['ProcedureBlock'] == runData['RunName']) & (data['Emotion'] == Condition) & (data['SubTrial'] == 36)]
  
        #Adjust block onsets and offsets by TriggerWAITRTTimeBlock
        FirstSubtrialsOn = FirstSubtrials.loc[:,(ReactivityITIStr)] - FirstSubtrials.loc[:,('TriggerWAITRTTimeBlock')]
        LastSubtrialsOff = LastSubtrials.loc[:,(ReactivityITIStr)] - LastSubtrials.loc[:,('TriggerWAITRTTimeBlock')]

        #Get onsets and offsets in seconds
        BlockOnsetsInSec = FirstSubtrialsOn / float(1000)
        BlockOffsetsInSec = (LastSubtrialsOff + float(500))/ float(1000)
        BlockDurationsInSec =  BlockOffsetsInSec.values -  BlockOnsetsInSec.values
        
        TROutput(Condition, runData, BlockOnsetsInSec, BlockDurationsInSec)
        

def TROutput (Condition, runData, BlockOnsets, BlockDurations):
    OutName = str(runData['FullTaskDir'] + '_' + Condition + '.txt')
    print str(OutName)
    if (not BlockOnsets.empty):
        OutputFile = open(OutName, "w")
        writer = csv.writer(OutputFile, delimiter=' ')
        for row in range(0,len(BlockOnsets)):
            print str(BlockOnsets.iloc[row]) + '\t' + str(BlockDurations[row]) + '\t' + str(1)
            writer.writerow([str(BlockOnsets.iloc[row]), str(BlockDurations[row]), str(1)])
        OutputFile.close()
    else:
        OutName = str(os.path.dirname(OutName) + '/' + os.path.basename(OutName).split('.txt')[0] + '-EMPTY.txt')
        Touch(OutName)
    print '\n'
    
    
#for runname in ['ThreatReactivity1','ThreatReactivity2']:
#    runData = GetRunData(runname)
#    data = pd.read_csv(str(SubjectDir) + 'behavior/' + runData['Task'] + '-eprime.csv')
#    ParseThreatReactivity(data, runData)
#    Touch(str(runData['FullTaskDir'] + 'Onsets.txt'))


# # Get behavioral data for Go-NoGo task
# 
# |Parameter | Row criteria | Column criteria
# |--- | :---: | --- |
# | Condition 1 | ProcedureSubTrial = 'TwoGoProc' | 
# | Condition 2 | ProcedureSubTrial = 'ThreeGoProc' |
# | Condition 3 | ProcedureSubTrial = 'FourGoProc' |
# | Sub-Condition A | ConditionLogLevel5 = 'Go' |
# | Sub-Condition B | ConditionLogLevel5 = 'NoGo' |
# | RespType A | Incorrect (GNGACC = 0) |
# | RespType B | Correct (GNGACC = 1) | 
# | OnsetTime | Subtrials that match each Condition, Sub-Condition, and RespType (as defined above) | GNGCueOnsetTime
# | Duration | Subtrials that match each Condition, Sub-Condition, and RespType (as defined above) | GNGCueOnsetToOnsetTime
# | TriggerAdj | Rows from each group of trials (as defined above) | TriggerWAITRTTimeTrial
 

def ParseGoNoGo (data, runData):
    
    for NumItems in ['Two','Three','Four']:
        GNGType = NumItems + 'GoProc'

        #Subtrials = data[(data['ProcedureBlock'] == runData['RunName'])]
        GNG = data[(data['ProcedureBlock'] == runData['RunName']) & (data['ProcedureSubTrial'] == GNGType)]
        
        for Condition in ['Go','NoGo']:
            for Accuracy in [0,1]:
                
                RespType = 'Correct'
                if (str(Accuracy) == '0'):
                    RespType = 'In' + RespType.lower()

                #print 'RespType: ' + str(RespType)
                Trials = GNG[(GNG['ConditionLogLevel5'] == str(Condition)) & (GNG['GNGACC'] == int(Accuracy))]
                TriggerOnsetTimes = Trials.TriggerWAITRTTimeTrial

                TrialOnsets = (Trials['GNGCueOnsetTime'] - TriggerOnsetTimes) / float(1000)
                TrialDurations = Trials['GNGCueOnsetToOnsetTime'] / float(1000)
                
                GNGOutput(str(NumItems + '_' + Condition + '_' + RespType), runData, TrialOnsets, TrialDurations)
        
    #Combine files for inaccurate go trials (across GNGTypes)
    GNG = data[(data['ProcedureBlock'] == runData['RunName']) & (data['ConditionLogLevel5'] == 'Go') & (data['GNGACC'] == 0)]
    TrialOnsets = (GNG['GNGCueOnsetTime'] - GNG['TriggerWAITRTTimeTrial']) / float(1000)
    TrialDurations = GNG['GNGCueOnsetToOnsetTime'] / float(1000)
    GNGOutput('ALL_Go_Incorrect', runData, TrialOnsets, TrialDurations)

def GNGOutput (Condition, runData, BlockOnsets, BlockDurations):
    OutName = str(runData['FullTaskDir'] + '_' + Condition + '.txt')
    print str(OutName)
    if (not BlockOnsets.empty):
        OutputFile = open(OutName, "w")
        writer = csv.writer(OutputFile, delimiter=' ')
        for row in range(0,len(BlockOnsets)):
            print str(BlockOnsets.iloc[row]) + '\t' + str(BlockDurations.iloc[row]) + '\t' + str(1)
            writer.writerow([str(BlockOnsets.iloc[row]), str(BlockDurations.iloc[row]), str(1)])
        OutputFile.close()
    else:
        OutName = str(os.path.dirname(OutName) + '/' + os.path.basename(OutName).split('.txt')[0] + '-EMPTY.txt')
        Touch(OutName)
    print '\n'

    if (Condition == 'ALL_Go_Incorrect'):
        a = []
        for l in ['Two','Three','Four']:
            OutName = str(runData['FullTaskDir'] + '_' + l + '_' + 'Go_Incorrect.txt')
            print OutName   
            if (os.path.exists(OutName)): 
                with open(OutName, 'r') as f:
                    for line in f.readlines():
                        a.append(line.strip())
	    OutName = str(runData['FullTaskDir'] + '_' + Condition + '.txt')
	    OutputFile = open(OutName, "w")
	    writer = csv.writer(OutputFile)
	    for i in sorted(a):
	        print i
	        writer.writerow([str(i)])
	    OutputFile.close()
	    print '\n'

#for runname in ['GNG1','GNG2','GNG3']:
#    runData = GetRunData(runname)
#    data = pd.read_csv(str(SubjectDir) + 'behavior/' + runData['Task'] + '-eprime.csv')
#    ParseGoNoGo(data, runData)
#    Touch(str(runData['FullTaskDir'] + 'Onsets.txt'))


# # Get behavioral data for ExtinctionRecall task
# 
# |Parameter | Row criteria | Column criteria
# |--- | :---: | --- |
# | Condition 1 | StimulusTrial = 'CSPlus_Threat' | 
# | Condition 2 | StimulusTrial = 'CSMinus_Threat' |
# | Sub-Condition A | CSImageRecall |
# | Sub-Condition B | ThreatResp |
# | RespType A | NoResponse (RT = 0) |
# | RespType B | Response (RT > 0) | 
# | OnsetTime | Subtrials that match each Condition, Sub-Condition, and RespType (as defined above) | CSImageRecallOnsetTime (or ThreatRespOnsetTime)
# | Duration | Subtrials that match each Condition, Sub-Condition, and RespType (as defined above) | CSImageRecallOnsetToOnsetTime (or ThreatRespOnsetToOnsetTime)
# | TriggerAdj | Rows from each group of trials (as defined above) | TriggerWAITRTTimeBlock


def ParseExtRecall (data, runData):
    
    #Set string names to match column names in behavioral file
    CSImageStr = 'CSImageRecall'
    ThreatRespStr = 'ThreatResp'
    CSImageStrOnsetTime = str(CSImageStr) + 'OnsetTime'
    CSImageStrOnsetToOnsetTime = str(CSImageStr) + 'OnsetToOnsetTime'
    ThreatRespStrOnsetTime = str(ThreatRespStr) + 'OnsetTime'
    ThreatRespStrOnsetToOnsetTime = str(ThreatRespStr) + 'OnsetToOnsetTime'
    CSImageStrRT = str(CSImageStr) + 'RT'
    ThreatRespStrRT = str(ThreatRespStr) + 'RT'

    #The column name needs to be adjusted when run number = 2
    if (runData['RunNum'] == '2'):
        CSImageStr += '2'
        ThreatRespStr += '2'
        CSImageStrOnsetTime += '2'
        CSImageStrOnsetToOnsetTime += '2'
        ThreatRespStrOnsetTime += '2'
        ThreatRespStrOnsetToOnsetTime += '2'
        CSImageStrRT += '2'
        ThreatRespStrRT += '2'

    #There are two condition in ExtinctionRecall (CSPlus_Threat and CSMinus_Threat)
    for TrialType in ['CSPlus','CSMinus']:
        Condition = TrialType + '_Threat'

        #Get TriggerOnsetTimes for each run and condition
        ImageRecallTrials = data[(data['ProcedureBlock'] == runData['RunName']) & (data['StimulusTrial'] == Condition)]
        TriggerOnsetTimes = ImageRecallTrials.TriggerWAITRTTimeBlock

        #Get ImageOnsets by selecting CSImageRecallOnsetTime and subtracting TriggerOnsetTimes for each run and conditon
        ImageOnsets = (ImageRecallTrials[CSImageStrOnsetTime] - TriggerOnsetTimes) / float(1000)

        #Get ImageDurations from same subset at above (but use CSImageRecallOnsetToOnsetTime column instead)
        ImageDurations = ImageRecallTrials[CSImageStrOnsetToOnsetTime] / float(1000)
           
        #Get ResponseOnsetTime from same subset as above (but use ThreatRespOnsetTime)
        ResponseOnsets = (ImageRecallTrials[ThreatRespStrOnsetTime] - TriggerOnsetTimes) / float(1000)

        #Get ResponseDurations from same subset at above (but use ThreatRespOnsetToOnsetTime)
        ResponseDurations = ImageRecallTrials[ThreatRespStrOnsetToOnsetTime] / float(1000)

        #CombinedDurations
        CombinedDurations = ResponseDurations + ImageDurations
  
        #Get response times from same subset as above (but use ThreatRespRT)
        ResponseTimes = ImageRecallTrials[ThreatRespStrRT] / float(1000)

        #Print output for all trials
        ExtRecallOutput('Image','C', runData, TrialType, ImageOnsets, ImageDurations)
        ExtRecallOutput('Response','C', runData, TrialType, ResponseOnsets, ResponseDurations)
        ExtRecallOutput('ImageResponse','C', runData, TrialType, ImageOnsets, CombinedDurations)

        
        #Now, get onsets by response type:
        
        #Starting with Non-Responses (RT == 0)
        #NRImageOnsets = ImageOnsets[(data[CSImageStrRT] == 0)]
        #NRImageDurations = ImageDurations[(data[CSImageStrRT] == 0)]
        #NRResponseOnsets = ResponseOnsets[(data[ThreatRespStrRT] == 0)]
        #NRResponseDurations = ResponseDurations[(data[ThreatRespStrRT] == 0)]
        #NRCombinedDurations = CombinedDurations[(data[CSImageStrRT] == 0) | (data[ThreatRespStrRT] == 0)]

        #Print output for Non-Responses
        #ExtRecallOutput('Image','NR', runData, TrialType, NRImageOnsets, NRImageDurations)
        #ExtRecallOutput('Response','NR', runData, TrialType, NRResponseOnsets, NRResponseDurations)
        #ExtRecallOutput('ImageResponse','NR', runData, TrialType, NRImageOnsets, NRCombinedDurations)

        #Now, we move on to the responses (RT > 0)
        #RImageOnsets = ImageOnsets[(data[CSImageStrRT] > 0)]
        #RImageDurations = ImageDurations[(data[CSImageStrRT] > 0)]
        #RResponseOnsets = ResponseOnsets[(data[ThreatRespStrRT] > 0)]
        #RResponseDurations = ResponseDurations[(data[ThreatRespStrRT] > 0)]
        #RCombinedDurations = CombinedDurations[(data[CSImageStrRT] > 0) | (data[ThreatRespStrRT] > 0)]
   
        #Print output for Responses now
        #ExtRecallOutput('Image','R', runData, TrialType, RImageOnsets, RImageDurations)
        #ExtRecallOutput('Response','R', runData, TrialType, RResponseOnsets, RResponseDurations)
        #ExtRecallOutput('ImageResponse','R', runData, TrialType, RImageOnsets, RCombinedDurations)

def ExtRecallOutput(OutFileType, OutRespType, runData, TrialType, dataA, dataB):
    if (not dataA.empty):
        if (OutRespType == 'C'):
            OutName = str(runData['FullTaskDir'] + '_' + TrialType + '_' + OutFileType + '.txt')
            OutputFile = open(str(OutName), "w")
            writer = csv.writer(OutputFile, delimiter=' ')
            for row in range(0,len(dataA)):
                print str(dataA.values[row]) + '\t' + str(dataB.values[row]) + '\t' + str(1)
                writer.writerow([str(dataA.values[row]), str(dataB.values[row]), str(1)])
        else:
            OutName = str(runData['FullTaskDir'] + '_' + TrialType + '_' + OutFileType + '_' + OutRespType + '.txt')
            OutputFile = open(str(OutName), "w")
            writer = csv.writer(OutputFile, delimiter=' ')
            for row in range(0,len(dataA)):
                print str(dataA.values[row]) + '\t' + str(dataB.values[row]) + '\t' + str(1)
                writer.writerow([str(dataA[row]), str(dataB[row]), str(1)])
    else:
        OutName = str(os.path.dirname(OutName) + '/' + os.path.basename(OutName).split('.txt')[0] + '-EMPTY.txt')
        Touch(OutName)
    print '\n'

        
#for runname in ['ExtinctionRecall1','ExtinctionRecall2']:
#    runData = GetRunData(runname)
#    data = pd.read_csv(str(SubjectDir) + 'behavior/' + runData['Task'] + '-eprime.csv')
#    ParseExtRecall(data, runData)
#    Touch(str(runData['FullTaskDir'] + 'Onsets.txt'))

runname = os.path.basename(task)
runData = GetRunData(runname)
data = pd.read_csv(str(SubjectDir) + 'behavior/' + runData['Task'] + '-eprime.csv')

print 'Getting ' + runname + ' onsets for subject # ' + subject
if (runData['Task'] == 'WMShapes') or (runData['Task'] == 'WMFaces'):
	data = pd.read_csv(str(SubjectDir) + 'behavior/' + str(subject) + '_clean_eprime.csv')
	ParseWM(data, runData)
elif (runData['Task'] == 'GNG'):
    ParseGoNoGo(data, runData)
elif (runData['Task'] == 'ThreatReactivity'):
    ParseThreatReactivity(data, runData)
elif (runData['Task'] == 'ExtinctionRecall'):
    ParseExtRecall(data, runData)
else:
    print "Error! Can not recognize task."