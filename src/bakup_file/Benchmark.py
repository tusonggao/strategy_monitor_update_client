import time

from TradeDateCompute import *
from MarketDataGetter import MarketDataGetterFromTS
from CommonUtilityFunc import *

CONTRACT_SIZE_DICT = {'IC': 200, 'IF': 300, 'IH': 300}

class BenchmarkIndex():
    def __init__(self, symbol, history=True):
        self.dataStore = {}
        self.symbol = symbol
        self.history = history
        self.dataStore[self.symbol] = {}
        self.gottenDate = ''
        self.dataGetter = MarketDataGetterFromTS(self.dataStore)
        
    def getLastTradeDayLastMinData(self, date_str):
        price = getPrevSettlementPrice(self.symbol, date_str)
        if self.symbol not in self.dataStore:
            self.dataStore[self.symbol] = {}
        self.dataStore[self.symbol]['09:30:00'] = price

    def get1MinDataByDate(self, date_str):
        self.dataGetter.get1MinDataByDate(self.symbol, date_str)
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if self.history:
            now = datetime.now()
            if not (datetime(date.year, date.month, date.day, 15, 0, 0) < now < \
                    datetime(date.year, date.month, date.day, 15, 30, 30)):
                price = getSettlementPrice(self.symbol, date_str)
                self.dataStore[self.symbol]['15:00:00'] = price
                logging.logging('In BenchmarkIndex getSettlementPrice ' + \
                            date_str + ' ' + self.symbol + ' ' + str(price))

    def getMarkePrice(self, time_str):
        return self.dataStore[self.symbol][time_str]
    
    def takenMargin(self, price):
        raise NotImplementedError('not implemented')

class BenchmarkIndexIC(BenchmarkIndex):  #中证500
    def __init__(self, history=True):
        self.symbol = 'SH000905'
        super(BenchmarkIndexIC, self).__init__(self.symbol, history)
        
    def getLastTradeDayLastMinData(self, date_str):
        price = getPrevClosePrice(self.symbol, date_str)
        if self.symbol not in self.dataStore:
            self.dataStore[self.symbol] = {}
        self.dataStore[self.symbol]['09:30:00'] = price
        
    def get1MinDataByDate(self, date_str):
        self.dataGetter.get1MinDataByDate(self.symbol, date_str)

class BenchmarkIndexIC_Future(BenchmarkIndex):  #中证500
    def __init__(self, symbol=None, history=True):
        if not symbol:
            today = datetime.today()
            today_str = today.strftime('%Y-%m-%d')
            symbol = getZLFutureSymbol(today_str, 'IC')
        logging.logging('In BenchmarkIndexIC_Future symbol is ', symbol)
        super(BenchmarkIndexIC_Future, self).__init__(symbol, history)
        
    def contractSize(self, price): #合约价值
        return price*200
        
    def takenMargin(self, price): #占用保证金
        return self.contractSize(price)*0.3
            
class BenchmarkIndexIF(BenchmarkIndex):  #沪深300
    def __init__(self, history=True):
        symbol = 'SH000300'
        super(BenchmarkIndexIF, self).__init__(symbol, history)
        
    def getLastTradeDayLastMinData(self, date_str):
        price = getPrevClosePrice(self.symbol, date_str)
        if self.symbol not in self.dataStore:
            self.dataStore[self.symbol] = {}
        self.dataStore[self.symbol]['09:30:00'] = price
        
    def get1MinDataByDate(self, date_str):
        self.dataGetter.get1MinDataByDate(self.symbol, date_str)
        
class BenchmarkIndexIF_Future(BenchmarkIndex):  #沪深300
    def __init__(self, symbol=None, history=True):
        if not symbol:
            today = datetime.today()
            today_str = today.strftime('%Y-%m-%d')
            symbol = getZLFutureSymbol(today_str, 'IF')
        logging.logging('In BenchmarkIndexIF_Future symbol is ', symbol)
        super(BenchmarkIndexIF_Future, self).__init__(symbol, history)
        
    def contractSize(self, price): #合约价值
        return price*300
        
    def takenMargin(self, price): #占用保证金
        return self.contractSize(price)*0.2
        
class BenchmarkIndexIH(BenchmarkIndex):  #上证50
    def __init__(self, history=True):
        symbol = 'SH000016'
        super(BenchmarkIndexIH, self).__init__(symbol, history)
        
    def getLastTradeDayLastMinData(self, date_str):
        price = getPrevClosePrice(self.symbol, date_str)
        if self.symbol not in self.dataStore:
            self.dataStore[self.symbol] = {}
        self.dataStore[self.symbol]['09:30:00'] = price
        
    def get1MinDataByDate(self, date_str):
        self.dataGetter.get1MinDataByDate(self.symbol, date_str)

class BenchmarkIndexIH_Future(BenchmarkIndex):  #上证50
    def __init__(self, symbol=None, history=True):
        if not symbol:
            today = datetime.today()
            today_str = today.strftime('%Y-%m-%d')
            symbol = getZLFutureSymbol(today_str, 'IH')
        logging.logging('In BenchmarkIndexIH_Future symbol is ', symbol)
        super(BenchmarkIndexIH_Future, self).__init__(symbol, history)
        
    def contractSize(self, price): #合约价值
        return price*300
        
    def takenMargin(self, price): #占用保证金
        return self.contractSize(price)*0.2
        
if __name__=='__main__':
#    benchmark = BenchmarkIndexIF()
#    benchmark.getLastTradeDayLastMinData('2017-2-12')
#    print(benchmark.dataStore)
    
    date = datetime.strptime('2017-2-9', '%Y-%m-%d')
    print(date.year, date.month, date.day)

