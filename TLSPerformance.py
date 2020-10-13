# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:35:38 2020

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

TESTING = False

def main():
    today = datetime.now().strftime('%Y%m%d_%V')
    mainWithDay(today)
    
def mainWithDay(today):
    currentRankingName = getCurrentRankingName()
    currentWeeklyAdoptionName = getCurrentWeeklyAdoptionName()
    try:
        con = sqlite3.connect(DATABASE)
        currentRanking = pd.read_sql('select * from "'+ currentRankingName +'"', con)
        currentWeeklyAdoptionIPv4 = pd.read_sql('select "WEBSITE", "IPV4_TLS13", "IPV4_TLS12" from "'
                                                + currentWeeklyAdoptionName +'" where "IPV4_TLS13" = 0 and "IPV4_TLS12" = 0', con)
        currentWeeklyAdoptionIPv6 = pd.read_sql('select "WEBSITE", "IPV6_TLS13", "IPV6_TLS12" from "'
                                                + currentWeeklyAdoptionName +'" where "IPV6_TLS13" = 0 and "IPV6_TLS12" = 0', con)
    finally:
        con.close()
    print(len(currentWeeklyAdoptionIPv4.index))
    print(len(currentWeeklyAdoptionIPv6.index))
    
    dfIPv4 = pd.merge(currentRanking, currentWeeklyAdoptionIPv4, on='WEBSITE', how='inner')
    print('Merge 1 done!')
    del currentWeeklyAdoptionIPv4
    
    dfIPv6 = pd.merge(currentRanking, currentWeeklyAdoptionIPv6, on='WEBSITE', how='inner')
    print('Merge 2 done!')
    del currentWeeklyAdoptionIPv6
    
    del currentRanking
    
    names = ['ALEXA','CISCO','TRANCO','MAJESTIC']
        
    howMany = 100
    if TESTING:
        howMany = 10
    
    #WEBSITE SAMPLES
    dfs = []
    for IPversion in [4,6]:
        for name in names:
            ranking = 'RANK_' + name
            if IPversion == 4:
                df = dfIPv4[['WEBSITE', ranking]].dropna().copy()
            else:
                df = dfIPv6[['WEBSITE', ranking]].dropna().copy()
            print(len(df.index))
            df.sort_values(by=ranking, inplace=True)
            
            top = df.iloc[:howMany].copy()
            top['CATEGORY'] = 'TOP'
            m = len(df.index) // 2
            middle = df.iloc[m-(howMany//2):m +(howMany//2)].copy()
            middle['CATEGORY'] = 'MIDDLE'
            bottom = df.iloc[-howMany:].copy()
            bottom['CATEGORY'] = 'BOTTOM'
            df = pd.concat([top,middle,bottom])
            df['RANKING_NAME'] = name
            df['IP_VERSION'] = IPversion
            
            df.reset_index(drop=True, inplace=True)
            df.reset_index(inplace=True)
            df.rename(columns={'index':'RANK_ONLY_TLS',ranking:'ABSOLUTE_RANK'}, inplace=True)
            
            df = df[['RANKING_NAME','WEBSITE','IP_VERSION','CATEGORY','RANK_ONLY_TLS','ABSOLUTE_RANK']]
            
            dfs.append(df)
            
    
    rankingSample = pd.concat(dfs)
    rankingSample['ABSOLUTE_RANK'] = rankingSample['ABSOLUTE_RANK'].astype('int64')
    if TESTING:
        rankingSample.to_csv('rankingSampleTest.csv', sep=';', index=False)
    
    #rankingSample is almost the daily list for performances.
    #rankingSample to sql as YYYYMMDD_WW_WEBSITE_SAMPLES
    
    if os.path.exists(TEMP + 'Performance.csv'):
        os.remove(TEMP + 'Performance.csv')
    outputfilePerformance = open(TEMP + 'Performance.csv', 'w')
    
    urlsPerformanceIPv4 = rankingSample.loc[rankingSample['IP_VERSION'] == 4, 'WEBSITE'].drop_duplicates()
    urlsPerformanceIPv6 = rankingSample.loc[rankingSample['IP_VERSION'] == 6, 'WEBSITE'].drop_duplicates()
    
    start = datetime.now()
    for url in urlsPerformanceIPv4.values:
        command = [PROJECT + 'C_CODE/TLSPerformance',url,'4']
        subprocess.run(command, stdout=outputfilePerformance)
    print(datetime.now() - start)
    
    start = datetime.now()
    for url in urlsPerformanceIPv6.values:
        command = [PROJECT + 'C_CODE/TLSPerformance',url,'6']
        subprocess.run(command, stdout=outputfilePerformance)
    outputfilePerformance.close()
    print(datetime.now() - start)
    
    if os.path.exists(TEMP + 'Cipher.csv'):
        os.remove(TEMP + 'Cipher.csv')
    outputfileCipher = open(TEMP + 'Cipher.csv', 'w')
    
    urlsCipherIPv4 = rankingSample.loc[((rankingSample['IP_VERSION'] == 4) & (rankingSample['CATEGORY'] == 'TOP')),'WEBSITE'].drop_duplicates()
    urlsCipherIPv6 = rankingSample.loc[((rankingSample['IP_VERSION'] == 6) & (rankingSample['CATEGORY'] == 'TOP')),'WEBSITE'].drop_duplicates()
    
    start = datetime.now()
    for url in urlsCipherIPv4.values:
        command = [PROJECT + 'C_CODE/TLSCipher',url,'4']
        subprocess.run(command, stdout=outputfileCipher)
    print(datetime.now() - start)
    
    start = datetime.now()
    for url in urlsCipherIPv6.values:
        command = [PROJECT + 'C_CODE/TLSCipher',url,'6']
        subprocess.run(command, stdout=outputfileCipher)
    outputfileCipher.close()
    print(datetime.now() - start)
    
    performance = pd.read_csv(TEMP + 'Performance.csv', sep=';', names=['WEBSITE','IP_VERSION','MEASUREMENT',
                                                                        'TLS12_NAMELOOKUP_TIME','TLS12_CONNECT_TIME',
                                                                        'TLS12_APPCONNECT_TIME','TLS12_TOTAL_TIME',
                                                                        'TLS13_NAMELOOKUP_TIME','TLS13_CONNECT_TIME',
                                                                        'TLS13_APPCONNECT_TIME','TLS13_TOTAL_TIME'])
    cipher = pd.read_csv(TEMP + 'Cipher.csv', sep=';', names=['WEBSITE','IP_VERSION','CIPHER','ERROR','ERROR_STRING',
                                                              'NAMELOOKUP_TIME','CONNECT_TIME','APPCONNECT_TIME','TOTAL_TIME'])
    performanceWithRanking = pd.merge(rankingSample, performance, on=['WEBSITE','IP_VERSION'], how='inner')
    
    cipherWithRanking = pd.merge(rankingSample, cipher, on=['WEBSITE','IP_VERSION'], how='inner')
    cipherWithRanking.drop(columns=['CATEGORY'], inplace=True)
    
    if TESTING:
        performanceWithRanking.to_csv('performanceWithRankingTest.csv', sep=';', index=False)
        cipherWithRanking.to_csv('cipherWithRankingTest.csv', sep=';', index=False)
    else:
        try:
            con = sqlite3.connect(DATABASE)
            performanceWithRanking.to_sql(today + '_PERFORMANCE', index=False, con=con, if_exists='replace')
            cipherWithRanking.to_sql(today + '_CIPHER', index=False, con=con, if_exists='replace')
        finally:
            con.close()
    
def getCurrentRankingName():
    try:
        con = sqlite3.connect(DATABASE)
        names = pd.read_sql('select name from "sqlite_master" where type="table"', con)['name'].tolist()
        rankings = []
        for name in names:
            if len(name) == len('YYYYMMDD_WW_RANKING') and name.endswith('_RANKING'):
                rankings.append(name)
        name = max(rankings)
    finally:
        con.close()
    return name

def getCurrentWeeklyAdoptionName():
    try:
        con = sqlite3.connect(DATABASE)
        names = pd.read_sql('select name from "sqlite_master" where type="table"', con)['name'].tolist()
        rankings = []
        for name in names:
            if len(name) == len('YYYY_WW_ADOPTION') and name.endswith('_ADOPTION'):
                rankings.append(name)
        name = max(rankings)
    finally:
        con.close()
    return name

if __name__ == "__main__":
    main()