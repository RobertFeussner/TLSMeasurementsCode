# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 14:38:01 2020

@author: Robert Feussner
"""
# %% run all - spyder configuration
import os
#os.chdir('/u/home/feussner/Project')

import pandas as pd
from global_variables import TEMP, DATA_PATH, DATABASE, deleteTEMP, PROJECT
import subprocess
from datetime import datetime
import sqlite3

def fun(url):
    global outputfile, pids
    command = [PROJECT + 'C_CODE/TLSAdoption', url]
    pids.append(subprocess.Popen(command, stdout=outputfile))
    
def main():
    today = datetime.now().strftime('%Y_%V')
    mainWithDay(today)
    
def mainWithDay(today):
    global outputfile, pids 
    start = datetime.now()
    
    weeklyAdoption = today + '_ADOPTION'
    try:
        con = sqlite3.connect(DATABASE)
        names = pd.read_sql('select name from "sqlite_master" where type="table"', con)
    finally:
        con.close()
        
    if weeklyAdoption in names.values:
        try:
            con = sqlite3.connect(DATABASE)
            dfWeeklyAdoption = pd.read_sql('select WEBSITE from "' + weeklyAdoption + '"', con)
        finally:
            con.close()
        dfCurrentRanking = getCurrentRanking()
        dfWeeklyAdoption['null'] = 0
        
        df = pd.merge(dfCurrentRanking, dfWeeklyAdoption, how='left', on='WEBSITE')
        df = df.loc[df['null'].isnull()]
        df.drop(columns=['null'], inplace=True)
        print(df)
        print('Vorhanden')
    else:
        df = getCurrentRanking()
        print('Nicht Vorhanden')
    laenge = len(df.index)
    df.to_csv(TEMP + 'CurrentRanking.csv', index=False)
    
    if os.path.exists(TEMP + 'CurrentWeeklyAdoption.csv'):
        os.remove(TEMP + 'CurrentWeeklyAdoption.csv')
    outputfile = open(TEMP + 'CurrentWeeklyAdoption.csv', 'w')
    
    counter = 0
    for chunk in pd.read_csv(TEMP + 'CurrentRanking.csv', chunksize=2500):
        print(str(counter) + '/' + str(laenge//2500))
        start1 = datetime.now()
        
        pids=[]
        chunk['WEBSITE'].apply(fun)
        
        for pid in pids:
            pid.wait()
        counter += 1
        
        print(datetime.now() - start1)
        
    outputfile.close()
    
    df = pd.read_csv(TEMP + 'CurrentWeeklyAdoption.csv', sep=';', names=['WEBSITE','IPV4_TLS13','IPV4_TLS12','IPV6_TLS13','IPV6_TLS12'])
    
    try:
        con = sqlite3.connect(DATABASE)
        df.to_sql(weeklyAdoption, index=False, con=con, if_exists='append')
    finally:
        con.close()
    
    print(datetime.now() - start)
    #deleteTEMP()

def getCurrentRanking():
    try:
        con = sqlite3.connect(DATABASE)
        names = pd.read_sql('select name from "sqlite_master" where type="table"', con)['name'].tolist()
        rankings = []
        for name in names:
            if len(name) == len('YYYYMMDD_WW_RANKING') and name.endswith('_RANKING'):
                rankings.append(name)
        name = max(rankings)
        df = pd.read_sql('select website from "'+ name +'"', con)
    finally:
        con.close()
    return df


if __name__ == "__main__":
    main()
