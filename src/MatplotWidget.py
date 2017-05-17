import numpy as np
import pandas as pd

import time
import pymongo
from datetime import datetime
import CommonUtilityFunc
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

class MatplotlibWidget(FigureCanvas):
    def __init__(self, parent=None, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=100, hold=False):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        self.axex_twinx = self.axes.twinx()
        
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlim(0, 240)
        self.axes.set_xticks([0, 60, 120, 180, 240])
        self.axes.set_xticklabels(['9:30', '10:30', '11:30', '14:00', '15:00'])
        
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
        
class StockBarraMplWidget(MatplotlibWidget):    
    def __init__(self, parent=None, strategy_name=None, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 width=4, height=3, dpi=100, hold=False):
        self.parent = parent
        self.current_legend_pos = 'upper right'
        self.strategy_name = strategy_name
        self.current_date_str = datetime.now().strftime('%Y-%m-%d')
        self.hedge_target_type = 'Index'
        self.ystick_num = 11.0
        super(StockBarraMplWidget, self).__init__(parent, title, 
                 xlabel, ylabel, xlim, ylim, xscale, yscale,
                 width, height, dpi, hold)
    
    def copyData(self, widget_obj):
        self.current_legend_pos = widget_obj.current_legend_pos
        self.strategy_name = widget_obj.strategy_name
        self.current_date_str = widget_obj.current_date_str
        self.hedge_target_type = widget_obj.hedge_target_type
        self.hedge_index_type = widget_obj.hedge_index_type
        self.value_series = widget_obj.value_series
        self.future_series = widget_obj.future_series
        self.index_series = widget_obj.index_series
        self.x_stick_list = widget_obj.x_stick_list
        self.future_id = widget_obj.future_id
        
    
    def clearPrevData(self):
        self.value_series = pd.Series()
        self.value_series_index = pd.Series()
        self.value_series_future = pd.Series()
        self.future_series = pd.Series()
        self.index_series = pd.Series()
        self.x_stick_list = []
        
        
    def changeHedgeTargetPlot(self, hedge_target_type):
        if hedge_target_type==self.hedge_target_type:
            return
        if hedge_target_type=='Index':
            self.value_series = self.value_series_index
        else:
            self.value_series = self.value_series_future            
        self.x_stick_list = list(range(self.value_series.size))
        self.hedge_target_type = hedge_target_type
        self.plot()
    
    def changeLegendPosPlot(self, index):
        pos_list = ['upper left', 'upper center','upper right',
                    'lower left', 'lower center', 'lower right']
        if pos_list[index]!=self.current_legend_pos:
            self.current_legend_pos = pos_list[index]
            self.plot()
    
    def normal_plot(self, date_str):
        self.current_date_str = date_str
        begin_t = time.time()
        self.get_data_from_mongodb()
        self.plot()
        end_t = time.time()
        print('normal_plot cost time %.7f sec'%(end_t-begin_t))
    
    def clear_plot(self):
        self.clearPrevData()
        self.plot()
    
    def get_data_from_mongodb(self):
        server_ip = self.parent.server_ip
        server_port = self.parent.server_port
        client = pymongo.MongoClient('mongodb://' + server_ip + ':' + 
                                     str(server_port) + '/')
        mydb = client['Meses_Strategy_Monitor_Updated']
        collection = mydb['monitor_record']
        filter_criteria = {'strategy_name': self.strategy_name,
                           'date': self.current_date_str}
        counter = CommonUtilityFunc.find_in_MongoDB(collection, filter_criteria)
        
        if counter>1:
            raise MongoDB_DataRecord_Error('already exists too much record')
        elif counter==1:
            results = collection.find(filter_criteria)
            for res in results:
                self.value_series_index = pd.read_json(res['value_series_index'],
                                                       typ='series')
                self.value_series_future = pd.read_json(res['value_series_future'],
                                                        typ='series')
                self.index_series = pd.read_json(res['index_series'],
                                                 typ='series')
                self.future_series = pd.read_json(res['future_series'],
                                                  typ='series')
                self.hedge_index_type = res['hedge_index_type']
                self.future_id = res['hedge_index_future_id']
                print('client get new data from mongodb')
            if self.hedge_target_type=='Index':
                self.value_series = self.value_series_index
            else:
                self.value_series = self.value_series_future
            self.x_stick_list = list(range(len(self.value_series)))
        else:
            self.clearPrevData()
        
        
    def plot(self):
        if self.value_series.size==0:
            self.default_plot = True
            self.ystick_min = -0.05
            self.ystick_max = 0.05
            self.ystick_list = np.arange(-0.05, 0.05, 0.01)
        else:
            self.default_plot = False
            min_v = min(self.value_series.min(), self.future_series.min(),
                        self.index_series.min())
            max_v = max(self.value_series.max(), self.future_series.max(),
                        self.index_series.max())
            vrange = max_v - min_v
            self.ystick_min = round(min_v - vrange*0.1, 4)
            self.ystick_max = round(max_v + vrange*0.1, 4)
            ystick_step = (self.ystick_max-self.ystick_min)/self.ystick_num
            if ystick_step==0.0:
                return
            ll = list(np.arange(0.0-ystick_step, self.ystick_min, -ystick_step))
            ll.reverse()
            self.ystick_list = ll + list(np.arange(0.0, 
                                        self.ystick_max, ystick_step))

        if self.default_plot:
            self.axes.plot(self.x_stick_list, self.value_series, color='r')
        else:
            self.axes.plot(self.x_stick_list, self.value_series, color='r', 
                           label=u'对冲后净值')
            
        self.axex_twinx.plot()
        self.axes.hold(True)
        self.axex_twinx.hold(True)
        self.axex_twinx.plot()

        if self.default_plot:
            self.axes.plot(self.x_stick_list, self.future_series, color='g')
            self.axes.plot(self.x_stick_list, self.index_series, color='y')
            
        else:
            self.axes.plot(self.x_stick_list, self.future_series, color='g', 
                           label=self.future_id.upper())
            self.axes.plot(self.x_stick_list, self.index_series, color='y', 
                           label=self.getStockIndexName())
                           
        self.axes.legend(fontsize='small', loc=self.current_legend_pos)
        self.axes.set_title(self.title)
        self.axes.set_xlabel(self.xlabel)
        self.axes.set_ylabel(self.ylabel)
        
        self.yMax = self.ystick_max
        self.yMin = self.ystick_min
        
        self.paintPlotGrid()

        self.axes.set_ylim(self.yMin, self.yMax)
        self.axex_twinx.set_ylim(self.yMin, self.yMax)
        self.axes.set_yticks(self.ystick_list)
        self.axex_twinx.set_yticks(self.ystick_list)
        
        if not self.default_plot:
            fmt='%.2f%%'
            yticks = mtick.FormatStrFormatter(fmt)
            self.axes.yaxis.set_major_formatter(yticks)
            self.axex_twinx.yaxis.set_major_formatter(yticks)
        self.axes.set_xlim(0, 240)
        xmajorLocator = MultipleLocator(60)   # 将x主刻度标签设置为20的倍数  
        xminorLocator = MultipleLocator(5)    # 将x轴次刻度标签设置为5的倍数  
        self.axes.xaxis.set_major_locator(xmajorLocator)
        self.axes.xaxis.set_minor_locator(xminorLocator)
        self.axes.set_xticks(range(0, 241, 10))
        xlabels = (['09:30'] + ['']*5 + ['10:30'] + ['']*5 +
                   ['11:30'] + ['']*5 + ['14:00'] + ['']*5 +
                   ['15:00'])
        self.axes.set_xticklabels(xlabels)
        self.axes.hold(False)
        self.axex_twinx.hold(False)
        self.draw()
        
    def paintPlotGrid(self):
        for i in range(60, 241, 60):
            self.axes.plot([i, i], [self.yMin, self.yMax], color ='red', 
                           linewidth=0.5, linestyle="-.")
        for i in range(30, 241, 60):
            self.axes.plot([i, i], [self.yMin, self.yMax], color ='red', 
                           linewidth=0.2, linestyle="-.")
                           
        for y_v in self.ystick_list:
            if y_v==0.0:
                self.axes.plot([0, 240], [y_v, y_v], color ='red', 
                           linewidth=0.5, linestyle="-.")
            else:
                self.axes.plot([0, 240], [y_v, y_v], color ='red', 
                           linewidth=0.2, linestyle="-.")
                           
    def getStockIndexName(self):
        name = self.hedge_index_type.upper()
        if name.startswith('IC'):
            return u'中证500指数'
        elif name.startswith('IH'):
            return u'上证50指数'
        elif name.startswith('IF'):
            return u'沪深300指数'
        else:
            return u'股票指数'
            
if __name__=='__main__':
    series = pd.Series([3, 4, 5, 6], index=['a', 'b', 'c', 'd'])
    sss = series.to_json()
    print(sss)
#    pd.DataFrame.from_json(sss)
    series = pd.read_json(sss, typ='series')
                
                
                