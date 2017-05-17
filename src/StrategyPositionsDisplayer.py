from PyQt4.QtGui import *    
from PyQt4.QtCore import *    

#import GlobalVars

import xlrd
import xlwt

class StrategyPositionsDisplayerTable(QTableWidget):    
    def __init__(self, recorder, parent=None):    
        super(StrategyPositionsDisplayerTable, self).__init__(parent)    
        self.dataRecorder = recorder
        
        self.timer = QTimer(self)
#        self.timer.timeout.connect(self.onShowNewContentInTable)
        self.timer.start(7000)    
        self.outputToExcel = True
        self.onShowNewContentInTable()        
        
    def onShowNewContentInTable(self):
        headers = [u'股票名称', u'股票代码', u'持仓数量', 
                   u'建仓价格', u'最新价格', u'持仓盈亏']
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(self.dataRecorder.stkId_list))
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
#        self.setSortingEnabled(False)
        self.setSortingEnabled(True)
        
        if self.outputToExcel:
            self.excelFile = xlwt.Workbook()
            self.excelTable = self.excelFile.add_sheet(u'策略持仓', cell_overwrite_ok=True)

        for i in range(len(self.dataRecorder.stkId_list)):
            sid = convertFromWindyStockId(self.dataRecorder.stkId_list[i])
#            stock_name = GlobalVars.stock_id_name_map[sid]
            qtableItem = QTableWidgetItem(stock_name)
            qtableItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 0, qtableItem)
            
            qtableItem = QTableWidgetItem(sid)
            qtableItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 1, qtableItem)   
            
            stock_num = self.dataRecorder.stockPositionsDict[self.dataRecorder.stkId_list[i]]
            qtableItem = QTableWidgetItem(str(stock_num))
            qtableItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 2, qtableItem)   
            
            initPrice = self.dataRecorder.stockInitPricesDict[self.dataRecorder.stkId_list[i]]
            qtableItem = QTableWidgetItem(str(initPrice))
            qtableItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 3, qtableItem) 

            if self.dataRecorder.state=='history':
                pass
#                newestPrice = GlobalVars.oneMinPricesDict[sid]['15:00:00']
            elif self.dataRecorder.state=='realtime':
                pass
#                newest_time_str = next(reversed(GlobalVars.todayOneMinPricesDict[sid]))
#                newestPrice = GlobalVars.todayOneMinPricesDict[sid][newest_time_str]
            else:
                raise ValueError('self.dataRecorder.state not contains the right value')
            
            qtableItem = QTableWidgetItem(str(round(newestPrice, 2)))
            qtableItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 4, qtableItem) 
            
            p_and_l = round((newestPrice-initPrice)*stock_num, 2)
            qtableItem = QTableWidgetItem(str(p_and_l))
            qtableItem.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 5, qtableItem)
            self.storeToExcel(stock_name, sid, stock_num, initPrice, 
                              newestPrice, p_and_l, i)
        if self.outputToExcel:
            self.excelFile.save(self.dataRecorder.strategy_name + '_position.xls')            
            
    def storeToExcel(self, stock_name, stock_id, stock_num, initPrice, 
                     newestPrice, p_and_l, row):
        if not self.outputToExcel:
            return
        self.excelTable.write(row, 1, stock_name)
        self.excelTable.write(row, 2, stock_id)
        self.excelTable.write(row, 3, stock_num)
        self.excelTable.write(row, 4, initPrice)
        self.excelTable.write(row, 5, newestPrice)
        self.excelTable.write(row, 6, p_and_l)            


class StrategyPositionsDisplayer(QMainWindow):
    def __init__(self, recorder, parent=None):
        super(StrategyPositionsDisplayer, self).__init__(parent)
        self.table = StrategyPositionsDisplayerTable(recorder)
        self.setCentralWidget(self.table)
        self.setWindowTitle(u'当前持仓')
        self.setGeometry(200, 200, 800, 600)
        screen=QDesktopWidget().screenGeometry()
        size=self.geometry()
        self.move((screen.width()-size.width())/2, 
                  (screen.height()-size.height())/2)
        
        