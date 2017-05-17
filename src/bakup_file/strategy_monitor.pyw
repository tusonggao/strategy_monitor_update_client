# encoding: UTF-8
from __future__ import print_function

__author__ = 'TuSonggao'

import sys
import os
import ctypes
import platform
import threading
from collections import OrderedDict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from WindPy import *

import time

from matplotlib.backends import qt_compat
use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
if use_pyside:
    from PySide import QtGui, QtCore
else:
    from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  #允许显示中文
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

progname = os.path.basename(sys.argv[0])
progversion = "0.1"

class TickDataSeries:
    def __init__(self, stock_id, dataSeries, constant=False):
        self.stock_id = stock_id
        self.dataSeries = dataSeries
        if constant:
            self.constPrice = dataSeries[0]
        else:
            self.constPrice = -1.0
        self.curr_index = 0
        
    def getNewestPriceByTime(self, dt):
        if self.constPrice > 0:
            return self.constPrice
        try:
            while self.dataSeries[self.curr_index+1][0] <= dt:
                self.curr_index += 1
            price = self.dataSeries[self.curr_index][1]
            if price==0.0:
                price = self.getNearestValidPrice()
            else:
                print(' not get In getNearestValidPrice!!!')
            return price
        except IndexError:
            return self.dataSeries[-1][1]
            
    def addTickData(self, dt, data):
        self.dataSeries.append((dt, data))
    
    def getNearestValidPrice(self):
        price = 0.0
        for i in range(self.curr_index+1, len(self.dataSeries)):
            if self.dataSeries[i][1] > 0:
                price = self.dataSeries[i][1]
        return price
        
    def storeData(self):
        pass
        

class BaseMatplotlibWidget(FigureCanvas):
    def __init__(self, parent=None, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=100, hold=False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        self.axes.hold(hold)

        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, 
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def sizeHint(self):
        w, h = self.get_width_height()
        return QtCore.QSize(w, h)

    def minimumSizeHint(self):
        return QtCore.QSize(20, 20)


class MatplotlibWidget(FigureCanvas):
    def __init__(self, parent=None, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=100, hold=False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        if xscale is not None:
            self.axes.set_xscale(xscale)
        if yscale is not None:
            self.axes.set_yscale(yscale)
        if xlim is not None:
            self.axes.set_xlim(*xlim)
        if ylim is not None:
            self.axes.set_ylim(*ylim)
        self.axes.hold(hold)

        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, 
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def sizeHint(self):
        w, h = self.get_width_height()
        return QtCore.QSize(w, h)

    def minimumSizeHint(self):
        return QtCore.QSize(20, 20)
        

class StockMplWidget(MatplotlibWidget):    
    def plot(self, num, n1, n2):
        x = np.linspace(-num, num)
        self.axes.plot(x, x**n1)
        self.axes.plot(x, x**n2)
        self.draw()
        self.repaint()
        
class StockBarraMplWidget(MatplotlibWidget):    
    def plot(self, val_list):
        self.axes.plot(val_list)
#        self.axes.plot(val_list, '*-')
        self.draw()        
        
#    def plot(self, num):
#        data = [np.random.random() for i in range(num)]
#        self.axes.plot(data, '*-')
#        self.draw()


class MainWnd(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.addSubPlot(2, 3, 2)
        
        self.barra300 = pd.read_excel('Barra_Hold_Positions\\Barra_300_Jan.xlsx')
        self.barra500 = pd.read_excel('Barra_Hold_Positions\\Barra_500_Jan.xlsx')
        self.initValue = 1000*10000
        self.showMaximized()
        self.setWindowTitle(u'策略实时监控')

#        self.preprocessingData_111()        
#        self.readWindData_111()
        
        self.preprocessingData()
        print('get out of the func')
        print('len of tds is', len(self.tds_list))
        print('self.tds_list[2] is ', self.tds_list[2])
        
        self.generateValueList()
        print('content of self.value_list is ', self.value_list)
        print('len of self.value_list is ', len(self.value_list))
#        plt.plot(self.value_list)
        
        self.mplwidget_list[0].plot(self.value_list)       
#        for stock_id in  self.stockInitPricesDict.keys():
#            print("processing the stock_id ", stock_id)
#            self.readWindData_111(stock_id)
#            time.sleep(4)
        
        
    def addSubPlot(self, m, n, num):
        mainLayout = QtGui.QGridLayout()
        self.mplwidget_list = []
        count = 0
        for i in range(m):
            for j in range(n):
                if count<num:
                    count += 1
                    widget = StockBarraMplWidget(self, title=u'日内收益曲线',
                                             xlabel=u'时间', ylabel=u'收益',
                                             hold=False, yscale='log')
                else:
                    widget = BaseMatplotlibWidget(self)                    
                mainLayout.addWidget(widget, i, j)
                self.mplwidget_list.append(widget)
        self.setCentralLayout(mainLayout)
        
    def setCentralLayout(self, layout):
        self.mainWidget = QtGui.QWidget()
        self.mainWidget.setLayout(layout)
        self.setCentralWidget(self.mainWidget)
        
    def preprocessingData(self):
        self.stockWeightsDict = OrderedDict()
        for index, row in self.barra300.iterrows():     # 获取每行的index、row
            print("row number: ", index)
            stkId = row['Stock'][2:] + '.' + row['Stock'][:2]
            self.stockWeightsDict[stkId] = row['Weight']            
        print(self.stockWeightsDict)
        
        with open('initPrices_stored.dat') as initPriceFile:
            stockId_list = initPriceFile.readline().strip().split(',')
            price_list = initPriceFile.readline().strip().split(',')
            price_list = [float(p) for p in price_list]            
        self.stockInitPricesDict = OrderedDict(zip(stockId_list, price_list))        
        print(self.stockInitPricesDict)
        
        self.stockPositionsDict = OrderedDict()
        taken_money = 0.0
        for k in self.stockWeightsDict.keys():
            val = self.initValue*0.01*self.stockWeightsDict[k]
            min_trade_size = 100*self.stockInitPricesDict[k]*1.00003  # 万三的手续费
            position = int(val/min_trade_size)*100            
            self.stockPositionsDict[k] = position
            taken_money += position*self.stockInitPricesDict[k]*1.00003
        self.freeCash = self.initValue - taken_money        
        print(self.stockPositionsDict)
        print('self.freeCash', self.freeCash)
        
        self.tds_list = []        
        with open('data_stored.dat') as tickDataFile:            
            for i, line in enumerate(tickDataFile.readlines()):
                print('Processing line i: ', i)
                if i%3 == 0:
                    stk_id = line.strip()
                if i%3 == 1:
                    time_str_list = [s for s in line.strip().split(',')]                    
                    time_list = []
                    err_time_list = []
                    for s in time_str_list:
                        try:
                            time_str = s[:s.index('.')] if s.find('.')!=-1 else s
                            dt = datetime.strptime(time_str,  '%Y-%m-%d %H:%M:%S')
                            time_list.append(dt)
                        except:
                            err_time_list.append(s)
                    if len(err_time_list):
                        print('stk_id is ', stk_id, '\n', err_time_list)
                if i%3==2:
                    prices_line = line.strip()
                    if prices_line=='No Content':
                        print ('get in this branch')
                        prices_list = None
                        tds = TickDataSeries(stk_id, 
                                             [self.stockInitPricesDict[stk_id]], True)                
                    else:
                        prices_list = [float(s) for s in prices_line.split(',')]
                        print('prices_list is ', prices_list)
                        tickdata_list = []
                        for i in range(len(prices_list)):
                            tickdata_list.append((time_list[i], prices_list[i]))
                        tds = TickDataSeries(stk_id, tickdata_list)
                    self.tds_list.append(tds)        
        

        
    def generateValueList(self):
        self.value_list = []
        startTime = datetime(year=2017, month=1, day=25,
                         hour=9, minute=30, second=0)                         
#        endTime = datetime(year=2017, month=1, day=25,
#                       hour=9, minute=35, second=0)
                       
        endTime = datetime(year=2017, month=1, day=25,
                       hour=15, minute=0, second=0)
                       
#        startTime = datetime(datetime.today().year, 
#                         datetime.today().month,
#                         datetime.today().day, 
#                         hour=9, minute=30, second=0)
#        endTime = datetime(datetime.today().year, 
#                       datetime.today().month,
#                       datetime.today().day, 
#                       hour=15, minute=0, second=0)
                       
        currTime = startTime
        while currTime <= endTime:
            print('processing time', currTime)
            val = self.freeCash
            for tds in self.tds_list:
                stk_id = tds.stock_id
#                if stk_id!='600004.SH':
#                    continue
                position = self.stockPositionsDict[stk_id]
                price = tds.getNewestPriceByTime(currTime)
                if price==0.0:
                    price = self.stockInitPricesDict[stk_id]
                val += position*price                
            self.value_list.append(val)
            currTime += timedelta(seconds=1)
            if (startTime + timedelta(hours=2)) < currTime \
                    < (startTime + timedelta(hours=3, minutes=30)):
                currTime = startTime + timedelta(hours=3, minutes=30)
        
    def preprocessingData_111(self):
        self.stockWeightsDict = OrderedDict()
        for index, row in self.barra300.iterrows():     # 获取每行的index、row
            print("row number: ", index)
            stkId = row['Stock'][2:] + '.' + row['Stock'][:2]
            self.stockWeightsDict[stkId] = row['Weight']
            
        print(self.stockWeightsDict)            
        wndData = w.wss(list(self.stockWeightsDict.keys()), 
                        "close", "rptDate=20161230")
        self.stockInitPricesDict = OrderedDict(zip(self.stockWeightsDict.keys(), 
                                       wndData.Data[0]))
        print(self.stockInitPricesDict)
        with open('initPrices_stored.dat', 'w') as targetFile:
            stockIdList_str = ','.join(self.stockInitPricesDict.keys())
            prices_str = ','.join(str(p) for p in self.stockInitPricesDict.values())
            targetFile.write(stockIdList_str + '\n')
            targetFile.write(prices_str + '\n')
        
        self.stockPositionsDict = OrderedDict()
        taken_money = 0.0
        for k in self.stockWeightsDict.keys():
            val = self.initValue*0.01*self.stockWeightsDict[k]
            min_trade_size = 100*self.stockInitPricesDict[k]*1.00003  # 万三的手续费
            position = int(val/min_trade_size)*100            
            self.stockPositionsDict[k] = position
            taken_money += position*self.stockInitPricesDict[k]*1.00003
        self.freeCash = self.initValue - taken_money
        print(self.stockPositionsDict)
        print('self.freeCash', self.freeCash)
        
        
    def readWindData_111(self, stock_id):
        startTime = datetime(year=2017, month=1, day=25,
                         hour=9, minute=30, second=0)                         
        endTime = datetime(year=2017, month=1, day=25,
                       hour=15, minute=0, second=0)
        
        
#        startTime = datetime(datetime.today().year, 
#                         datetime.today().month,
#                         datetime.today().day, 
#                         hour=9, minute=30, second=0)
#        endTime = datetime(datetime.today().year, 
#                       datetime.today().month,
#                       datetime.today().day, 
#                       hour=15, minute=0, second=0)
                       
        data = w.wst(stock_id, "last", startTime, endTime)
        data_str = ','.join(str(d) for d in data.Data[0])
        time_str = ','.join(str(t) for t in data.Times)
                       
        with open('data_stored.dat', 'a') as targetFile:
            targetFile.write(stock_id + '\n')            
            targetFile.write(time_str + '\n')
            targetFile.write(data_str + '\n')            
        print('len(data.Data is ', len(data.Data[0]))
        print('len(data.Times is ', len(data.Times))
        print(data)


pf = open('F:\\working_prog\\pywsqdataif.data', 'w')
def DemoWSQCallback(indata):
    print('Intrigged by Call back of wind')
    print('indata is ', indata)
    print('indata.Fields is ', indata.Fields)
    lastvalue =""
    for k in range(0,len(indata.Fields)):
         if(indata.Fields[k] == "RT_TIME"):
             begintime = indata.Data[k][0];
         if(indata.Fields[k] == "RT_LAST"):
             print('indata.Fields[k] is "RT_LAST" value is ', indata.Data[k][0])
             lastvalue = str(indata.Data[k][0]);

    string = str(begintime) + " " + lastvalue +"\n"    
    pf.writelines(string)
    print(string)

def main():
    qApp = QtGui.QApplication(sys.argv)
    aw = MainWnd()
    aw.show()
    sys.exit(qApp.exec_())

if __name__=='__main__':
    w.start()
    
    w.wsq("600000.SH, 000001.SZ","rt_time, rt_last", func=DemoWSQCallback) #订阅浦发银行等股票当前行情信息
    
#    w.menu()
#    data = w.wst("600000.SH","last", datetime.today()-timedelta(0,2*3600), datetime.now())

#    w.wsq("600000.SH,000001.SZ","last") # 取浦发银行等股票当前行情信息
#    data=w.wsq("600000.SH","last",func=DemoWSQCallback) #订阅浦发银行等股票当前行情信息

#    w.wsq('600000.SH,600005.SH', "rt_last,rt_last_vol")  # 取浦发银行等股票当前行情信息
#    data=w.wsq('600000.SH,600005.SH', "rt_last,rt_last_vol", func=DemoWSQCallback) # 订阅浦发银行等股票当前行情信息
#    w.start()
#    print(datetime.today()-timedelta(0, 2*3600))
#    print(datetime.now()-timedelta(0, 2*3600))
    main()
#    data = w.wss("600000.SH,600005.SH,600004.SH,600007.SH, 300148.SZ","close","rptDate=20161230")
#    print(data.Times)
#    print(data.Data[0])
    