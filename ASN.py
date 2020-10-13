# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 10:11:38 2020

@author: Robert Feussner
"""
# %% run all - spyder configuration
#import os
#os.chdir('/u/home/feussner/Project')

import pandas as pd
from global_variables import DATABASE
from datetime import datetime, timedelta
import sqlite3

import warnings
import socket
import ssl
import urllib
import urllib.request
import json

TESTING = False

def main():
    today = datetime.now().strftime('%Y%m%d_%V')
    mainWithDay(today)
    """
    fromDate=(2020,8,31)
    toDate=(2020,8,31)
    dateRange(fromDate, toDate)
    """
    
def dateRange(fromDate, toDate):
    fromDate = datetime(*fromDate)
    toDate = datetime(*toDate)
    days = [fromDate + timedelta(days=x) for x in range((toDate-fromDate).days + 1)]
    for day in days:
        day = day.strftime('%Y%m%d_%V')
        mainWithDay(day)

def mainWithDay(today):
    start = datetime.now()
    try:
        con = sqlite3.connect(DATABASE)
        performance = pd.read_sql('select * from "'+ today + '_PERFORMANCE'  +'"', con)
        cipher = pd.read_sql('select * from "'+ today + '_CIPHER'  +'"', con)
    finally:
        con.close()
    df1 = performance.copy()
    df2 = cipher.copy()
    df1 = df1[['WEBSITE','IP_VERSION']]
    df2 = df2[['WEBSITE','IP_VERSION']]
    df = pd.concat([df1,df2])
    del df1, df2
    asnInformation = []
    for IPVersion in [4,6]:
        urls = df.loc[df['IP_VERSION'] == IPVersion, ['WEBSITE']].drop_duplicates()
        results = []
        
        for i in range(0,len(urls)-10,10):
            print(str(IPVersion) + ': ' + str(i)+' von '+ str(len(urls)), flush=True)
            result = pd.DataFrame({'WEBSITE':[],'IP':[],'ASN':[],'ASN_HOLDER':[]})
            urlsPart = urls.iloc[i : i+10]
            result[['WEBSITE','IP','ASN','ASN_HOLDER']] = urlsPart.apply(lambda x : getIPandASN(IPVersion, x['WEBSITE']) , axis='columns', result_type='expand')
            results.append(result)
            if TESTING:
                print(result)
                break
        
        result=pd.concat(results)
        
        result['IP_VERSION'] = IPVersion
        asnInformation.append(result)
        if TESTING:
            print(result)
            break
    asnInformation = pd.concat(asnInformation)
    cipherWithASN = pd.merge(asnInformation, cipher, on=['WEBSITE','IP_VERSION'], how='inner')
    performanceWithASN = pd.merge(asnInformation, performance, on=['WEBSITE','IP_VERSION'], how='inner')
    print(datetime.now()-start)
    if TESTING:
        cipherWithASN.to_csv('cipherWithASNTest.csv', sep=';', index=False)
        performanceWithASN.to_csv('performanceWithASNTest.csv', sep=';', index=False)
    else:
        try:
            con = sqlite3.connect(DATABASE)
            cipherWithASN.to_sql(today + '_CIPHER_ASN', index=False, con=con, if_exists='replace')
            performanceWithASN.to_sql(today + '_PERFORMANCE_ASN', index=False, con=con, if_exists='replace')
            
            """
            #Alternatively:
            #Saves data less redundantly, but also less intuitevely:
            cipherWithASN.to_sql(today + '_CIPHER', index=False, con=con, if_exists='replace')
            performanceWithASN.to_sql(today + '_PERFORMANCE', index=False, con=con, if_exists='replace')
            """
            
        finally:
            con.close()
    
def getIPandASN(IPVersion, url):
    try:
        #Family and IPv4 to test!
        if IPVersion == 4:
            #ip = socket.gethostbyname(url)
            ip = socket.getaddrinfo(url, None, family = socket.AF_INET)[0][4][0]
        else:
            ip = socket.getaddrinfo(url, None, family = socket.AF_INET6)[0][4][0]
        asn, asnHolder = getAsn(ip)
    except Exception as e:
        warnings.warn("Could not gather data for " + url +"\nError:" + str(e))
        return url, None,None,None
    return url, ip, asn, asnHolder

def getAsn(ip):
    jsonUrl =  "https://stat.ripe.net/data/prefix-overview/data.json?max_related=50&resource=" + ip
    req = urllib.request.Request(jsonUrl, headers= {"X-Mashape-Key":"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"})
    context = ssl.SSLContext()
    response = urllib.request.urlopen(req, context=context)
    data = response.read()
    encoding = response.info().get_content_charset("utf-8")
    jsonData = json.loads(data.decode(encoding))
    data = jsonData["data"]
    asns = data["asns"]
    asn = asns[0]["asn"]
    holder = asns[0]["holder"]
    return str(asn), str(holder)

if __name__ == "__main__":
    main()
