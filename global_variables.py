# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 15:08:49 2020

@author: Robert Feussner
"""
import os


PROJECT = '/u/home/feussner/Project/'
DATA_PATH = '/data/ceph/feussner/'
VISUALISATION_PATH = DATA_PATH + 'images/'
DATABASE = DATA_PATH + 'database.db'
TEMP = '/data/ceph/feussner/temp/'
DAILY_VISUALIZATION = False

def deleteTEMP():
    for f in os.listdir(TEMP):
        os.remove(TEMP + f)


#/data/ceph/feussner/u/home/faulhabn/
