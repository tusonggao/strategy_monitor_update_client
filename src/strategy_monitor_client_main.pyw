# encoding: UTF-8
from __future__ import print_function

import sys
import os
import json
import threading
import requests
from collections import OrderedDict
from pprint import pprint
import functools

from pandas import Series, DataFrame
import pandas as pd
from MatplotWidget import *

from datetime import datetime

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from StrategyPositionsDisplayer import StrategyPositionsDisplayer
from HistoryDisplayer import HistoryDisplayerWnd
import CommonUtilityFunc
from CommonUtilityFunc import *
import GlobalVars

import time


class MaximizedWnd(QtGui.QMainWindow):
    def __init__(self, x, y, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u'策略实时监控')
        
        showPosBtn = QtGui.QPushButton(u"当前持仓明细")
        showPosBtn.setToolTip(u"显示当前持仓")   #Tool tip
#        self.connect(showPosBtn, QtCore.SIGNAL('clicked()'), 
#                     functools.partial(self.onShowPositionsBtnClicked,
#                     i, j))
        
        zoomBtn = QtGui.QPushButton()
        zoomBtn.setToolTip(u"缩小")   #Tool tip
        zoomBtn.setIcon(QIcon('zoom_in.jpg'))
        zoomBtn.setIconSize(QtCore.QSize(10, 7))
        self.connect(zoomBtn, QtCore.SIGNAL('clicked()'), 
                     self.onZoomBtnClicked)
                             
        vlLayout = QtGui.QHBoxLayout()
        vlLayout.addStretch()
        vlLayout.addWidget(showPosBtn)
        vlLayout.addWidget(zoomBtn)
        
        self.partner_widget = parent.widget_map[(x, y)]
        self.widget = StockBarraMplWidget(self, 
                            strategy_name=self.partner_widget.strategy_name,
                            title=self.partner_widget.strategy_name,
                            xlabel='', ylabel=u'收益百分比',
                            hold=False, yscale='linear',
                            xlim=range(0, 241) )
        self.widget.ystick_num = 41
        
        self.canvasTB = NavigationToolbar(self.widget, self)
        
        vLayout = QtGui.QVBoxLayout()
        vLayout.addWidget(self.canvasTB)
        vLayout.addWidget(self.widget)
        vLayout.addLayout(vlLayout)
#        self.setLayout(vLayout)
        self.setCentralLayout(vLayout)
        
        
    def onZoomBtnClicked(self):
        self.parent.resize(self.width(), self.height())
        self.parent.move(self.x(), self.y())
        if self.isMaximized():
            self.parent.showMaximized()
#        self.close()
        self.hide()
        self.parent.show()

    def setCentralLayout(self, layout):
        self.mainWidget = QtGui.QWidget()
        self.mainWidget.setLayout(layout)
        self.setCentralWidget(self.mainWidget)
        
    def plot(self):
        begin_t = time.time()
        self.widget.copyData(self.partner_widget)
        self.widget.plot()
        end_t = time.time()
        print('In MaximizedWnd plot() cost %.9f sec'%(end_t-begin_t))
        
    def closeEvent(self, event):
        self.parent.show()
        

class InfoLabel(QtGui.QLabel):
    def __init__(self, parent=None):
        QtGui.QLabel.__init__(self, parent)
        font = QFont()  
        font.setFamily("Helvetica")
        fontHeight = 12
        font.setPixelSize(fontHeight)  
        font.setBold(True)
        self.setFont(font) 
        
        
        
class MainWnd(QtGui.QMainWindow):
    def __init__(self, setting_file):
        QtGui.QMainWindow.__init__(self)
        self.showMaximized()
        self.setWindowTitle(u'策略实时监控_Updated_Client_v2')
        
        self.setting_file = setting_file
        self.timeoutCount = 0
        self.strategy_position_shower_map = {}
        self.strategy_MatplotlibWidget_map = {}
        self.strategy_zoomBtn_map = {}
        self.strategy_showPosBtn_map = {}
        self.strategy_showHistoryBtn_map = {}
        
        self.max_drawdown_label_map = {}
        self.current_drawdown_label_map = {}
        self.year_earnning_label_map = {}
        self.month_earnning_label_map = {}
                
        self.maxWnd_map = {}
        self.historyWnd_map = {}
        self.subPlt_xNum = 4
        self.subPlt_yNum = 2
        self.maxShowed = False
        self.inRealtimeState = True
        self.inHistoryPlotState = False
        self.plot_cleared = False
        self.calculated_date_str = ''
        self.current_date_str = datetime.today().strftime('%Y-%m-%d')
        self.today_date_str = datetime.today().strftime('%Y-%m-%d')
        
        self.used_widgets_list = []
        self.widget_map = {}
        
        self.read_server_setting()
        CommonUtilityFunc.getHistoryValueSeries(self.server_ip, self.server_port)
        
        self.initWidgets()
        self.initUi()

        self.onShowBtnClicked()
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.plot_on_timer)
        self.timer.start(7000)
        
    def initWidgets(self):
        self.hedgeTargetLabel = QtGui.QLabel(u'对冲标的: ')
        self.hedgeTargetComboBox = QtGui.QComboBox()
        self.hedgeTargetComboBox.addItems([u'期货', u'指数'])
        self.hedgeTargetComboBox.setCurrentIndex(1)
        self.hedgeTarget_type = 'Index'
        
        self.legendPosLabel = QtGui.QLabel(u'图例位置: ')
        self.legendPosComboBox = QtGui.QComboBox()
        self.legendPosComboBox.addItems([u'上左', u'上中', u'上右',
                                         u'下左', u'下中', u'下右'])
        self.setInitLegendPos()
        self.legendPosComboBox.setCurrentIndex(2)
        self.legendPosComboBoxCurrentIndex = 2
                                        
        self.dateLabel = QtGui.QLabel(u'选定日期:')
        now = datetime.now()
#        self.dateEdit = QtGui.QDateEdit(QtCore.QDate(now.year, 
#                                        now.month, now.day))
        self.dateEdit = QtGui.QDateEdit()        
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDisplayFormat('yyyy-MM-dd')
        self.dateEdit.setDate(QtCore.QDate(now.year, now.month, now.day))
        self.dateEdit.setDateRange(QtCore.QDate(now.year-1, now.month, now.day),
                                   QtCore.QDate.currentDate())
        self.todayCheckBox = QtGui.QCheckBox(u'今天')
        self.todayCheckBox.setChecked(True)
        self.showBtn = QtGui.QPushButton(u'显示')
        
        self.dateEdit.dateChanged.connect(self.onDateEditChanged)
        self.connect(self.hedgeTargetComboBox, QtCore.SIGNAL('activated(int)'), 
                     self.changeHedgeTarget)
        self.connect(self.legendPosComboBox, QtCore.SIGNAL('activated(int)'), 
                     self.changeLegendPos)
        self.connect(self.todayCheckBox, QtCore.SIGNAL('stateChanged(int)'), 
                     self.onTodayCheckBoxChecked)
        self.connect(self.showBtn, QtCore.SIGNAL('clicked()'), 
                     self.onShowBtnClicked)
        
        self.get_strategy_names_from_mongodb()
        print('after get_strategy_names_from_mongodb self.strategy_names is ', 
              self.strategy_names)
                
        self.used_Num = len(self.strategy_names)
                
        count = 0
        for i in range(self.subPlt_xNum):
            for j in range(self.subPlt_yNum):
                if count < self.used_Num:
                    widget = StockBarraMplWidget(parent=self, 
                                    strategy_name=self.strategy_names[count],
                                    title=self.strategy_names[count],
                                    xlabel='', ylabel=u'收益',
                                    hold=False, yscale='linear', 
                                    xlim=range(0, 241) )
                    self.used_widgets_list.append(widget)
                    self.widget_map[(i, j)] = widget
                    count += 1
                else:
                    widget = MatplotlibWidget(self)                
                self.strategy_MatplotlibWidget_map[(i, j)] = widget
                
                showPositionsBtn = QtGui.QPushButton(u"当前持仓")
                showPositionsBtn.setToolTip(u"显示当前持仓")   #Tool tip
                self.connect(showPositionsBtn, QtCore.SIGNAL('clicked()'), 
                             functools.partial(self.onShowPositionsBtnClicked,
                             i, j))
                self.strategy_showPosBtn_map[(i, j)] = showPositionsBtn
                
                showHistoryBtn = QtGui.QPushButton(u"历史表现")
                showHistoryBtn.setToolTip(u"显示策略历史表现")   #Tool tip
                self.connect(showHistoryBtn, QtCore.SIGNAL('clicked()'), 
                             functools.partial(self.onShowHistoryClicked,
                             i, j))
                self.strategy_showHistoryBtn_map[(i, j)] = showHistoryBtn
                
                zoomBtn = QtGui.QPushButton()
                zoomBtn.setToolTip(u"放大")   #Tool tip
                zoomBtn.setIcon(QIcon('zoom_in.jpg'))
                zoomBtn.setIconSize(QtCore.QSize(10, 7))
                self.connect(zoomBtn, QtCore.SIGNAL('clicked()'), 
                             functools.partial(self.onZoomBtnClicked, i, j))
                self.strategy_zoomBtn_map[(i, j)] = zoomBtn
                
                
    def initUi(self):
        mainLayout = QtGui.QVBoxLayout()
        
        lLayout = QtGui.QHBoxLayout()
        lLayout.addWidget(self.hedgeTargetLabel)
        lLayout.addSpacing(10)
        lLayout.addWidget(self.hedgeTargetComboBox)
        lLayout.addSpacing(10)
        lLayout.addWidget(self.legendPosLabel)
        lLayout.addSpacing(10)
        lLayout.addWidget(self.legendPosComboBox)
        lLayout.addSpacing(10)
        lLayout.addStretch()
        lLayout.addWidget(self.dateLabel)
        lLayout.addSpacing(10)
        lLayout.addWidget(self.dateEdit)
        lLayout.addSpacing(10)
        lLayout.addWidget(self.todayCheckBox)
        lLayout.addSpacing(10)
        lLayout.addWidget(self.showBtn)
        lLayout.addStretch()
        
        mainLayout.addLayout(lLayout)

        gridLayout = QtGui.QGridLayout()        
        for i in range(self.subPlt_xNum):
            for j in range(self.subPlt_yNum):
                hLayout = QtGui.QHBoxLayout()
                label1 = InfoLabel(u'历史最大回撤: ')
                self.max_drawdown_label_map[(i, j)] = InfoLabel('0.0%')
                
                label2 = InfoLabel(u'当前回撤: ')
                self.current_drawdown_label_map[(i, j)] = InfoLabel('0.0%')
                label3 = InfoLabel(u'年初至今收益: ')
                self.year_earnning_label_map[(i, j)] = InfoLabel('0.0%')
                label4 = InfoLabel(u'本月收益: ')
                self.month_earnning_label_map[(i, j)] = InfoLabel('0.0%')
                
                space_width = 25
                hLayout.addStretch()
                hLayout.addWidget(label1)
                hLayout.addWidget(self.max_drawdown_label_map[(i, j)])
                hLayout.addSpacing(space_width)
                hLayout.addWidget(label2)
                hLayout.addWidget(self.current_drawdown_label_map[(i, j)])
                hLayout.addSpacing(space_width)
                hLayout.addWidget(label3)
                hLayout.addWidget(self.year_earnning_label_map[(i, j)])
                hLayout.addSpacing(space_width)
                hLayout.addWidget(label4)
                hLayout.addWidget(self.month_earnning_label_map[(i, j)])
                hLayout.addStretch()
                
                showPositionsBtn = self.strategy_showPosBtn_map[(i, j)]
                showHistoryBtn = self.strategy_showHistoryBtn_map[(i, j)]
                zoomBtn = self.strategy_zoomBtn_map[(i, j)]
                
                hLayout.addWidget(showPositionsBtn)
                hLayout.addWidget(showHistoryBtn)
                hLayout.addWidget(zoomBtn)
                
                vLayout = QtGui.QVBoxLayout()
                vLayout.addWidget(self.strategy_MatplotlibWidget_map[(i, j)])
                vLayout.addLayout(hLayout)
                
                gridLayout.addLayout(vLayout, i, j)
                
        mainLayout.addLayout(gridLayout)
        self.setCentralLayout(mainLayout)
        print('In initUi self.max_drawdown_label_map.keys() is',
                      self.max_drawdown_label_map.keys())
        
    def changeHedgeTarget(self, index_int):
        begin_t = time.time()
        hedgeTarget_type = 'Future' if index_int==0 else 'Index'
        if self.hedgeTarget_type != hedgeTarget_type:
            self.hedgeTarget_type = hedgeTarget_type
            for widget in self.used_widgets_list:
                widget.changeHedgeTargetPlot(hedgeTarget_type)
        end_t = time.time()
        print('In MainWnd changeHedgeTarget cost time %.7f sec'%(end_t-begin_t))
        
    def changeLegendPos(self, index_int):
        begin_t = time.time()
        if index_int != self.legendPosComboBoxCurrentIndex:
            self.legendPosComboBoxCurrentIndex = index_int
            for widget in self.used_widgets_list:
                widget.changeLegendPosPlot(index_int)
        end_t = time.time()
        print('In MainWnd changeLegendPos cost time %.7f sec'%(end_t-begin_t))
        
    def setInitLegendPos(self):
        now = datetime.now()
        if now<=datetime(now.year, now.month, now.day, 14, 45, 0):
            self.legendPosComboBox.setCurrentIndex(2)
            self.legendPosComboBoxCurrentIndex = 2
        else:
            self.legendPosComboBox.setCurrentIndex(0)
            self.legendPosComboBoxCurrentIndex = 0
    
    def update_label_content(self, date_str):
        date = datetime.strptime(date_str, '%Y-%m-%d')
        try:
            for i, j in self.max_drawdown_label_map:
                if (i, j) not in self.widget_map:
                    continue
                widget = self.widget_map[(i, j)]
                strategy_name = widget.strategy_name
                if strategy_name not in GlobalVars.history_values_series:
                    continue
                value_series = GlobalVars.history_values_series[strategy_name][0]
                value_series = value_series[:date_str]
                drawdown_series = GlobalVars.history_values_series[strategy_name][2]
                drawdown_series = drawdown_series[:date_str]
                
                today_ratio = widget.value_series_index[-1]*0.01
                current_drawdown_rate = 1-(1-drawdown_series[-2])*(1+today_ratio)
                if current_drawdown_rate<0:
                    current_drawdown_rate = 0
                label_text = str(round(current_drawdown_rate*100, 2)) + '%'
                self.current_drawdown_label_map[(i, j)].setText(label_text)
                
                max_drawdown_rate = drawdown_series.max()
                if max_drawdown_rate < current_drawdown_rate:
                    max_drawdown_rate = current_drawdown_rate
                label_text = str(round(max_drawdown_rate*100, 2)) + '%'
                self.max_drawdown_label_map[(i, j)].setText(label_text)  
                
    
                year_first_day = datetime(date.year, 1, 1)
                year_first_day = year_first_day.strftime('%Y-%m-%d')   
                
                month_first_day = datetime(date.year, date.month, 1)
                month_first_day = month_first_day.strftime('%Y-%m-%d')
                
                last_year_val = value_series[value_series.index<year_first_day][-1]
                last_month_val = value_series[value_series.index<month_first_day][-1]
                last_day_val = value_series[value_series.index<date_str][-1]
                newest_value = last_day_val*(1+today_ratio)
                
                year_earnning = newest_value/last_year_val - 1.0
                label_text = str(round(year_earnning*100, 2)) + '%'
                self.year_earnning_label_map[(i, j)].setText(label_text)          
                
                month_earnning = newest_value/last_month_val - 1.0
                label_text = str(round(month_earnning*100, 2)) + '%'
                self.month_earnning_label_map[(i, j)].setText(label_text)
        except:
            pass    
            
    def onDateEditChanged(self, newDate):
        if newDate==QtCore.QDate.currentDate():
            self.todayCheckBox.setChecked(True)
        else:
            self.todayCheckBox.setChecked(False)
                   
    def onTodayCheckBoxChecked(self, state):
        if state:
            self.dateEdit.setDate(QtCore.QDate.currentDate())
    
    def checkCurrentState(self):
        begin_t = time.time()
        trading_days = CommonUtilityFunc.getTradingDays(self.current_date_str)
        print('In checkCurrentState self.current_date_str is', self.current_date_str)
        
        if self.current_date_str not in trading_days:
            self.state = 'no_trading'
        elif self.dateEdit.date()!=QtCore.QDate.currentDate():
            self.state = 'history'
        else:
            now = datetime.now()
            trding_start_t = datetime(now.year, now.month, now.day, 9, 28, 30)
            trading_end_t = datetime(now.year, now.month, now.day, 15, 31, 30)
            if trding_start_t <= now <= trading_end_t:
                self.state = 'realtime'
            else:
                self.state = 'history'
        end_t = time.time()
        print('In checkCurrentState state is ', self.state,
              'cost time %.9f sec'%(end_t-begin_t))
        
        return self.state 
        
    def showHistoryPlot(self, date_str):
        begin_t1 = time.time()
        if date_str==self.calculated_date_str:
            return
        self.clearAllShownPlot()
        end_t1 = time.time()        
        self.calculated_date_str = date_str
        begin_t2 = time.time()
        for widget in self.used_widgets_list:
             widget.normal_plot(date_str)    
        self.plot_cleared = False
        self.update_label_content(date_str)
        end_t2 = time.time()
        print('In showHistoryPlot: cost time1: %.9f sec'%(end_t1-begin_t1),
              'cost time2: %9.f sec'%(end_t2-begin_t2))
    
    def showRealtimePlot(self, date_str):
        for widget in self.used_widgets_list:
             widget.normal_plot(date_str)
        self.update_label_content(date_str)
        self.plot_cleared = False
        self.calculated_date_str = ''
        
    def clearAllShownPlot(self):
        if self.plot_cleared==False:
            for widget in self.used_widgets_list:
                widget.clear_plot() 
            self.plot_cleared = True
            self.calculated_date_str = ''
            
    
    def onShowBtnClicked(self):
        begin_t = time.time()
        
        date_str = self.dateEdit.date().toString('yyyy-MM-dd')
        self.current_date_str = date_str
        print('In plot_on_timer self.current_date_str is', self.current_date_str)
        self.plot_on_timer()
        
        end_t = time.time()
        print('In onShowBtnClicked: cost time: %.9f sec'%(end_t-begin_t))
        
    
    def plot_on_timer(self):
        if self.is_in_realtime_mode():
            self.showRealtimePlot(self.current_date_str)            
        else:
            self.showHistoryPlot(self.current_date_str)       
            

    def is_in_realtime_mode(self):
        now = datetime.now()
        if self.today_date_str != now.strftime('%Y-%m-%d'):
            self.dateEdit.setDateRange(QtCore.QDate(now.year-1, now.month, 
                                  now.day), QtCore.QDate.currentDate())
            self.today_date_str = now.strftime('%Y-%m-%d')
            
        if self.current_date_str!=datetime.today().strftime('%Y-%m-%d'):
            return False
        
        am_start_t = datetime(now.year, now.month, now.day, 9, 28, 30)
        am_end_t = datetime(now.year, now.month, now.day, 11, 31, 0)
        pm_start_t = datetime(now.year, now.month, now.day, 12, 59, 0)
        pm_end_t = datetime(now.year, now.month, now.day, 15, 31, 30)
        return am_start_t <= now <= am_end_t or pm_start_t <= now <= pm_end_t
        

    def removeAllChildLayout(self, parentLayout):
        layouts = parentLayout.findChildren(QtGui.QLayout)
        for layout in layouts:
            self.removeAllChildLayout(layout)
            QtGui.QWidget().setLayout(layout)
            
        
    def bringToTopMost(self, window):
        window.setWindowState(window.windowState() & ~
                              QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        window.activateWindow()
        
    
    def read_server_setting(self):
        with open(self.setting_file) as f:
            data = json.load(f)
            self.server_ip = data['server_ip']
            self.server_port = data['server_port']
            
    
    def get_strategy_names_from_mongodb(self, date_str=None):
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        client = pymongo.MongoClient('mongodb://' + self.server_ip + ':' + 
                                     str(self.server_port) + '/')
        mydb = client['Meses_Strategy_Monitor_Updated']
        collection = mydb['monitor_strategy']
        filter_criteria = {'date': date_str}
        results = collection.find(filter_criteria)
        flag = False
        for res in results:
            self.strategy_names = json.loads(res['strategy_names'])
            print('self.strategy_names is ', self.strategy_names)
            flag = True
        if flag==False:
            raise ValueError('Cannot find strategy names')
        
    def onShowPositionsBtnClicked(self, x, y):
        pass
        
    def onShowHistoryClicked(self, x, y):
        if (x, y) not in self.widget_map:
            return
        if (x, y) not in self.historyWnd_map:
            widget = self.widget_map[(x, y)]
            strategy_name = widget.strategy_name
            print('Strategy_name is ', strategy_name)
            self.historyWnd_map[(x, y)] = HistoryDisplayerWnd(strategy_name, self)
            
        self.historyWnd_map[(x, y)].plot()
        self.historyWnd_map[(x, y)].resize(self.width(), self.height())
        self.historyWnd_map[(x, y)].move(self.x(), self.y())
        if self.isMaximized():
            self.historyWnd_map[(x, y)].showMaximized()
        self.historyWnd_map[(x, y)].show()
        print('In onShowHistoryClicked ', x, y)
        
    def onZoomBtnClicked(self, x, y):
        print('ZoomBtnClicked x y', x, y)
        if (x, y) not in self.widget_map:
            return
        if (x, y) not in self.maxWnd_map:
            self.maxWnd_map[(x, y)] = MaximizedWnd(x, y, self)
        
        self.maxWnd_map[(x, y)].plot()
        self.maxWnd_map[(x, y)].resize(self.width(), self.height())
        self.maxWnd_map[(x, y)].move(self.x(), self.y())
        if self.isMaximized():
            self.maxWnd_map[(x, y)].showMaximized()
        self.maxWnd_map[(x, y)].show()
        self.hide()
        
    def setCentralLayout(self, layout):
        self.mainWidget = QtGui.QWidget()
        self.mainWidget.setLayout(layout)
        self.setCentralWidget(self.mainWidget)
                 
    def closeEvent(self, event):
        """关闭事件"""
        reply = QtGui.QMessageBox.question(self, u'退出',
                   u'确认退出?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
                   QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main(setting_file):
    qApp = QtGui.QApplication(sys.argv)
    aw = MainWnd(setting_file)
    aw.show()
    sys.exit(qApp.exec_())


if __name__=='__main__':
    setting_file = '.\\server_setting.json'    
    main(setting_file)
    
    
#    dict_ = {"2017-04-24": 47152979.3210138828, "2017-04-25": 46961120.7568461001,
#              "2017-04-26": 46564626.5416167304, "2017-04-27": 46637986.3332286179,
#              "2017-04-28": 46975763.478076987,  "2017-05-02": 47148556.4739719778}
#    month_first_day = '2017-05-02'
#    value_series = pd.Series(dict_)
#    
#    sub_series = value_series[value_series.index <= month_first_day]
#    newest_value = value_series[month_first_day:][0]
#    print(sub_series)
    
#    run_game()   
    
    
    
#    arr = np.arange(12.).reshape((3, 4))
#    print(arr)

    
#    data = {'state': ['Ohio', 'Ohio', 'Ohio', 'Nevada', 'Nevada'],
#            'year': [2000, 2001, 2002, 2001, 2002],
#            'pop': [1.5, 1.7, 3.6, 2.4, 2.9],
#            'pop1': 3.3}
#    frame = DataFrame(data, columns=['year', 'state', 'pop', 'debt'],
#                      index=['one', 'two', 'three', 'four', 'five'])
#    pprint(data)
#    
#    url = 'https://github.com/timeline.json'
#    r = requests.get(url)
#    json_obj = r.json()
#    repos = set()
#    for entry in json_obj:
#        try:
#            repos.add(entry['repository']['url'])
#        except KeyError as e:
#            print('No Key')
#    pprint(repos)
    
#    frame = DataFrame(data, index=['one', 'two', 'three', 'four', 'five'])
#    for index in frame.columns:
#        print(index)
##    print(frame.transpose())
#    
#    pop = {'Nevada': {2001: 2.4, 2002: 2.9, 1: 27},
#           'Ohio': {2000: 1.5, 1: 99, 2001: 1.7, 2002: 3.6, 4: 3.3}}
#    frame = DataFrame(pop)
#    frame.index.name = 'year'; frame.columns.name = 'state'
#    
#    obj = Series([4.5, 7.2, -5.3, 3.6], index=['d', 'b', 'a', 'c'])
##    obj = obj.reindex(['a', 'b', 'c', 'd'])
#    print(obj)
#    obj.index = ['dd', 'bb', 'aa', 'cc']
#    print(obj)
#    
#    frame = DataFrame(np.arange(9).reshape((3, 3)), index=['a', 'c', 'd'],
#                      columns=['Ohio', 'Texas', 'California'])
##    frame = frame.reindex(['a', 'b', 'c', 'd'])
#    print(frame.ix[['a', 'b', 'c', 'd'], ['Texas']])
    

    


    
    