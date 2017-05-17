from WindPy import *
import sys

from WindPy import w as WindPyGateway
from datetime import datetime
from CommonUtilityFunc import *


def getFirstTradeDayOfMonth(year_n, month_n):
    date_str = '%d-%d-%d'%(year_n, month_n, 1)
#    date_str_next = '%d-%d-%d'%(year_n, month_n, 2)
    if w.tdayscount(date_str, date_str).Data[0][0]==1:
        return date_str 
    tradeDay = WindPyGateway.tdaysoffset(1, date_str, "")
    return tradeDay.Data[0][0].strftime('%Y-%m-%d')

def getNearestTradeDay(date):
    date_str = '%d-%d-%d'%(date.year, date.month, date.day)
    tradeDay = WindPyGateway.tdaysoffset(0, date_str, "")
    return tradeDay.Data[0][0]

def getNextTradeDayStr(date_str):
    date = datetime.strptime(date_str,'%Y-%m-%d')
    date_str = '%d-%d-%d'%(date.year, date.month, date.day)
    tradeDay = WindPyGateway.tdaysoffset(1, date_str, "")
    return tradeDay.Data[0][0].strftime('%Y-%m-%d')
        
def getLastTradeDay(date_str):
    tradeDay = WindPyGateway.tdaysoffset(-1, date_str, "")
    return tradeDay.Data[0][0].strftime('%Y-%m-%d')
    
if __name__=='__main__':
    WindPyGateway.start()
    date_str = '2017-2-19'
    date = datetime.strptime(date_str,'%Y-%m-%d')
    print(getNearestTradeDay(date))
    
    print(getLastTwoTradeDaysOfStock('SH600004', '2017-2-18'))
    print(getNextTradeDayStr('2017-2-18'))
#    print(data, str(data[2], encoding='gbk'))
    print(getLastTradeDayOfStock('IC1703', '2017-2-18'))
#    print(getFirstTradeDayOfMonth(2017, 1))