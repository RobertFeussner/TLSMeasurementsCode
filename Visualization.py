# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 17:46:09 2020

@author: Robert Feussner
"""
# %% run all - spyder configuration
import os
os.chdir('/u/home/feussner/Project')

import pandas as pd
from global_variables import DATABASE, VISUALISATION_PATH
from datetime import datetime
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

SAVE_PDF = False
SAVE_PNG = True
TESTING = False

INPUT = False

showfliers = False

def main():
    global INPUT
    if INPUT:
        if checkAnswer('Perform visualization for today? (Yes, else Enter)\n'):
            today1 = datetime.now().strftime('%Y%m%d_%V')
            today2 = datetime.now().strftime('%Y_%V')
        else:
            today = input('Day for visualization in Format YYYYMMDD please.\n')
            today = datetime.strptime(today, '%Y%m%d')
    else:
        today = datetime.now()
    today1 = today.strftime('%Y%m%d_%V')
    today2 = today.strftime('%Y_%V')
    start = datetime.now()
    mainWithDay(today1, today2)
    print(datetime.now() - start)
    
def checkAnswer(question):
    answer = input(question)
    if answer == 'Yes' or answer == 'YES' or answer == 'yes' or answer == 'Y' or answer == 'y':
        return True
    else:
        return False

def changeLabels(listOfLabels):
    newLabels = []
    for label in listOfLabels:
        newlabel = ''
        while len(label) >= 20:
            newlabel += label[:20] + '-\n'
            label = label[20:]
        newLabels.append(newlabel + label)
    return newLabels

def mainWithDay(today1, today2):
    global rankings, cipher, performance, performanceASN, aggregated, errorCodes, VISUALISATION_DIRECTORY
    if SAVE_PDF or SAVE_PNG:
        if not os.path.exists(VISUALISATION_PATH):
            os.mkdir(VISUALISATION_PATH)
        if not os.path.exists(VISUALISATION_PATH + today1):
            os.mkdir(VISUALISATION_PATH + today1)
    VISUALISATION_DIRECTORY = VISUALISATION_PATH + today1 + '/'
    
    adoptionName = today2 + '_ADOPTION'
    rankingName = today1 + '_RANKING'
    cipherName = today1 + '_CIPHER'
    performanceName = today1 + '_PERFORMANCE'
    performanceASNName = today1 + '_PERFORMANCE_ASN'
    rankings = getRankingWithAdoption(adoptionName,rankingName)
    cipher = getDfFromDatabase(cipherName)
    performance = getDfFromDatabase(performanceName)
    performanceASN = getDfFromDatabase(performanceASNName)
    aggregated = getDfFromDatabase('AGGREGATED')
    
    errorCodes = getDfFromDatabase('CURL_ERROR_CODES')
    
    figuresAdoptionOverview()
    figuresAdoptionOverRanking()
    figuresPerformanceOverviewTime()
    
    figureTemplate('TLSPie', figureTLSPie, ipVersion=True)
    figureTemplate('ErrorBar', figureErrorBar, ipVersion=True, tlsDifference=True)
    
    figureTemplate('PerformanceOverview', figurePerformanceOverview, ipVersion=True, category=True)
    figureTemplate('PerformanceBoxplot', figureTLSPerformanceBoxplot, category=True)
    figureTemplate('PerformanceGraph', figureTLSPerformanceGraph, ipVersion=True, category=True)
    
    figureTemplate('CipherBoxplot', figureTLSCipherBoxplot, ipVersion=True)
    figureTemplate('CipherAdoption', figureTLSCipherAdoption, ipVersion=True)
    
    figureTemplate('PerformanceASNAdoptionBar', TLSPerformanceASNAdoptionBar, ipVersion=True, category=True)
    figureTemplate('PerformanceASNAdoptionPie', TLSPerformanceASNAdoptionPie, ipVersion=True, category=True)
    figureTemplate('PerformanceASNBoxplot', TLSPerformanceASNBoxplot, ipVersion=True, tlsDifference=True, category=True)

    
def figureTemplate(nameOfFunction, function, zoom=True, ipVersion=False, tlsDifference=False, category=False):
    global SAVE, VISUALISATION_DIRECTORY
    figures = []
    names = []
    rankingNames = ['ALEXA','CISCO','TRANCO','MAJESTIC']
    ipVersions = [-1]
    if ipVersion:
        ipVersions = [4,6]
    tlsVersions = [-1]
    if tlsDifference:
        tlsVersions = [2,3]
    categoryVersions = [-1]
    if category:
        categoryVersions = ['TOP','MIDDLE','BOTTOM']
    for rankingName in rankingNames:
        rankingNameLong = 'RANK_' + rankingName
        for ipVersion in ipVersions:
            for tlsVersion in tlsVersions:
                for categoryVersion in categoryVersions:
                    name = rankingName 
                    if ipVersion != -1:
                        name += ' - IPv' + str(ipVersion)
                    if tlsVersion != -1:
                        name += ' - TLS1.' + str(tlsVersion)  
                    if categoryVersion != -1:
                        name += ' - 100 '+ categoryVersion + ' sample'
                    names.append(nameOfFunction + name)
                    fig, axis = plt.subplots(1,1)
                    axis.set_title(name)
                    legend = function(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, categoryVersion)
                    if legend != None:
                        axis.legend(legend)
                    if not zoom:
                        axis.set_ylim([0,100])
                    fig.set_size_inches(7,6)
                    if nameOfFunction in ['PerformanceOverview','PerformanceASNAdoptionPie','TLSPie']:
                        #plt.tight_layout()
                        plt.subplots_adjust(bottom=0.2, left=0.2, right=0.8, top=0.8)
                    else:
                        plt.subplots_adjust(bottom=0.4, left=0.2, right=0.9)
                    figures.append(fig)
        if TESTING:
            break
    if SAVE_PDF or SAVE_PNG:
        formatTypes = []
        if SAVE_PDF:
            formatTypes.append('pdf')
        if SAVE_PNG:
            formatTypes.append('png')
        for formatType in formatTypes:     
            for i in range(len(figures)):
                figures[i].savefig(VISUALISATION_DIRECTORY + names[i].replace(' ', '') + '.'+formatType, format=formatType)
    return names, figures        

def TLSPerformanceASNBoxplot(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global performanceASN
    #time = 'TOTAL_TIME'
    usecols = ['ASN_HOLDER']
    times = ['NAMELOOKUP_TIME','APPCONNECT_TIME']
    for time in times:
        usecols.append('TLS1'+str(tlsVersion)+ '_' +time)
    df = performanceASN.loc[((performanceASN['RANKING_NAME'] == rankingName)&(performanceASN['IP_VERSION'] == ipVersion)&(performanceASN['CATEGORY'] == category)),usecols].copy()
    df = df.dropna()
    df['Time'] = df[usecols[2]] - df[usecols[1]]
    helper = df.groupby(by='ASN_HOLDER', as_index=False).count().sort_values(by='Time', ascending=False)
    values = []
    labels = []
    counter = 0
    for asnHolder in helper['ASN_HOLDER'].tolist():
        if counter > 4:
            values.append(df['Time'])
            labels.append('Rest')
            break
        values.append(df.loc[df['ASN_HOLDER'] == asnHolder, 'Time'])
        df = df.loc[df['ASN_HOLDER'] != asnHolder, :]
        labels.append(asnHolder)
        counter+=1
    axis.boxplot(values, showfliers = showfliers)
    labels = changeLabels(labels)
    plt.xticks(range(1,len(labels)+1), labels)
    axis.set_xlabel('ASN Holder')
    axis.set_ylabel('Time')
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_fn))
    plt.xticks(rotation=90)
    
def TLSPerformanceASNAdoptionBar(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    sizes, labels, explode = TLSPerformanceASNAdoption(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category)
    labels = changeLabels(labels)
    axis.bar(labels, sizes)
    axis.set_xlabel('ASN Holder')
    axis.set_ylabel('Ownership percentage of websites in sample')
    axis.yaxis.set_major_formatter(ticker.PercentFormatter(sum(sizes)))
    plt.xticks(rotation=90)
    plt.xticks(range(0,len(labels)), labels)


def TLSPerformanceASNAdoptionPie(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    sizes, labels, explode = TLSPerformanceASNAdoption(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category)
    axis.pie(sizes, labels=labels, shadow=True, startangle=90, explode=explode, autopct='%1.0f%%')
    
def TLSPerformanceASNAdoption(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global performanceASN
    usecols = ['WEBSITE', 'ASN_HOLDER']
    df = performanceASN.loc[((performanceASN['RANKING_NAME'] == rankingName)&(performanceASN['IP_VERSION'] == ipVersion)&(performanceASN['CATEGORY'] == category)),usecols].copy()
    df = df.dropna()
    df = df.groupby(by='ASN_HOLDER', as_index=False).count().sort_values(by='WEBSITE', ascending=False)
    sizes = df['WEBSITE'].tolist() 
    labels= df['ASN_HOLDER'].tolist()
    explode = None
    if len(df.index) > 5:
        newSizes = sizes[:5]
        restSize = sum(sizes[5:])
        newSizes.append(restSize)
        sizes = newSizes
        
        newLabels= labels[:5]
        restLabel= 'Rest (' + str(len(labels[5:])) + ' distinct ASN Holder)'
        newLabels.append(restLabel)
        labels = newLabels
        explode = [0.0]*5 + [0.1]
    return sizes, labels, explode
    
    

def figureTLSCipherAdoption(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global cipher
    df = cipher.loc[((cipher['RANKING_NAME'] == rankingName)&(cipher['IP_VERSION'] == ipVersion)),:].copy()
    df = df.dropna()
    df = df.groupby(by='CIPHER', as_index=False).agg({'TOTAL_TIME':'count'}).sort_values(by='CIPHER')
    
    labels = []
    for cipherName in df['CIPHER'].tolist():
        cipherNameNew = cipherName.split('_')
        cipherNameNew = ' '.join(cipherNameNew[:3]) + '\n' + ' '.join(cipherNameNew[3:])
        labels.append(cipherNameNew)
    
    axis.bar(df['CIPHER'], df['TOTAL_TIME'])
    axis.set_xlabel('Cipher')
    axis.set_ylabel('Adoption rate of sample')
    axis.yaxis.set_major_formatter(ticker.PercentFormatter(100))
    plt.xticks(rotation=90)
    plt.xticks(range(0,len(labels)), labels)

def figureTLSCipherBoxplot(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global cipher
    
    df = cipher.loc[((cipher['RANKING_NAME'] == rankingName)&(cipher['IP_VERSION'] == ipVersion)),:].copy()
    df = df.dropna()
    df['Time'] = df['APPCONNECT_TIME'] - df['NAMELOOKUP_TIME']
    labels = []
    sizes = []
    for cipherName in df['CIPHER'].drop_duplicates().sort_values().tolist():
        cipherNameNew = cipherName.split('_')
        cipherNameNew = ' '.join(cipherNameNew[:3]) + '\n' + ' '.join(cipherNameNew[3:])
        labels.append(cipherNameNew)
        sizes.append(df.loc[df['CIPHER'] == cipherName, 'Time'])    
    
    axis.boxplot(sizes, showfliers = showfliers)
    plt.xticks(range(1,len(labels)+1), labels)
    axis.set_xlabel('Cipher')
    axis.set_ylabel('Time')
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_fn))
    plt.xticks(rotation=90)
    
def figureTLSPerformanceGraph(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global performance
    usecols = ['ABSOLUTE_RANK']
    times = ['NAMELOOKUP_TIME','APPCONNECT_TIME']
    for time in times:
        usecols.append('TLS12_' +time)
        usecols.append('TLS13_' +time)
    
    df = performance.loc[((performance['RANKING_NAME'] == rankingName)&(performance['IP_VERSION'] == ipVersion)&(performance['CATEGORY'] == category)),usecols].copy()
    for tlsVersion in ['TLS12_','TLS13_']:
        df[tlsVersion+'Time'] = df[tlsVersion+'APPCONNECT_TIME'] - df[tlsVersion+'NAMELOOKUP_TIME']
    
    start = str(df['ABSOLUTE_RANK'].min())
    end = str(df['ABSOLUTE_RANK'].max())
    axis.plot(range(100), df['TLS12_Time'])
    axis.plot(range(100), df['TLS13_Time'])
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_fn))
    axis.set_ylabel('Time')
    axis.set_xlabel('100 Websites sample, range:\n[' + start + ':' + end + ']')
    return ['Time TLS 1.2','Time TLS 1.3']
    
def figureTLSPerformanceBoxplot(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global performance
    usecols = ['ABSOLUTE_RANK']
    times = ['NAMELOOKUP_TIME','APPCONNECT_TIME']
    for time in times:
        usecols.append('TLS12_' +time)
        usecols.append('TLS13_' +time)
    
    df = performance.loc[((performance['RANKING_NAME'] == rankingName)&(performance['CATEGORY'] == category)),:].copy()
    for tlsVersion in ['TLS12_','TLS13_']:
        df[tlsVersion+'Time'] = df[tlsVersion+'APPCONNECT_TIME'] - df[tlsVersion+'NAMELOOKUP_TIME']
        
    ipv4 = df.loc[(df['IP_VERSION'] == 4),:]
    ipv6 = df.loc[(df['IP_VERSION'] == 6),:]
    columns = [ipv4['TLS12_Time'].dropna(),ipv4['TLS13_Time'].dropna(),ipv6['TLS12_Time'].dropna(),ipv6['TLS13_Time'].dropna()]
    labels = ['IPv4 TLS1.2', 'IPv4 TLS1.3', 'IPv6 TLS1.2', 'IPv6 TLS1.3']
    axis.boxplot(columns, showfliers = showfliers)
    axis.set_ylabel('Time')
    axis.set_xlabel('IP and TLS version')
    axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_fn))
    plt.xticks([1, 2, 3, 4], labels)
    

def figurePerformanceOverview(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global performance
    differencePercent = 0.1
    
    usecols = []
    times = ['NAMELOOKUP_TIME','APPCONNECT_TIME']
    for time in times:
        usecols.append('TLS12_' +time)
        usecols.append('TLS13_' +time)
    
    df = performance.loc[((performance['RANKING_NAME'] == rankingName)&(performance['IP_VERSION'] == ipVersion)&(performance['CATEGORY'] == category)), usecols].copy()
    df = df.dropna()
    for tlsVersion in ['TLS12_','TLS13_']:
        df[tlsVersion+'Time'] = df[tlsVersion+'APPCONNECT_TIME'] - df[tlsVersion+'NAMELOOKUP_TIME']
    
    df['FASTER'] = df.apply(lambda x : performanceDifference(x['TLS12_Time'], x['TLS13_Time'], differencePercent) , axis='columns')
    df = df.groupby(by='FASTER', as_index=False).agg({'TLS12_Time':'count'})
    sizes = df['TLS12_Time']
    labels= df['FASTER']
    axis.pie(sizes, labels=labels, shadow=True, startangle=90, autopct=lambda p: '{:.1f}%\n({:.0f})'.format(p, p * sum(sizes) / 100))

def performanceDifference(tls12, tls13, percentError):
    if tls12 > tls13 + tls12 * percentError:
        return 'TLS 1.3 faster'
    if tls13 > tls12 + tls12 * percentError:
        return 'TLS 1.2 faster'
    else:
        return 'Performance difference less than\n10% of TLS 1.2 measurement'

def figureTLSPie(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global rankings
    df = rankings[rankingNameLong].copy()
    columns = []
    for tlsVersion in [2,3]:
        columns.append('IPV' + str(ipVersion) + '_TLS1' + str(tlsVersion))
    tls12 = df.loc[((df[columns[0]] == 0)&(df[columns[1]] != 0)), 'WEBSITE'].count()
    tls13 = df.loc[((df[columns[0]] != 0)&(df[columns[1]] == 0)), 'WEBSITE'].count()
    tls12And13 = df.loc[((df[columns[0]] == 0)&(df[columns[1]] == 0)), 'WEBSITE'].count()
    noTls = df.loc[((df[columns[0]] != 0)&(df[columns[1]] != 0)), 'WEBSITE'].count()
    labels = ['only TLS 1.2\nimplemented', 'only TLS 1.3\nimplemented', 'both TLS 1.2 and\n1.3 implemented', 'Error']
    sizes = [tls12, tls13, tls12And13, noTls]
    explode = [0.0,0.0,0.0,0.1]
    axis.pie(sizes, labels=labels, shadow=True, startangle=90, explode=explode, autopct='%1.1f%%')

def figureErrorBar(axis, rankingName, rankingNameLong, ipVersion, tlsVersion, category):
    global rankings, errorCodes
    df = rankings[rankingNameLong].copy()
    column = 'IPV' + str(ipVersion) + '_TLS1' + str(tlsVersion)
    df = df.loc[df[column] != 0, [column,'WEBSITE']].groupby(by=column, as_index=False).count()
    df = pd.merge(df, errorCodes, left_on=[column], right_on=['ERROR'])
    df = df[['WEBSITE', 'ERROR_STRING']]
    df = df.rename(columns={'WEBSITE':'Amount','ERROR_STRING':'Error'})
    df = df.sort_values(by='Amount', ascending=False)
    errors = df['Error'].tolist()
    errors = changeLabels(errors)
    """
    newErrors = []
    for error in errors:
        error = error.split(' ')
        error = ' '.join(error[:3]) + '\n' + ' '.join(error[3:])
        newErrors.append(error)
    """
    axis.bar(errors, df['Amount'])
    axis.set_xlabel('Error')
    axis.set_ylabel('Absolute number of occurences')
    plt.xticks(rotation=90)#,ha='right'
    
def figuresAdoptionOverview(zoom=True):
    global SAVE, VISUALISATION_DIRECTORY, aggregated
    figures = []
    names = []
    rankingNames = ['ALEXA','CISCO','TRANCO','MAJESTIC']
    for rankingName in rankingNames:
        for ipVersion in [4,6]:
            fig, axis = plt.subplots(1,1)
            name = rankingName + ' - IPv' + str(ipVersion)
            axis.set_title(name)
            names.append('AdoptionOverview' + name)
            legend = []
            for tlsVersion in [2,3]:
                df = aggregated.loc[((aggregated['IP_VERSION'] == ipVersion)&(aggregated['TLS_VERSION'] == tlsVersion)&(aggregated['RANKING_NAME'] == rankingName)), ['DAY','WEBSITES','NO_ERROR','TIMEOUT']].copy()
                df['DAY'] = pd.to_datetime(df['DAY'].apply(lambda x : x[0:8]), format='%Y%m%d')
                df.sort_values(by=['DAY'], inplace=True)
                axis.plot(df['DAY'], df['NO_ERROR']/df['WEBSITES']*100.0)
                legend.append('TLS 1.' + str(tlsVersion) + ' - No Error')
                axis.plot(df['DAY'], df['TIMEOUT']/df['WEBSITES']*100.0)
                legend.append('TLS 1.' + str(tlsVersion) + ' - Timeout')
            axis.yaxis.set_major_formatter(ticker.PercentFormatter())
            plt.xticks(rotation=60,ha='right')
            if not zoom:
                axis.set_ylim([0,100])
            #axis.legend(legend)
            axis.legend(legend, loc='lower left', bbox_to_anchor=(0.6, -0.73))

            axis.set_xlabel('Day of measurement')
            axis.set_ylabel('Percentage of occurence')
            fig.set_size_inches(7,6)
            plt.subplots_adjust(bottom=0.4, left=0.2, right=0.9)
            figures.append(fig)
    if SAVE_PDF or SAVE_PNG:
        formatTypes = []
        if SAVE_PDF:
            formatTypes.append('pdf')
        if SAVE_PNG:
            formatTypes.append('png')
        for formatType in formatTypes:     
            for i in range(len(figures)):
                figures[i].savefig(VISUALISATION_DIRECTORY + names[i].replace(' ', '') + '.'+formatType, format=formatType)
    return names, figures

def figuresPerformanceOverviewTime():
    global SAVE, VISUALISATION_DIRECTORY, aggregated
    figures = []
    names = []
    rankingNames = ['ALEXA','CISCO','TRANCO','MAJESTIC']
    for rankingName in rankingNames:
        for ipVersion in [4,6]:
            fig, axis = plt.subplots(1,1)
            name = rankingName + ' - IPv' + str(ipVersion)
            axis.set_title(name)
            names.append('PerformanceOverviewTime' + name)
            legend = []
            for tlsVersion in [2,3]:
                df = aggregated.loc[((aggregated['IP_VERSION'] == ipVersion)&(aggregated['TLS_VERSION'] == tlsVersion)&(aggregated['RANKING_NAME'] == rankingName)), 
                                    ['DAY','NAMELOOKUP_TIME','APPCONNECT_TIME']].copy()
                df['DAY'] = pd.to_datetime(df['DAY'].apply(lambda x : x[0:8]), format='%Y%m%d')
                df.sort_values(by=['DAY'], inplace=True)
                df['Time'] = df['APPCONNECT_TIME'] - df['NAMELOOKUP_TIME']
                axis.plot(df['DAY'], df['Time'])
                legend.append('TLS 1.' + str(tlsVersion))
                axis.yaxis.set_major_formatter(ticker.FuncFormatter(format_fn))

            plt.xticks(rotation=60,ha='right')
            axis.legend(legend)
            axis.set_xlabel('Day of measurement')
            axis.set_ylabel('Mean of time measurements')
            fig.set_size_inches(7,6)
            plt.subplots_adjust(bottom=0.4, left=0.2, right=0.9)
            figures.append(fig)
    if SAVE_PDF or SAVE_PNG:
        formatTypes = []
        if SAVE_PDF:
            formatTypes.append('pdf')
        if SAVE_PNG:
            formatTypes.append('png')
        for formatType in formatTypes:     
            for i in range(len(figures)):
                figures[i].savefig(VISUALISATION_DIRECTORY + names[i].replace(' ', '') + '.'+formatType, format=formatType)
    return names, figures

def figuresAdoptionOverRanking(zoom=True):
    global SAVE, VISUALISATION_DIRECTORY, rankings
    figures = []
    names = []
    groupSize = 10000
    
    rankingNames = ['ALEXA','CISCO','TRANCO','MAJESTIC']
    for rankingName in rankingNames:
        rankingNameLong = 'RANK_' + rankingName
        df = rankings[rankingNameLong].copy()
        for ipVersion in [4,6]:
            fig, axis = plt.subplots(1,1)
            name = rankingName + ' - IPv' + str(ipVersion)
            axis.set_title(name)
            names.append('AdoptionOverRanking' + name)
            legend = []
            for tlsVersion in [2,3]:
                column = 'IPV' + str(ipVersion) + '_TLS1' + str(tlsVersion)
                dfLocal = df.loc[df[column] == 0, [rankingNameLong, column]]
                dfLocal[rankingNameLong] = dfLocal[rankingNameLong].apply(lambda x : x // groupSize)
                dfLocal = dfLocal.groupby(by=rankingNameLong, as_index=False).count()
                dfLocal[column] = dfLocal[column].apply(lambda x : x / groupSize)
                if rankingName == 'ALEXA':
                    dfLocal = dfLocal[:-1]
                axis.plot(dfLocal[rankingNameLong], dfLocal[column])
                legend.append('TLS 1.' + str(tlsVersion))
            axis.legend(legend)
            axis.set_ylabel('Connection without error')
            axis.set_xlabel('Ranking Groups of 10,000')
            axis.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
            if not zoom:
                axis.set_ylim([0,1])
            fig.set_size_inches(7,6)
            plt.subplots_adjust(bottom=0.4, left=0.2, right=0.9)
            figures.append(fig)
    if SAVE_PDF or SAVE_PNG:
        formatTypes = []
        if SAVE_PDF:
            formatTypes.append('pdf')
        if SAVE_PNG:
            formatTypes.append('png')
        for formatType in formatTypes:     
            for i in range(len(figures)):
                figures[i].savefig(VISUALISATION_DIRECTORY + names[i].replace(' ', '') + '.'+formatType, format=formatType)
    return names, figures

def format_fn(tick_val, tick_pos):
    return '{:.0f} ms'.format(tick_val)

def getDfFromDatabase(name):
    try:
        con = sqlite3.connect(DATABASE)
        df = pd.read_sql('select * from "'+ name +'"', con)
    finally:
        con.close()
    return df

def getRankingWithAdoption(adoptionName,rankingName):
    rankingNames = ['RANK_ALEXA','RANK_CISCO','RANK_TRANCO','RANK_MAJESTIC']
    try:
        con = sqlite3.connect(DATABASE)
        allRankings = pd.read_sql('select * from "'+ rankingName +'"', con)
        adoption = pd.read_sql('select * from "'+ adoptionName +'"', con)
    finally:
        con.close()
    allRankingsWithAdoption = pd.merge(allRankings, adoption, how='inner', on='WEBSITE')
    
    rankings={}
    for ranking in rankingNames:
        df = allRankingsWithAdoption.loc[allRankingsWithAdoption[ranking].notnull(),['WEBSITE',ranking,'IPV4_TLS13','IPV4_TLS12','IPV6_TLS13','IPV6_TLS12']].copy()
        df = df.sort_values(by=[ranking])
        rankings[ranking] = df.copy()
    del df
    del allRankings
    del allRankingsWithAdoption
    del adoption
    return rankings

if __name__ == "__main__":
    main()