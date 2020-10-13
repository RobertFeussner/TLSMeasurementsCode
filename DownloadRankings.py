# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 15:38:21 2020

@author: Robert Feussner
"""
# %% run all - spyder configuration
import os
#os.chdir('/u/home/feussner/Project')

import pandas as pd
from global_variables import TEMP, DATA_PATH, DATABASE
from datetime import datetime

import sqlite3

def downloadWithRepeat(url, names,tests=5, usecols=None):
    counter = 0
    done = False
    while counter < tests:
        try:
            if usecols == None:
                df = pd.read_csv(url, names=names)
            else:
                df = pd.read_csv(url, usecols=usecols)
        except:
            print(str(counter) + ' Try not successful. Repeating...')
            counter += 1
        else:
            done = True
            break
    if not done:
        raise NameError('Could not download ranking properly. No data for ' + datetime.now().strftime('%Y%m%d_%V') + 'available.')
    return df

def main():
    today = datetime.now().strftime('%Y%m%d_%V')
    mainWithDay(today)
    
def mainWithDay(today):
    start = datetime.now()
    urlAlexa = 'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip'
    urlCisco = 'http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip'
    urlTranco = 'https://tranco-list.eu/top-1m.csv.zip'
    urlMajestic = 'http://downloads.majestic.com/majestic_million.csv'
    
    dfAlexa = downloadWithRepeat(urlAlexa, ['RANK_ALEXA','WEBSITE'])
    dfCisco = downloadWithRepeat(urlCisco, ['RANK_CISCO','WEBSITE'])
    dfTranco= downloadWithRepeat(urlTranco, ['RANK_TRANCO','WEBSITE'])
    dfMajestic=downloadWithRepeat(urlMajestic,None,  usecols=['GlobalRank','Domain'])
    
    dfMajestic.rename(columns={'GlobalRank':'RANK_MAJESTIC','Domain':'WEBSITE'}, inplace=True)
    
    df = pd.merge(dfAlexa, dfCisco, how='outer', on='WEBSITE')
    
    df = pd.merge(df, dfTranco, how='outer', on='WEBSITE')
    
    df = pd.merge(df, dfMajestic, how='outer', on='WEBSITE')
    
    df=df[['WEBSITE', 'RANK_ALEXA','RANK_CISCO','RANK_TRANCO','RANK_MAJESTIC']]
    print(df)
    
    try:
        con = sqlite3.connect(DATABASE)
        df.to_sql(today + '_RANKING', index=False, con=con, if_exists='replace')
    finally:
        con.close()
    print(datetime.now() - start)

if __name__ == "__main__":
    main()