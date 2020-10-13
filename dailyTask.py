# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 14:38:01 2020

@author: Robert Feussner
"""
# %% run all - spyder configuration
#import os
#os.chdir('/u/home/feussner/Project')

from datetime import datetime

from DownloadRankings import mainWithDay as mainDownloadRankings
from TLSAdoption import mainWithDay as mainTLSAdoption
from TLSPerformance import mainWithDay as mainTLSPerformance
from ASN import mainWithDay as mainASN
from Aggregation import mainWithDay as mainAggregation
from global_variables import DAILY_VISUALIZATION
from Visualization import mainWithDay as mainVisualization

def main():
    today1 = datetime.now().strftime('%Y%m%d_%V')
    today2 = datetime.now().strftime('%Y_%V')
    
    mainDownloadRankings(today1)
    mainTLSAdoption(today2)
    mainTLSPerformance(today1)
    mainASN(today1)
    mainAggregation(today1, today2)
    if DAILY_VISUALIZATION:
        mainVisualization(today1, today2)
    print(today1 + ' done.')
    
if __name__ == "__main__":
    main()
