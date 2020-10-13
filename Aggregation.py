# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 16:35:38 2020

@author: Robert Feussner
"""
# %% run all - spyder configuration
import os
#os.chdir('/u/home/feussner/Project')

import pandas as pd
from global_variables import DATABASE
from datetime import datetime, timedelta
import sqlite3


TESTING = False    

def main():
    fromDate=(2020,9,23)
    toDate=(2020,9,29)
    dateRange(fromDate, toDate)
    """
    today1 = datetime.now().strftime('%Y%m%d_%V')
    today2 = datetime.now().strftime('%Y_%V')
    mainWithDay(today1, today2)
    """
    
def dateRange(fromDate, toDate):
    fromDate = datetime(*fromDate)
    toDate = datetime(*toDate)
    days = [fromDate + timedelta(days=x) for x in range((toDate-fromDate).days + 1)]
    for day in days:
        day1 = day.strftime('%Y%m%d_%V')
        day2 = day.strftime('%Y_%V')
        mainWithDay(day1,day2)
        
    
    
def mainWithDay(today1, today2):
    print(today1)
    start = datetime.now()
    
    rankings = ['ALEXA','CISCO','TRANCO','MAJESTIC']
    ipVersions = ['IPV4','IPV6']
    tlsVersions = ['TLS12','TLS13']
    tlsVersionDict = {'TLS12':2,'TLS13':3}
    ipVersionDict = {'IPV4':4,'IPV6':6}
    newTimeNames = {'TLS13_NAMELOOKUP_TIME':'NAMELOOKUP_TIME','TLS13_CONNECT_TIME':'CONNECT_TIME',
                    'TLS13_APPCONNECT_TIME':'APPCONNECT_TIME','TLS13_TOTAL_TIME':'TOTAL_TIME',
                    'TLS12_NAMELOOKUP_TIME':'NAMELOOKUP_TIME','TLS12_CONNECT_TIME':'CONNECT_TIME',
                    'TLS12_APPCONNECT_TIME':'APPCONNECT_TIME','TLS12_TOTAL_TIME':'TOTAL_TIME'}
    
    try:
        con = sqlite3.connect(DATABASE)
        currentPerformance = pd.read_sql('select * from "'+ today1 +'_PERFORMANCE"', con)
    finally:
        con.close()
    
    currentPerformance = currentPerformance.drop(columns=['MEASUREMENT','ABSOLUTE_RANK','RANK_ONLY_TLS','WEBSITE'])
    currentPerformance = currentPerformance.groupby(['RANKING_NAME','IP_VERSION'],as_index=False).mean()
    df12 = currentPerformance.drop(columns=['TLS13_NAMELOOKUP_TIME','TLS13_CONNECT_TIME','TLS13_APPCONNECT_TIME','TLS13_TOTAL_TIME'])
    df13 = currentPerformance.drop(columns=['TLS12_NAMELOOKUP_TIME','TLS12_CONNECT_TIME','TLS12_APPCONNECT_TIME','TLS12_TOTAL_TIME'])
    df12 = df12.rename(columns=newTimeNames)
    df13 = df13.rename(columns=newTimeNames)
    df12['TLS_VERSION'] = 2
    df13['TLS_VERSION'] = 3
    currentPerformance = pd.concat([df12,df13])
    
    try:
        con = sqlite3.connect(DATABASE)
        currentRanking = pd.read_sql('select * from "'+ today1 +'_RANKING"', con)
        currentWeeklyAdoption = pd.read_sql('select * from "' + today2 + '_ADOPTION"', con)
    finally:
        con.close()
    currentAdoption = pd.merge(currentRanking, currentWeeklyAdoption, on='WEBSITE', how='inner')
    del currentRanking
    del currentWeeklyAdoption
    print(datetime.now() - start)
    start = datetime.now()
    adoptionAggregated = pd.DataFrame({'DAY':[],'RANKING_NAME':[],'IP_VERSION':[],'TLS_VERSION':[],'WEBSITES':[],'NO_ERROR':[],'TIMEOUT':[]})
    
    for ranking in rankings:
        for ipVersion in ipVersions:
            for tlsVersion in tlsVersions:
                df = currentAdoption.loc[currentAdoption['RANK_' + ranking].notnull(),:]
                
                numberWebsites = df['WEBSITE'].count()
                
                numberNoError = df.loc[df[ipVersion + '_' + tlsVersion] == 0,'WEBSITE'].count()
                numberTimeout = df.loc[df[ipVersion + '_' + tlsVersion] == 28,'WEBSITE'].count()
                newRow = pd.DataFrame({'DAY':[today1],'RANKING_NAME':[ranking],'IP_VERSION':[ipVersionDict[ipVersion]],'TLS_VERSION':[tlsVersionDict[tlsVersion]],'WEBSITES':[numberWebsites],'NO_ERROR':[numberNoError],'TIMEOUT':[numberTimeout]})
                adoptionAggregated = adoptionAggregated.append(newRow,ignore_index=True)
    #print(adoptionAggregated)
    
    del currentAdoption
    
    aggregated = pd.merge(adoptionAggregated,currentPerformance, on=['RANKING_NAME','IP_VERSION','TLS_VERSION'], how='inner')
    for column in aggregated.columns.tolist():
        if column in ['IP_VERSION','TLS_VERSION','WEBSITES','NO_ERROR','TIMEOUT']:
            aggregated[column] = aggregated[column].astype('int64')
    
    if TESTING:
        aggregated.to_csv('AGGREGATED_'+today1+'.csv', sep=';', index=False)
    else:
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            names = pd.read_sql('select name from "sqlite_master" where type="table"', con)['name'].tolist()
            if 'AGGREGATED' in names:
                cur.execute('delete from "AGGREGATED" where DAY = "' + today1 + '"')
            aggregated.to_sql('AGGREGATED', index=False, con=con, if_exists='append')
        finally:
            con.close()
    print(datetime.now() - start)

if __name__ == "__main__":
    main()
