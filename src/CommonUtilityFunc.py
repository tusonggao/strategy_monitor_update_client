from datetime import datetime, timedelta
import pandas as pd
import numpy as np

import time
import sys
import pymongo

import GlobalVars


def find_in_MongoDB(collection, filter_criteria):
    results = collection.find(filter_criteria)
    counter = 0
    for res in results:
        counter += 1
    return counter
	
def getHistoryValueSeries(server_ip, server_port):
    client = pymongo.MongoClient('mongodb://' + server_ip + 
                                 ':' + str(server_port) + '/')
    mydb = client['Meses_Strategy_Monitor_Updated']
    collection = mydb['history_record']
    docs = collection.find()        
    for doc in docs:
        strategy_name = doc['strategy_name']
        value_series = pd.read_json(doc['value_series'], typ='series')
        index_series = pd.read_json(doc['index_series'], typ='series')
        value_series /= value_series[0]
        index_series /= index_series[0]
        drawdown_series = computeMaxDrawdownSeries(value_series)
        index_symbol = doc['index_symbol']
        GlobalVars.history_values_series[strategy_name] = (value_series, 
                     index_series, drawdown_series, index_symbol)

def computeMaxDrawdownSeries(value_series):
    drawdown_list = []
    maxValue = -1
    for value in value_series:
        if value > maxValue:
            maxValue = value
        drawdown_rate = (maxValue-value)/maxValue
        drawdown_list.append(drawdown_rate)
    drawdown_series = pd.Series(drawdown_list, index=value_series.index)
    return drawdown_series


if __name__=='__main__':
    pass
#    print(getTradingDays('2017-04-15'))
#    print(getZLFutureSymbol('2017-4-15'))

 
    
    