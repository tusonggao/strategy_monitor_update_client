from collections import OrderedDict
import pymysql

from datetime import datetime
from TradeDateCompute import *

import CommonUtilityFunc
import time

class MarketDataGetter():
    def __init__(self, resultsStore):
        self.resultsStore = resultsStore
        self.costTime = []

    def get1MinDataByDate(self, stockID, date_str):
        raise NotImplementedError('not implemented')

    def getLastTradeDayLastMinData(self, stockID, date_str):
        raise NotImplementedError('not implemented')
              
#class MarketDataGetterFromDB(MarketDataGetter):
#    def __init__(self, resultsStore, ipConnection=None):
#        super(MarketDataGetterFromDB, self).__init__(resultsStore)
#        self.dbConn = pymysql.connect(use_unicode=True, charset="utf8", 
#                                      host='192.168.0.248', user='root',
#                                      passwd='123456', db='mssdb')
#        self.dbCur = self.dbConn.cursor()
#
#        
#    def read1MinPriceDataByDateWorkingFunc(self, sid, date_str):
#        print('Getting Into read1MinPriceDataByDateWorkingFunc ', sid)
#        mysql_str = 'select close, cur_time from '\
#                    'stocks_marketdata_1min t '\
#                    'where t.isin="%s" and '\
#                    't.cur_time like "%%%s%%"  '%(sid, date_str)
#        print('mysql_str is ', mysql_str)
#        begin_t = time.time()
#        self.dbCur.execute('select close, cur_time from '
#                           'stocks_marketdata_1min t '
#                           'where t.isin="%s" and '
#                           't.cur_time like "%%%s%%"  '%(sid, date_str))
#        rtn_data = self.dbCur.fetchall()
#        end_t = time.time()
#        print('cost time is ', end_t-begin_t)
#        self.costTime.append(end_t-begin_t)
#        oneMinPrices = {}
#        for d in rtn_data:
#            oneMinPrices[d[1].time()] = d[0]
#        self.results[sid] = oneMinPrices
#        print('Getting out of read1MinPriceDataByDateWorkingFunc ', sid)
#
#
#    def read1MinPriceDataByDate(self, stk_id, date):
#        print('Getting In read1MinPriceDataByDate() stk_id is ', 
#              stk_id, ' date is ', date)
#        
#        if isinstance(stk_id, (list, tuple)):
##            sid_str = ','.join(['\''+sid+'\'' for sid in stk_id])
##            print('sid_str is ', sid_str)
##            date_str = date.strftime('%Y-%m-%d')
##            self.read1MinPriceDataByDateWorkingFunc(sid_str, date_str)
#            for sid in stk_id:
#                newest_date = self.getNewestValidDateInDB(sid, date)
#                date_str = newest_date.strftime('%Y-%m-%d')
#                self.read1MinPriceDataByDateWorkingFunc(sid, date_str)
#        else:
#            date = self.getNewestValidDateInDB(sid, date)
#            date_str = date.strftime('%Y-%m-%d')
#            self.read1MinPriceDataByDateWorkingFunc(stk_id, date_str)
#        print('Getting outof read1MinPriceDataByDate() stk_id is ', 
#              stk_id, ' date is ', date)
#              
#              
#    def getNewestValidDateInDB(self, sid, date):
#        date += timedelta(hours=20)
#        date_str = date.strftime('%Y-%m-%d  %H:%M:%S')
#        self.dbCur.execute('select cur_time from stocks_marketdata_1min t '
#                           'where t.isin="%s" and t.cur_time<"%s" '
#                           'order by t.cur_time desc'%(sid, date_str))
#        newestDate = self.dbCur.fetchone()
#        return newestDate[0]
        
        
class MarketDataGetterFromTS(MarketDataGetter):     
    def __init__(self, resultsStore):
        super(MarketDataGetterFromTS, self).__init__(resultsStore)
    
    def get1MinDataByDate(self, stockID, date_str):
        data = CommonUtilityFunc.getMinMarketDataByDate(stockID, date_str)
        if stockID not in self.resultsStore:
            self.resultsStore[stockID] = OrderedDict()
        for d in data:
            if b'date' in d and b'close' in d:
                time_ = d[b'date'].split()[1].decode()
                self.resultsStore[stockID][time_] = d[b'close']
            else:
                time_ = d['date'].split()[1]
                self.resultsStore[stockID][time_] = d['close']
                

    def getLastTradeDayLastMinData(self, stockID, date_str):
        d = CommonUtilityFunc.getLastTradeDayLastMinData(
                                   stockID, date_str)
        if stockID not in self.resultsStore:
            self.resultsStore[stockID] = OrderedDict()
        if b'close' in d:
            self.resultsStore[stockID]['09:30:00'] = d[b'close']
        else:
            self.resultsStore[stockID]['09:30:00'] = d['close']
            
        
if __name__=="__main__":
    oneMinPricesDict = {}
    marketDataGetter = MarketDataGetterFromTS(oneMinPricesDict)
    
    begin_t = time.time()
    
    stockID = 'SZ002383'
    begin_date = "2017-01-4"
    end_date = "2017-01-4"
    
    marketDataGetter.getLastTradeDayLastMinData(stockID, begin_date)
    marketDataGetter.get1MinDataByDate(stockID, begin_date)
    
    print('oneMinPricesDict is ', oneMinPricesDict)
    
    end_t = time.time()

    print('cost time is ', end_t-begin_t) # 'SZ002300'
    
    aaa = getLastTradeDayOfStock('SZ002300', '2017-01-13')
    print('aaa is ', aaa)

