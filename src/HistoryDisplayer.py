# encoding: UTF-8
from __future__ import print_function

import sys
import os
import json
import threading
from collections import OrderedDict

import pandas as pd
from MatplotWidget import *

from datetime import datetime

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import CommonUtilityFunc
from CommonUtilityFunc import *
import GlobalVars

import time

from PyQt4 import QtGui, QtCore
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  #允许显示中文
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

class MongoDB_DataRecord_Error(Exception):
    pass

INDEX_SYMBOL_NAME_MAP = {'IF': u'沪深300指数', 'IC': u'中证500指数', 
                         'IH': u'上证50指数'}

class MatplotlibWidget_History(FigureCanvas):
    def __init__(self, parent=None, strategy_name='', title='',
                 xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=100, hold=False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
#        self.axes = self.figure.add_subplot(111)
        self.axes = self.figure.add_subplot(211)
        self.axex_twinx = self.axes.twinx()
        
        self.strategy_name = strategy_name
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        
        if xscale is not None:
            self.axes.set_xscale(xscale)
        if yscale is not None:
            self.axes.set_yscale(yscale)
            self.axex_twinx.set_yscale(yscale)
        if xlim is not None:
            self.axes.set_xlim(0, 240)
            self.axex_twinx.set_xlim(0, 240)
        if ylim is not None:
            self.axes.set_ylim(*ylim)
            self.axex_twinx.set_ylim(*ylim)
        self.axes.hold(hold)
        self.axex_twinx.hold(hold)

        FigureCanvas.__init__(self, self.figure)

        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, 
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def sizeHint(self):
        w, h = self.get_width_height()
        return QtCore.QSize(w, h)

    def minimumSizeHint(self):
        return QtCore.QSize(20, 20)
    
    def set_values_series(self, value_series):
        self.value_series = value_series
    
    def set_index_series(self, index_series):
        self.index_series = index_series
        
    def set_drawdown_series(self, drawdown_series):
        self.drawdown_series = drawdown_series
    
    def set_index_symbol(self, symbol):
        self.index_symbol = symbol
    
    def get_data(self):
        self.value_series = GlobalVars.history_values_series[self.strategy_name][0]
        self.index_series = GlobalVars.history_values_series[self.strategy_name][1]
        self.index_symbol = GlobalVars.history_values_series[self.strategy_name][3]
    
    def plot(self):
        if self.value_series.size==0:
            return
        self.axes.plot(self.value_series.index, self.value_series, color='r', 
                       label=u'策略净值')
        self.axes.hold(True)
        self.axes.plot(self.index_series.index, self.index_series, color='g', 
                       label=INDEX_SYMBOL_NAME_MAP[self.index_symbol])        
#        self.axes.legend(fontsize='small', loc='upper right')
        self.axes.legend(fontsize='medium', loc='upper left')
        self.axes.set_title(self.title)
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)
        self.axex_twinx.set_ylim(self.axes.get_ylim())
        self.axes.grid(True)
        
        self.axes = self.figure.add_subplot(212)
        self.axex_twinx = self.axes.twinx()
        self.axes.plot(self.drawdown_series.index, 
                               self.drawdown_series, color='y', 
                               label=self.index_symbol)
        self.axes.set_xlabel(u'时间')
        self.axes.set_ylabel(u'净值回撤率')
        self.axex_twinx.set_ylim(self.axes.get_ylim())
        
        self.axes.grid(True)
        self.axes.hold(False)
        
    
    
class InfoLabel(QtGui.QLabel):
    def __init__(self, parent=None):
        QtGui.QLabel.__init__(self, parent)
        font = QFont()  
        font.setFamily("Helvetica")  
        fontHeight = 12  
        font.setPixelSize(fontHeight)  
        font.setBold(True)  
        self.setFont(font)  
        

class HistoryDisplayerWnd(QtGui.QMainWindow):
    def __init__(self, strategy_name='', parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.strategy_name = strategy_name
        self.index_symbol = ''
        self.parent = parent
        self.setWindowTitle(u'策略历史展示') 
        
        label1 = InfoLabel(u'历史最大回撤: ')
        self.max_drawdown_label = InfoLabel('12%')        
        label2 = InfoLabel(u'当前回撤: ')
        self.current_drawdown_label = InfoLabel('3%')
        label3 = InfoLabel(u'累计收益: ')
        self.max_earnning_label = InfoLabel('4%')
        label4 = InfoLabel(u'本月收益: ')
        self.month_earnning_label = InfoLabel('1.3%')
        
        space_width = 25
        lLayout = QtGui.QHBoxLayout()
        lLayout.addStretch()
        lLayout.addWidget(label1)
        lLayout.addWidget(self.max_drawdown_label)
        lLayout.addSpacing(space_width)
        lLayout.addWidget(label2)
        lLayout.addWidget(self.current_drawdown_label)
        lLayout.addSpacing(space_width)
        lLayout.addWidget(label3)
        lLayout.addWidget(self.max_earnning_label)
        lLayout.addSpacing(space_width)
        lLayout.addWidget(label4)
        lLayout.addWidget(self.month_earnning_label)
        lLayout.addStretch()
        
        self.widget = MatplotlibWidget_History(self, 
                            strategy_name=strategy_name,
                            title=strategy_name,
                            xlabel=u'时间', ylabel=u'收益',
                            hold=False, yscale='linear',
                            xlim=range(0, 241))        
        self.canvasTB = NavigationToolbar(self.widget, self)
        
        vLayout = QtGui.QVBoxLayout()    
        vLayout.addLayout(lLayout)
        vLayout.addWidget(self.canvasTB)
        vLayout.addWidget(self.widget)        
        self.setCentralLayout(vLayout)    
        
        
    def setCentralLayout(self, layout):
        self.mainWidget = QtGui.QWidget()
        self.mainWidget.setLayout(layout)
        self.setCentralWidget(self.mainWidget)
        
        
    def plot(self):
#        self.current_date_str = date_str
        self.get_strategy_data()
        print('In plot() get new data')
        self.compute()
        self.widget.set_values_series(self.value_series)
        self.widget.set_index_series(self.index_series)
        self.widget.set_drawdown_series(self.drawdown_series)
        self.widget.set_index_symbol(self.index_symbol)
        self.widget.plot()
        
        
    def get_strategy_data(self):
        self.value_series = GlobalVars.history_values_series[self.strategy_name][0]
        self.index_series = GlobalVars.history_values_series[self.strategy_name][1]
        self.drawdown_series = GlobalVars.history_values_series[self.strategy_name][2]
        self.index_symbol = GlobalVars.history_values_series[self.strategy_name][3]        
        
    
    def compute(self):
        max_drawdown_rate = (self.drawdown_series.max() if 
                               len(self.drawdown_series)>0 else 0)
        content = str(round(max_drawdown_rate*100, 2)) + '%'
        self.max_drawdown_label.setText(content)
        content = str(round(self.drawdown_series[-1]*100, 2)) + '%'
        print('current drawdown is ', self.drawdown_series[-1])
        self.current_drawdown_label.setText(content)
        earnning = self.value_series[-1]/self.value_series[0]-1.0
        print('In compute() earnning is ', earnning)
        content = str(round(earnning*100, 2)) + '%'
        self.max_earnning_label.setText(content)
        earnning_ratio = self.compute_month_earnning()
        print('In compute() earnning_ratio is ', earnning_ratio)
        content = str(round(earnning_ratio*100, 2)) + '%'
        self.month_earnning_label.setText(content)
        
    def compute_month_earnning(self):
        now = datetime.now()
        first_day = datetime(now.year, now.month, 1)
        month_first_day = first_day.strftime('%Y-%m-%d')
        val = self.value_series[self.value_series.index<month_first_day][-1]
        return self.value_series[-1]/val-1.0           
            
    
if __name__=='__main__':
#    get_value_series('./positions_val_series.csv')
    series = pd.Series([22, 33, 44, 55, 66], index=['3', '4', '6', '7', '9'])
    
    print(series['5':][0])
    for val in series:
        print(val)
#    series = pd.Series()
    max_drawdown_rate = series.max() if len(series) > 0 else 0
    print(max_drawdown_rate)
#    series /= series[0]
#    print(series)
    
    
#    line_up, = plt.plot([1,2,3], label='Line 2')
#    line_down, = plt.plot([3,2,1], label='Line 1')
#    plt.legend(handles=[line_up, line_down])
    
#    max_drawdown_rate = 0.233359
#    content = str(round(max_drawdown_rate*100, 3)) + '%'
#    print(content)
    

    
#    series = pd.Series([22, 33, 44, 55, 66], index=['a', 'b', 'c', 'd', 'e'])
#    for i in range(len(series)):
#        print(series[i])
        
#    line_up, = plt.plot(series, label='Line 2')
#    line_down, = plt.plot(series, label='Line 1')
#    plt.legend(handles=[line_up, line_down])
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    